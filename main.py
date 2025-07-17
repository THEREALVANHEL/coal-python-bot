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
import sys
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

if not DISCORD_TOKEN:
    logger.error("❌ NO DISCORD_TOKEN FOUND")
    sys.exit(1)

logger.info("🚀 Starting Coal Python Bot with simplified startup")

# Keep-alive server for Render deployment
app = Flask(__name__)
bot_start_time = time.time()

@app.route('/')
def home():
    uptime = time.time() - bot_start_time
    uptime_hours = uptime // 3600
    uptime_minutes = (uptime % 3600) // 60
    
    bot_status = "online" if 'bot' in globals() and bot.is_ready() else "starting"
    
    return jsonify({
        "status": "✅ Coal Python Bot is running",
        "bot_status": bot_status,
        "uptime": f"{int(uptime_hours)}h {int(uptime_minutes)}m",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0 - Stable",
        "service": "Discord Bot",
        "port": int(os.environ.get('PORT', 10000))
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        bot_status = "online" if 'bot' in globals() and bot.is_ready() else "starting"
        uptime = int(time.time() - bot_start_time)
        
        return jsonify({
            "status": "healthy",
            "service": "Coal Python Bot",
            "bot_status": bot_status,
            "uptime_seconds": uptime,
            "timestamp": datetime.now().isoformat(),
            "port_exposed": True
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "healthy",
            "service": "Coal Python Bot",
            "bot_status": "starting",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 200

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
        logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return "PONG", 200

def run_flask_server():
    """Run Flask server"""
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Starting web server on port {port}")
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        logger.error(f"❌ Failed to start Flask server: {e}")
        raise

def start_web_server():
    """Start the web server in a separate thread"""
    logger.info("🚀 Starting Flask web server...")
    server_thread = Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server time to start
    logger.info("✅ Web server started successfully")
    return server_thread

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None,
    case_insensitive=True,
    heartbeat_timeout=60.0,
    guild_ready_timeout=10.0
)

# Global error handler
@bot.event
async def on_error(event, *args, **kwargs):
    """Handle bot errors gracefully"""
    logger.error(f"❌ Bot error in {event}: {sys.exc_info()[1]}")
    traceback.print_exc()

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        try:
            await ctx.send("❌ You don't have permission to use this command.")
        except:
            pass
    elif isinstance(error, discord.HTTPException):
        logger.error(f"❌ HTTP error in command: {error}")
        if "rate limit" in str(error).lower():
            await asyncio.sleep(5)
    else:
        logger.error(f"❌ Unhandled command error: {error}")
        traceback.print_exc()

@bot.event
async def on_ready():
    """Handle bot ready event"""
    logger.info(f"✅ BOT ONLINE: {bot.user.name}")
    logger.info(f"📊 Bot ID: {bot.user.id}")
    logger.info(f"🔗 Invite: https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands")
    logger.info(f"🌐 Connected to {len(bot.guilds)} guild(s)")
    
    # Load cogs
    await load_cogs()
    
    # Sync commands
    await sync_commands()
    
    # Start database maintenance
    asyncio.create_task(database_maintenance())
    
    logger.info("🎉 Bot initialization complete!")

async def load_cogs():
    """Load all cogs"""
    cogs_to_load = [
        'cogs.events',
        'cogs.moderation', 
        'cogs.economy',
        'cogs.leveling',
        'cogs.cookies',
        'cogs.community',
        'cogs.super_tickets',           # New super ticket system (replaces tickets & premium_tickets)
        'cogs.enhanced_moderation',
        'cogs.settings',
        'cogs.job_tracking',
        'cogs.enhanced_minigames',      # New enhanced minigames (replaces minigames)
        'cogs.dashboard',               # Personal dashboard
        'cogs.security_performance',    # Security and performance monitoring
        'cogs.cool_commands'            # Cool additional commands
    ]
    
    successful = 0
    failed = 0
    
    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            logger.info(f"✅ Loaded {cog}")
            successful += 1
        except Exception as e:
            logger.error(f"❌ Failed to load {cog}: {e}")
            failed += 1
    
    logger.info(f"🎮 Cog loading complete: {successful} successful, {failed} failed")
    return successful, failed

async def sync_commands():
    """Sync slash commands with error handling"""
    try:
        logger.info("🔄 Syncing slash commands...")
        synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")

async def database_maintenance():
    """Perform database maintenance tasks"""
    try:
        await asyncio.sleep(60)  # Wait 1 minute after startup
        logger.info("🔧 Starting database maintenance...")
        
        import database as db
        
        # Remove deprecated systems
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(db.remove_deprecated_warning_system),
                timeout=30
            )
            if result.get('success'):
                logger.info(f"✅ Cleaned up warning system for {result.get('users_updated', 0)} users")
        except Exception as e:
            logger.error(f"⚠️ Warning system cleanup failed: {e}")
        
        # Optimize database
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(db.optimize_database_live),
                timeout=30
            )
            if result.get('success'):
                logger.info(f"✅ Database optimized")
        except Exception as e:
            logger.error(f"⚠️ Database optimization failed: {e}")
        
        logger.info("✅ Database maintenance complete")
        
    except Exception as e:
        logger.error(f"❌ Database maintenance error: {e}")

async def main():
    """Main function to run the bot"""
    try:
        # Start web server
        web_server_thread = start_web_server()
        
        # Wait a moment for server to start
        await asyncio.sleep(3)
        
        # Start the bot
        logger.info("🚀 Starting Discord bot...")
        await bot.start(DISCORD_TOKEN)
        
    except discord.LoginFailure as e:
        logger.error(f"❌ Login failed: {e}")
        logger.error("🔑 Check your DISCORD_TOKEN environment variable")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        logger.info("=" * 50)
        logger.info("🤖 COAL PYTHON BOT - STABLE VERSION")
        logger.info("=" * 50)
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
