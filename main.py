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
    
    return jsonify({
        "status": "Coal Python Bot is running!",
        "uptime_hours": int(uptime_hours),
        "uptime_minutes": int(uptime_minutes),
        "timestamp": datetime.now().isoformat(),
        "enhanced_core": ENHANCED_CORE_AVAILABLE
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "bot_ready": bot.is_ready() if 'bot' in globals() else False,
        "enhanced_core": ENHANCED_CORE_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    })

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Enhanced bot setup with comprehensive intents
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True
intents.voice_states = True
intents.presences = True

# Create bot with enhanced features
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None,
    case_insensitive=True,
    strip_after_prefix=True,
    owner_ids={123456789}  # Replace with your actual Discord user ID
)

# Initialize error handler if available
if ENHANCED_CORE_AVAILABLE:
    try:
        initialize_error_handler(bot)
        logger.info("✅ Enhanced error handling initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize error handler: {e}")

# Enhanced startup event
@bot.event
async def on_ready():
    logger.info(f'🤖 {bot.user} has connected to Discord!')
    logger.info(f'📊 Serving {len(bot.guilds)} guilds with {len(bot.users)} users')
    
    # Set enhanced activity status
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="Coal Mining Operations | Enhanced V4.0"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)
    
    # Log enhanced features status
    if ENHANCED_CORE_AVAILABLE:
        logger.info("✅ All enhanced systems operational")
        if analytics:
            await analytics.log_bot_startup()
    else:
        logger.info("⚠️ Running in basic mode")
    
    # Sync commands on startup
    try:
        synced = await bot.tree.sync()
        logger.info(f"🔄 Synced {len(synced)} slash commands")
        
        # Also sync to specific guilds for faster updates
        for guild in bot.guilds:
            try:
                guild_synced = await bot.tree.sync(guild=guild)
                logger.info(f"🔄 Synced {len(guild_synced)} commands to {guild.name}")
            except Exception as e:
                logger.error(f"❌ Failed to sync to {guild.name}: {e}")
                
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")

# Enhanced error handling
@bot.event
async def on_command_error(ctx, error):
    if ENHANCED_CORE_AVAILABLE and get_error_handler():
        await get_error_handler().handle_command_error(ctx, error)
    else:
        # Basic error handling
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions!")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send("❌ An error occurred while processing the command.")

@bot.event
async def on_application_command_error(interaction, error):
    if ENHANCED_CORE_AVAILABLE and get_error_handler():
        await get_error_handler().handle_interaction_error(interaction, error)
    else:
        # Basic error handling for slash commands
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ An error occurred while processing the command.", ephemeral=True)
        logger.error(f"Slash command error: {error}")

# Enhanced member events
@bot.event
async def on_member_join(member):
    if ENHANCED_CORE_AVAILABLE and analytics:
        await analytics.log_member_join(member)
    logger.info(f"👋 {member} joined {member.guild.name}")

@bot.event
async def on_member_remove(member):
    if ENHANCED_CORE_AVAILABLE and analytics:
        await analytics.log_member_leave(member)
    logger.info(f"👋 {member} left {member.guild.name}")

# Manual sync command for bot owner
@bot.command(name='sync')
async def sync_commands(ctx):
    """Manually sync slash commands (Owner only)"""
    if ctx.author.id not in bot.owner_ids:
        await ctx.send("❌ Only the bot owner can use this command!")
        return
    
    try:
        # Clear and sync globally
        bot.tree.clear_commands(guild=None)
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} commands globally!")
        
        # Also sync to current guild for faster updates
        if ctx.guild:
            guild_synced = await bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"✅ Synced {len(guild_synced)} commands to {ctx.guild.name}!")
        
        logger.info(f"Manual sync completed by {ctx.author}")
        
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")
        logger.error(f"Manual sync failed: {e}")

# Enhanced message events
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Security check if available
    if ENHANCED_CORE_AVAILABLE and security_manager:
        if await security_manager.check_message_security(message):
            return  # Message was flagged and handled
    
    # Process commands
    await bot.process_commands(message)

# Load all cogs with enhanced error handling
async def load_cogs():
    cogs_to_load = [
        'cogs.economy',
        # 'cogs.enhanced_economy',  # Disabled to avoid work command conflict
        'cogs.moderation',
        'cogs.enhanced_moderation',
        'cogs.enhanced_minigames',
        'cogs.community',
        'cogs.events',
        'cogs.cookies',
        'cogs.dashboard',
        'cogs.cool_commands',
        'cogs.backup_system',
        'cogs.pet_system',
        'cogs.stock_market',
        'cogs.job_tracking',
        'cogs.leveling',
        'cogs.settings',
        'cogs.simple_tickets',
        'cogs.security_performance'
    ]
    
    loaded_count = 0
    failed_count = 0
    
    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            logger.info(f"✅ Loaded {cog}")
            loaded_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to load {cog}: {e}")
            failed_count += 1
    
    logger.info(f"📦 Cog loading complete: {loaded_count} loaded, {failed_count} failed")
    return loaded_count, failed_count

# Enhanced shutdown handler
@bot.event
async def on_disconnect():
    logger.info("🔌 Bot disconnected from Discord")
    if ENHANCED_CORE_AVAILABLE and analytics:
        await analytics.log_bot_shutdown()

# Main execution with enhanced startup
async def main():
    # Start Flask server in background
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask keep-alive server started")
    
    # Load all cogs
    await load_cogs()
    
    # Start the bot with enhanced error handling
    try:
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("🛑 Bot shutdown requested")
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")
        raise
    finally:
        if ENHANCED_CORE_AVAILABLE:
            # Cleanup enhanced systems
            if db_manager:
                await db_manager.close()
            logger.info("🧹 Enhanced systems cleaned up")

# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)