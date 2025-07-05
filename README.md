# Discord Bot - Setup Guide

This is a Discord bot built with Python using discord.py, featuring leveling, economy, moderation, and community features.

## 🔧 Issues Fixed

✅ **Fixed syntax errors in `database.py`:**
- Fixed missing indentation in `update_last_work()` function
- Fixed missing newline before `reset_guild_settings()` function

✅ **Fixed syntax error in `main.py`:**
- Removed leftover text at end of file that was causing syntax errors

✅ **Set up virtual environment and dependencies:**
- Created Python virtual environment
- Installed all required packages from `requirements.txt`

## 🚀 Quick Setup

### 1. Clone and Setup Environment

```bash
# Install virtual environment support
sudo apt install python3.13-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your credentials
nano .env
```

Required environment variables:
- `DISCORD_TOKEN`: Your Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)
- `MONGODB_URI`: Your MongoDB connection string

Optional:
- `GEMINI_API_KEY`: For AI features (Google Gemini API)

### 3. Run Environment Check

```bash
# Check if all environment variables are set correctly
python3 check_env.py
```

### 4. Start the Bot

```bash
# Run the bot
python3 main.py
```

## 📋 Features

- **Leveling System**: XP and level progression
- **Economy**: Coins and cookies currency system
- **Moderation**: Warning system and moderation tools
- **Community**: Interactive commands and features
- **Settings**: Configurable guild settings
- **Events**: Event management system

## 🗃️ Database

The bot uses MongoDB for data storage. Make sure to:
1. Create a MongoDB Atlas account or set up a local MongoDB instance
2. Create a database named `discord_bot`
3. Add your connection string to the `.env` file

## 🔍 Troubleshooting

If you encounter issues:

1. **Check environment variables**: Run `python3 check_env.py`
2. **Verify virtual environment**: Make sure you've activated it with `source venv/bin/activate`
3. **Check dependencies**: Run `pip install -r requirements.txt` again
4. **Check logs**: The bot prints detailed error messages to help debug issues

## 📁 Project Structure

```
├── main.py              # Bot entry point
├── database.py          # Database operations
├── check_env.py         # Environment validation
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── cogs/               # Bot command modules
│   ├── leveling.py
│   ├── economy.py
│   ├── moderation.py
│   └── ...
└── assets/             # Static files
```

## ⚠️ Security Notes

- Never commit your `.env` file to version control
- Keep your Discord token and MongoDB URI secure
- Use environment variables for all sensitive data