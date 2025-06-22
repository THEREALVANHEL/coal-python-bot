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
            title=f"📢 {title}",
            description=f"**__{content}__**",  # enlarged & bold content
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Announcement by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
            confirm = discord.Embed(
                description=f"✅ Your announcement has been posted in {channel.mention}!",
                color=discord.Color.green()
            )
            confirm.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
            await interaction.response.send_message(embed=confirm, ephemeral=True)
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
        image_path = f"./assets/{result.lower()}.jpeg"

        if not os.path.exists(image_path):
            await interaction.response.send_message(f"❌ Image for {result} not found in assets.", ephemeral=True)
            return

        file = discord.File(image_path, filename="result.jpeg")

        embed = discord.Embed(title=f"🪙 Coin Flip: It's {result}!", color=discord.Color.gold())
        embed.set_author(name=f"Flipped by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_image(url="attachment://result.jpeg")
        embed.add_field(name="Result", value=f"{emoji} **{result}**")
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="spinawheel", description="Spin a wheel with a title and comma-separated options.")
    @app_commands.describe(title="The title of the wheel.", options="A comma-separated list of options.")
    async def spinawheel(self, interaction: discord.Interaction, title: str, options: str):
        import matplotlib.pyplot as plt
        import numpy as np
        import io
        import textwrap
        from matplotlib.patheffects import withStroke

        option_list = [opt.strip() for opt in options.split(',')]
        if not (2 <= len(option_list) <= 10):
            await interaction.response.send_message("Please provide between 2 to 10 options.", ephemeral=True)
            return

        winner = random.choice(option_list)
        num_options = len(option_list)
        slice_degrees = 360 / num_options
        winner_index = option_list.index(winner)
        start_angle = (winner_index * slice_degrees) + (slice_degrees / 2)

        colors = ['#f94144', '#f3722c', '#f9c74f', '#90be6d', '#43aa8b', '#577590', '#277da1', '#9b5de5', '#f15bb5', '#00f5d4']
        final_colors = (colors * (num_options // len(colors) + 1))[:num_options]

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(aspect="equal"))
        wedges, _ = ax.pie(
            [1] * num_options,
            colors=final_colors,
            startangle=start_angle,
            counterclock=False,
            wedgeprops=dict(edgecolor='white', width=0.4)
        )

        for i, wedge in enumerate(wedges):
            angle = (wedge.theta1 + wedge.theta2) / 2
            x = 0.65 * np.cos(np.radians(angle))
            y = 0.65 * np.sin(np.radians(angle))
            wrapped = "\n".join(textwrap.wrap(option_list[i], 12))
            ax.text(
                x, y, wrapped, ha='center', va='center',
                fontsize=12, color='white', weight='bold',
                path_effects=[withStroke(linewidth=3, foreground='black')]
            )

        ax.annotate('', xy=(1.15, 0), xytext=(1.4, 0), arrowprops=dict(arrowstyle="simple", fc="black", ec="black"))
        ax.set_title(title, fontsize=18, weight='bold', pad=30)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True)
        buf.seek(0)
        plt.close(fig)

        wheel_file = discord.File(buf, filename="wheel.png")

        embed = discord.Embed(
            title=f"🍀 The Wheel Has Spun!",
            description=f"The wheel titled **'{title}'** landed on:",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="🏆 Winner", value=f"**{winner}**", inline=False)
        embed.set_image(url="attachment://wheel.png")
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed, file=wheel_file)

async def setup(bot):
    await bot.add_cog(Community(bot), guilds=[guild_obj])
