"""
cogs/settings.py
Server-configuration & starboard management commands
"""

import os
import sys
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands, Permissions

# ─────────────────────────────────────────────────────────────
# Locate database.py one level up from /cogs
# ─────────────────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db  # noqa: E402  (import after path tweak)

# ─────────────────────────────────────────────────────────────
# Guild scope (replace with your own ID if needed)
# ─────────────────────────────────────────────────────────────
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)


class Settings(commands.Cog):
    """Admin-only server-settings & starboard cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------------------------------------------------
    # Channel setters
    # ---------------------------------------------------------
    admin_perms = Permissions(administrator=True)
    _channel_types = {
        "welcome": ("👋 Welcome", "welcome"),
        "leave": ("👋 Leave", "leave"),
        "log": ("📝 Log", "log"),
        "leveling": ("🌌 Leveling", "leveling"),
        "suggestion": ("💡 Suggestion", "suggestion"),
    }

    def _register_setter(name: str, label: str):
        """Dynamically attach /setXchannel slash-commands."""

        @app_commands.command(
            name=f"set{name}channel", description=f"[Admin] Set the {label.lower()} channel."
        )
        @app_commands.guilds(guild_obj)
        @app_commands.default_permissions(administrator=True)
        @app_commands.describe(channel=f"The channel to use for {label.lower()} messages.")
        async def _cmd(self, interaction: discord.Interaction, channel: discord.TextChannel):
            db.set_channel(interaction.guild.id, name, channel.id)
            await interaction.response.send_message(
                f"✅ {label} messages will now be sent to {channel.mention}.", ephemeral=True
            )

        return _cmd

    # Generate setters for welcome/leave/log/leveling/suggestion
    for _key, (_label, _db_key) in _channel_types.items():
        locals()[f"set{_key}channel"] = _register_setter(_db_key, _label)
    del _key, _label, _db_key, _register_setter  # clean namespace

    # ---------------------------------------------------------
    # /setstarboard
    # ---------------------------------------------------------
    @app_commands.command(
        name="setstarboard",
        description="[Admin] Set the starboard channel and required star count.",
    )
    @app_commands.guilds(guild_obj)
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        channel="Channel to post starred messages.",
        count="Stars required to post (1-100).",
    )
    async def setstarboard(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        count: app_commands.Range[int, 1, 100],
    ):
        db.set_starboard(interaction.guild.id, channel.id, count)
        await interaction.response.send_message(
            f"✅ Starboard enabled. Messages with **{count}** ⭐ will be posted to {channel.mention}.",
            ephemeral=True,
        )

    # ---------------------------------------------------------
    # /showsettings
    # ---------------------------------------------------------
    @app_commands.command(name="showsettings", description="Display current channel settings.")
    @app_commands.guilds(guild_obj)
    async def showsettings(self, interaction: discord.Interaction):
        g_id = interaction.guild.id
        embed = discord.Embed(
            title="🔧 Server Settings",
            color=discord.Color.dark_teal(),
        )

        # core channels
        for key, (label, db_key) in self._channel_types.items():
            chan_id = db.get_channel(g_id, db_key)
            embed.add_field(
                name=f"{label} Channel",
                value=f"<#{chan_id}>" if chan_id else "Not set",
                inline=False,
            )

        # starboard
        sb = db.get_starboard_settings(g_id)
        if sb:
            sb_val = f"<#{sb['starboard_channel']}> ({sb.get('starboard_star_count', 'N/A')} ⭐)"
        else:
            sb_val = "Not set"
        embed.add_field(name="⭐ Starboard Channel", value=sb_val, inline=False)

        embed.set_footer(
            text="VANHELISMYSENSEI Settings",
            icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------------------------------------------------------
    # /botdebug  (owner-only)
    # ---------------------------------------------------------
    @app_commands.command(
        name="botdebug", description="[Owner] Show loaded cogs and synced commands."
    )
    @app_commands.guilds(guild_obj)
    @commands.is_owner()
    async def botdebug(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="🤖 Bot Debug Panel",
            description=f"**Bot:** {self.bot.user} (`{self.bot.user.id}`)",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow(),
        )
        embed.add_field(
            name="✅ Loaded Cogs",
            value="```\n" + ", ".join(self.bot.cogs.keys()) + "\n```",
            inline=False,
        )

        cmds = await self.bot.tree.fetch_commands(guild=guild_obj)
        names = sorted(f"/{c.name}" for c in cmds)
        chunks = []
        chunk = ""
        for n in names:
            if len(chunk) + len(n) > 1000:
                chunks.append(chunk.rstrip(", "))
                chunk = ""
            chunk += n + ", "
        chunks.append(chunk.rstrip(", "))

        for i, ch in enumerate(chunks, 1):
            embed.add_field(name=f"Slash Commands (part {i})", value=f"```\n{ch}\n```", inline=False)

        embed.set_footer(text=f"Latency: {round(self.bot.latency*1000)} ms")
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ---------------------------------------------------------
    # Starboard listener
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != "⭐":
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        sb = db.get_starboard_settings(payload.guild_id)
        if not sb:
            return

        sb_channel = guild.get_channel(sb["starboard_channel"])
        if not sb_channel or payload.channel_id == sb_channel.id:
            return

        if db.has_been_starred(payload.guild_id, payload.message_id):
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            msg = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        star_reac = discord.utils.get(msg.reactions, emoji="⭐")
        if not star_reac or star_reac.count < sb.get("starboard_star_count", 3):
            return

        if msg.author.bot:
            return

        embed = discord.Embed(
            description=msg.content or "*No text content*",
            color=discord.Color.gold(),
            timestamp=msg.created_at,
        )
        embed.set_author(name=msg.author.display_name, icon_url=msg.author.display_avatar.url)
        embed.set_footer(text=f"⭐ {star_reac.count} | #{channel.name}")

        if msg.attachments:
            embed.set_image(url=msg.attachments[0].url)

        post = await sb_channel.send(embed=embed)
        db.mark_as_starred(payload.guild_id, payload.message_id)
        db.add_starboard_message(msg.id, post.id)


# ─────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot), guilds=[guild_obj])
