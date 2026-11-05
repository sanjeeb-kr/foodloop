from datetime import datetime, timezone

VALID_ROLES = {"donor", "receiver"}
VALID_CATEGORIES = {"prepared_meal", "bakery", "fruits_vegetables", "packaged_food", "other"}
VALID_DIETARY_TYPES = {"vegetarian", "non_vegetarian", "vegan", "other"}
VALID_STATUSES = {"available", "claimed", "collected", "cancelled", "expired"}


def validate_registration(data):
    """Validates user registration input."""
    errors = []
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip().lower()
    city = (data.get("city") or "").strip()

    if not name:
        errors.append("Name is required and cannot be empty.")
    elif len(name) < 2:
        errors.append("Name must be at least 2 characters long.")
    if not email or "@" not in email or "." not in email:
        errors.append("Please enter a valid email address.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters long.")
    if role not in VALID_ROLES:
        errors.append(f"Role must be one of: {', '.join(sorted(VALID_ROLES))}.")
    if not city:
        errors.append("City is required.")

    return len(errors) == 0, errors


def validate_donation_input(data, is_update=False):
    """Validates donation fields before MongoDB write."""
    errors = []
    cleaned = {}

    food_name = (data.get("food_name") or "").strip()
    if not food_name:
        errors.append("Food name cannot be empty.")
    else:
        cleaned["food_name"] = food_name

    category = (data.get("category") or "").strip()
    if category not in VALID_CATEGORIES:
        errors.append(f"Category must be one of: {', '.join(sorted(VALID_CATEGORIES))}.")
    else:
        cleaned["category"] = category

    try:
        servings = int(data.get("servings"))
        if servings <= 0:
            errors.append("Servings quantity must be a positive integer.")
        else:
            cleaned["servings"] = servings
    except (ValueError, TypeError):
        errors.append("Servings must be a valid positive integer.")

    dietary_type = (data.get("dietary_type") or "").strip()
    if dietary_type not in VALID_DIETARY_TYPES:
        errors.append(f"Dietary type must be one of: {', '.join(sorted(VALID_DIETARY_TYPES))}.")
    else:
        cleaned["dietary_type"] = dietary_type

    # Clean allergen tags array
    raw_allergens = data.get("allergens", [])
    if isinstance(raw_allergens, str):
        cleaned["allergens"] = [a.strip() for a in raw_allergens.split(",") if a.strip()]
    elif isinstance(raw_allergens, list):
        cleaned["allergens"] = [str(a).strip() for a in raw_allergens if str(a).strip()]
    else:
        cleaned["allergens"] = []

    # Validate dates
    now_utc = datetime.now(timezone.utc)
    prepared_at = data.get("prepared_at")
    pickup_deadline = data.get("pickup_deadline")

    if not isinstance(prepared_at, datetime):
        errors.append("Valid preparation time is required.")
    else:
        cleaned["prepared_at"] = prepared_at

    if not isinstance(pickup_deadline, datetime):
        errors.append("Valid pickup deadline is required.")
    else:
        cleaned["pickup_deadline"] = pickup_deadline

    if isinstance(prepared_at, datetime) and isinstance(pickup_deadline, datetime):
        if prepared_at > pickup_deadline:
            errors.append("Preparation time cannot be later than the pickup deadline.")
        if not is_update and pickup_deadline <= now_utc:
            errors.append("Pickup deadline must be set to a future date and time.")

    # Location embedded sub-document
    area = (data.get("area") or "").strip()
    city = (data.get("city") or "").strip()
    if not area:
        errors.append("Pickup area is required.")
    if not city:
        errors.append("Pickup city is required.")
    cleaned["pickup_location"] = {"area": area, "city": city}

    return len(errors) == 0, cleaned, errors


def validate_claim_action(donation, user_id, user_role):
    """Verifies eligibility to claim a food donation."""
    if user_role != "receiver":
        return False, "Only registered receivers can claim food donations."
    if not donation:
        return False, "Donation not found."
    if str(donation.get("donor_id")) == str(user_id):
        return False, "Donors cannot claim their own food donations."
    if donation.get("status") != "available":
        return False, f"Listing cannot be claimed because it is currently '{donation.get('status')}'."

    deadline = donation.get("pickup_deadline")
    if deadline and deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if deadline and deadline <= datetime.now(timezone.utc):
        return False, "This donation has expired because the pickup deadline has passed."

    return True, None


def validate_collection_action(donation, user_id, user_role):
    """Verifies that only the claimant can confirm pickup."""
    if user_role != "receiver":
        return False, "Only receivers can confirm pickup."
    if not donation:
        return False, "Donation not found."
    if donation.get("status") != "claimed":
        return False, f"Cannot confirm collection: status is '{donation.get('status')}', expected 'claimed'."

    claim = donation.get("claim") or {}
    if str(claim.get("receiver_id")) != str(user_id):
        return False, "Only the receiver who claimed this donation can confirm its collection."

    return True, None


def validate_donor_ownership(donation, user_id, permitted_statuses=None):
    """Checks donor ownership and allowable status."""
    if not donation:
        return False, "Donation not found."
    if str(donation.get("donor_id")) != str(user_id):
        return False, "You do not have permission to modify or delete this donation."
    if permitted_statuses and donation.get("status") not in permitted_statuses:
        return False, f"Action not permitted when donation status is '{donation.get('status')}'."

    return True, None
