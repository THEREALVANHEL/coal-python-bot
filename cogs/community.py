import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
from datetime import datetime
from typing import Optional
import random
import asyncio
import io
import numpy as np
import matplotlib.pyplot as plt
import openai
from matplotlib.patheffects import withStroke
import textwrap

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

def create_wheel_image(options, title, winner=None):
    """Generates a simple, flat image of a spinning wheel."""
    
    num_options = len(options)
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(aspect="equal"))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

    # Simple, bright, flat colors like the example
    colors = ['#3498db', '#e74c3c', '#f1c40f', '#2ecc71', '#9b59b6', '#e67e22']
    
    final_colors = (colors * (num_options // len(colors) + 1))[:num_options]
    
    explode = [0] * num_options
    if winner and winner in options:
        winner_index = options.index(winner)
        explode[winner_index] = 0.1
        
    wedges, _ = ax.pie(
        [1] * num_options,
        explode=explode,
        colors=final_colors,
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )

    # Add more visible text labels, without rotation
    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        
        # Wrap long text
        wrapped_label = '\n'.join(textwrap.wrap(options[i], 10, break_long_words=False))
        
        ax.text(x*0.65, y*0.65, wrapped_label, ha='center', va='center', fontsize=16,
                fontweight='bold', color='white',
                path_effects=[withStroke(linewidth=4, foreground='black')])

    # Add a simple pointer on the right
    ax.add_patch(plt.Polygon([[1.0, 0.1], [1.0, -0.1], [1.2, 0]], fc='#808080', ec='black', lw=1.5))
    
    # Add a title at the top
    if title:
        fig.suptitle(title, fontsize=24, weight='bold', y=1.02)
    
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def check_is_event_host(self, interaction: discord.Interaction):
        """Checks if the user has event host roles or is an admin."""
        author = interaction.user
        if isinstance(author, discord.Member):
            # Role IDs for 'Host' and 'Head Host 🍵'
            allowed_role_ids = [1371003310223654974, 1378338515791904808]
            user_role_ids = {role.id for role in author.roles}

            if author.guild_permissions.administrator or any(role_id in user_role_ids for role_id in allowed_role_ids):
                return True
                
        await interaction.response.send_message("❌ You need to be a Host, Head Host, or an Administrator to use this command.", ephemeral=True)
        return False

    @app_commands.command(name="shout", description="[Event Host] Create a formatted event announcement.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(
        channel="The channel to send the announcement to.",
        title="The title of the event (e.g., 'Roblox Expo').",
        game_link="The link to the Roblox game.",
        timing="The date and time of the event.",
        host="The main host of the event.",
        co_host="The co-host of the event (optional).",
        medic_team="The users on the medic team (optional).",
        guide_team="The users on the guide team (optional).",
        notes="Any additional notes for the event (optional)."
    )
    async def shout(self, interaction: discord.Interaction, 
                    channel: discord.TextChannel,
                    title: str,
                    game_link: str,
                    timing: str,
                    host: discord.Member,
                    co_host: discord.Member = None,
                    medic_team: str = "None",
                    guide_team: str = "None",
                    notes: str = "None"):
        
        if not await self.check_is_event_host(interaction):
            return

        embed = discord.Embed(
            title=f"🎉 {title}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Event Announcement by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        embed.add_field(name="Host", value=host.mention, inline=True)
        if co_host:
            embed.add_field(name="Co-Host", value=co_host.mention, inline=True)
        
        embed.add_field(name="⏰ Timing", value=timing, inline=False)
        embed.add_field(name="🔗 Game Link", value=f"[Click Here]({game_link})", inline=False)
        
        embed.add_field(name="⛑️ Medic Team", value=medic_team, inline=True)
        embed.add_field(name="🗺️ Guide Team", value=guide_team, inline=True)
        
        if notes != "None":
            embed.add_field(name="📝 Additional Notes", value=notes, inline=False)
            
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Announcement sent successfully to {channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)

    @app_commands.command(name="gamelog", description="[Event Host] Log the summary of a completed game event.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(
        channel="The channel to post the game log to.",
        title="The title of the event that was hosted.",
        game_summary="A summary of what happened during the event.",
        host="The main host of the event.",
        participants="The users who participated (you can @mention them).",
        co_host="The co-host of the event (optional).",
        medic_team="The users or roles on the medic team (you can @mention them).",
        guide_team="The users or roles on the guide team (optional).",
        notes="Any additional notes from the event (optional).",
        picture="A picture from the event (optional)."
    )
    async def gamelog(self, interaction: discord.Interaction,
                      channel: discord.TextChannel,
                      title: str,
                      game_summary: str,
                      host: discord.Member,
                      participants: str,
                      co_host: discord.Member = None,
                      medic_team: str = "None",
                      guide_team: str = "None",
                      notes: str = "None",
                      picture: discord.Attachment = None):
        
        if not await self.check_is_event_host(interaction):
            return

        embed = discord.Embed(
            title=f"📝 Game Log: {title}",
            description=game_summary,
            color=discord.Color.dark_green(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Log submitted by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        embed.add_field(name="Host", value=host.mention, inline=True)
        if co_host:
            embed.add_field(name="Co-Host", value=co_host.mention, inline=True)
        
        embed.add_field(name="👥 Participants", value=participants, inline=False)
        
        embed.add_field(name="⛑️ Medic Team", value=medic_team, inline=True)
        embed.add_field(name="🗺️ Guide Team", value=guide_team, inline=True)
        
        if notes != "None":
            embed.add_field(name="📋 Additional Notes", value=notes, inline=False)
        
        if picture:
            embed.set_image(url=picture.url)
            
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Game log sent successfully to {channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages or upload images in that channel.", ephemeral=True)

    @app_commands.command(name="poll", description="Create a simple poll with up to 10 options.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(
        question="The question you want to ask.",
        option1="The first choice for the poll.",
        option2="The second choice for the poll.",
        option3="The third choice for the poll (optional).",
        option4="The fourth choice for the poll (optional).",
        option5="The fifth choice for the poll (optional).",
        option6="The sixth choice for the poll (optional).",
        option7="The seventh choice for the poll (optional).",
        option8="The eighth choice for the poll (optional).",
        option9="The ninth choice for the poll (optional).",
        option10="The tenth choice for the poll (optional)."
    )
    async def poll(self, interaction: discord.Interaction, 
                 question: str, 
                 option1: str, 
                 option2: str,
                 option3: Optional[str] = None, option4: Optional[str] = None, option5: Optional[str] = None,
                 option6: Optional[str] = None, option7: Optional[str] = None, option8: Optional[str] = None,
                 option9: Optional[str] = None, option10: Optional[str] = None):
        
        options = [opt for opt in [option1, option2, option3, option4, option5, option6, option7, option8, option9, option10] if opt is not None]
        
        embed = discord.Embed(
            title=f"📊 {question}",
            description="Vote by reacting with the corresponding number!",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        poll_options_text = ""
        for i, option in enumerate(options):
            poll_options_text += f"{number_emojis[i]} {option}\n"
            
        embed.add_field(name="Options", value=poll_options_text, inline=False)
        embed.set_author(name=f"Poll by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message("Creating your poll...", ephemeral=True)
        poll_message = await interaction.channel.send(embed=embed)
        
        for i in range(len(options)):
            await poll_message.add_reaction(number_emojis[i])

    @app_commands.command(name="askblecknephew", description="Ask Blecknephew a question.")
    @app_commands.describe(question="The question you want to ask.")
    @app_commands.guilds(guild_obj)
    async def askblecknephew(self, interaction: discord.Interaction, question: str):
        # Securely get the API key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await interaction.response.send_message(
                "❌ The OpenAI API key is not configured. An administrator needs to set the `OPENAI_API_KEY` environment variable.",
                ephemeral=True
            )
            return
        
        openai.api_key = api_key

        await interaction.response.defer() # Acknowledge the interaction and show a "thinking..." state

        try:
            # Asynchronous API call
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful and wise Discord bot assistant named Blecknephew. Provide clear and concise answers."},
                    {"role": "user", "content": question}
                ]
            )
            answer = response.choices[0].message.content.strip()

            embed = discord.Embed(
                title=f"🤔 {question}",
                description=answer,
                color=discord.Color.blue()
            )
            embed.set_author(name=f"A question from {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
            
            await interaction.followup.send(embed=embed)

        except openai.APIStatusError as e:
            error_message = f"An error occurred while contacting OpenAI (APIStatusError): {e}"
            print(error_message)
            # Add a specific message for 429 (quota/billing issues)
            if e.status_code == 429:
                await interaction.followup.send(
                    "Sorry, I can't answer right now. This is likely due to an issue with the API key's billing/quota (e.g., expired free trial). Please check the OpenAI dashboard.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"Sorry, I couldn't get an answer. The AI service reported an error: `{e.status_code}`.",
                    ephemeral=True
                )
        except openai.APIConnectionError as e:
            error_message = f"An error occurred while contacting OpenAI (APIConnectionError): {e}"
            print(error_message)
            await interaction.followup.send(
                "Sorry, I couldn't get an answer. I'm having trouble connecting to the AI service.", 
                ephemeral=True
            )
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            print(error_message) # Log the full error for debugging
            await interaction.followup.send(
                "Sorry, I couldn't get an answer. There might be an issue with the AI service.", 
                ephemeral=True
            )

    @app_commands.command(name="flip", description="Flip a coin.")
    @app_commands.guilds(guild_obj)
    async def flip(self, interaction: discord.Interaction):
        """Flips a coin and sends the result."""
        
        result = random.choice(["Heads", "Tails"])
        
        embed = discord.Embed(
            title="<:coin:1234567890> Coin Flip", # Placeholder, replace with a real coin emoji if you have one
            description=f"The coin landed on... **{result}**!",
            color=discord.Color.gold() if result == "Heads" else discord.Color.light_grey()
        )
        
        if result == "Heads":
            embed.set_thumbnail(url="https://i.imgur.com/M6X2V3X.png") # A simple heads image
        else:
            embed.set_thumbnail(url="https://i.imgur.com/B6aM4y0.png") # A simple tails image
            
        embed.set_author(name=f"{interaction.user.display_name} flipped a coin", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="suggest", description="Submit a suggestion for the server.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(suggestion="Your suggestion for the server.")
    async def suggest(self, interaction: discord.Interaction, *, suggestion: str):
        suggestion_channel_id = db.get_channel(interaction.guild.id, "suggestion")
        if not suggestion_channel_id:
            await interaction.response.send_message("The suggestion channel has not been set up yet!", ephemeral=True)
            return

        suggestion_channel = interaction.guild.get_channel(suggestion_channel_id)
        if not suggestion_channel:
            await interaction.response.send_message("I can't find the suggestion channel. Please contact an admin.", ephemeral=True)
            return

        embed = discord.Embed(
            title="💡 New Suggestion",
            description=suggestion,
            color=discord.Color.from_rgb(225, 225, 225), # Light Grey
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Suggested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        try:
            message = await suggestion_channel.send(embed=embed)
            await message.add_reaction("👍")
            await message.add_reaction("👎")
            await interaction.response.send_message(f"✅ Your suggestion has been submitted to {suggestion_channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages or add reactions in the suggestion channel.", ephemeral=True)

    @app_commands.command(name="spinawheel", description="Spin a wheel with your own custom options!")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(
        title="The title for the wheel spin.",
        options="A comma-separated list of options for the wheel (e.g., 'red, blue, green')."
    )
    async def spinawheel(self, interaction: discord.Interaction, title: str, options: str):
        
        # Parse the options from the comma-separated string
        option_list = [opt.strip() for opt in options.split(',') if opt.strip()]

        if len(option_list) < 2:
            await interaction.response.send_message("Please provide at least two options separated by commas.", ephemeral=True)
            return

        if len(option_list) > 50: # Set a reasonable limit
            await interaction.response.send_message("You can have a maximum of 50 options.", ephemeral=True)
            return
        
        # Initial response
        wheel_image_buf = create_wheel_image(option_list, title)
        wheel_file = discord.File(fp=wheel_image_buf, filename="wheel.png")

        embed = discord.Embed(
            title=f"🎡 {title}",
            description=f"The wheel is spinning with {len(option_list)} options!",
            color=discord.Color.dark_gold()
        )
        embed.set_image(url="attachment://wheel.png")
        embed.set_author(name=f"{interaction.user.display_name} is spinning...", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed, file=wheel_file)

        # Suspense
        await asyncio.sleep(4)

        # Choose the winner
        winner = random.choice(option_list)

        # Create the result image
        result_image_buf = create_wheel_image(option_list, title, winner=winner)
        result_file = discord.File(fp=result_image_buf, filename="wheel_result.png")

        result_embed = discord.Embed(
            title=f"🎡 {title}",
            description=f"Out of the provided options, the winner is...",
            color=discord.Color.green()
        )
        result_embed.set_author(name=f"Spin result for {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        result_embed.add_field(name="Landed on:", value=f"**🎉 {winner} 🎉**", inline=False)
        result_embed.set_image(url="attachment://wheel_result.png")
        result_embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)

        await interaction.edit_original_response(embed=result_embed, attachments=[result_file])

async def setup(bot):
    await bot.add_cog(Community(bot)) 