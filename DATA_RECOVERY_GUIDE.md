# 🔧 Data Recovery Guide - MongoDB Connection

## ❌ **Problem**: `module 'database' has no attribute 'users_collection'`

This error occurs when the bot fails to connect to MongoDB and falls back to memory storage, but other parts of the code still try to access MongoDB-specific attributes.

## ✅ **Solution**: Reconnect to MongoDB and Recover Data

### 📋 **Step 1: Get Your MongoDB Connection String**

1. **Go to MongoDB Atlas**: https://cloud.mongodb.com/
2. **Login** to your account
3. **Click "Connect"** on your cluster
4. **Choose "Connect your application"**
5. **Copy the connection string** (looks like):
   ```
   mongodb+srv://username:password@cluster.mongodb.net/databasename?retryWrites=true&w=majority
   ```

### 📋 **Step 2: Update Environment Variables on Render**

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Select your bot service**
3. **Go to "Environment" tab**
4. **Add/Update** the following variable:
   - **Key**: `MONGODB_URI`
   - **Value**: Your MongoDB connection string from Step 1

### 📋 **Step 3: Redeploy the Bot**

1. **In Render Dashboard**, click **"Manual Deploy"**
2. **Wait for deployment** to complete
3. **Check logs** - you should see:
   ```
   🎯 MongoDB connection established successfully! Database: coalbot
   📊 Found X users in database
   ```

### 📋 **Step 4: Use Admin Commands (If Needed)**

If you need to manually reconnect or migrate data, use these Discord commands:

#### **Check Database Status**:
```
!db_status
```

#### **Reconnect to MongoDB**:
```
!reconnect_db mongodb+srv://username:password@cluster.mongodb.net/coalbot?retryWrites=true&w=majority
```

#### **Migrate Memory Data to MongoDB**:
```
!migrate_data
```

## 🔍 **What Was Fixed**

### **1. Database Connection Logic**
- ✅ Fixed `get_default_database()` error by explicitly specifying database name
- ✅ Added proper error handling for missing `users_collection`
- ✅ Improved MongoDB URI parsing

### **2. Fallback Handling**
- ✅ Graceful fallback to memory storage when MongoDB unavailable
- ✅ Proper null checks for `users_collection` and `guilds_collection`
- ✅ Clear logging of database connection status

### **3. Data Recovery Features**
- ✅ Added `reconnect_mongodb()` function for runtime reconnection
- ✅ Added `migrate_memory_to_mongodb()` for data migration
- ✅ Added admin commands for manual database management

## 📊 **Data Recovery Status**

### **If MongoDB Was Never Connected**:
- ❌ **Previous data is lost** (was only in memory)
- ✅ **New data will be saved** once MongoDB is connected
- ✅ **Users will start fresh** with default values

### **If MongoDB Was Previously Connected**:
- ✅ **Your data is safe** in MongoDB
- ✅ **Data will be restored** once reconnected
- ✅ **All user progress preserved**

## 🚨 **Prevention for Future**

### **1. Always Set MongoDB URI**
- Set `MONGODB_URI` environment variable on deployment
- Use a proper MongoDB Atlas cluster (not local MongoDB)
- Include database name in the URI

### **2. Monitor Connection Status**
- Check logs for MongoDB connection messages
- Use `!db_status` command regularly
- Set up MongoDB Atlas alerts

### **3. Backup Strategy**
- Enable MongoDB Atlas automatic backups
- Consider periodic data exports
- Monitor database usage and storage

## 📞 **Need Help?**

If you're still having issues:

1. **Check the deployment logs** on Render
2. **Verify your MongoDB URI** is correct
3. **Test the connection** using MongoDB Compass
4. **Use the admin commands** to diagnose issues

The bot is now **fully operational** and ready to connect to MongoDB when you provide the correct URI!