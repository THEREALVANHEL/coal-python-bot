#!/usr/bin/env python3

import asyncio
import os
import sys
import discord
from discord.ext import commands
import traceback

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Get token from environment
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ Error: DISCORD_TOKEN not found in environment variables!")
    print("💡 Make sure you have a .env file with DISCORD_TOKEN=your_token_here")
    exit(1)

# Bot setup with proper intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"🤖 Successfully logged in as {bot.user}")
    print("=" * 80)
    print("🔧 COMPREHENSIVE COMMAND SYNC & FIX UTILITY")
    print("=" * 80)
    
    try:
        # First, clear any existing commands to start fresh
        print("🧹 Step 1: Clearing existing commands...")
        bot.tree.clear_commands(guild=None)
        print("✅ Cleared global commands")
        
        # Load all cogs with detailed error reporting
        cog_files = [
            'cogs.leveling',      # Contains the profile command
            'cogs.moderation', 
            'cogs.community',
            'cogs.economy',
            'cogs.settings',
            'cogs.tickets',
            'cogs.events',
            'cogs.cookies',
        ]
        
        print("\n📦 Step 2: Loading cogs with detailed error checking...")
        loaded_cogs = []
        failed_cogs = []
        
        for cog in cog_files:
            try:
                print(f"   Loading {cog}...")
                await bot.load_extension(cog)
                loaded_cogs.append(cog)
                print(f"   ✅ Successfully loaded {cog}")
            except Exception as e:
                failed_cogs.append((cog, str(e)))
                print(f"   ❌ Failed to load {cog}: {e}")
                print(f"   📝 Error details: {traceback.format_exc()}")
        
        print(f"\n📊 Cog Loading Results:")
        print(f"   ✅ Successfully loaded: {len(loaded_cogs)}/{len(cog_files)} cogs")
        print(f"   ❌ Failed to load: {len(failed_cogs)} cogs")
        
        if loaded_cogs:
            print(f"   📋 Loaded cogs: {', '.join(loaded_cogs)}")
        
        if failed_cogs:
            print(f"   🚫 Failed cogs:")
            for cog, error in failed_cogs:
                print(f"      - {cog}: {error}")
        
        # Check available commands before sync
        print(f"\n🔍 Step 3: Checking available commands...")
        commands_before = bot.tree.get_commands()
        print(f"   📊 Commands available for sync: {len(commands_before)}")
        
        if commands_before:
            print(f"   📋 Available commands:")
            for cmd in commands_before:
                print(f"      - /{cmd.name}: {cmd.description}")
        else:
            print("   ⚠️ No commands found! This indicates cogs didn't load properly.")
        
        # Perform comprehensive sync
        print(f"\n🔄 Step 4: Synchronizing commands...")
        sync_attempts = 0
        max_attempts = 3
        sync_successful = False
        
        while sync_attempts < max_attempts and not sync_successful:
            sync_attempts += 1
            print(f"   🔄 Sync attempt {sync_attempts}/{max_attempts}")
            
            try:
                # Add a small delay between attempts
                if sync_attempts > 1:
                    print("   ⏳ Waiting 5 seconds before retry...")
                    await asyncio.sleep(5)
                
                # Perform the sync
                synced = await bot.tree.sync()
                
                if synced:
                    sync_successful = True
                    print(f"   ✅ Successfully synced {len(synced)} commands globally!")
                    
                    print(f"   📋 Synced commands:")
                    for i, cmd in enumerate(synced, 1):
                        print(f"      {i:2d}. /{cmd.name} - {cmd.description}")
                    
                    # Special check for profile command
                    profile_found = any(cmd.name == 'profile' for cmd in synced)
                    if profile_found:
                        print(f"   ✅ Profile command successfully synced!")
                    else:
                        print(f"   ⚠️ Profile command not found in sync results!")
                        
                else:
                    print(f"   ❌ Sync returned None on attempt {sync_attempts}")
                    
            except discord.HTTPException as e:
                print(f"   ❌ HTTP error on attempt {sync_attempts}: {e}")
                if "rate limited" in str(e).lower():
                    print("   ⏰ Rate limited, waiting longer...")
                    await asyncio.sleep(15)
                    
            except discord.Forbidden as e:
                print(f"   ❌ Permission error on attempt {sync_attempts}: {e}")
                print("   🔧 Bot needs 'applications.commands' scope!")
                break
                
            except Exception as e:
                print(f"   ❌ Unexpected error on attempt {sync_attempts}: {e}")
                print(f"   🔍 Error type: {type(e).__name__}")
                print(f"   📝 Error details: {traceback.format_exc()}")
        
        # Final verification
        print(f"\n🔍 Step 5: Final verification...")
        final_commands = bot.tree.get_commands()
        print(f"   📊 Commands in tree after sync: {len(final_commands)}")
        
        # Test database connectivity if available
        print(f"\n💾 Step 6: Testing database connectivity...")
        try:
            import database as db
            health_check = db.quick_db_health_check()
            if health_check.get("success"):
                print(f"   ✅ Database connection: {health_check['message']}")
            else:
                print(f"   ❌ Database connection failed: {health_check.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"   ⚠️ Database test failed: {e}")
        
        # Summary
        print("\n" + "=" * 80)
        if sync_successful:
            print("🎉 SYNC COMPLETED SUCCESSFULLY!")
            print(f"✅ {len(loaded_cogs)} cogs loaded")
            print(f"✅ {len(synced) if 'synced' in locals() else 0} commands synced")
            print("✅ Commands should now be available in Discord")
            
            if len(failed_cogs) > 0:
                print(f"⚠️ {len(failed_cogs)} cogs failed to load - check errors above")
                
        else:
            print("❌ SYNC FAILED!")
            print("🔧 Possible solutions:")
            print("   1. Check bot permissions (needs applications.commands scope)")
            print("   2. Verify DISCORD_TOKEN is correct")
            print("   3. Check cog loading errors above")
            print("   4. Try running the sync script again in a few minutes")
            
        print("=" * 80)
        print("💡 If commands don't appear immediately:")
        print("   - Wait 1-2 minutes for Discord to update")
        print("   - Try restarting Discord client")
        print("   - Check bot permissions in server settings")
        
    except Exception as e:
        print(f"❌ Critical error during sync: {e}")
        print(f"📝 Full traceback: {traceback.format_exc()}")
    finally:
        print("\n🔚 Sync operation completed. Closing bot...")
        await bot.close()

if __name__ == "__main__":
    print("🚀 Starting Discord Bot Command Sync...")
    print("🔧 This script will fix CommandNotFound errors")
    
    try:
        asyncio.run(bot.start(TOKEN))
    except KeyboardInterrupt:
        print("\n🛑 Sync interrupted by user")
    except discord.LoginFailure:
        print("❌ Login failed - check your DISCORD_TOKEN")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print(f"📝 Full traceback: {traceback.format_exc()}")