import os
import functools
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash

from db import (
    get_users_collection, check_connection, utc_now, ist_to_utc, utc_to_ist
)
from validators import (
    validate_registration, validate_donation_input, validate_donor_ownership
)
import donation_service
import analytics_service
import performance_analysis

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "foodloop-super-secret-key-cse494")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

csrf = CSRFProtect(app)


# --- Template Filters & Context ---

@app.template_filter("ist_format")
def ist_format(dt, fmt="%d %b %Y, %I:%M %p"):
    """Formats UTC datetime into IST string."""
    if not dt:
        return "N/A"
    return utc_to_ist(dt).strftime(fmt)


@app.template_filter("status_badge_class")
def status_badge_class(status):
    """Maps status to CSS badge class."""
    mapping = {
        "available": "badge-available",
        "claimed": "badge-claimed",
        "collected": "badge-collected",
        "cancelled": "badge-cancelled",
        "expired": "badge-expired"
    }
    return mapping.get(status, "badge-default")


@app.context_processor
def inject_global_vars():
    """Provides current_user, utc_now, and csrf_token across templates."""
    user = None
    if "user_id" in session:
        user = {
            "id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
            "role": session.get("user_role"),
            "organization": session.get("user_org"),
            "city": session.get("user_city")
        }
    return {
        "current_user": user,
        "now": utc_now(),
        "csrf_token": generate_csrf
    }


# --- Auth Helpers ---

def login_required(view_func):
    """Requires an authenticated session."""
    @functools.wraps(view_func)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.path))
        return view_func(**kwargs)
    return wrapped_view


def role_required(required_role):
    """Requires a specific role ('donor' or 'receiver')."""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped_view(**kwargs):
            if "user_id" not in session:
                flash("Please log in first.", "warning")
                return redirect(url_for("login", next=request.path))
            if session.get("user_role") != required_role:
                flash(f"Access restricted to {required_role.capitalize()}s only.", "danger")
                return redirect(url_for("index"))
            return view_func(**kwargs)
        return wrapped_view
    return decorator


# --- Routes ---

@app.route("/")
def index():
    """Landing page with live platform statistics."""
    try:
        stats = analytics_service.get_platform_summary()
        recent_donations = analytics_service.get_approaching_deadline_donations(limit=6)
        conn_ok, _ = check_connection()
    except Exception:
        stats = {"total_donations": 0, "collected_servings": 0, "available_servings": 0, "donor_count": 0, "receiver_count": 0}
        recent_donations = []
        conn_ok = False

    return render_template("index.html", stats=stats, recent_donations=recent_donations, conn_ok=conn_ok)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles user registration."""
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "password": request.form.get("password"),
            "role": request.form.get("role"),
            "organization_name": request.form.get("organization_name"),
            "city": request.form.get("city")
        }

        is_valid, errors = validate_registration(data)
        if not is_valid:
            for err in errors:
                flash(err, "danger")
            return render_template("register.html", form_data=data)

        users_col = get_users_collection()
        if users_col.find_one({"email": data["email"].strip().lower()}):
            flash("An account with this email already exists. Please log in.", "danger")
            return render_template("register.html", form_data=data)

        new_user = {
            "name": data["name"].strip(),
            "email": data["email"].strip().lower(),
            "password_hash": generate_password_hash(data["password"]),
            "role": data["role"].strip().lower(),
            "organization_name": data["organization_name"].strip() if data["organization_name"] else None,
            "city": data["city"].strip(),
            "created_at": utc_now()
        }

        try:
            result = users_col.insert_one(new_user)
            session["user_id"] = str(result.inserted_id)
            session["user_name"] = new_user["name"]
            session["user_email"] = new_user["email"]
            session["user_role"] = new_user["role"]
            session["user_org"] = new_user["organization_name"]
            session["user_city"] = new_user["city"]

            flash(f"Welcome to FoodLoop, {new_user['name']}!", "success")
            return redirect(url_for("donor_dashboard" if new_user["role"] == "donor" else "receiver_dashboard"))
        except Exception as e:
            flash(f"Registration error: {str(e)}", "danger")

    return render_template("register.html", form_data={})


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles session login."""
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Please enter both email and password.", "warning")
            return render_template("login.html")

        try:
            user = get_users_collection().find_one({"email": email})
            if user and check_password_hash(user.get("password_hash", ""), password):
                session["user_id"] = str(user["_id"])
                session["user_name"] = user.get("name")
                session["user_email"] = user.get("email")
                session["user_role"] = user.get("role")
                session["user_org"] = user.get("organization_name")
                session["user_city"] = user.get("city")

                flash(f"Welcome back, {user.get('name')}!", "success")
                next_url = request.args.get("next")
                if next_url and next_url.startswith("/"):
                    return redirect(next_url)
                return redirect(url_for("donor_dashboard" if user.get("role") == "donor" else "receiver_dashboard"))
            else:
                flash("Invalid email or password.", "danger")
        except Exception as e:
            flash(f"Login error: {str(e)}", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clears user session."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/donations")
def discover_donations():
    """Browses active donations with category, city, dietary, and text search filters."""
    category = request.args.get("category", "all")
    city = request.args.get("city", "").strip()
    dietary_type = request.args.get("dietary_type", "all")
    search_query = request.args.get("q", "").strip()

    try:
        listings = donation_service.list_available_donations(
            category=category, city=city, dietary_type=dietary_type, search_query=search_query
        )
    except Exception as e:
        flash(f"Error loading donations: {str(e)}", "danger")
        listings = []

    return render_template(
        "donations.html",
        donations=listings,
        current_category=category,
        current_city=city,
        current_dietary=dietary_type,
        current_query=search_query
    )


@app.route("/donations/create", methods=["GET", "POST"])
@role_required("donor")
def create_donation():
    """Creates a new food donation listing."""
    if request.method == "POST":
        raw_data = {
            "food_name": request.form.get("food_name"),
            "category": request.form.get("category"),
            "servings": request.form.get("servings"),
            "dietary_type": request.form.get("dietary_type"),
            "allergens": request.form.get("allergens"),
            "prepared_at": ist_to_utc(request.form.get("prepared_at")),
            "pickup_deadline": ist_to_utc(request.form.get("pickup_deadline")),
            "area": request.form.get("area"),
            "city": request.form.get("city")
        }

        is_valid, cleaned, errors = validate_donation_input(raw_data, is_update=False)
        if not is_valid:
            for err in errors:
                flash(err, "danger")
            return render_template("donation_form.html", form_data=request.form, action="create")

        try:
            donation_service.create_donation(session["user_id"], cleaned)
            flash("Donation published successfully!", "success")
            return redirect(url_for("donor_dashboard"))
        except Exception as e:
            flash(f"Error publishing donation: {str(e)}", "danger")
            return render_template("donation_form.html", form_data=request.form, action="create")

    return render_template("donation_form.html", form_data={}, action="create")


@app.route("/donations/<donation_id>/edit", methods=["GET", "POST"])
@role_required("donor")
def edit_donation(donation_id):
    """Edits an existing available donation."""
    donation = donation_service.get_donation_by_id(donation_id)
    if not donation:
        abort(404)

    is_owner, err = validate_donor_ownership(donation, session["user_id"], permitted_statuses=["available"])
    if not is_owner:
        flash(err, "danger")
        return redirect(url_for("donor_dashboard"))

    if request.method == "POST":
        raw_data = {
            "food_name": request.form.get("food_name"),
            "category": request.form.get("category"),
            "servings": request.form.get("servings"),
            "dietary_type": request.form.get("dietary_type"),
            "allergens": request.form.get("allergens"),
            "prepared_at": ist_to_utc(request.form.get("prepared_at")),
            "pickup_deadline": ist_to_utc(request.form.get("pickup_deadline")),
            "area": request.form.get("area"),
            "city": request.form.get("city")
        }

        is_valid, cleaned, errors = validate_donation_input(raw_data, is_update=True)
        if not is_valid:
            for err in errors:
                flash(err, "danger")
            return render_template("donation_form.html", form_data=request.form, action="edit", donation=donation)

        success, msg = donation_service.update_donation(donation_id, session["user_id"], cleaned)
        flash(msg, "success" if success else "danger")
        return redirect(url_for("donor_dashboard"))

    prep_dt = utc_to_ist(donation.get("prepared_at"))
    dead_dt = utc_to_ist(donation.get("pickup_deadline"))
    form_data = {
        "food_name": donation.get("food_name"),
        "category": donation.get("category"),
        "servings": donation.get("servings"),
        "dietary_type": donation.get("dietary_type"),
        "allergens": ", ".join(donation.get("allergens", [])),
        "prepared_at": prep_dt.strftime("%Y-%m-%dT%H:%M") if prep_dt else "",
        "pickup_deadline": dead_dt.strftime("%Y-%m-%dT%H:%M") if dead_dt else "",
        "area": donation.get("pickup_location", {}).get("area", ""),
        "city": donation.get("pickup_location", {}).get("city", "")
    }
    return render_template("donation_form.html", form_data=form_data, action="edit", donation=donation)


@app.route("/donations/<donation_id>/cancel", methods=["POST"])
@role_required("donor")
def cancel_donation(donation_id):
    """Cancels a listing by its donor."""
    reason = request.form.get("reason", "Cancelled by donor.")
    success, msg = donation_service.cancel_donation(donation_id, session["user_id"], reason=reason)
    flash(msg, "info" if success else "danger")
    return redirect(url_for("donor_dashboard"))


@app.route("/donations/<donation_id>/delete", methods=["POST"])
@role_required("donor")
def delete_donation(donation_id):
    """Deletes an available or cancelled listing."""
    success, msg = donation_service.delete_donation(donation_id, session["user_id"])
    flash(msg, "success" if success else "danger")
    return redirect(url_for("donor_dashboard"))


@app.route("/donations/<donation_id>/claim", methods=["POST"])
@role_required("receiver")
def claim_donation(donation_id):
    """Atomic conditional claim by a receiver."""
    success, msg = donation_service.claim_donation_atomic(donation_id, session["user_id"])
    flash(msg, "success" if success else "danger")
    return redirect(url_for("receiver_dashboard" if success else "discover_donations"))


@app.route("/donations/<donation_id>/confirm_collection", methods=["POST"])
@role_required("receiver")
def confirm_collection(donation_id):
    """Confirms pickup of claimed donation."""
    success, msg = donation_service.confirm_collection(donation_id, session["user_id"])
    flash(msg, "success" if success else "danger")
    return redirect(url_for("receiver_dashboard"))


@app.route("/donor/dashboard")
@role_required("donor")
def donor_dashboard():
    """Donor dashboard for managing active listings."""
    my_listings = donation_service.get_donor_listings(session["user_id"])
    stats = {
        "total": len(my_listings),
        "available": sum(1 for d in my_listings if d.get("status") == "available"),
        "claimed": sum(1 for d in my_listings if d.get("status") == "claimed"),
        "collected": sum(1 for d in my_listings if d.get("status") == "collected"),
        "servings_rescued": sum(d.get("servings", 0) for d in my_listings if d.get("status") == "collected")
    }
    return render_template("donor_dashboard.html", listings=my_listings, stats=stats)


@app.route("/receiver/dashboard")
@role_required("receiver")
def receiver_dashboard():
    """Receiver dashboard for managing active claims and collections."""
    my_claims = donation_service.get_receiver_claims(session["user_id"])
    active_claims = [c for c in my_claims if c.get("status") == "claimed"]
    collected_history = [c for c in my_claims if c.get("status") == "collected"]
    available_recent = donation_service.list_available_donations()[:4]

    stats = {
        "active_claims": len(active_claims),
        "total_collected": len(collected_history),
        "servings_received": sum(c.get("servings", 0) for c in collected_history)
    }
    return render_template(
        "receiver_dashboard.html",
        active_claims=active_claims,
        collected_history=collected_history,
        available_recent=available_recent,
        stats=stats
    )


@app.route("/analytics")
def analytics():
    """Analytics dashboard powered by the 5 native MongoDB aggregations."""
    try:
        category_data = analytics_service.get_collected_servings_by_category()
        status_data = analytics_service.get_donations_by_status()
        top_donors = analytics_service.get_top_contributing_donors(limit=5)
        monthly_trends = analytics_service.get_monthly_collection_trends()
        rate_data = analytics_service.get_finalized_collection_rate()
        summary = analytics_service.get_platform_summary()
    except Exception as e:
        flash(f"Error loading analytics: {str(e)}", "danger")
        category_data, status_data, top_donors, monthly_trends = [], [], [], []
        rate_data = {"collection_rate_percent": 0.0, "total_finalized": 0}
        summary = {"total_donations": 0, "available_servings": 0, "collected_servings": 0}

    return render_template(
        "analytics.html",
        category_data=category_data,
        status_data=status_data,
        top_donors=top_donors,
        monthly_trends=monthly_trends,
        rate_data=rate_data,
        summary=summary
    )


@app.route("/database-insights")
@login_required
def database_insights():
    """Database insights page demonstrating indexes and explain() statistics."""
    try:
        db_stats = performance_analysis.get_database_statistics()
        query_analysis = performance_analysis.get_query_execution_analysis()
        conn_ok, conn_msg = check_connection()
    except Exception as e:
        db_stats, query_analysis = {"collections": [], "db_name": "foodloop"}, {}
        conn_ok, conn_msg = False, str(e)

    return render_template(
        "database_insights.html",
        db_stats=db_stats,
        query_analysis=query_analysis,
        conn_ok=conn_ok,
        conn_msg=conn_msg
    )


@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
