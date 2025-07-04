print("=== BOT STARTING ===")

import os
print("✅ OS imported")

try:
    import discord
    print("✅ Discord imported")
except Exception as e:
    print(f"❌ Discord import error: {e}")

try:
    from flask import Flask
    print("✅ Flask imported")
except Exception as e:
    print(f"❌ Flask import error: {e}")

from threading import Thread

# Keep-alive
app = Flask('')

@app.route('/')
def home():
    return "Bot Status: Starting..."

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

print("🌐 Starting Flask...")
keep_alive()

# Check token
token = os.getenv("DISCORD_TOKEN")
print(f"🔑 Token found: {bool(token)}")
if token:
    print(f"🔑 Token starts with: {token[:15]}...")
else:
    print("❌ NO TOKEN FOUND!")

print("🤖 Creating Discord client...")
try:
    intents = discord.Intents.default()
    bot = discord.Client(intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ BOT ONLINE: {bot.user}")
    
    print("🚀 Starting bot connection...")
    bot.run(token)
    
except Exception as e:
    print(f"❌ BOT ERROR: {e}")
