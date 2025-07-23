import discord
from discord.ext import commands
import os
import asyncio

# Simple force sync - add this to your bot or run separately
async def force_sync_commands():
    """Force sync all Discord commands"""
    
    # Bot setup with minimal requirements
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'🤖 Connected as {bot.user}')
        
        try:
            # Clear existing commands
            bot.tree.clear_commands(guild=None)
            print("🧹 Cleared existing commands")
            
            # Force sync
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} commands globally")
            
            # Also try guild-specific sync for faster updates
            for guild in bot.guilds:
                try:
                    guild_synced = await bot.tree.sync(guild=guild)
                    print(f"✅ Synced {len(guild_synced)} commands to {guild.name}")
                except Exception as e:
                    print(f"❌ Failed to sync to {guild.name}: {e}")
            
            print("🎉 Command sync completed!")
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
        
        await bot.close()
    
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ No DISCORD_TOKEN found in environment variables")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")

if __name__ == "__main__":
    asyncio.run(force_sync_commands())