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

# --- CONFIG: Cookie Manager role ID ---
COOKIE_MANAGER_ROLE_ID = 1372121024841125888

# --- Cookie System Helpers ---

def get_cookies(user_id):
    user = db.cookies.find_one({"user_id": str(user_id)})
    return user["cookies"] if user and "cookies" in user else 0

def set_cookies(user_id, amount):
    db.cookies.update_one(
        {"user_id": str(user_id)},
        {"$set": {"cookies": int(amount)}},
        upsert=True
    )

def add_cookies(user_id, amount):
    db.cookies.update_one(
        {"user_id": str(user_id)},
        {"$inc": {"cookies": int(amount)}},
        upsert=True
    )

def remove_cookies(user_id, amount):
    current = get_cookies(user_id)
    new_total = max(0, current - int(amount))
    set_cookies(user_id, new_total)

def get_leaderboard(skip=0, limit=10):
    return list(db.cookies.find().sort("cookies", -1).skip(skip).limit(limit))

def get_rank(user_id):
    all_users = list(db.cookies.find().sort("cookies", -1))
    for idx, user in enumerate(all_users, 1):
        if user["user_id"] == str(user_id):
            return idx
    return None

# --- Permission Check Helper ---

def is_admin_or_cookie_manager(member: discord.Member):
    return (
        member.guild_permissions.administrator or
        any(role.id == COOKIE_MANAGER_ROLE_ID for role in member.roles)
    )

# --- Bot Setup ---

intents = discord.Intents.default()
intents.members = True  # Needed for member join/leave events
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        await bot.sync_commands()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# --- /ping Command ---
@bot.slash_command(name="ping", description="Check if the bot is alive.")
async def ping(ctx):
    await ctx.respond("Pong!")

# --- /cookies Command ---
@bot.slash_command(name="cookies", description="Show how many cookies you or another user have.")
@option("user", description="User to check", required=False)
async def cookies(ctx, user: discord.Member = None):
    user = user or ctx.author
    total = get_cookies(user.id)
    await ctx.respond(f"{user.mention} has {total} 🍪 cookies.")

# --- /addcookies Command ---
@bot.slash_command(name="addcookies", description="Add cookies to a user (admin/Cookie Manager only).")
@option("user", description="User to add cookies to", required=True)
@option("amount", description="Amount of cookies to add", required=True)
async def addcookies(ctx, user: discord.Member, amount: int):
    if not is_admin_or_cookie_manager(ctx.author):
        await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        return
    add_cookies(user.id, amount)
    total = get_cookies(user.id)
    await ctx.respond(f"Added {amount} 🍪 to {user.mention}. They now have {total} cookies.")

# --- /removecookies Command ---
@bot.slash_command(name="removecookies", description="Remove cookies from a user (admin/Cookie Manager only).")
@option("user", description="User to remove cookies from", required=True)
@option("amount", description="Amount of cookies to remove", required=True)
async def removecookies(ctx, user: discord.Member, amount: int):
    if not is_admin_or_cookie_manager(ctx.author):
        await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        return
    remove_cookies(user.id, amount)
    total = get_cookies(user.id)
    await ctx.respond(f"Removed {amount} 🍪 from {user.mention}. They now have {total} cookies.")

# --- /cookiesgiveall Command ---
@bot.slash_command(name="cookiesgiveall", description="Give cookies to everyone in the server (admin/Cookie Manager only).")
@option("amount", description="Amount of cookies to give to everyone", required=True)
async def cookiesgiveall(ctx, amount: int):
    if not is_admin_or_cookie_manager(ctx.author):
        await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        return
    count = 0
    for member in ctx.guild.members:
        if not member.bot:
            add_cookies(member.id, amount)
            count += 1
    await ctx.respond(f"Gave {amount} 🍪 to {count} members!")

# --- /cookiesreset Command ---
@bot.slash_command(name="cookiesreset", description="Reset all cookies to zero (admin/Cookie Manager only).")
async def cookiesreset(ctx):
    if not is_admin_or_cookie_manager(ctx.author):
        await ctx.respond("You do not have permission to use this command.", ephemeral=True)
        return
    db.cookies.update_many({}, {"$set": {"cookies": 0}})
    await ctx.respond("All cookies have been reset to zero.")

# --- /cookiesrank Command ---
@bot.slash_command(name="cookiesrank", description="Show your or another user's rank in the cookies leaderboard.")
@option("user", description="User to check", required=False)
async def cookiesrank(ctx, user: discord.Member = None):
    user = user or ctx.author
    rank = get_rank(user.id)
    if rank:
        await ctx.respond(f"{user.mention} is ranked #{rank} in cookies!")
    else:
        await ctx.respond(f"{user.mention} is not ranked yet.")

# --- /top Command ---
@bot.slash_command(name="top", description="Show the cookie leaderboard (10 per page).")
@option("page", description="Leaderboard page", required=False)
async def top(ctx, page: int = 1):
    per_page = 10
    skip = (page - 1) * per_page
    leaderboard = get_leaderboard(skip, per_page)
    if not leaderboard:
        await ctx.respond("No data for this page.")
        return
    msg = f"**🍪 Cookie Leaderboard (Page {page})**\n"
    for idx, user in enumerate(leaderboard, start=skip + 1):
        user_id = int(user['user_id'])
        member = ctx.guild.get_member(user_id)
        name = member.mention if member else f\"<@{user_id}>\"
        msg += f\"{idx}. {name}: {user['cookies']} cookies\\n\"
    await ctx.respond(msg)

if __name__ == \"__main__\":
    if not DISCORD_TOKEN or not MONGODB_URI:
        print(\"Please set DISCORD_TOKEN and MONGODB_URI in your environment.\")
    else:
        bot.run(DISCORD_TOKEN)
