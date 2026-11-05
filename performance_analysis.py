from db import get_db, get_donations_collection, utc_now


def _extract_stages(plan):
    """Extracts scan stages (e.g. IXSCAN, COLLSCAN) from winningPlan."""
    stages = []

    def _traverse(node):
        if not isinstance(node, dict):
            return
        if "stage" in node:
            stages.append(node["stage"])
        if "inputStage" in node:
            _traverse(node["inputStage"])
        if "inputStages" in node:
            for s in node["inputStages"]:
                _traverse(s)

    _traverse(plan)
    return stages


def get_query_execution_analysis():
    """Compares query execution statistics between indexed and forced COLLSCAN scans."""
    donations = get_donations_collection()
    now = utc_now()
    filter_q = {"status": "available", "pickup_deadline": {"$gt": now}}

    # Query 1A: With Compound Index (status: 1, pickup_deadline: 1)
    try:
        cur_idx = donations.find(filter_q).sort("pickup_deadline", 1)
        plan_idx = cur_idx.explain()["executionStats"]
        winning_idx = cur_idx.explain().get("queryPlanner", {}).get("winningPlan", {})
        stages_idx = _extract_stages(winning_idx)
    except Exception as e:
        plan_idx, stages_idx = {"error": str(e)}, ["UNKNOWN"]

    # Query 1B: Forced Collection Scan (COLLSCAN via {$natural: 1})
    try:
        cur_unidx = donations.find(filter_q).hint([("$natural", 1)])
        plan_unidx = cur_unidx.explain()["executionStats"]
        winning_unidx = cur_unidx.explain().get("queryPlanner", {}).get("winningPlan", {})
        stages_unidx = _extract_stages(winning_unidx)
    except Exception as e:
        plan_unidx, stages_unidx = {"error": str(e)}, ["UNKNOWN"]

    # Query 2: City and Status Filter with compound index
    try:
        cur_city = donations.find({"pickup_location.city": "Bengaluru", "status": "available"})
        plan_city = cur_city.explain()["executionStats"]
        winning_city = cur_city.explain().get("queryPlanner", {}).get("winningPlan", {})
        stages_city = _extract_stages(winning_city)
    except Exception as e:
        plan_city, stages_city = {"error": str(e)}, ["UNKNOWN"]

    # Query 3: Full-text Search with text index
    try:
        cur_txt = donations.find({"$text": {"$search": "rice bread meal"}})
        plan_txt = cur_txt.explain()["executionStats"]
        winning_txt = cur_txt.explain().get("queryPlanner", {}).get("winningPlan", {})
        stages_txt = _extract_stages(winning_txt)
    except Exception as e:
        plan_txt, stages_txt = {"error": str(e)}, ["UNKNOWN"]

    return {
        "status_deadline_comparison": {
            "query_description": "Find available donations where pickup_deadline > now() sorted by deadline",
            "indexed": {
                "scan_type": "IXSCAN (Index Scan)" if "IXSCAN" in stages_idx else "/".join(stages_idx),
                "nReturned": plan_idx.get("nReturned", 0),
                "totalDocsExamined": plan_idx.get("totalDocsExamined", 0),
                "totalKeysExamined": plan_idx.get("totalKeysExamined", 0),
                "executionTimeMillis": plan_idx.get("executionTimeMillis", 0),
                "index_used": "idx_donations_status_deadline (status: 1, pickup_deadline: 1)"
            },
            "unindexed": {
                "scan_type": "COLLSCAN (Collection Scan)" if "COLLSCAN" in stages_unidx else "/".join(stages_unidx),
                "nReturned": plan_unidx.get("nReturned", 0),
                "totalDocsExamined": plan_unidx.get("totalDocsExamined", 0),
                "totalKeysExamined": plan_unidx.get("totalKeysExamined", 0),
                "executionTimeMillis": plan_unidx.get("executionTimeMillis", 0),
                "index_used": "None (Forced table scan via hint({'$natural': 1}))"
            }
        },
        "city_search": {
            "query_description": "Filter by pickup_location.city == 'Bengaluru' and status == 'available'",
            "scan_type": "IXSCAN (Index Scan)" if "IXSCAN" in stages_city else "/".join(stages_city),
            "nReturned": plan_city.get("nReturned", 0),
            "totalDocsExamined": plan_city.get("totalDocsExamined", 0),
            "totalKeysExamined": plan_city.get("totalKeysExamined", 0),
            "executionTimeMillis": plan_city.get("executionTimeMillis", 0),
            "index_used": "idx_donations_city_status"
        },
        "text_search": {
            "query_description": "Full-text search on food_name using $text: 'rice bread meal'",
            "scan_type": "TEXT_MATCH / IXSCAN" if ("TEXT_MATCH" in stages_txt or "IXSCAN" in stages_txt) else "/".join(stages_txt),
            "nReturned": plan_txt.get("nReturned", 0),
            "totalDocsExamined": plan_txt.get("totalDocsExamined", 0),
            "totalKeysExamined": plan_txt.get("totalKeysExamined", 0),
            "executionTimeMillis": plan_txt.get("executionTimeMillis", 0),
            "index_used": "idx_donations_food_name_text"
        }
    }


def get_database_statistics():
    """Extracts document counts and active index definitions from MongoDB."""
    db = get_db()
    users_col = db["users"]
    donations_col = db["donations"]

    def _format_indexes(col):
        res = []
        for name, info in col.index_information().items():
            keys = ", ".join([f"{k}: {d}" for k, d in info.get("key", [])])
            res.append({"name": name, "keys": keys, "unique": info.get("unique", False)})
        return res

    return {
        "db_name": db.name,
        "collections": [
            {
                "name": "users",
                "document_count": users_col.count_documents({}),
                "indexes": _format_indexes(users_col),
                "purpose": "Stores registered food donors and receiver NGOs with role-based access"
            },
            {
                "name": "donations",
                "document_count": donations_col.count_documents({}),
                "indexes": _format_indexes(donations_col),
                "purpose": "Stores surplus food listings with embedded locations, claims, and status history"
            }
        ]
    }
