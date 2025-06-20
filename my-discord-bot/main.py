import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# --- Keep-alive server for Render/UptimeRobot ---
app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run_flask():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- Bot Setup ---

# Load environment variables from a .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI')

# Define the bot's intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Event that runs when the bot is ready."""
    cogs_path = './my-discord-bot/cogs'
    if os.path.exists(cogs_path):
        for filename in os.listdir(cogs_path):
            if filename.endswith('.py'):
                bot.load_extension(f'my-discord-bot.cogs.{filename[:-3]}')
    else:
        print(f"Warning: {cogs_path} does not exist. No cogs loaded.")
    print(f"Logged in as {bot.user}")
    print("-------------------")
    print("Loading cogs...")

    # Load all .py files from the 'cogs' directory in the root
    for filename in os.listdir('./cogs'): # <-- THIS IS THE CORRECTED LINE
        if filename.endswith('.py'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")

    print("-------------------")
    
    # Sync slash commands
    try:
        await bot.sync_commands()
        print("✅ Slash commands synced successfully.")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    if not DISCORD_TOKEN or not MONGODB_URI:
        print("CRITICAL: DISCORD_TOKEN or MONGODB_URI not set.")
    else:
        print("Starting web server for keep-alive...")
        keep_alive()
        print("Starting bot...")
        bot.run(DISCORD_TOKEN)
