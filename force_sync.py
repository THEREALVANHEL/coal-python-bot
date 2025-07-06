#!/usr/bin/env python3
"""
Force Command Sync Script
This script can be run locally to force sync all Discord commands.
Run this if the bot is not showing the new commands after deployment.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ DISCORD_TOKEN not found in environment variables!")
    print("Make sure you have a .env file with your bot token.")
    sys.exit(1)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'📊 Connected to {len(bot.guilds)} guilds')
    
    # Load all cogs to get their commands
    print('\n📦 Loading cogs to get all commands...')
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
    
    loaded_cogs = 0
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'  ✅ Loaded {cog}')
            loaded_cogs += 1
        except Exception as e:
            print(f'  ❌ Failed to load {cog}: {e}')
    
    print(f'\n📊 Successfully loaded {loaded_cogs}/{len(cogs)} cogs')
    
    # Get all commands before sync
    tree_commands = [cmd.name for cmd in bot.tree.get_commands()]
    print(f'🌳 Commands in tree: {len(tree_commands)} total')
    print(f'   Commands: {", ".join(tree_commands)}')
    
    if len(tree_commands) == 0:
        print('⚠️ WARNING: No commands found in tree!')
        print('   This might indicate a problem with cog loading.')
        await bot.close()
        return
    
    # Clear existing commands
    print('\n🧹 Clearing existing commands...')
    bot.tree.clear_commands(guild=None)
    await asyncio.sleep(2)
    
    try:
        # Sync globally first
        print('🌐 Syncing commands globally...')
        synced_global = await bot.tree.sync()
        print(f'✅ Synced {len(synced_global)} commands globally')
        
        # Also sync to each guild for immediate availability
        print('\n🏠 Syncing to all guilds for immediate availability...')
        for guild in bot.guilds:
            try:
                guild_obj = discord.Object(id=guild.id)
                synced_guild = await bot.tree.sync(guild=guild_obj)
                print(f'  ✅ {guild.name}: {len(synced_guild)} commands')
            except Exception as e:
                print(f'  ❌ {guild.name}: {e}')
        
        # Show results
        global_commands = [cmd.name for cmd in synced_global]
        print(f'\n🎉 Sync completed successfully!')
        print(f'📋 Global commands synced: {", ".join(global_commands)}')
        print(f'\n⏰ Availability:')
        print(f'   • Guild commands: Available immediately')
        print(f'   • Global commands: May take up to 1 hour')
        
        # Check for new commands
        new_commands = ['addxp', 'sync', 'formticket', 'giveticketroleperms']
        found_new = [cmd for cmd in new_commands if cmd in global_commands]
        if found_new:
            print(f'\n✨ New commands detected: {", ".join(found_new)}')
        
        print(f'\n✅ All done! You can now close this script.')
        
    except discord.HTTPException as e:
        print(f'❌ HTTP error during sync: {e}')
        if "rate limited" in str(e).lower():
            print('⏰ You are being rate limited. Please wait a few minutes and try again.')
    except Exception as e:
        print(f'❌ Unexpected error during sync: {e}')
    
    await bot.close()

async def main():
    print("🚀 Discord Bot Command Sync Tool")
    print("=" * 50)
    print("This tool will force sync all Discord slash commands.")
    print("Use this if your bot is not showing the latest commands.\n")
    
    try:
        async with bot:
            await bot.start(TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid bot token! Please check your DISCORD_TOKEN environment variable.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Sync cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")