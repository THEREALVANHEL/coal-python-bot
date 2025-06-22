import os
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
MONGODB_URI = os.getenv('MONGODB_URI')

# --- Database Setup ---
try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client.get_database('coal') # You can change 'coal' to your preferred db name
    cookies_collection = db.get_collection('cookies')
    warnings_collection = db.get_collection('warnings')
    settings_collection = db.get_collection('settings')
    leveling_collection = db.get_collection('leveling') # New collection for levels
    dailies_collection = db.get_collection('dailies') # New collection for daily check-ins
    starboard_messages_collection = db.get_collection('starboard_messages') # Tracks starboard posts
    print("✅ Successfully connected to MongoDB.")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    mongo_client = None
    db = None
    cookies_collection = None
    warnings_collection = None
    settings_collection = None
    leveling_collection = None
    dailies_collection = None
    starboard_messages_collection = None

# --- Helper Functions ---

# --- Daily Check-in Functions ---
def get_daily_data(user_id: int):
    """Fetches the daily check-in data for a given user."""
    if dailies_collection is None: return None
    return dailies_collection.find_one({"user_id": user_id})

def update_daily_checkin(user_id: int, new_streak: int):
    """Updates the user's daily check-in timestamp and streak."""
    if dailies_collection is None: return
    dailies_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_checkin": datetime.utcnow(), "streak": new_streak}},
        upsert=True
    )

# --- Cookie Functions ---
def get_cookies(user_id: int):
    """Fetches the cookie count for a given user."""
    if cookies_collection is None: return 0
    user_data = cookies_collection.find_one({"user_id": user_id})
    return user_data.get("cookies", 0) if user_data else 0

def set_cookies(user_id: int, amount: int):
    """Sets the cookie count for a user."""
    if cookies_collection is None: return
    cookies_collection.update_one(
        {"user_id": user_id},
        {"$set": {"cookies": amount}},
        upsert=True
    )

def add_cookies(user_id: int, amount: int):
    """Adds a specific amount of cookies to a user."""
    if cookies_collection is None: return
    cookies_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"cookies": amount}},
        upsert=True
    )

def remove_cookies(user_id: int, amount: int):
    """Removes a specific amount of cookies from a user, ensuring it doesn't go below zero."""
    if cookies_collection is None: return
    current_cookies = get_cookies(user_id)
    new_amount = max(0, current_cookies - amount)
    set_cookies(user_id, new_amount)

def get_leaderboard(skip: int = 0, limit: int = 10):
    """Retrieves a paginated list of users sorted by cookie count."""
    if cookies_collection is None: return []
    return list(cookies_collection.find().sort("cookies", -1).skip(skip).limit(limit))

def get_total_users_in_leaderboard():
    """Counts the total number of users with cookies."""
    if cookies_collection is None: return 0
    return cookies_collection.count_documents({})

def get_user_rank(user_id: int):
    """Gets the rank of a specific user in the cookie leaderboard."""
    if cookies_collection is None: return 0
    rank = cookies_collection.count_documents({'cookies': {'$gt': get_cookies(user_id)}})
    return rank + 1

def reset_all_cookies(member_ids: list):
    """Resets cookies to zero for all specified member IDs."""
    if cookies_collection is None: return
    
    # This ensures that even if a user wasn't in the DB, they will be now with 0 cookies.
    # This is more robust for role updates after a reset.
    bulk_ops = [
        UpdateOne({"user_id": user_id}, {"$set": {"cookies": 0}}, upsert=True)
        for user_id in member_ids
    ]
    if bulk_ops:
        cookies_collection.bulk_write(bulk_ops)

def give_cookies_to_all(amount: int, member_ids: list):
    """Gives a specified number of cookies to all members in the list."""
    if cookies_collection is None: return
    for user_id in member_ids:
        cookies_collection.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {"cookies": 0}},
            upsert=True
        )
    cookies_collection.update_many(
        {"user_id": {"$in": member_ids}},
        {"$inc": {"cookies": amount}}
    )

def synchronize_cookies(all_member_ids: list):
    """Removes users from the cookie database who are no longer in the server."""
    if cookies_collection is None:
        return 0
    
    # Get all user IDs from the database collection
    db_user_ids = {doc['user_id'] for doc in cookies_collection.find({}, {'user_id': 1})}
    
    # Find users who are in the database but not in the server anymore
    ids_to_remove = list(db_user_ids - set(all_member_ids))
    
    if not ids_to_remove:
        return 0

    # Remove them from the collection
    result = cookies_collection.delete_many({'user_id': {'$in': ids_to_remove}})
    return result.deleted_count

# --- Warning Functions ---
def add_warning(user_id: int, moderator_id: int, reason: str):
    """Adds a warning to a user."""
    if warnings_collection is None: return
    warnings_collection.insert_one({
        "user_id": user_id,
        "moderator_id": moderator_id,
        "reason": reason,
        "timestamp": datetime.utcnow()
    })

def get_warnings(user_id: int):
    """Retrieves all warnings for a specific user."""
    if warnings_collection is None: return []
    return list(warnings_collection.find({"user_id": user_id}))

def clear_warnings(user_id: int):
    """Clears all warnings for a specific user."""
    if warnings_collection is None: return
    warnings_collection.delete_many({"user_id": user_id})

# --- Settings Functions ---
def set_channel(guild_id: int, channel_type: str, channel_id: int):
    """Saves a channel ID for a specific purpose (e.g., 'welcome', 'log')."""
    if settings_collection is None: return
    settings_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {f"{channel_type}_channel": channel_id}},
        upsert=True
    )

def get_channel(guild_id: int, channel_type: str):
    """Retrieves a saved channel ID."""
    if settings_collection is None: return None
    settings = settings_collection.find_one({"guild_id": guild_id})
    return settings.get(f"{channel_type}_channel") if settings else None

def set_starboard(guild_id: int, channel_id: int, star_count: int):
    """Saves the settings for the starboard."""
    if settings_collection is None: return
    settings_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {
            "starboard_channel": channel_id,
            "starboard_star_count": star_count
        }},
        upsert=True
    )

def get_starboard_settings(guild_id: int):
    """Retrieves the starboard settings for a guild."""
    if settings_collection is None: return None
    return settings_collection.find_one({"guild_id": guild_id})

# --- Starboard Message Tracking ---
def add_starboard_message(original_message_id: int, starboard_message_id: int):
    """Logs a message that has been posted to the starboard."""
    if starboard_messages_collection is None: return
    starboard_messages_collection.insert_one({
        "original_message_id": original_message_id,
        "starboard_message_id": starboard_message_id
    })

def get_starboard_message(original_message_id: int):
    """Finds the ID of a starboard message linked to an original message."""
    if starboard_messages_collection is None: return None
    doc = starboard_messages_collection.find_one({"original_message_id": original_message_id})
    return doc.get("starboard_message_id") if doc else None

# --- Leveling Functions ---
def get_user_level_data(user_id: int):
    """Fetches the level and XP for a given user."""
    if leveling_collection is None: return None
    return leveling_collection.find_one({"user_id": user_id})

def update_user_xp(user_id: int, xp_to_add: int):
    """Adds XP to a user, creating the user if they don't exist."""
    if leveling_collection is None: return
    leveling_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {"xp": xp_to_add},
            "$setOnInsert": {"level": 0} # Start at level 0, not 1
        },
        upsert=True
    )

def set_user_level(user_id: int, new_level: int):
    """Sets a user's level and resets their current XP for that level to 0."""
    if leveling_collection is None: return
    leveling_collection.update_one(
        {"user_id": user_id},
        {"$set": {"level": new_level, "xp": 0}}
    )

def get_leveling_leaderboard(skip: int = 0, limit: int = 10):
    """Retrieves a paginated list of users sorted by level and XP."""
    if leveling_collection is None: return []
    # Sort by level descending, then by XP descending
    return list(leveling_collection.find().sort([("level", -1), ("xp", -1)]).skip(skip).limit(limit))

def get_total_users_in_leveling():
    """Counts the total number of users in the leveling system."""
    if leveling_collection is None: return 0
    return leveling_collection.count_documents({})

def get_user_leveling_rank(user_id: int):
    """Gets the rank of a specific user in the leveling leaderboard."""
    if leveling_collection is None: return 0
    
    user_data = get_user_level_data(user_id)
    if user_data is None:
        return get_total_users_in_leveling() + 1 # Unranked user is last

    user_level = user_data.get('level', 0)
    user_xp = user_data.get('xp', 0)

    # Count users with a higher level, or same level with more XP
    higher_rank_count = leveling_collection.count_documents({
        "$or": [
            {"level": {"$gt": user_level}},
            {"level": user_level, "xp": {"$gt": user_xp}}
        ]
    })
    
    return higher_rank_count + 1
