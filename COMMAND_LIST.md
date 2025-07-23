# 🤖 Coal Python Bot - Complete Command List

*Last Updated: January 2025 - After Major Overhaul*
*⚠️ IMPORTANT: See `DISCORD_PERMISSIONS_REQUIRED.md` for role permission setup*

## 📋 Command Overview

This bot features a comprehensive ticket system, 24-hour job tracking, AI chat, economy system, and community features. Commands are organized by category with role permissions clearly marked.

---

## 🎫 **TICKET SYSTEM**

### `/ticket-panel`
- **Function:** Creates a modern ticket panel with integrated admin controls
- **Permissions:** Administrator only (to create panel), All users (to create tickets)
- **Features:** 
  - 4 control buttons (Claim, Close, Lock, Unlock) - Staff only
  - Integrated admin panel (Emergency Ban, Quick Warn, Temp Mute) - Staff only
  - Auto-ping staff roles when tickets created
  - Modern channel naming system (🔴┃username-ticket → 🟢┃staff-ticket)
  - **FIXED:** Lead Moderator and Moderator now have full channel access
  - Automatic role permissions: read, send, manage messages, manage channels

---

## 💼 **JOB TRACKING & ECONOMY**

### `/work`
- **Function:** Independent career progression system with 24-hour activity tracking
- **Permissions:** All users
- **Features:**
  - 5 job levels: Intern → Junior Developer → Developer → Senior Developer → Team Lead
  - Automatic promotions with visual confirmation
  - 24-hour auto-demotion system for inactivity
  - Earnings: 50-120 coins + XP based on role level

### `/work-policy`
- **Function:** View the 24-hour work policy and requirements
- **Permissions:** All users
- **Features:** Complete guide to job system, warning thresholds, requirements

### `/job-overview`
- **Function:** Management overview of all job role activity
- **Permissions:** Staff only (Lead Moderator, Moderator, Overseer, Forgotten One)
- **Features:** Real-time activity tracking, warning/critical status for all job holders

### `/balance`
- **Function:** Check your shiny coin balance
- **Permissions:** All users
- **Features:** Clean display of current coin balance

### 🆕 `/shop` *(COMPLETELY REWORKED)*
- **Function:** **ENHANCED** shop with banking, slots, and premium items
- **Permissions:** All users
- **Features:** 
  - 🎰 Slots & Gambling items (5x, 10x, 25x spins, Lucky Slot Pass)
  - 🏦 Banking & Financial items (ATM Card, Premium Account, Stock Analysis)
  - 🐾 Pet Supplies, 🚀 Power-Ups, 🔑 Access items, 💎 Premium items

### 🆕 `/inventory` *(REPLACED /myitems)*
- **Function:** **NEW** Comprehensive inventory with banking, pets, stocks overview
- **Permissions:** All users
- **Features:** 
  - 🏦 Banking status (Wallet, Bank, Savings, ATM access)
  - 🐾 Active pet status and stats
  - 📈 Stock portfolio overview
  - 🛍️ Active items by category with quick actions

### 🆕 `/atm`
- **Function:** **NEW** Complete ATM banking system
- **Permissions:** All users (requires ATM card from shop)
- **Features:**
  - 📥 Deposit/📤 Withdraw coins
  - 💸 Transfer to other users (with fees)
  - 💎 Savings account with 2% daily interest
  - 🏦 Complete account overview

### `/buy`
- **Function:** Purchase items from the enhanced shop
- **Permissions:** All users
- **Features:** Buy from categorized shop with banking integration

### `/coinflip`
- **Function:** Flip a coin and bet coins
- **Permissions:** All users
- **Features:** Gambling mini-game with coin rewards

---

## 🏆 **LEVELING & PROFILES**

### `/leaderboard`
- **Function:** View all server leaderboards with working pagination
- **Permissions:** All users
- **Features:** XP, level, cookies, and comprehensive server rankings

### `/profile`
- **Function:** Shows comprehensive profile with level, cookies, job, and daily streak
- **Permissions:** All users (view own), Admins (view others)
- **Features:** Complete user statistics, progress tracking, achievements

### `/daily`
- **Function:** Claim your daily XP and coin bonus with streak rewards
- **Permissions:** All users
- **Features:** Daily rewards, streak multipliers, bonus XP and coins

---

## 🛡️ **MODERATION**

### `/warn`
- **Function:** Warn a user with detailed logging
- **Permissions:** Staff roles (Forgotten One, Overseer, Lead Moderator, Moderator)
- **Features:** Comprehensive warning system with user notifications

### `/warnlist`
- **Function:** Check warnings for a user (visible to everyone)
- **Permissions:** All users
- **Features:** Public warning history display

### `/removewarnlist`
- **Function:** Remove specific warning or clear all warnings for a user
- **Permissions:** Staff roles
- **Features:** Warning management with detailed removal options

### `/modclear`
- **Function:** Deletes a specified number of messages from a channel
- **Permissions:** Staff roles
- **Features:** Bulk message deletion with safety limits

### 🔄 `/talktobleky` *(REVOLUTIONARY UPGRADE)*
- **Function:** **ENHANCED** Chat with your smart nephew Bleky - now with command knowledge!
- **Permissions:** All users
- **Features:** 
  - 🤖 **Full Command Knowledge** - Knows all bot commands and can explain them
  - 🏦 **Banking Data Access** - Can see your financial status and give advice
  - 💬 **Conversation Memory** - Remembers previous chats for better responses
  - 📊 **Personalized Advice** - Based on your progress and stats
  - 🔧 **Interactive Help** - Command assistance and troubleshooting
  - 👥 **More Human-like** - Enhanced personality with genuine helpfulness

---

## 🎉 **COMMUNITY & EVENTS**

### `/suggest`
- **Function:** Submit suggestions to improve the server (with optional media)
- **Permissions:** All users
- **Features:** Suggestion system with media attachment support

### `/shout`
- **Function:** Create detailed event announcements with live participant tracking
- **Permissions:** Staff roles with announce permissions
- **Features:** 
  - Live participant tracking
  - Join/Leave buttons
  - Event management controls (Start, End, Set Time)
  - Host/Co-host/Medic/Guide role assignments

### `/gamelog`
- **Function:** Log completed games with detailed information and optional picture
- **Permissions:** Staff roles with announce permissions
- **Features:** Game documentation, participant tracking, media support

### `/giveaway`
- **Function:** Start a giveaway with specified duration and winner count
- **Permissions:** Staff roles with announce permissions
- **Features:** 
  - Automated winner selection
  - Entry tracking and participation buttons
  - Single comprehensive end message (fixed double reply issue)
  - Duration: 1-10080 minutes, Winners: 1-20

### `/announce`
- **Function:** Creates professional pointwise announcements with optional attachments
- **Permissions:** Staff roles with announce permissions
- **Features:** Professional formatting, media attachments, structured point system

### `/remind`
- **Function:** Set a reminder for yourself
- **Permissions:** All users
- **Features:** 
  - Persistent database storage
  - Time formats: seconds, minutes, hours, days, weeks
  - DM and channel notification fallback
  - Maximum 4 weeks duration

---

## 🎮 **FUN & UTILITY**

### `/spinwheel`
- **Function:** Spin an enhanced wheel with arrow pointing to winner
- **Permissions:** All users
- **Features:** Visual wheel graphics, up to 10 options, random selection

### `/flip`
- **Function:** Flip a coin - heads or tails
- **Permissions:** All users
- **Features:** Visual coin graphics, random outcome

### 🔄 `/trivia` *(ENHANCED)*
- **Function:** **IMPROVED** AI-powered trivia with proper rewards
- **Permissions:** All users
- **Features:** 
  - 🆓 **Free to Play** - No entry fee required
  - 🏆 **Proper Rewards** - 1 coin (easy), 2 coins (medium), 3 coins (hard)
  - 🤖 **AI Generated** questions with better variety
  - 🔄 **No Repeated Questions** system (in development)

### 🔄 `/wordchain` *(FIXED)*
- **Function:** **FIXED** Enhanced word chain with proper validation
- **Permissions:** All users
- **Features:** 
  - ✅ **Fixed Case Sensitivity** - "Ran" and "ran" both work correctly
  - 🤖 **AI Word Validation** - Better authenticity checking
  - ⏰ **Wrong Answer Cooldown** - 5 minutes for invalid words
  - 🎯 **Better Feedback** - Clear error messages and guidance

### 🔄 `/slots` *(ENHANCED)*
- **Function:** **ENHANCED** Play slot machine with custom bet amounts
- **Permissions:** All users
- **Features:** 
  - 💰 **Custom Betting** - 10 to 1,000 coins (was fixed 25)
  - 🎰 **Better Validation** - Amount limits and error checking
  - 🛍️ **Shop Integration** - Buy slot spins in bulk from shop

### `/ping`
- **Function:** Check the bot's ping to Discord servers
- **Permissions:** All users
- **Features:** Real-time latency measurement

### `/serverinfo`
- **Function:** Shows stats and info about the server
- **Permissions:** All users
- **Features:** Comprehensive server statistics and information

---

## ⚙️ **ADMINISTRATION**

### `/addxp`
- **Function:** Add XP to a user
- **Permissions:** Admin only
- **Features:** Manual XP adjustment for users

### `/removexp`
- **Function:** Remove XP from a user
- **Permissions:** Admin only
- **Features:** Manual XP reduction for users

### `/addcoins`
- **Function:** Add coins to a user
- **Permissions:** Admin only
- **Features:** Manual coin adjustment

### `/removecoins`
- **Function:** Remove coins from a user
- **Permissions:** Admin only
- **Features:** Manual coin reduction

### `/addcookies`
- **Function:** Add cookies to a user
- **Permissions:** Manager only
- **Features:** Cookie balance management

### `/removecookies`
- **Function:** Remove cookies from a user with selection options
- **Permissions:** Manager only
- **Features:** Advanced cookie removal with options

### `/cookiesgiveall`
- **Function:** Give cookies to everyone in the server
- **Permissions:** Manager only
- **Features:** Server-wide cookie distribution

### `/removecookiesall`
- **Function:** Remove cookies from everyone in the server
- **Permissions:** Manager only
- **Features:** Server-wide cookie reset

### `/updateroles`
- **Function:** Updates roles based on a user's current level and cookies
- **Permissions:** Admin
- **Features:** Role synchronization system

### `/sync`
- **Function:** Force sync all slash commands
- **Permissions:** Admin only
- **Features:** Command registration and updates

### `/dbhealth`
- **Function:** Check database sync status
- **Permissions:** Admin only
- **Features:** Database connectivity and sync verification

---

## 🔧 **SETTINGS & CONFIGURATION**

### `/starboard`
- **Function:** Configure the starboard settings
- **Permissions:** Admin
- **Features:** Star reaction system configuration

### `/viewsettings`
- **Function:** View current server settings and configuration
- **Permissions:** Staff roles
- **Features:** Complete settings overview

### `/quicksetup`
- **Function:** Enhanced setup wizard for all bot functions
- **Permissions:** Admin
- **Features:** Guided bot configuration process

### `/setlog`
- **Function:** Set the moderation and logging channel for all server events
- **Permissions:** Admin
- **Features:** Centralized logging configuration

---

## 📊 **ROLE PERMISSIONS SUMMARY**

### **👑 Admin (Administrator)**
- All commands
- User management (XP, coins, roles)
- Bot configuration and sync
- Database health monitoring

### **🛠️ Staff Roles (Forgotten One, Overseer, Lead Moderator, Moderator)**
- **Ticket system** (claim, close, lock, unlock)
- **Ticket admin panel** (emergency ban, quick warn, temp mute)
- **Full ticket channel access** (read, send, manage messages, manage channels)
- **Moderation commands** (warn, clear, removewarn)
- **Job overview monitoring**
- **Event management** (shout, gamelog, giveaway, announce)
- **Settings viewing**

### **👥 Manager Roles**
- Cookie management (add, remove, server-wide operations)
- All user commands

### **🧑‍💼 Job Role Holders**
- Work command access
- Enhanced earnings based on job level
- 24-hour activity requirements

### **👤 All Users**
- Basic economy (balance, shop, buy, coinflip, myitems)
- Leveling system (profile, daily, leaderboard)
- Community features (suggest, AI chat)
- Fun commands (flip, spinwheel, ping, serverinfo)
- Personal reminders

---

## 🚀 **SYSTEM FEATURES**

### **🎫 Modern Ticket System**
- **Role-based access control** (automatic permission assignment)
- **Integrated admin panels** (ban, warn, mute directly from tickets)
- **Auto-staff pinging** (all 4 staff roles notified)
- **Transfer system** between staff (claim/unlock system)
- **Modern UI** with emoji indicators
- **FIXED:** Lead Moderator and Moderator now have full channel permissions
- **Enhanced permissions:** read, send, manage messages, manage channels, mention everyone

### **⏰ 24-Hour Job Tracking**
- Automatic activity monitoring
- Progressive warning system (12-20 hour marks)
- Auto-demotion after 24 hours of inactivity
- Real-time status tracking
- DM notifications and staff alerts

### **🤖 AI Integration**
- BleckNephew technical assistant
- TalkToBleky nephew chat with memory
- Context-aware responses
- Conversation continuation

### **💾 Database Persistence**
- All user data saved
- Reminder system persistence
- Activity tracking
- Warning history
- Economy data

### **🎨 Modern UI/UX**
- Emoji-based design
- Professional embeds
- Interactive buttons
- Visual feedback
- Clean, intuitive interfaces

---

## ❌ **REMOVED/MERGED COMMANDS**

### Commands that have been **removed** or **merged**:

- ~~`/myitems`~~ → **Replaced with** `/inventory` (enhanced functionality)
- ~~`/askblecknephew`~~ → **Merged into** `/talktobleky` (combined AI system)
- ~~`/dailychallenge`~~ → **Removed completely** (streamlined experience)
- ~~`/8ball`~~ → **Removed completely** (focus on core features)

### 🆕 **NEW MAJOR FEATURES**

- **🏦 Complete Banking System** - ATM, deposits, withdrawals, transfers, savings
- **🤖 Enhanced AI Chat** - Command knowledge, banking integration, memory
- **🛍️ Professional Shop** - Categorized items, banking integration
- **📋 Comprehensive Inventory** - Real-time status of all user assets
- **🎮 Improved Games** - Better rewards, fixed issues, enhanced validation

---

*🤖 Coal Python Bot - Your complete Discord server management solution*
*Repository: https://github.com/THEREALVANHEL/coal-python-bot*
*Last Major Update: January 2025*