# 🤖 Coal Python Bot - Complete Command List

*Last Updated: December 2024*

## 📋 Command Overview

This bot features a comprehensive ticket system, 24-hour job tracking, AI chat, economy system, and community features. Commands are organized by category with role permissions clearly marked.

---

## 🎫 **TICKET SYSTEM**

### `/ticket-panel`
- **Function:** Creates a modern ticket panel with integrated admin controls
- **Permissions:** Staff roles (Forgotten One, Overseer, Lead Moderator, Moderator)
- **Features:** 
  - 4 control buttons (Claim, Close, Lock, Unlock)
  - Integrated admin panel (Emergency Ban, Quick Warn, Temp Mute)
  - Auto-ping staff roles when tickets created
  - Modern channel naming system (🔴┃username-ticket → 🟢┃staff-ticket)

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

### `/shop`
- **Function:** View the premium temporary items shop
- **Permissions:** All users
- **Features:** Browse temporary boosts, multipliers, and special items

### `/buy`
- **Function:** Purchase items from the shop
- **Permissions:** All users
- **Features:** Buy temporary boosts, XP multipliers, special perks

### `/coinflip`
- **Function:** Flip a coin and bet coins
- **Permissions:** All users
- **Features:** Gambling mini-game with coin rewards

### `/myitems`
- **Function:** View your active temporary purchases and remaining time
- **Permissions:** All users
- **Features:** Track active boosts and their expiration times

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

### `/talktobleky`
- **Function:** Start a conversation with your nephew Bleky - AI chat system
- **Permissions:** All users
- **Features:** 
  - AI nephew personality (16-17 year old, gaming/tech interests)
  - Conversation memory and context awareness
  - Continue conversation button for ongoing chats
  - Family-friendly casual language

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

### `/askblecknephew`
- **Function:** Ask your nephew BleckNephew anything! (Technical AI assistant)
- **Permissions:** All users
- **Features:** 
  - Professional technical assistance
  - Focused, helpful responses
  - URL extraction and link buttons
  - Optimized for clarity and precision

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
- Ticket system (claim, close, lock, unlock)
- Moderation commands (warn, clear, removewarn)
- Job overview monitoring
- Event management (shout, gamelog, giveaway, announce)
- Settings viewing

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
- Role-based access control
- Integrated admin panels
- Auto-staff pinging
- Transfer system between staff
- Modern UI with emoji indicators

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

*🤖 Coal Python Bot - Your complete Discord server management solution*
*Repository: https://github.com/THEREALVANHEL/coal-python-bot*