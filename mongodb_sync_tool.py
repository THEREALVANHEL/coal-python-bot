#!/usr/bin/env python3
"""
MongoDB Data Synchronization and Backup Tool
For Coal Python Discord Bot

This tool helps:
1. Test MongoDB connectivity
2. Backup user data from MongoDB
3. Restore data to MongoDB
4. Migrate data between databases
5. Validate data integrity
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from pymongo import MongoClient
    from motor.motor_asyncio import AsyncIOMotorClient
    import gridfs
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.error("MongoDB drivers not available. Install with: pip install pymongo motor")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not available")

class MongoSyncTool:
    def __init__(self, mongodb_uri: Optional[str] = None):
        self.mongodb_uri = mongodb_uri or os.getenv('MONGODB_URI')
        self.client = None
        self.db = None
        self.connected = False
        
        if not MONGODB_AVAILABLE:
            raise ImportError("MongoDB drivers not installed")
            
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI not provided or set in environment")
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client['coalbot']  # Default database name
            self.connected = True
            logger.info("✅ Connected to MongoDB successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.connected = False
            return False
    
    def test_connection(self):
        """Test MongoDB connection and display database info"""
        if not self.connect():
            return False
            
        try:
            # Get database info
            server_info = self.client.server_info()
            db_stats = self.db.command("dbstats")
            
            print(f"🌟 MongoDB Connection Test Results:")
            print(f"   Server Version: {server_info.get('version', 'Unknown')}")
            print(f"   Database: {self.db.name}")
            print(f"   Collections: {len(self.db.list_collection_names())}")
            print(f"   Database Size: {db_stats.get('dataSize', 0) / 1024 / 1024:.2f} MB")
            
            # List collections
            collections = self.db.list_collection_names()
            if collections:
                print(f"   📁 Collections found: {', '.join(collections)}")
                
                # Get document counts
                for collection_name in collections:
                    count = self.db[collection_name].count_documents({})
                    print(f"      - {collection_name}: {count} documents")
            else:
                print("   📁 No collections found")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error getting database info: {e}")
            return False
    
    def backup_data(self, output_file: str = None):
        """Backup all user and guild data to JSON file"""
        if not self.connected and not self.connect():
            return False
            
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"mongodb_backup_{timestamp}.json"
            
        try:
            backup_data = {
                'metadata': {
                    'backup_date': datetime.now().isoformat(),
                    'database': self.db.name,
                    'collections': {}
                },
                'data': {}
            }
            
            # Backup each collection
            for collection_name in ['users', 'guilds']:
                if collection_name in self.db.list_collection_names():
                    collection = self.db[collection_name]
                    documents = list(collection.find({}))
                    
                    # Convert ObjectId to string for JSON serialization
                    for doc in documents:
                        if '_id' in doc:
                            doc['_id'] = str(doc['_id'])
                    
                    backup_data['data'][collection_name] = documents
                    backup_data['metadata']['collections'][collection_name] = len(documents)
                    
                    logger.info(f"📦 Backed up {len(documents)} documents from {collection_name}")
                else:
                    logger.warning(f"⚠️ Collection {collection_name} not found")
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"✅ Backup completed: {output_file}")
            print(f"📄 Backup saved to: {output_file}")
            
            # Display backup summary
            total_docs = sum(backup_data['metadata']['collections'].values())
            print(f"📊 Backup Summary:")
            print(f"   Total Documents: {total_docs}")
            for collection, count in backup_data['metadata']['collections'].items():
                print(f"   - {collection}: {count} documents")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def restore_data(self, backup_file: str):
        """Restore data from backup file"""
        if not self.connected and not self.connect():
            return False
            
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            if 'data' not in backup_data:
                logger.error("❌ Invalid backup file format")
                return False
            
            logger.info(f"📥 Restoring data from {backup_file}")
            
            # Restore each collection
            for collection_name, documents in backup_data['data'].items():
                if documents:
                    collection = self.db[collection_name]
                    
                    # Clear existing data (optional - remove if you want to merge)
                    # collection.delete_many({})
                    
                    # Insert documents
                    if isinstance(documents, list) and documents:
                        # Remove _id field to avoid conflicts
                        for doc in documents:
                            if '_id' in doc:
                                del doc['_id']
                        
                        result = collection.insert_many(documents)
                        logger.info(f"✅ Restored {len(result.inserted_ids)} documents to {collection_name}")
                    
            logger.info("✅ Data restoration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    def validate_data_integrity(self):
        """Validate data integrity and check for common issues"""
        if not self.connected and not self.connect():
            return False
            
        try:
            print("🔍 Validating Data Integrity...")
            
            issues_found = []
            
            # Check users collection
            if 'users' in self.db.list_collection_names():
                users = self.db.users
                total_users = users.count_documents({})
                
                # Check for users without user_id
                invalid_users = users.count_documents({"user_id": {"$exists": False}})
                if invalid_users > 0:
                    issues_found.append(f"Found {invalid_users} users without user_id")
                
                # Check for duplicate user_ids
                pipeline = [
                    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                    {"$match": {"count": {"$gt": 1}}}
                ]
                duplicates = list(users.aggregate(pipeline))
                if duplicates:
                    issues_found.append(f"Found {len(duplicates)} duplicate user_ids")
                
                print(f"👥 Users Collection: {total_users} total users")
                
            # Check guilds collection
            if 'guilds' in self.db.list_collection_names():
                guilds = self.db.guilds
                total_guilds = guilds.count_documents({})
                print(f"🏰 Guilds Collection: {total_guilds} total guilds")
            
            # Report issues
            if issues_found:
                print("⚠️ Issues Found:")
                for issue in issues_found:
                    print(f"   - {issue}")
            else:
                print("✅ No data integrity issues found")
                
            return len(issues_found) == 0
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("🔌 MongoDB connection closed")

def main():
    """Main CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 MongoDB Sync Tool for Coal Python Bot")
        print("\nUsage:")
        print("  python mongodb_sync_tool.py test       - Test MongoDB connection")
        print("  python mongodb_sync_tool.py backup     - Backup all data")
        print("  python mongodb_sync_tool.py restore <file> - Restore from backup")
        print("  python mongodb_sync_tool.py validate   - Validate data integrity")
        print("\nEnvironment variables required:")
        print("  MONGODB_URI - Your MongoDB connection string")
        return
    
    command = sys.argv[1].lower()
    
    try:
        tool = MongoSyncTool()
        
        if command == 'test':
            tool.test_connection()
            
        elif command == 'backup':
            tool.backup_data()
            
        elif command == 'restore':
            if len(sys.argv) < 3:
                print("❌ Please provide backup file path")
                return
            backup_file = sys.argv[2]
            if not os.path.exists(backup_file):
                print(f"❌ Backup file not found: {backup_file}")
                return
            tool.restore_data(backup_file)
            
        elif command == 'validate':
            tool.validate_data_integrity()
            
        else:
            print(f"❌ Unknown command: {command}")
            
    except Exception as e:
        logger.error(f"❌ Tool failed: {e}")
        
    finally:
        if 'tool' in locals():
            tool.close()

if __name__ == "__main__":
    main()