import discord
from discord.ext import commands
from discord import app_commands
import random
import os
from datetime import datetime
import google.generativeai as genai

# --- Globals ---
SUGGESTION_CHANNEL_ID = 1137000942544199742
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# Updated roles for announce command
ANNOUNCE_ROLES = [
    "Moderator 🚨🚓",
    "🚨 Lead moderator",
    "🦅 Overseer",
    "Forgotten one"
]

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    @commands.Cog.listener()
    async def on_ready(self):
        print("Community Cog is ready.")

    @app_commands.command(name="askblecknephew", description="Ask Bleck Nephew anything! (Powered by AI)")
    @app_commands.describe(question="The question you want to ask.")
    async def askblecknephew(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            prompt = f"You are Bleck Nephew, a helpful and slightly mischievous Discord bot. A user asked: {question}"
            response = await model.generate_content_async(prompt)
            answer = response.text

            embed = discord.Embed(
                title=f"🤔 {interaction.user.display_name} asks...",
                description=f"**{question}**",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name="Bleck Nephew AI", icon_url=self.bot.user.display_avatar.url)
            embed.add_field(name="💡 Answer", value=answer, inline=False)
            embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Gemini error: {e}")
            await interaction.followup.send("Couldn't get an answer from the AI service.", ephemeral=True)

    @app_commands.command(name="suggest", description="Submit a suggestion for the server.")
    @app_commands.describe(suggestion="Your suggestion.", notes="Any additional notes or details.")
    async def suggest(self, interaction: discord.Interaction, suggestion: str, notes: str = "None"):
        channel = interaction.guild.get_channel(SUGGESTION_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Suggestion channel not found.", ephemeral=True)
            return

        embed = discord.Embed(title="💡 New Suggestion", description=suggestion, color=discord.Color.yellow(), timestamp=datetime.utcnow())
        embed.set_author(name=f"Suggested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        if notes != "None":
            embed.add_field(name="🗘️ Additional Notes", value=notes, inline=False)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message("Suggestion submitted successfully!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Permission error: Can't send message to suggestion channel.", ephemeral=True)

    @app_commands.command(name="announce", description="[Moderator] Create a server announcement.")
    @app_commands.checks.has_any_role(*ANNOUNCE_ROLES)
    @app_commands.describe(
        title="The title of the announcement.",
        content="The main content of the announcement.",
        channel="The channel where the announcement should be sent."
    )
    async def announce(self, interaction: discord.Interaction, title: str, content: str, channel: discord.TextChannel):
        embed = discord.Embed(
            title=f"🎉 {title}",
            description=content,
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Announcement by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)

    @app_commands.command(name="poll", description="Create a simple poll.")
    @app_commands.describe(question="The poll question.", options="Up to 10 options, separated by commas.")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        option_list = [opt.strip() for opt in options.split(',')]
        if len(option_list) > 10:
            await interaction.response.send_message("Maximum 10 options allowed.", ephemeral=True)
            return

        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        poll_text = "".join(f"{emojis[i]} {opt}\n" for i, opt in enumerate(option_list))

        embed = discord.Embed(title=f"📊 Poll: {question}", description="React to vote:", color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.add_field(name="Options", value=poll_text, inline=False)
        embed.set_author(name=f"Poll by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message("Creating poll...")
        msg = await interaction.channel.send(embed=embed)
        for i in range(len(option_list)):
            await msg.add_reaction(emojis[i])
        await interaction.delete_original_response()

    @app_commands.command(name="flip", description="Flip a coin.")
    async def flip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        emoji = "👑" if result == "Heads" else "🪙"

        embed = discord.Embed(title=f"Coin Flip: It's {result}!", color=discord.Color.gold())
        embed.set_author(name=f"Flipped by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url="https://i.imgur.com/s0z6E5C.gif")
        embed.add_field(name="Result", value=f"{emoji} **{result}**")
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="spinawheel", description="Spin a wheel with a title and comma-separated options.")
    @app_commands.describe(title="The title of the wheel.", options="A comma-separated list of options.")
    async def spinawheel(self, interaction: discord.Interaction, title: str, options: str):
        option_list = [opt.strip() for opt in options.split(',')]
        if len(option_list) < 2:
            await interaction.response.send_message("At least two options required.", ephemeral=True)
            return

        winner = random.choice(option_list)

        # Use the static wheel image from assets
        file_path = "./assets/wheel.png"
        if not os.path.exists(file_path):
            await interaction.response.send_message("❌ Could not find wheel image.", ephemeral=True)
            return

        wheel_file = discord.File(file_path, filename="wheel.png")

        embed = discord.Embed(
            title=f"🎡 The Wheel Has Spun!",
            description=f"The wheel, titled **'{title}'**, landed on...",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="🏆 Winner", value=f"**{winner}**", inline=False)
        embed.set_image(url="attachment://wheel.png")
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed, file=wheel_file)

async def setup(bot):
    await bot.add_cog(Community(bot), guilds=[guild_obj])
