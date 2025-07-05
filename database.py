import pymongo
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    print("❌ MongoDB URI not found!")
    client = None
    db = None
    users_collection = None
    guild_settings_collection = None
    warnings_collection = None
    starboard_collection = None
else:
    try:
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.discord_bot
        users_collection = db.users
        guild_settings_collection = db.guild_settings
        warnings_collection = db.warnings
        starboard_collection = db.starboard
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        client = None
        db = None
        users_collection = None
        guild_settings_collection = None
        warnings_collection = None
        starboard_collection = None

def get_user_data(user_id):
    """Get user data from database"""
    if users_collection is None:
        return {}
    
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        return user_data if user_data else {}
    except Exception as e:
        print(f"Error getting user data: {e}")
        return {}

def add_xp(user_id, xp_amount):
    """Add XP to user"""
    if users_collection is None:
        return False
    
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"xp": xp_amount}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error adding XP: {e}")
        return False

def add_cookies(user_id, cookie_amount):
    """Add cookies to user"""
    if users_collection is None:
        return False
    
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"cookies": cookie_amount}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error adding cookies: {e}")
        return False

def remove_cookies(user_id, cookie_amount):
    """Remove cookies from user"""
    if users_collection is None:
        return False

    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"cookies": -cookie_amount}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error removing cookies: {e}")
        return False

def add_coins(user_id, coin_amount):
    """Add coins to user"""
    if users_collection is None:
        return False

    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"coins": coin_amount}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error adding coins: {e}")
        return False

def remove_coins(user_id, coin_amount):
    """Remove coins from user"""
    if users_collection is None:
        return False

    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"coins": -coin_amount}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error removing coins: {e}")
        return False

def update_last_xp_time(user_id, timestamp):
    """Update last XP time"""
    if users_collection is None:
        return False

    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_xp_time": timestamp}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error updating last XP time: {e}")
        return False

def update_last_work(user_id, timestamp):
    """Update last work time"""
    if users_collection is None:
        return False

    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_work": timestamp}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error updating last work time: {e}")
        return False

def claim_daily_xp(user_id):
    """Claim daily XP bonus"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        user_data = get_user_data(user_id)
        last_daily = user_data.get('last_daily', 0)
        current_time = datetime.now().timestamp()
        
        # Check if 24 hours have passed
        if current_time - last_daily < 86400:  # 24 hours in seconds
            time_left = 86400 - (current_time - last_daily)
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            return {
                "success": False, 
                "time_left": f"{hours}h {minutes}m"
            }
        
        # Calculate streak
        streak = user_data.get('daily_streak', 0)
        if current_time - last_daily <= 172800:  # Within 48 hours
            streak += 1
        else:
            streak = 1
        
        # Calculate XP (bonus every 7 days)
        base_xp = 100
        bonus_xp = 200 if streak % 7 == 0 else 0
        total_xp = base_xp + bonus_xp
        
        # Update database
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {"xp": total_xp},
                "$set": {
                    "last_daily": current_time,
                    "daily_streak": streak
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "xp_gained": total_xp,
            "streak": streak
        }
        
    except Exception as e:
        print(f"Error claiming daily: {e}")
        return {"success": False, "message": str(e)}

def get_leaderboard(field, limit=10):
    """Get leaderboard for a specific field"""
    if users_collection is None:
        return []
    try:
        pipeline = [
            {"$match": {field: {"$gt": 0}}},
            {"$sort": {field: -1}},
            {"$limit": limit}
        ]
        return list(users_collection.aggregate(pipeline))
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return []

def add_warning(user_id, reason, moderator_id):
    """Add warning to user"""
    if warnings_collection is None:
        return False

    try:
        warning = {
            "user_id": user_id,
            "reason": reason,
            "moderator_id": moderator_id,
            "timestamp": datetime.now().timestamp()
        }
        warnings_collection.insert_one(warning)
        return True
    except Exception as e:
        print(f"Error adding warning: {e}")
        return False

def get_user_warnings(user_id):
    """Get all warnings for a user"""
    if warnings_collection is None:
        return []

    try:
        return list(warnings_collection.find({"user_id": user_id}).sort("timestamp", -1))
    except Exception as e:
        print(f"Error getting warnings: {e}")
        return []

def set_guild_setting(guild_id, setting, value):
    """Set a guild setting"""
    if guild_settings_collection is None:
        return False

    try:
        guild_settings_collection.update_one(
            {"guild_id": guild_id},
            {"$set": {setting: value}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error setting guild setting: {e}")
        return False

def get_guild_setting(guild_id, setting, default=None):
    """Get a guild setting"""
    if guild_settings_collection is None:
        return default

    try:
        guild_data = guild_settings_collection.find_one({"guild_id": guild_id})
        if guild_data and setting in guild_data:
            return guild_data[setting]
        return default
    except Exception as e:
        print(f"Error getting guild setting: {e}")
        return default

def reset_guild_settings(guild_id):
    """Reset all guild settings"""
    if guild_settings_collection is None:
        return False

    try:
        guild_settings_collection.delete_one({"guild_id": guild_id})
        return True
    except Exception as e:
        print(f"Error resetting guild settings: {e}")
        return False

def add_starboard_message(message_id, starboard_message_id, star_count):
    """Add message to starboard"""
    if starboard_collection is None:
        return False

    try:
        starboard_entry = {
            "message_id": message_id,
            "starboard_message_id": starboard_message_id,
            "star_count": star_count,
            "timestamp": datetime.now().timestamp()
        }
        starboard_collection.insert_one(starboard_entry)
        return True
    except Exception as e:
        print(f"Error adding starboard message: {e}")
        return False

def get_starboard_message(message_id):
    """Get starboard entry for a message"""
    if starboard_collection is None:
        return None

    try:
        return starboard_collection.find_one({"message_id": message_id})
    except Exception as e:
        print(f"Error getting starboard message: {e}")
        return None

def update_starboard_count(message_id, new_count):
    """Update star count for starboard message"""
    if starboard_collection is None:
        return False

    try:
        starboard_collection.update_one(
            {"message_id": message_id},
            {"$set": {"star_count": new_count}}
        )
        return True
    except Exception as e:
        print(f"Error updating starboard count: {e}")
        return False
