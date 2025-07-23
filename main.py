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

# Import new core systems with error handling
try:
    from core.config import initialize_config, get_config
    from core.database import initialize_database, get_db_manager
    from core.security import get_security_manager
    from core.analytics import get_analytics
    from core.error_handler import initialize_error_handler, get_error_handler
    ENHANCED_CORE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Enhanced core systems not available, falling back to basic mode: {e}")
    ENHANCED_CORE_AVAILABLE = False
    # Provide basic fallbacks
    def initialize_config(): return None
    def get_config(): return None
    def initialize_database(uri): return None
    def get_db_manager(): return None
    def get_security_manager(): return None
    def get_analytics(): return None
    def initialize_error_handler(bot): return None
    def get_error_handler(): return None

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize configuration first
if ENHANCED_CORE_AVAILABLE:
    config = initialize_config()
    logger.info("✅ Enhanced configuration initialized")
else:
    config = None
    logger.info("⚠️ Running in basic mode without enhanced configuration")

# Load environment variables
load_dotenv()
DISCORD_TOKEN = config.discord_token if config else os.getenv("DISCORD_TOKEN")
MONGODB_URI = config.mongodb_uri if config else os.getenv("MONGODB_URI")

if not DISCORD_TOKEN:
    logger.error("❌ NO DISCORD_TOKEN FOUND")
    sys.exit(1)

logger.info("🚀 Starting Coal Python Bot with Enhanced Core Systems")

# Initialize core systems
if ENHANCED_CORE_AVAILABLE:
    try:
        # Initialize database with enhanced features
        db_manager = initialize_database(MONGODB_URI)
        logger.info("✅ Enhanced database system initialized")
        
        # Initialize security manager
        security_manager = get_security_manager()
        logger.info("✅ Security system initialized")
        
        # Initialize analytics
        analytics = get_analytics()
        logger.info("✅ Analytics system initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize core systems: {e}")
        logger.info("⚠️ Continuing in basic mode...")
        db_manager = None
        security_manager = None
        analytics = None
else:
    logger.info("⚠️ Enhanced core systems not available, running in basic mode")
    db_manager = None
    security_manager = None
    analytics = None

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
        "version": "4.0.0 - Enhanced Core Systems",
        "service": "Discord Bot",
        "port": config.port if config else int(os.environ.get('PORT', 10000)),
        "features": {
            "enhanced_database": True,
            "security_system": True,
            "analytics": True,
            "error_handling": True,
            "configuration_management": True
        }
    })

@app.route('/health')
def health_check():
    """Enhanced health check endpoint"""
    try:
        bot_status = "online" if 'bot' in globals() and bot.is_ready() else "starting"
        uptime = int(time.time() - bot_start_time)
        
        # Get system health metrics
        health_data = {
            "status": "healthy",
            "service": "Coal Python Bot",
            "bot_status": bot_status,
            "uptime_seconds": uptime,
            "timestamp": datetime.now().isoformat(),
            "port_exposed": True,
            "systems": {}
        }
        
        # Check database health
        if db_manager:
            db_health = asyncio.run(db_manager.health_check())
            health_data["systems"]["database"] = db_health
        
        # Check security system
        health_data["systems"]["security"] = {
            "status": "active",
            "blocked_users": len(security_manager.blocked_users),
            "rate_limits_active": len(security_manager.rate_limits)
        }
        
        # Check analytics
        health_data["systems"]["analytics"] = {
            "status": "active",
            "tracked_users": len(analytics.user_activity),
            "performance_metrics": len(analytics.performance_metrics)
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "degraded",
            "service": "Coal Python Bot",
            "bot_status": "starting",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 200

@app.route('/stats')
def bot_stats():
    """Enhanced bot statistics endpoint"""
    try:
        if 'bot' not in globals() or not bot.is_ready():
            return jsonify({"error": "Bot not ready"}), 503
        
        # Get comprehensive statistics
        stats = {
            "basic_stats": {
                "guild_count": len(bot.guilds),
                "user_count": len(bot.users),
                "latency": round(bot.latency * 1000, 2),
                "uptime_seconds": int(time.time() - bot_start_time)
            },
            "system_stats": {},
            "performance": {}
        }
        
        # Add database stats
        if db_manager:
            db_stats = asyncio.run(db_manager.get_server_stats())
            stats["system_stats"]["database"] = db_stats
        
        # Add security stats
        stats["system_stats"]["security"] = {
            "blocked_users": len(security_manager.blocked_users),
            "rate_limit_violations": len([
                v for violations in security_manager.suspicious_activity.values()
                for v in violations
                if time.time() - v["timestamp"] < 86400
            ])
        }
        
        # Add analytics insights
        server_insights = asyncio.run(analytics.get_server_insights())
        stats["analytics"] = server_insights
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/config')
def bot_config():
    """Configuration endpoint"""
    try:
        return jsonify(config.to_dict())
    except Exception as e:
        logger.error(f"Config error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return "PONG", 200

def run_flask_server():
    """Run Flask server"""
    port = config.port if config else int(os.environ.get('PORT', 10000))
    host = config.host if config else '0.0.0.0'
    logger.info(f"🌐 Starting enhanced web server on port {port}")
    try:
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
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

# Discord Bot Setup with Enhanced Features
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

# Initialize error handler
if ENHANCED_CORE_AVAILABLE:
    error_handler = initialize_error_handler(bot)
    logger.info("✅ Enhanced error handling system initialized")
else:
    error_handler = None
    logger.info("⚠️ Using basic error handling")

# Enhanced global error handler
@bot.event
async def on_error(event, *args, **kwargs):
    """Handle bot errors gracefully with enhanced logging"""
    try:
        if error_handler:
            await error_handler.handle_global_error(event, *args, **kwargs)
        else:
            logger.error(f"❌ Bot error in {event}: {sys.exc_info()[1]}")
            traceback.print_exc()
    except Exception as e:
        logger.error(f"❌ Critical error in error handler: {e}")
        traceback.print_exc()

@bot.event
async def on_command_error(ctx, error):
    """Enhanced command error handling"""
    try:
        # Track performance metrics if analytics available
        if analytics:
            await analytics.track_performance("command_error", 0, False)
        
        # Let the error handler deal with it
        if error_handler:
            handled = await error_handler.handle_command_error(ctx, error)
            if not handled:
                logger.error(f"❌ Unhandled command error: {error}")
                traceback.print_exc()
        else:
            # Basic error handling
            if isinstance(error, commands.CommandNotFound):
                return
            elif isinstance(error, commands.MissingPermissions):
                try:
                    await ctx.send("❌ You don't have permission to use this command.")
                except:
                    pass
            else:
                logger.error(f"❌ Command error: {error}")
                traceback.print_exc()
            
    except Exception as e:
        logger.error(f"❌ Error in command error handler: {e}")
        traceback.print_exc()

@bot.event
async def on_application_command_error(interaction, error):
    """Enhanced slash command error handling"""
    try:
        # Track performance metrics if analytics available
        if analytics:
            await analytics.track_performance("interaction_error", 0, False)
        
        # Let the error handler deal with it
        if error_handler:
            handled = await error_handler.handle_interaction_error(interaction, error)
            if not handled:
                logger.error(f"❌ Unhandled interaction error: {error}")
                traceback.print_exc()
        else:
            # Basic error handling
            logger.error(f"❌ Interaction error: {error}")
            traceback.print_exc()
            
    except Exception as e:
        logger.error(f"❌ Error in interaction error handler: {e}")
        traceback.print_exc()

@bot.event
async def on_ready():
    """Enhanced bot ready event with system initialization"""
    logger.info(f"✅ BOT ONLINE: {bot.user.name}")
    logger.info(f"📊 Bot ID: {bot.user.id}")
    logger.info(f"🔗 Invite: https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands")
    logger.info(f"🌐 Connected to {len(bot.guilds)} guild(s)")
    
    # Load cogs
    successful, failed = await load_cogs()
    
    # Sync commands
    await sync_commands()
    
    # Start background tasks
    asyncio.create_task(background_maintenance())
    
    # Track bot startup if analytics available
    if analytics:
        await analytics.track_performance("bot_startup", time.time() - bot_start_time, True)
    
    logger.info("🎉 Enhanced bot initialization complete!")

async def load_cogs():
    """Load all cogs with enhanced error handling"""
    cogs_to_load = [
        'cogs.events',
        'cogs.moderation', 
        'cogs.economy',
        'cogs.leveling',
        'cogs.cookies',
        'cogs.community',
        'cogs.simple_tickets',
        'cogs.enhanced_moderation',
        'cogs.settings',
        'cogs.job_tracking',
        'cogs.enhanced_minigames',
        'cogs.dashboard',
        'cogs.security_performance',
        'cogs.cool_commands',
        'cogs.pet_system',
        'cogs.stock_market',
        'cogs.backup_system'
    ]
    
    successful = 0
    failed = 0
    
    for cog in cogs_to_load:
        try:
            start_time = time.time()
            await bot.load_extension(cog)
            load_time = time.time() - start_time
            
            logger.info(f"✅ Loaded {cog} ({load_time:.2f}s)")
            if analytics:
                await analytics.track_performance(f"cog_load_{cog}", load_time, True)
            successful += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to load {cog}: {e}")
            if analytics:
                await analytics.track_error("CogLoadError", cog, 0, str(e))
            failed += 1
    
    logger.info(f"🎮 Cog loading complete: {successful} successful, {failed} failed")
    return successful, failed

async def sync_commands():
    """Sync slash commands with enhanced error handling"""
    try:
        start_time = time.time()
        logger.info("🔄 Syncing slash commands...")
        
        synced = await bot.tree.sync()
        sync_time = time.time() - start_time
        
        logger.info(f"✅ Synced {len(synced)} commands ({sync_time:.2f}s)")
        if analytics:
            await analytics.track_performance("command_sync", sync_time, True)
        
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")
        if analytics:
            await analytics.track_error("CommandSyncError", "sync", 0, str(e))

async def background_maintenance():
    """Enhanced background maintenance tasks"""
    logger.info("🔧 Starting background maintenance tasks...")
    
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            # Database maintenance
            if db_manager:
                await db_manager.cleanup_cache()
            
            # Security system maintenance
            await security_manager.cleanup_old_data()
            
            # Error handler maintenance
            if error_handler:
                await error_handler.clear_old_errors()
            
            # Analytics maintenance (run less frequently)
            if int(time.time()) % 3600 == 0:  # Every hour
                try:
                    # Generate and log insights
                    insights = await analytics.get_server_insights()
                    recommendations = await analytics.generate_recommendations()
                    
                    if recommendations:
                        logger.info(f"📊 Generated {len(recommendations)} recommendations")
                        for rec in recommendations[:3]:  # Log top 3
                            logger.info(f"💡 {rec['title']}: {rec['description']}")
                
                except Exception as e:
                    logger.error(f"Error in analytics maintenance: {e}")
            
            # Track maintenance performance
            await analytics.track_performance("background_maintenance", 5, True)
            
        except Exception as e:
            logger.error(f"❌ Background maintenance error: {e}")
            await analytics.track_error("MaintenanceError", "background", 0, str(e))
            await asyncio.sleep(60)  # Wait before retrying

async def main():
    """Enhanced main function with comprehensive initialization"""
    try:
        # Start web server
        web_server_thread = start_web_server()
        
        # Wait for server to start
        await asyncio.sleep(3)
        
        # Log configuration summary
        logger.info("🛠️  Configuration Summary:")
        if config:
            logger.info(f"   Environment: {config.environment}")
            logger.info(f"   Debug Mode: {config.debug_mode}")
            logger.info(f"   Features Enabled: Economy={config.features.enable_economy}, AI={config.features.enable_ai_features}, Analytics={config.analytics.enable_analytics}")
        else:
            logger.info("   Environment: production (basic mode)")
            logger.info("   Debug Mode: False")
            logger.info("   Features Enabled: Basic mode - all features enabled")
        
        # Start the bot
        logger.info("🚀 Starting Discord bot with enhanced systems...")
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
        logger.info("=" * 60)
        logger.info("🤖 COAL PYTHON BOT - ENHANCED VERSION 4.0")
        logger.info("🚀 Features: Advanced Database | Security | Analytics | Error Handling")
        logger.info("=" * 60)
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
