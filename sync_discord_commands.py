#!/usr/bin/env python3
"""
Discord Command Sync Script
This script syncs all bot commands to Discord and removes any non-existent commands.
"""

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    print("❌ NO DISCORD_TOKEN FOUND")
    exit(1)

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} connected to Discord!')
    print(f'📊 Serving {len(bot.guilds)} guilds')
    
    try:
        # Load all cogs first
        cogs_to_load = [
            'cogs.economy',
            'cogs.enhanced_economy', 
            'cogs.moderation',
            'cogs.enhanced_moderation',
            'cogs.enhanced_minigames',
            'cogs.community',
            'cogs.events',
            'cogs.cookies',
            'cogs.dashboard',
            'cogs.cool_commands',
            'cogs.backup_system',
            'cogs.pet_system',
            'cogs.stock_market',
            'cogs.job_tracking',
            'cogs.leveling',
            'cogs.settings',
            'cogs.simple_tickets',
            'cogs.security_performance'
        ]
        
        loaded_count = 0
        for cog in cogs_to_load:
            try:
                await bot.load_extension(cog)
                print(f"✅ Loaded {cog}")
                loaded_count += 1
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
        
        print(f"📦 Loaded {loaded_count} cogs")
        
        # Clear all existing global commands first
        print("🧹 Clearing existing global commands...")
        bot.tree.clear_commands(guild=None)
        
        # Sync commands globally
        print("🔄 Syncing commands globally...")
        synced = await bot.tree.sync()
        print(f"✅ Successfully synced {len(synced)} global commands")
        
        # List all synced commands
        print("\n📋 Synced Commands:")
        for i, command in enumerate(synced, 1):
            print(f"  {i}. /{command.name} - {command.description[:50]}...")
        
        # Also sync to specific guilds if needed
        print("\n🏰 Syncing to specific guilds...")
        for guild in bot.guilds:
            try:
                guild_synced = await bot.tree.sync(guild=guild)
                print(f"✅ Synced {len(guild_synced)} commands to {guild.name}")
            except Exception as e:
                print(f"❌ Failed to sync to {guild.name}: {e}")
        
        print("\n🎉 Command sync completed successfully!")
        print("🔄 All non-existent commands have been removed.")
        print("✨ All current commands are now available in Discord.")
        
    except Exception as e:
        print(f"❌ Error during command sync: {e}")
    
    # Close the bot after syncing
    await bot.close()

if __name__ == "__main__":
    print("🚀 Starting Discord Command Sync...")
    bot.run(DISCORD_TOKEN)