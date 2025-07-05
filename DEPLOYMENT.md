# 🚀 Deployment Guide for Render

## Quick Deploy to Render

1. **Fork this repository** to your GitHub account

2. **Connect to Render:**
   - Go to [render.com](https://render.com)
   - Create a new Web Service
   - Connect your GitHub repository

3. **Configure Environment Variables:**
   ```
   DISCORD_TOKEN=your_bot_token_here
   MONGODB_URI=your_mongodb_connection_string
   GEMINI_API_KEY=your_gemini_key_here (optional)
   ```

4. **Deploy Settings:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Environment:** Python 3.11.6

## ✅ Features for Render

- **Health Check Endpoint:** `/health`
- **Bot Statistics:** `/stats`  
- **Auto Port Detection:** Uses Render's PORT environment variable
- **Uptime Monitoring:** Built-in uptime tracking
- **Proper Error Handling:** Graceful startup and shutdown

## 🔧 Health Check Endpoints

- **`/`** - Bot status and uptime information
- **`/health`** - Health check for Render monitoring
- **`/stats`** - Discord bot statistics (guilds, users, latency)

## 🎯 Deployment Checklist

- ✅ Flask web server for port binding
- ✅ Environment variable configuration
- ✅ Health check endpoints
- ✅ Proper threading for bot + web server
- ✅ Auto-startup maintenance
- ✅ Graceful error handling
- ✅ Render.yaml configuration
- ✅ Procfile for deployment

## 🔍 Troubleshooting

**"No open ports detected":** Fixed! The bot now properly binds to Render's PORT.

**Bot not responding:** Check the `/health` endpoint to verify bot status.

**Environment variables:** Make sure all required env vars are set in Render dashboard.

## 📊 Monitoring

Visit your Render service URL to see:
- Real-time bot status
- Uptime information  
- Connection statistics
- Health monitoring data

Your bot is now ready for professional deployment! 🎉