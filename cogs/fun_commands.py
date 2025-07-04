# cogs/fun_commands.py
# Additional fun commands for the Discord bot
import discord
from discord.ext import commands
from discord import option
import random
import os
import sys
from datetime import datetime

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
        name="joke",
        description="Get a random joke to brighten your day!",
        guild_ids=[GUILD_ID],
    )
    async def joke(self, ctx: discord.ApplicationContext):
        joke = random.choice(self.jokes)
        
        embed = discord.Embed(
            title="😂 Random Joke",
            description=joke,
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Joke Master", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

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
        name="compliment",
        description="Give someone a nice compliment!",
        guild_ids=[GUILD_ID],
    )
    @option("user", description="User to compliment", type=discord.Member, required=False)
    async def compliment(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target = user or ctx.author
        compliment = random.choice(self.compliments)
        
        embed = discord.Embed(
            title="💝 Compliment",
            description=f"{target.mention}, {compliment}",
            color=discord.Color.pink(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Compliment from {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text="Spread positivity! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="truth",
        description="Get a truth question for truth or dare!",
        guild_ids=[GUILD_ID],
    )
    async def truth(self, ctx: discord.ApplicationContext):
        truth = random.choice(self.truths)
        
        embed = discord.Embed(
            title="🤔 Truth Question",
            description=truth,
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Truth or Dare", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Answer honestly! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="dare",
        description="Get a dare challenge for truth or dare!",
        guild_ids=[GUILD_ID],
    )
    async def dare(self, ctx: discord.ApplicationContext):
        dare = random.choice(self.dares)
        
        embed = discord.Embed(
            title="💪 Dare Challenge",
            description=dare,
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name="Truth or Dare", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="You got this! • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
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

# ─────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(FunCommands(bot), guilds=[guild_obj])