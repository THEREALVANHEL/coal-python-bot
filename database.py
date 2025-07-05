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

def add_temporary_role(user_id, role_id, duration_seconds):
    """Add a temporary role to user"""
    if users_collection is None:
        return False
    
    try:
        end_time = datetime.now().timestamp() + duration_seconds
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "temporary_roles": {
                        "role_id": role_id,
                        "end_time": end_time
                    }
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error adding temporary role: {e}")
        return False

def add_temporary_purchase(user_id, item_type, duration_seconds):
    """Add a temporary purchase (like XP boost, badge, etc.)"""
    if users_collection is None:
        return False
    
    try:
        end_time = datetime.now().timestamp() + duration_seconds if duration_seconds > 0 else 0
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "temporary_purchases": {
                        "item_type": item_type,
                        "end_time": end_time,
                        "purchase_time": datetime.now().timestamp()
                    }
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error adding temporary purchase: {e}")
        return False

def get_active_temporary_roles(user_id):
    """Get all active temporary roles for a user"""
    if users_collection is None:
        return []
    
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or "temporary_roles" not in user_data:
            return []
        
        current_time = datetime.now().timestamp()
        active_roles = []
        expired_roles = []
        
        for role_data in user_data["temporary_roles"]:
            if role_data["end_time"] > current_time:
                active_roles.append(role_data)
            else:
                expired_roles.append(role_data)
        
        # Remove expired roles
        if expired_roles:
            users_collection.update_one(
                {"user_id": user_id},
                {"$pullAll": {"temporary_roles": expired_roles}}
            )
        
        return active_roles
    except Exception as e:
        print(f"Error getting temporary roles: {e}")
        return []

def get_active_temporary_purchases(user_id):
    """Get all active temporary purchases for a user"""
    if users_collection is None:
        return []
    
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or "temporary_purchases" not in user_data:
            return []
        
        current_time = datetime.now().timestamp()
        active_purchases = []
        expired_purchases = []
        
        for purchase_data in user_data["temporary_purchases"]:
            # If end_time is 0, it's permanent
            if purchase_data["end_time"] == 0 or purchase_data["end_time"] > current_time:
                active_purchases.append(purchase_data)
            else:
                expired_purchases.append(purchase_data)
        
        # Remove expired purchases
        if expired_purchases:
            users_collection.update_one(
                {"user_id": user_id},
                {"$pullAll": {"temporary_purchases": expired_purchases}}
            )
        
        return active_purchases
    except Exception as e:
        print(f"Error getting temporary purchases: {e}")
        return []

def cleanup_expired_items():
    """Clean up all expired temporary roles and purchases"""
    if users_collection is None:
        return False
    
    try:
        current_time = datetime.now().timestamp()
        
        # Remove expired temporary roles
        users_collection.update_many(
            {},
            {
                "$pull": {
                    "temporary_roles": {"end_time": {"$lt": current_time}},
                    "temporary_purchases": {
                        "end_time": {"$lt": current_time, "$ne": 0}
                    }
                }
            }
        )
        return True
    except Exception as e:
        print(f"Error cleaning up expired items: {e}")
        return False

def get_all_user_data():
    """Get all user data from database for migration/sync purposes"""
    if users_collection is None:
        return []
    
    try:
        return list(users_collection.find({}))
    except Exception as e:
        print(f"Error getting all user data: {e}")
        return []

def sync_user_data(user_id):
    """Sync specific user's data to ensure it's properly formatted"""
    if users_collection is None:
        return False
    
    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            # Ensure all required fields exist with defaults
            update_data = {}
            
            if "xp" not in user_data:
                update_data["xp"] = 0
            if "cookies" not in user_data:
                update_data["cookies"] = 0
            if "coins" not in user_data:
                update_data["coins"] = 0
            if "daily_streak" not in user_data:
                update_data["daily_streak"] = 0
            if "last_daily" not in user_data:
                update_data["last_daily"] = 0
            if "last_xp_time" not in user_data:
                update_data["last_xp_time"] = 0
            if "last_work" not in user_data:
                update_data["last_work"] = 0
            
            if update_data:
                users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": update_data}
                )
        
        return True
    except Exception as e:
        print(f"Error syncing user data: {e}")
        return False

def restore_all_data():
    """Restore and sync all user data in the database"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        all_users = users_collection.find({})
        restored_count = 0
        
        for user_data in all_users:
            user_id = user_data.get("user_id")
            if user_id:
                sync_user_data(user_id)
                restored_count += 1
        
        return {
            "success": True,
            "restored_count": restored_count,
            "message": f"Successfully restored data for {restored_count} users"
        }
    except Exception as e:
        print(f"Error restoring all data: {e}")
        return {"success": False, "message": str(e)}

def get_database_stats():
    """Get statistics about the database"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        total_users = users_collection.count_documents({})
        users_with_xp = users_collection.count_documents({"xp": {"$gt": 0}})
        users_with_cookies = users_collection.count_documents({"cookies": {"$gt": 0}})
        users_with_coins = users_collection.count_documents({"coins": {"$gt": 0}})
        
        # Get total XP and cookies in database
        pipeline_xp = [{"$group": {"_id": None, "total": {"$sum": "$xp"}}}]
        pipeline_cookies = [{"$group": {"_id": None, "total": {"$sum": "$cookies"}}}]
        
        total_xp_result = list(users_collection.aggregate(pipeline_xp))
        total_cookies_result = list(users_collection.aggregate(pipeline_cookies))
        
        total_xp = total_xp_result[0]["total"] if total_xp_result else 0
        total_cookies = total_cookies_result[0]["total"] if total_cookies_result else 0
        
        return {
            "success": True,
            "total_users": total_users,
            "users_with_xp": users_with_xp,
            "users_with_cookies": users_with_cookies,
            "users_with_coins": users_with_coins,
            "total_xp": total_xp,
            "total_cookies": total_cookies
        }
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return {"success": False, "message": str(e)}
