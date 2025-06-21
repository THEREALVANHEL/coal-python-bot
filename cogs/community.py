import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
from datetime import datetime

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

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
            
        embed.set_footer(text="Please be respectful and follow all server rules during the event.")

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
        co_host="The co-host of the event (optional).",
        medic_team="The users on the medic team (optional).",
        guide_team="The users on the guide team (optional).",
        notes="Any additional notes from the event (optional).",
        picture="A picture from the event (optional)."
    )
    async def gamelog(self, interaction: discord.Interaction,
                      channel: discord.TextChannel,
                      title: str,
                      game_summary: str,
                      host: discord.Member,
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
        
        embed.add_field(name="⛑️ Medic Team", value=medic_team, inline=True)
        embed.add_field(name="🗺️ Guide Team", value=guide_team, inline=True)
        
        if notes != "None":
            embed.add_field(name="📋 Additional Notes", value=notes, inline=False)
        
        if picture:
            embed.set_image(url=picture.url)
            
        embed.set_footer(text="Thank you to all who participated!")

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Game log sent successfully to {channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages or upload images in that channel.", ephemeral=True)

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
            color=discord.Color.light_grey(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Suggested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        try:
            message = await suggestion_channel.send(embed=embed)
            await message.add_reaction("👍")
            await message.add_reaction("👎")
            await interaction.response.send_message(f"✅ Your suggestion has been submitted to {suggestion_channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages or add reactions in the suggestion channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Community(bot)) 