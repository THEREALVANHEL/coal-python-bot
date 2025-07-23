# 🤖 Coal Python Bot

A feature-rich Discord bot with economy, games, moderation, and AI chat capabilities.

## 🚀 Recent Updates

### ✨ New Features
- **ATM Command**: Now visible to all users (no longer private)
- **Command Expiration**: ATM buttons expire after single use to prevent reuse
- **Talktosensei**: Renamed from `talktobleky` with updated wise mentor personality
- **Askblecknephew**: New AI Q&A command with conversation memory

### 🧹 Repository Cleanup
- Removed 50+ unnecessary documentation files
- Cleaned up redundant Python utility files
- Streamlined repository structure for better maintainability

### 🔧 Technical Improvements
- Enhanced ATM view with disable functionality after use
- Improved conversation memory system for AI commands
- Better error handling and user feedback

## 📋 Available Commands

### 💰 Economy & Banking
- `/atm` - Access ATM services (now visible to all)
- `/balance` - Check your balance
- `/shop` - Browse items
- `/deposit` - Deposit coins to bank
- `/withdraw` - Withdraw from bank
- `/transfer` - Transfer coins to other users

### 🤖 AI Chat Commands
- `/talktosensei` - Chat with your wise sensei mentor
- `/askblecknephew` - Ask Bleky any question with conversation memory

### 🎮 Games & Fun
- `/trivia` - Play trivia games
- `/slots` - Play slot machine
- `/coinflip` - Flip a coin
- `/rps` - Rock paper scissors
- `/spinwheel` - Spin the wheel

### 📈 Stocks & Pets
- `/stocks` - View stock market
- `/portfolio` - Check your investments
- `/pet` - Manage your virtual pet

### 🛡️ Moderation (Staff Only)
- `/warn` - Warn a user
- `/ticket-panel` - Create ticket system
- Various moderation tools

## 🔧 Setup & Deployment

### Requirements
- Python 3.11+
- Discord Bot Token
- MongoDB URI
- Gemini AI API Key (for AI commands)

### Environment Variables
```env
DISCORD_TOKEN=your_discord_bot_token
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_gemini_api_key
```

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run the bot: `python main.py`

### Command Sync
To sync commands to Discord and remove non-existent ones:
```bash
python sync_discord_commands.py
```

## 📁 Project Structure
```
├── main.py                 # Main bot file
├── requirements.txt        # Dependencies
├── runtime.txt            # Python version
├── cogs/                  # Command modules
│   ├── economy.py         # Economy commands
│   ├── moderation.py      # Moderation & AI commands
│   └── ...               # Other command modules
├── core/                  # Core systems
│   ├── database.py        # Database management
│   ├── config.py          # Configuration
│   └── ...               # Other core modules
└── assets/               # Static assets
```

## 🎯 Key Features

- **Economy System**: Complete banking with ATM, savings, loans
- **AI Integration**: Smart chat with conversation memory
- **Game Suite**: Multiple mini-games and entertainment
- **Moderation Tools**: Comprehensive server management
- **Stock Market**: Virtual trading system
- **Pet System**: Virtual pet management
- **Ticket System**: Support ticket management
- **Analytics**: Performance tracking and insights

## 🔄 Recent Changes Summary

The bot has been significantly improved with:
1. **Enhanced User Experience**: ATM responses now visible to all
2. **Better Command Management**: Buttons expire after use
3. **AI Improvements**: New AI chat command with memory
4. **Code Quality**: Cleaner repository structure
5. **Maintainability**: Reduced technical debt

---

*Built with ❤️ using Discord.py and enhanced with AI capabilities*