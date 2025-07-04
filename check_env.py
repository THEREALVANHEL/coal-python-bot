#!/usr/bin/env python3
"""
Environment Variable Checker
Run this to verify your bot's environment variables are set correctly
"""

import os
from dotenv import load_dotenv

def check_environment():
    print("🔍 Checking Environment Variables...")
    print("=" * 50)
    
    # Load .env file if it exists
    load_dotenv()
    
    # Required variables
    required_vars = {
        'DISCORD_TOKEN': 'Discord Bot Token',
        'MONGODB_URI': 'MongoDB Connection String',
        'GEMINI_API_KEY': 'Google Gemini API Key (optional for AI features)'
    }
    
    all_good = True
    
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            if 'TOKEN' in var_name or 'KEY' in var_name:
                masked = value[:8] + '*' * (len(value) - 12) + value[-4:] if len(value) > 12 else '****'
                print(f"✅ {var_name}: {masked}")
            else:
                print(f"✅ {var_name}: {value[:50]}...")
        else:
            print(f"❌ {var_name}: Missing - {description}")
            all_good = False
    
    print("=" * 50)
    if all_good:
        print("🎉 All required environment variables are set!")
    else:
        print("⚠️  Some environment variables are missing.")
        print("   Make sure to set them in your deployment environment.")
    
    return all_good

if __name__ == "__main__":
    check_environment()