import discord
from discord.ext import commands
from discord import app_commands
import os
import sys

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setwelcomechannel", description="[Admin] Set the welcome channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "welcome", channel.id)
        await interaction.response.send_message(f"✅ Welcome messages will go to {channel.mention}", ephemeral=True)

    @app_commands.command(name="setleavechannel", description="[Admin] Set the leave channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_leave(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "leave", channel.id)
        await interaction.response.send_message(f"✅ Leave messages will go to {channel.mention}", ephemeral=True)

    @app_commands.command(name="setlogchannel", description="[Admin] Set the log channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_log(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "log", channel.id)
        await interaction.response.send_message(f"✅ Logs will go to {channel.mention}", ephemeral=True)

    @app_commands.command(name="setlevelingchannel", description="[Admin] Set the leveling announcement channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_leveling(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "leveling", channel.id)
        await interaction.response.send_message(f"✅ Leveling announcements will go to {channel.mention}", ephemeral=True)

    @app_commands.command(name="showsettings", description="Show the current channel settings.")
    async def show_settings(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        welcome = db.get_channel(guild_id, "welcome")
        leave = db.get_channel(guild_id, "leave")
        log = db.get_channel(guild_id, "log")
        leveling = db.get_channel(guild_id, "leveling")

        embed = discord.Embed(
            title="🔧 Server Settings",
            color=discord.Color.dark_teal()
        )
        embed.add_field(name="👋 Welcome Channel", value=f"<#{welcome}>" if welcome else "Not set", inline=False)
        embed.add_field(name="👋 Leave Channel", value=f"<#{leave}>" if leave else "Not set", inline=False)
        embed.add_field(name="📝 Log Channel", value=f"<#{log}>" if log else "Not set", inline=False)
        embed.add_field(name="🌌 Leveling Channel", value=f"<#{leveling}>" if leveling else "Not set", inline=False)
        embed.set_footer(text="Futuristic UK Settings | BLEK NEPHEW", icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Settings(bot), guilds=[guild_obj])
