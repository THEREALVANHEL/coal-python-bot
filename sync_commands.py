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

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1370009417726169250

# Setup bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class SyncBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Load all cogs before syncing"""
        print("🔄 Loading cogs for sync...")
        
        cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                cog_name = filename[:-3]
                try:
                    await self.load_extension(f'cogs.{cog_name}')
                    print(f"✅ Loaded cog: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load {filename}: {e}")

    async def on_ready(self):
        print(f"✅ Bot ready: {self.user}")
        
        try:
            # Force sync to specific guild for instant updates
            guild = discord.Object(id=GUILD_ID)
            synced = await self.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} slash commands to guild {GUILD_ID}")
            
            # Also try global sync for backup
            try:
                global_synced = await self.tree.sync()
                print(f"✅ Synced {len(global_synced)} commands globally")
            except Exception as e:
                print(f"⚠️ Global sync failed (this is usually fine): {e}")
            
            print("🎉 All commands should now be visible in Discord!")
            print("\n📋 Available Commands:")
            print("="*50)
            
            # List all commands
            for command in self.tree.get_commands():
                print(f"/{command.name} - {command.description}")
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
        
        finally:
            await self.close()

async def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment!")
        return
    
    bot = SyncBot()
    try:
        await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("� Starting command sync...")
    asyncio.run(main())