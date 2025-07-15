# ⏰ Auto-Enable Feature - Automatic Discord Connection

## ✅ **Feature Overview**
The bot now automatically enables Discord operations after the startup delay, eliminating the need for manual activation after each deployment.

## 🚀 **How It Works**
1. **Deployment starts** - Bot begins in protection mode
2. **Startup delay** - Waits for configured delay (default 5 minutes)
3. **Auto-enable** - Automatically enables Discord operations
4. **Bot connects** - Discord bot comes online automatically

## ⚙️ **Configuration**
New environment variables control the auto-enable behavior:

```bash
# Auto-enable Discord after startup delay (default: true)
AUTO_ENABLE_AFTER_STARTUP=true

# Nuclear mode - completely disable Discord (default: false)
NUCLEAR_MODE=false

# Manual enable required - disable auto-features (default: false)
MANUAL_ENABLE_REQUIRED=false
```

## 🔧 **Configuration Options**

### **Auto-Enable Mode (Default)**
```bash
NUCLEAR_MODE=false
MANUAL_ENABLE_REQUIRED=false
AUTO_ENABLE_AFTER_STARTUP=true
```
- ✅ Bot automatically connects after startup delay
- ✅ No manual intervention required
- ✅ Protection delay still active

### **Manual Mode**
```bash
NUCLEAR_MODE=false
MANUAL_ENABLE_REQUIRED=true
AUTO_ENABLE_AFTER_STARTUP=false
```
- ❌ Manual activation required
- ❌ POST to `/nuclear-enable` needed
- ✅ Full manual control

### **Nuclear Mode**
```bash
NUCLEAR_MODE=true
MANUAL_ENABLE_REQUIRED=true
AUTO_ENABLE_AFTER_STARTUP=false
```
- ❌ Discord completely disabled
- ❌ Manual activation required
- ❌ Maximum protection mode

## 📊 **Expected Behavior**

### **During Deployment**
```
🚨 CLOUDFLARE PROTECTION: 1800s cooldown, 300s startup delay
🛡️ EMERGENCY MODE: All connections will be heavily rate limited
⏰ AUTO-ENABLE MODE: Discord will connect automatically after startup delay
🚀 Discord will be enabled after 300s protection delay
```

### **After Startup Delay**
```
⏰ AUTO-ENABLE: Discord will be enabled after 300s startup delay
✅ AUTO-ENABLE: Discord operations enabled after startup delay
🔍 Checking for previous Cloudflare blocks...
✅ Discord bot connecting...
```

## 🎯 **Benefits**
- ✅ **No manual intervention** required after deployment
- ✅ **Maintains protection** during startup delay
- ✅ **Automatic recovery** after deployment
- ✅ **Backward compatible** with manual mode

## 🔄 **Migration from Nuclear Mode**
If you were using nuclear mode before, no action required:
1. Bot will automatically use auto-enable mode
2. Discord will connect after startup delay
3. No more manual `/nuclear-enable` requests needed

## 📱 **Manual Override**
You can still use manual endpoints if needed:
- `GET /nuclear-status` - Check current status
- `POST /nuclear-enable` - Force enable Discord
- `POST /nuclear-disable` - Force disable Discord

## ⚠️ **Emergency Fallback**
If auto-enable causes issues, you can revert to nuclear mode:
```bash
NUCLEAR_MODE=true
MANUAL_ENABLE_REQUIRED=true
AUTO_ENABLE_AFTER_STARTUP=false
```

---

**Status**: ✅ **Active** - Auto-enable feature is now the default behavior
**Action Required**: None - Bot will automatically connect after deployment