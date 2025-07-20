# 🤖 Coal Python Bot - Complete Command List

## 🏠 BASIC & UTILITY COMMANDS

- **/test** - Simple test command to verify bot functionality
- **/hello** - Basic hello command and response test  
- **/ping** - Check bot latency and response time
- **/info** - Show bot information and status
- **/serverinfo** - Shows server stats and information

**Permissions: Everyone**

---

## 👤 PROFILE & PROGRESSION COMMANDS

- **/profile** [user] - Shows comprehensive profile with level, cookies, job, and daily streak
- **/daily** - Claim daily XP and coin bonus with streak rewards
- **/balance** - Check your shiny coin balance
- **/cookies** [user] - Check your delicious cookie balance
- **/work** - Independent career progression system - work your way up!
- **/myitems** - View your active temporary purchases and their remaining time

**Permissions: Everyone**

---

## 🏆 LEADERBOARDS & RANKINGS

- **/leaderboard** [type] [page] - View server leaderboards with pagination
  - `xp` - XP & Levels leaderboard
  - `cookies` - Cookies leaderboard  
  - `coins` - Coins leaderboard
  - `streak` - Daily streaks leaderboard

**Permissions: Everyone**

---

## 🛒 ECONOMY & SHOP COMMANDS

- **/shop** - View the premium temporary items shop
- **/buy** [item] [duration] - Purchase temporary items with coins
- **/coinflip** [amount] - Flip a coin and bet coins

**Permissions: Everyone**

---

## 🎪 FUN & ENTERTAINMENT COMMANDS

- **/flip** - Flip a coin - heads or tails
- **/spinwheel** - Spin an enhanced wheel with arrow pointing to winner
- **/8ball** [question] - Ask the magic 8-ball a question
- **/fortune** - Get your daily fortune
- **/askblecknephew** [question] - Ask your nephew BleckNephew anything!
- **/talktobleky** - Start a conversation with your nephew Bleky
- **/rps** - Rock Paper Scissors game
- **/slots** [bet] - Play slot machine with betting
- **/trivia** - Answer trivia questions for rewards
- **/tournament** [game] - Join tournaments (Coming Soon)
- **/wordchain** - Word association game
- **/dailychallenge** - Complete daily challenges for bonus rewards
- **/inspire** - Get inspirational quotes
- **/weather** [location] - Get weather information
- **/facts** - Get random fun facts
- **/rng** [min] [max] - Generate random numbers
- **/calculate** [expression] - Calculate mathematical expressions

**Permissions: Everyone**

---

## 🐾 PET SYSTEM COMMANDS

- **/pet** - Manage your pet dashboard
- **/adopt** - Adopt a new pet companion
- **/feed** [food] - Feed your pet to keep it healthy
- **/play** [activity] - Play with your pet for happiness

**Permissions: Everyone**

---

## 📈 STOCK MARKET COMMANDS

- **/stocks** - View current stock market prices
- **/buystock** [symbol] [shares] - Buy stocks (renamed from /buy to avoid conflict)
- **/sell** [symbol] [shares] - Sell your stocks
- **/portfolio** - View your stock portfolio and performance
- **/market** - Market overview and analysis

**Permissions: Everyone**

---

## 🏦 BANKING SERVICES

- **/bank** - Main banking dashboard and account summary
- **/deposit** [amount] - Deposit coins into your bank account (safe from gambling)
- **/withdraw** [amount] - Withdraw coins from your bank account
- **/loan** [amount] [type] - Apply for loans with different interest rates
  - Types: `personal`, `business`, `emergency`
- **/creditcard** - Apply for credit cards with spending limits
- **/creditscore** - View detailed credit analysis and recommendations

**Permissions: Everyone**

---

## 📅 EVENTS & COMMUNITY COMMANDS

- **/shout** [title] [description] [host] [co_host] [medic] [guide] - Create detailed event announcements
- **/gamelog** [game] [result] [participants] [image] - Log completed games with details
- **/giveaway** [duration] [winners] [prize] - Start a giveaway
- **/announce** [title] [content] - Create professional pointwise announcements
- **/remind** [time] [message] - Set a reminder for yourself
- **/suggest** [suggestion] [media] - Submit suggestions with optional media
- **/poll** [question] [options] - Create polls for community voting

**Permissions: Everyone**

---

## 🎫 TICKET SYSTEM COMMANDS

- **/ticket-panel** - Create a simple ticket panel (Admin only)
- **/close** - Close current ticket (Staff only)

**Permissions:**
- ticket-panel: Administrator only
- close: Forgotten One, Overseer, Lead Moderator, Moderator

---

## 🔨 MODERATION COMMANDS

- **/warn** [user] [reason] - Warn a user with logging
- **/warnlist** [user] - Check warnings for a user (public view)
- **/removewarnlist** [user] [warning_index] [reason] - Remove/clear user warnings
- **/modclear** [amount] - Delete messages (1-100 limit)
- **/setlog** [channel] - Set moderation and logging channel

**Permissions: Forgotten One, Overseer, Lead Moderator, Moderator**

---

## ⚙️ ADMINISTRATION COMMANDS

- **/addxp** [user] [amount] - Add XP to a user
- **/removexp** [user] [amount] - Remove XP from a user
- **/addcoins** [user] [amount] - Add coins to a user  
- **/removecoins** [user] [amount] - Remove coins from a user
- **/updateroles** [user] - Update roles based on level and cookies
- **/sync** - Force sync all slash commands
- **/dbhealth** - Check database sync status and performance

**Permissions: Administrator only**

---

## 🍪 COOKIE MANAGEMENT COMMANDS

- **/addcookies** [user] [amount] - Add cookies to a user
- **/removecookies** [user] [amount] - Remove cookies from a user
- **/cookiesgiveall** [amount] - Give cookies to everyone in server
- **/removecookiesall** [amount] - Remove cookies from everyone in server

**Permissions: CookiesManager role**

---

## 🎯 HOST & EVENT COMMANDS

- **/shout** [message] [channel] - Make bot send message to specific channel
- **/gamelog** [game] [result] [image] - Log game events with image support

**Permissions: Head Host and Host roles**

---

## 📊 SETTINGS & CONFIGURATION

- **/starboard** [channel] [emoji] [threshold] - Configure starboard settings
- **/viewsettings** - View current server settings and configuration
- **/quicksetup** - Enhanced setup wizard for all bot functions
- **/timezone** [timezone] - Set server timezone

**Permissions:**
- Configuration commands: Administrator only
- viewsettings: Everyone

---

## 💼 JOB & WORK TRACKING

- **/work-policy** - View 24-hour work policy and requirements
- **/job-overview** - Management overview of all job role activity

**Permissions:**
- work-policy: Everyone
- job-overview: Moderator, Lead Moderator, Overseer

---

## 🔧 SYSTEM & PERFORMANCE

- **/dashboard** - Personal user dashboard with statistics
- **/security-status** - View security monitoring status
- **/security-audit** - Run security audit (Admin only)
- **/clear-rate-limits** - Clear rate limiting data (Admin only)

**Permissions:**
- dashboard: Everyone
- security commands: Administrator only

---

## 🎮 ADDITIONAL GAMES & UTILITIES

- **/avatar** [user] - Display user's avatar
- **/userinfo** [user] - Detailed user information
- **/market** - Economy market overview

**Permissions: Everyone**

---

# 📊 COMMAND STATISTICS

- **Total Commands**: 85+
- **Public Commands**: 65+
- **Staff Commands**: 10+
- **Admin Commands**: 10+

---

# 🎯 NEW COMMANDS ADDED

## ✅ Recently Added:
- `/test` - Bot functionality test
- `/hello` - Basic greeting command
- `/info` - Bot information display
- `/loan` - Banking loan system
- `/creditcard` - Credit card applications
- `/creditscore` - Credit analysis
- `/tournament` - Tournament system (Coming Soon)
- `/dailychallenge` - Daily challenge system

## ❌ Commands Removed:
- None - All existing commands maintained

---

*Last Updated: January 20, 2025*
*Coal Python Bot v2.0 - Complete Feature Set*