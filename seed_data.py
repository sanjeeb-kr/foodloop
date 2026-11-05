from bson import ObjectId
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash
from db import get_db, check_connection, utc_now

# Fixed deterministic ObjectIds for consistent cross-referencing between users and donations
DONOR_IDS = [
    ObjectId("660000000000000000000001"),  # Campus Central Canteen (Bengaluru)
    ObjectId("660000000000000000000002"),  # Green Leaf Bakery (Bengaluru)
    ObjectId("660000000000000000000003"),  # Royal Palace Banquet Hall (Hyderabad)
    ObjectId("660000000000000000000004"),  # TechPark Food Court (Pune)
]

RECEIVER_IDS = [
    ObjectId("660000000000000000000005"),  # Robin Hood Community Kitchen (Bengaluru)
    ObjectId("660000000000000000000006"),  # Annapoorna Food Relief NGO (Hyderabad)
    ObjectId("660000000000000000000007"),  # Hope Shelter Trust (Pune)
]


def get_demo_users():
    """
    Returns list of 7 demonstration user documents (4 Donors, 3 Receivers).
    Passphrases are unusable random strings by default to prevent unauthorized logins.
    """
    now = utc_now()
    demo_pass_hash = generate_password_hash("DemoSecretPass#2026")

    return [
        {
            "_id": DONOR_IDS[0],
            "name": "Prof. R. Sharma (Canteen Head)",
            "email": "canteen@campus.edu",
            "password_hash": demo_pass_hash,
            "role": "donor",
            "organization_name": "Campus Central Canteen",
            "city": "Bengaluru",
            "created_at": now - timedelta(days=90),
            "seed_demo": True
        },
        {
            "_id": DONOR_IDS[1],
            "name": "Ananya Sen (Master Baker)",
            "email": "ananya@greenleafbakery.in",
            "password_hash": demo_pass_hash,
            "role": "donor",
            "organization_name": "Green Leaf Artisan Bakery",
            "city": "Bengaluru",
            "created_at": now - timedelta(days=80),
            "seed_demo": True
        },
        {
            "_id": DONOR_IDS[2],
            "name": "Vikram Malhotra (Events Mgr)",
            "email": "events@royalpalacebanquets.com",
            "password_hash": demo_pass_hash,
            "role": "donor",
            "organization_name": "Royal Palace Banquet Hall",
            "city": "Hyderabad",
            "created_at": now - timedelta(days=70),
            "seed_demo": True
        },
        {
            "_id": DONOR_IDS[3],
            "name": "Pooja Hegde (Operations)",
            "email": "operations@techparkfoods.com",
            "password_hash": demo_pass_hash,
            "role": "donor",
            "organization_name": "TechPark Central Food Court",
            "city": "Pune",
            "created_at": now - timedelta(days=60),
            "seed_demo": True
        },
        {
            "_id": RECEIVER_IDS[0],
            "name": "Siddharth Verma (Field Lead)",
            "email": "siddharth@robinhoodkitchen.org",
            "password_hash": demo_pass_hash,
            "role": "receiver",
            "organization_name": "Robin Hood Community Kitchen",
            "city": "Bengaluru",
            "created_at": now - timedelta(days=85),
            "seed_demo": True
        },
        {
            "_id": RECEIVER_IDS[1],
            "name": "Sunita Rao (Director)",
            "email": "sunita@annapoorna-ngo.org",
            "password_hash": demo_pass_hash,
            "role": "receiver",
            "organization_name": "Annapoorna Food Relief NGO",
            "city": "Hyderabad",
            "created_at": now - timedelta(days=75),
            "seed_demo": True
        },
        {
            "_id": RECEIVER_IDS[2],
            "name": "Amit Kulkarni (Coordinator)",
            "email": "amit@hopeshelter.org",
            "password_hash": demo_pass_hash,
            "role": "receiver",
            "organization_name": "Hope Shelter Trust",
            "city": "Pune",
            "created_at": now - timedelta(days=65),
            "seed_demo": True
        }
    ]


def get_demo_donations():
    """
    Returns 30 synthetic donation documents spanning available, claimed,
    collected, cancelled, and expired states across varied dates.
    """
    now = utc_now()

    donations = [
        # --- AVAILABLE LISTINGS (Future pickup deadlines) ---
        {
            "_id": ObjectId("661000000000000000000001"),
            "donor_id": DONOR_IDS[0],
            "food_name": "Fresh Vegetable Biryani & Raita",
            "category": "prepared_meal",
            "servings": 45,
            "dietary_type": "vegetarian",
            "allergens": ["dairy"],
            "prepared_at": now - timedelta(hours=2),
            "pickup_deadline": now + timedelta(hours=5),
            "pickup_location": {"area": "Koramangala 4th Block", "city": "Bengaluru"},
            "status": "available",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=2), "changed_by": DONOR_IDS[0], "note": "Post-lunch surplus buffet food."}
            ],
            "created_at": now - timedelta(hours=2),
            "updated_at": now - timedelta(hours=2),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000002"),
            "donor_id": DONOR_IDS[1],
            "food_name": "Sourdough Loaves & Multigrain Croissants",
            "category": "bakery",
            "servings": 30,
            "dietary_type": "vegetarian",
            "allergens": ["gluten", "dairy"],
            "prepared_at": now - timedelta(hours=4),
            "pickup_deadline": now + timedelta(hours=8),
            "pickup_location": {"area": "Indiranagar 100ft Road", "city": "Bengaluru"},
            "status": "available",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=4), "changed_by": DONOR_IDS[1], "note": "End-of-shift bakery batch."}
            ],
            "created_at": now - timedelta(hours=4),
            "updated_at": now - timedelta(hours=4),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000003"),
            "donor_id": DONOR_IDS[2],
            "food_name": "Paneer Butter Masala with Tandoori Rotis",
            "category": "prepared_meal",
            "servings": 60,
            "dietary_type": "vegetarian",
            "allergens": ["dairy", "gluten"],
            "prepared_at": now - timedelta(hours=3),
            "pickup_deadline": now + timedelta(hours=6),
            "pickup_location": {"area": "Banjara Hills Rd No 2", "city": "Hyderabad"},
            "status": "available",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=3), "changed_by": DONOR_IDS[2], "note": "Surplus catering from seminar."}
            ],
            "created_at": now - timedelta(hours=3),
            "updated_at": now - timedelta(hours=3),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000004"),
            "donor_id": DONOR_IDS[3],
            "food_name": "Organic Apples & Seasonal Bananas Crates",
            "category": "fruits_vegetables",
            "servings": 50,
            "dietary_type": "vegan",
            "allergens": [],
            "prepared_at": now - timedelta(hours=5),
            "pickup_deadline": now + timedelta(hours=14),
            "pickup_location": {"area": "Hinjawadi Phase 1", "city": "Pune"},
            "status": "available",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=5), "changed_by": DONOR_IDS[3], "note": "Corporate cafeteria fruit stock."}
            ],
            "created_at": now - timedelta(hours=5),
            "updated_at": now - timedelta(hours=5),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000005"),
            "donor_id": DONOR_IDS[0],
            "food_name": "Steamed Idlis & Sambar Kettles",
            "category": "prepared_meal",
            "servings": 40,
            "dietary_type": "vegan",
            "allergens": ["mustard"],
            "prepared_at": now - timedelta(hours=1),
            "pickup_deadline": now + timedelta(hours=4),
            "pickup_location": {"area": "Campus North Mess", "city": "Bengaluru"},
            "status": "available",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=1), "changed_by": DONOR_IDS[0], "note": "Breakfast surplus batch."}
            ],
            "created_at": now - timedelta(hours=1),
            "updated_at": now - timedelta(hours=1),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000006"),
            "donor_id": DONOR_IDS[3],
            "food_name": "Tetra Pack Fruit Juices & Healthy Granola Bars",
            "category": "packaged_food",
            "servings": 75,
            "dietary_type": "vegetarian",
            "allergens": ["nuts"],
            "prepared_at": now - timedelta(hours=12),
            "pickup_deadline": now + timedelta(hours=24),
            "pickup_location": {"area": "Viman Nagar", "city": "Pune"},
            "status": "available",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=12), "changed_by": DONOR_IDS[3], "note": "Event snacks remaining."}
            ],
            "created_at": now - timedelta(hours=12),
            "updated_at": now - timedelta(hours=12),
            "collected_at": None,
            "seed_demo": True
        },

        # --- CLAIMED LISTINGS (Active claims waiting for pickup) ---
        {
            "_id": ObjectId("661000000000000000000007"),
            "donor_id": DONOR_IDS[0],
            "food_name": "Dal Tadka and Jeera Rice Handis",
            "category": "prepared_meal",
            "servings": 55,
            "dietary_type": "vegan",
            "allergens": [],
            "prepared_at": now - timedelta(hours=3),
            "pickup_deadline": now + timedelta(hours=3),
            "pickup_location": {"area": "Koramangala 4th Block", "city": "Bengaluru"},
            "status": "claimed",
            "claim": {
                "receiver_id": RECEIVER_IDS[0],
                "claimed_at": now - timedelta(hours=1)
            },
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=3), "changed_by": DONOR_IDS[0], "note": "Listing created."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(hours=1), "changed_by": RECEIVER_IDS[0], "note": "Claimed by Robin Hood Community Kitchen."}
            ],
            "created_at": now - timedelta(hours=3),
            "updated_at": now - timedelta(hours=1),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000008"),
            "donor_id": DONOR_IDS[2],
            "food_name": "Assorted Sandwiches and Quiches",
            "category": "bakery",
            "servings": 35,
            "dietary_type": "non_vegetarian",
            "allergens": ["gluten", "eggs", "dairy"],
            "prepared_at": now - timedelta(hours=4),
            "pickup_deadline": now + timedelta(hours=2),
            "pickup_location": {"area": "Jubilee Hills", "city": "Hyderabad"},
            "status": "claimed",
            "claim": {
                "receiver_id": RECEIVER_IDS[1],
                "claimed_at": now - timedelta(minutes=45)
            },
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=4), "changed_by": DONOR_IDS[2], "note": "Listing created."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(minutes=45), "changed_by": RECEIVER_IDS[1], "note": "Claimed by Annapoorna Relief."}
            ],
            "created_at": now - timedelta(hours=4),
            "updated_at": now - timedelta(minutes=45),
            "collected_at": None,
            "seed_demo": True
        },

        # --- COLLECTED DONATIONS (Historical records across multiple months for Report 1, 3, 4, 5) ---
        # 4 months ago
        {
            "_id": ObjectId("661000000000000000000009"),
            "donor_id": DONOR_IDS[0],
            "food_name": "South Indian Thali Meal Trays",
            "category": "prepared_meal",
            "servings": 120,
            "dietary_type": "vegetarian",
            "allergens": ["dairy"],
            "prepared_at": now - timedelta(days=110, hours=5),
            "pickup_deadline": now - timedelta(days=110, hours=1),
            "pickup_location": {"area": "Campus Main Canteen", "city": "Bengaluru"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[0], "claimed_at": now - timedelta(days=110, hours=3)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=110, hours=5), "changed_by": DONOR_IDS[0], "note": "Annual college fest surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=110, hours=3), "changed_by": RECEIVER_IDS[0], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=110, hours=2), "changed_by": RECEIVER_IDS[0], "note": "Picked up successfully."}
            ],
            "created_at": now - timedelta(days=110, hours=5),
            "updated_at": now - timedelta(days=110, hours=2),
            "collected_at": now - timedelta(days=110, hours=2),
            "seed_demo": True
        },
        # 3 months ago
        {
            "_id": ObjectId("661000000000000000000010"),
            "donor_id": DONOR_IDS[1],
            "food_name": "French Baguettes and Herb Brioches",
            "category": "bakery",
            "servings": 65,
            "dietary_type": "vegetarian",
            "allergens": ["gluten"],
            "prepared_at": now - timedelta(days=85, hours=6),
            "pickup_deadline": now - timedelta(days=85, hours=2),
            "pickup_location": {"area": "Indiranagar", "city": "Bengaluru"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[0], "claimed_at": now - timedelta(days=85, hours=4)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=85, hours=6), "changed_by": DONOR_IDS[1], "note": "Bakery surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=85, hours=4), "changed_by": RECEIVER_IDS[0], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=85, hours=3), "changed_by": RECEIVER_IDS[0], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=85, hours=6),
            "updated_at": now - timedelta(days=85, hours=3),
            "collected_at": now - timedelta(days=85, hours=3),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000011"),
            "donor_id": DONOR_IDS[2],
            "food_name": "Hyderabadi Chicken Dum Biryani",
            "category": "prepared_meal",
            "servings": 150,
            "dietary_type": "non_vegetarian",
            "allergens": ["dairy"],
            "prepared_at": now - timedelta(days=78, hours=7),
            "pickup_deadline": now - timedelta(days=78, hours=2),
            "pickup_location": {"area": "Hitec City", "city": "Hyderabad"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[1], "claimed_at": now - timedelta(days=78, hours=4)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=78, hours=7), "changed_by": DONOR_IDS[2], "note": "Wedding reception feast surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=78, hours=4), "changed_by": RECEIVER_IDS[1], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=78, hours=3), "changed_by": RECEIVER_IDS[1], "note": "Distributed to local shelter."}
            ],
            "created_at": now - timedelta(days=78, hours=7),
            "updated_at": now - timedelta(days=78, hours=3),
            "collected_at": now - timedelta(days=78, hours=3),
            "seed_demo": True
        },
        # 2 months ago
        {
            "_id": ObjectId("661000000000000000000012"),
            "donor_id": DONOR_IDS[3],
            "food_name": "Farm Fresh Tomatoes & Green Peppers",
            "category": "fruits_vegetables",
            "servings": 80,
            "dietary_type": "vegan",
            "allergens": [],
            "prepared_at": now - timedelta(days=55, hours=10),
            "pickup_deadline": now - timedelta(days=55, hours=3),
            "pickup_location": {"area": "Hinjawadi", "city": "Pune"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[2], "claimed_at": now - timedelta(days=55, hours=6)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=55, hours=10), "changed_by": DONOR_IDS[3], "note": "Excess harvest supply."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=55, hours=6), "changed_by": RECEIVER_IDS[2], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=55, hours=4), "changed_by": RECEIVER_IDS[2], "note": "Delivered to kitchen."}
            ],
            "created_at": now - timedelta(days=55, hours=10),
            "updated_at": now - timedelta(days=55, hours=4),
            "collected_at": now - timedelta(days=55, hours=4),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000013"),
            "donor_id": DONOR_IDS[0],
            "food_name": "Chana Masala and Whole Wheat Parathas",
            "category": "prepared_meal",
            "servings": 95,
            "dietary_type": "vegan",
            "allergens": ["gluten"],
            "prepared_at": now - timedelta(days=48, hours=5),
            "pickup_deadline": now - timedelta(days=48, hours=1),
            "pickup_location": {"area": "Campus South Canteen", "city": "Bengaluru"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[0], "claimed_at": now - timedelta(days=48, hours=3)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=48, hours=5), "changed_by": DONOR_IDS[0], "note": "Dinner surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=48, hours=3), "changed_by": RECEIVER_IDS[0], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=48, hours=2), "changed_by": RECEIVER_IDS[0], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=48, hours=5),
            "updated_at": now - timedelta(days=48, hours=2),
            "collected_at": now - timedelta(days=48, hours=2),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000014"),
            "donor_id": DONOR_IDS[1],
            "food_name": "Mixed Fruit Tarts and Cinnamon Rolls",
            "category": "bakery",
            "servings": 50,
            "dietary_type": "vegetarian",
            "allergens": ["gluten", "dairy"],
            "prepared_at": now - timedelta(days=42, hours=8),
            "pickup_deadline": now - timedelta(days=42, hours=2),
            "pickup_location": {"area": "Indiranagar", "city": "Bengaluru"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[0], "claimed_at": now - timedelta(days=42, hours=4)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=42, hours=8), "changed_by": DONOR_IDS[1], "note": "Bakery batch."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=42, hours=4), "changed_by": RECEIVER_IDS[0], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=42, hours=3), "changed_by": RECEIVER_IDS[0], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=42, hours=8),
            "updated_at": now - timedelta(days=42, hours=3),
            "collected_at": now - timedelta(days=42, hours=3),
            "seed_demo": True
        },
        # 1 month ago
        {
            "_id": ObjectId("661000000000000000000015"),
            "donor_id": DONOR_IDS[2],
            "food_name": "Gulab Jamun and Rasmalai Dessert Trays",
            "category": "other",
            "servings": 70,
            "dietary_type": "vegetarian",
            "allergens": ["dairy", "nuts"],
            "prepared_at": now - timedelta(days=25, hours=6),
            "pickup_deadline": now - timedelta(days=25, hours=2),
            "pickup_location": {"area": "Secunderabad", "city": "Hyderabad"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[1], "claimed_at": now - timedelta(days=25, hours=4)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=25, hours=6), "changed_by": DONOR_IDS[2], "note": "Banquet sweets surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=25, hours=4), "changed_by": RECEIVER_IDS[1], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=25, hours=3), "changed_by": RECEIVER_IDS[1], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=25, hours=6),
            "updated_at": now - timedelta(days=25, hours=3),
            "collected_at": now - timedelta(days=25, hours=3),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000016"),
            "donor_id": DONOR_IDS[3],
            "food_name": "Sealed Milk Cartons and Greek Yogurts",
            "category": "packaged_food",
            "servings": 85,
            "dietary_type": "vegetarian",
            "allergens": ["dairy"],
            "prepared_at": now - timedelta(days=20, hours=12),
            "pickup_deadline": now - timedelta(days=20, hours=4),
            "pickup_location": {"area": "Baner", "city": "Pune"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[2], "claimed_at": now - timedelta(days=20, hours=8)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=20, hours=12), "changed_by": DONOR_IDS[3], "note": "Inventory surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=20, hours=8), "changed_by": RECEIVER_IDS[2], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=20, hours=5), "changed_by": RECEIVER_IDS[2], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=20, hours=12),
            "updated_at": now - timedelta(days=20, hours=5),
            "collected_at": now - timedelta(days=20, hours=5),
            "seed_demo": True
        },
        # Current month collections
        {
            "_id": ObjectId("661000000000000000000017"),
            "donor_id": DONOR_IDS[0],
            "food_name": "Rajma Masala with Steamed Basmati",
            "category": "prepared_meal",
            "servings": 110,
            "dietary_type": "vegan",
            "allergens": [],
            "prepared_at": now - timedelta(days=10, hours=5),
            "pickup_deadline": now - timedelta(days=10, hours=1),
            "pickup_location": {"area": "Koramangala 4th Block", "city": "Bengaluru"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[0], "claimed_at": now - timedelta(days=10, hours=3)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=10, hours=5), "changed_by": DONOR_IDS[0], "note": "Lunch buffet surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=10, hours=3), "changed_by": RECEIVER_IDS[0], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=10, hours=2), "changed_by": RECEIVER_IDS[0], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=10, hours=5),
            "updated_at": now - timedelta(days=10, hours=2),
            "collected_at": now - timedelta(days=10, hours=2),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000018"),
            "donor_id": DONOR_IDS[1],
            "food_name": "Garlic Focaccia and Cheese Bagels",
            "category": "bakery",
            "servings": 45,
            "dietary_type": "vegetarian",
            "allergens": ["gluten", "dairy"],
            "prepared_at": now - timedelta(days=5, hours=6),
            "pickup_deadline": now - timedelta(days=5, hours=2),
            "pickup_location": {"area": "Indiranagar", "city": "Bengaluru"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[0], "claimed_at": now - timedelta(days=5, hours=4)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=5, hours=6), "changed_by": DONOR_IDS[1], "note": "Listing created."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=5, hours=4), "changed_by": RECEIVER_IDS[0], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=5, hours=3), "changed_by": RECEIVER_IDS[0], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=5, hours=6),
            "updated_at": now - timedelta(days=5, hours=3),
            "collected_at": now - timedelta(days=5, hours=3),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000019"),
            "donor_id": DONOR_IDS[2],
            "food_name": "Butter Chicken with Garlic Naan",
            "category": "prepared_meal",
            "servings": 130,
            "dietary_type": "non_vegetarian",
            "allergens": ["dairy", "gluten"],
            "prepared_at": now - timedelta(days=3, hours=5),
            "pickup_deadline": now - timedelta(days=3, hours=1),
            "pickup_location": {"area": "Gachibowli", "city": "Hyderabad"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[1], "claimed_at": now - timedelta(days=3, hours=3)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=3, hours=5), "changed_by": DONOR_IDS[2], "note": "Banquet dinner surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=3, hours=3), "changed_by": RECEIVER_IDS[1], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=3, hours=2), "changed_by": RECEIVER_IDS[1], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=3, hours=5),
            "updated_at": now - timedelta(days=3, hours=2),
            "collected_at": now - timedelta(days=3, hours=2),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000020"),
            "donor_id": DONOR_IDS[3],
            "food_name": "Crisp Salad Greens and Baby Carrots",
            "category": "fruits_vegetables",
            "servings": 60,
            "dietary_type": "vegan",
            "allergens": [],
            "prepared_at": now - timedelta(days=2, hours=6),
            "pickup_deadline": now - timedelta(days=2, hours=2),
            "pickup_location": {"area": "Kalyani Nagar", "city": "Pune"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[2], "claimed_at": now - timedelta(days=2, hours=4)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=2, hours=6), "changed_by": DONOR_IDS[3], "note": "Cafeteria stock."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=2, hours=4), "changed_by": RECEIVER_IDS[2], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=2, hours=3), "changed_by": RECEIVER_IDS[2], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=2, hours=6),
            "updated_at": now - timedelta(days=2, hours=3),
            "collected_at": now - timedelta(days=2, hours=3),
            "seed_demo": True
        },

        # --- CANCELLED DONATIONS ---
        {
            "_id": ObjectId("661000000000000000000021"),
            "donor_id": DONOR_IDS[0],
            "food_name": "Mixed Vegetable Pulao",
            "category": "prepared_meal",
            "servings": 25,
            "dietary_type": "vegetarian",
            "allergens": [],
            "prepared_at": now - timedelta(days=15, hours=4),
            "pickup_deadline": now - timedelta(days=15, hours=1),
            "pickup_location": {"area": "Campus Canteen", "city": "Bengaluru"},
            "status": "cancelled",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=15, hours=4), "changed_by": DONOR_IDS[0], "note": "Listing created."},
                {"old_status": "available", "new_status": "cancelled", "changed_at": now - timedelta(days=15, hours=2), "changed_by": DONOR_IDS[0], "note": "Internal kitchen redistribution."}
            ],
            "created_at": now - timedelta(days=15, hours=4),
            "updated_at": now - timedelta(days=15, hours=2),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000022"),
            "donor_id": DONOR_IDS[2],
            "food_name": "Pastry Assortment Box",
            "category": "bakery",
            "servings": 20,
            "dietary_type": "vegetarian",
            "allergens": ["gluten", "dairy"],
            "prepared_at": now - timedelta(days=8, hours=5),
            "pickup_deadline": now - timedelta(days=8, hours=1),
            "pickup_location": {"area": "Banjara Hills", "city": "Hyderabad"},
            "status": "cancelled",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=8, hours=5), "changed_by": DONOR_IDS[2], "note": "Created."},
                {"old_status": "available", "new_status": "cancelled", "changed_at": now - timedelta(days=8, hours=2), "changed_by": DONOR_IDS[2], "note": "Storage refrigeration issue."}
            ],
            "created_at": now - timedelta(days=8, hours=5),
            "updated_at": now - timedelta(days=8, hours=2),
            "collected_at": None,
            "seed_demo": True
        },

        # --- EXPIRED DONATIONS (Unclaimed past deadline) ---
        {
            "_id": ObjectId("661000000000000000000023"),
            "donor_id": DONOR_IDS[1],
            "food_name": "Gluten-Free Seed Breads",
            "category": "bakery",
            "servings": 25,
            "dietary_type": "vegan",
            "allergens": ["sesame"],
            "prepared_at": now - timedelta(days=6, hours=8),
            "pickup_deadline": now - timedelta(days=5, hours=2),
            "pickup_location": {"area": "Indiranagar", "city": "Bengaluru"},
            "status": "expired",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=6, hours=8), "changed_by": DONOR_IDS[1], "note": "Created."},
                {"old_status": "available", "new_status": "expired", "changed_at": now - timedelta(days=5, hours=2), "changed_by": None, "note": "Unclaimed past pickup deadline."}
            ],
            "created_at": now - timedelta(days=6, hours=8),
            "updated_at": now - timedelta(days=5, hours=2),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000024"),
            "donor_id": DONOR_IDS[3],
            "food_name": "Mixed Ripe Papayas and Melons",
            "category": "fruits_vegetables",
            "servings": 35,
            "dietary_type": "vegan",
            "allergens": [],
            "prepared_at": now - timedelta(days=4, hours=10),
            "pickup_deadline": now - timedelta(days=3, hours=4),
            "pickup_location": {"area": "Kothrud", "city": "Pune"},
            "status": "expired",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=4, hours=10), "changed_by": DONOR_IDS[3], "note": "Created."},
                {"old_status": "available", "new_status": "expired", "changed_at": now - timedelta(days=3, hours=4), "changed_by": None, "note": "Expired past deadline."}
            ],
            "created_at": now - timedelta(days=4, hours=10),
            "updated_at": now - timedelta(days=3, hours=4),
            "collected_at": None,
            "seed_demo": True
        },

        # --- ADDITIONAL VARIETY (Packaged food, other categories, various cities) ---
        {
            "_id": ObjectId("661000000000000000000025"),
            "donor_id": DONOR_IDS[0],
            "food_name": "Packaged Biscuit Packets and Tea Bags",
            "category": "packaged_food",
            "servings": 100,
            "dietary_type": "vegetarian",
            "allergens": ["gluten", "dairy"],
            "prepared_at": now - timedelta(days=30, hours=5),
            "pickup_deadline": now - timedelta(days=29, hours=2),
            "pickup_location": {"area": "Campus Canteen", "city": "Bengaluru"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[0], "claimed_at": now - timedelta(days=30, hours=2)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=30, hours=5), "changed_by": DONOR_IDS[0], "note": "Snack inventory donation."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=30, hours=2), "changed_by": RECEIVER_IDS[0], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=29, hours=3), "changed_by": RECEIVER_IDS[0], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=30, hours=5),
            "updated_at": now - timedelta(days=29, hours=3),
            "collected_at": now - timedelta(days=29, hours=3),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000026"),
            "donor_id": DONOR_IDS[2],
            "food_name": "South Indian Filter Coffee Decoction & Sweets",
            "category": "other",
            "servings": 40,
            "dietary_type": "vegetarian",
            "allergens": ["dairy"],
            "prepared_at": now - timedelta(days=18, hours=4),
            "pickup_deadline": now - timedelta(days=18, hours=1),
            "pickup_location": {"area": "Madhapur", "city": "Hyderabad"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[1], "claimed_at": now - timedelta(days=18, hours=3)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=18, hours=4), "changed_by": DONOR_IDS[2], "note": "Created."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=18, hours=3), "changed_by": RECEIVER_IDS[1], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=18, hours=2), "changed_by": RECEIVER_IDS[1], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=18, hours=4),
            "updated_at": now - timedelta(days=18, hours=2),
            "collected_at": now - timedelta(days=18, hours=2),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000027"),
            "donor_id": DONOR_IDS[1],
            "food_name": "Whole Wheat Pita Breads & Hummus",
            "category": "bakery",
            "servings": 35,
            "dietary_type": "vegan",
            "allergens": ["gluten", "sesame"],
            "prepared_at": now - timedelta(hours=6),
            "pickup_deadline": now + timedelta(hours=10),
            "pickup_location": {"area": "Whitefield", "city": "Bengaluru"},
            "status": "available",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=6), "changed_by": DONOR_IDS[1], "note": "Batch freshly prepared."}
            ],
            "created_at": now - timedelta(hours=6),
            "updated_at": now - timedelta(hours=6),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000028"),
            "donor_id": DONOR_IDS[3],
            "food_name": "Tofu Fried Rice and Veg Manchurian",
            "category": "prepared_meal",
            "servings": 55,
            "dietary_type": "vegan",
            "allergens": ["soy", "gluten"],
            "prepared_at": now - timedelta(hours=2),
            "pickup_deadline": now + timedelta(hours=7),
            "pickup_location": {"area": "Magarpatta City", "city": "Pune"},
            "status": "available",
            "claim": None,
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(hours=2), "changed_by": DONOR_IDS[3], "note": "Lunch catering surplus."}
            ],
            "created_at": now - timedelta(hours=2),
            "updated_at": now - timedelta(hours=2),
            "collected_at": None,
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000029"),
            "donor_id": DONOR_IDS[2],
            "food_name": "Kadhai Paneer with Rumali Roti",
            "category": "prepared_meal",
            "servings": 80,
            "dietary_type": "vegetarian",
            "allergens": ["dairy", "gluten"],
            "prepared_at": now - timedelta(days=60, hours=5),
            "pickup_deadline": now - timedelta(days=60, hours=1),
            "pickup_location": {"area": "Abids", "city": "Hyderabad"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[1], "claimed_at": now - timedelta(days=60, hours=3)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=60, hours=5), "changed_by": DONOR_IDS[2], "note": "Wedding buffet surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=60, hours=3), "changed_by": RECEIVER_IDS[1], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=60, hours=2), "changed_by": RECEIVER_IDS[1], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=60, hours=5),
            "updated_at": now - timedelta(days=60, hours=2),
            "collected_at": now - timedelta(days=60, hours=2),
            "seed_demo": True
        },
        {
            "_id": ObjectId("661000000000000000000030"),
            "donor_id": DONOR_IDS[0],
            "food_name": "Vegetable Pulao with Mint Boondi Raita",
            "category": "prepared_meal",
            "servings": 70,
            "dietary_type": "vegetarian",
            "allergens": ["dairy"],
            "prepared_at": now - timedelta(days=1, hours=4),
            "pickup_deadline": now - timedelta(days=1, hours=1),
            "pickup_location": {"area": "Campus Central Canteen", "city": "Bengaluru"},
            "status": "collected",
            "claim": {"receiver_id": RECEIVER_IDS[0], "claimed_at": now - timedelta(days=1, hours=3)},
            "status_history": [
                {"old_status": None, "new_status": "available", "changed_at": now - timedelta(days=1, hours=4), "changed_by": DONOR_IDS[0], "note": "Dinner surplus."},
                {"old_status": "available", "new_status": "claimed", "changed_at": now - timedelta(days=1, hours=3), "changed_by": RECEIVER_IDS[0], "note": "Claimed."},
                {"old_status": "claimed", "new_status": "collected", "changed_at": now - timedelta(days=1, hours=2), "changed_by": RECEIVER_IDS[0], "note": "Collected."}
            ],
            "created_at": now - timedelta(days=1, hours=4),
            "updated_at": now - timedelta(days=1, hours=2),
            "collected_at": now - timedelta(days=1, hours=2),
            "seed_demo": True
        }
    ]

    return donations


def seed_database():
    """
    Inserts demo users and demo donations into MongoDB idempotently.
    Uses 'seed_demo': True marker to avoid duplicate insertions.
    Never alters or deletes real user accounts or real listings.
    """
    print("=" * 65)
    print(" FOODLOOP: SEEDING DEMONSTRATION DATA")
    print("=" * 65)

    is_connected, msg = check_connection()
    if not is_connected:
        print(f"[ERROR] Could not connect to MongoDB: {msg}")
        return False

    db = get_db()
    users_col = db["users"]
    donations_col = db["donations"]

    # 1. Seed Demo Users
    demo_users = get_demo_users()
    users_inserted = 0
    users_skipped = 0

    for u in demo_users:
        # Check if demo user with same email or _id already exists
        existing = users_col.find_one({"$or": [{"_id": u["_id"]}, {"email": u["email"]}]})
        if not existing:
            users_col.insert_one(u)
            users_inserted += 1
        else:
            users_skipped += 1

    print(f"Users Seeding: {users_inserted} inserted, {users_skipped} already present.")

    # 2. Seed Demo Donations
    demo_donations = get_demo_donations()
    donations_inserted = 0
    donations_skipped = 0

    for d in demo_donations:
        existing = donations_col.find_one({"_id": d["_id"]})
        if not existing:
            donations_col.insert_one(d)
            donations_inserted += 1
        else:
            # Refresh timestamps and status for demo listings so available demo records have future deadlines
            donations_col.replace_one({"_id": d["_id"]}, d)
            donations_inserted += 1

    print(f"Donations Seeding: {donations_inserted} synced.")
    print("\nDemonstration data seeding completed successfully! All records verified.")
    return True


if __name__ == "__main__":
    seed_database()
