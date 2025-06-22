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
    db = mongo_client.get_database('coal')
    cookies_collection = db.get_collection('cookies')
    warnings_collection = db.get_collection('warnings')
    settings_collection = db.get_collection('settings')
    leveling_collection = db.get_collection('leveling')
    dailies_collection = db.get_collection('dailies')
    starboard_messages_collection = db.get_collection('starboard_messages')
    print("✅ Successfully connected to MongoDB.")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    mongo_client = db = cookies_collection = warnings_collection = settings_collection = leveling_collection = dailies_collection = starboard_messages_collection = None

# --- Daily Check-in Functions ---
def get_daily_data(user_id: int):
    if dailies_collection is None: return None
    return dailies_collection.find_one({"user_id": user_id})

def update_daily_checkin(user_id: int, new_streak: int):
    if dailies_collection is None: return
    dailies_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_checkin": datetime.utcnow(), "streak": new_streak}},
        upsert=True
    )

# --- Cookie Functions ---
def get_cookies(user_id: int):
    if cookies_collection is None: return 0
    user_data = cookies_collection.find_one({"user_id": user_id})
    return user_data.get("cookies", 0) if user_data else 0

def set_cookies(user_id: int, amount: int):
    if cookies_collection is None: return
    cookies_collection.update_one(
        {"user_id": user_id},
        {"$set": {"cookies": amount}},
        upsert=True
    )

def add_cookies(user_id: int, amount: int):
    if cookies_collection is None: return
    cookies_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"cookies": amount}},
        upsert=True
    )

def remove_cookies(user_id: int, amount: int):
    if cookies_collection is None: return
    current_cookies = get_cookies(user_id)
    new_amount = max(0, current_cookies - amount)
    set_cookies(user_id, new_amount)

def get_leaderboard(skip: int = 0, limit: int = 10):
    if cookies_collection is None: return []
    return list(cookies_collection.find().sort("cookies", -1).skip(skip).limit(limit))

def get_total_users_in_leaderboard():
    if cookies_collection is None: return 0
    return cookies_collection.count_documents({})

def get_user_rank(user_id: int):
    if cookies_collection is None: return 0
    rank = cookies_collection.count_documents({'cookies': {'$gt': get_cookies(user_id)}})
    return rank + 1

def reset_all_cookies(member_ids: list):
    if cookies_collection is None: return
    bulk_ops = [UpdateOne({"user_id": user_id}, {"$set": {"cookies": 0}}, upsert=True) for user_id in member_ids]
    if bulk_ops:
        cookies_collection.bulk_write(bulk_ops)

def give_cookies_to_all(amount: int, member_ids: list):
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
    if cookies_collection is None: return 0
    db_user_ids = {doc['user_id'] for doc in cookies_collection.find({}, {'user_id': 1})}
    ids_to_remove = list(db_user_ids - set(all_member_ids))
    if not ids_to_remove: return 0
    result = cookies_collection.delete_many({'user_id': {'$in': ids_to_remove}})
    return result.deleted_count

def get_all_users_data():
    if cookies_collection is None: return []
    return list(cookies_collection.find({}, {"user_id": 1}))

def remove_user(user_id: int):
    if cookies_collection is None: return
    cookies_collection.delete_one({"user_id": user_id})

def add_user(user_id: int):
    if cookies_collection is None: return
    cookies_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {"cookies": 0}},
        upsert=True
    )

# --- Warning Functions ---
def add_warning(user_id: int, moderator_id: int, reason: str):
    if warnings_collection is None: return
    warnings_collection.insert_one({
        "user_id": user_id,
        "moderator_id": moderator_id,
        "reason": reason,
        "timestamp": datetime.utcnow()
    })

def get_warnings(user_id: int):
    if warnings_collection is None: return []
    return list(warnings_collection.find({"user_id": user_id}))

def clear_warnings(user_id: int):
    if warnings_collection is None: return
    warnings_collection.delete_many({"user_id": user_id})

# --- Settings Functions ---
def set_channel(guild_id: int, channel_type: str, channel_id: int):
    if settings_collection is None: return
    settings_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {f"{channel_type}_channel": channel_id}},
        upsert=True
    )

def get_channel(guild_id: int, channel_type: str):
    if settings_collection is None: return None
    settings = settings_collection.find_one({"guild_id": guild_id})
    return settings.get(f"{channel_type}_channel") if settings else None

def set_starboard(guild_id: int, channel_id: int, star_count: int):
    if settings_collection is None: return
    settings_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {"starboard_channel": channel_id, "starboard_star_count": star_count}},
        upsert=True
    )

def get_starboard_settings(guild_id: int):
    if settings_collection is None: return None
    return settings_collection.find_one({"guild_id": guild_id})

# --- Starboard Message Tracking ---
def add_starboard_message(original_message_id: int, starboard_message_id: int):
    if starboard_messages_collection is None: return
    starboard_messages_collection.insert_one({
        "original_message_id": original_message_id,
        "starboard_message_id": starboard_message_id
    })

def get_starboard_message(original_message_id: int):
    if starboard_messages_collection is None: return None
    doc = starboard_messages_collection.find_one({"original_message_id": original_message_id})
    return doc.get("starboard_message_id") if doc else None

# --- Leveling Functions ---
def get_user_level_data(user_id: int):
    if leveling_collection is None: return None
    return leveling_collection.find_one({"user_id": user_id})

def update_user_xp(user_id: int, xp_to_add: int):
    if leveling_collection is None: return
    leveling_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"xp": xp_to_add}, "$setOnInsert": {"level": 0}},
        upsert=True
    )

def set_user_level(user_id: int, new_level: int):
    if leveling_collection is None: return
    leveling_collection.update_one(
        {"user_id": user_id},
        {"$set": {"level": new_level, "xp": 0}}
    )

def get_leveling_leaderboard(skip: int = 0, limit: int = 10):
    if leveling_collection is None: return []
    return list(leveling_collection.find().sort([("level", -1), ("xp", -1)]).skip(skip).limit(limit))

def get_total_users_in_leveling():
    if leveling_collection is None: return 0
    return leveling_collection.count_documents({})

def get_user_leveling_rank(user_id: int):
    if leveling_collection is None: return 0
    user_data = get_user_level_data(user_id)
    if user_data is None:
        return get_total_users_in_leveling() + 1
    user_level = user_data.get('level', 0)
    user_xp = user_data.get('xp', 0)
    higher_rank_count = leveling_collection.count_documents({
        "$or": [
            {"level": {"$gt": user_level}},
            {"level": user_level, "xp": {"$gt": user_xp}}
        ]
    })
    return higher_rank_count + 1
