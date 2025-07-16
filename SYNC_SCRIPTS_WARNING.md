# ⚠️ SYNC SCRIPTS WARNING

## Important Notice

The following sync scripts in this repository create their own bot instances and should **NOT** be run while the main bot is active:

- `improved_sync.py`
- `force_sync.py` 
- `emergency_sync.py`
- `sync_commands.py`
- `quick_fix_sync.py`

## Why This Matters

Running these scripts while the main bot is running can cause:
- **Discord API conflicts** - Multiple bot instances fighting for the same token
- **Rate limiting issues** - Exceeding Discord's rate limits
- **Bot crashes** - The main bot may crash due to token conflicts
- **Command sync failures** - Commands may not sync properly

## When to Use Sync Scripts

### ✅ **Safe Usage**
- **Only when the main bot is offline**
- For emergency command syncing
- When testing new commands in development
- After major cog updates

### ❌ **Avoid Using When**
- Main bot is running in production
- Bot is already online and functioning
- Commands are working normally
- You're not sure if the main bot is running

## Recommended Approach

Instead of using these sync scripts, the main bot now has:
- **Automatic command syncing** on startup
- **Proper error handling** for sync failures
- **Background sync operations** that don't interfere with normal operation

## If You Must Use a Sync Script

1. **Stop the main bot first**
2. **Wait 30 seconds** for Discord to recognize the disconnect
3. **Run the sync script**
4. **Wait for it to complete**
5. **Start the main bot again**

## Better Alternative

The main bot (v3.0.0) now includes a built-in sync system that:
- Automatically syncs commands on startup
- Handles errors gracefully
- Doesn't cause conflicts
- Provides proper logging

**Just restart the main bot instead of using these scripts!**

---

**Updated:** 2025-01-16  
**Status:** ⚠️ Use with caution  
**Recommendation:** Avoid using these scripts with the new stable bot version