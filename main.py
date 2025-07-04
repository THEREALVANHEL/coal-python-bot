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
bot = commands.Bot(command_prefix="!", intents=intents)

# Flag to prevent multiple syncs
synced = False

# --- Ready Event ---
@bot.event
async def on_ready():
    global synced
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print("🔄 Loading cogs...")

    cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f'cogs.{cog_name}')
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

    # Only sync once when bot starts
    if not synced:
        print("🔄 Syncing slash commands...")
        try:
            # Add a delay to avoid rate limiting
            await asyncio.sleep(2)
            
            # Try guild sync first
            guild = discord.Object(id=GUILD_ID)
            synced_commands = await bot.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced_commands)} command(s) to guild {GUILD_ID}")
            
            # Wait a bit more before global sync
            await asyncio.sleep(3)
            
            # Also sync globally for DMs and other guilds
            global_synced = await bot.tree.sync()
            print(f"✅ Synced {len(global_synced)} command(s) globally")
            
            synced = True
            
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                print(f"❌ Rate limited during sync. Waiting 60 seconds...")
                await asyncio.sleep(60)
                try:
                    synced_commands = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
                    print(f"✅ Synced {len(synced_commands)} command(s) after retry")
                    synced = True
                except Exception as retry_e:
                    print(f"❌ Failed to sync after retry: {retry_e}")
            else:
                print(f"❌ HTTP error during sync: {e}")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

# Add error handler for rate limiting
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Error in {event}: {args}, {kwargs}")

# --- Run the Bot ---
async def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing in .env")
        return
    elif not MONGODB_URI:
        print("❌ MONGODB_URI is missing in .env")
        return
    
    print("🌐 Starting keep-alive server...")
    keep_alive()
    print("🤖 Starting bot...")
    
    # Add retry logic for initial connection
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await bot.start(DISCORD_TOKEN)
            break
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                wait_time = 60 * (attempt + 1)  # Exponential backoff
                print(f"❌ Rate limited on startup attempt {attempt + 1}. Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                print(f"❌ HTTP error on startup: {e}")
                if attempt == max_retries - 1:
                    raise
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            if attempt == max_retries - 1:
                raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
