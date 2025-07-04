#!/usr/bin/env python3
"""
Environment Variables Checker
Run this to verify your environment setup before starting the bot
"""

import os
from dotenv import load_dotenv

def check_environment():
    """Check if all required environment variables are set"""
    load_dotenv()
    
    required_vars = {
        'DISCORD_TOKEN': 'Discord bot token',
        'MONGODB_URI': 'MongoDB connection string',
    }
    
    optional_vars = {
        'GEMINI_API_KEY': 'Google Gemini AI API key (for /askblecknephew command)',
    }
    
    print("🔍 Checking Environment Variables...\n")
    
    # Check required variables
    missing_required = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 8)}... ({description})")
        else:
            print(f"❌ {var}: Missing! ({description})")
            missing_required.append(var)
    
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 8)}... ({description})")
        else:
            print(f"⚠️  {var}: Not set ({description})")
    
    print(f"\n{'='*50}")
    
    if missing_required:
        print(f"❌ Missing {len(missing_required)} required environment variable(s):")
        for var in missing_required:
            print(f"   - {var}")
        print("\n💡 Please add these to your .env file or deployment environment")
        return False
    else:
        print("✅ All required environment variables are set!")
        print("🚀 Your bot should be ready to run!")
        return True

if __name__ == "__main__":
    success = check_environment()
    exit(0 if success else 1)
