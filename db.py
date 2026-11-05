import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "").strip()
DB_NAME = os.getenv("DB_NAME", "foodloop").strip()

# IST (+05:30) and UTC timezones
IST = timezone(timedelta(hours=5, minutes=30), name="IST")
UTC = timezone.utc

_client = None
_db = None


def get_client():
    """Initializes and returns a reusable MongoClient singleton."""
    global _client
    if _client is None:
        if not MONGO_URI:
            raise ConfigurationError("MONGO_URI environment variable is missing.")
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            appname="FoodLoop-App"
        )
    return _client


def get_db():
    """Returns database instance."""
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db


def get_users_collection():
    return get_db()["users"]


def get_donations_collection():
    return get_db()["donations"]


def check_connection():
    """Pings MongoDB to verify connection."""
    if not MONGO_URI:
        return False, "MONGO_URI is not set."
    try:
        get_client().admin.command("ping")
        return True, f"Connected to MongoDB database '{DB_NAME}'."
    except ConnectionFailure as e:
        return False, f"Connection failure: {str(e)}"
    except ConfigurationError as e:
        return False, f"Configuration error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def utc_now():
    """Returns current UTC datetime."""
    return datetime.now(UTC)


def ist_to_utc(dt_or_str):
    """Converts local datetime input string to UTC datetime."""
    if not dt_or_str:
        return None
    if isinstance(dt_or_str, str):
        try:
            naive = datetime.fromisoformat(dt_or_str)
        except ValueError:
            return None
    else:
        naive = dt_or_str

    if naive.tzinfo is None:
        ist_dt = naive.replace(tzinfo=IST)
    else:
        ist_dt = naive.astimezone(IST)
    return ist_dt.astimezone(UTC)


def utc_to_ist(dt):
    """Converts UTC datetime to IST for frontend display."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(IST)
