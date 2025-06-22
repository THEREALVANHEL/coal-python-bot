import discord
from discord.ext import commands
from discord import app_commands, Permissions
import sys
import os
from datetime import datetime

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

    @app_commands.command(name="botdebug", description="[Owner] Shows a debug panel with loaded cogs and commands.")
    @app_commands.guilds(guild_obj)
    @commands.is_owner()
    async def botdebug(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="🤖 Bot Debug Panel",
            description=f"**Bot Name:** {self.bot.user.name}\n**Bot ID:** {self.bot.user.id}",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )

        loaded_cogs = ", ".join(self.bot.cogs.keys())
        embed.add_field(name="✅ Loaded Cogs", value=f"```\n{loaded_cogs}\n```", inline=False)

        commands_list = await self.bot.tree.fetch_commands(guild=guild_obj)
        if commands_list:
            command_names = [f"/{cmd.name}" for cmd in commands_list]
            commands_str = ", ".join(command_names)
            if len(commands_str) > 1000:
                parts = []
                current_part = ""
                for name in command_names:
                    if len(current_part) + len(name) > 1000:
                        parts.append(current_part)
                        current_part = ""
                    current_part += name + ", "
                parts.append(current_part.strip(', '))
                for i, part in enumerate(parts):
                    embed.add_field(name=f" Slash Commands (Part {i+1})", value=f"```\n{part}\n```", inline=False)
            else:
                embed.add_field(name=" Slash Commands", value=f"```\n{commands_str}\n```", inline=False)
        else:
            embed.add_field(name=" Slash Commands", value="No slash commands registered.", inline=False)

        embed.set_footer(text=f"Latency: {round(self.bot.latency * 1000)}ms")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ⭐ Starboard Listener
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != "⭐":
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        starboard_settings = db.get_starboard_settings(payload.guild_id)
        if not starboard_settings:
            return

        starboard_channel_id = starboard_settings.get("starboard_channel")
        required_stars = starboard_settings.get("starboard_star_count", 3)
        starboard_channel = guild.get_channel(starboard_channel_id)
        if not starboard_channel:
            return

        channel = guild.get_channel(payload.channel_id)
        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return

        star_reaction = next((r for r in message.reactions if r.emoji == "⭐"), None)
        if not star_reaction or star_reaction.count < required_stars:
            return

        if message.author.bot:
            return

        embed = discord.Embed(
            description=message.content or "*No text content*",
            color=discord.Color.gold(),
            timestamp=message.created_at
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.set_footer(text=f"⭐ {star_reaction.count} | #{channel.name}")

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        await starboard_channel.send(embed=embed)

# Setup the Cog
async def setup(bot):
    await bot.add_cog(Settings(bot))
