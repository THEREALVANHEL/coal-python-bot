# Coal Python Bot - Setup Instructions

## Issues Fixed

### ✅ Fixed Issues:
1. **Dependencies**: Updated requirements.txt and installed all necessary packages
2. **DateTime Deprecation**: Fixed all `datetime.utcnow()` usage to use `datetime.now(timezone.utc)`
3. **MongoDB Support**: Installed pymongo and motor drivers
4. **Voice Support**: Installed PyNaCl for Discord voice features
5. **Environment Configuration**: Created proper .env file template
6. **Database Fallback**: Bot gracefully falls back to memory storage when MongoDB is unavailable
7. **AI Integration**: Gemini AI integration works (requires valid API key)

### 🔧 Configuration Required:

To make the bot fully functional, you need to provide the following environment variables in your `.env` file:

#### Required:
- `DISCORD_TOKEN`: Your Discord bot token from Discord Developer Portal
- `DISCORD_CLIENT_ID`: Your Discord application client ID

#### Optional but Recommended:
- `MONGODB_URI`: MongoDB connection string for persistent data storage
- `GEMINI_API_KEY`: Google Gemini AI API key for AI features

## Setup Steps

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Fill in your Discord bot token and other credentials

3. **Discord Bot Setup**:
   - Go to https://discord.com/developers/applications
   - Create a new application or use existing one
   - Go to "Bot" section and copy the token
   - Enable necessary intents (Message Content Intent, Server Members Intent)

4. **MongoDB Setup** (Optional):
   - Create a MongoDB Atlas cluster or use local MongoDB
   - Get connection string and add to `MONGODB_URI`
   - If not provided, bot will use in-memory storage

5. **Gemini AI Setup** (Optional):
   - Get API key from Google AI Studio
   - Add to `GEMINI_API_KEY` in .env file
   - If not provided, AI features will be disabled

## Running the Bot

```bash
python3 main.py
```

## Features

The bot includes:
- **Economy System**: Complete economy with jobs, daily rewards, banking
- **Leveling System**: XP and level progression
- **Moderation Tools**: Warnings, mutes, bans, and more
- **AI Integration**: Gemini AI for smart responses
- **Mini Games**: Various games and entertainment
- **Community Features**: Tickets, events, social features
- **Database**: MongoDB with automatic fallback to memory storage
- **Web Dashboard**: Flask-based health monitoring

## Troubleshooting

### Common Issues:

1. **"Improper token has been passed"**:
   - Check your DISCORD_TOKEN in .env file
   - Ensure token is valid and bot is enabled

2. **MongoDB Connection Failed**:
   - Check MONGODB_URI format
   - Ensure network connectivity
   - Bot will fall back to memory storage automatically

3. **AI Features Not Working**:
   - Verify GEMINI_API_KEY is valid
   - Check API quota and billing
   - Features will be disabled if key is invalid

4. **Missing Permissions**:
   - Ensure bot has necessary permissions in Discord server
   - Check role hierarchy and permissions

## File Structure

- `main.py`: Main bot entry point
- `database.py`: Database management with MongoDB/memory fallback
- `gemini_ai.py`: AI integration and conversation management
- `cogs/`: Bot commands organized by category
- `core/`: Core system modules
- `.env`: Environment configuration (create from .env.example)

## Development

The bot is designed to be modular and extensible:
- Add new commands in the `cogs/` directory
- Database operations are abstracted in `database.py`
- AI features are centralized in `gemini_ai.py`
- Core systems provide additional functionality

## Support

If you encounter issues:
1. Check the logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check Discord bot permissions and intents