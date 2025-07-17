# 🤖 **COAL PYTHON BOT - COPYABLE COMMAND REFERENCE**

## 🔑 **REQUIRED ROLES & PERMISSIONS**

### **🛡️ Staff Roles (Ticket & Moderation)**
```
Forgotten One
🦥 Overseer  
🚨 Lead Moderator
Moderator
```

### **🍪 Special Manager Roles**
```
Cookie Manager (ID: 1372121024841125888)
Special Admin (ID: 1376574861333495910)
```

### **🎯 Auto-Assigned Role**
```
New Member Role (ID: 1384141744303636610)
```

### **💼 Job System Roles (Auto-assigned by level)**
```
Intern (Level 0-9)
Junior Developer (Level 10-19)
Software Developer (Level 20-29)
Senior Developer (Level 30-49)
Team Lead (Level 50-99)
Engineering Manager (Level 100-199)
Director (Level 200-299)
VP of Engineering (Level 300-449)
CTO (Level 450-999)
Tech Legend (Level 1000+)
```

---

## 📋 **ALL COMMANDS BY CATEGORY**

### **🏠 BASIC & UTILITY COMMANDS**

```
/test - Simple test command to verify bot functionality
/hello - Basic hello command and response test
/ping - Check bot latency and response time
/info - Show bot information and status
/serverinfo - Shows server stats and information
```
**Permissions:** Everyone

---

### **👤 PROFILE & PROGRESSION COMMANDS**

```
/profile [user] - Shows comprehensive profile with level, cookies, job, and daily streak
/daily - Claim daily XP and coin bonus with streak rewards
/balance - Check your shiny coin balance
/cookies [user] - Check your delicious cookie balance  
/work - Independent career progression system - work your way up!
/myitems - View your active temporary purchases and their remaining time
```
**Permissions:** Everyone

---

### **🏆 LEADERBOARDS & RANKINGS**

```
/leaderboard [type] [page] - View server leaderboards with pagination
```
**Types available:**
- `xp` - XP & Levels leaderboard
- `cookies` - Cookies leaderboard
- `coins` - Coins leaderboard  
- `streak` - Daily streaks leaderboard

**Permissions:** Everyone

---

### **🛒 ECONOMY & SHOP COMMANDS**

```
/shop - View the premium temporary items shop
/buy [item] [duration] - Purchase temporary items with coins
/coinflip [amount] - Flip a coin and bet coins
```
**Permissions:** Everyone

---

### **🎪 FUN & ENTERTAINMENT COMMANDS**

```
/flip - Flip a coin - heads or tails
/spinwheel - Spin an enhanced wheel with arrow pointing to winner
/askblecknephew [question] - Ask your nephew BleckNephew anything!
/talktobleky - Start a conversation with your nephew Bleky
/trivia [difficulty] - AI-powered trivia with dynamic questions (easy/medium/hard)
/wordchain - Enhanced word chain game with no hints, skill-based
```
**Permissions:** Everyone

**New AI Features:**
- Smart trivia generates unique questions every time
- Word chain doesn't reveal answers, purely skill-based
- Dynamic difficulty and reward systems

---

### **📅 EVENTS & COMMUNITY COMMANDS**

```
/shout [title] [description] [host] [co_host] [medic] [guide] - Create detailed event announcement
/gamelog [game] [result] [participants] [image] - Log completed game with details
/giveaway [duration] [winners] [prize] - Start a giveaway  
/announce [title] [content] - Creates professional pointwise announcement
/remind [time] [message] - Set a reminder for yourself
/suggest [suggestion] [media] - Submit suggestions with optional media
```
**Permissions:** Everyone

---

### **🎫 SIMPLE TICKET SYSTEM COMMANDS**

```
/ticket-panel - Create simple ticket panel with one button
```
**Permissions:** Administrator only

**Simple Ticket Features:**
- Single ticket creation button
- Channel naming: {username}ticket initially, 🟢{claimed_user} when claimed
- Auto ping 4 staff roles when ticket created
- Transferable between staff without limitation
- Claim cooldown protection (2 seconds)

**Ticket Management Buttons (Staff only):**
- 🔴 Claim Ticket (changes to 🟢 when claimed, renames channel)
- 🔐 Close Ticket (deletes channel after 5 seconds)

**Required roles for buttons:** Forgotten One, 🦥 Overseer, 🚨 Lead Moderator, Moderator

---

### **🔨 MODERATION COMMANDS**

```
/warn [user] [reason] - Warn a user
/warnlist [user] - Check warnings for a user (public)
/removewarnlist [user] [warning_index] [reason] - Remove/clear warnings
/modclear [amount] - Delete messages (1-100)
/setlog [channel] - Set moderation and logging channel
```
**Permissions:** Staff roles (4 roles) or Administrator

---

### **⚙️ ADMINISTRATION COMMANDS**

```
/addxp [user] [amount] - Add XP to a user
/removexp [user] [amount] - Remove XP from a user  
/addcoins [user] [amount] - Add coins to a user
/removecoins [user] [amount] - Remove coins from a user
/updateroles [user] - Update roles based on level and cookies
/sync - Force sync all slash commands
/dbhealth - Check database sync status
```
**XP commands:** Administrator or Special Admin role  
**Coin commands:** Administrator only  
**Other commands:** Administrator only

---

### **🍪 COOKIE MANAGEMENT COMMANDS**

```
/addcookies [user] [amount] - Add cookies to a user
/removecookies [user] [amount] - Remove cookies from a user
/cookiesgiveall [amount] - Give cookies to everyone
/removecookiesall [amount] - Remove cookies from everyone
```
**Permissions:** Cookie Manager role only (ID: 1372121024841125888)

---

### **🎯 HOST & EVENT COMMANDS**

```
/shout [message] [channel] - Make bot send message to specific channel
/gamelog [game] [result] [image] - Log game event with image support
```
**Permissions:** Host roles only (🦥 Overseer, Forgotten one, 🚨 Lead moderator)

---

### **📊 SETTINGS & CONFIGURATION**

```
/starboard [channel] [emoji] [threshold] - Configure starboard settings
/viewsettings - View current server settings
/quicksetup - Enhanced setup wizard for all bot functions
```
**Admin commands:** Administrator only  
**View settings:** Everyone

---

### **💼 JOB & WORK TRACKING**

```
/work-policy - View 24-hour work policy and requirements  
/job-overview - Management overview of all job role activity
```
**Work policy:** Everyone  
**Job overview:** Staff roles only

---

## 🌐 **WEB API ENDPOINTS**

```
GET /nuclear-status - Check protection status
POST /nuclear-enable - Manually enable Discord (CAUTION)
POST /nuclear-disable - Disable Discord operations  
GET /health - Service health check
GET / - Home page with status
GET /stats - Bot statistics
GET /ping - Simple ping test
```

---

## 📊 **COMMAND SUMMARY BY PERMISSION**

### **👥 Everyone (25 commands)**
```
test, hello, ping, info, serverinfo, profile, daily, balance, cookies, work, myitems, leaderboard, shop, buy, coinflip, flip, spinwheel, askblecknephew, talktobleky, shout, gamelog, giveaway, announce, remind, suggest, viewsettings, work-policy
```

### **🛡️ Staff Roles (8 commands)**  
```
warn, warnlist, removewarnlist, modclear, setlog, updateroles, job-overview, ticket buttons
```

### **🍪 Cookie Manager (4 commands)**
```
addcookies, removecookies, cookiesgiveall, removecookiesall
```

### **🎯 Host Roles (2 commands)**
```
shout (host version), gamelog (host version)
```

### **👑 Administrator (12 commands)**
```
addxp, removexp, addcoins, removecoins, sync, dbhealth, ticket-panel, setlog, starboard, quicksetup, updateroles, modclear
```

### **⭐ Special Admin Role (2 commands)**
```
addxp, removexp
```

---

## 🎯 **AUTOMATIC FEATURES**

### **🔄 Auto-Role Assignment**
- New Member Role (ID: 1384141744303636610) - Assigned on join
- Level-based job roles - Updated automatically
- Cookie milestone roles - Updated automatically  
- Temporary shop roles - Managed automatically

### **📈 Background Systems**
- Daily streak tracking
- Temporary item expiration
- Role synchronization
- Database optimization
- Auto-moderation logging

---

## 🏗️ **BOT STRUCTURE**

### **Loaded Cogs:**
```
cogs.leveling - XP, levels, daily rewards
cogs.cookies - Cookie management system
cogs.economy - Coins, shop, work, gambling
cogs.events - Auto-role and event handling
cogs.community - Fun commands and community features
cogs.moderation - Warning system and mod tools
cogs.enhanced_moderation - Advanced mod features
cogs.settings - Server configuration
cogs.simple_tickets - Simple ticket system (claim/close only)
cogs.job_tracking - Work policy and job oversight
cogs.cool_commands - Enhanced features and commands
cogs.dashboard - Web dashboard functionality
cogs.enhanced_minigames - AI-powered games (trivia, word chain)
cogs.security_performance - Security and performance tools
```

### **Special Role IDs:**
```
Cookie Manager: 1372121024841125888
Special Admin: 1376574861333495910  
New Member Role: 1384141744303636610
```

---

## 🚀 **TOTAL: 49 SLASH COMMANDS + WEB API**

**Permission Breakdown:**
- **Public Access:** 27 commands (55%)
- **Staff Access:** 8 commands (16%)  
- **Manager Access:** 4 commands (8%)
- **Host Access:** 2 commands (4%)
- **Admin Access:** 8 commands (17%)

**Categories:**
- Basic/Utility: 5 commands
- Profile/Progress: 6 commands
- Economy/Shop: 6 commands  
- Fun/Entertainment: 6 commands (includes AI games)
- Events/Community: 6 commands
- Simple Tickets: 1 command + basic button system
- Moderation: 5 commands
- Administration: 7 commands
- Cookie Management: 4 commands
- Settings: 3 commands
- Job Tracking: 2 commands

**Recent Improvements:**
- ✅ Simplified ticket system with basic claim/close functionality
- ✅ Fixed AI-powered trivia with dynamic questions
- ✅ Fixed word chain game (no answer reveals)
- ✅ Auto role pings and channel renaming in tickets
- ✅ Transferable tickets between staff with cooldown protection

---

**✅ All commands are active and functional with nuclear protection enabled!**
**🚀 Recently optimized and enhanced with AI-powered features!**