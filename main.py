#!/usr/bin/env python3
"""
Professional Discord Bot - Main Entry Point
Complete rewrite with proper MongoDB and Gemini AI integration
"""

import os
import sys
import asyncio
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands, tasks
from flask import Flask, jsonify
import threading
import time

# Import our systems
from database import db
from gemini_ai import ai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ Environment variables loaded")
except ImportError:
    logger.warning("⚠️ python-dotenv not available")

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

if not DISCORD_TOKEN:
    logger.error("❌ DISCORD_TOKEN not found in environment variables!")
    sys.exit(1)

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True
intents.voice_states = True

# Create bot instance
class ProfessionalBot(commands.Bot):
    """Professional Discord Bot with enhanced features"""
    
    def __init__(self):
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
            owner_ids={1297924079243890780}  # Your Discord user ID
        )
        
        self.start_time = datetime.now(timezone.utc)
        self.commands_used = 0
        self.cogs_loaded = 0
        self.cogs_failed = 0
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        logger.info("🚀 Bot setup hook called")
        
        # Start background tasks
        if not self.cleanup_task.is_running():
            self.cleanup_task.start()
        
        # Load all cogs
        await self.load_all_cogs()
        
        # Sync commands
        await self.sync_commands()
    
    async def load_all_cogs(self):
        """Load all cog extensions"""
        cogs_to_load = [
            'cogs.economy',
            'cogs.moderation', 
            'cogs.leveling',
            'cogs.events',
            'cogs.cookies',
            'cogs.community',
            'cogs.dashboard',
            'cogs.cool_commands',
            'cogs.backup_system',
            'cogs.pet_system',
            'cogs.stock_market',
            'cogs.job_tracking',
            'cogs.settings',
            'cogs.simple_tickets',
            'cogs.security_performance',
            'cogs.enhanced_moderation',
            'cogs.enhanced_minigames'
        ]
        
        logger.info(f"📦 Loading {len(cogs_to_load)} cogs...")
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                self.cogs_loaded += 1
                logger.info(f"✅ Loaded {cog}")
            except Exception as e:
                self.cogs_failed += 1
                logger.error(f"❌ Failed to load {cog}: {e}")
                if DEBUG:
                    traceback.print_exc()
        
        logger.info(f"📦 Cog loading complete: {self.cogs_loaded} loaded, {self.cogs_failed} failed")
    
    async def sync_commands(self):
        """Sync slash commands"""
        try:
            logger.info("🔄 Syncing slash commands...")
            synced = await self.tree.sync()
            logger.info(f"🔄 Synced {len(synced)} slash commands globally")
            
            # Wait for Discord to process
            await asyncio.sleep(2)
            logger.info("✅ Command sync completed - commands should be visible shortly")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"🤖 {self.user} has connected to Discord!")
        logger.info(f"📊 Serving {len(self.guilds)} guilds with {sum(g.member_count for g in self.guilds)} users")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | {BOT_PREFIX}help"
        )
        await self.change_presence(
            status=discord.Status.online,
            activity=activity
        )
        
        logger.info("✅ Bot is ready and operational!")
    
    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.")
            return
        
        logger.error(f"Command error in {ctx.command}: {error}")
        await ctx.send("❌ An error occurred while executing the command.")
    
    async def on_application_command_error(self, interaction, error):
        """Global slash command error handler"""
        if interaction.response.is_done():
            send_method = interaction.followup.send
        else:
            send_method = interaction.response.send_message
        
        if isinstance(error, discord.app_commands.MissingPermissions):
            await send_method("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        logger.error(f"Slash command error in {interaction.command}: {error}")
        await send_method("❌ An error occurred while executing the command.", ephemeral=True)
    
    async def on_message(self, message):
        """Message event handler"""
        if message.author.bot:
            return
        
        # Update user activity
        try:
            user_data = db.get_user_data(message.author.id)
            user_data['stats']['messages_sent'] += 1
            user_data['last_seen'] = datetime.now(timezone.utc)
            db.update_user_data(message.author.id, user_data)
            
            # Add XP for message
            if len(message.content) > 5:  # Only for meaningful messages
                xp_result = db.add_xp(message.author.id, 5)
                
                # Check for level up
                if xp_result.get('leveled_up'):
                    embed = discord.Embed(
                        title="🎉 Level Up!",
                        description=f"{message.author.mention} reached level **{xp_result['new_level']}**!",
                        color=0x00ff00
                    )
                    await message.channel.send(embed=embed, delete_after=10)
        
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
        
        # Process commands
        await self.process_commands(message)
    
    @tasks.loop(hours=1)
    async def cleanup_task(self):
        """Periodic cleanup task"""
        try:
            logger.info("🧹 Running periodic cleanup...")
            
            # Database cleanup
            db.cleanup_expired_data()
            
            # AI conversation cleanup
            ai.cleanup_old_conversations()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
    
    @cleanup_task.before_loop
    async def before_cleanup(self):
        """Wait for bot to be ready before starting cleanup"""
        await self.wait_until_ready()

# Create bot instance
bot = ProfessionalBot()

# Manual sync command
@bot.command(name='sync')
async def sync_commands(ctx):
    """Manually sync slash commands (Owner/Admin only)"""
    # Check permissions
    is_owner = ctx.author.id in bot.owner_ids
    is_admin = ctx.guild and ctx.author.guild_permissions.administrator
    
    if not (is_owner or is_admin):
        await ctx.send("❌ You need to be a bot owner or administrator to use this command!")
        return
    
    try:
        await ctx.send("🔄 Starting command sync...")
        
        # Clear and sync globally
        bot.tree.clear_commands(guild=None)
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} commands globally!")
        
        # Wait for Discord to process
        await asyncio.sleep(2)
        await ctx.send("🔄 Commands are being processed by Discord - they should appear within 1-2 minutes!")
        
        logger.info(f"Manual sync completed by {ctx.author} (ID: {ctx.author.id})")
        await ctx.send("✅ Command sync completed successfully!")
        
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")
        logger.error(f"Manual sync failed: {e}")

# Bot info command
@bot.command(name='info')
async def bot_info(ctx):
    """Display bot information"""
    uptime = datetime.now(timezone.utc) - bot.start_time
    db_stats = db.get_database_stats()
    ai_stats = ai.get_all_conversations()
    
    embed = discord.Embed(
        title="🤖 Bot Information",
        color=0x00d4aa,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="📊 Statistics",
        value=f"""
        **Guilds:** {len(bot.guilds)}
        **Users:** {sum(g.member_count for g in bot.guilds)}
        **Commands Used:** {bot.commands_used}
        **Uptime:** {str(uptime).split('.')[0]}
        """,
        inline=True
    )
    
    embed.add_field(
        name="🗄️ Database",
        value=f"""
        **Storage:** {db_stats.get('storage', 'Unknown')}
        **Status:** {db_stats.get('status', 'Unknown')}
        **Users:** {db_stats.get('users', 0)}
        **Guilds:** {db_stats.get('guilds', 0)}
        """,
        inline=True
    )
    
    embed.add_field(
        name="🤖 AI System",
        value=f"""
        **Status:** {'Available' if ai.is_available() else 'Unavailable'}
        **Conversations:** {ai_stats.get('total_conversations', 0)}
        **Messages:** {ai_stats.get('total_messages', 0)}
        **Active Users:** {ai_stats.get('active_users', 0)}
        """,
        inline=True
    )
    
    embed.add_field(
        name="📦 System",
        value=f"""
        **Cogs Loaded:** {bot.cogs_loaded}
        **Cogs Failed:** {bot.cogs_failed}
        **Commands:** {len(bot.tree.get_commands())}
        **Python:** {sys.version.split()[0]}
        """,
        inline=False
    )
    
    embed.set_footer(text="Professional Discord Bot")
    await ctx.send(embed=embed)

# Flask web server for health checks
app = Flask(__name__)
bot_start_time = time.time()

@app.route('/')
def home():
    """Health check endpoint"""
    uptime = time.time() - bot_start_time
    uptime_hours = uptime // 3600
    uptime_minutes = (uptime % 3600) // 60
    
    return jsonify({
        "status": "online",
        "bot_name": str(bot.user) if bot.user else "Bot Starting",
        "uptime_hours": int(uptime_hours),
        "uptime_minutes": int(uptime_minutes),
        "guilds": len(bot.guilds) if bot.guilds else 0,
        "database": db.get_database_stats(),
        "ai_available": ai.is_available(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/health')
def health():
    """Detailed health check"""
    return jsonify({
        "bot_ready": bot.is_ready(),
        "database_connected": db.connected_to_mongodb,
        "ai_available": ai.is_available(),
        "cogs_loaded": bot.cogs_loaded,
        "cogs_failed": bot.cogs_failed,
        "commands_synced": len(bot.tree.get_commands()),
        "last_check": datetime.now(timezone.utc).isoformat()
    })

def run_flask():
    """Run Flask server in a separate thread"""
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Admin commands for data recovery
@bot.command(name='reconnect_db', hidden=True)
async def reconnect_database(ctx, *, mongodb_uri: str = None):
    """Admin command to reconnect to MongoDB with a new URI"""
    # Check if user is bot owner (you can replace this with your Discord ID)
    if not await bot.is_owner(ctx.author):
        await ctx.send("❌ This command is restricted to bot owners.")
        return
    
    if not mongodb_uri:
        await ctx.send("❌ Please provide a MongoDB URI: `!reconnect_db mongodb+srv://...`")
        return
    
    try:
        # Attempt reconnection
        success = db.reconnect_mongodb(mongodb_uri)
        
        if success:
            embed = discord.Embed(
                title="✅ Database Reconnection Successful",
                color=0x00ff00,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Status", value="Connected to MongoDB", inline=False)
            embed.add_field(name="Users in DB", value=f"{db.users_collection.count_documents({})}", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to reconnect to MongoDB. Check logs for details.")
            
    except Exception as e:
        logger.error(f"Error in reconnect_db command: {e}")
        await ctx.send(f"❌ Error during reconnection: {str(e)}")

@bot.command(name='migrate_data', hidden=True)
async def migrate_data(ctx):
    """Admin command to migrate memory data to MongoDB"""
    if not await bot.is_owner(ctx.author):
        await ctx.send("❌ This command is restricted to bot owners.")
        return
    
    try:
        if not db.connected_to_mongodb:
            await ctx.send("❌ MongoDB is not connected. Use `!reconnect_db` first.")
            return
        
        migrated = db.migrate_memory_to_mongodb()
        
        embed = discord.Embed(
            title="📊 Data Migration Complete",
            color=0x00ff00,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Migrated Users", value=f"{migrated}", inline=True)
        embed.add_field(name="Total Users in DB", value=f"{db.users_collection.count_documents({})}", inline=True)
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in migrate_data command: {e}")
        await ctx.send(f"❌ Error during migration: {str(e)}")

@bot.command(name='db_status', hidden=True)
async def database_status(ctx):
    """Admin command to check database status"""
    if not await bot.is_owner(ctx.author):
        await ctx.send("❌ This command is restricted to bot owners.")
        return
    
    try:
        embed = discord.Embed(
            title="📊 Database Status",
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="Connection", value="✅ MongoDB" if db.connected_to_mongodb else "📝 Memory", inline=True)
        
        if db.connected_to_mongodb and db.users_collection:
            user_count = db.users_collection.count_documents({})
            embed.add_field(name="Users in MongoDB", value=f"{user_count}", inline=True)
        
        memory_users = len(db.memory_users)
        embed.add_field(name="Users in Memory", value=f"{memory_users}", inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in db_status command: {e}")
        await ctx.send(f"❌ Error checking database status: {str(e)}")

# Main execution
async def main():
    """Main async function"""
    try:
        # Start Flask server in background
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info(f"🌐 Flask server started on port {os.getenv('PORT', 10000)}")
        
        # Log system status
        logger.info("🎯 Professional Discord Bot Starting...")
        logger.info(f"📊 Database: {'MongoDB' if db.connected_to_mongodb else 'Memory'}")
        logger.info(f"🤖 AI System: {'Available' if ai.is_available() else 'Unavailable'}")
        
        # Start the bot
        await bot.start(DISCORD_TOKEN)
        
    except KeyboardInterrupt:
        logger.info("👋 Bot shutdown requested")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        traceback.print_exc()
        sys.exit(1)