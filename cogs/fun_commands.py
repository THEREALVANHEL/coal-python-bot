THIS SHOULD BE A LINTER ERROR# cogs/fun_commands.py
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

# ─────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(FunCommands(bot), guilds=[guild_obj])