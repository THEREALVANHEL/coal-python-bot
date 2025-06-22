import discord
from discord.ext import commands
from discord import app_commands
import random
import os
from datetime import datetime
import google.generativeai as genai
import database as db  # ✅ Importing the database module

# --- Globals ---
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

ANNOUNCE_ROLES = [
    "Moderator 🚨🚓",
    "🚨 Lead moderator",
    "🦥 Overseer",
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
            answer = response.text.strip() if hasattr(response, 'text') and response.text.strip() else "Hmm... I couldn't think of a clever answer this time. Try asking again later!"

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
        channel_id = db.get_channel(interaction.guild.id, "suggestion")
        channel = interaction.guild.get_channel(channel_id) if channel_id else None

        if not channel:
            await interaction.response.send_message("❌ Suggestion channel not set. Use `/setsuggestionchannel` first.", ephemeral=True)
            return

        embed = discord.Embed(title="💡 New Suggestion", description=suggestion, color=discord.Color.yellow(), timestamp=datetime.utcnow())
        embed.set_author(name=f"Suggested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        if notes != "None":
            embed.add_field(name="🗘️ Additional Notes", value=notes, inline=False)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Suggestion submitted successfully!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)

    # (All other commands like announce, poll, flip, spinawheel remain unchanged below)

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
            description=f"**__{content}__**",
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
        await interaction.response.defer()

        result = random.choice(["Heads", "Tails"])
        emoji = "👑" if result == "Heads" else "🪙"
        image_path = f"./assets/{result.lower()}.jpeg"

        if not os.path.exists(image_path):
            await interaction.followup.send(f"❌ Image for {result} not found in assets.", ephemeral=True)
            return

        file = discord.File(image_path, filename="result.jpeg")

        embed = discord.Embed(title=f"🪙 Coin Flip: It's {result}!", color=discord.Color.gold())
        embed.set_author(name=f"Flipped by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_image(url="attachment://result.jpeg")
        embed.add_field(name="Result", value=f"{emoji} **{result}**")
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.followup.send(embed=embed, file=file)

    @app_commands.command(name="spinawheel", description="Spin a wheel with a title and comma-separated options.")
    @app_commands.describe(title="The title of the wheel.", options="A comma-separated list of options.")
    async def spinawheel(self, interaction: discord.Interaction, title: str, options: str):
        await interaction.response.defer()

        import matplotlib.pyplot as plt
        import numpy as np
        import io
        import textwrap
        from matplotlib.patches import FancyArrow
        from matplotlib.patheffects import withStroke

        option_list = [opt.strip() for opt in options.split(',') if opt.strip()]
        if not (2 <= len(option_list) <= 10):
            await interaction.followup.send("Please provide between 2 to 10 options.", ephemeral=True)
            return

        winner = random.choice(option_list)
        winner_index = option_list.index(winner)
        num_options = len(option_list)
        slice_angle = 360 / num_options
        start_angle = 90 - (slice_angle * winner_index + slice_angle / 2)

        base_colors = ['white', 'black', 'yellow', 'gray', 'lightgray', 'gold', 'silver', 'beige', 'ivory', 'darkgray']
        colors = base_colors[:num_options]

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(aspect="equal"))
        wedges, _ = ax.pie([1] * num_options, colors=colors, startangle=90, counterclock=False)

        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 + wedge.theta1) / 2
            x = 0.75 * np.cos(np.radians(angle))
            y = 0.75 * np.sin(np.radians(angle))
            label = textwrap.fill(option_list[i], width=10)
            ax.text(
                x, y, label,
                ha='center', va='center',
                fontsize=36, color='black', weight='bold',
                path_effects=[withStroke(linewidth=2, foreground='white')]
            )

        pointer_angle_rad = np.radians(start_angle)
        pointer_x = np.cos(pointer_angle_rad) * 1.1
        pointer_y = np.sin(pointer_angle_rad) * 1.1
        ax.add_patch(FancyArrow(pointer_x, pointer_y, -pointer_x * 0.1, -pointer_y * 0.1, width=0.05, length_includes_head=True, color='gold'))
        ax.set_title(title, fontsize=32, weight='bold', pad=20, color='gold')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True)
        buf.seek(0)
        plt.close(fig)

        wheel_file = discord.File(buf, filename="wheel.png")

        embed = discord.Embed(
            title="🍀 The Wheel Has Spun!",
            description=f"The wheel titled **'{title}'** landed on:",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="🏆 Winner", value=f"**{winner}**", inline=False)
        embed.set_image(url="attachment://wheel.png")
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.followup.send(embed=embed, file=wheel_file)

async def setup(bot):
    await bot.add_cog(Community(bot), guilds=[guild_obj])
