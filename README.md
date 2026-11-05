# FoodLoop — Surplus Food Rescue & Redistribution Platform

> **CSE494: Intelligent NoSQL Databases — B.Tech CSE Course Project**  
> Developed with **Python 3.12+**, **Flask**, and **MongoDB Atlas** using **PyMongo**.

---

## 1. Problem Statement & Real-World Purpose

Every year, millions of metric tons of edible food are discarded by college canteens, bakeries, hostels, banquet halls, and restaurants while vulnerable urban populations face nutritional insecurity. Surplus food is highly time-sensitive: if not matched and collected before its safe consumption window lapses, it ends up in landfills.

**FoodLoop** is a sustainability-focused food rescue platform designed to bridge this gap:
- **Donors** (canteens, bakeries, caterers) publish available surplus batches specifying quantity (servings), allergen tags, preparation time, and strict pickup deadlines.
- **Receivers** (NGOs, community kitchens, shelters) discover nearby donations, conditionally claim items, and verify pickup.
- **Academic NoSQL Core:** The platform is built around **MongoDB** to demonstrate document modeling, JSON Schema validation, embedding vs. referencing, atomic state transitions, compound and text indexing, query plan inspection (`explain()`), and multi-stage aggregation pipelines.

---

## 2. Key Features

- **Responsive Sustainability UI:** Forest green and warm cream aesthetic with status badges, dynamic cards, and Chart.js dashboards.
- **Role-Based Workflows:** Distinct donor dashboard (listing management, cancel, delete) and receiver dashboard (active claims, pickup confirmation).
- **Atomic Concurrency Protection:** Race-condition-free single-document updates prevent double claiming of food.
- **Full-Text & Compound Search:** Discover listings by category, city, dietary preferences, or keyword search.
- **Audit History Log:** Every status change is appended to an embedded chronological array.
- **Real-Time Aggregation Reports:** 5 complex aggregation pipelines calculated directly inside MongoDB.
- **Database Insights Page:** Real-time collection stats, schema validator breakdown, and live query execution plan comparisons (`IXSCAN` vs `COLLSCAN`).

---

## 3. Technology Stack

- **Backend:** Python 3.12+, Flask 3.1+
- **Database & Driver:** MongoDB Atlas / Local MongoDB, PyMongo 4.19+
- **Security:** Werkzeug password hashing, Flask-WTF CSRF protection, HTTP-only session cookies
- **Frontend:** Semantic HTML5, Custom CSS3, Vanilla JavaScript, Chart.js 4.4
- **Testing & Deployment:** pytest, Gunicorn, Render (`render.yaml`)

*All MongoDB operations are implemented purely in Python using PyMongo. No external Node.js or JavaScript database scripts are used.*

---

## 4. Project File Structure

```
foodloop/
├── app.py                      # Flask routes, sessions, permissions, error handlers
├── db.py                       # PyMongo MongoClient singleton, timeouts, timezone utilities
├── validators.py               # Input validation and business authorization logic
├── donation_service.py         # PyMongo CRUD, atomic claiming, status history updates
├── analytics_service.py        # 5 Native MongoDB aggregation pipelines
├── performance_analysis.py     # explain() execution plans (IXSCAN vs COLLSCAN analysis)
├── init_db.py                  # Schema validation setup and index initialization script
├── seed_data.py                # Idempotent 30-record synthetic demonstration dataset
├── requirements.txt            # Minimal, compatible production dependencies
├── .env.example                # Template for environment variables
├── .gitignore                  # Git exclusion rules
├── .python-version             # Python version pin (3.12.2)
├── render.yaml                 # Deployment blueprint for Render hosting
├── README.md                   # Project documentation and viva preparation guide
│
├── templates/
│   ├── base.html               # Base layout, navbar, flash messages, footer
│   ├── index.html              # Landing page with live impact statistics
│   ├── login.html              # Authentication login form
│   ├── register.html           # User registration (donor / receiver)
│   ├── donations.html          # Discovery page with filters and text search
│   ├── donation_form.html      # Create / Edit surplus food listing form
│   ├── donor_dashboard.html    # Donor management portal
│   ├── receiver_dashboard.html # Receiver claim and pickup portal
│   ├── analytics.html          # Chart.js dashboards powered by MongoDB aggregations
│   ├── database_insights.html  # Academic NoSQL insights & explain() metrics
│   ├── 404.html                # Not found error page
│   └── 500.html                # Server error page
│
├── static/
│   ├── css/
│   │   └── style.css           # Clean sustainability-themed styling
│   └── js/
│       └── main.js             # UI helpers, flash timeouts, Chart.js renderers
│
└── tests/
    └── test_validators.py      # Automated pytest unit test suite
```

---

## 5. MongoDB Database Design

The database `foodloop` contains two core collections: `users` and `donations`.

### Collection: `users`
| Field | BSON Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique user identifier |
| `name` | string | Full name or representative name |
| `email` | string | Unique email address (indexed) |
| `password_hash` | string | Werkzeug hashed password |
| `role` | string | `"donor"` or `"receiver"` |
| `organization_name`| string / null | Optional entity or NGO name |
| `city` | string | Base operating city |
| `created_at` | date | UTC timestamp |

### Collection: `donations`
| Field | BSON Type | Description |
|---|---|---|
| `_id` | ObjectId | Unique donation identifier |
| `donor_id` | ObjectId | Referenced `_id` in `users` (Referencing) |
| `food_name` | string | Name / description of food |
| `category` | string | `prepared_meal`, `bakery`, `fruits_vegetables`, `packaged_food`, `other` |
| `servings` | int | Quantity in human servings (&ge; 1) |
| `dietary_type` | string | `vegetarian`, `non_vegetarian`, `vegan`, `other` |
| `allergens` | array of strings | Allergen tags (e.g., `["dairy", "gluten"]`) |
| `prepared_at` | date | Preparation timestamp |
| `pickup_deadline` | date | Expiry deadline |
| `pickup_location` | object | Embedded document: `{"area": string, "city": string}` |
| `status` | string | `available`, `claimed`, `collected`, `cancelled`, `expired` |
| `claim` | object / null | Embedded document: `{"receiver_id": ObjectId, "claimed_at": date}` |
| `status_history` | array of objects| Embedded audit log `[{old_status, new_status, changed_at, changed_by, note}]` |
| `created_at` / `updated_at` | date | Timestamps |
| `collected_at` | date / null | Timestamp when collection was confirmed |

---

## 6. Embedding vs Referencing Demonstration

- **Referencing (`donor_id`, `claim.receiver_id`):**  
  Used to link donations to the `users` collection. Storing user profiles once prevents repetitive data duplication across hundreds of donation records. When user profile information (e.g., organization name or contact) updates, only one document in `users` is updated.
- **Embedding (`pickup_location`, `claim`, `status_history`):**  
  - `pickup_location` is fixed per donation and always retrieved alongside the food card, eliminating costly joins.
  - `claim` contains the active receiver link and claim time directly on the donation document, enabling **atomic conditional single-document updates**.
  - `status_history` is a 1-to-few bounded array (averaging 3–5 transitions per donation lifecycle), well within MongoDB's 16MB document limit.

---

## 7. MongoDB Schema Validation (`init_db.py`)

Configured using `$jsonSchema` inside `init_db.py`:
- Validates required fields, enum constraints (roles, categories, dietary types, statuses).
- Enforces BSON types (`objectId`, `date`, `int`, `string`, `array`, `object`).
- Rejects negative servings (`minimum: 1`).
- Validates structure of embedded location, claims, and status history entries.
- Applied via `db.create_collection(validator=...)` or `db.command({'collMod': ..., 'validator': ...})`.

---

## 8. Atomic Claiming & Status Management

To prevent race conditions where multiple receivers claim the same food simultaneously, FoodLoop executes a conditional atomic update via `update_one()`:

```python
filter_query = {
    "_id": donation_id,
    "status": "available",
    "pickup_deadline": {"$gt": now_utc},
    "donor_id": {"$ne": receiver_id}  # Donors cannot claim own listings
}
update_doc = {
    "$set": {
        "status": "claimed",
        "claim": {"receiver_id": receiver_id, "claimed_at": now_utc},
        "updated_at": now_utc
    },
    "$push": {
        "status_history": {
            "old_status": "available",
            "new_status": "claimed",
            "changed_at": now_utc,
            "changed_by": receiver_id,
            "note": "Listing claimed by receiver for pickup."
        }
    }
}
result = db.donations.update_one(filter_query, update_doc)
```
If two requests arrive concurrently, MongoDB locks the single document, succeeds for the first request (`matched_count == 1`), and fails safely for the second (`matched_count == 0`), preventing double-allocation without database deadlocks.

---

## 9. MongoDB Indexes

Created and managed via PyMongo in `init_db.py`:

1. **`users.email` (Unique):**  
   `db.users.create_index([("email", 1)], unique=True)`  
   *Enforces unique accounts at the database engine level.*
2. **`donations.status` + `donations.pickup_deadline` (Compound):**  
   `db.donations.create_index([("status", 1), ("pickup_deadline", 1)])`  
   *Optimizes the discovery query and lazy expiration filter.*
3. **`donations.donor_id` + `donations.created_at` (Compound):**  
   `db.donations.create_index([("donor_id", 1), ("created_at", -1)])`  
   *Accelerates Donor Dashboard queries retrieving user listings sorted by newest.*
4. **`donations.pickup_location.city` + `donations.status` (Compound):**  
   `db.donations.create_index([("pickup_location.city", 1), ("status", 1)])`  
   *Accelerates geographic filtering on the embedded location subfield.*
5. **`donations.food_name` (Text Index):**  
   `db.donations.create_index([("food_name", "text")])`  
   *Enables natural language `$text` search queries across food titles.*

---

## 10. The 5 Required Aggregation Pipelines (`analytics_service.py`)

All computations execute inside MongoDB using `donations.aggregate(...)`:

1. **Report 1: Collected Servings by Category**  
   Stages: `$match` (status == "collected") &rarr; `$group` (by category, summing servings & count) &rarr; `$sort` (total servings desc).
2. **Report 2: Donations by Status**  
   Stages: `$group` (by status, summing count) &rarr; `$sort` (by count desc).
3. **Report 3: Top Contributing Donors**  
   Stages: `$match` (status == "collected") &rarr; `$group` (by donor_id) &rarr; `$sort` &rarr; `$limit` (5) &rarr; `$lookup` (from users) &rarr; `$unwind` &rarr; `$project`.
4. **Report 4: Monthly Collection Trends**  
   Stages: `$match` (status == "collected") &rarr; `$group` (by `$dateToString: {format: "%Y-%m", date: "$collected_at"}`) &rarr; `$sort` (chronological by month).
5. **Report 5: Finalized Collection Rate**  
   Stages: `$match` (status in ["collected", "cancelled", "expired"]) &rarr; `$group` (conditional sum of collected vs total finalized) &rarr; `$project` (`collection_rate_percent = (collected / total_finalized) * 100`).

---

## 11. Local Setup & Execution Guide

### Step 1: Clone or Open Workspace
```bash
cd c:\Users\V\Downloads\foodloop
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your MongoDB connection string:
```ini
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
DB_NAME=foodloop
SECRET_KEY=foodloop-cse494-secret-key-super-safe
PORT=5000
```

### Step 4: Initialize Collections, Schema Validation, and Indexes
```bash
python init_db.py
```

### Step 5: Load Synthetic Demonstration Data (Optional but Recommended)
```bash
python seed_data.py
```
*Inserts 30 realistic donations and 7 demo users across multiple months. It is idempotent and safe to run multiple times.*

### Step 6: Run Automated Tests
```bash
python -m pytest tests/
```

### Step 7: Launch Local Web Server
```bash
python app.py
```
Open **`http://localhost:5000`** in your browser.

---

## 12. Deployment to Render

1. **Create MongoDB Atlas Cluster:**
   - Create a free shared cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas).
   - In **Network Access**, add `0.0.0.0/0` (allow access from anywhere) so Render servers can connect.
   - In **Database Access**, create a user with read/write privileges on `foodloop`.
2. **Push Repository to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit of FoodLoop platform"
   git remote add origin https://github.com/YOUR_USERNAME/foodloop.git
   git push -u origin main
   ```
3. **Deploy on Render:**
   - Log in to [Render](https://render.com/) and click **New &rarr; Web Service**.
   - Connect your GitHub repository.
   - Set:
     - **Runtime:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app`
   - Add Environment Variables in the Render dashboard:
     - `MONGO_URI`: Your MongoDB Atlas connection URI.
     - `DB_NAME`: `foodloop`
     - `SECRET_KEY`: A random secret key string.
4. **Initialize DB on Atlas:**
   - Run `python init_db.py` and `python seed_data.py` once locally pointing to your Atlas `MONGO_URI`.

---

## 13. Viva Voce Preparation Guide (CSE494)

| Question | Short Viva Answer |
|---|---|
| **Why MongoDB over relational SQL for FoodLoop?** | Food listings are dynamic and benefit from polymorphic attributes (allergen arrays, dietary tags, flexible location payloads). Subdocuments allow atomic claiming and embedded chronological status histories without multi-table locks. |
| **How is double claiming avoided?** | Through single-document conditional atomic updates (`update_one`) with an exact filter condition (`status == "available"`, `pickup_deadline > now`). MongoDB executes this as an atomic write, preventing race conditions. |
| **What is the difference between IXSCAN and COLLSCAN?** | `COLLSCAN` reads every document in a collection sequentially ($O(N)$), while `IXSCAN` traverses a balanced B-Tree index ($O(\log N)$). On our Database Insights page, PyMongo's `explain()` shows `totalDocsExamined` dropping significantly during index usage. |
| **Why not store donor details inside every donation document?** | That would cause uncontrolled redundancy. If a donor updates their phone number or canteen name, thousands of past records would need updating. Referencing `donor_id` maintains normalization for user entities while `$lookup` joins them on demand. |
| **What do the aggregation stages `$match`, `$group`, and `$lookup` do?** | `$match` filters documents (similar to SQL `WHERE`), `$group` aggregates rows by a key and calculates metrics (`$sum`, `$avg`), and `$lookup` performs a left outer join with another collection. |
