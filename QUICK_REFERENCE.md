# 🚀 Quick Reference: Commands & Permissions

## 🎫 **TICKET SYSTEM**
| Command | Function | Who Can Use | Required Discord Permissions |
|---------|----------|-------------|------------------------------|
| `/ticket-panel` | Create ticket panel | Administrators | Administrator |
| **Ticket Buttons** | Claim/Close/Lock/Unlock | **4 Staff Roles:** Forgotten One, Overseer, Lead Moderator, Moderator | View Channels, Send Messages, Manage Messages, Manage Channels, Mention Everyone |
| **Admin Panel** | Emergency Ban/Quick Warn/Temp Mute | **4 Staff Roles:** Forgotten One, Overseer, Lead Moderator, Moderator | Ban Members, Kick Members, Moderate Members |

## 💼 **JOB & ECONOMY**
| Command | Function | Who Can Use | Required Discord Permissions |
|---------|----------|-------------|------------------------------|
| `/work` | Career progression | All Users | None |
| `/work-policy` | View policy | All Users | None |
| `/job-overview` | Monitor all jobs | **4 Staff Roles** | View Channels |
| `/balance` | Check coins | All Users | None |
| `/shop` | View items | All Users | None |
| `/buy` | Purchase items | All Users | None |
| `/coinflip` | Gambling game | All Users | None |
| `/myitems` | View purchases | All Users | None |

## 🛡️ **MODERATION**
| Command | Function | Who Can Use | Required Discord Permissions |
|---------|----------|-------------|------------------------------|
| `/warn` | Warn users | **4 Staff Roles** | Kick Members |
| `/warnlist` | View warnings | All Users | None |
| `/removewarnlist` | Remove warnings | **4 Staff Roles** | Kick Members |
| `/modclear` | Bulk delete messages | **4 Staff Roles** | Manage Messages |
| `/talktobleky` | AI nephew chat | All Users | None |

## 🎉 **EVENTS & COMMUNITY**
| Command | Function | Who Can Use | Required Discord Permissions |
|---------|----------|-------------|------------------------------|
| `/suggest` | Submit suggestions | All Users | None |
| `/shout` | Event announcements | **4 Staff Roles** | Mention Everyone |
| `/gamelog` | Log games | **4 Staff Roles** | Send Messages |
| `/giveaway` | Start giveaways | **4 Staff Roles** | Mention Everyone |
| `/announce` | Official announcements | **4 Staff Roles** | Mention Everyone |
| `/remind` | Set reminders | All Users | None |

## 🎮 **FUN & UTILITY**
| Command | Function | Who Can Use | Required Discord Permissions |
|---------|----------|-------------|------------------------------|
| `/spinwheel` | Spin wheel | All Users | None |
| `/flip` | Coin flip | All Users | None |
| `/askblecknephew` | Technical AI | All Users | None |
| `/ping` | Bot latency | All Users | None |
| `/serverinfo` | Server stats | All Users | None |
| `/profile` | User profile | All Users | None |
| `/leaderboard` | Rankings | All Users | None |
| `/daily` | Daily rewards | All Users | None |

## ⚙️ **ADMINISTRATION**
| Command | Function | Who Can Use | Required Discord Permissions |
|---------|----------|-------------|------------------------------|
| `/addxp` | Add XP | Administrators | Administrator |
| `/removexp` | Remove XP | Administrators | Administrator |
| `/addcoins` | Add coins | Administrators | Administrator |
| `/removecoins` | Remove coins | Administrators | Administrator |
| `/sync` | Sync commands | Administrators | Administrator |
| `/dbhealth` | Database check | Administrators | Administrator |
| `/starboard` | Configure starboard | Administrators | Administrator |
| `/viewsettings` | View settings | **4 Staff Roles** | None |
| `/quicksetup` | Bot setup | Administrators | Administrator |
| `/setlog` | Set log channel | Administrators | Administrator |

---

## 🔑 **THE 4 STAFF ROLES**
These roles have special access to ticket system and moderation:
- 🔥 **Forgotten One**
- 🔱 **Overseer** 
- ⚡ **Lead Moderator**
- 🛡️ **Moderator**

## ⚠️ **CRITICAL SETUP**
1. **See `DISCORD_PERMISSIONS_REQUIRED.md`** for exact Discord permissions needed
2. **Staff roles MUST have all required permissions** for buttons to work
3. **Bot needs Administrator permission** (or all permissions listed in guide)
4. **Role hierarchy:** Bot role must be ABOVE staff roles

---

*Fixed Issues: Lead Moderator & Moderator button access, role name matching, permission verification*