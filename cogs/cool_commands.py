import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
import random
import asyncio
import aiohttp
from datetime import datetime, timedelta
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class CoolCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="inspire", description="💫 Get an inspirational quote to boost your day!")
    async def inspire(self, interaction: discord.Interaction):
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Code is poetry written for machines. - Anonymous",
            "Programming isn't about what you know; it's about what you can figure out. - Chris Pine",
            "The best error message is the one that never shows up. - Thomas Fuchs",
            "Any fool can write code that a computer can understand. Good programmers write code that humans can understand. - Martin Fowler",
            "First, solve the problem. Then, write the code. - John Johnson",
            "Experience is the name everyone gives to their mistakes. - Oscar Wilde",
            "Java is to JavaScript what car is to Carpet. - Chris Heilmann",
            "Programming is the art of algorithm design and the craft of debugging errant code. - Ellen Ullman",
            "Talk is cheap. Show me the code. - Linus Torvalds",
            "The best way to get a project done faster is to start sooner. - Jim Highsmith",
            "Debugging is twice as hard as writing the code in the first place. - Brian W. Kernighan",
            "Code never lies, comments sometimes do. - Ron Jeffries",
            "Simplicity is the ultimate sophistication. - Leonardo da Vinci"
        ]
        
        quote = random.choice(quotes)
        author = quote.split(" - ")[-1]
        text = " - ".join(quote.split(" - ")[:-1])
        
        embed = discord.Embed(
            title="💫 Daily Inspiration",
            description=f"*\"{text}\"*",
            color=0xf39c12
        )
        embed.add_field(name="📝 Author", value=f"**{author}**", inline=True)
        embed.set_footer(text="✨ Keep coding and stay inspired!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="🎱 Ask the magic 8-ball a question!")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        if not question.endswith('?'):
            await interaction.response.send_message("❓ Please ask a proper question ending with '?'", ephemeral=True)
            return
            
        responses = [
            "🟢 It is certain",
            "🟢 Without a doubt", 
            "🟢 Yes definitely",
            "🟢 You may rely on it",
            "🟢 As I see it, yes",
            "🟢 Most likely",
            "🟢 Outlook good",
            "🟢 Yes",
            "🟢 Signs point to yes",
            "🟡 Reply hazy, try again",
            "🟡 Ask again later",
            "🟡 Better not tell you now",
            "🟡 Cannot predict now",
            "🟡 Concentrate and ask again",
            "🔴 Don't count on it",
            "🔴 My reply is no",
            "🔴 My sources say no",
            "🔴 Outlook not so good",
            "🔴 Very doubtful"
        ]
        
        answer = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=0x000000
        )
        embed.add_field(name="❓ Your Question", value=question, inline=False)
        embed.add_field(name="🔮 Answer", value=answer, inline=False)
        embed.set_footer(text="🎱 The magic 8-ball has spoken!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fortune", description="🔮 Get your daily fortune!")
    async def fortune(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = db.get_user_data(user_id)
        last_fortune = user_data.get('last_fortune', 0)
        current_time = datetime.now().timestamp()
        
        # Check if already got fortune today (24 hours)
        if current_time - last_fortune < 86400:
            time_left = 86400 - (current_time - last_fortune)
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            await interaction.response.send_message(
                f"🕐 You've already received your daily fortune! Come back in {hours}h {minutes}m", 
                ephemeral=True
            )
            return
        
        fortunes = [
            "🌟 Great fortune awaits you today!",
            "💰 Unexpected wealth will come your way",
            "❤️ Love and friendship surround you",
            "🎯 Your goals are within reach",
            "🌈 After rain comes sunshine",
            "🔥 Your passion will lead to success",
            "🎭 A creative opportunity approaches",
            "🌱 Growth comes from challenges",
            "🎪 Adventure calls your name",
            "⚡ Energy and enthusiasm guide you",
            "🎨 Express yourself boldly today",
            "🎵 Harmony will enter your life",
            "🎪 Embrace the unexpected",
            "🌺 Beauty blooms where you plant kindness",
            "🏆 Victory comes to the persistent"
        ]
        
        fortune = random.choice(fortunes)
        
        # Give random bonus coins (10-50)
        bonus_coins = random.randint(10, 50)
        db.add_coins(user_id, bonus_coins)
        db.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_fortune": current_time}},
            upsert=True
        )
        
        embed = discord.Embed(
            title="🔮 Daily Fortune",
            description=fortune,
            color=0x9b59b6
        )
        embed.add_field(name="🎁 Bonus", value=f"+{bonus_coins} coins!", inline=True)
        embed.set_footer(text="🔮 Come back tomorrow for another fortune!")
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rng", description="🎲 Generate random numbers or pick from a list!")
    async def random_number(self, interaction: discord.Interaction, 
                          minimum: int = 1, maximum: int = 100, 
                          choices: str = None):
        
        if choices:
            # Pick from list
            choice_list = [choice.strip() for choice in choices.split(',')]
            if len(choice_list) < 2:
                await interaction.response.send_message("❌ Please provide at least 2 choices separated by commas", ephemeral=True)
                return
            
            selected = random.choice(choice_list)
            
            embed = discord.Embed(
                title="🎯 Random Choice",
                description=f"From your options, I choose:\n**{selected}**",
                color=0x3498db
            )
            embed.add_field(name="📋 Your Options", value=", ".join(choice_list), inline=False)
        else:
            # Generate random number
            if minimum >= maximum:
                await interaction.response.send_message("❌ Minimum must be less than maximum", ephemeral=True)
                return
            
            if maximum - minimum > 1000000:
                await interaction.response.send_message("❌ Range too large! Maximum range is 1,000,000", ephemeral=True)
                return
            
            number = random.randint(minimum, maximum)
            
            embed = discord.Embed(
                title="🎲 Random Number",
                description=f"Your random number is: **{number:,}**",
                color=0xe74c3c
            )
            embed.add_field(name="📊 Range", value=f"{minimum:,} - {maximum:,}", inline=True)
        
        embed.set_footer(text="🎲 Powered by true randomness!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="weather", description="🌤️ Get weather information for any city!")
    async def weather(self, interaction: discord.Interaction, city: str):
        # This is a simplified weather command - in production, you'd use a real weather API
        await interaction.response.send_message(
            "🌤️ Weather feature coming soon! This would integrate with a weather API to show real weather data.",
            ephemeral=True
        )

    @app_commands.command(name="facts", description="🧠 Learn interesting random facts!")
    async def facts(self, interaction: discord.Interaction):
        facts = [
            "A group of flamingos is called a 'flamboyance'",
            "Honey never spoils. Archaeologists have found 3000-year-old honey that's still edible",
            "The shortest war in history lasted 38-45 minutes (Anglo-Zanzibar War of 1896)",
            "A single cloud can weigh more than a million pounds",
            "Bananas are berries, but strawberries aren't",
            "There are more possible chess games than atoms in the observable universe",
            "Octopuses have three hearts and blue blood",
            "The human brain uses about 20% of the body's total energy",
            "A group of pandas is called an 'embarrassment'",
            "The longest recorded flight of a chicken is 13 seconds",
            "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid",
            "A day on Venus is longer than a year on Venus",
            "The word 'set' has the most different meanings in the English language",
            "Sharks have existed longer than trees",
            "There are more trees on Earth than stars in the Milky Way galaxy"
        ]
        
        fact = random.choice(facts)
        
        embed = discord.Embed(
            title="🧠 Random Fact",
            description=fact,
            color=0x2ecc71
        )
        embed.set_footer(text="🤓 The more you know!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="flip", description="🪙 Flip a coin or multiple coins!")
    async def flip_coin(self, interaction: discord.Interaction, count: int = 1):
        if count < 1 or count > 10:
            await interaction.response.send_message("❌ You can flip 1-10 coins at a time", ephemeral=True)
            return
        
        results = []
        heads_count = 0
        tails_count = 0
        
        for i in range(count):
            result = random.choice(['Heads', 'Tails'])
            results.append(result)
            if result == 'Heads':
                heads_count += 1
            else:
                tails_count += 1
        
        embed = discord.Embed(
            title="🪙 Coin Flip Results",
            color=0xf1c40f
        )
        
        if count == 1:
            emoji = "👑" if results[0] == "Heads" else "🔹"
            embed.description = f"{emoji} **{results[0]}**!"
        else:
            result_text = ", ".join(results)
            embed.add_field(name="📊 Results", value=result_text, inline=False)
            embed.add_field(name="👑 Heads", value=str(heads_count), inline=True)
            embed.add_field(name="🔹 Tails", value=str(tails_count), inline=True)
            
            if heads_count == tails_count:
                embed.add_field(name="🎯 Outcome", value="Perfect tie!", inline=True)
            elif heads_count > tails_count:
                embed.add_field(name="🎯 Outcome", value="Heads wins!", inline=True)
            else:
                embed.add_field(name="🎯 Outcome", value="Tails wins!", inline=True)
        
        embed.set_footer(text="🪙 Fair and random!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="calculate", description="🧮 Perform basic calculations!")
    async def calculate(self, interaction: discord.Interaction, expression: str):
        try:
            # Security: Only allow basic math operations
            allowed_chars = set('0123456789+-*/()%. ')
            if not all(char in allowed_chars for char in expression):
                await interaction.response.send_message("❌ Only basic math operations are allowed (+, -, *, /, %, parentheses)", ephemeral=True)
                return
            
            # Prevent complex expressions
            if len(expression) > 100:
                await interaction.response.send_message("❌ Expression too long! Keep it under 100 characters", ephemeral=True)
                return
            
            # Evaluate safely
            result = eval(expression)
            
            embed = discord.Embed(
                title="🧮 Calculator",
                color=0x3498db
            )
            embed.add_field(name="📝 Expression", value=f"`{expression}`", inline=False)
            embed.add_field(name="🎯 Result", value=f"**{result:,}**", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except ZeroDivisionError:
            await interaction.response.send_message("❌ Cannot divide by zero!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("❌ Invalid expression! Please check your math.", ephemeral=True)

    @app_commands.command(name="poll", description="📊 Create a quick poll!")
    async def quick_poll(self, interaction: discord.Interaction, question: str, 
                        option1: str, option2: str, option3: str = None, option4: str = None):
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        
        if len(question) > 200:
            await interaction.response.send_message("❌ Question too long! Keep it under 200 characters", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Quick Poll",
            description=f"**{question}**",
            color=0x9b59b6
        )
        
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        
        for i, option in enumerate(options):
            embed.add_field(name=f"{emojis[i]} Option {i+1}", value=option, inline=True)
        
        embed.set_footer(text=f"📊 Poll by {interaction.user.display_name} • React to vote!")
        
        message = await interaction.response.send_message(embed=embed)
        
        # Add reactions
        for i in range(len(options)):
            await message.edit(embed=embed)  # Get the message object
            try:
                await (await interaction.original_response()).add_reaction(emojis[i])
            except:
                pass

    @app_commands.command(name="timezone", description="🌍 Get current time in different timezones!")
    async def timezone(self, interaction: discord.Interaction, timezone: str = "UTC"):
        timezones = {
            "UTC": 0, "GMT": 0,
            "EST": -5, "CST": -6, "MST": -7, "PST": -8,
            "CET": 1, "EET": 2, "JST": 9, "AEST": 10,
            "IST": 5.5, "CST_CHINA": 8, "BST": 1
        }
        
        tz_upper = timezone.upper()
        if tz_upper not in timezones:
            available = ", ".join(timezones.keys())
            await interaction.response.send_message(
                f"❌ Unknown timezone! Available: {available}", 
                ephemeral=True
            )
            return
        
        offset = timezones[tz_upper]
        current_utc = datetime.utcnow()
        target_time = current_utc + timedelta(hours=offset)
        
        embed = discord.Embed(
            title="🌍 World Clock",
            color=0x3498db
        )
        embed.add_field(name="🕐 Timezone", value=tz_upper, inline=True)
        embed.add_field(name="📅 Date", value=target_time.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="⏰ Time", value=target_time.strftime("%H:%M:%S"), inline=True)
        embed.set_footer(text="🌍 Current time in selected timezone")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="🖼️ Get someone's avatar in high quality!")
    async def avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {target_user.display_name}'s Avatar",
            color=target_user.color if target_user.color.value != 0 else 0x3498db
        )
        
        avatar_url = target_user.display_avatar.url
        
        embed.set_image(url=avatar_url)
        embed.add_field(name="📥 Download Links", 
                       value=f"[PNG]({avatar_url}?format=png) | [JPG]({avatar_url}?format=jpg) | [WebP]({avatar_url}?format=webp)", 
                       inline=False)
        
        if target_user.avatar != target_user.display_avatar:
            embed.set_footer(text="This user is using a server-specific avatar")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="👤 Get detailed information about a user!")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        # Get user data from database
        user_data = db.get_user_data(target_user.id)
        
        embed = discord.Embed(
            title=f"👤 User Information",
            color=target_user.color if target_user.color.value != 0 else 0x3498db
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Basic info
        embed.add_field(
            name="📋 Basic Info",
            value=f"**Name:** {target_user.display_name}\n**Username:** {target_user.name}\n**ID:** {target_user.id}",
            inline=True
        )
        
        # Discord info
        created_at = target_user.created_at.strftime("%B %d, %Y")
        joined_at = target_user.joined_at.strftime("%B %d, %Y") if target_user.joined_at else "Unknown"
        
        embed.add_field(
            name="📅 Discord Info",
            value=f"**Created:** {created_at}\n**Joined Server:** {joined_at}",
            inline=True
        )
        
        # Bot stats
        level = 0
        xp = user_data.get('xp', 0)
        # Calculate level from XP (simplified)
        while (level + 1) * 100 <= xp:
            level += 1
        
        embed.add_field(
            name="🎮 Bot Stats",
            value=f"**Level:** {level}\n**XP:** {xp:,}\n**Coins:** {user_data.get('coins', 0):,}",
            inline=True
        )
        
        # Roles (top 5)
        roles = [role.name for role in target_user.roles if role.name != "@everyone"][:5]
        roles_text = ", ".join(roles) if roles else "No roles"
        if len(target_user.roles) > 6:  # 5 + @everyone
            roles_text += f" (+{len(target_user.roles) - 6} more)"
        
        embed.add_field(name="🎭 Roles", value=roles_text, inline=False)
        
        # Status and activity
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡", 
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        
        embed.add_field(
            name="💫 Status",
            value=f"{status_emoji.get(target_user.status, '❓')} {target_user.status.name.title()}",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(CoolCommands(bot))