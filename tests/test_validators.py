"""
test_validators.py - Automated Unit Tests for FoodLoop Business Logic & Validation
----------------------------------------------------------------------------------
Tests application validation functions without requiring an external MongoDB connection.
Executes quickly and cleanly with pytest.
"""

from datetime import datetime, timedelta, timezone
from bson import ObjectId
from validators import (
    validate_registration,
    validate_donation_input,
    validate_claim_action,
    validate_collection_action,
    validate_donor_ownership
)


def test_valid_registration():
    data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "secretpassword123",
        "role": "donor",
        "city": "Bengaluru"
    }
    is_valid, errors = validate_registration(data)
    assert is_valid is True
    assert len(errors) == 0


def test_invalid_registration_missing_fields_and_weak_password():
    data = {
        "name": "",
        "email": "invalid-email-address",
        "password": "123",  # less than 6 chars
        "role": "admin",    # invalid privileged role
        "city": ""
    }
    is_valid, errors = validate_registration(data)
    assert is_valid is False
    assert any("Name is required" in e for e in errors)
    assert any("valid email" in e for e in errors)
    assert any("Password must be at least 6 characters" in e for e in errors)
    assert any("Role must be one of" in e for e in errors)
    assert any("City is required" in e for e in errors)


def test_valid_donation_input():
    now = datetime.now(timezone.utc)
    data = {
        "food_name": "Vegetable Biryani",
        "category": "prepared_meal",
        "servings": 50,
        "dietary_type": "vegetarian",
        "allergens": "dairy, gluten",
        "prepared_at": now - timedelta(hours=1),
        "pickup_deadline": now + timedelta(hours=4),
        "area": "Campus Canteen",
        "city": "Bengaluru"
    }
    is_valid, cleaned, errors = validate_donation_input(data, is_update=False)
    assert is_valid is True
    assert len(errors) == 0
    assert cleaned["servings"] == 50
    assert cleaned["category"] == "prepared_meal"
    assert "dairy" in cleaned["allergens"]
    assert "gluten" in cleaned["allergens"]
    assert cleaned["pickup_location"]["area"] == "Campus Canteen"
    assert cleaned["pickup_location"]["city"] == "Bengaluru"


def test_invalid_donation_input_negative_servings_and_past_deadline():
    now = datetime.now(timezone.utc)
    data = {
        "food_name": "",
        "category": "invalid_cat",
        "servings": -10,
        "dietary_type": "invalid_diet",
        "allergens": "",
        "prepared_at": now + timedelta(hours=5),  # prepared after deadline
        "pickup_deadline": now - timedelta(hours=2), # deadline in past
        "area": "",
        "city": ""
    }
    is_valid, cleaned, errors = validate_donation_input(data, is_update=False)
    assert is_valid is False
    assert any("Food name cannot be empty" in e for e in errors)
    assert any("Category must be one of" in e for e in errors)
    assert any("positive integer" in e for e in errors)
    assert any("Dietary type must be one of" in e for e in errors)
    assert any("cannot be later than the pickup deadline" in e for e in errors)
    assert any("future date and time" in e for e in errors)
    assert any("Pickup area" in e for e in errors)
    assert any("Pickup city" in e for e in errors)


def test_claim_action_validation():
    now = datetime.now(timezone.utc)
    donor_id = ObjectId()
    receiver_id = ObjectId()
    other_user_id = ObjectId()

    donation = {
        "_id": ObjectId(),
        "donor_id": donor_id,
        "food_name": "Meals",
        "status": "available",
        "pickup_deadline": now + timedelta(hours=3),
        "claim": None
    }

    # 1. Valid claim by receiver
    can_claim, err = validate_claim_action(donation, receiver_id, "receiver")
    assert can_claim is True
    assert err is None

    # 2. Donor attempting to claim own donation
    can_claim, err = validate_claim_action(donation, donor_id, "receiver")
    assert can_claim is False
    assert "cannot claim their own" in err

    # 3. Non-receiver attempting to claim
    can_claim, err = validate_claim_action(donation, other_user_id, "donor")
    assert can_claim is False
    assert "Only registered receivers" in err

    # 4. Attempting to claim non-available donation
    donation["status"] = "claimed"
    can_claim, err = validate_claim_action(donation, receiver_id, "receiver")
    assert can_claim is False
    assert "currently 'claimed'" in err

    # 5. Attempting to claim expired donation
    donation["status"] = "available"
    donation["pickup_deadline"] = now - timedelta(minutes=10)
    can_claim, err = validate_claim_action(donation, receiver_id, "receiver")
    assert can_claim is False
    assert "expired" in err


def test_collection_action_validation():
    receiver_id = ObjectId()
    other_receiver_id = ObjectId()

    donation = {
        "_id": ObjectId(),
        "status": "claimed",
        "claim": {
            "receiver_id": receiver_id,
            "claimed_at": datetime.now(timezone.utc)
        }
    }

    # 1. Valid confirmation by the claimant
    can_confirm, err = validate_collection_action(donation, receiver_id, "receiver")
    assert can_confirm is True
    assert err is None

    # 2. Different receiver attempting to confirm
    can_confirm, err = validate_collection_action(donation, other_receiver_id, "receiver")
    assert can_confirm is False
    assert "Only the receiver who claimed" in err

    # 3. Attempting to confirm when not in 'claimed' status
    donation["status"] = "available"
    can_confirm, err = validate_collection_action(donation, receiver_id, "receiver")
    assert can_confirm is False
    assert "status is 'available'" in err


def test_donor_ownership_validation():
    donor_id = ObjectId()
    stranger_id = ObjectId()

    donation = {
        "_id": ObjectId(),
        "donor_id": donor_id,
        "status": "available"
    }

    # 1. Allowed owner access
    is_owner, err = validate_donor_ownership(donation, donor_id, permitted_statuses=["available"])
    assert is_owner is True

    # 2. Unauthorized user access
    is_owner, err = validate_donor_ownership(donation, stranger_id)
    assert is_owner is False
    assert "permission" in err

    # 3. Status restriction test
    donation["status"] = "collected"
    is_owner, err = validate_donor_ownership(donation, donor_id, permitted_statuses=["available"])
    assert is_owner is False
    assert "not permitted when donation status is 'collected'" in err
