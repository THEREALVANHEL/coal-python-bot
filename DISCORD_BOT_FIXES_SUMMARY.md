# Discord Bot Fixes Summary - January 20, 2025

## Issues Resolved

### 1. Stock Market Cog - Duplicate Command Error
**Error:** `CommandAlreadyRegistered: Command 'buy' already registered.`

**Root Cause:** Both `cogs/stock_market.py` and `cogs/economy.py` had a command named "buy", causing a conflict.

**Fix Applied:**
- Changed stock market command from `buy` to `buystock`
- Updated help text references from `/buy` to `/buystock`

**Files Modified:**
- `cogs/stock_market.py`: Line 159 and 302

### 2. Backup System Cog - Import Error
**Error:** `ImportError: cannot import name 'json_util' from 'pymongo'`

**Root Cause:** In modern pymongo versions (4.0+), `json_util` is part of the `bson` package, not directly under `pymongo`.

**Fix Applied:**
- Changed import from `from pymongo import json_util` to `from bson import json_util`

**Files Modified:**
- `cogs/backup_system.py`: Line 11

## Expected Results

After these fixes, the bot should load all cogs successfully:
- ✅ 18 successful cog loads (instead of 16)
- ❌ 0 failed cog loads (instead of 2)

## Commands Affected

### Stock Market Commands
- **Old:** `/buy` (conflicted with economy)
- **New:** `/buystock` (unique to stock market)
- All other stock market commands remain unchanged: `/stocks`, `/sell`, `/portfolio`

### Backup System Commands
- No command changes, only fixed the internal import issue
- All backup system functionality should now work properly

## Deployment Status

These fixes are ready for deployment and should resolve the cog loading errors seen in the logs.

---
*Fixes applied: January 20, 2025*