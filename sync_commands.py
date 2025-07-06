import asyncio
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1370009417726169250

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} guilds')
    
    # Load all cogs first
    print('Loading cogs...')
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
            print(f'✅ Loaded {cog}')
        except Exception as e:
            print(f'❌ Failed to load {cog}: {e}')
    
    # Clear existing commands first
    print('Clearing existing commands...')
    bot.tree.clear_commands(guild=None)
    await asyncio.sleep(2)
    
    try:
        # Sync commands to specific guild first (faster)
        print('Syncing commands to guild...')
        guild = discord.Object(id=GUILD_ID)
        synced_guild = await bot.tree.sync(guild=guild)
        print(f'✅ Synced {len(synced_guild)} commands to guild {GUILD_ID}')
        
        # List synced commands
        guild_commands = [cmd.name for cmd in synced_guild]
        print(f'Guild commands: {", ".join(guild_commands)}')
        
        # Sync globally (takes up to 1 hour to appear)
        print('Syncing commands globally...')
        synced_global = await bot.tree.sync()
        print(f'✅ Synced {len(synced_global)} commands globally')
        
        # List all commands in tree
        tree_commands = [cmd.name for cmd in bot.tree.get_commands()]
        print(f'All commands in tree: {", ".join(tree_commands)}')
        
        print('🎉 Command sync completed successfully!')
        
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')
    
    await bot.close()

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    print("🔄 Starting comprehensive command sync...")
    print("This will sync all commands including the new ones you added.")
    asyncio.run(main())
