#!/usr/bin/env python3
"""
Manual Command Sync Script
Use this if commands still aren't syncing automatically
"""

import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1370009417726169250

async def manual_sync():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables")
        return
    
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Logged in as {bot.user}")
        
        try:
            # Guild sync (faster)
            guild = discord.Object(id=GUILD_ID)
            guild_synced = await bot.tree.sync(guild=guild)
            print(f"✅ Synced {len(guild_synced)} commands to guild {GUILD_ID}")
            
            # Wait a bit then do global sync
            await asyncio.sleep(5)
            global_synced = await bot.tree.sync()
            print(f"✅ Synced {len(global_synced)} commands globally")
            
            print("🎉 Manual sync completed!")
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
        finally:
            await bot.close()
    
    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    print("🔄 Starting manual command sync...")
    asyncio.run(manual_sync())