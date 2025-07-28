# 🚀 Render Deployment Guide for Coal Python Bot

## ✅ Issues Fixed for Render Deployment

The following deployment issues have been resolved:

1. **✅ Requirements.txt Fixed**: Removed exact version pins that caused `cryptography==41.0.8` error
2. **✅ Flexible Dependencies**: Using `>=` version constraints for better compatibility
3. **✅ Essential Packages Only**: Removed unnecessary packages that caused conflicts
4. **✅ Python 3.11 Compatibility**: All packages work with Render's Python 3.11.6

## 📋 Quick Deployment Steps

### 1. Fork/Clone Repository
- Fork this repository to your GitHub account
- Or clone: `git clone https://github.com/THEREALVANHEL/coal-python-bot.git`

### 2. Create Render Service
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the `coal-python-bot` repository

### 3. Configure Render Settings
- **Name**: `coal-python-bot` (or your preferred name)
- **Environment**: `Python`
- **Build Command**: `pip install -r requirements.txt` (auto-detected)
- **Start Command**: `python main.py` (auto-detected)
- **Plan**: Free (or paid for better performance)

### 4. Set Environment Variables
In Render dashboard, add these environment variables:

#### Required:
```
DISCORD_TOKEN = your_actual_discord_bot_token
```

#### Optional (but recommended):
```
MONGODB_URI = your_mongodb_connection_string
GEMINI_API_KEY = your_gemini_api_key
PORT = 10000
```

### 5. Deploy
- Click "Create Web Service"
- Render will automatically build and deploy your bot
- Check the logs for any issues

## 🔧 Getting Required Tokens

### Discord Bot Token:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application or select existing
3. Go to "Bot" section
4. Copy the token
5. **Important**: Enable "Message Content Intent" and "Server Members Intent"

### MongoDB URI (Optional):
1. Create free cluster at [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create database user
3. Get connection string
4. Replace `<password>` with your password

### Gemini AI Key (Optional):
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Copy the key

## 🔍 Troubleshooting Render Deployment

### Common Issues:

#### 1. Build Fails with Package Errors
- **Solution**: The requirements.txt has been fixed to use flexible versions
- If still failing, check Render logs for specific package conflicts

#### 2. Bot Starts but Doesn't Respond
- **Check**: Discord token is correctly set in environment variables
- **Check**: Bot has proper permissions in Discord server
- **Check**: Message Content Intent is enabled

#### 3. Database Errors
- **Solution**: Bot automatically falls back to memory storage if MongoDB fails
- For persistent data, ensure MONGODB_URI is correctly formatted
- Test MongoDB connection string locally first

#### 4. AI Features Not Working
- **Check**: GEMINI_API_KEY is set correctly
- **Check**: API key has proper permissions and quota
- AI features will be disabled if key is invalid (bot continues working)

### Health Check:
- Render will check `/health` endpoint
- Bot includes Flask server for health monitoring
- Access `https://your-app-name.onrender.com/health` to verify status

## 📊 Render Configuration

The bot is configured for Render with:
- **Python Version**: 3.11.6 (specified in render.yaml)
- **Health Check**: `/health` endpoint
- **Auto Deploy**: Enabled (deploys on git push)
- **Port**: 10000 (configurable via PORT env var)

## 🎯 Features Working on Render

- ✅ **Economy System**: Jobs, daily rewards, banking
- ✅ **Leveling System**: XP progression, level ups  
- ✅ **Moderation Tools**: Warnings, mutes, bans
- ✅ **Database**: MongoDB with memory fallback
- ✅ **AI Integration**: Gemini AI (when key provided)
- ✅ **Web Dashboard**: Health monitoring at `/health`
- ✅ **All Discord Commands**: Slash commands and text commands

## 🔄 Auto-Deployment

The bot is configured for automatic deployment:
- Push changes to `main` branch
- Render automatically rebuilds and deploys
- Zero-downtime deployment
- Logs available in Render dashboard

## 📞 Support

If deployment fails:
1. Check Render build logs for specific errors
2. Verify all environment variables are set
3. Test Discord token validity
4. Check bot permissions in Discord server

The bot has been thoroughly tested and should deploy successfully on Render's free tier.