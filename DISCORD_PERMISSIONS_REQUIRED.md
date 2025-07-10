# 🛡️ Discord Role Permissions Required

## 📋 **CRITICAL: Staff Role Permissions Setup**

For **Moderator**, **Lead Moderator**, **Overseer**, and **Forgotten One** roles to use ticket system buttons and admin controls, they MUST have these Discord permissions:

### 🎫 **TICKET SYSTEM PERMISSIONS**
```
✅ View Channels
✅ Send Messages  
✅ Manage Messages
✅ Manage Channels
✅ Mention Everyone
✅ Read Message History
✅ Use External Emojis
✅ Add Reactions
```

### 🛡️ **MODERATION PERMISSIONS** 
```
✅ Kick Members (for warnings/admin panel)
✅ Ban Members (for emergency ban feature)
✅ Moderate Members (for temp mute feature)
✅ Manage Messages (for message management)
✅ View Audit Log (for tracking actions)
```

### 💼 **JOB SYSTEM PERMISSIONS**
```
✅ Manage Roles (for job role assignments)
✅ View Channels (to monitor work channels)
✅ Send Messages (for system notifications)
```

## 🔧 **BOT PERMISSIONS REQUIRED**

The bot itself needs these permissions in your server:

### 🤖 **ESSENTIAL BOT PERMISSIONS**
```
✅ Administrator (RECOMMENDED - simplifies everything)

OR if you prefer granular permissions:
✅ View Channels
✅ Send Messages
✅ Manage Messages
✅ Manage Channels
✅ Manage Roles
✅ Kick Members
✅ Ban Members
✅ Moderate Members (Timeout)
✅ Mention Everyone
✅ Use External Emojis
✅ Add Reactions
✅ Read Message History
✅ Attach Files
✅ Embed Links
✅ Use Slash Commands
```

## ⚠️ **TROUBLESHOOTING PERMISSIONS**

### **Issue: Buttons Not Working for Staff**
**Solution:** Ensure staff roles have ALL permissions listed above

### **Issue: Can't Create Ticket Channels**  
**Solution:** Bot needs `Manage Channels` permission

### **Issue: Can't Ban/Kick from Admin Panel**
**Solution:** Staff roles need `Ban Members` and `Kick Members` permissions

### **Issue: Temp Mute Not Working**
**Solution:** Staff roles need `Moderate Members` permission

## 🎯 **ROLE HIERARCHY SETUP**

```
👑 Server Owner
🔥 Forgotten One    ← NEEDS ALL PERMISSIONS ABOVE
🔱 Overseer         ← NEEDS ALL PERMISSIONS ABOVE  
⚡ Lead Moderator   ← NEEDS ALL PERMISSIONS ABOVE
🛡️ Moderator        ← NEEDS ALL PERMISSIONS ABOVE
🤖 Coal Python Bot  ← NEEDS BOT PERMISSIONS ABOVE
👥 Other Roles
@everyone
```

## ✅ **QUICK PERMISSION CHECK**

1. Go to Server Settings → Roles
2. Select each staff role (Moderator, Lead Moderator, Overseer, Forgotten One)
3. Enable ALL permissions listed in "TICKET SYSTEM" and "MODERATION" sections
4. Make sure bot role has Administrator OR all bot permissions listed
5. Ensure bot role is ABOVE staff roles in hierarchy
6. Save changes and test ticket system

---

**💡 TIP:** Giving the bot `Administrator` permission is the easiest way to ensure everything works, but use granular permissions if you prefer more control.