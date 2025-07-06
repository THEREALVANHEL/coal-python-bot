# 🤖 COAL BOT - Commands List

## 📋 **Role Permissions Reference**
- **Administrator** - Administrator permission or special admin role
- **Manage Messages** - Manage Messages permission or special admin role  
- **Manage Channels** - Manage Channels permission
- **Manage Roles** - Manage Roles permission or special admin role
- **Manage Guild** - Manage Guild/Server permission
- **Cookie Manager** - Role ID: 1372121024841125888
- **Host Roles** - "🦥 Overseer", "Forgotten one", "🚨 Lead moderator" or special admin role
- **Announce Roles** - Role IDs: 1378338515791904808, 1371003310223654974
- **Moderator Role** - "Moderator 🚨🚓", "🚨 Lead moderator" or special admin role
- **Everyone** - No permissions required

---

## 🎫 **TICKET SYSTEM**

| Command | Function | Permissions |
|---------|----------|-------------|
| `/createticket` | Create a support ticket instantly | Everyone |
| `/ticketpanel` | Create ticket panel in current channel | Administrator |
| `/giveticketroleperms` | Grant ticket support permissions to roles | Administrator |
| `/ticketstats` | View comprehensive ticket system statistics | Manage Channels |
| `/closealltickets` | Emergency: Close all open tickets | Administrator |
| `/ticketdashboard` | View live ticket dashboard with real-time stats | Manage Channels |
| `/ticketmanager` | Advanced ticket management interface for staff | Manage Channels |

---

## �️ **MODERATION**

| Command | Function | Permissions |
|---------|----------|-------------|
| `/addxp` | Add XP to a user | Administrator |
| `/removexp` | Remove XP from a user | Administrator |
| `/modclear` | Delete specified number of messages from channel | Manage Messages |
| `/setlogchannel` | Set the moderation log channel | Administrator |
| `/warn` | Warn a user | Moderator Role |
| `/checkwarnlist` | Check warnings for a user | Moderator Role |
| `/removewarnlist` | Remove specific warning or clear all warnings | Moderator Role |
| `/updateroles` | Update roles based on user's level and cookies | Manage Roles |
| `/roleplay` | Interactive AI roleplay with character persistence | Everyone |
| `/sync` | Force sync all slash commands | Administrator |

---

## 💰 **ECONOMY SYSTEM**

| Command | Function | Permissions |
|---------|----------|-------------|
| `/balance` | Check your coin balance | Everyone |
| `/work` | Independent career progression system | Everyone |
| `/shop` | View the premium temporary items shop | Everyone |
| `/buy` | Purchase premium temporary items | Everyone |
| `/coinflip` | Flip a coin and bet coins | Everyone |
| `/myitems` | View your active temporary purchases | Everyone |

---

## 🍪 **COOKIE SYSTEM**

| Command | Function | Permissions |
|---------|----------|-------------|
| `/cookies` | Check your cookie balance | Everyone |
| `/addcookies` | Add cookies to a user | Cookie Manager |
| `/removecookies` | Remove cookies from a user with selection options | Cookie Manager |
| `/cookiesgiveall` | Give cookies to everyone in server | Cookie Manager |
| `/cookiesremoveall` | Remove all cookies from everyone in server | Cookie Manager |

---

## 🏆 **LEVELING & PROFILE**

| Command | Function | Permissions |
|---------|----------|-------------|
| `/profile` | Show comprehensive profile with level, cookies, job, daily streak | Everyone |
| `/leaderboard` | View all server leaderboards with pagination | Everyone |
| `/daily` | Claim daily XP and coin bonus with streak rewards | Everyone |

---

## � **COMMUNITY & EVENTS**

| Command | Function | Permissions |
|---------|----------|-------------|
| `/suggest` | Submit server improvement suggestions with optional media | Everyone |
| `/shout` | Create event announcement with live participant tracking | Announce Roles |
| `/gamelog` | Log completed game with details and optional picture | Announce Roles |
| `/spinwheel` | Spin enhanced wheel with arrow pointing to winner | Everyone |
| `/userinfo` | View detailed member information | Everyone |
| `/serverinfo` | Show server stats and information | Everyone |
| `/ping` | Check bot's ping to Discord servers | Everyone |
| `/askblecknephew` | Ask BleckNephew AI anything | Everyone |
| `/flip` | Flip a coin - heads or tails | Everyone |
| `/giveaway` | Start giveaway with specified duration and winner count | Announce Roles |
| `/announce` | Create professional pointwise announcement with attachments | Announce Roles |
| `/remind` | Set personal reminders | Everyone |

---

## ⚙️ **SERVER SETTINGS**

| Command | Function | Permissions |
|---------|----------|-------------|
| `/starboard` | Configure starboard settings | Manage Guild |
| `/viewsettings` | View current server configuration | Manage Guild |
| `/quicksetup` | Enhanced setup wizard for all bot functions | Manage Guild |

---

## 🔧 **EVENT COMMANDS** (Alternative)

| Command | Function | Permissions |
|---------|----------|-------------|
| Event `/shout` | Make bot send message to specific channel | Host Roles |
| Event `/gamelog` | Log game event with image support | Host Roles |

---

## 🧪 **UTILITY/TESTING**

| Command | Function | Permissions |
|---------|----------|-------------|
| `/hello` | Basic hello command - test bot response | Everyone |
| `/test` | Simple test command to verify bot responsiveness | Everyone |
| `/ping` | Check bot latency and response time | Everyone |
| `/info` | Show bot information and status | Everyone |
| `/sync` | Manually sync slash commands | Administrator |

---

## � **SUMMARY**

- **Total Commands:** 47
- **Categories:** 8
- **Admin Commands:** 9
- **Moderator Commands:** 3
- **Public Commands:** 25
- **Special Role Commands:** 10

---

*Commands require exact role names or role IDs as specified. Special admin role bypasses most permission checks.*