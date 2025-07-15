# Coal Python Bot

A comprehensive Discord bot with leveling, economy, moderation, and community features.

## Quick Start
1. Set environment variables: `DISCORD_TOKEN`, `MONGODB_URI`
2. Deploy to Render or run locally with `python main.py`
3. Bot includes nuclear Cloudflare protection - use `/nuclear-enable` if needed

## Features
- **Leveling System**: XP tracking with role rewards
- **Economy**: Coins, cookies, work system, shop
- **Moderation**: Kick, ban, timeout, warnings
- **Community**: Server info, member count, polls
- **Tickets**: Support ticket system with role management
- **Events**: Auto role assignment, level up notifications

## Commands
51+ slash commands across all categories - see COMMANDS.md for full list.

## Nuclear Protection
The bot includes Cloudflare protection with manual override endpoints:
- `/nuclear-status` - Check protection status
- `/nuclear-enable` - Enable Discord operations (POST)
- `/nuclear-disable` - Disable Discord operations (POST)

## Deployment
Configured for Render deployment with automatic port detection and health checks.

<!-- Deployment trigger: 2025-07-15T11:23:47 -->