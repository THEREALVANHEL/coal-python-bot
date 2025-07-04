# 🤖 **BLECKOPS DISCORD BOT - COMPLETE COMMAND LIST**

## 👑 **Server Management & Moderation**
| Command | Description | Permissions Required |
|---------|-------------|---------------------|
| `/modclear` | 🗑️ Deletes a specified number of messages from a channel | Manage Messages |
| `/announce` | 📢 Creates and sends a formatted announcement | Administrator |
| `/updateroles` | 🔄 Updates roles based on a user's current level and cookies | Manage Roles |
| `/warn` | ⚠️ Issue a warning to a user | Moderator |
| `/warnlist` | 📜 List a user's warnings | Moderator |
| `/removewarnlist` | 🗑️ Clear all warnings for a user | Moderator |

## 🍪 **Cookie & Economy Commands**
| Command | Description | Usage |
|---------|-------------|-------|
| `/cookies` | 🍪 View your or another user's cookie balance | `/cookies [user]` |
| `/cookietop` | 🏆 Shows the top 10 users with the most cookies | `/cookietop` |
| `/cookiesrank` | 🏅 Displays your current rank in the cookie leaderboard | `/cookiesrank` |
| `/addcookies` | ➕ Adds cookies to a user (Manager only) | `/addcookies <user> <amount>` |
| `/removecookies` | ➖ Removes cookies from a user (Manager only) | `/removecookies <user> <amount>` |
| `/cookiesgiveall` | 🎉 Gives cookies to everyone in the server (Manager only) | `/cookiesgiveall <amount>` |
| `/donatecookies` | 🎁 Give some of your cookies to another user | `/donatecookies <user> <amount>` |
| `/coinflipbet` | 🪙 Bet cookies on a coin flip! | `/coinflipbet <amount> <heads/tails>` |

## 🚀 **Leveling & Profile Commands**
| Command | Description | Usage |
|---------|-------------|-------|
| `/rank` | 📊 Shows your current level, XP, and server rank | `/rank [user]` |
| `/leveltop` | 🥇 Displays the top 10 users by level | `/leveltop` |
| `/profile` | 👤 Shows your level and cookie stats in one profile | `/profile [user]` |
| `/chatlvlup` | ✨ Announces your latest level-up in chat | `/chatlvlup` |
| `/daily` | 🌞 Claim your daily XP and build a streak! | `/daily` |
| `/streaktop` | 🔥 Show the top users with the highest daily streaks | `/streaktop` |

## 🎉 **Fun & Community Commands**
| Command | Description | Usage |
|---------|-------------|-------|
| `/suggest` | 💡 Submit a suggestion to the server | `/suggest <suggestion>` |
| `/spinawheel` | 🎡 Spin a wheel with up to 10 options | `/spinawheel <title> <options>` |
| `/userinfo` | ℹ️ View detailed info about a server member | `/userinfo [user]` |
| `/serverinfo` | 📈 Shows stats and info about the server | `/serverinfo` |
| `/ping` | 🏓 Check the bot's ping to Discord servers | `/ping` |
| `/askblecknephew` | 🤔 Ask Bleck Nephew anything! (Powered by AI) | `/askblecknephew <question>` |
| `/flip` | 🪙 Flip a coin (heads or tails) | `/flip` |
| `/poll` | 📊 Create a simple poll with reactions | `/poll <question> <options>` |

## 🎮 **NEW Fun Commands**
| Command | Description | Usage |
|---------|-------------|-------|
| `/8ball` | 🎱 Ask the magic 8-ball a question! | `/8ball <question>` |
| `/joke` | 😂 Get a random joke to brighten your day! | `/joke` |
| `/quote` | ✨ Get an inspirational quote! | `/quote` |
| `/compliment` | 💝 Give someone a nice compliment! | `/compliment [user]` |
| `/truth` | 🤔 Get a truth question for truth or dare! | `/truth` |
| `/dare` | 💪 Get a dare challenge for truth or dare! | `/dare` |
| `/trivia` | 🧠 Answer a random trivia question! | `/trivia` |

## 🎪 **Event & Host Commands**
| Command | Description | Permissions Required |
|---------|-------------|---------------------|
| `/shout` | 📣 Make the bot send a message to a specific channel | Host |
| `/gamelog` | 🎮 Log a game event or result, with image support | Host |

## ⚙️ **Settings Commands**
| Command | Description | Permissions Required |
|---------|-------------|---------------------|
| `/setsuggestionchannel` | Set the channel for suggestions | Administrator |
| `/setlevelingchannel` | Set the channel for level-up announcements | Administrator |
| `/setmodlogchannel` | Set the channel for moderation logs | Administrator |
| `/showsettings` | Display current channel settings | Administrator |

---

## 🚀 **How to Sync Commands Instantly**

If commands aren't showing up in Discord, run this:

```bash
python sync_commands.py
```

This will:
- ✅ Load all cogs
- ✅ Sync commands to your guild instantly
- ✅ List all available commands
- ✅ Make commands appear immediately in Discord

---

## 🎯 **Quick Setup Checklist**

1. **Set up channels** using `/setsuggestionchannel`, `/setlevelingchannel`, etc.
2. **Run sync script** if commands don't appear: `python sync_commands.py`
3. **Test commands** starting with `/ping` and `/userinfo`
4. **Have fun!** Try `/8ball`, `/joke`, `/coinflipbet`, and more!

---

## 🔧 **Bot Features**

- **Auto Leveling**: Users gain XP from chatting
- **Cookie Economy**: Earn cookies, donate them, bet them!
- **Daily Streaks**: Build streaks with `/daily` for bonus XP
- **Fun Activities**: Games, jokes, trivia, truth or dare
- **Smart Moderation**: Warnings, message clearing, announcements
- **AI Integration**: Ask questions with `/askblecknephew`

---

**🎉 BLECKOPS ON TOP! 🎉**