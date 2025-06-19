import os
import discord
from discord.ext import commands
from discord.commands import Option
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
ARRIVALS_CHANNEL_ID = int(os.getenv("ARRIVALS_CHANNEL_ID"))
GUILD_ID = 1370009417726169250  # Your server's ID

# MongoDB setup
mongo = MongoClient(MONGODB_URI)
db = mongo["coal"]  # Use your DB name here

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Helper Functions ---

def is_admin(ctx):
    return ctx.author.guild_permissions.administrator

def is_cookie_manager(ctx):
    role = discord.utils.get(ctx.author.roles, name="🚨🚓Cookie Manager 🍪")
    return is_admin(ctx) or role is not None

def is_moderator(ctx):
    mod_roles = ["Moderator ��🚓", "🚨 Lead moderator"]
    return is_admin(ctx) or any(discord.utils.get(ctx.author.roles, name=role) for role in mod_roles)

def get_cookies(user_id):
    user = db.cookies.find_one({"_id": user_id})
    return user["cookies"] if user else 0

def set_cookies(user_id, amount):
    db.cookies.update_one({"_id": user_id}, {"$set": {"cookies": amount}}, upsert=True)

def add_cookies(user_id, amount):
    db.cookies.update_one({"_id": user_id}, {"$inc": {"cookies": amount}}, upsert=True)

def get_leaderboard(skip=0, limit=10):
    return list(db.cookies.find().sort("cookies", -1).skip(skip).limit(limit))

def get_rank(user_id):
    all_users = list(db.cookies.find().sort("cookies", -1))
    for i, user in enumerate(all_users, 1):
        if user["_id"] == user_id:
            return i
    return None

def get_log_channel_id(guild):
    config = db.config.find_one({"_id": "log_channel"})
    return config["channel_id"] if config else LOG_CHANNEL_ID

# --- Slash Commands ---

@bot.slash_command(guild_ids=[GUILD_ID], description="Add cookies to a user")
async def addcookies(ctx, user: Option(discord.Member, "User"), amount: Option(int, "Amount")):
    if not is_cookie_manager(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    add_cookies(user.id, amount)
    await ctx.respond(f"Added {amount} cookies to {user.mention}.")

@bot.slash_command(guild_ids=[GUILD_ID], description="Remove all cookies from a user")
async def removecookies(ctx, user: Option(discord.Member, "User")):
    if not is_cookie_manager(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    set_cookies(user.id, 0)
    await ctx.respond(f"All cookies removed from {user.mention}.")

@bot.slash_command(guild_ids=[GUILD_ID], description="Reset cookies for a user")
async def resetcookies(ctx, user: Option(discord.Member, "User")):
    if not is_cookie_manager(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    set_cookies(user.id, 0)
    await ctx.respond(f"{user.mention}'s cookies have been reset to zero.")

@bot.slash_command(guild_ids=[GUILD_ID], description="Show your or another user's cookies")
async def cookies(ctx, user: Option(discord.Member, "User", required=False)):
    user = user or ctx.author
    cookies = get_cookies(user.id)
    await ctx.respond(f"{user.mention} has {cookies} cookies.")

@bot.slash_command(guild_ids=[GUILD_ID], description="Show the leaderboard")
async def top(ctx, page: Option(int, "Page", default=1)):
    per_page = 10
    skip = (page - 1) * per_page
    leaderboard = get_leaderboard(skip, per_page)
    desc = ""
    for i, user in enumerate(leaderboard, skip + 1):
        member = ctx.guild.get_member(user['_id'])
        name = member.mention if member else f"User {user['_id']}"
        desc += f"{i}. {name} - {user['cookies']} cookies\n"
    embed = discord.Embed(title="Cookie Leaderboard", description=desc or "No data.", color=0xFFD700)
    await ctx.respond(embed=embed)

@bot.slash_command(guild_ids=[GUILD_ID], description="Show your rank in the leaderboard")
async def cookiesrank(ctx, user: Option(discord.Member, "User", required=False)):
    user = user or ctx.author
    rank = get_rank(user.id)
    if rank:
        await ctx.respond(f"{user.mention} is ranked #{rank}.")
    else:
        await ctx.respond(f"{user.mention} is not ranked.")

@bot.slash_command(guild_ids=[GUILD_ID], description="Give cookies to all members")
async def cookiesgiveall(ctx, amount: Option(int, "Amount")):
    if not is_cookie_manager(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    for member in ctx.guild.members:
        if not member.bot:
            add_cookies(member.id, amount)
    await ctx.respond(f"Gave {amount} cookies to everyone!")

@bot.slash_command(guild_ids=[GUILD_ID], description="Warn a user")
async def warn(ctx, user: Option(discord.Member, "User"), reason: Option(str, "Reason", required=False)):
    if not is_moderator(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    db.warnings.insert_one({"user_id": user.id, "reason": reason or "No reason", "mod": ctx.author.id})
    await ctx.respond(f"{user.mention} has been warned. Reason: {reason or 'No reason'}")

@bot.slash_command(guild_ids=[GUILD_ID], description="Show warnings for a user")
async def warnlist(ctx, user: Option(discord.Member, "User")):
    if not is_moderator(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    warnings = list(db.warnings.find({"user_id": user.id}))
    if not warnings:
        await ctx.respond(f"{user.mention} has no warnings.")
        return
    desc = "\n".join([f"{i+1}. {w['reason']} (by <@{w['mod']}>)" for i, w in enumerate(warnings)])
    embed = discord.Embed(title=f"Warnings for {user}", description=desc, color=0xFF0000)
    await ctx.respond(embed=embed)

@bot.slash_command(guild_ids=[GUILD_ID], description="Send an announcement")
async def announcement(ctx, message: Option(str, "Announcement")):
    if not is_admin(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    embed = discord.Embed(title="Announcement", description=message, color=0x00FF00)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.slash_command(guild_ids=[GUILD_ID], description="Show server info")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=guild.name, color=0x3498db)
    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"))
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    await ctx.respond(embed=embed)

@bot.slash_command(guild_ids=[GUILD_ID], description="Create a poll")
async def poll(ctx, question: Option(str, "Question"), option1: Option(str, "Option 1"), option2: Option(str, "Option 2")):
    embed = discord.Embed(title="Poll", description=question, color=0x7289da)
    embed.add_field(name="1️⃣", value=option1, inline=False)
    embed.add_field(name="2️⃣", value=option2, inline=False)
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("1️⃣")
    await msg.add_reaction("2️⃣")
    await ctx.respond("Poll created!", ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID], description="Set welcome message")
async def setwelcome(ctx, message: Option(str, "Welcome message")):
    if not is_admin(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    db.config.update_one({"_id": "welcome"}, {"$set": {"message": message}}, upsert=True)
    await ctx.respond("Welcome message updated.")

@bot.slash_command(guild_ids=[GUILD_ID], description="Set leave message")
async def setleave(ctx, message: Option(str, "Leave message")):
    if not is_admin(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    db.config.update_one({"_id": "leave"}, {"$set": {"message": message}}, upsert=True)
    await ctx.respond("Leave message updated.")

@bot.slash_command(guild_ids=[GUILD_ID], description="Set the logging channel")
async def setlogchannel(ctx, channel: Option(discord.TextChannel, "Channel")):
    if not is_admin(ctx):
        await ctx.respond("You don't have permission to use this command.", ephemeral=True)
        return
    db.config.update_one({"_id": "log_channel"}, {"$set": {"channel_id": channel.id}}, upsert=True)
    await ctx.respond(f"Logging channel set to {channel.mention}.")

# --- Logging and Events ---

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        await bot.sync_commands()
        print("Commands synced successfully.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.event
async def on_member_join(member):
    config = db.config.find_one({"_id": "welcome"})
    message = config["message"] if config else "Welcome, {user}!"
    channel = member.guild.get_channel(ARRIVALS_CHANNEL_ID)
    if channel:
        embed = discord.Embed(description=message.format(user=member.mention), color=0x00ff00)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Joined: {member.joined_at.strftime('%Y-%m-%d')}")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    config = db.config.find_one({"_id": "leave"})
    message = config["message"] if config else "{user} has left the server."
    channel = member.guild.get_channel(ARRIVALS_CHANNEL_ID)
    if channel:
        embed = discord.Embed(description=message.format(user=member.mention), color=0xff0000)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Left: {discord.utils.utcnow().strftime('%Y-%m-%d')}")
        await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.guild and not message.author.bot:
        channel_id = get_log_channel_id(message.guild)
        channel = message.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(title="Message Deleted", description=message.content, color=0xffa500)
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.guild and not before.author.bot:
        channel_id = get_log_channel_id(before.guild)
        channel = before.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(title="Message Edited", color=0x3498db)
            embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
            embed.add_field(name="Before", value=before.content, inline=False)
            embed.add_field(name="After", value=after.content, inline=False)
            await channel.send(embed=embed)

# --- Run the bot ---
bot.run(TOKEN)
