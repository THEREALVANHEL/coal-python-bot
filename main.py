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
  # Make sure to run on 0.0.0.0 to be accessible externally
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- Bot Setup ---

# Load environment variables from a .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI') # We'll use this in our database file

# Define the bot's intents
intents = discord.Intents.default()
intents.members = True          # Required for welcome/leave messages
intents.message_content = True  # Required for message logging

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Event that runs when the bot is ready."""
    print(f"Logged in as {bot.user}")
    print("-------------------")
    print("Loading cogs...")

    # Load all .py files from the 'cogs' directory
    for filename in os.listdir('./my-discord-bot/cogs'):
        if filename.endswith('.py'):
            try:
                # The path needs to match the directory structure
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")
                print(type(e)) # print the exception type

    print("-------------------")
    
    # Sync slash commands
    try:
        await bot.sync_commands()
        print(" Slash commands synced successfully.")
    except Exception as e:
        print(f" Error syncing commands: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # Validate that the token is present
    if not DISCORD_TOKEN:
        print("CRITICAL: DISCORD_TOKEN is not set in your environment or .env file.")
    elif not MONGODB_URI:
         print("CRITICAL: MONGODB_URI is not set in your environment or .env file.")
    else:
        print("Starting web server for keep-alive...")
        keep_alive()
        print("Starting bot...")
        bot.run(DISCORD_TOKEN)
