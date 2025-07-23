# Compatibility wrapper for database imports
# This file provides backward compatibility for cogs that import 'database' directly

try:
    from core.database import *
    from core.database import get_db_manager, initialize_database
    
    # Create a global db instance for backward compatibility
    db_manager = get_db_manager()
    if db_manager:
        db = db_manager
    else:
        # Fallback database implementation
        import os
        from pymongo import MongoClient
        from datetime import datetime, timedelta
        import time
        
        class DatabaseManager:
            def __init__(self):
                self.client = None
                self.db = None
                self.users_collection = None
                self.guilds_collection = None
                self.initialize()
            
            def initialize(self):
                try:
                    mongodb_uri = os.getenv('MONGODB_URI')
                    if mongodb_uri:
                        self.client = MongoClient(mongodb_uri)
                        self.db = self.client.get_default_database()
                        self.users_collection = self.db.users
                        self.guilds_collection = self.db.guilds
                        print("✅ Database connection established")
                    else:
                        print("⚠️ No MONGODB_URI found, using fallback")
                        self.users_collection = FallbackCollection()
                        self.guilds_collection = FallbackCollection()
                except Exception as e:
                    print(f"❌ Database connection failed: {e}")
                    self.users_collection = FallbackCollection()
                    self.guilds_collection = FallbackCollection()
            
            def get_user_data(self, user_id):
                try:
                    if hasattr(self.users_collection, 'find_one'):
                        result = self.users_collection.find_one({"user_id": user_id})
                        return result if result else {}
                    else:
                        return {}
                except:
                    return {}
            
            def update_user_data(self, user_id, data):
                try:
                    if hasattr(self.users_collection, 'update_one'):
                        self.users_collection.update_one(
                            {"user_id": user_id},
                            {"$set": data},
                            upsert=True
                        )
                        return True
                except:
                    pass
                return False
            
            def add_coins(self, user_id, amount):
                try:
                    if hasattr(self.users_collection, 'update_one'):
                        self.users_collection.update_one(
                            {"user_id": user_id},
                            {"$inc": {"coins": amount}},
                            upsert=True
                        )
                        return True
                except:
                    pass
                return False
            
            def add_temporary_purchase(self, user_id, item_type, duration):
                try:
                    expiry_time = time.time() + duration
                    purchase_data = {
                        "item_type": item_type,
                        "expiry_time": expiry_time,
                        "purchased_at": time.time()
                    }
                    
                    if hasattr(self.users_collection, 'update_one'):
                        self.users_collection.update_one(
                            {"user_id": user_id},
                            {"$push": {"temporary_purchases": purchase_data}},
                            upsert=True
                        )
                        return True
                except:
                    pass
                return False
        
        class FallbackCollection:
            def __init__(self):
                self.data = {}
            
            def find_one(self, query):
                user_id = query.get("user_id")
                return self.data.get(user_id, {})
            
            def update_one(self, query, update, upsert=False):
                user_id = query.get("user_id")
                if "$set" in update:
                    if user_id not in self.data:
                        self.data[user_id] = {}
                    self.data[user_id].update(update["$set"])
                elif "$inc" in update:
                    if user_id not in self.data:
                        self.data[user_id] = {}
                    for key, value in update["$inc"].items():
                        self.data[user_id][key] = self.data[user_id].get(key, 0) + value
                elif "$push" in update:
                    if user_id not in self.data:
                        self.data[user_id] = {}
                    for key, value in update["$push"].items():
                        if key not in self.data[user_id]:
                            self.data[user_id][key] = []
                        self.data[user_id][key].append(value)
        
        # Create fallback database instance
        db = DatabaseManager()

except ImportError as e:
    print(f"⚠️ Core database import failed: {e}")
    # Create minimal fallback
    class MinimalDB:
        def get_user_data(self, user_id):
            return {}
        def update_user_data(self, user_id, data):
            return False
        def add_coins(self, user_id, amount):
            return False
        def add_temporary_purchase(self, user_id, item_type, duration):
            return False
    
    db = MinimalDB()

# Additional compatibility functions
def cleanup_expired_items():
    """Clean up expired items from database"""
    try:
        if hasattr(db, 'users_collection') and hasattr(db.users_collection, 'update_many'):
            # Remove expired temporary purchases
            current_time = time.time()
            db.users_collection.update_many(
                {},
                {"$pull": {"temporary_purchases": {"expiry_time": {"$lt": current_time}}}}
            )
            print("🧹 Cleaned up expired items")
        else:
            print("🧹 Cleanup skipped (fallback mode)")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

def get_database():
    """Get database instance"""
    return db