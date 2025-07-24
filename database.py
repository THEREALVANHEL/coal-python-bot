"""
Professional Discord Bot Database System
Supports MongoDB with automatic fallback to in-memory storage
"""

import os
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dependencies with fallbacks
try:
    from pymongo import MongoClient
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGODB_AVAILABLE = True
    logger.info("✅ MongoDB drivers available")
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("⚠️ MongoDB drivers not available, using memory storage")

try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ Environment variables loaded")
except ImportError:
    logger.warning("⚠️ python-dotenv not available")

class DatabaseManager:
    """
    Professional Database Manager with MongoDB and Memory Storage
    """
    
    def __init__(self):
        self.mongodb_client = None
        self.mongodb_db = None
        self.users_collection = None
        self.guilds_collection = None
        self.connected_to_mongodb = False
        
        # In-memory storage as fallback
        self.memory_users = {}
        self.memory_guilds = {}
        
        # Initialize connection
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize database connection"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            
            if MONGODB_AVAILABLE and mongodb_uri:
                # Try MongoDB connection
                self.mongodb_client = MongoClient(
                    mongodb_uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000
                )
                
                # Test connection
                self.mongodb_client.admin.command('ping')
                self.mongodb_db = self.mongodb_client.get_default_database()
                self.users_collection = self.mongodb_db.users
                self.guilds_collection = self.mongodb_db.guilds
                self.connected_to_mongodb = True
                
                logger.info("🎯 MongoDB connection established successfully!")
                return
                
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
        
        # Fallback to memory storage
        self.connected_to_mongodb = False
        logger.info("📝 Using in-memory database storage")
    
    # ==================== USER DATA OPERATIONS ====================
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data from database"""
        try:
            if self.connected_to_mongodb:
                result = self.users_collection.find_one({"user_id": user_id})
                if result:
                    return result
            else:
                if user_id in self.memory_users:
                    return self.memory_users[user_id]
            
            # Return default user data
            return self._create_default_user_data(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user data for {user_id}: {e}")
            return self._create_default_user_data(user_id)
    
    def update_user_data(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update user data in database"""
        try:
            if self.connected_to_mongodb:
                self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": data},
                    upsert=True
                )
                return True
            else:
                if user_id not in self.memory_users:
                    self.memory_users[user_id] = self._create_default_user_data(user_id)
                self.memory_users[user_id].update(data)
                return True
                
        except Exception as e:
            logger.error(f"Error updating user data for {user_id}: {e}")
            return False
    
    def _create_default_user_data(self, user_id: int) -> Dict[str, Any]:
        """Create default user data structure"""
        return {
            "user_id": user_id,
            "coins": 1000,
            "bank": 0,
            "xp": 0,
            "level": 1,
            "daily_streak": 0,
            "last_daily": 0,
            "work_streak": 0,
            "last_work": 0,
            "inventory": {},
            "achievements": [],
            "settings": {
                "notifications": True,
                "privacy": "public"
            },
            "stats": {
                "commands_used": 0,
                "messages_sent": 0,
                "time_active": 0
            },
            "economy": {
                "total_earned": 0,
                "total_spent": 0,
                "investments": {},
                "loans": []
            },
            "social": {
                "friends": [],
                "blocked": [],
                "reputation": 0
            },
            "moderation": {
                "warnings": [],
                "mutes": [],
                "notes": []
            },
            "created_at": datetime.utcnow(),
            "last_seen": datetime.utcnow()
        }
    
    # ==================== ECONOMY OPERATIONS ====================
    
    def add_coins(self, user_id: int, amount: int) -> bool:
        """Add coins to user account"""
        try:
            if self.connected_to_mongodb:
                result = self.users_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$inc": {"coins": amount, "economy.total_earned": amount},
                        "$set": {"last_seen": datetime.utcnow()}
                    },
                    upsert=True
                )
                return result.acknowledged
            else:
                if user_id not in self.memory_users:
                    self.memory_users[user_id] = self._create_default_user_data(user_id)
                self.memory_users[user_id]["coins"] += amount
                self.memory_users[user_id]["economy"]["total_earned"] += amount
                return True
                
        except Exception as e:
            logger.error(f"Error adding coins for {user_id}: {e}")
            return False
    
    def remove_coins(self, user_id: int, amount: int) -> bool:
        """Remove coins from user account"""
        try:
            user_data = self.get_user_data(user_id)
            if user_data["coins"] < amount:
                return False
            
            if self.connected_to_mongodb:
                result = self.users_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$inc": {"coins": -amount, "economy.total_spent": amount},
                        "$set": {"last_seen": datetime.utcnow()}
                    }
                )
                return result.acknowledged
            else:
                self.memory_users[user_id]["coins"] -= amount
                self.memory_users[user_id]["economy"]["total_spent"] += amount
                return True
                
        except Exception as e:
            logger.error(f"Error removing coins for {user_id}: {e}")
            return False
    
    def claim_daily_bonus(self, user_id: int) -> Dict[str, Any]:
        """Claim daily bonus with streak system"""
        try:
            user_data = self.get_user_data(user_id)
            current_time = time.time()
            last_daily = user_data.get("last_daily", 0)
            
            # Check if already claimed today
            if current_time - last_daily < 86400:  # 24 hours
                time_left = 86400 - (current_time - last_daily)
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                return {
                    "success": False,
                    "message": f"Already claimed! Next claim in {hours}h {minutes}m"
                }
            
            # Calculate streak
            streak = user_data.get("daily_streak", 0)
            if current_time - last_daily <= 172800:  # Within 48 hours
                streak += 1
            else:
                streak = 1
            
            # Calculate rewards
            base_coins = 100
            base_xp = 50
            
            # Streak bonuses
            streak_bonus = min(streak * 10, 500)  # Max 500 bonus
            total_coins = base_coins + streak_bonus
            total_xp = base_xp + (streak * 5)
            
            # Update user data
            update_data = {
                "last_daily": current_time,
                "daily_streak": streak,
                "coins": user_data["coins"] + total_coins,
                "xp": user_data["xp"] + total_xp,
                "last_seen": datetime.utcnow()
            }
            
            # Calculate new level
            new_level = self._calculate_level(update_data["xp"])
            if new_level > user_data["level"]:
                update_data["level"] = new_level
            
            self.update_user_data(user_id, update_data)
            
            return {
                "success": True,
                "coins_earned": total_coins,
                "xp_earned": total_xp,
                "streak": streak,
                "level_up": new_level > user_data["level"],
                "new_level": new_level
            }
            
        except Exception as e:
            logger.error(f"Error claiming daily bonus for {user_id}: {e}")
            return {"success": False, "message": "An error occurred"}
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate level based on XP"""
        return int((xp / 100) ** 0.5) + 1
    
    # ==================== WORK SYSTEM ====================
    
    def can_work(self, user_id: int) -> bool:
        """Check if user can work"""
        try:
            user_data = self.get_user_data(user_id)
            last_work = user_data.get("last_work", 0)
            return time.time() - last_work >= 3600  # 1 hour cooldown
        except:
            return True
    
    def process_work(self, user_id: int, job_name: str, earnings: int) -> Dict[str, Any]:
        """Process work activity"""
        try:
            user_data = self.get_user_data(user_id)
            current_time = time.time()
            
            # Update work data
            work_streak = user_data.get("work_streak", 0)
            last_work = user_data.get("last_work", 0)
            
            if current_time - last_work <= 86400:  # Within 24 hours
                work_streak += 1
            else:
                work_streak = 1
            
            update_data = {
                "last_work": current_time,
                "work_streak": work_streak,
                "coins": user_data["coins"] + earnings,
                "xp": user_data["xp"] + 25,
                "last_seen": datetime.utcnow()
            }
            
            self.update_user_data(user_id, update_data)
            
            return {
                "success": True,
                "earnings": earnings,
                "xp_gained": 25,
                "work_streak": work_streak
            }
            
        except Exception as e:
            logger.error(f"Error processing work for {user_id}: {e}")
            return {"success": False}
    
    # ==================== LEVELING SYSTEM ====================
    
    def add_xp(self, user_id: int, amount: int) -> Dict[str, Any]:
        """Add XP and handle level ups"""
        try:
            user_data = self.get_user_data(user_id)
            old_level = user_data["level"]
            new_xp = user_data["xp"] + amount
            new_level = self._calculate_level(new_xp)
            
            update_data = {
                "xp": new_xp,
                "level": new_level,
                "last_seen": datetime.utcnow()
            }
            
            self.update_user_data(user_id, update_data)
            
            return {
                "xp_gained": amount,
                "total_xp": new_xp,
                "old_level": old_level,
                "new_level": new_level,
                "leveled_up": new_level > old_level
            }
            
        except Exception as e:
            logger.error(f"Error adding XP for {user_id}: {e}")
            return {"xp_gained": 0, "leveled_up": False}
    
    # ==================== GUILD DATA OPERATIONS ====================
    
    def get_guild_data(self, guild_id: int) -> Dict[str, Any]:
        """Get guild data from database"""
        try:
            if self.connected_to_mongodb:
                result = self.guilds_collection.find_one({"guild_id": guild_id})
                if result:
                    return result
            else:
                if guild_id in self.memory_guilds:
                    return self.memory_guilds[guild_id]
            
            return self._create_default_guild_data(guild_id)
            
        except Exception as e:
            logger.error(f"Error getting guild data for {guild_id}: {e}")
            return self._create_default_guild_data(guild_id)
    
    def update_guild_data(self, guild_id: int, data: Dict[str, Any]) -> bool:
        """Update guild data in database"""
        try:
            if self.connected_to_mongodb:
                self.guilds_collection.update_one(
                    {"guild_id": guild_id},
                    {"$set": data},
                    upsert=True
                )
                return True
            else:
                if guild_id not in self.memory_guilds:
                    self.memory_guilds[guild_id] = self._create_default_guild_data(guild_id)
                self.memory_guilds[guild_id].update(data)
                return True
                
        except Exception as e:
            logger.error(f"Error updating guild data for {guild_id}: {e}")
            return False
    
    def _create_default_guild_data(self, guild_id: int) -> Dict[str, Any]:
        """Create default guild data structure"""
        return {
            "guild_id": guild_id,
            "settings": {
                "prefix": "!",
                "welcome_channel": None,
                "modlog_channel": None,
                "autorole": None
            },
            "economy": {
                "enabled": True,
                "daily_bonus": 100,
                "work_cooldown": 3600
            },
            "moderation": {
                "auto_mod": False,
                "warn_threshold": 3,
                "mute_role": None
            },
            "leveling": {
                "enabled": True,
                "xp_per_message": 15,
                "level_up_channel": None
            },
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
    
    # ==================== UTILITY METHODS ====================
    
    def get_leaderboard(self, field: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for specified field"""
        try:
            if self.connected_to_mongodb:
                cursor = self.users_collection.find().sort(field, -1).limit(limit)
                return list(cursor)
            else:
                users = list(self.memory_users.values())
                users.sort(key=lambda x: x.get(field, 0), reverse=True)
                return users[:limit]
                
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            if self.connected_to_mongodb:
                user_count = self.users_collection.count_documents({})
                guild_count = self.guilds_collection.count_documents({})
                return {
                    "users": user_count,
                    "guilds": guild_count,
                    "storage": "MongoDB",
                    "status": "Connected"
                }
            else:
                return {
                    "users": len(self.memory_users),
                    "guilds": len(self.memory_guilds),
                    "storage": "Memory",
                    "status": "Fallback"
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"users": 0, "guilds": 0, "storage": "Error", "status": "Error"}
    
    def cleanup_expired_data(self):
        """Clean up expired data"""
        try:
            current_time = time.time()
            logger.info("🧹 Starting database cleanup...")
            
            if self.connected_to_mongodb:
                # Clean up old temporary data
                self.users_collection.update_many(
                    {},
                    {"$pull": {"temporary_items": {"expires_at": {"$lt": current_time}}}}
                )
                logger.info("✅ MongoDB cleanup completed")
            else:
                # Clean up memory storage
                for user_data in self.memory_users.values():
                    if "temporary_items" in user_data:
                        user_data["temporary_items"] = [
                            item for item in user_data["temporary_items"]
                            if item.get("expires_at", 0) > current_time
                        ]
                logger.info("✅ Memory cleanup completed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Create global database instance
db = DatabaseManager()

# Legacy compatibility functions for existing cogs
def get_user_data(user_id: int) -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    return db.get_user_data(user_id)

def update_user_data(user_id: int, data: Dict[str, Any]) -> bool:
    """Legacy function for backward compatibility"""
    return db.update_user_data(user_id, data)

def add_coins(user_id: int, amount: int) -> bool:
    """Legacy function for backward compatibility"""
    return db.add_coins(user_id, amount)

def remove_coins(user_id: int, amount: int) -> bool:
    """Legacy function for backward compatibility"""
    return db.remove_coins(user_id, amount)

def get_database():
    """Get database instance"""
    return db

# Export commonly used functions
__all__ = [
    'DatabaseManager', 'db', 'get_user_data', 'update_user_data', 
    'add_coins', 'remove_coins', 'get_database'
]

logger.info("🎯 Database system initialized successfully!")
logger.info(f"📊 Storage mode: {'MongoDB' if db.connected_to_mongodb else 'Memory'}")
logger.info(f"🔧 Available methods: {len([m for m in dir(db) if not m.startswith('_')])}")