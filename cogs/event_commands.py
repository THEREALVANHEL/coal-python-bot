import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

def is_event_host():
    """Custom check to verify if the user is an event host or admin."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        
        host_roles = ["Host", "Head Host 🍵"]
        
        has_role = any(role.name in host_roles for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("You don't have the required role (Host) to use this command.", ephemeral=True)
        return has_role
    return app_commands.check(predicate)

class EventCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shout", description="[Host] Creates and sends a formatted event announcement.")
    @app_commands.guilds(guild_obj)
    @is_event_host()
    @app_commands.describe(
        channel="The channel to send the announcement to.",
        title="The title of the event.",
        description="A description of the event.",
        image="An optional image to attach to the announcement."
    )
    async def shout(self, interaction: discord.Interaction, channel: discord.TextChannel, title: str, description: str, image: discord.Attachment = None):
        embed = discord.Embed(
            title=f"🎉 {title} 🎉",
            description=description,
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Event hosted by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        if image:
            embed.set_image(url=image.url)
        
        embed.set_footer(text="Get ready for the fun!")

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permissions to send messages in that channel.", ephemeral=True)

    @app_commands.command(name="gamelog", description="[Host] Post a summary log of a completed game event.")
    @app_commands.guilds(guild_obj)
    @is_event_host()
    @app_commands.describe(
        title="The title of the game that was played.",
        winners="The winner(s) of the game. (e.g., @user1, @user2).",
        participants="A list of participants in the event.",
        notes="Any additional notes or summary of the event."
    )
    async def gamelog(self, interaction: discord.Interaction, title: str, winners: str, participants: str, notes: str):
        log_channel_id = db.get_channel(interaction.guild.id, "gamelog")
        if not log_channel_id:
            return await interaction.response.send_message("The game log channel has not been set up. Please ask an admin to set it.", ephemeral=True)
        
        log_channel = interaction.guild.get_channel(log_channel_id)
        if not log_channel:
            return await interaction.response.send_message("I couldn't find the game log channel. Please contact an admin.", ephemeral=True)
            
        embed = discord.Embed(
            title=f"📜 Game Log: {title}",
            color=discord.Color.from_rgb(153, 102, 204), # A nice purple
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Logged by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        embed.add_field(name="🏆 Winner(s)", value=winners, inline=False)
        embed.add_field(name="👥 Participants", value=participants, inline=False)
        embed.add_field(name="📝 Notes", value=notes, inline=False)
        
        embed.set_footer(text="Another great event concluded!")

        try:
            await log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Game log posted successfully to {log_channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages in the game log channel.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(EventCommands(bot)) 