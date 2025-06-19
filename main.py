import os
import discord
from discord import option
from discord.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file (for local dev)
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI')

# MongoDB setup
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['coal']  # Database name

# Intents and bot setup
intents = discord.Intents.default()
intents.members = True  # Needed for member join/leave events
bot = commands.Bot(command_prefix="!", intents=intents)

# Sync slash commands on startup
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        await bot.sync_commands()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Simple /ping command
guild_ids = []  # Add your guild ID(s) here for testing, or leave empty for global

@bot.slash_command(name="ping", description="Check if the bot is alive.", guild_ids=guild_ids)
async def ping(ctx):
    await ctx.respond("Pong!")

if __name__ == "__main__":
    if not DISCORD_TOKEN or not MONGODB_URI:
        print("Please set DISCORD_TOKEN and MONGODB_URI in your environment.")
    else:
        bot.run(DISCORD_TOKEN)
