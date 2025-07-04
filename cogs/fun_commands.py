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
import re

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
        
        # Medieval insults
        self.insults = [
            "Thou art a most loathsome, beetle-headed flap dragon!",
            "You are nothing but a clay-brained guts-griping pignut!",
            "Thou art a craven milk-livered cur!",
            "You're a pox-marked, sheep-biting canker-blossom!",
            "Thou art a villainous earth-vexing dewberry!",
            "You're a bootless beef-witted barnacle!",
            "Thou art a churlish doghearted moldwarp!",
            "You're a wayward rude-growing hedge-pig!",
            "Thou art a infectious fly-bitten foot-licker!",
            "You're a yeasty half-faced haggard!"
        ]
        
        # Ancient wisdom
        self.wisdom = [
            "The journey of a thousand miles begins with a single step. - Lao Tzu",
            "A wise man learns more from his enemies than a fool from his friends. - Baltasar Gracián",
            "The best time to plant a tree was 20 years ago. The second best time is now. - Chinese Proverb",
            "It is better to remain silent and be thought a fool than to speak and remove all doubt. - Mark Twain",
            "The only true wisdom is in knowing you know nothing. - Socrates",
            "A diamond is merely a lump of coal that handled stress exceptionally well. - Unknown",
            "The wise man does not lay up his own treasures. The more he gives to others, the more he has for his own. - Lao Tzu",
            "In the depth of winter, I finally learned that within me there lay an invincible summer. - Albert Camus"
        ]
        
        # Short stories
        self.stories = [
            "A man found a lamp. A genie appeared and granted him three wishes. His first wish: 'I want to be rich!' Poof - he became Rich Johnson. His second wish: 'I want to be the most handsome man alive!' Poof - his name became Rich Handsome Johnson. For his third wish, he said 'I want to be irresistible to women!' Poof - he became a chocolate bar.",
            "A time traveler went back to prevent a disaster but accidentally caused it. He went back again to fix it but made it worse. After 47 attempts, he realized the disaster was him constantly trying to prevent it.",
            "The last human on Earth heard a knock at the door. When they opened it, they found a package addressed to 'Current Resident.' Inside was a note: 'Warranty expired. Please vacate premises. - Management'",
            "A dragon applied for a job at a coffee shop. 'Can you make hot drinks?' asked the manager. 'I AM the hot drink,' replied the dragon confidently."
        ]
        
        # Conspiracy theories (funny ones)
        self.conspiracies = [
            "Birds aren't real - they're government surveillance drones. That's why they sit on power lines... they're recharging!",
            "Finland doesn't exist. It's just a made-up place created by the USSR and Japan for fishing rights.",
            "Giraffes are just horses that believed in themselves too much.",
            "The moon landing was fake... it was actually filmed on Venus to throw people off.",
            "Wyoming doesn't exist. It's just a rectangular void used by the government to store extra taxpayers.",
            "Bananas are trying to evolve hands to take over the world. That's why they're shaped like that.",
            "Mattress stores are money laundering fronts. No one actually buys that many mattresses.",
            "Australia is just paid actors hired by the government to make us think the Earth is round."
        ]
        
        # Shower thoughts
        self.shower_thoughts = [
            "If you're waiting for the waiter, aren't you the waiter?",
            "The letter 'W' is pronounced 'double-u' but looks like 'double-v'.",
            "Your future self is watching you right now through memories.",
            "Humans are the only animals that pay to live on Earth.",
            "You've never seen your own face, only pictures and reflections.",
            "Night mode on phones is just fancy darkness.",
            "Every photo is from the past, so every photo is technically a throwback.",
            "You're always looking at the past because light takes time to reach your eyes."
        ]
        
        # Tongue twisters
        self.tongue_twisters = [
            "She sells seashells by the seashore!",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
            "Peter Piper picked a peck of pickled peppers!",
            "Red lorry, yellow lorry, red lorry, yellow lorry!",
            "Fuzzy Wuzzy was a bear. Fuzzy Wuzzy had no hair. Fuzzy Wuzzy wasn't fuzzy, was he?",
            "Six sick slick slim sycamore saplings!",
            "A proper copper coffee pot!",
            "Irish wristwatch, Swiss wristwatch!"
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
            
        except discord.Forbidden:
            await ctx.respond("❌ I don't have permission to send messages in that channel!", ephemeral=True)

    def parse_duration(self, duration_str: str) -> int:
        """Parse duration string like '1h', '30m', '2d' into seconds"""
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

    @commands.slash_command(
        name="insult",
        description="Get a medieval-style insult (all in good fun)!",
        guild_ids=[GUILD_ID],
    )
    @option("user", description="User to insult (optional)", type=discord.Member, required=False)
    async def insult(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target = user or ctx.author
        insult = random.choice(self.insults)
        
        embed = discord.Embed(
            title="⚔️ Medieval Insult!",
            description=f"{target.mention}, {insult}",
            color=discord.Color.dark_purple(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Ye Olde Insult Generator", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="'Tis but jest! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="wisdom",
        description="Get ancient wisdom and profound quotes!",
        guild_ids=[GUILD_ID],
    )
    async def wisdom(self, ctx: discord.ApplicationContext):
        wise_quote = random.choice(self.wisdom)
        
        embed = discord.Embed(
            title="🧙‍♂️ Ancient Wisdom",
            description=f"*{wise_quote}*",
            color=discord.Color.dark_blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="The Sage", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Wisdom of the ages • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="storytime",
        description="Get a random short story!",
        guild_ids=[GUILD_ID],
    )
    async def storytime(self, ctx: discord.ApplicationContext):
        story = random.choice(self.stories)
        
        embed = discord.Embed(
            title="📚 Story Time!",
            description=story,
            color=discord.Color.dark_green(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="The Storyteller", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Once upon a time... • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="conspiracy",
        description="Get a funny conspiracy theory!",
        guild_ids=[GUILD_ID],
    )
    async def conspiracy(self, ctx: discord.ApplicationContext):
        theory = random.choice(self.conspiracies)
        
        embed = discord.Embed(
            title="🕵️‍♂️ Conspiracy Theory Alert!",
            description=theory,
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="The Truth Seeker", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Wake up sheeple! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="showerthought",
        description="Get a mind-bending shower thought!",
        guild_ids=[GUILD_ID],
    )
    async def showerthought(self, ctx: discord.ApplicationContext):
        thought = random.choice(self.shower_thoughts)
        
        embed = discord.Embed(
            title="🚿 Shower Thought",
            description=thought,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Deep Thinker", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Mind = Blown! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="tonguetwister",
        description="Get a challenging tongue twister!",
        guild_ids=[GUILD_ID],
    )
    async def tonguetwister(self, ctx: discord.ApplicationContext):
        twister = random.choice(self.tongue_twisters)
        
        embed = discord.Embed(
            title="👅 Tongue Twister Challenge!",
            description=f"**Try saying this fast 5 times:**\n\n*{twister}*",
            color=discord.Color.magenta(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Speech Master", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Good luck! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="dice",
        description="Roll dice! (e.g., 1d6, 2d10, 3d20)",
        guild_ids=[GUILD_ID],
    )
    @option("dice_notation", description="Dice to roll (e.g., 1d6, 2d10, 3d20)", default="1d6")
    async def dice(self, ctx: discord.ApplicationContext, dice_notation: str = "1d6"):
        try:
            # Parse dice notation (e.g., "2d10" = 2 dice with 10 sides each)
            if 'd' not in dice_notation.lower():
                return await ctx.respond("❌ Invalid format! Use: 1d6, 2d10, etc.", ephemeral=True)
            
            parts = dice_notation.lower().split('d')
            num_dice = int(parts[0]) if parts[0] else 1
            num_sides = int(parts[1])
            
            if num_dice > 10 or num_dice < 1:
                return await ctx.respond("❌ Please roll between 1-10 dice!", ephemeral=True)
            if num_sides > 100 or num_sides < 2:
                return await ctx.respond("❌ Dice must have between 2-100 sides!", ephemeral=True)
            
            # Roll the dice
            rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(rolls)
            
            embed = discord.Embed(
                title="🎲 Dice Roll!",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            roll_text = " + ".join([f"**{roll}**" for roll in rolls])
            embed.add_field(name=f"Rolling {dice_notation.upper()}", value=roll_text, inline=False)
            embed.add_field(name="Total", value=f"**{total}**", inline=True)
            
            embed.set_author(name=f"{ctx.author.display_name}'s Roll", icon_url=ctx.author.display_avatar.url)
            embed.set_footer(text="May the odds be with you! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
            
            await ctx.respond(embed=embed)
            
        except ValueError:
            await ctx.respond("❌ Invalid dice format! Use: 1d6, 2d10, 3d20, etc.", ephemeral=True)

    @commands.slash_command(
        name="rps",
        description="Play Rock Paper Scissors against the bot!",
        guild_ids=[GUILD_ID],
    )
    @option("choice", description="Your choice", choices=["rock", "paper", "scissors"])
    async def rps(self, ctx: discord.ApplicationContext, choice: str):
        bot_choice = random.choice(["rock", "paper", "scissors"])
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = discord.Color.yellow()
            emoji = "🤝"
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            color = discord.Color.green()
            emoji = "🎉"
            # Give small cookie reward
            db.add_cookies(ctx.author.id, 2)
        else:
            result = "Bot wins!"
            color = discord.Color.red()
            emoji = "🤖"
        
        # Emojis for choices
        choice_emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        embed = discord.Embed(
            title=f"{emoji} Rock Paper Scissors",
            description=f"**{result}**",
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Your Choice", value=f"{choice_emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="Bot's Choice", value=f"{choice_emojis[bot_choice]} {bot_choice.title()}", inline=True)
        
        if result == "You win!":
            embed.add_field(name="Reward", value="+2 🍪", inline=False)
        
        embed.set_author(name=f"{ctx.author.display_name} vs Bot", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="Best of luck! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="hangman",
        description="Start a word guessing game!",
        guild_ids=[GUILD_ID],
    )
    async def hangman(self, ctx: discord.ApplicationContext):
        words = ["PYTHON", "DISCORD", "GAMING", "COMPUTER", "KEYBOARD", "BLECKOPS", "CHALLENGE", "VICTORY"]
        word = random.choice(words)
        
        # Create display word with blanks
        display = "_ " * len(word)
        
        embed = discord.Embed(
            title="🎯 Hangman Game!",
            description=f"**Word:** {display.strip()}\n**Length:** {len(word)} letters",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="How to Play", value="Guess the word by typing letters in chat!\nYou have 6 wrong guesses.", inline=False)
        embed.add_field(name="Wrong Guesses", value="0/6", inline=True)
        embed.add_field(name="Letters Used", value="None", inline=True)
        embed.set_author(name=f"{ctx.author.display_name}'s Hangman", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="Type letters to guess! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="complain",
        description="Submit a complaint to a specific channel!",
        guild_ids=[GUILD_ID],
    )
    @option("complaint", description="Your complaint or feedback")
    @option("channel", description="Channel to send complaint to", type=discord.TextChannel)
    async def complain(self, ctx: discord.ApplicationContext, complaint: str, channel: discord.TextChannel):
        # Create complaint embed
        embed = discord.Embed(
            title="📢 New Complaint",
            description=complaint,
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"From: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Submitted From", value=ctx.channel.mention, inline=True)
        embed.add_field(name="User ID", value=ctx.author.id, inline=True)
        embed.set_footer(text="Complaint submitted • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
            
            confirm_embed = discord.Embed(
                title="✅ Complaint Submitted!",
                description=f"Your complaint has been sent to {channel.mention}",
                color=discord.Color.green()
            )
            await ctx.respond(embed=confirm_embed, ephemeral=True)
            
        except discord.Forbidden:
            await ctx.respond("❌ I don't have permission to send messages in that channel!", ephemeral=True)

    @commands.slash_command(
        name="reminder",
        description="Set a reminder! (AI-powered with smart time parsing)",
        guild_ids=[GUILD_ID],
    )
    @option("time", description="When to remind (e.g., '10 minutes', '2 hours', 'tomorrow')")
    @option("message", description="What to remind you about")
    async def reminder(self, ctx: discord.ApplicationContext, time: str, message: str):
        # Smart time parsing using AI-like logic
        reminder_seconds = self.parse_smart_time(time)
        
        if not reminder_seconds:
            return await ctx.respond("❌ I couldn't understand that time format. Try: '10 minutes', '2 hours', '1 day'", ephemeral=True)
        
        if reminder_seconds > 86400 * 7:  # Max 7 days
            return await ctx.respond("❌ Maximum reminder time is 7 days!", ephemeral=True)
        
        if reminder_seconds < 60:  # Min 1 minute
            return await ctx.respond("❌ Minimum reminder time is 1 minute!", ephemeral=True)
        
        # Store reminder (simplified - you could use a database)
        embed = discord.Embed(
            title="⏰ Reminder Set!",
            description=f"I'll remind you about: **{message}**",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Time", value=time, inline=True)
        embed.add_field(name="In Seconds", value=f"{reminder_seconds}s", inline=True)
        embed.set_author(name=f"Reminder for {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="I'll ping you when it's time! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed, ephemeral=True)
        
        # Wait and send reminder
        await asyncio.sleep(reminder_seconds)
        
        reminder_embed = discord.Embed(
            title="🔔 Reminder!",
            description=message,
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        reminder_embed.set_author(name="Your Reminder", icon_url=self.bot.user.display_avatar.url)
        reminder_embed.set_footer(text="Hope this helps! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        try:
            await ctx.author.send(f"{ctx.author.mention}", embed=reminder_embed)
        except discord.Forbidden:
            # If DM fails, send in channel
            await ctx.followup.send(f"{ctx.author.mention}", embed=reminder_embed)

    def parse_smart_time(self, time_str: str) -> int:
        """Smart time parsing with AI-like natural language understanding"""
        time_str = time_str.lower().strip()
        total_seconds = 0
        
        # Handle common phrases
        if 'tomorrow' in time_str:
            total_seconds += 86400
        elif 'next week' in time_str:
            total_seconds += 86400 * 7
        elif 'next hour' in time_str:
            total_seconds += 3600
        
        # Parse specific time units
        patterns = [
            (r'(\d+)\s*(?:seconds?|secs?|s)', 1),
            (r'(\d+)\s*(?:minutes?|mins?|m)', 60),
            (r'(\d+)\s*(?:hours?|hrs?|h)', 3600),
            (r'(\d+)\s*(?:days?|d)', 86400),
            (r'(\d+)\s*(?:weeks?|w)', 86400 * 7),
        ]
        
        for pattern, multiplier in patterns:
            matches = re.findall(pattern, time_str)
            for match in matches:
                total_seconds += int(match) * multiplier
        
        return total_seconds if total_seconds > 0 else None

# ─────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(FunCommands(bot), guilds=[guild_obj])