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
    print(f"🌐 Connected to {len(bot.guilds)} guild(s)")
    
    # Sync slash commands
    print("⚡ Starting command sync...")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands successfully")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
        print("🔄 Bot will continue without command sync")
    
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
        'cogs.leveling',
        'cogs.cookies', 
        'cogs.economy',
        'cogs.events',
        'cogs.community',
        'cogs.moderation',
        'cogs.settings',
        'cogs.tickets'
    ]
    
    loaded_count = 0
    failed_cogs = []
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"[Main] ✅ Loaded {cog}")
            loaded_count += 1
        except Exception as e:
            print(f"[Main] ❌ Failed to load {cog}: {e}")
            failed_cogs.append(cog)
            # Continue loading other cogs instead of failing completely
            
    print(f"[Main] 📊 Cog loading complete: {loaded_count}/{len(cogs)} successful")
    if failed_cogs:
        print(f"[Main] ⚠️ Failed cogs: {', '.join(failed_cogs)}")
    
    return loaded_count > 0  # Return True if at least one cog loaded

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
    """Main function to run the bot"""
    try:
        print("🚀 Starting Coal Python Bot...")
        
        # Start the web server first
        start_web_server()
        
        # Load all cogs with timeout
        print("📦 Loading cogs...")
        try:
            cogs_loaded = await asyncio.wait_for(load_cogs(), timeout=45)
            if cogs_loaded:
                print("✅ Cogs loaded successfully (at least partially)")
            else:
                print("⚠️ No cogs loaded successfully - bot will have limited functionality")
        except asyncio.TimeoutError:
            print("⏰ Cog loading timed out, continuing with bot startup...")
        except Exception as e:
            print(f"❌ Error during cog loading: {e}")
            print("🔄 Continuing with bot startup despite cog errors...")
        
        # Perform startup maintenance with timeout
        print("🔧 Running startup maintenance...")
        try:
            await asyncio.wait_for(startup_maintenance(), timeout=60)
        except asyncio.TimeoutError:
            print("⏰ Startup maintenance timed out, continuing with bot startup...")
        except Exception as e:
            print(f"❌ Startup maintenance failed: {e}")
        
        print("🎮 Starting Discord bot...")
        
        # Start background user sync task
        asyncio.create_task(background_user_sync())
        
        # Start the bot
        await bot.start(DISCORD_TOKEN)
        
    except Exception as e:
        print(f"[Main] ❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()

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
