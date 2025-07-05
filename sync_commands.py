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

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    
    try:
        # Sync commands to specific guild (faster)
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f'Synced {len(synced)} commands to guild {GUILD_ID}')
        
        # Optionally sync globally (takes up to 1 hour)
        # synced_global = await bot.tree.sync()
        # print(f'Synced {len(synced_global)} commands globally')
        
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    
    await bot.close()

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
