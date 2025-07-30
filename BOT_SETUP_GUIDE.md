# Discord Bot Setup and Fix Guide

## Issues Identified

Based on the logs and testing, the following issues were found:

1. **❌ Invalid Discord Token**: The bot is using placeholder token
2. **❌ MongoDB Connection Failed**: Using placeholder MongoDB URI
3. **❌ Gemini AI API Key Invalid**: Using placeholder API key
4. **✅ Bot Structure Working**: All cogs load correctly, database falls back to memory

## Required Environment Variables

You need to set up the following environment variables in your `.env` file:

### 1. Discord Bot Token
```bash
DISCORD_TOKEN=your_actual_discord_bot_token_here
```
**How to get this:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select existing one
3. Go to "Bot" section
4. Click "Reset Token" to get your bot token
5. Copy the token and paste it in your .env file

### 2. Discord Client ID
```bash
DISCORD_CLIENT_ID=your_discord_client_id_here
```
**How to get this:**
1. In the same Discord Developer Portal
2. Go to "General Information" section
3. Copy the "Application ID"

### 3. MongoDB Connection String
```bash
MONGODB_URI=mongodb+srv://username:password@your-cluster.mongodb.net/coalbot?retryWrites=true&w=majority
```
**How to get this:**
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a free cluster
3. Click "Connect" on your cluster
4. Choose "Connect your application"
5. Copy the connection string
6. Replace `<username>`, `<password>`, and `<dbname>` with your actual values

### 4. Gemini AI API Key
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```
**How to get this:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and paste it in your .env file

## Complete .env File Example

```bash
# Discord Bot Configuration
DISCORD_TOKEN=your_actual_discord_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id_here

# MongoDB Database Configuration
MONGODB_URI=mongodb+srv://yourusername:yourpassword@cluster0.abc123.mongodb.net/coalbot?retryWrites=true&w=majority

# Gemini AI Configuration
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Bot Configuration
BOT_PREFIX=!
DEBUG=False
ENVIRONMENT=production

# Optional: Redis Configuration (for caching)
REDIS_URL=redis://localhost:6379

# Optional: Additional API Keys
WEATHER_API_KEY=your_weather_api_key_here
NEWS_API_KEY=your_news_api_key_here
```

## Bot Features Working

✅ **Database System**: Falls back to memory storage when MongoDB unavailable
✅ **Cog Loading**: All 17 cogs load successfully
✅ **Flask Server**: Health check endpoint running on port 10000
✅ **Error Handling**: Proper error handling and logging
✅ **Command Structure**: Slash commands and prefix commands ready

## Bot Features Available

- **Economy System**: Coins, bank, daily bonuses, work system
- **Leveling System**: XP, levels, leaderboards
- **Moderation**: Warnings, mutes, bans, auto-moderation
- **Pet System**: Virtual pets with feeding and training
- **Stock Market**: Virtual stock trading
- **Job Tracking**: Work performance and career progression
- **Community Features**: Reputation, marriage, social interactions
- **AI Integration**: Gemini AI for chat and assistance
- **Dashboard**: Web-based bot management interface
- **Backup System**: Data backup and recovery
- **Security**: Performance monitoring and security features

## How to Start the Bot

1. **Set up environment variables** (see above)
2. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```
3. **Run the bot**:
   ```bash
   python main.py
   ```

## Health Check

Once running, you can check the bot status at:
- `http://localhost:10000/` - Basic status
- `http://localhost:10000/health` - Detailed health check

## Command Sync

After the bot is running, you can sync slash commands:
- Use `!sync` command (requires admin permissions)
- Commands will be available within 1-2 minutes

## Troubleshooting

### Bot won't start
- Check that all environment variables are set correctly
- Ensure Discord token is valid
- Verify MongoDB connection string format

### Commands not working
- Wait 1-2 minutes for Discord to process slash commands
- Use `!sync` command to force sync
- Check bot permissions in Discord server

### Database issues
- Bot will automatically fall back to memory storage
- Check MongoDB connection string
- Ensure MongoDB cluster is running

## Next Steps

1. **Get real API keys and tokens** (see above)
2. **Update .env file** with actual values
3. **Test bot startup** with `python main.py`
4. **Invite bot to Discord server** using OAuth2 URL
5. **Test commands** in Discord
6. **Deploy to production** (Render, Heroku, etc.)

## Support

If you encounter issues:
1. Check the logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure bot has proper permissions in Discord
4. Test with a simple command like `!info` or `!help`