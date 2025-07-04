import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# --- Keep-alive server (useful for Render health checks) ---
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

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

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def setup_hook(self):
        """This is called when the bot is starting up"""
        print("🔄 Loading cogs...")
        
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
        print(f"✅ Logged in as {self.user} ({self.user.id})")
        
        # Only sync once when bot starts
        if not self.synced:
            print("🔄 Syncing slash commands...")
            try:
                # Guild sync (faster and less likely to be rate limited)
                guild = discord.Object(id=GUILD_ID)
                synced_commands = await self.tree.sync(guild=guild)
                print(f"✅ Synced {len(synced_commands)} command(s) to guild {GUILD_ID}")
                
                self.synced = True
                print("🎉 Bot is ready and commands are synced!")
                except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    print(f"⚠️ Rate limited during sync. Commands will sync later.")
                else:
                    print(f"❌ HTTP error during sync: {e}")
            except Exception as e:
                print(f"❌ Failed to sync commands: {e}")

bot = MyBot()

# --- Run the Bot ---
async def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing in environment variables")
        print("💡 Make sure to set DISCORD_TOKEN in your Render dashboard")
        return
    elif not MONGODB_URI:
        print("❌ MONGODB_URI is missing in environment variables")
        print("💡 Make sure to set MONGODB_URI in your Render dashboard")
        return
    
    print("🌐 Starting keep-alive server...")
    keep_alive()
    print("🤖 Starting bot...")
    
    try:
        async with bot:
            await bot.start(DISCORD_TOKEN)
    except discord.HTTPException as e:
        if e.status == 429:
            print("❌ Rate limited. Please wait before restarting.")
        else:
            print(f"❌ HTTP error: {e}")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
