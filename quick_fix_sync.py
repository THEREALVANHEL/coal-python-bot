"""
Quick Fix Sync Script - Run this on your server to sync commands immediately
"""

import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def emergency_sync():
    """Emergency sync function"""
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    # Create a minimal bot just for syncing
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"🤖 Connected as {client.user}")
        
        # Create command tree
        tree = discord.app_commands.CommandTree(client)
        
        # Clear old commands
        print("🗑️ Clearing old commands...")
        tree.clear_commands(guild=None)
        await asyncio.sleep(2)
        
        # Force sync
        print("🔄 Force syncing commands...")
        try:
            synced = await tree.sync()
            print(f"✅ Synced {len(synced)} commands!")
            
            if len(synced) == 0:
                print("⚠️ 0 commands synced - commands may be cached")
                print("💡 Try again in a few minutes")
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            
        await client.close()
    
    # Start the client
    await client.start(TOKEN)

if __name__ == "__main__":
    print("🚨 EMERGENCY SYNC UTILITY")
    print("=" * 30)
    try:
        asyncio.run(emergency_sync())
        print("✅ Sync operation completed")
    except Exception as e:
        print(f"❌ Error: {e}")