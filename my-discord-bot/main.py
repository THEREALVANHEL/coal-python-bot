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
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    """Event that runs when the bot is ready."""
    # Load cogs from cogs directory
    cogs_path = './my-discord-bot/cogs'
    if os.path.exists(cogs_path):
        for filename in os.listdir(cogs_path):
            if filename.endswith('.py') and filename not in ['__init__.py']:
                try:
                    bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f"✅ Loaded cog from cogs: {filename}")
                except Exception as e:
                    print(f"❌ Failed to load cog {filename} from cogs: {e}")
    else:
        print(f"Warning: {cogs_path} does not exist. No cogs loaded from cogs directory.")
    # Load cogs from parent directory
    parent_cogs = ['leveling', 'events', 'moderation']
    for cog in parent_cogs:
        try:
            bot.load_extension(cog)
            print(f"✅ Loaded cog from parent: {cog}.py")
        except Exception as e:
            print(f"❌ Failed to load cog {cog} from parent: {e}")
    print(f"Logged in as {bot.user}")
    print("-------------------")
    # Sync slash commands (if using py-cord 2.0+)
    try:
        await bot.sync_commands()
        print("✅ Slash commands synced successfully.")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

@bot.slash_command(name="botdebug", description="Show loaded cogs and commands.", guild_ids=[1370009417726169250])
async def botdebug(ctx):
    cogs = list(bot.cogs.keys())
    commands_list = [cmd.name for cmd in bot.commands]
    embed = discord.Embed(
        title="🤖 Bot Debug Panel",
        description="Here are the loaded cogs and commands:",
        color=discord.Color.dark_blue()
    )
    embed.add_field(name="🧩 Loaded Cogs", value="\n".join(cogs) if cogs else "None", inline=False)
    embed.add_field(name="🛠️ Commands", value=", ".join(commands_list) if commands_list else "None", inline=False)
    embed.set_footer(text="Futuristic UK Debug | BLEK NEPHEW", icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
    await ctx.respond(embed=embed, ephemeral=True)

# --- Main Execution ---
if __name__ == "__main__":
    if not DISCORD_TOKEN or not MONGODB_URI:
        print("CRITICAL: DISCORD_TOKEN or MONGODB_URI not set.")
    else:
        print("Starting web server for keep-alive...")
        keep_alive()
        print("Starting bot...")
        bot.run(DISCORD_TOKEN)
