import sys
from pymongo.errors import OperationFailure
from db import get_db, check_connection

USERS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "email", "password_hash", "role", "city", "created_at"],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "name": {"bsonType": "string", "minLength": 1},
            "email": {"bsonType": "string", "pattern": "^.+@.+\\..+$"},
            "password_hash": {"bsonType": "string"},
            "role": {"enum": ["donor", "receiver"]},
            "organization_name": {"bsonType": ["string", "null"]},
            "city": {"bsonType": "string", "minLength": 1},
            "created_at": {"bsonType": "date"}
        }
    }
}

DONATIONS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "donor_id", "food_name", "category", "servings", "dietary_type",
            "allergens", "prepared_at", "pickup_deadline", "pickup_location",
            "status", "status_history", "created_at", "updated_at"
        ],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "donor_id": {"bsonType": "objectId"},
            "food_name": {"bsonType": "string", "minLength": 1},
            "category": {"enum": ["prepared_meal", "bakery", "fruits_vegetables", "packaged_food", "other"]},
            "servings": {"bsonType": "int", "minimum": 1},
            "dietary_type": {"enum": ["vegetarian", "non_vegetarian", "vegan", "other"]},
            "allergens": {"bsonType": "array", "items": {"bsonType": "string"}},
            "prepared_at": {"bsonType": "date"},
            "pickup_deadline": {"bsonType": "date"},
            "pickup_location": {
                "bsonType": "object",
                "required": ["area", "city"],
                "properties": {
                    "area": {"bsonType": "string", "minLength": 1},
                    "city": {"bsonType": "string", "minLength": 1}
                }
            },
            "status": {"enum": ["available", "claimed", "collected", "cancelled", "expired"]},
            "claim": {
                "bsonType": ["object", "null"],
                "properties": {
                    "receiver_id": {"bsonType": "objectId"},
                    "claimed_at": {"bsonType": "date"}
                }
            },
            "status_history": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["old_status", "new_status", "changed_at", "changed_by"],
                    "properties": {
                        "old_status": {"bsonType": ["string", "null"]},
                        "new_status": {"bsonType": "string"},
                        "changed_at": {"bsonType": "date"},
                        "changed_by": {"bsonType": ["objectId", "null"]},
                        "note": {"bsonType": ["string", "null"]}
                    }
                }
            },
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "collected_at": {"bsonType": ["date", "null"]},
            "seed_demo": {"bsonType": "bool"}
        }
    }
}


def apply_collection_schema(db, collection_name, validator):
    """Creates collection with validator or updates existing validator via collMod."""
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name, validator=validator, validationLevel="moderate", validationAction="error")
        print(f"[OK] Collection '{collection_name}' created with JSON schema validation.")
    else:
        try:
            db.command({"collMod": collection_name, "validator": validator, "validationLevel": "moderate", "validationAction": "error"})
            print(f"[OK] Collection '{collection_name}' validator updated.")
        except OperationFailure as e:
            print(f"[WARN] collMod failed on '{collection_name}': {e.details}")


def setup_indexes(db):
    """Creates unique, compound, and full-text indexes."""
    db.users.create_index([("email", 1)], unique=True, name="idx_users_email_unique")
    db.donations.create_index([("status", 1), ("pickup_deadline", 1)], name="idx_donations_status_deadline")
    db.donations.create_index([("donor_id", 1), ("created_at", -1)], name="idx_donations_donor_created")
    db.donations.create_index([("pickup_location.city", 1), ("status", 1)], name="idx_donations_city_status")
    db.donations.create_index([("food_name", "text")], name="idx_donations_food_name_text")
    print("[OK] Indexes created on users and donations.")


def test_validation_rejection(db):
    """Verifies that MongoDB schema rejects invalid documents."""
    invalid_doc = {"food_name": "Test", "category": "bad_cat", "servings": -1}
    try:
        db.donations.insert_one(invalid_doc)
        print("[FAIL] Invalid document was unexpectedly inserted.")
    except OperationFailure:
        print("[PASSED] MongoDB schema validator successfully rejected invalid document.")


def main():
    is_connected, msg = check_connection()
    if not is_connected:
        print(f"[ERROR] {msg}")
        sys.exit(1)

    db = get_db()
    apply_collection_schema(db, "users", USERS_VALIDATOR)
    apply_collection_schema(db, "donations", DONATIONS_VALIDATOR)
    setup_indexes(db)
    test_validation_rejection(db)
    print("Database initialization complete.")


if __name__ == "__main__":
    main()
