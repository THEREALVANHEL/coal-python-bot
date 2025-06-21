import discord
from discord.ext import commands
from discord import app_commands, Permissions
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    admin_perms = Permissions(administrator=True)

    @app_commands.command(name="setwelcomechannel", description="[Admin] Set the channel for welcome messages.")
    @app_commands.guilds(guild_obj)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="The channel to use for welcome messages.")
    async def setwelcomechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "welcome", channel.id)
        await interaction.response.send_message(f"✅ Welcome messages will now be sent to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="setleavechannel", description="[Admin] Set the channel for leave messages.")
    @app_commands.guilds(guild_obj)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="The channel to use for leave messages.")
    async def setleavechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "leave", channel.id)
        await interaction.response.send_message(f"✅ Leave messages will now be sent to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="setlogchannel", description="[Admin] Set the channel for audit logs.")
    @app_commands.guilds(guild_obj)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="The channel to use for audit logs.")
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "log", channel.id)
        await interaction.response.send_message(f"✅ Audit logs will now be sent to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="setlevelingchannel", description="[Admin] Set the channel for level-up announcements.")
    @app_commands.guilds(guild_obj)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="The channel to use for level-up announcements.")
    async def setlevelingchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "leveling", channel.id)
        await interaction.response.send_message(f"✅ Level-up announcements will now be sent to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="setsuggestionchannel", description="[Admin] Set the channel for user suggestions.")
    @app_commands.guilds(guild_obj)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(channel="The channel where suggestions should be posted.")
    async def setsuggestionchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        db.set_channel(interaction.guild.id, "suggestion", channel.id)
        await interaction.response.send_message(f"✅ Suggestions will now be sent to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="setstarboard", description="[Admin] Set the starboard channel and required star count.")
    @app_commands.guilds(guild_obj)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        channel="The channel to use for the starboard.",
        count="The number of stars required to post a message."
    )
    async def setstarboard(self, interaction: discord.Interaction, channel: discord.TextChannel, count: app_commands.Range[int, 1, 100]):
        db.set_starboard(interaction.guild.id, channel.id, count)
        await interaction.response.send_message(f"✅ Starboard enabled. Messages with **{count}** ⭐ will be posted to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="showsettings", description="Show current configured channels.")
    @app_commands.guilds(guild_obj)
    async def showsettings(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        welcome = db.get_channel(guild_id, "welcome")
        leave = db.get_channel(guild_id, "leave")
        log = db.get_channel(guild_id, "log")
        leveling = db.get_channel(guild_id, "leveling")
        suggestion = db.get_channel(guild_id, "suggestion")
        starboard_settings = db.get_starboard_settings(guild_id)
        
        embed = discord.Embed(
            title="🔧 Server Settings",
            description="Here are your current channel settings:",
            color=discord.Color.dark_teal()
        )
        embed.add_field(name="👋 Welcome Channel", value=f"<#{welcome}>" if welcome else "Not set", inline=False)
        embed.add_field(name="👋 Leave Channel", value=f"<#{leave}>" if leave else "Not set", inline=False)
        embed.add_field(name="📝 Log Channel", value=f"<#{log}>" if log else "Not set", inline=False)
        embed.add_field(name="🌌 Leveling Channel", value=f"<#{leveling}>" if leveling else "Not set", inline=False)
        embed.add_field(name="💡 Suggestion Channel", value=f"<#{suggestion}>" if suggestion else "Not set", inline=False)

        if starboard_settings and "starboard_channel" in starboard_settings:
            channel_id = starboard_settings["starboard_channel"]
            star_count = starboard_settings.get("starboard_star_count", "N/A")
            starboard_info = f"<#{channel_id}> ({star_count} ⭐ required)"
        else:
            starboard_info = "Not set"
        embed.add_field(name="⭐ Starboard Channel", value=starboard_info, inline=False)

        embed.set_footer(text="Futuristic UK Settings | BLEK NEPHEW", icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Settings(bot))
