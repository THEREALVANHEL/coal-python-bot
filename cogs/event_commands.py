# cogs/event_commands.py
# Pycord-only slash commands with **instant guild sync**
# – /shout  (event announcement)
# – /gamelog  (post-event summary)
# – Uses custom host-role check
# – Persistent “Join Event” button view

from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord import option                        # Pycord slash option helper
from discord.ext import commands

# ── project imports ───────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db  # noqa: E402

# ── Config ───────────────────────────────────────────────
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# ─────────────────────────────────────────────────────────
# helper: parse time strings like “in 1 hour” or “1h30m”
# ─────────────────────────────────────────────────────────
def parse_time(time_str: str) -> Optional[datetime]:
    match = re.match(r"in\s+(\d+)\s+(hour|minute|day)s?", time_str, re.I)
    if match:
        val, unit = int(match[1]), match[2].lower()
        if unit == "hour":
            return datetime.utcnow() + timedelta(hours=val)
        if unit == "minute":
            return datetime.utcnow() + timedelta(minutes=val)
        if unit == "day":
            return datetime.utcnow() + timedelta(days=val)

    seconds = 0
    for value, unit in re.findall(r"(\d+)\s*(d|h|m|s)", time_str, re.I):
        value = int(value)
        seconds += value * {"d": 86400, "h": 3600, "m": 60, "s": 1}[unit.lower()]
    return datetime.utcnow() + timedelta(seconds=seconds) if seconds else None

# ─────────────────────────────────────────────────────────
# persistent “Join Event” button
# ─────────────────────────────────────────────────────────
class EventJoinView(discord.ui.View):
    def __init__(self, host: Optional[discord.Member], title: str):
        super().__init__(timeout=None)  # persistent
        self.host = host
        self.title = title
        self.participants: list[int] = []

    # helper to rebuild embed w/ participant list
    def _embed_with_participants(self, interaction: discord.Interaction) -> discord.Embed:
        embed = interaction.message.embeds[0]
        plist = "\n".join(f"- <@{pid}>" for pid in self.participants) or "No one has joined yet."
        # replace / add field
        for idx, fld in enumerate(embed.fields):
            if fld.name == "👥 Participants":
                embed.set_field_at(idx, name="👥 Participants", value=plist, inline=False)
                break
        else:
            embed.add_field(name="👥 Participants", value=plist, inline=False)
        return embed

    @discord.ui.button(label="Join Event", style=discord.ButtonStyle.success, custom_id="event_join_button")
    async def join(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.participants:
            return await interaction.response.send_message("⚠️ You already joined!", ephemeral=True)
        self.participants.append(uid)
        await interaction.response.edit_message(embed=self._embed_with_participants(interaction))

# ─────────────────────────────────────────────────────────
# host-role check decorator
# ─────────────────────────────────────────────────────────
def is_event_host():
    async def predicate(ctx: discord.ApplicationContext) -> bool:
        if ctx.author.guild_permissions.administrator:
            return True
        host_roles = {"Host", "Head Host 🍵", "Guide", "Medic"}
        if any(r.name in host_roles for r in ctx.author.roles):
            return True
        await ctx.respond("❌ You don't have the required role.", ephemeral=True)
        return False
    return commands.check(predicate)

# ─────────────────────────────────────────────────────────
# Cog
# ─────────────────────────────────────────────────────────
class EventCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # add persistent view once
        if not getattr(bot, "event_views_added", False):
            bot.add_view(EventJoinView(host=None, title=""))
            bot.event_views_added = True

    # instant guild sync
    async def cog_load(self):
        await self.bot.sync_commands(guild_ids=[GUILD_ID])
        print("[Events] Slash commands synced to guild.")

    # ──────────────────────────────────────────────────────
    # /shout  – event announcement
    # ──────────────────────────────────────────────────────
    @commands.slash_command(
        name="shout",
        description="[Host] Create a formatted event announcement.",
        guild_ids=[GUILD_ID],
    )
    @is_event_host()
    @option("gamename",      description="Name of the event")
    @option("description",   description="Event description")
    @option("time",          description="When it starts (e.g. 'in 1 hour', '1h30m')")
    @option("channel",       description="Channel to post in",     type=discord.TextChannel)
    @option("host",          description="Host(s) of the event")
    @option("cohost",        description="Co-host(s)",             required=False)
    @option("medic_team",    description="Medic team",             required=False)
    @option("guide_team",    description="Guide team",             required=False)
    @option("joining_option",description="How to join",            required=False)
    async def shout(
        self,
        ctx: discord.ApplicationContext,
        gamename: str,
        description: str,
        time: str,
        channel: discord.TextChannel,
        host: str,
        cohost: Optional[str] = None,
        medic_team: Optional[str] = None,
        guide_team: Optional[str] = None,
        joining_option: Optional[str] = None,
    ):
        start_dt = parse_time(time)
        if not start_dt:
            return await ctx.respond("⏱️ Invalid time format.", ephemeral=True)

        ts = int(start_dt.timestamp())
        embed = discord.Embed(
            title=f"🎉 {gamename} 🎉",
            description=description,
            color=discord.Color.blurple(),
        )
        embed.set_author(name="Event Announcement", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)

        staff = f"**Host:** {host}\n"
        if cohost:
            staff += f"**Co-Host:** {cohost}\n"
        if medic_team:
            staff += f"**Medic Team:** {medic_team}\n"
        if guide_team:
            staff += f"**Guide Team:** {guide_team}"
        embed.add_field(name="📋 Event Staff", value=staff, inline=False)

        embed.add_field(name="⏰ Starts", value=f"<t:{ts}:F> (<t:{ts}:R>)", inline=False)
        if joining_option:
            embed.add_field(name="🔗 How to Join", value=joining_option, inline=False)

        try:
            await channel.send(embed=embed)
            await ctx.respond(f"✅ Announcement posted in {channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("🚫 Can't send messages in that channel.", ephemeral=True)

    # ──────────────────────────────────────────────────────
    # /gamelog  – post-event summary
    # ──────────────────────────────────────────────────────
    @commands.slash_command(
        name="gamelog",
        description="[Host] Post a summary log of a completed event.",
        guild_ids=[GUILD_ID],
    )
    @is_event_host()
    @option("channel",       description="Channel to post log",   type=discord.TextChannel)
    @option("host",          description="Host(s) of the game")
    @option("participants",  description="List of participants")
    @option("timings",       description="Start & end times")
    @option("summary",       description="What happened")
    @option("cohost",        description="Co-host(s)",           required=False)
    @option("medic_team",    description="Medic team",           required=False)
    @option("guide_team",    description="Guide team",           required=False)
    @option("picture",       description="Image attachment",     type=discord.Attachment, required=False)
    async def gamelog(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel,
        host: str,
        participants: str,
        timings: str,
        summary: str,
        cohost: Optional[str] = None,
        medic_team: Optional[str] = None,
        guide_team: Optional[str] = None,
        picture: Optional[discord.Attachment] = None,
    ):
        embed = discord.Embed(
            title="📜 Game Log",
            description=summary,
            color=discord.Color.from_rgb(153, 102, 204),
            timestamp=datetime.utcnow(),
        )
        embed.set_author(name=f"Logged by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        staff = f"**Host:** {host}\n"
        if cohost:
            staff += f"**Co-host:** {cohost}\n"
        if guide_team:
            staff += f"**Guide Team:** {guide_team}\n"
        if medic_team:
            staff += f"**Medic Team:** {medic_team}"
        embed.add_field(name="👑 Staff", value=staff, inline=False)

        embed.add_field(name="👥 Participants", value=participants, inline=False)
        embed.add_field(name="⏱️ Timings", value=timings, inline=False)
        if picture:
            embed.set_image(url=picture.url)

        embed.set_footer(text="Another great event concluded!")

        try:
            await channel.send(embed=embed)
            await ctx.respond(f"✅ Game log posted in {channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("🚫 Can't send messages in that channel.", ephemeral=True)

# ─────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(EventCommands(bot), guilds=[guild_obj])
