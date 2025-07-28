# 🔧 Fix "Unknown Integration" Error

## ❌ **Problem**: All commands show "unknown integration"

This error occurs when there's a mismatch between your bot token and application ID, or missing permissions.

## ✅ **Step-by-Step Fix**:

### **1. Check Your Discord Developer Portal**

1. Go to https://discord.com/developers/applications
2. Select your bot application
3. Copy the **Application ID** from the "General Information" tab
4. Go to the "Bot" tab and copy the **Token**

### **2. Update Environment Variables on Render**

1. Go to your Render Dashboard
2. Select your bot service
3. Go to "Environment" tab
4. Update these variables:
   ```
   DISCORD_TOKEN=your_bot_token_here
   DISCORD_CLIENT_ID=your_application_id_here
   ```

### **3. Verify Bot Permissions**

Make sure your bot has these permissions in Discord:
- ✅ **Send Messages**
- ✅ **Use Slash Commands** 
- ✅ **Embed Links**
- ✅ **Read Message History**
- ✅ **Add Reactions**

### **4. Re-invite Your Bot (If Needed)**

If the error persists, re-invite your bot with proper scopes:

1. In Discord Developer Portal → OAuth2 → URL Generator
2. Select scopes: `bot` and `applications.commands`
3. Select permissions: `Administrator` (or specific permissions)
4. Use the generated URL to re-invite your bot

### **5. Use Diagnostic Commands**

Once your bot is running, use these commands in Discord:

```
!bot_info        # Check bot configuration
!fix_integration # Attempt automatic fix
```

## 🔍 **Common Causes**:

1. **Token/ID Mismatch**: Bot token doesn't match the application ID
2. **Missing Scopes**: Bot wasn't invited with `applications.commands` scope
3. **Insufficient Permissions**: Bot lacks required permissions
4. **Cache Issues**: Discord needs time to update command registry

## ⚡ **Quick Fix**:

If you have access to the bot, try:
1. Use `!fix_integration` command
2. Wait 2-3 minutes for Discord to update
3. Try slash commands again

## 🎯 **Expected Result**:

After fixing, you should see:
- ✅ Slash commands appear in Discord
- ✅ Commands execute without "unknown integration" error
- ✅ All 87 bot commands working properly

The bot will work perfectly once the token/ID configuration is correct!