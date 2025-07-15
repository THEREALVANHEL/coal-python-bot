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

# Deployment trigger: 2025-07-15T12:54:30 - Cookie removal command aliases fix
# Setup logging
logging.basicConfig(level=logging.INFO)

# Load environment variables first
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI")

# 🚨 NUCLEAR CLOUDFLARE PROTECTION - REDUCED DELAYS FOR FASTER STARTUP
CLOUDFLARE_COOLDOWN = int(os.getenv("CLOUDFLARE_COOLDOWN", "1800"))  # 30 minutes default (reduced)
STARTUP_DELAY = int(os.getenv("STARTUP_DELAY", "300"))  # 5 MINUTES default (reduced for faster startup)
MAX_STARTUP_RETRIES = int(os.getenv("MAX_STARTUP_RETRIES", "3"))     # Fewer retries to prevent loops
EMERGENCY_MODE = True  # Force maximum protection
NUCLEAR_MODE = os.getenv("NUCLEAR_MODE", "true").lower() == "true"   # Complete Discord shutdown
MANUAL_ENABLE_REQUIRED = True  # Require manual activation

if not DISCORD_TOKEN:
    print("❌ NO TOKEN FOUND")
    exit(1)

print(f"🚨 NUCLEAR CLOUDFLARE PROTECTION: {CLOUDFLARE_COOLDOWN}s cooldown, {STARTUP_DELAY}s startup delay")
print("🛡️ EMERGENCY MODE: All connections will be heavily rate limited")
if NUCLEAR_MODE:
    print("☢️ NUCLEAR MODE ACTIVE: Discord operations COMPLETELY DISABLED")
    print("🔒 Manual activation required via /nuclear-enable endpoint")
if MANUAL_ENABLE_REQUIRED:
    print("✋ MANUAL ENABLE REQUIRED: Bot will NOT connect to Discord automatically")

# Keep-alive server for Render deployment
app = Flask(__name__)

# Bot start time for uptime tracking
bot_start_time = time.time()
last_cloudflare_block = 0  # Track when we last got blocked

# Global Discord enable flag for nuclear protection
discord_enabled = False

@app.route('/')
def home():
    uptime = time.time() - bot_start_time
    uptime_hours = uptime // 3600
    uptime_minutes = (uptime % 3600) // 60
    
    # Check nuclear mode first
    if NUCLEAR_MODE or MANUAL_ENABLE_REQUIRED:
        if globals().get('discord_enabled', False):
            status_msg = "⚠️ Discord manually enabled (nuclear protection bypassed)"
        else:
            status_msg = "☢️ NUCLEAR MODE: Discord operations DISABLED for maximum protection"
    # Check if we're in startup protection mode
    elif uptime < STARTUP_DELAY:
        remaining = STARTUP_DELAY - uptime
        status_msg = f"🛡️ Starting with Cloudflare protection ({remaining:.0f}s remaining)"
    else:
        status_msg = "✅ Coal Python Bot is online!"
    
    return jsonify({
        "status": status_msg,
        "uptime": f"{int(uptime_hours)}h {int(uptime_minutes)}m",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0 - Nuclear Cloudflare Protection",
        "service": "Discord Bot",
        "port": int(os.environ.get('PORT', 10000)),
        "cloudflare_protection": True,
        "nuclear_mode": NUCLEAR_MODE,
        "discord_enabled": globals().get('discord_enabled', False),
        "manual_enable_required": MANUAL_ENABLE_REQUIRED,
        "startup_delay": STARTUP_DELAY,
        "protection_active": uptime < STARTUP_DELAY or NUCLEAR_MODE or MANUAL_ENABLE_REQUIRED,
        "manual_endpoints": {
            "status": "/nuclear-status",
            "enable": "POST /nuclear-enable",
            "disable": "POST /nuclear-disable"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Check if bot is ready
        if NUCLEAR_MODE or MANUAL_ENABLE_REQUIRED:
            if globals().get('discord_enabled', False):
                bot_status = "manually_enabled" if 'bot' in globals() and bot.is_ready() else "enabling"
            else:
                bot_status = "nuclear_disabled"
        elif 'bot' in globals() and bot.is_ready():
            bot_status = "online"
        else:
            bot_status = "starting"
        
        # Calculate startup progress
        uptime = int(time.time() - bot_start_time)
        startup_progress = min(100, (uptime / STARTUP_DELAY) * 100) if STARTUP_DELAY > 0 else 100
        
        return jsonify({
            "status": "healthy",
            "service": "Coal Python Bot",
            "bot_status": bot_status,
            "startup_progress": f"{startup_progress:.1f}%",
            "uptime_seconds": uptime,
            "timestamp": datetime.now().isoformat(),
            "cloudflare_protection": True,
            "port_exposed": True
        }), 200
    except Exception as e:
        return jsonify({
            "status": "healthy",  # Still healthy even if bot isn't ready
            "service": "Coal Python Bot",
            "bot_status": "starting",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "port_exposed": True
        }), 200  # Return 200 so Render doesn't think service is down

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
            "status": "online",
            "cloudflare_protection": True,
            "last_block_time": last_cloudflare_block
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ready')
def ready_check():
    """Simple ready check for Render port detection"""
    return jsonify({
        "ready": True,
        "service": "Coal Python Bot",
        "port": int(os.environ.get('PORT', 10000)),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/ping')
def ping():
    """Simple ping endpoint for Render"""
    return "PONG", 200

@app.route('/nuclear-status')
def nuclear_status():
    """Check nuclear protection status"""
    return jsonify({
        "nuclear_mode": NUCLEAR_MODE,
        "manual_enable_required": MANUAL_ENABLE_REQUIRED,
        "discord_enabled": globals().get('discord_enabled', False),
        "last_cloudflare_block": last_cloudflare_block,
        "protection_active": should_wait_for_cloudflare(),
        "startup_delay": STARTUP_DELAY,
        "cooldown_period": CLOUDFLARE_COOLDOWN,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/nuclear-enable', methods=['POST'])
def nuclear_enable():
    """Manually enable Discord operations (EXTREME CAUTION)"""
    global MANUAL_ENABLE_REQUIRED, discord_enabled
    
    # Check if we're still in cooldown
    if should_wait_for_cloudflare():
        remaining = CLOUDFLARE_COOLDOWN - (time.time() - last_cloudflare_block)
        return jsonify({
            "error": "Still in Cloudflare cooldown period",
            "remaining_seconds": int(remaining),
            "message": "Wait for cooldown to complete before enabling"
        }), 423  # Locked
    
    MANUAL_ENABLE_REQUIRED = False
    discord_enabled = True
    
    return jsonify({
        "message": "⚠️ Discord operations manually enabled",
        "warning": "This bypasses nuclear protection - use EXTREME caution",
        "discord_enabled": True,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/nuclear-disable', methods=['POST'])
def nuclear_disable():
    """Manually disable Discord operations"""
    global MANUAL_ENABLE_REQUIRED, discord_enabled
    
    MANUAL_ENABLE_REQUIRED = True
    discord_enabled = False
    
    return jsonify({
        "message": "🚨 Discord operations disabled - nuclear protection reactivated",
        "discord_enabled": False,
        "timestamp": datetime.now().isoformat()
    }), 200

def detect_cloudflare_block(error_text):
    """Detect if an error indicates Cloudflare blocking"""
    cloudflare_indicators = [
        "1015", "cloudflare", "ray id", "banned you temporarily",
        "owner of this website", "discord.com", "has banned you"
    ]
    error_lower = str(error_text).lower()
    return any(indicator in error_lower for indicator in cloudflare_indicators)

def mark_cloudflare_block():
    """Mark that we've been blocked by Cloudflare"""
    global last_cloudflare_block
    last_cloudflare_block = time.time()
    print(f"� CLOUDFLARE BLOCK DETECTED at {datetime.now().isoformat()}")
    print(f"🛡️ Entering {CLOUDFLARE_COOLDOWN}s protection mode")
    
    # Save to file for persistence across restarts
    try:
        with open('/tmp/cloudflare_block.txt', 'w') as f:
            f.write(str(last_cloudflare_block))
    except:
        pass

def load_previous_cloudflare_blocks():
    """Load any previous Cloudflare block times"""
    global last_cloudflare_block
    try:
        with open('/tmp/cloudflare_block.txt', 'r') as f:
            last_cloudflare_block = float(f.read().strip())
            if last_cloudflare_block > 0:
                time_since = time.time() - last_cloudflare_block
                print(f"🚨 Previous Cloudflare block detected {time_since:.0f}s ago")
                return True
    except:
        pass
    return False

def should_wait_for_cloudflare():
    """Check if we should wait due to recent Cloudflare blocks"""
    global last_cloudflare_block
    if last_cloudflare_block == 0:
        return False
    
    time_since_block = time.time() - last_cloudflare_block
    if time_since_block < CLOUDFLARE_COOLDOWN:
        remaining = CLOUDFLARE_COOLDOWN - time_since_block
        print(f"🛡️ Cloudflare cooldown: {remaining:.0f}s remaining")
        return True
    return False

async def emergency_delay(reason, duration):
    """Emergency delay with progress reporting"""
    print(f"⏰ EMERGENCY DELAY: {reason} - waiting {duration}s")
    for i in range(0, duration, 30):  # Report every 30 seconds
        remaining = duration - i
        if remaining > 30:
            print(f"⏳ {remaining}s remaining ({reason})")
            await asyncio.sleep(30)
        else:
            await asyncio.sleep(remaining)
            break
    print(f"✅ Emergency delay complete: {reason}")

def run_flask_server():
    """Run Flask server on the port provided by Render"""
    port = int(os.environ.get('PORT', 10000))  # Use Render's PORT or fallback to 10000
    print(f"🌐 Starting web server on port {port}")
    print(f"🌍 Server will be available at http://0.0.0.0:{port}")
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
        raise

def start_web_server():
    """Start the web server in a separate thread"""
    print("🚀 Starting Flask web server...")
    server_thread = Thread(target=run_flask_server, daemon=False)  # Non-daemon to keep service alive
    server_thread.start()
    
    # Give the server a moment to start
    import time
    time.sleep(2)
    print("✅ Web server thread started successfully")
    return server_thread

# Discord Bot Setup with improved rate limiting
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Configure bot with better rate limiting and connection settings
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None,
    case_insensitive=True,
    # Add connection timeout and rate limiting parameters
    heartbeat_timeout=60.0,
    guild_ready_timeout=10.0,
    # Disable automatic sync to prevent rate limits
    auto_sync_commands=False
)

# Add a simple test command to verify bot is working
@bot.tree.command(name="test", description="Simple test command to verify bot functionality")
async def test_command(interaction: discord.Interaction):
    """Test command to verify bot is working"""
    embed = discord.Embed(
        title="✅ Bot Test Successful!",
        description="The bot is online and commands are working!",
        color=0x00ff00
    )
    embed.add_field(
        name="📊 Status", 
        value=f"Loaded Extensions: {len(bot.extensions)}\nCommands in Tree: {len(bot.tree.get_commands())}", 
        inline=False
    )
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_disconnect():
    """Handle bot disconnections gracefully"""
    print("⚠️ Bot disconnected from Discord")

@bot.event
async def on_resumed():
    """Handle bot reconnections"""
    print("🔄 Bot connection resumed")

@bot.event 
async def on_connect():
    """Handle initial connection"""
    print("🔗 Bot connected to Discord")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler to prevent crashes"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    elif isinstance(error, commands.MissingPermissions):
        try:
            await ctx.send("❌ You don't have permission to use this command.")
        except:
            pass
    elif isinstance(error, discord.HTTPException):
        print(f"❌ HTTP error in command: {error}")
        if "rate limit" in str(error).lower():
            print("🚫 Rate limited - adding delay")
            await asyncio.sleep(5)
    else:
        print(f"❌ Unhandled command error: {error}")

@bot.event
async def on_ready():
    print(f"✅ BOT ONLINE: {bot.user.name}")
    print(f"📊 Bot ID: {bot.user.id}")
    print(f"🔗 Invite: https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot%20applications.commands")
    print(f"🌐 Connected to {len(bot.guilds)} guild(s)")
    
    # Load cogs after bot is ready (if not already loaded)
    print("📦 Loading/Reloading cogs after bot ready...")
    await ensure_cogs_loaded()
    
    # Check how many commands are available
    tree_commands = bot.tree.get_commands()
    print(f"🌳 Commands in tree before sync: {len(tree_commands)}")
    if tree_commands:
        command_names = [cmd.name for cmd in tree_commands]
        print(f"📋 Available commands: {', '.join(command_names[:10])}{'...' if len(command_names) > 10 else ''}")
    
    # EMERGENCY MODE: Disable all command syncing
    if EMERGENCY_MODE:
        print("🚨 EMERGENCY MODE: Command sync DISABLED to prevent Cloudflare blocks")
        print("🛡️ All slash commands MUST be synced manually when safe")
        print("💡 Use the /sync command when Cloudflare protection period ends")
        return
    
    # Emergency Cloudflare protection for command sync
    print("⚡ Starting emergency-protected command sync...")
    commands_synced = False
    
    # Check if we should skip sync due to recent Cloudflare blocks
    if should_wait_for_cloudflare():
        print("🛡️ Skipping command sync due to Cloudflare protection mode")
        print("💡 Commands will need to be synced manually later with /sync command")
        return
    
    try:
        # Longer delay to ensure all cogs are loaded and reduce API pressure
        await emergency_delay("Pre-sync protection", 10)
        
        # Check if we have commands to sync
        tree_commands = bot.tree.get_commands()
        if not tree_commands:
            print("⚠️ No commands found in tree, skipping sync")
            print("💡 Commands may need to be loaded manually with /sync command")
        else:
            print(f"🌐 Attempting SINGLE conservative sync with {len(tree_commands)} commands...")
            print("🛡️ Using emergency Cloudflare protection")
            
            # Single attempt with much longer timeout and protection
            synced = await asyncio.wait_for(bot.tree.sync(), timeout=60.0)
            
            if synced is not None:
                commands_synced = True
                print(f"✅ SUCCESS! Synced {len(synced)} slash commands globally")
                
                # Log synced commands (limited to prevent spam)
                command_names = [cmd.name for cmd in synced]
                if len(command_names) <= 10:
                    print(f"📋 Synced commands: {', '.join(command_names)}")
                else:
                    print(f"📋 Synced {len(command_names)} commands: {', '.join(command_names[:10])}...")
                    
                if len(synced) == 0:
                    print("⚠️ WARNING: 0 commands synced")
            else:
                print("❌ Sync returned None")
                
    except asyncio.TimeoutError:
        print("⏰ Command sync timed out after 30 seconds")
        print("💡 Commands may take up to 1 hour to appear due to Discord caching")
        
    except discord.HTTPException as e:
        print(f"❌ HTTP error during sync: {e}")
        
        if detect_cloudflare_block(str(e)):
            mark_cloudflare_block()
            print("🚫 EMERGENCY: Cloudflare blocking detected during command sync!")
            print("💡 Bot will operate in minimal mode to prevent further blocks")
            print(f"�️ All Discord operations suspended for {CLOUDFLARE_COOLDOWN}s")
            
        elif "rate limited" in str(e).lower() or "429" in str(e):
            print("🚫 Rate limited by Discord during command sync")
            print("💡 Bot will continue without syncing, use /sync command later")
        
    except discord.Forbidden as e:
        print(f"❌ Permission error during sync: {e}")
        print("🔧 Check bot permissions: applications.commands scope required")
        
    except Exception as e:
        print(f"❌ Unexpected error during sync: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
    
    if commands_synced:
        print("🎉 Command sync completed successfully!")
    else:
        print("⚠️ All sync attempts failed, but bot will continue")
        print("💡 Commands may take up to 1 hour to appear due to Discord caching")
        print("🔧 Try using the /sync command (if visible) to manually sync")
    
    # Check database connectivity and stats with timeout
    print("💾 Starting database connectivity check...")
    try:
        # Add timeout to database operations
        async def check_database():
            try:
                import database as db
                
                # Quick health check first
                health_check = db.quick_db_health_check()
                if health_check["success"]:
                    print(f"✅ {health_check['message']}")
                    
                    # Get basic stats with timeout protection
                    try:
                        stats = db.get_database_stats()
                        if stats["success"]:
                            estimated = " (estimated)" if stats.get('is_estimated') else ""
                            print(f"📊 Database stats - {stats['total_users']} users, {stats['total_xp']:,} total XP{estimated}, {stats['total_cookies']:,} total cookies{estimated}")
                        else:
                            print(f"⚠️ Database stats warning: {stats['message']}")
                    except Exception as e:
                        print(f"⚠️ Could not get database stats: {e}")
                        
                else:
                    print(f"❌ Database health check failed: {health_check['error']}")
                    print("🔄 Bot will continue without database features")
                    
            except Exception as e:
                print(f"❌ Database import/check failed: {e}")
                print("🔄 Bot will continue in limited mode")
        
        # Run database check with timeout
        await asyncio.wait_for(check_database(), timeout=30)
        print("✅ Database check completed")
        
    except asyncio.TimeoutError:
        print("⏰ Database check timed out - continuing without database")
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        print("🔄 Bot will continue in limited mode")
    
    print("🎉 Bot initialization complete! Ready to serve users.")

# Load cogs
async def load_cogs():
    """Load all cogs with individual error handling"""
    cogs = [
        'cogs.leveling',      # Contains profile command - critical
        'cogs.cookies', 
        'cogs.economy',
        'cogs.events',
        'cogs.community',
        'cogs.moderation',
        'cogs.enhanced_moderation',  # Simple logging system
        'cogs.settings',
        'cogs.tickets',
        'cogs.job_tracking'   # Job time tracking with auto-demotion
    ]
    
    loaded_count = 0
    failed_cogs = []
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"[Main] ✅ Loaded {cog}")
            loaded_count += 1
            
            # Special check for leveling cog (contains profile command)
            if cog == 'cogs.leveling':
                print(f"[Main] 🎯 Critical cog 'leveling' loaded - profile command should be available")
                
        except ImportError as e:
            print(f"[Main] ❌ Import error loading {cog}: {e}")
            print(f"[Main] 💡 This usually means missing dependencies or syntax errors")
            failed_cogs.append(cog)
        except Exception as e:
            print(f"[Main] ❌ Failed to load {cog}: {e}")
            print(f"[Main] 🔍 Error type: {type(e).__name__}")
            print(f"[Main] 📝 Error details: {str(e)}")
            failed_cogs.append(cog)
            # Continue loading other cogs instead of failing completely
            
    print(f"[Main] 📊 Cog loading complete: {loaded_count}/{len(cogs)} successful")
    if failed_cogs:
        print(f"[Main] ⚠️ Failed cogs: {', '.join(failed_cogs)}")
        # Special warning for critical cogs
        if 'cogs.leveling' in failed_cogs:
            print(f"[Main] 🚨 CRITICAL: leveling cog failed to load - profile command will not work!")
    
    return loaded_count > 0  # Return True if at least one cog loaded

async def ensure_cogs_loaded():
    """Ensure cogs are loaded, reload if necessary"""
    print("[Ensure] 🔍 Checking loaded cogs...")
    
    # Check what's currently loaded
    loaded_cogs = list(bot.extensions.keys())
    print(f"[Ensure] 📋 Currently loaded: {loaded_cogs}")
    
    target_cogs = [
        'cogs.leveling',
        'cogs.cookies', 
        'cogs.economy',
        'cogs.events',
        'cogs.community',
        'cogs.moderation',
        'cogs.enhanced_moderation',
        'cogs.settings',
        'cogs.tickets',
        'cogs.job_tracking'
    ]
    
    missing_cogs = [cog for cog in target_cogs if cog not in loaded_cogs]
    print(f"[Ensure] 🚫 Missing cogs: {missing_cogs}")
    
    # Load missing cogs
    newly_loaded = 0
    for cog in missing_cogs:
        try:
            print(f"[Ensure] 🔄 Loading {cog}...")
            await bot.load_extension(cog)
            print(f"[Ensure] ✅ Successfully loaded {cog}")
            newly_loaded += 1
        except Exception as e:
            print(f"[Ensure] ❌ Failed to load {cog}: {e}")
            print(f"[Ensure] 🔍 Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
    
    # Final status
    final_loaded = list(bot.extensions.keys())
    print(f"[Ensure] 📊 Final status: {len(final_loaded)}/{len(target_cogs)} cogs loaded")
    print(f"[Ensure] ✅ Loaded cogs: {final_loaded}")
    
    # Check commands after loading
    commands_count = len(bot.tree.get_commands())
    print(f"[Ensure] 🎯 Commands available: {commands_count}")
    
    return len(final_loaded) > 0

async def startup_maintenance():
    """Perform startup maintenance and optimization with timeouts"""
    try:
        print("[Main] 🔧 Performing startup maintenance...")
        
        import database as db
        
        # Add timeout wrapper for database operations
        async def run_with_timeout(func, timeout_seconds=30):
            try:
                # Run in executor to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                return await asyncio.wait_for(
                    loop.run_in_executor(None, func), 
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                print(f"[Main] ⏰ Operation timed out after {timeout_seconds}s")
                return {"success": False, "error": "timeout"}
            except Exception as e:
                print(f"[Main] ❌ Operation failed: {e}")
                return {"success": False, "error": str(e)}
        
        # Remove deprecated warning system with timeout
        print("[Main] 🗑️ Removing deprecated warning system...")
        result = await run_with_timeout(db.remove_deprecated_warning_system, 15)
        if result.get('success'):
            print(f"[Main] ✅ Removed warning system from {result.get('users_updated', 0)} users")
        else:
            print(f"[Main] ⚠️ Warning system cleanup failed: {result.get('error', 'unknown')}")
        
        # Optimize database with timeout
        print("[Main] 🎯 Optimizing database...")
        optimization = await run_with_timeout(db.optimize_database_live, 20)
        if optimization.get('success'):
            indexes = optimization.get('indexes_created', [])
            print(f"[Main] ✅ Database optimized with {len(indexes)} indexes")
        else:
            print(f"[Main] ⚠️ Database optimization failed: {optimization.get('error', 'unknown')}")
        
        # Skip auto-sync during startup to prevent hanging
        # This will be done in background after bot is online
        print("[Main] ⏭️ Skipping user auto-sync during startup (will run in background)")
        
        print(f"[Main] ✅ Startup maintenance complete (with graceful timeouts)")
        
    except Exception as e:
        print(f"[Main] ❌ Error in startup maintenance: {e}")
        print(f"[Main] 🔄 Continuing with bot startup despite maintenance errors...")

async def background_user_sync():
    """Run user sync in background after bot is online"""
    try:
        # Wait for bot to be fully ready
        await asyncio.sleep(60)  # Wait 1 minute after startup
        
        print("[Background] 🔄 Starting background user sync...")
        import database as db
        
        users_synced = 0
        try:
            # Limit to 50 users to prevent overload
            all_users = db.get_all_users_for_maintenance()[:50]
            for user_data in all_users:
                db.auto_sync_user_data(user_data['user_id'])
                users_synced += 1
                
                # Add small delay to prevent overwhelming the database
                if users_synced % 10 == 0:
                    await asyncio.sleep(1)
                    
        except Exception as e:
            print(f"[Background] ⚠️ Error in user sync: {e}")
        
        print(f"[Background] ✅ Background sync complete. Synced {users_synced} users.")
        
    except Exception as e:
        print(f"[Background] ❌ Background sync failed: {e}")

async def main():
    """Main function to run the bot with NUCLEAR Cloudflare protection"""
    
    # Use global discord_enabled variable
    global discord_enabled
    
    # 🌐 START WEB SERVER IMMEDIATELY for Render port detection
    print("🌐 Starting web server IMMEDIATELY for Render...")
    web_server_thread = start_web_server()
    print("✅ Web server running - Render should detect the port now")
    
    # ☢️ NUCLEAR MODE CHECK - COMPLETELY DISABLE DISCORD
    if NUCLEAR_MODE or MANUAL_ENABLE_REQUIRED:
        print("☢️ NUCLEAR PROTECTION ACTIVE: Discord operations DISABLED")
        print("🌐 Web server will continue running for health checks")
        print("🔒 To enable Discord: POST to /nuclear-enable (EXTREME CAUTION)")
        print("� Check status: GET /nuclear-status")
        
        # Run indefinitely serving only web requests
        while True:
            # Check if Discord has been manually enabled
            if discord_enabled:
                print("✅ Discord manually enabled - proceeding with startup")
                break
            await asyncio.sleep(10)  # Check every 10 seconds for manual enable
            print(f"☢️ Nuclear mode active - Discord disabled (check /nuclear-status)")
    
    # �� CHECK FOR PREVIOUS CLOUDFLARE BLOCKS (only if Discord enabled)
    print("🔍 Checking for previous Cloudflare blocks...")
    if load_previous_cloudflare_blocks():
        if should_wait_for_cloudflare():
            remaining = CLOUDFLARE_COOLDOWN - (time.time() - last_cloudflare_block)
            if remaining > 0:
                print(f"🚨 STILL IN CLOUDFLARE COOLDOWN: {remaining:.0f}s remaining")
                await emergency_delay("Previous Cloudflare block cooldown", int(remaining))
    
    # 🚨 MANDATORY EMERGENCY PROTECTION - NO EXCEPTIONS (only if Discord enabled)
    print("🚨 EMERGENCY PROTECTION ACTIVATED")
    print(f"⏰ MANDATORY {STARTUP_DELAY}s delay before Discord connection")
    print("🌐 NOTE: Web server is already running for Render port detection")
    await emergency_delay("MANDATORY Discord connection protection", STARTUP_DELAY)
    
    retry_count = 0
    max_retries = MAX_STARTUP_RETRIES
    
    while retry_count < max_retries:
        try:
            print(f"🚀 Starting Coal Python Bot... (Attempt {retry_count + 1}/{max_retries})")
            
            # Web server is already running from main() startup
            
            # Check for Cloudflare cooldown AFTER web server is running
            if should_wait_for_cloudflare():
                remaining = CLOUDFLARE_COOLDOWN - (time.time() - last_cloudflare_block)
                await emergency_delay("Cloudflare cooldown before Discord connection", int(remaining))
            
            # Load all cogs with timeout
            print("📦 Loading cogs during startup...")
            try:
                cogs_loaded = await asyncio.wait_for(load_cogs(), timeout=60)
                if cogs_loaded:
                    print("✅ Cogs loaded successfully during startup")
                    # Show what was loaded
                    loaded_extensions = list(bot.extensions.keys())
                    print(f"📋 Loaded extensions: {loaded_extensions}")
                else:
                    print("⚠️ No cogs loaded successfully during startup")
                    print("🔄 Will attempt to load again after bot connects")
            except asyncio.TimeoutError:
                print("⏰ Cog loading timed out during startup")
                print("🔄 Will attempt to load again after bot connects")
            except Exception as e:
                print(f"❌ Error during startup cog loading: {e}")
                print(f"🔍 Error type: {type(e).__name__}")
                print("🔄 Continuing with bot startup, will retry after connection")
            
            # Perform startup maintenance with timeout
            print("🔧 Running startup maintenance...")
            try:
                await asyncio.wait_for(startup_maintenance(), timeout=60)
            except asyncio.TimeoutError:
                print("⏰ Startup maintenance timed out, continuing with bot startup...")
            except Exception as e:
                print(f"❌ Startup maintenance failed: {e}")
            
            print("🎮 Starting Discord bot with MAXIMUM protection...")
            print("🛡️ Using extended timeout for safe connection")
            
            # Start the bot with extended timeout protection
            await asyncio.wait_for(bot.start(DISCORD_TOKEN), timeout=600)  # 10 minute timeout (doubled)
            
            # If we get here, the bot started successfully
            break
            
        except asyncio.TimeoutError:
            print(f"⏰ Bot startup timed out on attempt {retry_count + 1} (this may indicate Cloudflare blocking)")
            print("🛡️ Treating timeout as potential Cloudflare issue")
            mark_cloudflare_block()  # Treat timeouts as potential blocks
            retry_count += 1
            if retry_count < max_retries:
                wait_time = min(CLOUDFLARE_COOLDOWN * retry_count, 1800)  # Use Cloudflare delays for timeouts
                await emergency_delay(f"Timeout protection (attempt {retry_count})", wait_time)
            
        except discord.HTTPException as e:
            print(f"[Main] ❌ Discord HTTP error on attempt {retry_count + 1}: {e}")
            
            if detect_cloudflare_block(str(e)):
                mark_cloudflare_block()
                print("� CRITICAL: Cloudflare blocking detected!")
                print("�️ Implementing MAXIMUM emergency protection")
                retry_count += 1
                if retry_count < max_retries:
                    # EXTREME delays for Cloudflare blocks
                    wait_time = min(CLOUDFLARE_COOLDOWN * retry_count * 2, 3600)  # Max 1 hour, double cooldown
                    await emergency_delay(f"MAXIMUM Cloudflare protection (attempt {retry_count})", wait_time)
                
            elif "rate limit" in str(e).lower() or "429" in str(e):
                print("🚫 Rate limited by Discord API - treating as Cloudflare risk")
                mark_cloudflare_block()  # Treat rate limits as potential Cloudflare triggers
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 600  # 10 minutes for rate limits (doubled)
                    await emergency_delay(f"Rate limit protection (attempt {retry_count})", wait_time)
            else:
                print("❌ Unknown HTTP error, not retrying")
                break
                
        except discord.LoginFailure as e:
            print(f"[Main] ❌ Login failed: {e}")
            print("🔑 Check your DISCORD_TOKEN environment variable")
            break  # Don't retry login failures
            
        except Exception as e:
            print(f"[Main] ❌ Unexpected error on attempt {retry_count + 1}: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 30
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)
    
    if retry_count >= max_retries:
        print("❌ All retry attempts exhausted. Bot failed to start.")
        print("💡 Check logs above for specific errors and try manual restart.")
    else:
        print("✅ Bot startup completed successfully!")

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
