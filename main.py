import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from discord import app_commands

# --- Keep-alive server (for Render/UptimeRobot/Glitch etc.) ---
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
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI')

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Needed for member updates and roles

GUILD_ID = 1370009417726169250  # Your guild/server ID

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
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

    print("🔄 Syncing slash commands...")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} command(s) to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# --- Run the Bot ---
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN is missing in the .env file.")
    elif not MONGODB_URI:
        print("❌ MONGODB_URI is missing in the .env file.")
    else:
        print("🌐 Starting Flask keep-alive server...")
        keep_alive()
        print("🤖 Starting Discord bot...")
        bot.run(DISCORD_TOKEN)
