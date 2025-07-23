#!/usr/bin/env python3
"""
FORCE SYNC ALL DISCORD COMMANDS
This script forces Discord to sync all slash commands immediately
"""

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    print("❌ NO DISCORD_TOKEN FOUND")
    exit(1)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None,
    case_insensitive=True
)

@bot.event
async def on_ready():
    print(f"✅ BOT CONNECTED: {bot.user.name}")
    print(f"🔗 Connected to {len(bot.guilds)} guild(s)")
    
    # Load all cogs
    cogs_to_load = [
        'cogs.events',
        'cogs.moderation', 
        'cogs.economy',
        'cogs.leveling',
        'cogs.cookies',
        'cogs.community',
        'cogs.simple_tickets',
        'cogs.enhanced_moderation',
        'cogs.settings',
        'cogs.job_tracking',
        'cogs.enhanced_minigames',
        'cogs.dashboard',
        'cogs.security_performance',
        'cogs.cool_commands',
        'cogs.pet_system',
        'cogs.stock_market',
        'cogs.backup_system'
    ]
    
    print("🔄 Loading cogs...")
    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")
    
    # Force sync commands
    print("🚀 FORCE SYNCING ALL COMMANDS...")
    try:
        synced = await bot.tree.sync()
        print(f"✅ SUCCESSFULLY SYNCED {len(synced)} COMMANDS!")
        
        # Print all synced commands
        print("\n📋 SYNCED COMMANDS:")
        for cmd in synced:
            print(f"  • /{cmd.name} - {cmd.description}")
        
        print(f"\n🎉 ALL COMMANDS NOW LIVE IN DISCORD!")
        print("🔄 Bot will stay online for 30 seconds to ensure sync...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ SYNC FAILED: {e}")
    
    print("✅ SYNC COMPLETE - CLOSING BOT")
    await bot.close()

if __name__ == "__main__":
    print("🚀 STARTING FORCE SYNC...")
    asyncio.run(bot.start(DISCORD_TOKEN))