import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import sys
import os
import re
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# --- Helper to parse time string ---
def parse_time(time_str: str) -> Optional[datetime]:
    """Parses a time string like '1h30m' or 'in 1 hour' into a future datetime object."""
    # For formats like "in 1 hour", "in 30 minutes"
    match = re.match(r'in\s+(\d+)\s+(hour|minute|day)s?', time_str, re.IGNORECASE)
    if match:
        value = int(match.group(1))
        unit = match.group(2).lower()
        if unit == 'hour':
            return datetime.utcnow() + timedelta(hours=value)
        elif unit == 'minute':
            return datetime.utcnow() + timedelta(minutes=value)
        elif unit == 'day':
            return datetime.utcnow() + timedelta(days=value)

    # For formats like "1h30m", "1d", "30m"
    seconds = 0
    matches = re.findall(r'(\d+)\s*(d|h|m|s)', time_str, re.IGNORECASE)
    if not matches:
        return None
        
    for value, unit in matches:
        value = int(value)
        if unit == 'd': seconds += value * 86400
        elif unit == 'h': seconds += value * 3600
        elif unit == 'm': seconds += value * 60
        elif unit == 's': seconds += value
        
    return datetime.utcnow() + timedelta(seconds=seconds)

# --- Event View with Join Button ---
class EventJoinView(discord.ui.View):
    def __init__(self, host: discord.Member, title: str):
        super().__init__(timeout=None) # Persistent view
        self.host = host
        self.title = title
        self.participants = []

    def generate_embed(self, interaction: discord.Interaction):
        """Generates the event embed based on the current state."""
        original_embed = interaction.message.embeds[0]
        
        # We replace the participants field or add it if it doesn't exist
        participant_list = "No one has joined yet."
        if self.participants:
            participant_list = "\n".join([f"- <@{p_id}>" for p_id in self.participants])
        
        # Find and update the field
        field_found = False
        for i, field in enumerate(original_embed.fields):
            if field.name == "👥 Participants":
                original_embed.set_field_at(i, name="👥 Participants", value=participant_list, inline=False)
                field_found = True
                break
        
        if not field_found:
             original_embed.add_field(name="👥 Participants", value=participant_list, inline=False)

        return original_embed

    @discord.ui.button(label="Join Event", style=discord.ButtonStyle.success, custom_id="event_join_button")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.participants:
            await interaction.response.send_message("You have already joined this event!", ephemeral=True)
            return
        
        self.participants.append(user_id)
        embed = self.generate_embed(interaction)
        await interaction.response.edit_message(embed=embed)


def is_event_host():
    """Custom check to verify if the user is an event host or admin."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        
        host_roles = ["Host", "Head Host 🍵", "Guide", "Medic"] # Added more roles
        
        has_role = any(role.name in host_roles for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("You don't have the required role to use this command.", ephemeral=True)
        return has_role
    return app_commands.check(predicate)

class EventCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # We register the view with dummy data. The actual data is passed when the view is created.
        # This is necessary for persistent views to be recognized on bot startup.
        if not hasattr(bot, 'persistent_views_added'):
             bot.add_view(EventJoinView(host=None, title=""))
             bot.persistent_views_added = True

    @app_commands.command(name="shout", description="[Host] Creates and sends a formatted event announcement.")
    @app_commands.guilds(guild_obj)
    @is_event_host()
    @app_commands.describe(
        gamename="The name/title of the event.",
        description="A description of the event.",
        time="When the event starts (e.g., 'in 1 hour', '1h30m').",
        channel="The channel to send the announcement to.",
        host="The host(s) for the event.",
        cohost="The co-host(s) for the event (optional).",
        medic_team="The medic team for the event (optional).",
        guide_team="The guide team for the event (optional).",
        joining_option="Information on how to join the event (optional)."
    )
    async def shout(self, interaction: discord.Interaction, 
                  gamename: str, description: str, time: str, channel: discord.TextChannel, host: str,
                  cohost: Optional[str] = None, medic_team: Optional[str] = None,
                  guide_team: Optional[str] = None, joining_option: Optional[str] = None):
        
        start_time_obj = parse_time(time)
        if not start_time_obj:
            return await interaction.response.send_message("Invalid time format. Please use a format like 'in 1 hour' or '1h30m'.", ephemeral=True)
        
        unix_timestamp = int(start_time_obj.timestamp())

        embed = discord.Embed(
            title=f"🎉 {gamename} 🎉",
            description=description,
            color=discord.Color.blurple(),
        )
        embed.set_author(name=f"Event Announcement", icon_url=interaction.guild.icon.url)
        
        details = f"**Host:** {host}\n"
        if cohost: details += f"**Co-Host:** {cohost}\n"
        if medic_team: details += f"**Medic Team:** {medic_team}\n"
        if guide_team: details += f"**Guide Team:** {guide_team}\n"
        embed.add_field(name="📋 Event Staff", value=details, inline=False)
            
        embed.add_field(name="⏰ Starts", value=f"<t:{unix_timestamp}:F> (<t:{unix_timestamp}:R>)", inline=False)

        if joining_option:
            embed.add_field(name="🔗 How to Join", value=joining_option, inline=False)
        
        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permissions to send messages in that channel.", ephemeral=True)

    @app_commands.command(name="gamelog", description="[Host] Post a summary log of a completed game event.")
    @app_commands.guilds(guild_obj)
    @is_event_host()
    @app_commands.describe(
        channel="The channel to send the game log to.",
        host="The host(s) of the game.",
        cohost="The co-host(s) of the game (optional).",
        medic_team="The medic team for the game (optional).",
        guide_team="The guide team for the game (optional).",
        participants="A list of all participants in the event.",
        timings="The start and end times of the event.",
        summary="A summary of what happened in the event.",
        picture="A URL to an image for the log (optional)."
    )
    async def gamelog(self, interaction: discord.Interaction, 
                  channel: discord.TextChannel, host: str, participants: str, timings: str, summary: str,
                  cohost: Optional[str] = None, 
                  medic_team: Optional[str] = None, 
                  guide_team: Optional[str] = None, 
                  picture: Optional[str] = None):
            
        embed = discord.Embed(
            title=f"📜 Game Log",
            description=summary,
            color=discord.Color.from_rgb(153, 102, 204), # A nice purple
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Logged by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        staff_info = f"**Host:** {host}\n"
        if cohost: staff_info += f"**Co-host:** {cohost}\n"
        if guide_team: staff_info += f"**Guide Team:** {guide_team}\n"
        if medic_team: staff_info += f"**Medic Team:** {medic_team}"
        embed.add_field(name="👑 Staff", value=staff_info, inline=False)
        
        embed.add_field(name="👥 Participants", value=participants, inline=False)
        embed.add_field(name="⏱️ Timings", value=timings, inline=False)
        
        if picture:
            # Basic URL validation
            if picture.startswith("http://") or picture.startswith("https://"):
                embed.set_image(url=picture)

        embed.set_footer(text="Another great event concluded!")

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Game log posted successfully to {channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages in the game log channel.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(EventCommands(bot))