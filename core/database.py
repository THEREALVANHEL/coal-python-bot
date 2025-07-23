import motor.motor_asyncio
import pymongo
import os
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Enhanced database manager with connection pooling and caching"""
    
    def __init__(self, mongodb_uri: str):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.connection_pool_size = 50
        self.setup_connection()
    
    def setup_connection(self):
        """Setup MongoDB connection with enhanced configuration"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.mongodb_uri,
                maxPoolSize=self.connection_pool_size,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=10000,
                connectTimeoutMS=10000,
                retryWrites=True,
                retryReads=True,
                w="majority",
                readPreference="primaryPreferred"
            )
            self.db = self.client.coal_bot
            logger.info("✅ Enhanced database connection established")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_timestamps:
            return False
        return time.time() - self.cache_timestamps[cache_key] < self.cache_ttl
    
    def _set_cache(self, cache_key: str, data: Any):
        """Set data in cache with timestamp"""
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()
    
    def _get_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        return None
    
    async def get_user_data_cached(self, user_id: int) -> Dict[str, Any]:
        """Get user data with caching"""
        cache_key = f"user_{user_id}"
        
        # Try cache first
        cached_data = self._get_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fetch from database
        try:
            data = await self.db.users.find_one({"user_id": user_id})
            if data is None:
                data = self._create_default_user_data(user_id)
                await self.db.users.insert_one(data)
            
            # Cache the result
            self._set_cache(cache_key, data)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching user data for {user_id}: {e}")
            return self._create_default_user_data(user_id)
    
    async def bulk_update_users(self, updates: List[Dict[str, Any]]) -> bool:
        """Batch update multiple users at once"""
        try:
            operations = []
            for update in updates:
                operations.append(
                    pymongo.UpdateOne(
                        {"user_id": update["user_id"]}, 
                        {"$set": update["data"]}, 
                        upsert=True
                    )
                )
            
            if operations:
                result = await self.db.users.bulk_write(operations)
                
                # Invalidate cache for updated users
                for update in updates:
                    cache_key = f"user_{update['user_id']}"
                    if cache_key in self.cache:
                        del self.cache[cache_key]
                        del self.cache_timestamps[cache_key]
                
                return result.acknowledged
            return True
            
        except Exception as e:
            logger.error(f"Bulk update failed: {e}")
            return False
    
    async def update_user_data_cached(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update user data and invalidate cache"""
        try:
            data['last_updated'] = time.time()
            result = await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": data},
                upsert=True
            )
            
            # Invalidate cache
            cache_key = f"user_{user_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]
                del self.cache_timestamps[cache_key]
            
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Error updating user data for {user_id}: {e}")
            return False
    
    async def get_multiple_users(self, user_ids: List[int]) -> List[Dict[str, Any]]:
        """Get multiple users in parallel"""
        tasks = []
        for user_id in user_ids:
            tasks.append(self.get_user_data_cached(user_id))
        return await asyncio.gather(*tasks)
    
    async def get_leaderboard_cached(self, field: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard with caching"""
        cache_key = f"leaderboard_{field}_{limit}"
        
        # Try cache first
        cached_data = self._get_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            cursor = self.db.users.find({field: {"$exists": True}}).sort(field, -1).limit(limit)
            data = await cursor.to_list(length=limit)
            
            # Cache the result with shorter TTL for leaderboards
            self.cache[cache_key] = data
            self.cache_timestamps[cache_key] = time.time()
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching leaderboard: {e}")
            return []
    
    async def log_transaction(self, user_id: int, transaction_type: str, amount: int, details: Dict[str, Any] = None):
        """Log transaction for audit trail"""
        try:
            transaction = {
                "user_id": user_id,
                "type": transaction_type,
                "amount": amount,
                "details": details or {},
                "timestamp": datetime.now(),
                "ip_hash": None  # Could add IP hashing for security
            }
            await self.db.transactions.insert_one(transaction)
        except Exception as e:
            logger.error(f"Error logging transaction: {e}")
    
    async def get_transaction_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user transaction history"""
        try:
            cursor = self.db.transactions.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error fetching transaction history: {e}")
            return []
    
    async def track_command_usage(self, command: str, user_id: int, guild_id: int = None):
        """Track command usage for analytics"""
        try:
            await self.db.analytics.update_one(
                {"type": "command_usage", "command": command, "date": datetime.now().date().isoformat()},
                {
                    "$inc": {"count": 1},
                    "$addToSet": {"users": user_id},
                    "$set": {"last_used": datetime.now()}
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error tracking command usage: {e}")
    
    async def get_server_stats(self) -> Dict[str, Any]:
        """Get comprehensive server statistics"""
        try:
            stats = {}
            
            # User statistics
            stats['total_users'] = await self.db.users.count_documents({})
            stats['active_users_24h'] = await self.db.users.count_documents({
                "last_updated": {"$gte": time.time() - 86400}
            })
            
            # Economic statistics
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total_coins": {"$sum": "$coins"},
                    "total_bank": {"$sum": "$bank_balance"},
                    "avg_coins": {"$avg": "$coins"}
                }}
            ]
            economy_stats = await self.db.users.aggregate(pipeline).to_list(1)
            if economy_stats:
                stats.update(economy_stats[0])
            
            # Command usage statistics
            stats['popular_commands'] = await self.db.analytics.find(
                {"type": "command_usage"}
            ).sort("count", -1).limit(10).to_list(10)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching server stats: {e}")
            return {}
    
    def _create_default_user_data(self, user_id: int) -> Dict[str, Any]:
        """Create default user data structure"""
        return {
            "user_id": user_id,
            "coins": 100,
            "bank_balance": 0,
            "savings_balance": 0,
            "xp": 0,
            "level": 1,
            "last_work": 0,
            "last_daily": 0,
            "last_updated": time.time(),
            "job_tier": "entry",
            "successful_works": 0,
            "pets": [],
            "stocks": {},
            "items": [],
            "achievements": [],
            "settings": {
                "notifications": True,
                "dm_reminders": False,
                "privacy_mode": False
            },
            "statistics": {
                "commands_used": 0,
                "games_played": 0,
                "total_earned": 0,
                "total_spent": 0
            }
        }
    
    async def cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            del self.cache_timestamps[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            start_time = time.time()
            await self.db.command("ping")
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "cache_size": len(self.cache),
                "connection_pool_size": self.connection_pool_size
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "cache_size": len(self.cache)
            }

# Global database manager instance
db_manager = None

def initialize_database(mongodb_uri: str):
    """Initialize the global database manager"""
    global db_manager
    db_manager = DatabaseManager(mongodb_uri)
    return db_manager

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return db_manager