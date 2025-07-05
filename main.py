import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask, jsonify
from threading import Thread
import asyncio
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)

# Load environment variables first
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

if not DISCORD_TOKEN:
    print("❌ NO TOKEN FOUND")
    exit(1)

# Keep-alive server for Render deployment
app = Flask(__name__)

# Bot start time for uptime tracking
bot_start_time = time.time()

@app.route('/')
def home():
    uptime = time.time() - bot_start_time
    uptime_hours = uptime // 3600
    uptime_minutes = (uptime % 3600) // 60
    
    return jsonify({
        "status": "✅ Coal Python Bot is online!",
        "uptime": f"{int(uptime_hours)}h {int(uptime_minutes)}m",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "service": "Discord Bot"
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Check if bot is ready
        bot_status = "online" if 'bot' in globals() and bot.is_ready() else "starting"
        
        return jsonify({
            "status": "healthy",
            "bot_status": bot_status,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": int(time.time() - bot_start_time)
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/stats')
def bot_stats():
    """Bot statistics endpoint"""
    try:
        if 'bot' not in globals() or not bot.is_ready():
            return jsonify({"error": "Bot not ready"}), 503
            
        return jsonify({
            "guild_count": len(bot.guilds),
            "user_count": len(bot.users),
            "latency": round(bot.latency * 1000, 2),
            "uptime_seconds": int(time.time() - bot_start_time),
            "status": "online"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_flask_server():
    """Run Flask server on the port provided by Render"""
    port = int(os.environ.get('PORT', 8080))  # Use Render's PORT or fallback to 8080
    print(f"🌐 Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def start_web_server():
    """Start the web server in a separate thread"""
    server_thread = Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    print("🚀 Web server started successfully")

# Discord Bot Setup
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
    print(f"✅ BOT ONLINE: {bot.user.name}")
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
        'cogs.tickets'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"[Main] ✅ Loaded {cog}")
        except Exception as e:
            print(f"[Main] ❌ Failed to load {cog}: {e}")

async def startup_maintenance():
    """Perform startup maintenance and optimization"""
    try:
        print("[Main] 🔧 Performing startup maintenance...")
        
        import database as db
        
        # Remove deprecated warning system
        result = db.remove_deprecated_warning_system()
        if result['success']:
            print(f"[Main] ✅ Removed warning system from {result['users_updated']} users")
        
        # Optimize database
        optimization = db.optimize_database_live()
        if optimization['success']:
            print(f"[Main] ✅ Database optimized with {len(optimization['indexes_created'])} indexes")
        
        # Auto-sync first 100 users for better performance
        print("[Main] 🔄 Auto-syncing user data...")
        users_synced = 0
        try:
            all_users = db.get_all_users_for_maintenance()[:100]  # Limit to 100 for startup
            for user_data in all_users:
                db.auto_sync_user_data(user_data['user_id'])
                users_synced += 1
        except Exception as e:
            print(f"[Main] ⚠️ Error in user sync: {e}")
        
        print(f"[Main] ✅ Startup maintenance complete. Synced {users_synced} users.")
        
    except Exception as e:
        print(f"[Main] ❌ Error in startup maintenance: {e}")

async def main():
    """Main function to run the bot"""
    try:
        print("🚀 Starting Coal Python Bot...")
        
        # Start the web server first
        start_web_server()
        
        # Load all cogs
        await load_cogs()
        
        # Perform startup maintenance
        await startup_maintenance()
        
        print("🎮 Starting Discord bot...")
        # Start the bot
        await bot.start(DISCORD_TOKEN)
        
    except Exception as e:
        print(f"[Main] ❌ Error starting bot: {e}")

if __name__ == "__main__":
    try:
        # Set bot start time
        bot_start_time = time.time()
        
        print("=" * 50)
        print("🤖 COAL PYTHON BOT - STARTING UP")
        print("=" * 50)
        
        # Run the main function
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        raise
