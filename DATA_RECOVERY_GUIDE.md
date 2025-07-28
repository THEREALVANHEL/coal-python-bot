# 🔧 Data Recovery Guide - MongoDB Connection

## ❌ **Problem**: `module 'database' has no attribute 'users_collection'`

This error occurs when the bot fails to connect to MongoDB and falls back to memory storage, but other parts of the code still try to access MongoDB-specific attributes.

## ✅ **Solution**: Reconnect to MongoDB and Recover Data

### �� **Step 1: Get Your MongoDB Connection String**
1. **Go to MongoDB Atlas**: https://cloud.mongodb.com/
2. **Login** to your account
3. **Click "Connect"** on your cluster
4. **Choose "Connect your application"**
5. **Copy the connection string**

### 📋 **Step 2: Update Environment Variables on Render**
1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Select your bot service**
3. **Go to "Environment" tab**
4. **Add/Update**: `MONGODB_URI` with your connection string

### 📋 **Step 3: Use Admin Commands**
- `!db_status` - Check database status
- `!reconnect_db <uri>` - Reconnect to MongoDB
- `!migrate_data` - Migrate memory data to MongoDB

## 🔍 **What Was Fixed**
- ✅ Fixed `get_default_database()` error
- ✅ Added proper error handling for missing `users_collection`
- ✅ Added MongoDB reconnection functions
- ✅ Added data migration capabilities

The bot is now ready to connect to MongoDB when you provide the correct URI!
