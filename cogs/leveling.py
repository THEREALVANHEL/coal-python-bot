"""
Leveling & Daily-Streak Cog
discord.py ≥ 2.3  •  Guild-scoped slash commands that sync instantly
Copy-paste into cogs/leveling.py and load with bot.load_extension.
"""

from __future__ import annotations

import asyncio
import os
import random
import sys
from typing import Final

import discord
from discord import app_commands
from discord.ext import commands

# ── Database helper ───────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db  # noqa: E402  (local module)

# ── Constants ─────────────────────────────────────────────
GUILD_ID: Final[int] = 1370009417726169250
guild_obj: Final[discord.Object] = discord.Object(id=GUILD_ID)

LEVEL_ROLES: Final[dict[int, int]] = {
    5: 1371032270361853962,
    10: 1371032537740214302,
    20: 1371032664026382427,
    35: 1371032830217289748,
    50: 1371032964938600521,
    75: 1371033073038266429,
}
XP_COOLDOWN: Final[int] = 60  # seconds

# ── Leaderboard Views ─────────────────────────────────────
class LevelLeaderboardView(discord.ui.View):
    def __init__(self, author: discord.Member, interaction: discord.Interaction) -> None:
        super().__init__(timeout=180)
        self.author = author
        self.interaction = interaction
        self.current_page = 0
        self.per_page = 10

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

    async def embed_for_page(self) -> discord.Embed:
        total = db.get_total_users_in_leveling()
        if total == 0:
            return discord.Embed(
                title="🚀 Level Leaderboard",
                description="No one has gained any XP yet!",
                color=discord.Color.blue(),
            )

        pages = (total + self.per_page - 1) // self.per_page
        self.current_page = max(0, min(self.current_page, pages - 1))
        skip = self.current_page * self.per_page
        rows = db.get_leveling_leaderboard(skip=skip, limit=self.per_page)

        desc = ""
        for i, row in enumerate(rows):
            rank = skip + i + 1
            desc += (
                f"**{rank}.** <@{row['user_id']}> — "
                f"**Lvl {row.get('level', 0)}** ({row.get('xp', 0)} XP)\n"
            )

        embed = discord.Embed(
            title="🚀 Top Adventurers", description=desc, color=discord.Color.purple()
        )
        embed.set_footer(text=f"Page {self.current_page + 1}/{pages}")
        self.prev.disabled = self.current_page == 0
        self.next.disabled = self.current_page >= pages - 1
        return embed

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This isn't for you!", ephemeral=True)
        self.current_page -= 1
        await interaction.response.edit_message(embed=await self.embed_for_page(), view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This isn't for you!", ephemeral=True)
        self.current_page += 1
        await interaction.response.edit_message(embed=await self.embed_for_page(), view=self)


class DailyStreakLeaderboardView(discord.ui.View):
    def __init__(self, author: discord.Member, interaction: discord.Interaction) -> None:
        super().__init__(timeout=180)
        self.author = author
        self.interaction = interaction
        self.current_page = 0
        self.per_page = 10

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

    async def embed_for_page(self) -> discord.Embed:
        total = db.get_total_users_in_dailies()
        if total == 0:
            return discord.Embed(
                title="🔥 Daily-Streak Leaderboard",
                description="No streaks yet – be the first to /daily!",
                color=discord.Color.orange(),
            )

        pages = (total + self.per_page - 1) // self.per_page
        self.current_page = max(0, min(self.current_page, pages - 1))
        skip = self.current_page * self.per_page
        rows = db.get_top_daily_streaks(skip=skip, limit=self.per_page)

        desc = ""
        for i, row in enumerate(rows):
            rank = skip + i + 1
            desc += f"**{rank}.** <@{row['user_id']}> — **{row.get('streak', 0)}-day streak** 🔥\n"

        embed = discord.Embed(
            title="🔥 Daily-Streak Leaderboard", description=desc, color=discord.Color.orange()
        )
        embed.set_footer(text=f"Page {self.current_page + 1}/{pages}")
        self.prev.disabled = self.current_page == 0
        self.next.disabled = self.current_page >= pages - 1
        return embed

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This isn't for you!", ephemeral=True)
        self.current_page -= 1
        await interaction.response.edit_message(embed=await self.embed_for_page(), view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This isn't for you!", ephemeral=True)
        self.current_page += 1
        await interaction.response.edit_message(embed=await self.embed_for_page(), view=self)

# ── Leveling Cog ──────────────────────────────────────────
class Leveling(commands.Cog):
    """XP, level roles, and daily-streak slash commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.xp_cooldowns: dict[int, float] = {}

    # Instant guild-scoped sync when the cog is loaded
    async def cog_load(self) -> None:
        await self.bot.tree.sync(guild=guild_obj)
        print("[Leveling] Slash commands synced ✔")

    # XP curve
    @staticmethod
    def get_xp_for_level(level: int) -> int:
        return 15 * (level**2) + 50 * level + 100

    # Message listener for XP
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        if len(message.content.strip()) < 5:
            return

        uid = message.author.id
        now = asyncio.get_running_loop().time()
        if uid in self.xp_cooldowns and now - self.xp_cooldowns[uid] < XP_COOLDOWN:
            return
        self.xp_cooldowns[uid] = now

        db.update_user_xp(uid, random.randint(1, 5))
        data = db.get_user_level_data(uid) or {}
        level, xp = data.get("level", 0), data.get("xp", 0)
        needed = self.get_xp_for_level(level)

        if xp >= needed:
            new_level = level + 1
            db.set_user_level(uid, new_level)

            channel_id = db.get_channel(message.guild.id, "leveling")
            if channel_id and (channel := message.guild.get_channel(channel_id)):
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"Congratulations {message.author.mention}, you're now **Level {new_level}**!",
                    color=discord.Color.fuchsia(),
                )
                embed.set_author(
                    name=message.author.display_name, icon_url=message.author.display_avatar.url
                )
                await channel.send(embed=embed)

            if new_level in LEVEL_ROLES:
                await self.update_user_roles(message.author)

    # Role updater
    async def update_user_roles(self, member: discord.Member) -> None:
        data = db.get_user_level_data(member.id) or {}
        level = data.get("level", 0)

        highest_role_id: int | None = next(
            (rid for lvl, rid in sorted(LEVEL_ROLES.items(), reverse=True) if level >= lvl), None
        )
        if highest_role_id is None:
            return

        level_role_ids = set(LEVEL_ROLES.values())
        roles_to_remove = [r for r in member.roles if r.id in level_role_ids and r.id != highest_role_id]
        role_to_add = member.guild.get_role(highest_role_id)

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Level role update")
            if role_to_add and role_to_add not in member.roles:
                await member.add_roles(role_to_add, reason=f"Reached level {level}")
        except discord.Forbidden:
            print(f"[Leveling] Missing permissions to edit roles for {member}.")
        except Exception as exc:
            print(f"[Leveling] Role update error for {member}: {exc}")

    # ── Slash commands ────────────────────────────────────
    @app_commands.command(name="rank", description="See a user's level & XP")
    @app_commands.guilds(guild_obj)
    async def slash_rank(
        self, interaction: discord.Interaction, user: discord.Member | None = None
    ) -> None:
        target = user or interaction.user
        data = db.get_user_level_data(target.id)
        if not data:
            return await interaction.response.send_message(
                f"{target.display_name} has no XP yet.", ephemeral=True
            )

        level, xp = data["level"], data["xp"]
        needed = self.get_xp_for_level(level)
        rank_idx = db.get_user_leveling_rank(target.id)
        progress = int((xp / needed) * 20)

        embed = discord.Embed(
            title=f"🏆 Rank for {target.display_name}", color=target.color
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="Rank", value=f"#{rank_idx}", inline=True)
        embed.add_field(name="XP", value=f"`{xp} / {needed}`", inline=False)
        embed.add_field(
            name="Progress", value="🟩" * progress + "⬛" * (20 - progress), inline=False
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="Show cookies, level & XP")
    @app_commands.guilds(guild_obj)
    async def slash_profile(
        self, interaction: discord.Interaction, user: discord.Member | None = None
    ) -> None:
        target = user or interaction.user
        data = db.get_user_level_data(target.id)
        cookies = db.get_cookies(target.id)
        if not data:
            return await interaction.response.send_message(
                f"{target.display_name} has no profile yet.", ephemeral=True
            )

        level, xp = data["level"], data["xp"]
        needed = self.get_xp_for_level(level)
        rank_idx = db.get_user_leveling_rank(target.id)
        progress = int((xp / needed) * 20)

        embed = discord.Embed(
            title=f"🌌 {target.display_name}'s Profile", color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="Rank", value=f"#{rank_idx}", inline=True)
        embed.add_field(name="XP", value=f"{xp}/{needed}", inline=True)
        embed.add_field(name="Cookies", value=str(cookies), inline=True)
        embed.add_field(
            name="Progress", value="🟦" * progress + "⬛" * (20 - progress), inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leveltop", description="Top 10 users by level")
    @app_commands.guilds(guild_obj)
    async def slash_leveltop(self, interaction: discord.Interaction) -> None:
        view = LevelLeaderboardView(interaction.user, interaction)
        await interaction.response.send_message(
            embed=await view.embed_for_page(), view=view
        )

    @app_commands.command(name="streaktop", description="Top users by daily streak")
    @app_commands.guilds(guild_obj)
    async def slash_streaktop(self, interaction: discord.Interaction) -> None:
        view = DailyStreakLeaderboardView(interaction.user, interaction)
        await interaction.response.send_message(
            embed=await view.embed_for_page(), view=view
        )

# ── Setup helper ─────────────────────────────────────────
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leveling(bot), guilds=[guild_obj])
