# Complete Database System for Discord Bot
# This provides full compatibility for all cogs and commands

import os
import time
import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import random
import json

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ComprehensiveDatabase:
    """Complete database system supporting all bot commands"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.guilds_collection = None
        self.connected = False
        self.initialize()
    
    def initialize(self):
        """Initialize MongoDB connection"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            if mongodb_uri:
                self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client.get_default_database()
                self.users_collection = self.db.users
                self.guilds_collection = self.db.guilds
                self.connected = True
                print("✅ Complete database system connected successfully")
            else:
                print("⚠️ No MONGODB_URI found, using in-memory fallback")
                self.connected = False
                self._setup_fallback()
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.connected = False
            self._setup_fallback()
    
    def _setup_fallback(self):
        """Setup in-memory fallback database"""
        self.memory_users = {}
        self.memory_guilds = {}
        print("🔄 Using in-memory database fallback")
    
    # ==================== USER DATA METHODS ====================
    
    def get_user_data(self, user_id):
        """Get user data"""
        try:
            if self.connected and self.users_collection:
                result = self.users_collection.find_one({"user_id": user_id})
                return result if result else self._default_user_data(user_id)
            else:
                return self.memory_users.get(user_id, self._default_user_data(user_id))
        except Exception as e:
            print(f"❌ Error getting user data: {e}")
            return self._default_user_data(user_id)
    
    def update_user_data(self, user_id, data):
        """Update user data"""
        try:
            if self.connected and self.users_collection:
                self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": data},
                    upsert=True
                )
                return True
            else:
                if user_id not in self.memory_users:
                    self.memory_users[user_id] = self._default_user_data(user_id)
                self.memory_users[user_id].update(data)
                return True
        except Exception as e:
            print(f"❌ Error updating user data: {e}")
            return False
    
    def _default_user_data(self, user_id):
        """Default user data structure"""
        return {
            "user_id": user_id,
            "coins": 1000,
            "bank": 0,
            "xp": 0,
            "level": 1,
            "last_daily_claim": 0,
            "daily_streak": 0,
            "last_work": 0,
            "work_streak": 0,
            "inventory": {},
            "temporary_purchases": [],
            "temporary_roles": [],
            "reminders": [],
            "pets": [],
            "stocks": {},
            "cookies": 0,
            "last_cookie": 0,
            "settings": {},
            "achievements": [],
            "warnings": [],
            "mutes": [],
            "bans": [],
            "tickets": [],
            "reputation": 0,
            "marriage": None,
            "job_performance": {},
            "credit_cards": [],
            "loans": [],
            "insurance": {},
            "investments": {},
            "gambling_stats": {"wins": 0, "losses": 0, "total_bet": 0, "total_won": 0}
        }
    
    # ==================== ECONOMY METHODS ====================
    
    def add_coins(self, user_id, amount):
        """Add coins to user"""
        try:
            if self.connected and self.users_collection:
                self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$inc": {"coins": amount}},
                    upsert=True
                )
                return True
            else:
                if user_id not in self.memory_users:
                    self.memory_users[user_id] = self._default_user_data(user_id)
                self.memory_users[user_id]["coins"] += amount
                return True
        except Exception as e:
            print(f"❌ Error adding coins: {e}")
            return False
    
    def remove_coins(self, user_id, amount):
        """Remove coins from user"""
        try:
            if self.connected and self.users_collection:
                self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$inc": {"coins": -amount}},
                    upsert=True
                )
                return True
            else:
                if user_id not in self.memory_users:
                    self.memory_users[user_id] = self._default_user_data(user_id)
                self.memory_users[user_id]["coins"] = max(0, self.memory_users[user_id]["coins"] - amount)
                return True
        except Exception as e:
            print(f"❌ Error removing coins: {e}")
            return False
    
    def get_leaderboard(self, field, limit=10):
        """Get leaderboard for a field"""
        try:
            if self.connected and self.users_collection:
                cursor = self.users_collection.find().sort(field, -1).limit(limit)
                return list(cursor)
            else:
                # Sort memory users by field
                sorted_users = sorted(
                    self.memory_users.values(), 
                    key=lambda x: x.get(field, 0), 
                    reverse=True
                )
                return sorted_users[:limit]
        except Exception as e:
            print(f"❌ Error getting leaderboard: {e}")
            return []
    
    # ==================== DAILY BONUS SYSTEM ====================
    
    def claim_daily_bonus(self, user_id):
        """Claim daily bonus with streak system"""
        try:
            current_time = time.time()
            user_data = self.get_user_data(user_id)
            
            # Check cooldown
            last_daily = user_data.get("last_daily_claim", 0)
            time_since_last = current_time - last_daily
            
            if time_since_last < 86400:  # 24 hours
                hours_left = int((86400 - time_since_last) / 3600)
                minutes_left = int(((86400 - time_since_last) % 3600) / 60)
                time_left = f"{hours_left}h {minutes_left}m"
                return {"success": False, "time_left": time_left}
            
            # Calculate streak
            streak = user_data.get("daily_streak", 0)
            if time_since_last <= 172800:  # Within 48 hours
                streak += 1
            else:
                streak = 1
            
            # Calculate rewards
            base_xp = 50
            base_coins = 100
            streak_multiplier = min(1 + (streak * 0.1), 3.0)
            xp_gained = int(base_xp * streak_multiplier)
            coins_gained = int(base_coins * streak_multiplier)
            
            # Weekly bonus
            if streak % 7 == 0:
                xp_gained += 200
                coins_gained += 500
            
            # Update user data
            user_data["last_daily_claim"] = current_time
            user_data["daily_streak"] = streak
            user_data["xp"] += xp_gained
            user_data["coins"] += coins_gained
            
            self.update_user_data(user_id, user_data)
            
            return {
                "success": True,
                "xp_gained": xp_gained,
                "coins_gained": coins_gained,
                "streak": streak
            }
            
        except Exception as e:
            print(f"❌ Error claiming daily bonus: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== WORK SYSTEM ====================
    
    def can_work(self, user_id):
        """Check if user can work"""
        try:
            user_data = self.get_user_data(user_id)
            last_work = user_data.get("last_work", 0)
            cooldown = 3600  # 1 hour
            return time.time() - last_work >= cooldown
        except:
            return True
    
    def do_work(self, user_id, job_name, earnings):
        """Record work activity"""
        try:
            current_time = time.time()
            user_data = self.get_user_data(user_id)
            
            user_data["last_work"] = current_time
            user_data["coins"] += earnings
            
            # Update work streak
            last_work = user_data.get("last_work", 0)
            if current_time - last_work <= 86400:  # Within 24 hours
                user_data["work_streak"] = user_data.get("work_streak", 0) + 1
            else:
                user_data["work_streak"] = 1
            
            self.update_user_data(user_id, user_data)
            return True
        except Exception as e:
            print(f"❌ Error recording work: {e}")
            return False
    
    # ==================== TEMPORARY ITEMS ====================
    
    def add_temporary_purchase(self, user_id, item_type, duration):
        """Add temporary purchase"""
        try:
            expiry_time = time.time() + duration
            purchase_data = {
                "item_type": item_type,
                "expires_at": expiry_time,
                "purchased_at": time.time()
            }
            
            user_data = self.get_user_data(user_id)
            if "temporary_purchases" not in user_data:
                user_data["temporary_purchases"] = []
            user_data["temporary_purchases"].append(purchase_data)
            
            self.update_user_data(user_id, user_data)
            return True
        except Exception as e:
            print(f"❌ Error adding temporary purchase: {e}")
            return False
    
    def get_active_temporary_purchases(self, user_id):
        """Get active temporary purchases"""
        try:
            user_data = self.get_user_data(user_id)
            current_time = time.time()
            active_purchases = []
            
            for purchase in user_data.get("temporary_purchases", []):
                if purchase.get("expires_at", 0) > current_time:
                    active_purchases.append(purchase)
            
            return active_purchases
        except Exception as e:
            print(f"❌ Error getting active purchases: {e}")
            return []
    
    def get_active_temporary_roles(self, user_id=None):
        """Get active temporary roles"""
        try:
            current_time = time.time()
            active_roles = []
            
            if user_id:
                user_data = self.get_user_data(user_id)
                for role in user_data.get("temporary_roles", []):
                    if role.get("expires_at", 0) > current_time:
                        active_roles.append(role)
            else:
                # Get all users with active roles
                if self.connected and self.users_collection:
                    users = self.users_collection.find({"temporary_roles": {"$exists": True}})
                else:
                    users = self.memory_users.values()
                
                for user_data in users:
                    for role in user_data.get("temporary_roles", []):
                        if role.get("expires_at", 0) > current_time:
                            active_roles.append(role)
            
            return active_roles
        except Exception as e:
            print(f"❌ Error getting active roles: {e}")
            return []
    
    # ==================== LEVELING SYSTEM ====================
    
    def add_xp(self, user_id, amount):
        """Add XP to user"""
        try:
            user_data = self.get_user_data(user_id)
            user_data["xp"] += amount
            
            # Calculate level
            old_level = user_data.get("level", 1)
            new_level = int((user_data["xp"] / 100) ** 0.5) + 1
            user_data["level"] = new_level
            
            self.update_user_data(user_id, user_data)
            
            return {
                "leveled_up": new_level > old_level,
                "old_level": old_level,
                "new_level": new_level,
                "total_xp": user_data["xp"]
            }
        except Exception as e:
            print(f"❌ Error adding XP: {e}")
            return {"leveled_up": False, "old_level": 1, "new_level": 1, "total_xp": 0}
    
    # ==================== PET SYSTEM ====================
    
    def get_user_pets(self, user_id):
        """Get user pets"""
        try:
            user_data = self.get_user_data(user_id)
            return user_data.get("pets", [])
        except:
            return []
    
    def add_pet(self, user_id, pet_data):
        """Add pet to user"""
        try:
            user_data = self.get_user_data(user_id)
            if "pets" not in user_data:
                user_data["pets"] = []
            user_data["pets"].append(pet_data)
            self.update_user_data(user_id, user_data)
            return True
        except:
            return False
    
    # ==================== COOKIE SYSTEM ====================
    
    def add_cookies(self, user_id, amount):
        """Add cookies to user"""
        try:
            user_data = self.get_user_data(user_id)
            user_data["cookies"] += amount
            user_data["last_cookie"] = time.time()
            self.update_user_data(user_id, user_data)
            return True
        except:
            return False
    
    def get_cookies(self, user_id):
        """Get user cookies"""
        try:
            user_data = self.get_user_data(user_id)
            return user_data.get("cookies", 0)
        except:
            return 0
    
    # ==================== MODERATION SYSTEM ====================
    
    def add_warning(self, user_id, warning_data):
        """Add warning to user"""
        try:
            user_data = self.get_user_data(user_id)
            if "warnings" not in user_data:
                user_data["warnings"] = []
            user_data["warnings"].append(warning_data)
            self.update_user_data(user_id, user_data)
            return True
        except:
            return False
    
    def get_warnings(self, user_id):
        """Get user warnings"""
        try:
            user_data = self.get_user_data(user_id)
            return user_data.get("warnings", [])
        except:
            return []
    
    # ==================== REMINDERS SYSTEM ====================
    
    def add_reminder(self, user_id, reminder_data):
        """Add reminder"""
        try:
            user_data = self.get_user_data(user_id)
            if "reminders" not in user_data:
                user_data["reminders"] = []
            user_data["reminders"].append(reminder_data)
            self.update_user_data(user_id, user_data)
            return True
        except:
            return False
    
    def get_pending_reminders(self):
        """Get pending reminders"""
        try:
            current_time = time.time()
            pending_reminders = []
            
            if self.connected and self.users_collection:
                users = self.users_collection.find({"reminders": {"$exists": True}})
            else:
                users = self.memory_users.values()
            
            for user_data in users:
                for reminder in user_data.get("reminders", []):
                    if reminder.get("remind_at", 0) <= current_time:
                        pending_reminders.append(reminder)
            
            return pending_reminders
        except Exception as e:
            print(f"❌ Error getting pending reminders: {e}")
            return []
    
    # ==================== STOCK MARKET ====================
    
    def get_user_stocks(self, user_id):
        """Get user stocks"""
        try:
            user_data = self.get_user_data(user_id)
            return user_data.get("stocks", {})
        except:
            return {}
    
    def update_user_stocks(self, user_id, stocks):
        """Update user stocks"""
        try:
            user_data = self.get_user_data(user_id)
            user_data["stocks"] = stocks
            self.update_user_data(user_id, user_data)
            return True
        except:
            return False
    
    # ==================== SETTINGS SYSTEM ====================
    
    def get_user_settings(self, user_id):
        """Get user settings"""
        try:
            user_data = self.get_user_data(user_id)
            return user_data.get("settings", {})
        except:
            return {}
    
    def update_user_settings(self, user_id, settings):
        """Update user settings"""
        try:
            user_data = self.get_user_data(user_id)
            user_data["settings"] = settings
            self.update_user_data(user_id, user_data)
            return True
        except:
            return False
    
    # ==================== GUILD DATA ====================
    
    def get_guild_data(self, guild_id):
        """Get guild data"""
        try:
            if self.connected and self.guilds_collection:
                result = self.guilds_collection.find_one({"guild_id": guild_id})
                return result if result else self._default_guild_data(guild_id)
            else:
                return self.memory_guilds.get(guild_id, self._default_guild_data(guild_id))
        except:
            return self._default_guild_data(guild_id)
    
    def update_guild_data(self, guild_id, data):
        """Update guild data"""
        try:
            if self.connected and self.guilds_collection:
                self.guilds_collection.update_one(
                    {"guild_id": guild_id},
                    {"$set": data},
                    upsert=True
                )
                return True
            else:
                if guild_id not in self.memory_guilds:
                    self.memory_guilds[guild_id] = self._default_guild_data(guild_id)
                self.memory_guilds[guild_id].update(data)
                return True
        except:
            return False
    
    def _default_guild_data(self, guild_id):
        """Default guild data"""
        return {
            "guild_id": guild_id,
            "settings": {},
            "moderation": {},
            "channels": {},
            "roles": {},
            "automod": {},
            "tickets": [],
            "economy_settings": {},
            "leveling_settings": {}
        }
    
    # ==================== SYSTEM HEALTH ====================
    
    def get_database_health(self):
        """Get database health"""
        try:
            if self.connected and self.client:
                self.client.admin.command('ping')
                return {"status": "healthy", "connected": True}
            return {"status": "fallback", "connected": False}
        except Exception as e:
            return {"status": "error", "connected": False, "error": str(e)}
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            if self.connected and self.users_collection:
                total_users = self.users_collection.count_documents({})
                total_guilds = self.guilds_collection.count_documents({}) if self.guilds_collection else 0
                return {"total_users": total_users, "total_guilds": total_guilds}
            else:
                return {"total_users": len(self.memory_users), "total_guilds": len(self.memory_guilds)}
        except:
            return {"total_users": 0, "total_guilds": 0}

# Create global database instance
db = ComprehensiveDatabase()

# Legacy compatibility functions
def cleanup_expired_items():
    """Clean up expired items"""
    try:
        current_time = time.time()
        
        if db.connected and db.users_collection:
            # Clean expired purchases
            db.users_collection.update_many(
                {},
                {"$pull": {"temporary_purchases": {"expires_at": {"$lt": current_time}}}}
            )
            # Clean expired roles
            db.users_collection.update_many(
                {},
                {"$pull": {"temporary_roles": {"expires_at": {"$lt": current_time}}}}
            )
            print("🧹 Cleaned up expired items from database")
        else:
            # Clean memory database
            for user_data in db.memory_users.values():
                if "temporary_purchases" in user_data:
                    user_data["temporary_purchases"] = [
                        p for p in user_data["temporary_purchases"] 
                        if p.get("expires_at", 0) > current_time
                    ]
                if "temporary_roles" in user_data:
                    user_data["temporary_roles"] = [
                        r for r in user_data["temporary_roles"] 
                        if r.get("expires_at", 0) > current_time
                    ]
            print("🧹 Cleaned up expired items from memory")
    except Exception as e:
        print(f"❌ Error in cleanup: {e}")

def get_database():
    """Get database instance"""
    return db

def get_active_temporary_roles(user_id=None):
    """Get active temporary roles"""
    return db.get_active_temporary_roles(user_id)

def get_pending_reminders():
    """Get pending reminders"""
    return db.get_pending_reminders()

# Additional compatibility exports
users_collection = db.users_collection if db.connected else None
guilds_collection = db.guilds_collection if db.connected else None

print("🎯 Comprehensive database system initialized - ALL COMMANDS SUPPORTED!")