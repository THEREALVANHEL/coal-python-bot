#!/usr/bin/env python3
"""
Emergency Command Sync Script
Run this script to force sync all Discord commands when regular sync fails.
"""

import discord
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord bot setup
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ DISCORD_TOKEN not found in environment variables!")
    sys.exit(1)

class EmergencyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        print("🔄 Emergency sync starting...")
        
        # Load all cogs to register commands
        cog_files = [
            'cogs.economy',
            'cogs.community', 
            'cogs.cookies',
            'cogs.leveling',
            'cogs.moderation',
            'cogs.events',
            'cogs.event_commands',
            'cogs.settings'
        ]
        
        print("📦 Loading cogs...")
        for cog_file in cog_files:
            try:
                await self.load_extension(cog_file)
                print(f"✅ Loaded {cog_file}")
            except Exception as e:
                print(f"⚠️ Failed to load {cog_file}: {e}")
        
        # Clear existing commands
        print("🗑️ Clearing old commands...")
        self.tree.clear_commands(guild=None)
        
        # Short delay
        await asyncio.sleep(2)
        
        # Sync globally
        print("🌍 Syncing commands globally...")
        try:
            synced = await self.tree.sync()
            print(f"✅ Successfully synced {len(synced)} commands globally!")
            
            # List all synced commands
            command_names = [cmd.name for cmd in synced]
            print(f"📋 Synced commands: {', '.join(command_names)}")
            
        except Exception as e:
            print(f"❌ Global sync failed: {e}")
            return

        print("✅ Emergency sync completed successfully!")
        await self.close()

    async def on_ready(self):
        print(f"🤖 Bot connected as {self.user}")

async def main():
    print("🚨 EMERGENCY COMMAND SYNC")
    print("=" * 50)
    
    client = EmergencyBot()
    
    try:
        await client.start(TOKEN)
    except Exception as e:
        print(f"❌ Emergency sync failed: {e}")
    finally:
        if not client.is_closed():
            await client.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Emergency sync cancelled by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")