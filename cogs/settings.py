"""
cogs/settings.py
Server-configuration & starboard management commands
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

import discord
from discord.ext import commands
from discord import option

# ─────────────────────────────────────────────────────────
# Locate database.py one level up from /cogs
# ─────────────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db  # noqa: E402

# ─────────────────────────────────────────────────────────
# Guild scope (instant sync)
# ─────────────────────────────────────────────────────────
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)


class Settings(commands.Cog):
    """Admin-only server-settings & starboard cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Load cog without syncing (main.py handles syncing)
    async def cog_load(self):
        print("[Settings] Cog loaded successfully.")

    # Helper function to check admin permissions
    def has_admin_permissions(self, ctx: discord.ApplicationContext) -> bool:
        return ctx.user.guild_permissions.administrator

    # -----------------------------------------------------
    # Channel setters - converted to individual commands
    # -----------------------------------------------------
    @commands.slash_command(name="setwelcomechannel", description="[Admin] Set the welcome channel.", guild_ids=[GUILD_ID])
    @option("channel", description="The channel used for welcome messages.", type=discord.TextChannel)
    async def setwelcomechannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if not self.has_admin_permissions(ctx):
            await ctx.respond("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        db.set_channel(ctx.guild.id, "welcome", channel.id)
        await ctx.respond(f"✅ Welcome messages will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(name="setleavechannel", description="[Admin] Set the leave channel.", guild_ids=[GUILD_ID])
    @option("channel", description="The channel used for leave messages.", type=discord.TextChannel)
    async def setleavechannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if not self.has_admin_permissions(ctx):
            await ctx.respond("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        db.set_channel(ctx.guild.id, "leave", channel.id)
        await ctx.respond(f"✅ Leave messages will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(name="setlogchannel", description="[Admin] Set the log channel.", guild_ids=[GUILD_ID])
    @option("channel", description="The channel used for log messages.", type=discord.TextChannel)
    async def setlogchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if not self.has_admin_permissions(ctx):
            await ctx.respond("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        db.set_channel(ctx.guild.id, "log", channel.id)
        await ctx.respond(f"✅ Log messages will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(name="setlevelingchannel", description="[Admin] Set the leveling channel.", guild_ids=[GUILD_ID])
    @option("channel", description="The channel used for leveling messages.", type=discord.TextChannel)
    async def setlevelingchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if not self.has_admin_permissions(ctx):
            await ctx.respond("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        db.set_channel(ctx.guild.id, "leveling", channel.id)
        await ctx.respond(f"✅ Leveling messages will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(name="setsuggestionchannel", description="[Admin] Set the suggestion channel.", guild_ids=[GUILD_ID])
    @option("channel", description="The channel used for suggestion messages.", type=discord.TextChannel)
    async def setsuggestionchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if not self.has_admin_permissions(ctx):
            await ctx.respond("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        db.set_channel(ctx.guild.id, "suggestion", channel.id)
        await ctx.respond(f"✅ Suggestion messages will now be sent to {channel.mention}.", ephemeral=True)

    # -----------------------------------------------------
    # /setstarboard
    # -----------------------------------------------------
    @commands.slash_command(
        name="setstarboard",
        description="[Admin] Set the starboard channel and required star count.",
        guild_ids=[GUILD_ID]
    )
    @option("channel", description="Channel to post starred messages.", type=discord.TextChannel)
    @option("count", description="Stars required to post (1-100).", min_value=1, max_value=100)
    async def setstarboard(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel,
        count: int,
    ):
        if not self.has_admin_permissions(ctx):
            await ctx.respond("❌ You need administrator permissions to use this command.", ephemeral=True)
            return

        db.set_starboard(ctx.guild.id, channel.id, count)
        await ctx.respond(
            f"✅ Starboard enabled. Messages with **{count}** ⭐ will be posted to {channel.mention}.",
            ephemeral=True,
        )
# -----------------------------------------------------
    # /showsettings
    # -----------------------------------------------------
    @commands.slash_command(name="showsettings", description="Display current channel settings.", guild_ids=[GUILD_ID])
    async def showsettings(self, ctx: discord.ApplicationContext):
        g_id = ctx.guild.id
        embed = discord.Embed(title="🔧 Server Settings", color=discord.Color.dark_teal())

        # Channel settings
        channel_types = {
            "welcome": ("👋 Welcome", "welcome"),
            "leave": ("👋 Leave", "leave"),
            "log": ("📝 Log", "log"),
            "leveling": ("🌌 Leveling", "leveling"),
            "suggestion": ("💡 Suggestion", "suggestion"),
        }

        for key, (label, db_key) in channel_types.items():
            chan_id = db.get_channel(g_id, db_key)
            embed.add_field(
                name=f"{label} Channel",
                value=f"<#{chan_id}>" if chan_id else "Not set",
                inline=False,
            )

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
        await ctx.respond(embed=embed, ephemeral=True)

    # -----------------------------------------------------
    # /botdebug  (owner-only)
    # -----------------------------------------------------
    @commands.slash_command(
        name="botdebug", 
        description="[Owner] Show loaded cogs and synced commands.",
        guild_ids=[GUILD_ID]
    )
    async def botdebug(self, ctx: discord.ApplicationContext):
        # Check if user is bot owner
        app_info = await self.bot.application_info()
        if ctx.user != app_info.owner:
            await ctx.respond("❌ Only the bot owner can use this command.", ephemeral=True)
            return

        await ctx.response.defer(ephemeral=True)

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
        chunk = ""
        part = 1
        for n in names:
            if len(chunk) + len(n) > 1000:
                embed.add_field(name=f"Slash Commands (part {part})", value=f"```\n{chunk.rstrip(', ')}\n```", inline=False)
                part += 1
                chunk = ""
            chunk += n + ", "
        embed.add_field(name=f"Slash Commands (part {part})", value=f"```\n{chunk.rstrip(', ')}\n```", inline=False)

        embed.set_footer(text=f"Latency: {round(self.bot.latency*1000)} ms")
        await ctx.followup.send(embed=embed, ephemeral=True)

    # -----------------------------------------------------
    # Starboard listener
    # -----------------------------------------------------
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.emoji.name != "⭐":
            return

        settings = db.get_starboard_settings(payload.guild_id)
        if not settings:
            return

        starboard_id = settings["starboard_channel"]
        star_thresh  = settings.get("starboard_star_count", 3)

        if payload.channel_id == starboard_id:
            return

        guild   = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id) if guild else None
        if not channel:
            return

        try:
            msg = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if msg.author.bot:
            return

        star_reac = discord.utils.get(msg.reactions, emoji="⭐")
        if not star_reac or star_reac.count < star_thresh:
            return

        if db.has_been_starred(payload.guild_id, msg.id):
            return

        sb_channel = guild.get_channel(starboard_id)
        if not sb_channel or sb_channel.id == payload.channel_id:
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
        db.mark_as_starred(payload.guild_id, msg.id)
        db.add_starboard_message(msg.id, post.id)
# ─────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot), guilds=[guild_obj])
