# Compatibility wrapper for database imports
# This file provides backward compatibility for cogs that import 'database' directly

import os
from pymongo import MongoClient
from datetime import datetime, timedelta
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Try to use core database first, but have robust fallback
try:
    from core.database import get_db_manager, initialize_database
    
    # Create a global db instance for backward compatibility
    core_db_manager = get_db_manager()
    if core_db_manager:
        print("⚠️ Core database manager is async, using sync fallback")
        raise ImportError("Core database is async, need sync fallback")
    else:
        raise ImportError("Core database manager not available")
        
except (ImportError, Exception) as e:
    print(f"⚠️ Core database import failed: {e}, using sync fallback")
    
    # Create sync database fallback that actually works
    class DatabaseManager:
        def __init__(self):
            self.client = None
            self.db = None
            self.users_collection = None
            self.guilds_collection = None
            self.connected = False
            self.initialize()
        
        def initialize(self):
            try:
                mongodb_uri = os.getenv('MONGODB_URI')
                if mongodb_uri:
                    self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
                    # Test the connection
                    self.client.admin.command('ping')
                    self.db = self.client.get_default_database()
                    self.users_collection = self.db.users
                    self.guilds_collection = self.db.guilds
                    self.connected = True
                    print("✅ Sync database connection established successfully")
                else:
                    print("⚠️ No MONGODB_URI found in environment")
                    self.connected = False
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                self.connected = False
        
        def get_user_data(self, user_id):
            try:
                if self.connected and self.users_collection:
                    result = self.users_collection.find_one({"user_id": user_id})
                    return result if result else {}
                else:
                    return {}
            except Exception as e:
                print(f"❌ Error getting user data: {e}")
                return {}
        
        def update_user_data(self, user_id, data):
            try:
                if self.connected and self.users_collection:
                    self.users_collection.update_one(
                        {"user_id": user_id},
                        {"$set": data},
                        upsert=True
                    )
                    return True
                return False
            except Exception as e:
                print(f"❌ Error updating user data: {e}")
                return False
        
        def add_coins(self, user_id, amount):
            try:
                if self.connected and self.users_collection:
                    self.users_collection.update_one(
                        {"user_id": user_id},
                        {"$inc": {"coins": amount}},
                        upsert=True
                    )
                    return True
                return False
            except Exception as e:
                print(f"❌ Error adding coins: {e}")
                return False
        
        def get_active_temporary_roles(self, user_id=None):
            try:
                if self.connected and self.users_collection:
                    if user_id:
                        user_data = self.users_collection.find_one({"user_id": user_id})
                        if user_data and "temporary_roles" in user_data:
                            current_time = time.time()
                            return [role for role in user_data["temporary_roles"] 
                                   if role.get("expires_at", 0) > current_time]
                    else:
                        # Get all active temporary roles
                        current_time = time.time()
                        users = self.users_collection.find({"temporary_roles": {"$exists": True}})
                        active_roles = []
                        for user in users:
                            for role in user.get("temporary_roles", []):
                                if role.get("expires_at", 0) > current_time:
                                    active_roles.append(role)
                        return active_roles
                return []
            except Exception as e:
                print(f"❌ Error getting active temporary roles: {e}")
                return []
        
        def get_pending_reminders(self):
            try:
                if self.connected and self.users_collection:
                    current_time = time.time()
                    users = self.users_collection.find({"reminders": {"$exists": True}})
                    pending_reminders = []
                    for user in users:
                        for reminder in user.get("reminders", []):
                            if reminder.get("remind_at", 0) <= current_time:
                                pending_reminders.append(reminder)
                    return pending_reminders
                return []
            except Exception as e:
                print(f"❌ Error getting pending reminders: {e}")
                return []
        
        def add_temporary_purchase(self, user_id, item_type, duration):
            try:
                if self.connected and self.users_collection:
                    expiry_time = time.time() + duration
                    purchase_data = {
                        "item_type": item_type,
                        "expires_at": expiry_time,
                        "purchased_at": time.time()
                    }
                    self.users_collection.update_one(
                        {"user_id": user_id},
                        {"$push": {"temporary_purchases": purchase_data}},
                        upsert=True
                    )
                    return True
                return False
            except Exception as e:
                print(f"❌ Error adding temporary purchase: {e}")
                return False
        
        def claim_daily_bonus(self, user_id):
            try:
                if not self.connected or not self.users_collection:
                    return {"success": False, "error": "Database not connected"}
                
                current_time = time.time()
                user_data = self.users_collection.find_one({"user_id": user_id}) or {}
                
                # Check if user already claimed today
                last_daily = user_data.get("last_daily_claim", 0)
                time_since_last = current_time - last_daily
                
                # 24 hours = 86400 seconds
                if time_since_last < 86400:
                    hours_left = int((86400 - time_since_last) / 3600)
                    minutes_left = int(((86400 - time_since_last) % 3600) / 60)
                    time_left = f"{hours_left}h {minutes_left}m"
                    return {"success": False, "time_left": time_left}
                
                # Calculate streak
                streak = user_data.get("daily_streak", 0)
                if time_since_last <= 172800:  # Within 48 hours (allows for 1 day gap)
                    streak += 1
                else:
                    streak = 1  # Reset streak
                
                # Calculate rewards based on streak
                base_xp = 50
                base_coins = 100
                
                # Streak bonuses
                streak_multiplier = min(1 + (streak * 0.1), 3.0)  # Max 3x multiplier
                xp_gained = int(base_xp * streak_multiplier)
                coins_gained = int(base_coins * streak_multiplier)
                
                # Weekly streak bonus (every 7 days)
                if streak % 7 == 0:
                    xp_gained += 200
                    coins_gained += 500
                
                # Update user data
                self.users_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "last_daily_claim": current_time,
                            "daily_streak": streak
                        },
                        "$inc": {
                            "xp": xp_gained,
                            "coins": coins_gained
                        }
                    },
                    upsert=True
                )
                
                return {
                    "success": True,
                    "xp_gained": xp_gained,
                    "coins_gained": coins_gained,
                    "streak": streak
                }
                
            except Exception as e:
                print(f"❌ Error claiming daily bonus: {e}")
                return {"success": False, "error": str(e)}
        
        def remove_coins(self, user_id, amount):
            try:
                if self.connected and self.users_collection:
                    self.users_collection.update_one(
                        {"user_id": user_id},
                        {"$inc": {"coins": -amount}},
                        upsert=True
                    )
                    return True
                return False
            except Exception as e:
                print(f"❌ Error removing coins: {e}")
                return False
        
        def get_leaderboard(self, field, limit=10):
            try:
                if self.connected and self.users_collection:
                    cursor = self.users_collection.find().sort(field, -1).limit(limit)
                    return list(cursor)
                return []
            except Exception as e:
                print(f"❌ Error getting leaderboard: {e}")
                return []
        
        def get_active_temporary_purchases(self, user_id):
            try:
                if self.connected and self.users_collection:
                    user_data = self.users_collection.find_one({"user_id": user_id})
                    if user_data and "temporary_purchases" in user_data:
                        current_time = time.time()
                        return [purchase for purchase in user_data["temporary_purchases"] 
                               if purchase.get("expires_at", 0) > current_time]
                return []
            except Exception as e:
                print(f"❌ Error getting active temporary purchases: {e}")
                return []
        
        def get_database_health(self):
            try:
                if self.connected and self.client:
                    # Test connection
                    self.client.admin.command('ping')
                    return {"status": "healthy", "connected": True}
                return {"status": "disconnected", "connected": False}
            except Exception as e:
                return {"status": "error", "connected": False, "error": str(e)}
        
        def get_database_stats(self):
            try:
                if self.connected and self.users_collection:
                    total_users = self.users_collection.count_documents({})
                    return {"total_users": total_users}
                return {"total_users": 0}
            except Exception as e:
                print(f"❌ Error getting database stats: {e}")
                return {"total_users": 0}
    
    # Create the database instance
    db = DatabaseManager()
    
    # If database connection failed, create minimal fallback
    if not db.connected:
        print("🔄 Database connection failed, using minimal fallback mode")
        
        class MinimalDB:
            def get_user_data(self, user_id):
                return {}
            def update_user_data(self, user_id, data):
                return False
            def add_coins(self, user_id, amount):
                return False
            def add_temporary_purchase(self, user_id, item_type, duration):
                return False
            def get_active_temporary_roles(self, user_id=None):
                return []
            def get_pending_reminders(self):
                return []
            def claim_daily_bonus(self, user_id):
                return {"success": False, "error": "Database not available"}
            def remove_coins(self, user_id, amount):
                return False
            def get_leaderboard(self, field, limit=10):
                return []
            def get_active_temporary_purchases(self, user_id):
                return []
            def get_database_health(self):
                return {"status": "disconnected", "connected": False}
            def get_database_stats(self):
                return {"total_users": 0}
        
        db = MinimalDB()

# Additional compatibility functions
def cleanup_expired_items():
    """Clean up expired items from database"""
    try:
        if hasattr(db, 'connected') and db.connected and hasattr(db, 'users_collection'):
            # Clean up expired temporary purchases
            current_time = time.time()
            db.users_collection.update_many(
                {},
                {"$pull": {"temporary_purchases": {"expires_at": {"$lt": current_time}}}}
            )
            
            # Clean up expired temporary roles
            db.users_collection.update_many(
                {},
                {"$pull": {"temporary_roles": {"expires_at": {"$lt": current_time}}}}
            )
            
            print("🧹 Cleaned up expired items from database")
        else:
            print("🧹 Cleanup skipped (database not connected)")
    except Exception as e:
        print(f"❌ Error in cleanup: {e}")

def get_database():
    """Get the database instance"""
    return db

def get_active_temporary_roles(user_id=None):
    """Get active temporary roles for a user or all users"""
    try:
        return db.get_active_temporary_roles(user_id)
    except Exception as e:
        # Only log the first error to avoid spam
        if not hasattr(get_active_temporary_roles, '_error_logged'):
            print(f"❌ Error getting active temporary roles: {e}")
            get_active_temporary_roles._error_logged = True
        return []

def get_pending_reminders():
    """Get pending reminders"""
    try:
        return db.get_pending_reminders()
    except Exception as e:
        # Only log the first error to avoid spam
        if not hasattr(get_pending_reminders, '_error_logged'):
            print(f"❌ Error getting pending reminders: {e}")
            get_pending_reminders._error_logged = True
        return []