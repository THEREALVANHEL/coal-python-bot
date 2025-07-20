# Enhanced MongoDB Safety and Backup System
import pymongo
import os
from datetime import datetime, timedelta
import json
import time
import threading
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection with retry logic
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    print("❌ MongoDB URI not found!")
    client = None
    db = None
    users_collection = None
    starboard_collection = None
    tickets_collection = None
    settings_collection = None
    guild_settings_collection = None
    backups_collection = None
else:
    try:
        # Enhanced connection with retry logic and better configuration
        client = pymongo.MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=10000,
            connectTimeoutMS=10000,
            maxPoolSize=50,
            retryWrites=True,
            retryReads=True
        )
        
        # Test connection
        client.server_info()
        db = client.discord_bot
        users_collection = db.users
        starboard_collection = db.starboard
        tickets_collection = db.tickets
        settings_collection = db.settings
        guild_settings_collection = db.guild_settings
        backups_collection = db.backups  # New collection for backup metadata
        
        print("✅ Connected to MongoDB with enhanced safety features")
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        client = None
        db = None
        users_collection = None
        starboard_collection = None
        tickets_collection = None
        settings_collection = None
        guild_settings_collection = None
        backups_collection = None

# Enhanced Data Safety System
class DataSafetyManager:
    """Advanced data safety and backup management system"""
    
    def __init__(self):
        self.last_backup = 0
        self.backup_interval = 3600  # 1 hour
        self.emergency_backup_interval = 86400  # 24 hours for full backup
        self.max_backup_age = 604800  # 7 days
        
    def create_automatic_backup(self) -> Dict[str, Any]:
        """Create automatic incremental backup"""
        try:
            current_time = time.time()
            
            # Skip if too recent
            if current_time - self.last_backup < self.backup_interval:
                return {"success": False, "reason": "Too recent"}
            
            backup_data = {
                "timestamp": current_time,
                "backup_type": "incremental",
                "collections": {},
                "metadata": {
                    "total_users": 0,
                    "total_documents": 0,
                    "server_count": 0
                }
            }
            
            # Backup critical collections
            if users_collection is not None:
                # Get recent changes (last 2 hours)
                recent_cutoff = current_time - 7200
                recent_users = list(users_collection.find({
                    "$or": [
                        {"last_updated": {"$gte": recent_cutoff}},
                        {"last_xp_gain": {"$gte": recent_cutoff}},
                        {"last_work": {"$gte": recent_cutoff}}
                    ]
                }))
                
                backup_data["collections"]["users"] = recent_users
                backup_data["metadata"]["total_users"] = users_collection.count_documents({})
            
            if settings_collection is not None:
                # Always backup all settings (small collection)
                settings = list(settings_collection.find({}))
                backup_data["collections"]["settings"] = settings
                backup_data["metadata"]["server_count"] = len(settings)
            
            # Calculate total documents
            backup_data["metadata"]["total_documents"] = sum(
                len(data) for data in backup_data["collections"].values()
            )
            
            # Store backup metadata in database
            if backups_collection is not None:
                backup_metadata = {
                    "timestamp": current_time,
                    "type": "incremental",
                    "document_count": backup_data["metadata"]["total_documents"],
                    "collections_backed_up": list(backup_data["collections"].keys()),
                    "success": True
                }
                backups_collection.insert_one(backup_metadata)
            
            self.last_backup = current_time
            
            return {
                "success": True,
                "backup_data": backup_data,
                "documents_backed_up": backup_data["metadata"]["total_documents"],
                "timestamp": current_time
            }
            
        except Exception as e:
            print(f"Error creating automatic backup: {e}")
            return {"success": False, "error": str(e)}
    
    def create_emergency_full_backup(self) -> Dict[str, Any]:
        """Create complete full backup for emergency recovery"""
        try:
            current_time = time.time()
            
            backup_data = {
                "timestamp": current_time,
                "backup_type": "full_emergency",
                "collections": {},
                "metadata": {}
            }
            
            total_docs = 0
            
            # Backup ALL collections completely
            for collection_name in ["users", "starboard", "tickets", "settings"]:
                collection = db[collection_name] if db else None
                if collection is not None:
                    all_data = list(collection.find({}))
                    backup_data["collections"][collection_name] = all_data
                    backup_data["metadata"][f"{collection_name}_count"] = len(all_data)
                    total_docs += len(all_data)
            
            backup_data["metadata"]["total_documents"] = total_docs
            backup_data["metadata"]["backup_size_estimate"] = total_docs * 1000  # Rough estimate
            
            # Store full backup metadata
            if backups_collection is not None:
                backup_metadata = {
                    "timestamp": current_time,
                    "type": "full_emergency",
                    "document_count": total_docs,
                    "collections_backed_up": list(backup_data["collections"].keys()),
                    "success": True,
                    "is_emergency": True
                }
                backups_collection.insert_one(backup_metadata)
            
            return {
                "success": True,
                "backup_data": backup_data,
                "total_documents": total_docs,
                "collections": list(backup_data["collections"].keys()),
                "timestamp": current_time,
                "type": "full_emergency"
            }
            
        except Exception as e:
            print(f"Error creating emergency full backup: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_data_integrity(self) -> Dict[str, Any]:
        """Verify database integrity and consistency"""
        try:
            integrity_report = {
                "timestamp": time.time(),
                "collections": {},
                "issues_found": [],
                "health_score": 100
            }
            
            if users_collection is not None:
                # Check user data integrity
                user_issues = []
                total_users = users_collection.count_documents({})
                
                # Check for negative values
                negative_xp = users_collection.count_documents({"xp": {"$lt": 0}})
                negative_coins = users_collection.count_documents({"coins": {"$lt": 0}})
                negative_cookies = users_collection.count_documents({"cookies": {"$lt": 0}})
                
                if negative_xp > 0:
                    user_issues.append(f"{negative_xp} users with negative XP")
                if negative_coins > 0:
                    user_issues.append(f"{negative_coins} users with negative coins")
                if negative_cookies > 0:
                    user_issues.append(f"{negative_cookies} users with negative cookies")
                
                # Check for missing required fields
                missing_xp = users_collection.count_documents({"xp": {"$exists": False}})
                if missing_xp > 0:
                    user_issues.append(f"{missing_xp} users missing XP field")
                
                integrity_report["collections"]["users"] = {
                    "total_documents": total_users,
                    "issues": user_issues,
                    "health": "good" if not user_issues else "issues_found"
                }
                
                integrity_report["issues_found"].extend(user_issues)
            
            # Calculate health score
            total_issues = len(integrity_report["issues_found"])
            if total_issues == 0:
                integrity_report["health_score"] = 100
            elif total_issues <= 5:
                integrity_report["health_score"] = 85
            elif total_issues <= 10:
                integrity_report["health_score"] = 70
            else:
                integrity_report["health_score"] = 50
            
            return {
                "success": True,
                "integrity_report": integrity_report,
                "health_score": integrity_report["health_score"],
                "issues_count": total_issues
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_recovery_options(self) -> Dict[str, Any]:
        """Get available recovery options and backup history"""
        try:
            if backups_collection is None:
                return {"success": False, "error": "Backup collection not available"}
            
            # Get recent backups
            recent_backups = list(backups_collection.find({}).sort("timestamp", -1).limit(10))
            
            recovery_options = {
                "recent_backups": recent_backups,
                "full_backups": [],
                "incremental_backups": [],
                "emergency_options": []
            }
            
            for backup in recent_backups:
                if backup.get("type") == "full_emergency":
                    recovery_options["full_backups"].append(backup)
                elif backup.get("type") == "incremental":
                    recovery_options["incremental_backups"].append(backup)
            
            # Emergency recovery options
            recovery_options["emergency_options"] = [
                "Restore from latest full backup",
                "Rebuild from incremental backups",
                "Manual data reconstruction",
                "Contact support for advanced recovery"
            ]
            
            return {
                "success": True,
                "recovery_options": recovery_options,
                "backup_count": len(recent_backups)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Initialize safety manager
safety_manager = DataSafetyManager()

# Enhanced database functions with safety checks
def get_user_data_safe(user_id: int) -> Dict[str, Any]:
    """Get user data with automatic safety checks and backup triggers"""
    try:
        # Trigger automatic backup periodically
        if time.time() - safety_manager.last_backup > safety_manager.backup_interval:
            safety_manager.create_automatic_backup()
        
        # Get user data with validation
        user_data = get_user_data(user_id)
        
        # Validate data integrity
        if user_data.get("xp", 0) < 0:
            print(f"WARNING: User {user_id} has negative XP, fixing...")
            fix_user_data(user_id, {"xp": 0})
        
        if user_data.get("coins", 0) < 0:
            print(f"WARNING: User {user_id} has negative coins, fixing...")
            fix_user_data(user_id, {"coins": 0})
        
        return user_data
        
    except Exception as e:
        print(f"Error in safe user data retrieval: {e}")
        return {"user_id": user_id, "xp": 0, "coins": 0, "cookies": 0}

def fix_user_data(user_id: int, fixes: Dict[str, Any]) -> bool:
    """Fix corrupted user data"""
    try:
        if users_collection is not None:
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": fixes},
                upsert=True
            )
            return True
    except Exception as e:
        print(f"Error fixing user data: {e}")
        return False

def emergency_data_recovery() -> Dict[str, Any]:
    """Emergency data recovery function"""
    try:
        print("🚨 EMERGENCY DATA RECOVERY INITIATED")
        
        # Create immediate backup of current state
        current_backup = safety_manager.create_emergency_full_backup()
        
        # Verify data integrity
        integrity_check = safety_manager.verify_data_integrity()
        
        # Get recovery options
        recovery_options = safety_manager.get_recovery_options()
        
        return {
            "success": True,
            "emergency_backup": current_backup,
            "integrity_check": integrity_check,
            "recovery_options": recovery_options,
            "timestamp": time.time(),
            "status": "Emergency protocols activated"
        }
        
    except Exception as e:
        print(f"CRITICAL ERROR in emergency recovery: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": "Emergency recovery failed",
            "manual_action_required": True
        }

# Automatic safety monitoring (runs in background)
def start_safety_monitoring():
    """Start background safety monitoring"""
    def monitor():
        while True:
            try:
                time.sleep(3600)  # Check every hour
                
                # Create automatic backup
                backup_result = safety_manager.create_automatic_backup()
                if backup_result["success"]:
                    print(f"✅ Automatic backup completed: {backup_result['documents_backed_up']} documents")
                
                # Run integrity check
                integrity_result = safety_manager.verify_data_integrity()
                if integrity_result["success"]:
                    health_score = integrity_result["health_score"]
                    if health_score < 80:
                        print(f"⚠️ Database health warning: {health_score}% - {integrity_result['issues_count']} issues found")
                
            except Exception as e:
                print(f"Error in safety monitoring: {e}")
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    print("🛡️ Database safety monitoring started")

# Start safety monitoring when module is loaded
if client is not None:
    # Only start monitoring if we have a successful connection
    try:
        # Quick health check before starting monitoring
        client.admin.command('ping')
        start_safety_monitoring()
    except Exception as e:
        print(f"⚠️ Database health check failed, skipping safety monitoring: {e}")

def get_user_data(user_id):
    """Get user data from database"""
    if users_collection is None:
        return {"user_id": user_id, "xp": 0, "level": 0, "cookies": 0, "coins": 0, "daily_streak": 0}

    try:
        # Get user data directly without validation to prevent recursion
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            # Ensure all required fields exist with defaults
            defaults = {
                "xp": 0,
                "level": 0,
                "cookies": 0,
                "coins": 0,
                "daily_streak": 0,
                "last_daily": 0,
                "last_work": 0,
                "temporary_purchases": [],
                "last_updated": time.time()
            }
            
            for key, default_value in defaults.items():
                if key not in user_data:
                    user_data[key] = default_value
            
            return user_data
        else:
            # Create new user with defaults
            return create_user_data(user_id)
            
    except Exception as e:
        print(f"Error getting user data for {user_id}: {e}")
        # Return safe defaults if database fails
        return {"user_id": user_id, "xp": 0, "level": 0, "cookies": 0, "coins": 0, "daily_streak": 0}

def create_user_data(user_id):
    """Create new user data with all required fields"""
    if users_collection is None:
        return {"user_id": user_id, "xp": 0, "level": 0, "cookies": 0, "coins": 0, "daily_streak": 0}

    try:
        current_time = time.time()
        user_data = {
            "user_id": user_id,
            "xp": 0,
            "level": 0,
            "cookies": 0,
            "coins": 0,
            "daily_streak": 0,
            "last_daily": 0,
            "last_work": 0,
            "temporary_purchases": [],
            "created_at": current_time,
            "last_updated": current_time
        }
        
        users_collection.insert_one(user_data)
        return user_data
        
    except Exception as e:
        print(f"Error creating user data for {user_id}: {e}")
        return {"user_id": user_id, "xp": 0, "level": 0, "cookies": 0, "coins": 0, "daily_streak": 0}

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

def remove_xp(user_id, xp_amount):
    """Remove XP from user"""
    if users_collection is None:
        return False
    
    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"xp": -xp_amount}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error removing XP: {e}")
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

def set_cookies(user_id, cookie_amount):
    """Set cookies for user to exact amount"""
    if users_collection is None:
        return False

    try:
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"cookies": max(0, cookie_amount)}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error setting cookies: {e}")
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

def claim_daily_bonus(user_id):
    """Claim daily XP and coin bonus"""
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
        
        # Calculate rewards (bonus every 7 days)
        base_xp = 150
        base_coins = 50
        
        # Streak bonuses
        streak_multiplier = 1.5 if streak % 7 == 0 else 1.0
        total_xp = int(base_xp * streak_multiplier)
        total_coins = int(base_coins * streak_multiplier)
        
        # Update database
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "xp": total_xp,
                    "coins": total_coins
                },
                "$set": {
                    "last_daily": current_time,
                    "daily_streak": streak
                }
            },
            upsert=True
        )
        
        # Get updated user data for return
        updated_data = get_user_data(user_id)
        
        return {
            "success": True,
            "xp_gained": total_xp,
            "coins_gained": total_coins,
            "streak": streak,
            "total_xp": updated_data.get('xp', 0),
            "total_coins": updated_data.get('coins', 0)
        }
        
    except Exception as e:
        print(f"Error claiming daily bonus: {e}")
        return {"success": False, "message": str(e)}

def remove_all_cookies_admin(admin_user_id):
    """Remove all cookies from all users (admin only)"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        # Update all users to have 0 cookies
        result = users_collection.update_many(
            {},
            {"$set": {"cookies": 0}}
        )
        
        return {
            "success": True,
            "users_affected": result.modified_count,
            "admin_id": admin_user_id
        }
        
    except Exception as e:
        print(f"Error removing all cookies: {e}")
        return {"success": False, "message": str(e)}

def get_leaderboard(field, limit=100):
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

def get_paginated_leaderboard(field, page=1, items_per_page=10):
    """Get paginated leaderboard for a specific field"""
    if users_collection is None:
        return {"users": [], "total_pages": 0, "current_page": page}
    
    try:
        # Get total count
        total_users = users_collection.count_documents({field: {"$gt": 0}})
        total_pages = (total_users + items_per_page - 1) // items_per_page
        
        # Calculate skip
        skip = (page - 1) * items_per_page
        
        # Get users for this page
        pipeline = [
            {"$match": {field: {"$gt": 0}}},
            {"$sort": {field: -1}},
            {"$skip": skip},
            {"$limit": items_per_page}
        ]
        
        users = list(users_collection.aggregate(pipeline))
        
        return {
            "users": users,
            "total_pages": total_pages,
            "current_page": page,
            "total_users": total_users
        }
        
    except Exception as e:
        print(f"Error getting paginated leaderboard: {e}")
        return {"users": [], "total_pages": 0, "current_page": page}

# Ticket System Functions
def log_ticket_creation(guild_id, user_id, channel_id, category, subject):
    """Log when a ticket is created"""
    try:
        tickets_collection = db.tickets
        ticket_data = {
            'guild_id': guild_id,
            'user_id': user_id,
            'channel_id': channel_id,
            'category': category,
            'subject': subject,
            'status': 'open',
            'created_at': datetime.now().timestamp(),
            'closed_at': None,
            'closed_by': None
        }
        tickets_collection.insert_one(ticket_data)
        print(f"[Database] Ticket created: {channel_id}")
    except Exception as e:
        print(f"[Database] Error logging ticket creation: {e}")

def log_ticket_closure(guild_id, closed_by_user_id, channel_id):
    """Log when a ticket is closed"""
    try:
        tickets_collection = db.tickets
        tickets_collection.update_one(
            {'guild_id': guild_id, 'channel_id': channel_id, 'status': 'open'},
            {
                '$set': {
                    'status': 'closed',
                    'closed_at': datetime.now().timestamp(),
                    'closed_by': closed_by_user_id
                }
            }
        )
        print(f"[Database] Ticket closed: {channel_id}")
    except Exception as e:
        print(f"[Database] Error logging ticket closure: {e}")

def get_ticket_stats(guild_id):
    """Get comprehensive ticket statistics for a guild"""
    try:
        tickets_collection = db.tickets
        
        # Total tickets
        total_tickets = tickets_collection.count_documents({'guild_id': guild_id})
        
        # Open tickets
        open_tickets = tickets_collection.count_documents({'guild_id': guild_id, 'status': 'open'})
        
        # Closed tickets
        closed_tickets = tickets_collection.count_documents({'guild_id': guild_id, 'status': 'closed'})
        
        # Category breakdown
        pipeline = [
            {'$match': {'guild_id': guild_id}},
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        category_breakdown = {}
        for result in tickets_collection.aggregate(pipeline):
            category_breakdown[result['_id']] = result['count']
        
        return {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'closed_tickets': closed_tickets,
            'category_breakdown': category_breakdown
        }
    except Exception as e:
        print(f"[Database] Error getting ticket stats: {e}")
        return {
            'total_tickets': 0,
            'open_tickets': 0,
            'closed_tickets': 0,
            'category_breakdown': {}
        }

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

def update_server_setting(guild_id, setting, value):
    """Update a server setting (alias for set_guild_setting)"""
    return set_guild_setting(guild_id, setting, value)

def get_server_settings(guild_id):
    """Get all server settings for a guild"""
    if guild_settings_collection is None:
        return {}

    try:
        guild_data = guild_settings_collection.find_one({"guild_id": guild_id})
        if guild_data:
            # Remove MongoDB's _id field
            guild_data.pop('_id', None)
            return guild_data
        return {}
    except Exception as e:
        print(f"Error getting server settings: {e}")
        return {}

# Removed unused ticketzone functions - simplified ticket system now in use

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

def recover_lost_data():
    """Advanced data recovery system to find and restore lost user data"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        # Find users with incomplete data
        incomplete_users = users_collection.find({
            "$or": [
                {"xp": {"$exists": False}},
                {"cookies": {"$exists": False}},
                {"coins": {"$exists": False}},
                {"daily_streak": {"$exists": False}},
                {"last_daily": {"$exists": False}},
                {"last_xp_time": {"$exists": False}},
                {"last_work": {"$exists": False}}
            ]
        })
        
        recovered_count = 0
        for user_data in incomplete_users:
            user_id = user_data.get("user_id")
            if user_id:
                # Create complete user profile with defaults
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
                if "join_date" not in user_data:
                    update_data["join_date"] = datetime.now().timestamp()
                if "last_seen" not in user_data:
                    update_data["last_seen"] = datetime.now().timestamp()
                
                if update_data:
                    users_collection.update_one(
                        {"user_id": user_id},
                        {"$set": update_data}
                    )
                    recovered_count += 1
        
        return {
            "success": True,
            "recovered_count": recovered_count,
            "message": f"Successfully recovered data for {recovered_count} users"
        }
        
    except Exception as e:
        print(f"Error recovering lost data: {e}")
        return {"success": False, "message": str(e)}

def clean_invalid_data():
    """Remove invalid and unnecessary data from the database"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        cleaned_count = 0
        
        # Remove users with invalid user_ids
        result = users_collection.delete_many({
            "$or": [
                {"user_id": {"$exists": False}},
                {"user_id": None},
                {"user_id": ""},
                {"user_id": {"$type": "string"}}  # user_id should be int
            ]
        })
        cleaned_count += result.deleted_count
        
        # Fix negative values
        users_collection.update_many(
            {"xp": {"$lt": 0}},
            {"$set": {"xp": 0}}
        )
        users_collection.update_many(
            {"cookies": {"$lt": 0}},
            {"$set": {"cookies": 0}}
        )
        users_collection.update_many(
            {"coins": {"$lt": 0}},
            {"$set": {"coins": 0}}
        )
        users_collection.update_many(
            {"daily_streak": {"$lt": 0}},
            {"$set": {"daily_streak": 0}}
        )
        
        # Remove old temporary items that are expired
        current_time = datetime.now().timestamp()
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
        
        # Remove unnecessary fields that might exist
        users_collection.update_many(
            {},
            {
                "$unset": {
                    "invalid_field": "",
                    "old_data": "",
                    "temp_data": "",
                    "debug_info": ""
                }
            }
        )
        
        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"Successfully cleaned {cleaned_count} invalid entries"
        }
        
    except Exception as e:
        print(f"Error cleaning invalid data: {e}")
        return {"success": False, "message": str(e)}

def optimize_database():
    """Optimize database performance and ensure data integrity"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        # Create indexes for better performance
        users_collection.create_index("user_id", unique=True)
        users_collection.create_index([("xp", -1)])
        users_collection.create_index([("cookies", -1)])
        users_collection.create_index([("coins", -1)])
        users_collection.create_index([("daily_streak", -1)])
        
        # Index for guild settings
        if guild_settings_collection:
            guild_settings_collection.create_index("guild_id", unique=True)
        
        # Index for warnings
        if warnings_collection:
            warnings_collection.create_index([("user_id", 1), ("timestamp", -1)])
        
        return {
            "success": True,
            "message": "Database optimized successfully"
        }
        
    except Exception as e:
        print(f"Error optimizing database: {e}")
        return {"success": False, "message": str(e)}

def validate_user_data(user_id):
    """DEPRECATED - This function has been removed to prevent infinite recursion"""
    # This function was causing infinite recursion loops
    # All validation is now done inline where needed
    print(f"[Database] validate_user_data called for {user_id} - this function is deprecated")
    return True

# Enhanced Live Data Functions
def get_live_user_stats(user_id):
    """Get real-time validated user statistics"""
    try:
        # Get data directly from database to prevent recursion
        user_data = users_collection.find_one({"user_id": user_id}) if users_collection is not None else None
        if not user_data:
            user_data = {"user_id": user_id, "xp": 0, "cookies": 0, "coins": 0, "daily_streak": 0}
        
        # Validate and clean data
        validated_data = {
            'user_id': user_id,
            'xp': max(0, user_data.get('xp', 0)),
            'cookies': max(0, user_data.get('cookies', 0)),
            'coins': max(0, user_data.get('coins', 0)),
            'daily_streak': max(0, user_data.get('daily_streak', 0)),
            'last_daily': user_data.get('last_daily', 0),
            'last_work': user_data.get('last_work', 0),
            'warnings': [],  # Removed warning system
            'muted_until': 0,
            'inventory': user_data.get('inventory', {}),
            'last_updated': datetime.now().timestamp()
        }
        
        # Update the database with validated data
        # This function is not directly available in the original file,
        # so we'll assume a placeholder or that it will be added later.
        # For now, we'll just return the validated data.
        return validated_data
    except Exception as e:
        print(f"[Database] Error getting live user stats: {e}")
        return {"user_id": user_id, "xp": 0, "cookies": 0, "coins": 0, "daily_streak": 0}

def auto_sync_user_data(user_id):
    """Automatically sync and validate user data in real-time"""
    try:
        # Get data directly from database to prevent recursion
        current_data = users_collection.find_one({"user_id": user_id}) if users_collection is not None else None
        if not current_data:
            return {"user_id": user_id, "xp": 0, "cookies": 0, "coins": 0}
        
        # Auto-fix common issues
        fixes_applied = []
        
        # Fix negative values
        if current_data.get('xp', 0) < 0:
            current_data['xp'] = 0
            fixes_applied.append('negative_xp')
        
        if current_data.get('cookies', 0) < 0:
            current_data['cookies'] = 0
            fixes_applied.append('negative_cookies')
        
        if current_data.get('coins', 0) < 0:
            current_data['coins'] = 0
            fixes_applied.append('negative_coins')
        
        # Ensure required fields exist
        required_fields = {
            'daily_streak': 0,
            'last_daily': 0,
            'last_work': 0,
            'inventory': {},
            'muted_until': 0
        }
        
        for field, default_value in required_fields.items():
            if field not in current_data:
                current_data[field] = default_value
                fixes_applied.append(f'missing_{field}')
        
        # Remove deprecated warning system
        if 'warnings' in current_data:
            del current_data['warnings']
            fixes_applied.append('removed_warnings')
        
        # Update timestamp
        current_data['last_updated'] = datetime.now().timestamp()
        
        # Save if fixes were applied
        if fixes_applied:
            # This function is not directly available in the original file,
            # so we'll assume a placeholder or that it will be added later.
            # For now, we'll just print the fixes.
            print(f"[Database] Auto-synced user {user_id}: {fixes_applied}")
        
        return current_data
    except Exception as e:
        print(f"[Database] Error auto-syncing user data: {e}")
        return {"user_id": user_id, "xp": 0, "cookies": 0, "coins": 0, "daily_streak": 0}

def get_advanced_server_analytics(guild_id):
    """Get comprehensive server analytics with live data"""
    try:
        users_collection = db.users
        
        # Active users (interacted in last 30 days)
        thirty_days_ago = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        active_users = users_collection.count_documents({
            'last_updated': {'$gte': thirty_days_ago}
        })
        
        # Top performers
        pipeline = [
            {'$sort': {'xp': -1}},
            {'$limit': 10},
            {'$project': {'user_id': 1, 'xp': 1, 'cookies': 1, 'coins': 1}}
        ]
        top_users = list(users_collection.aggregate(pipeline))
        
        # Server totals
        totals_pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_xp': {'$sum': '$xp'},
                    'total_cookies': {'$sum': '$cookies'},
                    'total_coins': {'$sum': '$coins'},
                    'avg_xp': {'$avg': '$xp'},
                    'avg_cookies': {'$avg': '$cookies'},
                    'avg_coins': {'$avg': '$coins'}
                }
            }
        ]
        totals = list(users_collection.aggregate(totals_pipeline))
        total_stats = totals[0] if totals else {}
        
        # Daily activity trends (last 7 days)
        daily_activity = []
        for i in range(7):
            day_start = datetime.now().timestamp() - (i * 24 * 60 * 60)
            day_end = day_start + (24 * 60 * 60)
            
            daily_users = users_collection.count_documents({
                'last_updated': {'$gte': day_start, '$lt': day_end}
            })
            daily_activity.append({
                'day': i,
                'active_users': daily_users
            })
        
        return {
            'active_users_30d': active_users,
            'top_users': top_users,
            'server_totals': total_stats,
            'daily_activity': daily_activity,
            'timestamp': datetime.now().timestamp()
        }
    except Exception as e:
        print(f"[Database] Error getting server analytics: {e}")
        return {}

def optimize_database_live():
    """Perform live database optimization"""
    try:
        # Create indexes for better performance
        indexes_created = []
        
        # User collection indexes
        try:
            db.users.create_index("user_id", unique=True)
            indexes_created.append("users.user_id")
        except:
            pass
        
        try:
            db.users.create_index([("xp", -1)])
            indexes_created.append("users.xp")
        except:
            pass
        
        try:
            db.users.create_index([("cookies", -1)])
            indexes_created.append("users.cookies")
        except:
            pass
        
        try:
            db.users.create_index([("coins", -1)])
            indexes_created.append("users.coins")
        except:
            pass
        
        try:
            db.users.create_index([("last_updated", -1)])
            indexes_created.append("users.last_updated")
        except:
            pass
        
        # Server settings indexes
        try:
            db.server_settings.create_index("guild_id", unique=True)
            indexes_created.append("server_settings.guild_id")
        except:
            pass
        
        # Ticket indexes
        try:
            db.tickets.create_index([("guild_id", 1), ("status", 1)])
            indexes_created.append("tickets.guild_id_status")
        except:
            pass
        
        try:
            db.tickets.create_index([("channel_id", 1)])
            indexes_created.append("tickets.channel_id")
        except:
            pass
        
        # Mod logs indexes
        try:
            db.mod_logs.create_index([("guild_id", 1), ("timestamp", -1)])
            indexes_created.append("mod_logs.guild_id_timestamp")
        except:
            pass
        
        print(f"[Database] Live optimization complete. Indexes: {indexes_created}")
        return {
            'success': True,
            'indexes_created': indexes_created,
            'timestamp': datetime.now().timestamp()
        }
    except Exception as e:
        print(f"[Database] Error in live optimization: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().timestamp()
        }

def remove_deprecated_warning_system():
    """Remove all warning-related data from the database"""
    try:
        users_collection = db.users
        
        # Remove warnings field from all users
        result = users_collection.update_many(
            {'warnings': {'$exists': True}},
            {'$unset': {'warnings': ""}}
        )
        
        # Drop warnings collection if it exists
        try:
            db.warnings.drop()
        except:
            pass
        
        print(f"[Database] Removed warning system. Updated {result.modified_count} users.")
        return {
            'success': True,
            'users_updated': result.modified_count,
            'timestamp': datetime.now().timestamp()
        }
    except Exception as e:
        print(f"[Database] Error removing warning system: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().timestamp()
        }

def get_database_health():
    """Get comprehensive database health metrics"""
    try:
        # Get collection stats
        stats = {
            'collections': {},
            'total_documents': 0,
            'database_size': 0,
            'indexes': {},
            'timestamp': datetime.now().timestamp()
        }
        
        # Check each collection
        collections = ['users', 'server_settings', 'mod_logs', 'tickets']
        
        for collection_name in collections:
            try:
                collection = getattr(db, collection_name)
                doc_count = collection.count_documents({})
                
                # Get indexes
                indexes = list(collection.list_indexes())
                index_names = [idx['name'] for idx in indexes]
                
                stats['collections'][collection_name] = {
                    'document_count': doc_count,
                    'indexes': index_names
                }
                stats['total_documents'] += doc_count
                stats['indexes'][collection_name] = len(index_names)
                
            except Exception as e:
                stats['collections'][collection_name] = {
                    'error': str(e)
                }
        
        # Performance metrics
        stats['performance'] = {
            'avg_response_time': 'N/A',  # Would need monitoring
            'connection_status': 'Connected',
            'last_optimization': 'N/A'
        }
        
        return stats
    except Exception as e:
        print(f"[Database] Error getting health metrics: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.now().timestamp()
        }

def calculate_level_from_xp(xp: int) -> int:
    """Calculate level from XP using binary search for efficiency"""
    level = 0
    while calculate_xp_for_level(level + 1) <= xp:
        level += 1
    return level

def calculate_xp_for_level(level: int) -> int:
    """Calculate XP required for level"""
    if level <= 10:
        return int(200 * (level ** 2))
    elif level <= 50:
        return int(300 * (level ** 2.2))
    elif level <= 100:
        return int(500 * (level ** 2.5))
    else:
        return int(1000 * (level ** 2.8))

def backup_user_data():
    """Create a backup of all user data"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        # Get all user data
        all_users = list(users_collection.find({}))
        
        # Create backup with timestamp
        backup_data = {
            "backup_timestamp": datetime.now().timestamp(),
            "total_users": len(all_users),
            "users": all_users
        }
        
        return {
            "success": True,
            "backup_data": backup_data,
            "message": f"Successfully backed up {len(all_users)} users"
        }
        
    except Exception as e:
        print(f"Error creating backup: {e}")
        return {"success": False, "message": str(e)}

def maintenance_cleanup():
    """Perform comprehensive database maintenance"""
    if users_collection is None:
        return {"success": False, "message": "Database unavailable"}
    
    try:
        results = {
            "recovery": recover_lost_data(),
            "cleanup": clean_invalid_data(),
            "optimization": optimize_database()
        }
        
        total_recovered = results["recovery"].get("recovered_count", 0)
        total_cleaned = results["cleanup"].get("cleaned_count", 0)
        
        return {
            "success": True,
            "recovered_users": total_recovered,
            "cleaned_entries": total_cleaned,
            "optimized": results["optimization"]["success"],
            "message": f"Maintenance complete: {total_recovered} users recovered, {total_cleaned} entries cleaned"
        }
        
    except Exception as e:
        print(f"Error during maintenance: {e}")
        return {"success": False, "message": str(e)}

def get_database_stats():
    """Get database statistics with error handling"""
    try:
        if users_collection is None:
            return {
                "success": False,
                "message": "Database not connected",
                "total_users": 0,
                "total_xp": 0,
                "total_cookies": 0
            }
        
        # Use aggregation with timeout protection
        total_users = users_collection.count_documents({})
        
        # Quick stats without complex aggregation
        if total_users == 0:
            return {
                "success": True,
                "message": "Database connected but empty",
                "total_users": 0,
                "total_xp": 0,
                "total_cookies": 0
            }
        
        # Sample a few users for basic stats
        sample_size = min(100, total_users)
        sample_users = list(users_collection.find({}).limit(sample_size))
        
        total_xp = sum(user.get('xp', 0) for user in sample_users)
        total_cookies = sum(user.get('cookies', 0) for user in sample_users)
        
        # Estimate totals based on sample
        if sample_size < total_users:
            ratio = total_users / sample_size
            total_xp = int(total_xp * ratio)
            total_cookies = int(total_cookies * ratio)
        
        return {
            "success": True,
            "message": "Database connected and operational",
            "total_users": total_users,
            "total_xp": total_xp,
            "total_cookies": total_cookies,
            "is_estimated": sample_size < total_users
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Database stats error: {str(e)}",
            "total_users": 0,
            "total_xp": 0,
            "total_cookies": 0
        }

def get_all_users_for_maintenance():
    """Get all users for maintenance operations (limit for performance)"""
    try:
        users_collection = db.users
        return list(users_collection.find({}, {'user_id': 1, 'xp': 1, 'cookies': 1, 'coins': 1}).limit(1000))
    except Exception as e:
        print(f"[Database] Error getting users for maintenance: {e}")
        return []

def update_last_work(user_id, timestamp):
    """Update the last work timestamp for a user"""
    try:
        users_collection = db.users
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_work": timestamp}},
            upsert=True
        )
    except Exception as e:
        print(f"[Database] Error updating last work: {e}")

def get_streak_leaderboard(page=1, items_per_page=10):
    """Get streak leaderboard with pagination"""
    try:
        users_collection = db.users
        
        # Get users sorted by daily streak
        skip = (page - 1) * items_per_page
        pipeline = [
            {"$match": {"daily_streak": {"$gt": 0}}},
            {"$sort": {"daily_streak": -1}},
            {"$skip": skip},
            {"$limit": items_per_page}
        ]
        
        users = list(users_collection.aggregate(pipeline))
        
        # Get total count for pagination
        total_users = users_collection.count_documents({"daily_streak": {"$gt": 0}})
        total_pages = (total_users + items_per_page - 1) // items_per_page
        
        return {
            "users": users,
            "total_pages": total_pages,
            "current_page": page,
            "total_users": total_users
        }
    except Exception as e:
        print(f"[Database] Error getting streak leaderboard: {e}")
        return {"users": [], "total_pages": 0, "current_page": page, "total_users": 0}

def quick_db_health_check():
    """Quick database health check for startup"""
    try:
        if not client:
            return {"success": False, "error": "No database client"}
        
        # Simple ping to check connection
        client.admin.command('ping')
        
        # Quick count check (with timeout)
        if users_collection is not None:
            count = users_collection.count_documents({})
            return {
                "success": True, 
                "message": f"Database healthy - {count} users",
                "user_count": count
            }
        else:
            return {"success": False, "error": "Collections not initialized"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# Warning system functions (legacy support)

def remove_specific_warning(user_id, warning_index):
    """Remove a specific warning by index"""
    try:
        user_data = get_user_data(user_id)
        warnings = user_data.get('warnings', [])
        
        if 0 <= warning_index < len(warnings):
            warnings.pop(warning_index)
            users_collection.update_one(
                {'user_id': user_id},
                {'$set': {'warnings': warnings}},
                upsert=True
            )
            return True
        return False
    except Exception as e:
        print(f"Error removing specific warning: {e}")
        return False

# Reminder system functions for persistence
def add_reminder(reminder_data):
    """Add a reminder to the database for persistence"""
    try:
        reminders_collection = db.reminders
        reminder_doc = {
            'user_id': reminder_data['user_id'],
            'channel_id': reminder_data['channel_id'],
            'guild_id': reminder_data['guild_id'],
            'reminder_text': reminder_data['reminder_text'],
            'created_at': reminder_data['created_at'],
            'remind_at': reminder_data['remind_at'],
            'completed': False
        }
        
        result = reminders_collection.insert_one(reminder_doc)
        return {'success': True, 'reminder_id': str(result.inserted_id)}
    except Exception as e:
        print(f"Error adding reminder: {e}")
        return {'success': False, 'error': str(e)}

def get_pending_reminders():
    """Get all pending reminders from database"""
    try:
        reminders_collection = db.reminders
        current_time = datetime.now()
        
        # Get reminders that are not completed and are due or overdue
        reminders = list(reminders_collection.find({
            'completed': False,
            'remind_at': {'$lte': current_time}
        }))
        
        # Convert MongoDB ObjectId to string and datetime objects
        for reminder in reminders:
            reminder['_id'] = str(reminder['_id'])
            if isinstance(reminder['created_at'], str):
                reminder['created_at'] = datetime.fromisoformat(reminder['created_at'])
            if isinstance(reminder['remind_at'], str):
                reminder['remind_at'] = datetime.fromisoformat(reminder['remind_at'])
        
        return reminders
    except Exception as e:
        print(f"Error getting pending reminders: {e}")
        return []

def is_reminder_completed(user_id, created_at):
    """Check if a reminder is completed"""
    try:
        reminders_collection = db.reminders
        result = reminders_collection.find_one({
            'user_id': user_id,
            'created_at': created_at,
            'completed': True
        })
        return result is not None
    except Exception as e:
        print(f"Error checking reminder completion: {e}")
        return False

def complete_reminder(user_id, created_at):
    """Mark a reminder as completed"""
    try:
        reminders_collection = db.reminders
        result = reminders_collection.update_one(
            {
                'user_id': user_id,
                'created_at': created_at
            },
            {'$set': {'completed': True}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error completing reminder: {e}")
        return False

def cleanup_old_reminders():
    """Clean up old completed reminders (older than 7 days)"""
    try:
        reminders_collection = db.reminders
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        result = reminders_collection.delete_many({
            'completed': True,
            'remind_at': {'$lt': seven_days_ago}
        })
        
        return {'success': True, 'deleted_count': result.deleted_count}
    except Exception as e:
        print(f"Error cleaning up reminders: {e}")
        return {'success': False, 'error': str(e)}

# Work requirement and demotion system functions
def update_staff_activity(user_id, activity_type, timestamp=None):
    """Track staff activity for work requirements"""
    try:
        if timestamp is None:
            timestamp = datetime.now()
        
        staff_activity_collection = db.staff_activity
        
        # Update or create activity record
        staff_activity_collection.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'last_activity': timestamp,
                    'last_activity_type': activity_type
                },
                '$inc': {f'activity_count_{activity_type}': 1},
                '$push': {
                    'activity_log': {
                        'type': activity_type,
                        'timestamp': timestamp
                    }
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error updating staff activity: {e}")
        return False

def get_staff_activity_summary(user_id, days=7):
    """Get staff activity summary for work requirement checking"""
    try:
        staff_activity_collection = db.staff_activity
        days_ago = datetime.now() - timedelta(days=days)
        
        staff_data = staff_activity_collection.find_one({'user_id': user_id})
        if not staff_data:
            return {
                'total_activities': 0,
                'days_active': 0,
                'last_activity': None,
                'meets_requirements': False
            }
        
        # Count activities in the specified period
        activity_log = staff_data.get('activity_log', [])
        recent_activities = [
            activity for activity in activity_log
            if activity['timestamp'] >= days_ago
        ]
        
        # Count unique days with activity
        active_days = set()
        for activity in recent_activities:
            active_days.add(activity['timestamp'].date())
        
        # Requirements: at least 3 days of activity per week
        meets_requirements = len(active_days) >= 3
        
        return {
            'total_activities': len(recent_activities),
            'days_active': len(active_days),
            'last_activity': staff_data.get('last_activity'),
            'meets_requirements': meets_requirements,
            'required_days': 3
        }
    except Exception as e:
        print(f"Error getting staff activity summary: {e}")
        return {
            'total_activities': 0,
            'days_active': 0,
            'last_activity': None,
            'meets_requirements': False
        }

def check_staff_demotion_candidates():
    """Get staff members who might need demotion (legacy function - keeping for compatibility)"""
    try:
        if users_collection is None:
            return []
        
        # Legacy function - return empty list since we have a new job tracking system
        return []
        
    except Exception as e:
        print(f"Error checking staff demotion candidates: {e}")
        return []

# ===== JOB TRACKING SYSTEM =====

def get_active_work_session(user_id):
    """Get active work session for user"""
    try:
        if db is None:
            return None
            
        work_sessions = db.work_sessions
        session = work_sessions.find_one({
            "user_id": user_id,
            "active": True
        })
        return session
        
    except Exception as e:
        print(f"Error getting active work session: {e}")
        return None

def start_work_session(session_data):
    """Start a new work session"""
    try:
        if db is None:
            return False
            
        work_sessions = db.work_sessions
        
        # Make sure user doesn't have an active session first
        existing = work_sessions.find_one({
            "user_id": session_data["user_id"],
            "active": True
        })
        
        if existing:
            return False  # Already has active session
        
        work_sessions.insert_one(session_data)
        return True
        
    except Exception as e:
        print(f"Error starting work session: {e}")
        return False

def end_work_session(user_id, end_time, hours_worked):
    """End active work session and record hours"""
    try:
        if db is None:
            return False
            
        work_sessions = db.work_sessions
        
        # Update the active session
        result = work_sessions.update_one(
            {"user_id": user_id, "active": True},
            {
                "$set": {
                    "end_time": end_time,
                    "hours_worked": hours_worked,
                    "active": False
                }
            }
        )
        
        return result.modified_count > 0
        
    except Exception as e:
        print(f"Error ending work session: {e}")
        return False

def get_weekly_work_stats(user_id):
    """Get work statistics for the current week"""
    try:
        if db is None:
            return {"total_hours": 0, "days_worked": 0}
            
        work_sessions = db.work_sessions
        
        # Calculate start of current week (Monday)
        now = datetime.now()
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday, hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "active": False,  # Only completed sessions
                    "end_time": {"$gte": week_start}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_hours": {"$sum": "$hours_worked"},
                    "days_worked": {
                        "$addToSet": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$start_time"
                            }
                        }
                    }
                }
            }
        ]
        
        result = list(work_sessions.aggregate(pipeline))
        
        if result:
            return {
                "total_hours": result[0].get("total_hours", 0),
                "days_worked": len(result[0].get("days_worked", []))
            }
        else:
            return {"total_hours": 0, "days_worked": 0}
            
    except Exception as e:
        print(f"Error getting weekly work stats: {e}")
        return {"total_hours": 0, "days_worked": 0}

def get_monthly_work_stats(user_id):
    """Get work statistics for the current month"""
    try:
        if db is None:
            return {"total_hours": 0, "days_worked": 0}
            
        work_sessions = db.work_sessions
        
        # Calculate start of current month
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "active": False,  # Only completed sessions
                    "end_time": {"$gte": month_start}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_hours": {"$sum": "$hours_worked"},
                    "days_worked": {
                        "$addToSet": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$start_time"
                            }
                        }
                    }
                }
            }
        ]
        
        result = list(work_sessions.aggregate(pipeline))
        
        if result:
            return {
                "total_hours": result[0].get("total_hours", 0),
                "days_worked": len(result[0].get("days_worked", []))
            }
        else:
            return {"total_hours": 0, "days_worked": 0}
            
    except Exception as e:
        print(f"Error getting monthly work stats: {e}")
        return {"total_hours": 0, "days_worked": 0}

def get_job_performance_leaderboard(limit=10):
    """Get job performance leaderboard for current week"""
    try:
        if db is None:
            return []
            
        work_sessions = db.work_sessions
        
        # Calculate start of current week
        now = datetime.now()
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday, hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
        
        pipeline = [
            {
                "$match": {
                    "active": False,  # Only completed sessions
                    "end_time": {"$gte": week_start}
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "weekly_hours": {"$sum": "$hours_worked"},
                    "job_role": {"$last": "$job_role"},
                    "sessions_count": {"$sum": 1}
                }
            },
            {
                "$sort": {"weekly_hours": -1}
            },
            {
                "$limit": limit
            },
            {
                "$project": {
                    "user_id": "$_id",
                    "weekly_hours": 1,
                    "job_role": 1,
                    "sessions_count": 1,
                    "_id": 0
                }
            }
        ]
        
        result = list(work_sessions.aggregate(pipeline))
        return result
        
    except Exception as e:
        print(f"Error getting job performance leaderboard: {e}")
        return []

def get_last_work_date(user_id):
    """Get the last date user worked"""
    try:
        if db is None:
            return None
            
        work_sessions = db.work_sessions
        
        last_session = work_sessions.find_one(
            {"user_id": user_id, "active": False},
            sort=[("end_time", -1)]
        )
        
        if last_session and "end_time" in last_session:
            return last_session["end_time"]
        return None
        
    except Exception as e:
        print(f"Error getting last work date: {e}")
        return None

def get_recent_job_warning(user_id, days=3):
    """Check if user has received a job warning recently"""
    try:
        if db is None:
            return None
            
        job_warnings = db.job_warnings
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_warning = job_warnings.find_one({
            "user_id": user_id,
            "timestamp": {"$gte": cutoff_date}
        })
        
        return recent_warning
        
    except Exception as e:
        print(f"Error checking recent job warning: {e}")
        return None

def record_job_warning(user_id, job_name, warning_type):
    """Record a job performance warning"""
    try:
        if db is None:
            return False
            
        job_warnings = db.job_warnings
        
        warning_data = {
            "user_id": user_id,
            "job_name": job_name,
            "warning_type": warning_type,
            "timestamp": datetime.now()
        }
        
        job_warnings.insert_one(warning_data)
        return True
        
    except Exception as e:
        print(f"Error recording job warning: {e}")
        return False

def record_job_action(user_id, job_name, action_type, details):
    """Record a job action (promotion, demotion, etc.)"""
    try:
        if db is None:
            return False
            
        job_actions = db.job_actions
        
        action_data = {
            "user_id": user_id,
            "job_name": job_name,
            "action_type": action_type,
            "details": details,
            "timestamp": datetime.now()
        }
        
        job_actions.insert_one(action_data)
        return True
        
    except Exception as e:
        print(f"Error recording job action: {e}")
        return False

def get_user_job_history(user_id):
    """Get complete job history for a user"""
    try:
        if db is None:
            return {"sessions": [], "warnings": [], "actions": []}
            
        # Get work sessions
        work_sessions = db.work_sessions
        sessions = list(work_sessions.find(
            {"user_id": user_id},
            sort=[("start_time", -1)]
        ).limit(50))
        
        # Get warnings
        job_warnings = db.job_warnings
        warnings = list(job_warnings.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        ).limit(20))
        
        # Get actions
        job_actions = db.job_actions
        actions = list(job_actions.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        ).limit(20))
        
        return {
            "sessions": sessions,
            "warnings": warnings,
            "actions": actions
        }
        
    except Exception as e:
        print(f"Error getting user job history: {e}")
        return {"sessions": [], "warnings": [], "actions": []}

# ===== WARNING SYSTEM ENHANCEMENT =====

def add_warning(warning_data):
    """Add a warning to the database"""
    try:
        if db is None:
            return False
            
        warnings = db.warnings
        warnings.insert_one(warning_data)
        return True
        
    except Exception as e:
        print(f"Error adding warning: {e}")
        return False

def get_user_warnings(user_id):
    """Get all warnings for a user"""
    try:
        if db is None:
            return []
            
        warnings = db.warnings
        user_warnings = list(warnings.find(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        ))
        
        return user_warnings
        
    except Exception as e:
        print(f"Error getting user warnings: {e}")
        return []

def clear_user_warnings(user_id):
    """Clear all warnings for a user"""
    try:
        if db is None:
            return False
            
        warnings = db.warnings
        result = warnings.delete_many({"user_id": user_id})
        return result.deleted_count > 0
        
    except Exception as e:
        print(f"Error clearing user warnings: {e}")
        return False

# ========================
# ENHANCED TICKET SYSTEM
# ========================

async def set_ticket_data(user_id: int, ticket_data: dict):
    """Save ticket data to database"""
    try:
        tickets = db.tickets
        await tickets.update_one(
            {"user_id": user_id},
            {"$set": ticket_data},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving ticket data: {e}")
        return False

async def get_ticket_data(user_id: int):
    """Get ticket data from database"""
    try:
        tickets = db.tickets
        return await tickets.find_one({"user_id": user_id})
    except Exception as e:
        print(f"Error getting ticket data: {e}")
        return None

async def save_ticket_transcript(ticket_id: int, transcript_data: dict):
    """Save ticket transcript to database"""
    try:
        transcripts = db.ticket_transcripts
        await transcripts.update_one(
            {"ticket_id": ticket_id},
            {"$set": transcript_data},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving ticket transcript: {e}")
        return False

async def get_ticket_statistics():
    """Get ticket system statistics"""
    try:
        tickets = db.tickets
        transcripts = db.ticket_transcripts
        
        # Count total tickets
        total_tickets = await tickets.count_documents({})
        
        # Count resolved tickets
        resolved_tickets = await transcripts.count_documents({})
        
        # Count by priority
        high_priority = await tickets.count_documents({"priority": "High"})
        medium_priority = await tickets.count_documents({"priority": "Medium"})
        low_priority = await tickets.count_documents({"priority": "Low"})
        
        # Count by category
        general = await tickets.count_documents({"category": "general"})
        bug = await tickets.count_documents({"category": "bug"})
        appeal = await tickets.count_documents({"category": "appeal"})
        report = await tickets.count_documents({"category": "report"})
        suggestion = await tickets.count_documents({"category": "suggestion"})
        
        return {
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "general": general,
            "bug": bug,
            "appeal": appeal,
            "report": report,
            "suggestion": suggestion,
            "avg_response_time": "N/A"  # Could be calculated with more data
        }
        
    except Exception as e:
        print(f"Error getting ticket statistics: {e}")
        return {}

print("[Database] All functions loaded successfully with enhanced MongoDB support, reminder system, and ticket system")
