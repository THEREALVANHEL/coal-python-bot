# 🤖 COAL BOT - Complete Command List

## 📋 **Role Permissions Reference**
- **🦥 Overseer** - Full admin access
- **Forgotten one** - Full admin access  
- **� Lead moderator** - Manager + Host permissions
- **Moderator �🚓** - Basic moderation + announcements

---

## � **TICKET SYSTEM**

### `/createticket`
- **Function:** Create a support ticket instantly
- **Permissions:** Everyone
- **Description:** Opens a private ticket with regional support options (UK/US/EU)

### `/ticketpanel`
- **Function:** Create ticket panel in current channel
- **Permissions:** Administrator only
- **Description:** Sets up the ticket creation interface

### `/giveticketroleperms`
- **Function:** Grant ticket support permissions to roles
- **Permissions:** Administrator only
- **Description:** Allows roles to access and manage tickets

### `/ticketstats`
- **Function:** View comprehensive ticket system statistics
- **Permissions:** Manage Channels
- **Description:** Shows ticket analytics and system info

### `/closealltickets`
- **Function:** Emergency: Close all open tickets
- **Permissions:** Administrator only
- **Description:** Nuclear option for emergency situations

---

## 💰 **ECONOMY SYSTEM**

### `/balance`
- **Function:** Check your shiny coin balance
- **Permissions:** Everyone
- **Description:** View your current coin wallet

### `/work`
- **Function:** Work various jobs to earn coins
- **Permissions:** Everyone
- **Description:** Choose from different jobs to earn money

### `/shop`
- **Function:** View the premium temporary items shop
- **Permissions:** Everyone
- **Description:** Browse 16 premium items across 4 categories

### `/buy`
- **Function:** Purchase premium temporary items
- **Permissions:** Everyone
- **Description:** Buy power-ups, social status, access perks, and fun items

### `/coinflip`
- **Function:** Flip a coin and bet coins
- **Permissions:** Everyone
- **Description:** Gambling mini-game with coin betting

### `/myitems`
- **Function:** View your active temporary purchases
- **Permissions:** Everyone
- **Description:** Check remaining time on purchased items

---

## 🍪 **COOKIE SYSTEM**

### `/cookies`
- **Function:** Check your delicious cookie balance
- **Permissions:** Everyone
- **Description:** View your cookie wealth and stats

### `/addcookies`
- **Function:** Add cookies to a user
- **Permissions:** Manager roles only (🦥 Overseer, Forgotten one, 🚨 Lead moderator)
- **Description:** Give cookies to members

### `/removecookies`
- **Function:** Remove cookies with selection options
- **Permissions:** Manager roles only (🦥 Overseer, Forgotten one, 🚨 Lead moderator)
- **Description:** Remove cookies, supports percentages, reset, penalty codes

### `/cookiesgiveall`
- **Function:** Give cookies to everyone in server
- **Permissions:** Manager roles only (🦥 Overseer, Forgotten one, 🚨 Lead moderator)
- **Description:** Mass cookie distribution

---

## 🏆 **LEVELING & PROFILE**

### `/profile`
- **Function:** Show comprehensive profile
- **Permissions:** Everyone
- **Description:** View level, cookies, job, daily streak, and stats

### `/leaderboard`
- **Function:** View all server leaderboards
- **Permissions:** Everyone
- **Description:** See top members by XP, cookies, and level

### `/daily`
- **Function:** Claim daily XP and coin bonus
- **Permissions:** Everyone
- **Description:** Daily rewards with streak multipliers

---

## 🚨 **MODERATION**

### `/addxp`
- **Function:** Add XP to a user
- **Permissions:** Administrator only
- **Description:** Manually adjust member XP

### `/removexp`
- **Function:** Remove XP from a user
- **Permissions:** Administrator only
- **Description:** Reduce member XP for violations

### `/modclear`
- **Function:** Delete specified number of messages
- **Permissions:** Manage Messages
- **Description:** Bulk message deletion for cleanup

### `/warn`
- **Function:** Warn a user
- **Permissions:** Manage Messages
- **Description:** Issue formal warnings to members

### `/checkwarnlist`
- **Function:** Check warnings for a user
- **Permissions:** Manage Messages
- **Description:** View member's warning history

### `/removewarnlist`
- **Function:** Remove warnings or clear all
- **Permissions:** Manage Messages
- **Description:** Delete specific warnings or reset count

### `/updateroles`
- **Function:** Update roles based on level and cookies
- **Permissions:** Manage Roles
- **Description:** Sync member roles with their progression

### `/roleplay`
- **Function:** Interactive AI roleplay with persistence
- **Permissions:** Everyone
- **Description:** Chat with AI characters with memory

---

## 📢 **COMMUNITY & EVENTS**

### `/suggest`
- **Function:** Submit server improvement suggestions
- **Permissions:** Everyone
- **Description:** Send suggestions with optional media to suggestion channel

### `/shout`
- **Function:** Create event announcements with live tracking
- **Permissions:** Announcement roles (Moderator 🚨🚓, 🚨 Lead moderator, 🦥 Overseer, Forgotten one)
- **Description:** Professional event posts with participant tracking, time strings (1h, 30m)

### `/gamelog`
- **Function:** Log completed games with details
- **Permissions:** Announcement roles (Moderator 🚨🚓, 🚨 Lead moderator, 🦥 Overseer, Forgotten one)
- **Description:** Record game results with participants and media

### `/spinwheel`
- **Function:** Spin enhanced wheel with arrow
- **Permissions:** Everyone
- **Description:** Modern wheel spinner with premium design

### `/giveaway`
- **Function:** Start giveaway with duration and winners
- **Permissions:** Announcement roles (Moderator 🚨🚓, 🚨 Lead moderator, 🦥 Overseer, Forgotten one)
- **Description:** Automated giveaway system with time limits

### `/announce`
- **Function:** Create professional pointwise announcements
- **Permissions:** Announcement roles (Moderator 🚨🚓, 🚨 Lead moderator, 🦥 Overseer, Forgotten one)
- **Description:** Structured announcements with bullet points

### `/remind`
- **Function:** Set personal reminders
- **Permissions:** Everyone
- **Description:** Get pinged after specified time (5m, 1h, 2d format)

---

## ℹ️ **INFORMATION & UTILITY**

### `/userinfo`
- **Function:** View detailed member information
- **Permissions:** Everyone
- **Description:** Comprehensive user stats and details

### `/serverinfo`
- **Function:** Show server stats and information
- **Permissions:** Everyone
- **Description:** Server overview with member counts and features

### `/ping`
- **Function:** Check bot's ping to Discord
- **Permissions:** Everyone
- **Description:** Test bot responsiveness and latency

### `/askblecknephew`
- **Function:** Ask BleckNephew AI anything
- **Permissions:** Everyone
- **Description:** Chat with optimized AI assistant (under 500 words)

### `/flip`
- **Function:** Flip a coin - heads or tails
- **Permissions:** Everyone
- **Description:** Simple coin flip game

---

## ⚙️ **SERVER SETTINGS**

### `/quicksetup`
- **Function:** Enhanced setup wizard for all bot functions
- **Permissions:** Manage Server
- **Description:** Configure channels, roles, and bot features

### `/starboard`
- **Function:** Configure starboard settings
- **Permissions:** Manage Server
- **Description:** Set up reaction-based message highlighting

### `/viewsettings`
- **Function:** View current server configuration
- **Permissions:** Manage Server
- **Description:** Check all bot settings and channels

### `/sync`
- **Function:** Force sync all slash commands
- **Permissions:** Administrator only
- **Description:** Refresh command registration (emergency use)

---

## 🔧 **DEVELOPMENT/TESTING**

### `/hello`
- **Function:** Basic hello command
- **Permissions:** Everyone
- **Description:** Test if bot is responding

### `/test`
- **Function:** Simple test command
- **Permissions:** Everyone
- **Description:** Verify bot responsiveness

### `/info`
- **Function:** Show bot information and status
- **Permissions:** Everyone
- **Description:** Bot version and system info

---

## 🎮 **EVENT COMMANDS** (Alternative versions)

### Event `/shout`
- **Function:** Make bot send message to specific channel
- **Permissions:** Host roles (🦥 Overseer, Forgotten one, 🚨 Lead moderator)
- **Description:** Alternative shout command for events

### Event `/gamelog`
- **Function:** Log game event with image support
- **Permissions:** Host roles (🦥 Overseer, Forgotten one, 🚨 Lead moderator)
- **Description:** Alternative gamelog with winner tracking

---

## 📊 **USAGE TIPS**

- **Time Formats:** Use `1h` (1 hour), `30m` (30 minutes), `2d` (2 days), `now` for immediate
- **Percentage Cookies:** Use `25%` to remove percentage of cookies
- **Special Codes:** Use `reset` or `penalty` for special cookie removal
- **Live Events:** Shout command now shows live participant count to everyone
- **Temporary Items:** Shop items are organized in Power-Ups, Social Status, Access, and Fun categories

## 🎯 **PREMIUM SHOP CATEGORIES**

### 💪 Power-Ups (4 items)
- XP Boost, Cookie Multiplier, Coin Boost, Work Success

### ⭐ Social Status (4 items)  
- VIP Role, Custom Color, Crown Badge, Rainbow Name

### 🔓 Access (4 items)
- VIP Channels, Nickname Freedom, Voice Priority, Early Access

### 🎉 Fun & Games (4 items)
- Luck Boost, Party Mode, Double Daily, Mystery Box

---

## 🚀 **RECENT UPDATES**

### ✨ **Latest Features**
- **Live Event Tracking:** Shout command now shows real-time participant counts
- **Enhanced Ticket System:** Regional support with claim/unclaim functionality
- **Expanded Premium Shop:** 16 temporary items across 4 categories
- **Time String Support:** Natural time parsing (1h, 30m, 2d)
- **Optimized AI:** BleckNephew responses under 500 words for better engagement
- **Advanced Cookie Management:** Percentage removal and special codes

### 🎨 **Design Improvements**
- **Modern Spin Wheel:** Premium typography and gradient effects
- **Professional Embeds:** Consistent branding across all commands
- **Enhanced UI:** Better buttons, modals, and user interactions
- **Responsive Design:** Optimized for all Discord platforms

### 🛡️ **System Enhancements**
- **Permission Overhaul:** Clear role-based access control
- **Database Optimization:** Efficient data management and cleanup
- **Error Handling:** Improved stability and user feedback
- **Performance:** Faster response times and better resource usage

---

## � **Support & Documentation**

### 🔗 **Quick Links**
- **GitHub Repository:** https://github.com/THEREALVANHEL/coal-python-bot.git
- **Command Categories:** 9 major categories with 47 total commands
- **Premium Features:** 16 temporary shop items with auto-cleanup

### 💡 **Getting Help**
- Use `/help` or specific command help for guidance
- Contact moderators for permission-related issues
- Check `/viewsettings` to verify server configuration

**Total Commands: 47** | **Categories: 9** | **Premium Items: 16**

---

*Last Updated: January 2025 - Complete Feature Set*