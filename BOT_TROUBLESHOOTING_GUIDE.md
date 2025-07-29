# Discord Bot Troubleshooting Guide
## MongoDB Connection & Data Issues

### 🔍 Issues Diagnosed

1. **Missing Environment Variables**
   - `MONGODB_URI` was not set
   - `DISCORD_TOKEN` was not set
   - Bot was falling back to memory storage

2. **Dependencies Issues**
   - MongoDB drivers were installed but needed system-level configuration
   - Some Python packages needed manual installation with `--break-system-packages`

3. **Database Configuration**
   - Bot was properly configured to fall back to memory storage when MongoDB unavailable
   - Data operations were working but not persisting to actual database

### ✅ Solutions Implemented

#### 1. Environment Configuration
Created `.env` file with required variables:
```bash
# Copy the template and fill in your values
cp .env.example .env
# Edit .env with your actual credentials
```

Required environment variables:
- `DISCORD_TOKEN` - Your Discord bot token
- `DISCORD_CLIENT_ID` - Your Discord application ID  
- `MONGODB_URI` - Your MongoDB connection string
- `GEMINI_API_KEY` - Your Google Gemini AI API key

#### 2. Dependencies Fixed
All required packages now installed:
```bash
pip3 install --break-system-packages -r requirements.txt
```

Key packages:
- `discord.py>=2.3.0` - Discord bot framework
- `pymongo>=4.6.0` - MongoDB sync driver
- `motor>=3.3.0` - MongoDB async driver
- `python-dotenv>=1.0.0` - Environment variable loader

#### 3. MongoDB Data Synchronization Tool
Created `mongodb_sync_tool.py` for data management:

**Test MongoDB Connection:**
```bash
python3 mongodb_sync_tool.py test
```

**Backup All Data:**
```bash
python3 mongodb_sync_tool.py backup
```

**Restore from Backup:**
```bash
python3 mongodb_sync_tool.py restore backup_file.json
```

**Validate Data Integrity:**
```bash
python3 mongodb_sync_tool.py validate
```

### 🚀 Quick Start Guide

1. **Set Up Environment:**
   ```bash
   # Copy and configure environment
   cp .env.example .env
   # Edit .env with your credentials
   nano .env
   ```

2. **Install Dependencies:**
   ```bash
   pip3 install --break-system-packages -r requirements.txt
   ```

3. **Test Database Connection:**
   ```bash
   python3 mongodb_sync_tool.py test
   ```

4. **Start the Bot:**
   ```bash
   python3 main.py
   ```

### 🔧 Environment Variables Setup

#### Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create/select your application
3. Go to "Bot" section
4. Copy the token and add to `.env`:
   ```
   DISCORD_TOKEN=your_bot_token_here
   ```

#### MongoDB URI
1. Get your MongoDB connection string from:
   - MongoDB Atlas (cloud)
   - Local MongoDB installation
   - Docker MongoDB instance

2. Format examples:
   ```bash
   # MongoDB Atlas
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/coalbot?retryWrites=true&w=majority
   
   # Local MongoDB
   MONGODB_URI=mongodb://localhost:27017/coalbot
   
   # Docker MongoDB
   MONGODB_URI=mongodb://username:password@localhost:27017/coalbot
   ```

#### Gemini AI API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add to `.env`:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

### 🛟 Data Recovery Procedures

#### If You Have MongoDB Access
1. **Backup Current Data:**
   ```bash
   python3 mongodb_sync_tool.py backup
   ```

2. **Validate Data:**
   ```bash
   python3 mongodb_sync_tool.py validate
   ```

3. **Check Database Status:**
   ```bash
   python3 mongodb_sync_tool.py test
   ```

#### If MongoDB is Unavailable
The bot automatically falls back to memory storage:
- User data is temporarily stored in memory
- Data will be lost when bot restarts
- Set up MongoDB connection to persist data

#### Emergency Data Recovery
If you have backup files:
```bash
# List available backups
ls mongodb_backup_*.json

# Restore from most recent backup
python3 mongodb_sync_tool.py restore mongodb_backup_YYYYMMDD_HHMMSS.json
```

### 🔍 Common Issues & Solutions

#### Issue: "MongoDB drivers not available"
**Solution:**
```bash
pip3 install --break-system-packages pymongo motor
```

#### Issue: "MONGODB_URI environment variable is required"
**Solution:**
1. Create `.env` file with MongoDB URI
2. Or set environment variable:
   ```bash
   export MONGODB_URI="your_connection_string"
   ```

#### Issue: "Discord token not found"
**Solution:**
1. Add Discord token to `.env` file
2. Or set environment variable:
   ```bash
   export DISCORD_TOKEN="your_bot_token"
   ```

#### Issue: "Connection timeout" to MongoDB
**Solutions:**
1. Check internet connection
2. Verify MongoDB URI format
3. Check MongoDB server status
4. Verify firewall/network settings
5. Check credentials in URI

#### Issue: Bot works but data doesn't persist
**Cause:** Bot is using memory storage fallback
**Solution:** Fix MongoDB connection

### 📊 Database Health Monitoring

#### Regular Health Checks
```bash
# Test connection daily
python3 mongodb_sync_tool.py test

# Backup data weekly  
python3 mongodb_sync_tool.py backup

# Validate integrity monthly
python3 mongodb_sync_tool.py validate
```

#### Monitor Bot Logs
Check bot startup logs for:
- ✅ MongoDB connection established
- ⚠️ Using in-memory database storage
- ❌ MongoDB connection failed

### 🚨 Emergency Contacts & Resources

- **MongoDB Atlas Support:** [support.mongodb.com](https://support.mongodb.com)
- **Discord Developer Support:** [discord.com/developers](https://discord.com/developers)
- **Bot Repository:** Your GitHub repository

### 📝 Maintenance Schedule

**Daily:**
- Monitor bot status
- Check error logs

**Weekly:**
- Backup MongoDB data
- Review bot performance

**Monthly:**
- Validate data integrity
- Update dependencies
- Review security settings

### 🔄 Deployment Checklist

Before deploying:
- [ ] All environment variables set
- [ ] MongoDB connection tested
- [ ] Discord bot token valid
- [ ] Dependencies installed
- [ ] Data backed up
- [ ] Bot tested in development

After deploying:
- [ ] Bot connects successfully
- [ ] Commands working
- [ ] Data persisting to MongoDB
- [ ] No error logs
- [ ] User data intact

---

## 🆘 Need Help?

If you're still experiencing issues:
1. Check the bot logs for specific error messages
2. Test MongoDB connection with the sync tool
3. Verify all environment variables are set correctly
4. Ensure all dependencies are installed
5. Check network connectivity to MongoDB

The bot is designed to be resilient - it will continue operating with memory storage even if MongoDB is unavailable, but data won't persist between restarts.