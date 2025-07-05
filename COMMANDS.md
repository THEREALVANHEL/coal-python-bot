# 🤖 Coal Python Bot - Command List

## 📋 **Table of Contents**
- [🎮 Community Commands](#-community-commands)
- [💰 Economy Commands](#-economy-commands)
- [🍪 Cookie Commands](#-cookie-commands)
- [📊 Leveling Commands](#-leveling-commands)
- [🛠️ Moderation Commands](#️-moderation-commands)
- [⚙️ Settings Commands](#️-settings-commands)
- [🎉 Event Commands](#-event-commands)
- [🔧 General Commands](#-general-commands)
- [🎭 Auto Events](#-auto-events)

---

## 🎮 **Community Commands**

### `/suggest <suggestion>`
- **Description:** Submit a suggestion to the server
- **Usage:** `/suggest Make a gaming channel`
- **Permissions:** Everyone
- **Features:** Automatic voting reactions (👍/👎)

### `/flip`
- **Description:** Flip a coin - heads or tails
- **Usage:** `/flip`
- **Permissions:** Everyone
- **Features:** Shows actual coin images (heads.jpeg/tails.jpeg)

### `/spinawheel <options>`
- **Description:** Spin a wheel with up to 10 options
- **Usage:** `/spinawheel Pizza, Burger, Tacos, Sushi`
- **Permissions:** Everyone
- **Features:** Creates custom wheel image with your options
- **Limits:** 2-10 options

### `/userinfo [user]`
- **Description:** View detailed info about a server member
- **Usage:** `/userinfo @username` or `/userinfo` (for yourself)
- **Permissions:** Everyone
- **Shows:** Username, ID, join date, roles, account creation

### `/serverinfo`
- **Description:** Shows stats and info about the server
- **Usage:** `/serverinfo`
- **Permissions:** Everyone
- **Shows:** Owner, member count, channels, roles, boost info

### `/ping`
- **Description:** Check the bot's ping to Discord servers
- **Usage:** `/ping`
- **Permissions:** Everyone

### `/askblecknephew <question>`
- **Description:** THE SAINT shall clear your doubts (AI-powered)
- **Usage:** `/askblecknephew What's the meaning of life?`
- **Permissions:** Everyone
- **Features:** AI responses with clickable links

### `/giveaway <duration> <prize> [winners] [channel]`
- **Description:** Start a giveaway with specified duration and winner count
- **Usage:** `/giveaway 60 Discord Nitro 2 #general`
- **Permissions:** 🚨 **Moderator+** (Moderator 🚨🚓, 🚨 Lead moderator, 🦥 Overseer, Forgotten one)
- **Features:** Interactive button entry, automatic winner selection
- **Limits:** 1-10080 minutes (1 week max), 1-20 winners

### `/announce <channel> <title> <message>`
- **Description:** Creates and sends a formatted announcement
- **Usage:** `/announce #announcements Server Update New rules added!`
- **Permissions:** 🚨 **Moderator+** (Moderator 🚨🚓, 🚨 Lead moderator, 🦥 Overseer, Forgotten one)

---

## 💰 **Economy Commands**

### `/balance [user]`
- **Description:** Check your or another user's coin balance
- **Usage:** `/balance` or `/balance @username`
- **Permissions:** Everyone

### `/work`
- **Description:** Work to earn some coins
- **Usage:** `/work`
- **Permissions:** Everyone
- **Cooldown:** 30 minutes
- **Earnings:** 50-200 coins per work
- **Features:** Detailed job descriptions, realistic scenarios (Software Developer, Pro Gamer, etc.)
- **Boost:** Double earnings with XP Boost active

### `/coinflip <amount> <choice>`
- **Description:** Flip a coin and bet coins
- **Usage:** `/coinflip 100 heads`
- **Permissions:** Everyone
- **Choices:** heads, tails
- **Features:** Shows actual coin images, win/lose system

### `/shop`
- **Description:** View the server shop
- **Usage:** `/shop`
- **Permissions:** Everyone
- **Items:** XP Boost (250), VIP Role (800), Custom Role (1500), Profile Badge (500)
- **Note:** All roles are temporary with time limits!

### `/buy <item>`
- **Description:** Buy an item from the shop
- **Usage:** `/buy VIP Role`
- **Permissions:** Everyone
- **Items:** XP Boost (1 hour), VIP Role (7 days), Custom Role (30 days), Profile Badge (permanent)
- **Features:** Temporary roles auto-removed when expired

---

## 🍪 **Cookie Commands**

### `/cookies [user]`
- **Description:** Check your or another user's cookie count
- **Usage:** `/cookies` or `/cookies @username`
- **Permissions:** Everyone

### `/givecookies <user> <amount>`
- **Description:** Give cookies to another user
- **Usage:** `/givecookies @username 10`
- **Permissions:** Everyone
- **Limits:** Must have enough cookies to give

### `/cookieleaderboard`
- **Description:** View the top cookie holders
- **Usage:** `/cookieleaderboard`
- **Permissions:** Everyone
- **Shows:** Top 10 cookie holders

---

## 📊 **Leveling Commands**

### `/level [user]`
- **Description:** Check your or another user's level and XP
- **Usage:** `/level` or `/level @username`
- **Permissions:** Everyone

### `/leaderboard`
- **Description:** View the XP leaderboard
- **Usage:** `/leaderboard`
- **Permissions:** Everyone
- **Shows:** Top 10 XP holders

### `/daily`
- **Description:** Claim your daily XP bonus
- **Usage:** `/daily`
- **Permissions:** Everyone
- **Cooldown:** 24 hours
- **Reward:** 100 XP base + streak bonus
- **Features:** Streak system (bonus every 7 days)

### `/streaktop`
- **Description:** Shows the top 10 users with the highest daily streaks
- **Usage:** `/streaktop`
- **Permissions:** Everyone
- **Features:** Fire emojis for long streaks, tracks daily consistency

---

## 🛠️ **Moderation Commands**

### `/warn <user> [reason]`
- **Description:** Warn a user
- **Usage:** `/warn @username Spamming in chat`
- **Permissions:** 🚨 **Moderator+**

### `/warnings <user>`
- **Description:** View all warnings for a user
- **Usage:** `/warnings @username`
- **Permissions:** 🚨 **Moderator+**

### `/kick <user> [reason]`
- **Description:** Kick a user from the server
- **Usage:** `/kick @username Breaking rules`
- **Permissions:** 🚨 **Kick Members**

### `/ban <user> [reason]`
- **Description:** Ban a user from the server
- **Usage:** `/ban @username Serious rule violation`
- **Permissions:** 🚨 **Ban Members**

### `/timeout <user> <duration> [reason]`
- **Description:** Timeout a user for specified duration
- **Usage:** `/timeout @username 60 Excessive spam`
- **Permissions:** 🚨 **Moderate Members**
- **Duration:** In minutes

### `/purge <amount>`
- **Description:** Delete multiple messages at once
- **Usage:** `/purge 10`
- **Permissions:** 🚨 **Manage Messages**
- **Limits:** 1-100 messages

---

## ⚙️ **Settings Commands**

### `/setchannel <function> <channel>`
- **Description:** Set a channel for specific bot functions
- **Usage:** `/setchannel Level Up Announcements #level-ups`
- **Permissions:** 🚨 **Manage Server**
- **Functions:** Level Up, Welcome, Goodbye, Starboard, Mod Logs

### `/starboard <action> [value]`
- **Description:** Configure the starboard settings
- **Usage:** `/starboard Set Star Threshold 5`
- **Permissions:** 🚨 **Manage Server**
- **Actions:** Set Star Threshold, Toggle Starboard, Set Starboard Channel

### `/viewsettings`
- **Description:** View current server settings
- **Usage:** `/viewsettings`
- **Permissions:** Everyone
- **Shows:** Channel settings, starboard config

### `/resetsettings`
- **Description:** Reset all server settings to default
- **Usage:** `/resetsettings`
- **Permissions:** 🚨 **Administrator**
- **Warning:** This action cannot be undone!

---

## 🎉 **Event Commands**

### `/shout <channel> <message>`
- **Description:** Make the bot send a message to a specific channel
- **Usage:** `/shout #general Event starting in 5 minutes!`
- **Permissions:** 🚨 **Host Only** (🦥 Overseer, Forgotten one, 🚨 Lead moderator)
- **Features:** Formatted embed with join button

### `/gamelog <title> <description> [winner] [image]`
- **Description:** Log a game event or result with image support
- **Usage:** `/gamelog Tournament Finals Epic battle royale @winner screenshot.png`
- **Permissions:** 🚨 **Host Only** (🦥 Overseer, Forgotten one, 🚨 Lead moderator)
- **Features:** Image attachment support, winner highlighting

---

## 🔧 **General Commands**

### `/help`
- **Description:** Show help information
- **Usage:** `/help`
- **Permissions:** Everyone

### `/sync`
- **Description:** Sync slash commands (owner only)
- **Usage:** `/sync`
- **Permissions:** 🚨 **Bot Owner Only**

---

## 🎭 **Auto Events**

### **Message XP System**
- **Trigger:** Sending messages
- **Reward:** 15-25 XP per message (30-50 with XP Boost)
- **Cooldown:** 1 minute between XP gains
- **Features:** Automatic level up announcements, XP boost detection
- **Boost:** Double XP when XP Boost item is active

### **Welcome Messages**
- **Trigger:** User joins server
- **Features:** Welcome embed with animated GIF, member count
- **Requirement:** Welcome channel must be set

### **Goodbye Messages**
- **Trigger:** User leaves server
- **Features:** Goodbye embed with animated GIF
- **Requirement:** Goodbye channel must be set

### **Starboard System**
- **Trigger:** ⭐ reactions on messages
- **Requirement:** Starboard enabled + threshold met
- **Features:** Automatic message highlighting in starboard channel

### **Temporary Role System**
- **Trigger:** Purchasing roles from shop
- **Features:** Automatic role removal when expired
- **Cleanup:** Hourly cleanup task removes expired roles
- **Tracking:** All temporary roles stored in MongoDB with timestamps

### **Auto-Cleanup System**
- **Frequency:** Every hour
- **Function:** Removes expired roles, purchases, and temporary items
- **Scope:** Server-wide cleanup of all expired items
- **Logging:** Automatic cleanup status logging

---

## 🎨 **Special Features**

### **Asset Integration**
- 🪙 **Coin Images:** Real coin images for flip/coinflip commands
- 🎡 **Custom Wheels:** Generated wheel images with your options
- 🎬 **Animated GIFs:** Welcome/goodbye messages with GIFs
- 🎨 **Custom Fonts:** Poppins-Bold font for wheel text

### **Permission Levels**
- 👤 **Everyone:** Basic commands, fun features
- 🚨 **Moderator+:** Warn, announce, giveaway commands
- 🛠️ **Manage Server:** Settings configuration
- 👑 **Administrator:** Reset settings, advanced config
- 🎯 **Host Only:** Event management, shout commands

### **Interactive Features**
- 🎉 **Giveaway Buttons:** Click to enter giveaways
- 🌟 **Reaction Voting:** Automatic reactions on suggestions
- 🔗 **Link Buttons:** Clickable links in AI responses
- 🎮 **Event Buttons:** Join event buttons in announcements
- ⚡ **XP Boost System:** Temporary double XP from shop purchases
- 🌟 **VIP Role System:** Temporary premium roles with auto-removal
- 🔄 **Auto-Cleanup:** Hourly removal of expired items

### **Error Handling**
- 🛡️ **Interaction Safety:** Prevents "already acknowledged" errors
- 🔧 **MongoDB Compatibility:** Proper collection truth value testing
- 📊 **Database Syncing:** All data stored and retrieved from MongoDB
- 🔄 **Automatic Recovery:** Graceful error handling with fallbacks

---

## 📞 **Need Help?**

If you need assistance with any command or feature, feel free to:
- Use `/help` for basic information
- Ask a moderator for command-specific help
- Check the bot's responses for usage examples

**Bot Version:** Latest with Temporary Roles & Error Fixes
**Last Updated:** January 2025 - Major System Update

---

*This bot is continuously updated with new features and improvements!* 🚀