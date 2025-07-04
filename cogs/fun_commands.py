# cogs/fun_commands.py
# Additional fun commands for the Discord bot
import discord
from discord.ext import commands
from discord import option
import random
import os
import sys
from datetime import datetime
import asyncio

# ── project imports ───────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db

# ── Config ───────────────────────────────────────────────
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class FunCommands(commands.Cog):
    """Fun and entertainment commands for the server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # 8-ball responses
        self.eight_ball_responses = [
            "🎱 It is certain", "🎱 Without a doubt", "🎱 Yes definitely",
            "🎱 You may rely on it", "🎱 As I see it, yes", "🎱 Most likely",
            "🎱 Outlook good", "🎱 Yes", "🎱 Signs point to yes",
            "🎱 Reply hazy, try again", "🎱 Ask again later", "🎱 Better not tell you now",
            "🎱 Cannot predict now", "🎱 Concentrate and ask again",
            "🎱 Don't count on it", "🎱 My reply is no", "🎱 My sources say no",
            "🎱 Outlook not so good", "🎱 Very doubtful"
        ]
        
        # Jokes collection
        self.jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "Why don't skeletons fight each other? They don't have the guts.",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "I'm reading a book about anti-gravity. It's impossible to put down!",
            "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them!",
            "Why don't programmers like nature? It has too many bugs!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
            "I told my computer I needed a break... now it won't stop sending me Kit-Kat ads!"
        ]
        
        # Inspirational quotes
        self.quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Life is what happens to you while you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
            "The only impossible journey is the one you never begin. - Tony Robbins",
            "In the end, we will remember not the words of our enemies, but the silence of our friends. - Martin Luther King Jr."
        ]
        
        # Compliments
        self.compliments = [
            "You're absolutely amazing!", "You light up the room!", "You're incredibly thoughtful!",
            "You have the best sense of humor!", "You're a fantastic friend!", "You're really talented!",
            "You make everyone feel welcomed!", "You're so creative!", "You have great taste!",
            "You're an inspiration!", "You're incredibly kind!", "You make people smile!",
            "You're awesome at everything you do!", "You have such a positive energy!",
            "You're incredibly intelligent!", "You're a great listener!"
        ]
        
        # Truth questions
        self.truths = [
            "What's the most embarrassing thing you've ever done?",
            "What's your biggest fear?", "Who is your secret crush?",
            "What's the weirdest dream you've ever had?", "What's your most unpopular opinion?",
            "What's the most childish thing you still do?", "What's your guilty pleasure?",
            "What's the worst advice you've ever given?", "What's your strangest habit?",
            "What's the most trouble you've ever been in?"
        ]
        
        # Dare challenges
        self.dares = [
            "Send a funny selfie to the chat!", "Do your best animal impression!",
            "Sing a song of the group's choice!", "Do 10 push-ups!",
            "Tell a joke that makes someone laugh!", "Dance for 30 seconds!",
            "Text your mom 'I love you'!", "Do your best celebrity impression!",
            "Speak in an accent for the next 3 messages!", "Share an unpopular food opinion!"
        ]

    async def cog_load(self):
        print("[FunCommands] Cog loaded successfully.")

    @commands.slash_command(
        name="8ball",
        description="Ask the magic 8-ball a question!",
        guild_ids=[GUILD_ID],
    )
    @option("question", description="Your yes/no question for the magic 8-ball")
    async def eight_ball(self, ctx: discord.ApplicationContext, question: str):
        response = random.choice(self.eight_ball_responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="🔮 Answer", value=response, inline=False)
        embed.set_author(name=f"Asked by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="fun",
        description="Get a random joke, compliment, truth question, or dare challenge!",
        guild_ids=[GUILD_ID],
    )
    @option("type", description="Choose specific type or leave blank for random", 
            choices=["random", "joke", "compliment", "truth", "dare"], required=False)
    @option("user", description="Target user for compliments", type=discord.Member, required=False)
    async def fun(self, ctx: discord.ApplicationContext, type: str = "random", user: discord.Member = None):
        # If type is random or not specified, pick randomly
        if type == "random":
            type = random.choice(["joke", "compliment", "truth", "dare"])
        
        if type == "joke":
            content = random.choice(self.jokes)
            embed = discord.Embed(
                title="😂 Random Joke",
                description=content,
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name="Joke Master", icon_url=self.bot.user.display_avatar.url)
            
        elif type == "compliment":
            target = user or ctx.author
            content = random.choice(self.compliments)
            embed = discord.Embed(
                title="💝 Compliment",
                description=f"{target.mention}, {content}",
                color=discord.Color.pink(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=f"Compliment from {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            
        elif type == "truth":
            content = random.choice(self.truths)
            embed = discord.Embed(
                title="🤔 Truth Question",
                description=content,
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name="Truth or Dare", icon_url=self.bot.user.display_avatar.url)
            
        elif type == "dare":
            content = random.choice(self.dares)
            embed = discord.Embed(
                title="💪 Dare Challenge",
                description=content,
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name="Truth or Dare", icon_url=self.bot.user.display_avatar.url)
        
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="giveaway",
        description="Start a giveaway with reactions!",
        guild_ids=[GUILD_ID],
    )
    @option("prize", description="What's being given away")
    @option("duration", description="Duration (e.g., '1h', '30m', '2d')")
    @option("winners", description="Number of winners", type=int, default=1)
    @option("channel", description="Channel to post giveaway", type=discord.TextChannel, required=False)
    @option("required_role", description="Required role to enter (optional)", type=discord.Role, required=False)
    async def giveaway(self, ctx: discord.ApplicationContext, prize: str, duration: str, 
                      winners: int = 1, channel: discord.TextChannel = None, 
                      required_role: discord.Role = None):
        
        # Parse duration
        duration_seconds = self.parse_duration(duration)
        if not duration_seconds:
            return await ctx.respond("❌ Invalid duration format! Use: 1h, 30m, 2d, etc.", ephemeral=True)
        
        target_channel = channel or ctx.channel
        
        # Create giveaway embed
        embed = discord.Embed(
            title="🎉 GIVEAWAY! 🎉",
            description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Duration:** {duration}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        if required_role:
            embed.add_field(name="🎫 Requirements", value=f"Must have {required_role.mention} role", inline=False)
        
        embed.add_field(name="📝 How to Enter", value="React with 🎉 to enter!", inline=False)
        embed.set_author(name=f"Hosted by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Ends in {duration} • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        try:
            giveaway_msg = await target_channel.send(embed=embed)
            await giveaway_msg.add_reaction("🎉")
            
            confirm_embed = discord.Embed(
                title="✅ Giveaway Started!",
                description=f"Giveaway posted in {target_channel.mention}!\nEnds in **{duration}**",
                color=discord.Color.green()
            )
            await ctx.respond(embed=confirm_embed, ephemeral=True)
            
            # Store giveaway data in database (you'll need to implement this)
            # For now, we'll just send a reminder
            await asyncio.sleep(min(duration_seconds, 3600))  # Max 1 hour for demo
            
        except discord.Forbidden:
            await ctx.respond("❌ I don't have permission to send messages in that channel!", ephemeral=True)

    def parse_duration(self, duration_str: str) -> int:
        """Parse duration string like '1h', '30m', '2d' into seconds"""
        import re
        
        total_seconds = 0
        # Find all number+unit pairs
        matches = re.findall(r'(\d+)([dhms])', duration_str.lower())
        
        for value, unit in matches:
            value = int(value)
            if unit == 'd':
                total_seconds += value * 86400  # days
            elif unit == 'h':
                total_seconds += value * 3600   # hours  
            elif unit == 'm':
                total_seconds += value * 60     # minutes
            elif unit == 's':
                total_seconds += value          # seconds
        
        return total_seconds if total_seconds > 0 else None

    @commands.slash_command(
        name="quote",
        description="Get an inspirational quote!",
        guild_ids=[GUILD_ID],
    )
    async def quote(self, ctx: discord.ApplicationContext):
        quote = random.choice(self.quotes)
        
        embed = discord.Embed(
            title="✨ Inspirational Quote",
            description=f"*{quote}*",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Daily Inspiration", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="coinflipbet",
        description="Bet cookies on a coin flip!",
        guild_ids=[GUILD_ID],
    )
    @option("bet_amount", description="Amount of cookies to bet (1-100)", type=int)
    @option("choice", description="Your guess: heads or tails", choices=["heads", "tails"])
    async def coinflipbet(self, ctx: discord.ApplicationContext, bet_amount: int, choice: str):
        user_id = ctx.author.id
        
        # Validate bet amount
        if bet_amount < 1 or bet_amount > 100:
            return await ctx.respond("❌ Bet amount must be between 1-100 cookies!", ephemeral=True)
        
        # Check user's cookie balance
        user_cookies = db.get_cookies(user_id)
        if user_cookies < bet_amount:
            return await ctx.respond(f"❌ You don't have enough cookies! Your balance: **{user_cookies}** 🍪", ephemeral=True)
        
        # Flip the coin
        result = random.choice(["heads", "tails"])
        won = (choice.lower() == result)
        
        # Calculate winnings/losses
        if won:
            winnings = bet_amount
            db.add_cookies(user_id, winnings)
            new_balance = user_cookies + winnings
            
            embed = discord.Embed(
                title="🎉 You Won!",
                description=f"The coin landed on **{result}**!\nYou won **{winnings}** 🍪!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
        else:
            db.remove_cookies(user_id, bet_amount)
            new_balance = user_cookies - bet_amount
            
            embed = discord.Embed(
                title="💸 You Lost!",
                description=f"The coin landed on **{result}**!\nYou lost **{bet_amount}** 🍪!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
        
        embed.add_field(name="Your Guess", value=choice.capitalize(), inline=True)
        embed.add_field(name="Result", value=result.capitalize(), inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance} 🍪", inline=True)
        embed.set_author(name=f"{ctx.author.display_name}'s Coin Flip Bet", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="Gambling responsibly! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="trivia",
        description="Answer a random trivia question!",
        guild_ids=[GUILD_ID],
    )
    async def trivia(self, ctx: discord.ApplicationContext):
        # Simple trivia questions with answers
        trivia_questions = [
            {"q": "What is the capital of France?", "a": "Paris", "options": ["London", "Paris", "Berlin", "Madrid"]},
            {"q": "How many planets are in our solar system?", "a": "8", "options": ["7", "8", "9", "10"]},
            {"q": "What is the largest ocean on Earth?", "a": "Pacific", "options": ["Atlantic", "Pacific", "Indian", "Arctic"]},
            {"q": "Who painted the Mona Lisa?", "a": "Leonardo da Vinci", "options": ["Leonardo da Vinci", "Pablo Picasso", "Van Gogh", "Michelangelo"]},
            {"q": "What is the smallest country in the world?", "a": "Vatican City", "options": ["Monaco", "Vatican City", "San Marino", "Luxembourg"]},
        ]
        
        question = random.choice(trivia_questions)
        
        embed = discord.Embed(
            title="🧠 Trivia Time!",
            description=question["q"],
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        options_text = "\n".join([f"**{chr(65+i)}.** {opt}" for i, opt in enumerate(question["options"])])
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.add_field(name="💡 Answer", value=f"||{question['a']}||", inline=False)
        embed.set_footer(text="Click the spoiler to see the answer! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="roast",
        description="Get a funny roast (all in good fun!)!",
        guild_ids=[GUILD_ID],
    )
    @option("user", description="User to roast (optional)", type=discord.Member, required=False)
    async def roast(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        roasts = [
            "You're like a cloud. When you disappear, it's a beautiful day!",
            "If I had a dollar for every brain you don't have, I'd have one dollar.",
            "You're proof that even god makes mistakes sometimes.",
            "I'd explain it to you, but I don't have any crayons with me.",
            "You're like Monday mornings - nobody likes you.",
            "If stupidity was a superpower, you'd be invincible!",
            "You're the reason they put instructions on shampoo bottles.",
            "I'm not saying you're dumb, but you'd struggle to pour water out of a boot with instructions on the heel.",
            "You're like a broken pencil... pointless!",
            "If brains were dynamite, you wouldn't have enough to blow your nose."
        ]
        
        target = user or ctx.author
        roast = random.choice(roasts)
        
        embed = discord.Embed(
            title="🔥 Roast Time!",
            description=f"{target.mention}, {roast}",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Roast Master", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="All in good fun! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="pickupline",
        description="Get a cheesy pickup line!",
        guild_ids=[GUILD_ID],
    )
    async def pickupline(self, ctx: discord.ApplicationContext):
        pickup_lines = [
            "Are you a magician? Because whenever I look at you, everyone else disappears!",
            "Do you have a map? I keep getting lost in your eyes.",
            "Are you Wi-Fi? Because I'm feeling a connection!",
            "Is your name Google? Because you have everything I've been searching for.",
            "Are you a parking ticket? Because you've got 'FINE' written all over you!",
            "Do you believe in love at first sight, or should I walk by again?",
            "Are you a campfire? Because you're hot and I want s'more!",
            "Is your dad a boxer? Because you're a knockout!",
            "Are you made of copper and tellurium? Because you're Cu-Te!",
            "Do you have a Band-Aid? I just scraped my knee falling for you."
        ]
        
        line = random.choice(pickup_lines)
        
        embed = discord.Embed(
            title="💕 Pickup Line Alert!",
            description=line,
            color=discord.Color.magenta(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Cupid's Helper", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Use at your own risk! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="wouldyourather",
        description="Get a 'Would You Rather' question!",
        guild_ids=[GUILD_ID],
    )
    async def wouldyourather(self, ctx: discord.ApplicationContext):
        questions = [
            "Would you rather have the ability to fly OR be invisible?",
            "Would you rather eat pizza for every meal OR never eat pizza again?",
            "Would you rather live in the past OR live in the future?",
            "Would you rather be really hot OR really cold all the time?",
            "Would you rather have super strength OR super speed?",
            "Would you rather never use the internet again OR never watch TV again?",
            "Would you rather be able to read minds OR predict the future?",
            "Would you rather always speak your mind OR never speak again?",
            "Would you rather have unlimited money OR unlimited time?",
            "Would you rather fight 100 duck-sized horses OR 1 horse-sized duck?"
        ]
        
        question = random.choice(questions)
        
        embed = discord.Embed(
            title="🤔 Would You Rather?",
            description=question,
            color=discord.Color.teal(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Decision Time!", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Choose wisely! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="fact",
        description="Get a random fun fact!",
        guild_ids=[GUILD_ID],
    )
    async def fact(self, ctx: discord.ApplicationContext):
        facts = [
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible!",
            "A group of flamingos is called a 'flamboyance'.",
            "Bananas are berries, but strawberries aren't!",
            "Octopuses have three hearts and blue blood.",
            "A shrimp's heart is in its head.",
            "It's impossible to hum while holding your nose closed.",
            "The shortest war in history lasted only 38-45 minutes between Britain and Zanzibar in 1896.",
            "A cloud can weigh more than a million pounds.",
            "Your stomach gets an entirely new lining every 3-4 days.",
            "Dolphins have names for each other - they use unique whistle signatures!"
        ]
        
        fact = random.choice(facts)
        
        embed = discord.Embed(
            title="🧐 Random Fun Fact!",
            description=fact,
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Fact Generator", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="The more you know! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="choose",
        description="Can't decide? Let me choose for you!",
        guild_ids=[GUILD_ID],
    )
    @option("options", description="Separate options with commas (e.g., 'pizza, burgers, tacos')")
    async def choose(self, ctx: discord.ApplicationContext, options: str):
        choices = [choice.strip() for choice in options.split(',') if choice.strip()]
        
        if len(choices) < 2:
            return await ctx.respond("❌ Please provide at least 2 options separated by commas!", ephemeral=True)
        
        if len(choices) > 10:
            return await ctx.respond("❌ Maximum 10 options allowed!", ephemeral=True)
        
        chosen = random.choice(choices)
        
        embed = discord.Embed(
            title="🎯 Decision Made!",
            description=f"I choose: **{chosen}**",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        all_options = "\n".join([f"• {opt}" for opt in choices])
        embed.add_field(name="Options", value=all_options, inline=False)
        embed.set_author(name=f"Decision for {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="Trust the process! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="meme",
        description="Get a random meme template with custom text!",
        guild_ids=[GUILD_ID],
    )
    @option("top_text", description="Text for the top of the meme", required=False)
    @option("bottom_text", description="Text for the bottom of the meme", required=False)
    async def meme(self, ctx: discord.ApplicationContext, top_text: str = None, bottom_text: str = None):
        meme_templates = [
            "Drake pointing meme",
            "Distracted boyfriend meme", 
            "This is fine dog",
            "Change my mind",
            "Surprised Pikachu",
            "Woman yelling at cat",
            "Expanding brain",
            "Two buttons meme"
        ]
        
        template = random.choice(meme_templates)
        
        embed = discord.Embed(
            title="😂 Meme Generator!",
            description=f"**Template:** {template}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        if top_text:
            embed.add_field(name="Top Text", value=top_text, inline=False)
        if bottom_text:
            embed.add_field(name="Bottom Text", value=bottom_text, inline=False)
        
        if not top_text and not bottom_text:
            embed.add_field(name="💡 Tip", value="Use `/meme <top_text> <bottom_text>` to add custom text!", inline=False)
        
        embed.set_author(name="Meme Master", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Stonks! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

# ─────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(FunCommands(bot), guilds=[guild_obj])