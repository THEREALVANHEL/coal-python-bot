#!/usr/bin/env python3

import asyncio
import os
import sys
import discord
from discord.ext import commands

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Get token from environment
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ Error: DISCORD_TOKEN not found in environment variables!")
    exit(1)

# Bot setup with all intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")
    print("=" * 60)
    print("🔄 STARTING COMPREHENSIVE COMMAND SYNC...")
    print("=" * 60)
    
    try:
        # Load all cogs first
        cog_files = [
            'cogs.leveling',
            'cogs.moderation', 
            'cogs.community',
            'cogs.economy',
            'cogs.settings',
            'cogs.tickets',
            'cogs.events',
            'cogs.cookies',
            'cogs.event_commands'
        ]
        
        print("📦 Loading cogs...")
        for cog in cog_files:
            try:
                await bot.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        print("\n🔄 Syncing commands...")
        
        # Clear all commands first
        print("🧹 Clearing existing commands...")
        bot.tree.clear_commands(guild=None)
        
        # Get total command count
        total_commands = len(bot.tree.get_commands())
        print(f"📊 Found {total_commands} commands to sync")
        
        # Sync globally 
        print("🌍 Syncing commands globally...")
        synced_global = await bot.tree.sync()
        print(f"✅ Synced {len(synced_global)} global commands")
        
        # List all synced commands
        print("\n📋 Synced Commands:")
        print("-" * 40)
        for i, cmd in enumerate(synced_global, 1):
            print(f"{i:2d}. /{cmd.name} - {cmd.description[:50]}...")
        
        print("\n" + "=" * 60)
        print("✅ COMMAND SYNC COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("🎯 All commands should now be visible in Discord")
        print("💡 If commands don't appear immediately, wait 1-2 minutes")
        print("🔄 You can also try restarting Discord client")
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.close()

if __name__ == "__main__":
    print("� Starting command sync bot...")
    try:
        asyncio.run(bot.start(TOKEN))
    except KeyboardInterrupt:
        print("\n🛑 Sync interrupted by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
