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
    
    # Check database connectivity and stats
    try:
        import database as db
        stats = db.get_database_stats()
        if stats["success"]:
            print(f"💾 Database connected - {stats['total_users']} users, {stats['total_xp']:,} total XP, {stats['total_cookies']:,} total cookies")
            
            # Perform automatic database maintenance
            print("🔧 Running automatic database maintenance...")
            maintenance_result = db.maintenance_cleanup()
            if maintenance_result["success"]:
                print(f"✅ Maintenance complete - {maintenance_result['recovered_users']} users recovered, {maintenance_result['cleaned_entries']} entries cleaned")
            else:
                print(f"⚠️ Maintenance warning: {maintenance_result['message']}")
                
            # Get updated stats after maintenance
            updated_stats = db.get_database_stats()
            if updated_stats["success"]:
                print(f"📊 Post-maintenance stats - {updated_stats['total_users']} users total")
        else:
            print(f"❌ Database issue: {stats['message']}")
    except Exception as e:
        print(f"❌ Database check failed: {e}")

# Load cogs
async def load_cogs():
    """Load all cogs"""
    cogs = [
        'cogs.leveling',
        'cogs.cookies', 
        'cogs.economy',
        'cogs.events',
        'cogs.community',
        'cogs.moderation',
        'cogs.settings',
        'cogs.tickets'  # Added tickets system
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"[Main] Loaded {cog}")
        except Exception as e:
            print(f"[Main] Failed to load {cog}: {e}")

async def startup_maintenance():
    """Perform startup maintenance and optimization"""
    try:
        print("[Main] Performing startup maintenance...")
        
        # Remove deprecated warning system
        result = db.remove_deprecated_warning_system()
        if result['success']:
            print(f"[Main] Removed warning system from {result['users_updated']} users")
        
        # Optimize database
        optimization = db.optimize_database_live()
        if optimization['success']:
            print(f"[Main] Database optimized with {len(optimization['indexes_created'])} indexes")
        
        # Auto-sync first 100 users for better performance
        print("[Main] Auto-syncing user data...")
        users_synced = 0
        try:
            all_users = db.get_all_users_for_maintenance()[:100]  # Limit to 100 for startup
            for user_data in all_users:
                db.auto_sync_user_data(user_data['user_id'])
                users_synced += 1
        except Exception as e:
            print(f"[Main] Error in user sync: {e}")
        
        print(f"[Main] Startup maintenance complete. Synced {users_synced} users.")
        
    except Exception as e:
        print(f"[Main] Error in startup maintenance: {e}")

async def main():
    """Main function to run the bot"""
    try:
        # Load all cogs
        await load_cogs()
        
        # Perform startup maintenance
        await startup_maintenance()
        
        # Start the bot
        await bot.start(DISCORD_TOKEN)
        
    except Exception as e:
        print(f"[Main] Error starting bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
