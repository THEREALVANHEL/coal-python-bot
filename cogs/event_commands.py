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
        title="The title of the event.",
        description="A description of the event.",
        starttime="When the event starts (e.g., 'in 1 hour', '30m', '1d 2h').",
        channel="The channel to send the announcement to.",
        host="The main host for the event.",
        cohost="The co-host for the event (optional).",
        medic="The medic for the event (optional).",
        guide="The guide for the event (optional).",
        gamelist="A list of games to be played (optional).",
        image="An optional image to attach to the announcement."
    )
    async def shout(self, interaction: discord.Interaction, 
                  title: str, description: str, starttime: str, channel: discord.TextChannel,
                  host: discord.Member, cohost: discord.Member = None, medic: discord.Member = None,
                  guide: discord.Member = None, gamelist: str = None, image: discord.Attachment = None):
        
        start_time_obj = parse_time(starttime)
        if not start_time_obj:
            return await interaction.response.send_message("Invalid time format. Please use a format like 'in 1 hour' or '1h30m'.", ephemeral=True)
        
        unix_timestamp = int(start_time_obj.timestamp())

        embed = discord.Embed(
            title=f"🎉 {title} 🎉",
            description=description,
            color=discord.Color.blurple(),
        )
        embed.set_author(name=f"Event Announcement", icon_url=interaction.guild.icon.url)
        
        # --- Event Details ---
        details = f"**Host:** {host.mention}\n"
        if cohost: details += f"**Co-Host:** {cohost.mention}\n"
        if medic: details += f"**Medic:** {medic.mention}\n"
        if guide: details += f"**Guide:** {guide.mention}\n"
        embed.add_field(name="📋 Event Staff", value=details, inline=False)
        
        if gamelist:
            embed.add_field(name="🎮 Gamelist", value=gamelist, inline=False)
            
        embed.add_field(name="⏰ Starts", value=f"<t:{unix_timestamp}:F> (<t:{unix_timestamp}:R>)", inline=False)

        if image:
            embed.set_image(url=image.url)
        
        embed.set_footer(text="Click 'Join Event' to participate!")

        view = EventJoinView(host=host, title=title)
        
        try:
            await channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permissions to send messages in that channel.", ephemeral=True)

    @app_commands.command(name="gamelog", description="[Host] Post a summary log of a completed game event.")
    @app_commands.guilds(guild_obj)
    @is_event_host()
    @app_commands.describe(
        title="The title of the game that was played.",
        host="The host of the game.",
        cohost="The co-host of the game. Mention 'None' if there wasn't one.",
        guide="The guide for the game. Mention 'None' if there wasn't one.",
        medic="The medic for the game. Mention 'None' if there wasn't one.",
        participants="A list of all participants in the event.",
        summary="A summary of what happened in the event.",
        notes="Any additional notes about the event.",
        picture="An optional picture to include in the log."
    )
    async def gamelog(self, interaction: discord.Interaction, 
                  title: str, host: discord.Member, cohost: str, guide: str, medic: str,
                  participants: str, summary: str, notes: Optional[str] = None, picture: Optional[discord.Attachment] = None):
        
        log_channel_id = db.get_channel(interaction.guild.id, "gamelog")
        if not log_channel_id:
            return await interaction.response.send_message("The game log channel has not been set up. Please ask an admin to set it.", ephemeral=True)
        
        log_channel = interaction.guild.get_channel(log_channel_id)
        if not log_channel:
            return await interaction.response.send_message("I couldn't find the game log channel. Please contact an admin.", ephemeral=True)
            
        embed = discord.Embed(
            title=f"📜 Game Log: {title}",
            description=summary,
            color=discord.Color.from_rgb(153, 102, 204), # A nice purple
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Logged by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        staff_info = f"**Host:** {host.mention}\n"
        if cohost.lower() != 'none': staff_info += f"**Co-host:** {cohost}\n"
        if guide.lower() != 'none': staff_info += f"**Guide:** {guide}\n"
        if medic.lower() != 'none': staff_info += f"**Medic:** {medic}"
        embed.add_field(name="👑 Staff", value=staff_info, inline=False)
        
        embed.add_field(name="👥 Participants", value=participants, inline=False)
        
        if notes:
            embed.add_field(name="📝 Notes", value=notes, inline=False)
        
        if picture:
            embed.set_image(url=picture.url)

        embed.set_footer(text="Another great event concluded!")

        try:
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Game log posted successfully to {log_channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages in the game log channel.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(EventCommands(bot)) 