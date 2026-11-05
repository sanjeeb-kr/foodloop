from bson import ObjectId
from db import get_donations_collection, utc_now


def expire_overdue_donations():
    """Auto-expires available listings whose pickup deadline has passed."""
    now = utc_now()
    result = get_donations_collection().update_many(
        {"status": "available", "pickup_deadline": {"$lte": now}},
        {
            "$set": {"status": "expired", "updated_at": now},
            "$push": {
                "status_history": {
                    "old_status": "available",
                    "new_status": "expired",
                    "changed_at": now,
                    "changed_by": None,
                    "note": "Automatically expired: pickup deadline elapsed."
                }
            }
        }
    )
    return result.modified_count


def create_donation(donor_id, cleaned_data):
    """Inserts a new donation document with initial status history."""
    now = utc_now()
    donor_obj_id = ObjectId(donor_id) if isinstance(donor_id, str) else donor_id

    doc = {
        "donor_id": donor_obj_id,
        "food_name": cleaned_data["food_name"],
        "category": cleaned_data["category"],
        "servings": int(cleaned_data["servings"]),
        "dietary_type": cleaned_data["dietary_type"],
        "allergens": cleaned_data["allergens"],
        "prepared_at": cleaned_data["prepared_at"],
        "pickup_deadline": cleaned_data["pickup_deadline"],
        "pickup_location": cleaned_data["pickup_location"],
        "status": "available",
        "claim": None,
        "status_history": [
            {
                "old_status": None,
                "new_status": "available",
                "changed_at": now,
                "changed_by": donor_obj_id,
                "note": "Listing published by donor."
            }
        ],
        "created_at": now,
        "updated_at": now,
        "collected_at": None
    }

    result = get_donations_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_donation_by_id(donation_id):
    """Retrieves donation with joined donor and receiver details via $lookup."""
    try:
        obj_id = ObjectId(donation_id) if isinstance(donation_id, str) else donation_id
    except Exception:
        return None

    pipeline = [
        {"$match": {"_id": obj_id}},
        {
            "$lookup": {
                "from": "users",
                "localField": "donor_id",
                "foreignField": "_id",
                "as": "donor_info"
            }
        },
        {"$unwind": {"path": "$donor_info", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "users",
                "localField": "claim.receiver_id",
                "foreignField": "_id",
                "as": "receiver_info"
            }
        },
        {"$unwind": {"path": "$receiver_info", "preserveNullAndEmptyArrays": True}}
    ]

    results = list(get_donations_collection().aggregate(pipeline))
    return results[0] if results else None


def list_available_donations(category=None, city=None, dietary_type=None, search_query=None):
    """Retrieves available donations matching filters and ordered by earliest deadline."""
    expire_overdue_donations()
    now = utc_now()

    query = {"status": "available", "pickup_deadline": {"$gt": now}}

    if category and category != "all":
        query["category"] = category
    if city and city.strip():
        query["pickup_location.city"] = {"$regex": f"^{city.strip()}$", "$options": "i"}
    if dietary_type and dietary_type != "all":
        query["dietary_type"] = dietary_type
    if search_query and search_query.strip():
        query["$text"] = {"$search": search_query.strip()}

    pipeline = [
        {"$match": query},
        {
            "$lookup": {
                "from": "users",
                "localField": "donor_id",
                "foreignField": "_id",
                "as": "donor"
            }
        },
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"pickup_deadline": 1}}
    ]
    return list(get_donations_collection().aggregate(pipeline))


def get_donor_listings(donor_id):
    """Retrieves all donations created by a donor."""
    expire_overdue_donations()
    donor_obj_id = ObjectId(donor_id) if isinstance(donor_id, str) else donor_id

    pipeline = [
        {"$match": {"donor_id": donor_obj_id}},
        {
            "$lookup": {
                "from": "users",
                "localField": "claim.receiver_id",
                "foreignField": "_id",
                "as": "receiver"
            }
        },
        {"$unwind": {"path": "$receiver", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"created_at": -1}}
    ]
    return list(get_donations_collection().aggregate(pipeline))


def get_receiver_claims(receiver_id):
    """Retrieves all donations claimed or collected by a receiver."""
    expire_overdue_donations()
    receiver_obj_id = ObjectId(receiver_id) if isinstance(receiver_id, str) else receiver_id

    pipeline = [
        {"$match": {"claim.receiver_id": receiver_obj_id}},
        {
            "$lookup": {
                "from": "users",
                "localField": "donor_id",
                "foreignField": "_id",
                "as": "donor"
            }
        },
        {"$unwind": {"path": "$donor", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"updated_at": -1}}
    ]
    return list(get_donations_collection().aggregate(pipeline))


def claim_donation_atomic(donation_id, receiver_id):
    """Atomic conditional update to prevent double claiming."""
    expire_overdue_donations()
    now = utc_now()

    try:
        d_id = ObjectId(donation_id) if isinstance(donation_id, str) else donation_id
        r_id = ObjectId(receiver_id) if isinstance(receiver_id, str) else receiver_id
    except Exception:
        return False, "Invalid identifier."

    filter_query = {
        "_id": d_id,
        "status": "available",
        "pickup_deadline": {"$gt": now},
        "donor_id": {"$ne": r_id}
    }

    update_doc = {
        "$set": {
            "status": "claimed",
            "claim": {"receiver_id": r_id, "claimed_at": now},
            "updated_at": now
        },
        "$push": {
            "status_history": {
                "old_status": "available",
                "new_status": "claimed",
                "changed_at": now,
                "changed_by": r_id,
                "note": "Listing claimed by receiver for pickup."
            }
        }
    }

    result = get_donations_collection().update_one(filter_query, update_doc)
    if result.matched_count == 1:
        return True, "Donation claimed successfully!"

    current = get_donations_collection().find_one({"_id": d_id})
    if not current:
        return False, "Listing not found."
    if current.get("donor_id") == r_id:
        return False, "You cannot claim your own donation."
    if current.get("status") != "available":
        return False, f"Listing was already {current.get('status')}."
    if current.get("pickup_deadline") <= now:
        return False, "Pickup deadline has already passed."
    return False, "Failed to claim donation."


def confirm_collection(donation_id, receiver_id):
    """Updates listing to collected once picked up by receiver."""
    now = utc_now()
    try:
        d_id = ObjectId(donation_id) if isinstance(donation_id, str) else donation_id
        r_id = ObjectId(receiver_id) if isinstance(receiver_id, str) else receiver_id
    except Exception:
        return False, "Invalid identifier."

    result = get_donations_collection().update_one(
        {"_id": d_id, "status": "claimed", "claim.receiver_id": r_id},
        {
            "$set": {"status": "collected", "collected_at": now, "updated_at": now},
            "$push": {
                "status_history": {
                    "old_status": "claimed",
                    "new_status": "collected",
                    "changed_at": now,
                    "changed_by": r_id,
                    "note": "Food collected by receiver."
                }
            }
        }
    )
    if result.matched_count == 1:
        return True, "Collection confirmed successfully!"
    return False, "Could not confirm collection. Please verify your claim."


def update_donation(donation_id, donor_id, cleaned_data):
    """Updates permitted fields of an available donation."""
    now = utc_now()
    try:
        d_id = ObjectId(donation_id) if isinstance(donation_id, str) else donation_id
        u_id = ObjectId(donor_id) if isinstance(donor_id, str) else donor_id
    except Exception:
        return False, "Invalid identifier."

    update_fields = {
        "food_name": cleaned_data["food_name"],
        "category": cleaned_data["category"],
        "servings": int(cleaned_data["servings"]),
        "dietary_type": cleaned_data["dietary_type"],
        "allergens": cleaned_data["allergens"],
        "prepared_at": cleaned_data["prepared_at"],
        "pickup_deadline": cleaned_data["pickup_deadline"],
        "pickup_location": cleaned_data["pickup_location"],
        "updated_at": now
    }

    result = get_donations_collection().update_one(
        {"_id": d_id, "donor_id": u_id, "status": "available"},
        {
            "$set": update_fields,
            "$push": {
                "status_history": {
                    "old_status": "available",
                    "new_status": "available",
                    "changed_at": now,
                    "changed_by": u_id,
                    "note": "Listing details updated by donor."
                }
            }
        }
    )
    if result.matched_count == 1:
        return True, "Donation updated successfully."
    return False, "Listing can only be updated while 'available'."


def cancel_donation(donation_id, donor_id, reason="Cancelled by donor."):
    """Cancels an active or claimed donation."""
    now = utc_now()
    try:
        d_id = ObjectId(donation_id) if isinstance(donation_id, str) else donation_id
        u_id = ObjectId(donor_id) if isinstance(donor_id, str) else donor_id
    except Exception:
        return False, "Invalid identifier."

    current = get_donations_collection().find_one({
        "_id": d_id, "donor_id": u_id, "status": {"$in": ["available", "claimed"]}
    })
    if not current:
        return False, "Listing cannot be cancelled."

    result = get_donations_collection().update_one(
        {"_id": d_id},
        {
            "$set": {"status": "cancelled", "updated_at": now},
            "$push": {
                "status_history": {
                    "old_status": current.get("status"),
                    "new_status": "cancelled",
                    "changed_at": now,
                    "changed_by": u_id,
                    "note": reason
                }
            }
        }
    )
    if result.matched_count == 1:
        return True, "Listing cancelled successfully."
    return False, "Cancellation failed."


def delete_donation(donation_id, donor_id):
    """Permanently deletes available or cancelled listing."""
    try:
        d_id = ObjectId(donation_id) if isinstance(donation_id, str) else donation_id
        u_id = ObjectId(donor_id) if isinstance(donor_id, str) else donor_id
    except Exception:
        return False, "Invalid identifier."

    result = get_donations_collection().delete_one({
        "_id": d_id, "donor_id": u_id, "status": {"$in": ["available", "cancelled"]}
    })
    if result.deleted_count == 1:
        return True, "Donation permanently deleted."
    return False, "Only available or cancelled listings can be deleted."
