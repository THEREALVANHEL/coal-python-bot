"""
database.py – MongoDB helper layer for the Discord bot
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
# Logger setup
# ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Environment & Mongo Client
# ─────────────────────────────────────────────────────────────
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

try:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client["coal"]

    cookies_collection            = db["cookies"]
    warnings_collection           = db["warnings"]
    settings_collection           = db["settings"]
    leveling_collection           = db["leveling"]
    dailies_collection            = db["dailies"]
    starboard_messages_collection = db["starboard_messages"]

    logger.info("✅ Successfully connected to MongoDB.")
except Exception as e:
    logger.error("❌ Failed to connect to MongoDB", exc_info=True)
    mongo_client = None
    cookies_collection = warnings_collection = settings_collection = None
    leveling_collection = dailies_collection = starboard_messages_collection = None

# ─────────────────────────────────────────────────────────────
# Daily-Streak Functions
# ─────────────────────────────────────────────────────────────
def get_daily_data(user_id: int) -> Optional[Dict[str, Any]]:
    if dailies_collection is None:
        return None
    return dailies_collection.find_one({"user_id": user_id})

def update_daily_checkin(user_id: int, new_streak: int) -> None:
    if dailies_collection is None:
        return
    dailies_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "last_checkin": datetime.utcnow(),
                "streak": new_streak,
            }
        },
        upsert=True,
    )

def get_top_daily_streaks(skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    if dailies_collection is None:
        return []
    return (
        dailies_collection.find({"streak": {"$gt": 0}})
        .sort("streak", -1)
        .skip(skip)
        .limit(limit)
    )

def get_total_users_in_dailies() -> int:
    if dailies_collection is None:
        return 0
    return dailies_collection.count_documents({"streak": {"$gt": 0}})

def get_top_streak_users(limit: int = 10) -> list[dict]:
    """Get users with the highest daily streaks."""
    try:
        cursor = db.daily_data.find(
            {"streak": {"$gt": 0}},  # Only users with active streaks
            {"user_id": 1, "streak": 1, "_id": 0}
        ).sort("streak", -1).limit(limit)
        
        return list(cursor)
    except Exception as e:
        print(f"[DB] Error getting top streak users: {e}")
        return []

# ─────────────────────────────────────────────────────────────
# Cookie Functions
# ─────────────────────────────────────────────────────────────
def get_cookies(user_id: int) -> int:
    if cookies_collection is None:
        return 0
    doc = cookies_collection.find_one({"user_id": user_id})
    return doc.get("cookies", 0) if doc else 0

def set_cookies(user_id: int, amount: int) -> None:
    if cookies_collection is None:
        return
    cookies_collection.update_one(
        {"user_id": user_id}, {"$set": {"cookies": amount}}, upsert=True
    )

def add_cookies(user_id: int, amount: int) -> None:
    if cookies_collection is None:
        return
    cookies_collection.update_one(
        {"user_id": user_id}, {"$inc": {"cookies": amount}}, upsert=True
    )

def remove_cookies(user_id: int, amount: int) -> None:
    if cookies_collection is None:
        return
    current = get_cookies(user_id)
    set_cookies(user_id, max(0, current - amount))

def get_leaderboard(skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    if cookies_collection is None:
        return []
    return list(
        cookies_collection.find().sort("cookies", -1).skip(skip).limit(limit)
    )

def get_total_users_in_leaderboard() -> int:
    if cookies_collection is None:
        return 0
    return cookies_collection.count_documents({})

def get_user_rank(user_id: int) -> int:
    if cookies_collection is None:
        return 0
    ahead = cookies_collection.count_documents(
        {"cookies": {"$gt": get_cookies(user_id)}}
    )
    return ahead + 1

def reset_all_cookies(member_ids: List[int]) -> None:
    if cookies_collection is None:
        return
    ops = [
        UpdateOne({"user_id": uid}, {"$set": {"cookies": 0}}, upsert=True)
        for uid in member_ids
    ]
    if ops:
        cookies_collection.bulk_write(ops)

def give_cookies_to_all(amount: int, member_ids: List[int]) -> None:
    if cookies_collection is None:
        return
    cookies_collection.update_many(
        {"user_id": {"$in": member_ids}},
        {"$setOnInsert": {"cookies": 0}},
        upsert=True,
    )
    cookies_collection.update_many(
        {"user_id": {"$in": member_ids}}, {"$inc": {"cookies": amount}}
    )

def synchronize_cookies(all_member_ids: List[int]) -> int:
    if cookies_collection is None:
        return 0
    db_ids = {doc["user_id"] for doc in cookies_collection.find({}, {"user_id": 1})}
    to_remove = list(db_ids - set(all_member_ids))
    if not to_remove:
        return 0
    result = cookies_collection.delete_many({"user_id": {"$in": to_remove}})
    return result.deleted_count

def get_all_users_data() -> List[Dict[str, Any]]:
    if cookies_collection is None:
        return []
    return list(cookies_collection.find({}, {"user_id": 1}))

def remove_user(user_id: int) -> None:
    if cookies_collection is None:
        return
    cookies_collection.delete_one({"user_id": user_id})

def add_user(user_id: int) -> None:
    if cookies_collection is None:
        return
    cookies_collection.update_one(
        {"user_id": user_id}, {"$setOnInsert": {"cookies": 0}}, upsert=True
    )

# ─────────────────────────────────────────────────────────────
# Warning Functions
# ─────────────────────────────────────────────────────────────
def add_warning(user_id: int, moderator_id: int, reason: str) -> None:
    if warnings_collection is None:
        return
    warnings_collection.insert_one(
        {
            "user_id": user_id,
            "moderator_id": moderator_id,
            "reason": reason,
            "timestamp": datetime.utcnow(),
        }
    )

def get_warnings(user_id: int) -> List[Dict[str, Any]]:
    if warnings_collection is None:
        return []
    return list(warnings_collection.find({"user_id": user_id}))

def clear_warnings(user_id: int) -> None:
    if warnings_collection is None:
        return
    warnings_collection.delete_many({"user_id": user_id})

# ─────────────────────────────────────────────────────────────
# Settings Functions
# ─────────────────────────────────────────────────────────────
def set_channel(guild_id: int, channel_type: str, channel_id: int) -> None:
    if settings_collection is None:
        return
    settings_collection.update_one(
        {"guild_id": guild_id},
        {"$set": {f"{channel_type}_channel": channel_id}},
        upsert=True,
    )

def get_channel(guild_id: int, channel_type: str) -> Optional[int]:
    if settings_collection is None:
        return None
    doc = settings_collection.find_one({"guild_id": guild_id})
    return doc.get(f"{channel_type}_channel") if doc else None

def set_starboard(guild_id: int, channel_id: int, star_count: int) -> None:
    if settings_collection is None:
        return
    settings_collection.update_one(
        {"guild_id": guild_id},
        {
            "$set": {
                "starboard_channel": channel_id,
                "starboard_star_count": star_count,
            }
        },
        upsert=True,
    )

def get_starboard_settings(guild_id: int) -> Optional[Dict[str, Any]]:
    if settings_collection is None:
        return None
    return settings_collection.find_one({"guild_id": guild_id})

# ─────────────────────────────────────────────────────────────
# Starboard Message Tracking
# ─────────────────────────────────────────────────────────────
def has_been_starred(guild_id: int, message_id: int) -> bool:
    if starboard_messages_collection is None:
        return False
    return (
        starboard_messages_collection.find_one(
            {"guild_id": guild_id, "message_id": message_id}
        )
        is not None
    )

def mark_as_starred(guild_id: int, message_id: int) -> None:
    if starboard_messages_collection is None:
        return
    starboard_messages_collection.insert_one(
        {
            "guild_id": guild_id,
            "message_id": message_id,
            "timestamp": datetime.utcnow(),
        }
    )

def get_starboard_message(message_id: int) -> Optional[int]:
    if starboard_messages_collection is None:
        return None
    doc = starboard_messages_collection.find_one({"message_id": message_id})
    return doc["starboard_post_id"] if doc else None

def add_starboard_message(original_id: int, post_id: int) -> None:
    if starboard_messages_collection is None:
        return
    starboard_messages_collection.update_one(
        {"message_id": original_id},
        {"$set": {"starboard_post_id": post_id, "timestamp": datetime.utcnow()}},
        upsert=True,
    )

# ─────────────────────────────────────────────────────────────
# Leveling Functions
# ─────────────────────────────────────────────────────────────
def get_user_level_data(user_id: int) -> Optional[Dict[str, Any]]:
    if leveling_collection is None:
        return None
    return leveling_collection.find_one({"user_id": user_id})

def update_user_xp(user_id: int, xp_to_add: int) -> None:
    if leveling_collection is None:
        return
    leveling_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"xp": xp_to_add}, "$setOnInsert": {"level": 0}},
        upsert=True,
    )

def set_user_level(user_id: int, new_level: int) -> None:
    if leveling_collection is None:
        return
    leveling_collection.update_one(
        {"user_id": user_id}, {"$set": {"level": new_level, "xp": 0}}
    )

def get_leveling_leaderboard(skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    if leveling_collection is None:
        return []
    return list(
        leveling_collection.find()
        .sort([("level", -1), ("xp", -1)])
        .skip(skip)
        .limit(limit)
    )

def get_total_users_in_leveling() -> int:
    if leveling_collection is None:
        return 0
    return leveling_collection.count_documents({})

def get_user_leveling_rank(user_id: int) -> int:
    if leveling_collection is None:
        return 0
    data = get_user_level_data(user_id)
    if data is None:
        return get_total_users_in_leveling() + 1
    level, xp = data.get("level", 0), data.get("xp", 0)
    higher = leveling_collection.count_documents(
        {"$or": [{"level": {"$gt": level}}, {"level": level, "xp": {"$gt": xp}}]}
    )
    return higher + 1
