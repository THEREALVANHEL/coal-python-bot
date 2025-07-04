import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from discord import app_commands
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# --- Keep-alive server (useful for hosting) ---
app = Flask('')

@app.route('/')
def home():
    return "✅ BLECKOPS Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

# --- Load Environment Variables ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

GUILD_ID = 1370009417726169250  # Update if your server ID changes

class BleckOpsBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def setup_hook(self):
        """This is called when the bot is starting up"""
        print("🔄 Loading cogs...")
        
        cogs_to_load = [
            'cogs.moderation',
            'cogs.cookies', 
            'cogs.economy',
            'cogs.leveling',
            'cogs.community',
            'cogs.event_commands',
            'cogs.events',
            'cogs.settings',
            'cogs.fun_commands'  # New cog
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} ({self.user.id})")
        
        # Only sync once when bot starts
        if not self.synced:
            print("🔄 Syncing slash commands...")
            try:
                # Add a delay to avoid rate limiting
                await asyncio.sleep(3)
                
                # Try guild sync first (faster and less likely to be rate limited)
                guild = discord.Object(id=GUILD_ID)
                synced_commands = await self.tree.sync(guild=guild)
                print(f"✅ Synced {len(synced_commands)} command(s) to guild {GUILD_ID}")
                
                self.synced = True
                print("🎉 BLECKOPS Bot is ready and commands are synced!")
                
                # Print all available commands
                print("\n📋 Available Commands:")
                print("="*50)
                for command in self.tree.get_commands():
                    print(f"/{command.name} - {command.description}")
                
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    print(f"❌ Rate limited during sync. This is usually temporary.")
                    print("💡 Commands will sync automatically when rate limit expires.")
                else:
                    print(f"❌ HTTP error during sync: {e}")
            except Exception as e:
                print(f"❌ Failed to sync commands: {e}")

bot = BleckOpsBot()

# --- Run the Bot ---
async def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing in environment variables")
        print("💡 Make sure to set DISCORD_TOKEN in your hosting dashboard")
        return
    elif not MONGODB_URI:
        print("❌ MONGODB_URI is missing in environment variables")
        print("💡 Make sure to set MONGODB_URI in your hosting dashboard")
        return
    
    print("🌐 Starting keep-alive server...")
    keep_alive()
    print("🤖 Starting BLECKOPS Bot...")
    
    # Add retry logic for initial connection with exponential backoff
    max_retries = 5
    for attempt in range(max_retries):
        try:
            async with bot:
                await bot.start(DISCORD_TOKEN)
            break
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                wait_time = min(300, 30 * (2 ** attempt))  # Exponential backoff, max 5 minutes
                print(f"❌ Rate limited on startup attempt {attempt + 1}/{max_retries}")
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ HTTP error on startup: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(10)
        except Exception as e:
            print(f"❌ Error starting bot (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
