import discord
from discord.ext import commands
from discord import app_commands
import random
import os
import io
import textwrap
from datetime import datetime
import google.generativeai as genai
import matplotlib.pyplot as plt
from matplotlib.patheffects import withStroke
import numpy as np

# --- Globals ---
SUGGESTION_CHANNEL_ID = 1137000942544199742
ANNOUNCEMENT_CHANNEL_ID = 1137000942544199745
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

def create_wheel_image(options, title, winner=None):
    """Generates a simple, flat image of a spinning wheel."""

    num_options = len(options)
    
    # --- Calculate rotation to land on the winner ---
    start_angle = 90  # Default start angle if no winner is provided
    winner_index = -1
    if winner and winner in options:
        winner_index = options.index(winner)
        slice_degrees = 360 / num_options
        # The pie is drawn clockwise. To align the middle of the winning slice with the
        # arrow at 0 degrees, we set the start angle accordingly.
        start_angle = (winner_index * slice_degrees) + (slice_degrees / 2)

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(aspect="equal"))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

    colors = ['#3498db', '#e74c3c', '#f1c40f', '#2ecc71', '#9b59b6', '#e67e22', '#1abc9c', '#d35400']
    final_colors = (colors * (num_options // len(colors) + 1))[:num_options]

    explode = [0.0] * num_options
    if winner_index != -1:
        explode[winner_index] = 0.1

    wedges, _ = ax.pie(
        [1] * num_options,
        explode=explode,
        colors=final_colors,
        startangle=start_angle,
        counterclock=False,
        wedgeprops={'edgecolor': 'white', 'linewidth': 3}
    )

    ax.set_title(title, fontsize=32, weight='bold', pad=40, color='#FFD700', path_effects=[withStroke(linewidth=2, foreground='black')])

    for i, p in enumerate(wedges):
        # Calculate the middle angle of the wedge for text placement
        ang = (p.theta1 + p.theta2) / 2
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        wrapped_label = '\n'.join(textwrap.wrap(options[i], 12, break_long_words=False))
        ax.text(x*0.65, y*0.65, wrapped_label, ha='center', va='center', fontsize=24,
                fontweight='bold', color='white',
                path_effects=[withStroke(linewidth=4, foreground='black')])

    # The static arrow pointing at the winner
    ax.add_patch(plt.Polygon([[1.0, 0.1], [1.0, -0.1], [1.2, 0]], fc='#808080', ec='black', lw=1.5))
    ax.axis('equal')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True, dpi=300)
    buf.seek(0)
    plt.close(fig)
    return buf

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configure the Gemini client
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    @commands.Cog.listener()
    async def on_ready(self):
        print("Community Cog is ready.")

    # --- Commands ---

    @app_commands.command(name="askblecknephew", description="Ask Bleck Nephew anything! (Powered by AI)")
    @app_commands.describe(question="The question you want to ask.")
    async def askblecknephew(self, interaction: discord.Interaction, question: str):
        """Answers a user's question using Google's Gemini model."""
        await interaction.response.defer(ephemeral=False)

        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            prompt = f"You are Bleck Nephew, a helpful and slightly mischievous Discord bot. A user has asked you the following question. Keep your answer concise, helpful, and under 250 words. Question: {question}"
            
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
            error_message = f"An unexpected error occurred in askblecknephew: {e}"
            print(error_message)
            await interaction.followup.send(
                "Sorry, I couldn't get an answer. There seems to be an issue with the AI service right now.", 
                ephemeral=True
            )


    @app_commands.command(name="suggest", description="Submit a suggestion for the server.")
    @app_commands.describe(suggestion="Your suggestion.", notes="Any additional notes or details.")
    async def suggest(self, interaction: discord.Interaction, suggestion: str, notes: str = "None"):
        channel = interaction.guild.get_channel(SUGGESTION_CHANNEL_ID)
        
        if not channel:
            await interaction.response.send_message("The suggestion channel could not be found. Please contact an admin.", ephemeral=True)
            return

        embed = discord.Embed(
            title="💡 New Suggestion",
            description=suggestion,
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Suggested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        if notes != "None":
            embed.add_field(name="📝 Additional Notes", value=notes, inline=False)
            
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message("Your suggestion has been submitted successfully!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages in the suggestion channel.", ephemeral=True)

    @app_commands.command(name="announce", description="[Moderator] Create a server announcement.")
    @app_commands.checks.has_any_role("Moderator 🚨🚓", "🚨 Lead moderator")
    @app_commands.describe(
        title="The title of the announcement.",
        content="The main content of the announcement."
    )
    async def announce(self, interaction: discord.Interaction, title: str, content: str):
        channel = interaction.guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)

        if not channel:
            await interaction.response.send_message("The announcement channel could not be found.", ephemeral=True)
            return

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
            await interaction.response.send_message("Announcement created successfully!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages in the announcement channel.", ephemeral=True)

    @app_commands.command(name="poll", description="Create a simple poll.")
    @app_commands.describe(question="The poll question.", options="Up to 10 options, separated by commas.")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        option_list = [opt.strip() for opt in options.split(',')]
        if len(option_list) > 10:
            await interaction.response.send_message("You can only have a maximum of 10 options.", ephemeral=True)
            return

        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        poll_options_text = ""
        for i, option in enumerate(option_list):
            poll_options_text += f"{emojis[i]} {option}\n"

        embed = discord.Embed(
            title=f"📊 Poll: {question}",
            description="React with the emoji corresponding to your choice.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
            
        embed.add_field(name="Options", value=poll_options_text, inline=False)
        embed.set_author(name=f"Poll by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message("Creating poll...")
        poll_message = await interaction.channel.send(embed=embed)

        for i in range(len(option_list)):
            await poll_message.add_reaction(emojis[i])
            
        await interaction.delete_original_response()

    @app_commands.command(name="flip", description="Flip a coin.")
    async def flip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        emoji = "👑" if result == "Heads" else "🪙"
        
        embed = discord.Embed(
            title=f"Coin Flip: It's {result}!",
            color=discord.Color.gold()
        )
        embed.set_author(name=f"Flipped by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_thumbnail(url="https://i.imgur.com/s0z6E5C.gif")
        embed.add_field(name="Result", value=f"{emoji} **{result}**")
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="spinawheel", description="Spin a wheel with a title and comma-separated options.")
    @app_commands.describe(title="The title of the wheel.", options="A comma-separated list of options (e.g., Option A, Option B).")
    async def spinawheel(self, interaction: discord.Interaction, title: str, options: str):
        """Spins a wheel with a title and a list of options."""
        await interaction.response.defer()

        option_list = [opt.strip() for opt in options.split(',')]
        if len(option_list) < 2:
            await interaction.followup.send("Please provide at least two options, separated by commas.", ephemeral=True)
            return

        winner = random.choice(option_list)
        wheel_image_buffer = create_wheel_image(option_list, title, winner=winner)
        wheel_file = discord.File(wheel_image_buffer, filename="spinning_wheel.png")

        embed = discord.Embed(
            title=f"🎡 The Wheel has Spun! 🎡",
            description=f"The wheel, titled **'{title}'**, landed on...",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="👑 Winner", value=f"**{winner}**", inline=False)
        embed.set_image(url="attachment://spinning_wheel.png")
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed, file=wheel_file)


async def setup(bot):
    await bot.add_cog(Community(bot), guilds=[guild_obj])
