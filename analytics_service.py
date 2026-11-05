from db import get_donations_collection, get_users_collection, utc_now


def get_collected_servings_by_category():
    """Report 1: Aggregates collected servings grouped by food category."""
    pipeline = [
        {"$match": {"status": "collected"}},
        {"$group": {"_id": "$category", "collected_count": {"$sum": 1}, "total_servings": {"$sum": "$servings"}}},
        {"$sort": {"total_servings": -1}},
        {"$project": {"_id": 0, "category": "$_id", "collected_count": 1, "total_servings": 1}}
    ]
    return list(get_donations_collection().aggregate(pipeline))


def get_donations_by_status():
    """Report 2: Groups and counts total donations by status."""
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$project": {"_id": 0, "status": "$_id", "count": 1}}
    ]
    return list(get_donations_collection().aggregate(pipeline))


def get_top_contributing_donors(limit=5):
    """Report 3: Aggregates top donors by collected servings with $lookup."""
    pipeline = [
        {"$match": {"status": "collected"}},
        {"$group": {"_id": "$donor_id", "collected_donations": {"$sum": 1}, "total_servings": {"$sum": "$servings"}}},
        {"$sort": {"total_servings": -1}},
        {"$limit": limit},
        {"$lookup": {"from": "users", "localField": "_id", "foreignField": "_id", "as": "donor_info"}},
        {"$unwind": {"path": "$donor_info", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 0,
                "donor_id": "$_id",
                "donor_name": {"$ifNull": ["$donor_info.name", "Unknown Donor"]},
                "organization": {"$ifNull": ["$donor_info.organization_name", "Individual"]},
                "city": {"$ifNull": ["$donor_info.city", "N/A"]},
                "collected_donations": 1,
                "total_servings": 1
            }
        }
    ]
    return list(get_donations_collection().aggregate(pipeline))


def get_monthly_collection_trends():
    """Report 4: Groups collected donations chronologically by month (YYYY-MM)."""
    pipeline = [
        {"$match": {"status": "collected", "collected_at": {"$ne": None}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$collected_at"}},
                "collected_count": {"$sum": 1},
                "total_servings": {"$sum": "$servings"}
            }
        },
        {"$sort": {"_id": 1}},
        {"$project": {"_id": 0, "month": "$_id", "collected_count": 1, "total_servings": 1}}
    ]
    return list(get_donations_collection().aggregate(pipeline))


def get_finalized_collection_rate():
    """Report 5: Calculates (collected / finalized) * 100 percentage."""
    pipeline = [
        {"$match": {"status": {"$in": ["collected", "cancelled", "expired"]}}},
        {
            "$group": {
                "_id": None,
                "total_finalized": {"$sum": 1},
                "collected_count": {"$sum": {"$cond": [{"$eq": ["$status", "collected"]}, 1, 0]}},
                "cancelled_count": {"$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}},
                "expired_count": {"$sum": {"$cond": [{"$eq": ["$status", "expired"]}, 1, 0]}}
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_finalized": 1,
                "collected_count": 1,
                "cancelled_count": 1,
                "expired_count": 1,
                "collection_rate_percent": {
                    "$cond": [
                        {"$gt": ["$total_finalized", 0]},
                        {"$round": [{"$multiply": [{"$divide": ["$collected_count", "$total_finalized"]}, 100]}, 1]},
                        0.0
                    ]
                }
            }
        }
    ]
    results = list(get_donations_collection().aggregate(pipeline))
    return results[0] if results else {
        "total_finalized": 0, "collected_count": 0, "cancelled_count": 0, "expired_count": 0, "collection_rate_percent": 0.0
    }


def get_platform_summary():
    """Aggregates high-level counters for platform overview."""
    user_counts = list(get_users_collection().aggregate([{"$group": {"_id": "$role", "count": {"$sum": 1}}}]))
    role_map = {item["_id"]: item["count"] for item in user_counts}

    donation_stats = list(get_donations_collection().aggregate([
        {
            "$group": {
                "_id": None,
                "total_donations": {"$sum": 1},
                "total_servings_all": {"$sum": "$servings"},
                "collected_servings": {"$sum": {"$cond": [{"$eq": ["$status", "collected"]}, "$servings", 0]}},
                "available_servings": {"$sum": {"$cond": [{"$eq": ["$status", "available"]}, "$servings", 0]}},
                "available_count": {"$sum": {"$cond": [{"$eq": ["$status", "available"]}, 1, 0]}},
                "claimed_count": {"$sum": {"$cond": [{"$eq": ["$status", "claimed"]}, 1, 0]}},
                "collected_count": {"$sum": {"$cond": [{"$eq": ["$status", "collected"]}, 1, 0]}}
            }
        }
    ]))

    stats = donation_stats[0] if donation_stats else {
        "total_donations": 0, "total_servings_all": 0, "collected_servings": 0,
        "available_servings": 0, "available_count": 0, "claimed_count": 0, "collected_count": 0
    }
    stats["donor_count"] = role_map.get("donor", 0)
    stats["receiver_count"] = role_map.get("receiver", 0)
    return stats


def get_approaching_deadline_donations(limit=6):
    """Retrieves available donations sorted by nearest pickup deadline."""
    now = utc_now()
    pipeline = [
        {"$match": {"status": "available", "pickup_deadline": {"$gt": now}}},
        {"$sort": {"pickup_deadline": 1}},
        {"$limit": limit},
        {"$lookup": {"from": "users", "localField": "donor_id", "foreignField": "_id", "as": "donor"}},
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}}
    ]
    return list(get_donations_collection().aggregate(pipeline))
