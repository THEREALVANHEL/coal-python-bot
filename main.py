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

if not DISCORD_TOKEN:
    print("❌ NO TOKEN FOUND")
    exit(1)

# Discord Bot Setup - discord.py style
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():
    print(f"✅ BOT ONLINE: {bot.user.name}#{bot.user.discriminator}")
    print(f"📊 Bot ID: {bot.user.id}")
    print(f"🔗 Invite: https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands")
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"⚡ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# Load cogs
async def load_cogs():
    try:
        cogs = [
            'cogs.leveling',
            'cogs.economy', 
            'cogs.moderation',
            'cogs.community',
            'cogs.settings',
            'cogs.cookies',
            'cogs.events',
            'cogs.event_commands'
        ]
        for cog in cogs:
            try:
                await bot.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
    except Exception as e:
        print(f"❌ Error loading cogs: {e}")

async def main():
    print("=== BOT STARTING ===")
    print("✅ OS imported")
    print("✅ Discord imported") 
    print("✅ Flask imported")
    print("🌐 Starting Flask...")
    
    # Start keep-alive server
    keep_alive()
    
    print(f"🔑 Token found: {bool(DISCORD_TOKEN)}")
    print(f"🔑 Token starts with: {DISCORD_TOKEN[:15]}...")
    print("🤖 Creating Discord client...")
    
    # Load cogs
    await load_cogs()
    
    print("🚀 Starting bot connection...")
    
    # Start bot with better error handling
    try:
        await bot.start(DISCORD_TOKEN)
    except discord.HTTPException as e:
        if e.status == 429:
            print("⏳ Rate limited. Waiting 5 minutes before retry...")
            await asyncio.sleep(300)  # Wait 5 minutes
            await bot.start(DISCORD_TOKEN)
        else:
            print(f"❌ BOT ERROR: {e}")
            raise
    except Exception as e:
        print(f"❌ BOT ERROR: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")