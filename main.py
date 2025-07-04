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

# Keep-alive server
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

GUILD_ID = 1370009417726169250

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def setup_hook(self):
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
        
        if not self.synced:
            print("🔄 Syncing slash commands...")
            try:
                guild = discord.Object(id=GUILD_ID)
                synced_commands = await self.tree.sync(guild=guild)
                print(f"✅ Synced {len(synced_commands)} command(s) to guild {GUILD_ID}")
                self.synced = True
                print("🎉 Bot is ready and commands are synced!")
            except Exception as e:
                print(f"❌ Failed to sync commands: {e}")
                bot = MyBot()

async def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing in environment variables")
        return
    elif not MONGODB_URI:
        print("❌ MONGODB_URI is missing in environment variables")
        return
    
    print("🌐 Starting keep-alive server...")
    keep_alive()
    print("🤖 Starting bot...")
    
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
