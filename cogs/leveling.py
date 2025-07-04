from __future__ import annotations

import asyncio
import os
import random
import sys
from typing import Final

import discord
from discord import option
from discord.ext import commands

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db

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
XP_COOLDOWN: Final[int] = 60

class LevelLeaderboardView(discord.ui.View):
    def __init__(self, author: discord.Member, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.author = author
        self.interaction = interaction
        self.current_page = 0
        self.per_page = 10

    async def embed_for_page(self) -> discord.Embed:
        total = db.get_total_users_in_leveling()
        if total == 0:
            return discord.Embed(title="🚀 Level Leaderboard", description="No XP yet!", color=discord.Color.blue())

        pages = (total + self.per_page - 1) // self.per_page
        self.current_page = max(0, min(self.current_page, pages - 1))
        skip = self.current_page * self.per_page
        rows = db.get_leveling_leaderboard(skip=skip, limit=self.per_page)

        desc = "\n".join(
            f"**{skip+i+1}.** <@{row['user_id']}> — **Lvl {row.get('level',0)}** ({row.get('xp',0)} XP)"
            for i, row in enumerate(rows)
        )
        embed = discord.Embed(title="🚀 Top Adventurers", description=desc, color=discord.Color.purple())
        embed.set_footer(text=f"Page {self.current_page+1}/{pages}")
        self.prev.disabled = self.current_page == 0
        self.next.disabled = self.current_page >= pages - 1
        return embed

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass
    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, _btn):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This isn't for you!", ephemeral=True)
        self.current_page -= 1
        await interaction.response.edit_message(embed=await self.embed_for_page(), view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, _btn):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This isn't for you!", ephemeral=True)
        self.current_page += 1
        await interaction.response.edit_message(embed=await self.embed_for_page(), view=self)

class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.xp_cooldowns: dict[int, float] = {}

    async def cog_load(self):
        print("[Leveling] Cog loaded successfully.")

    @staticmethod
    def get_xp_for_level(level: int) -> int:
        return 15 * level * level + 50 * level + 100

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or len(message.content.strip()) < 5:
            return
        uid = message.author.id
        now = asyncio.get_running_loop().time()
        if uid in self.xp_cooldowns and now - self.xp_cooldowns[uid] < XP_COOLDOWN:
            return
        self.xp_cooldowns[uid] = now

        db.update_user_xp(uid, random.randint(1, 5))
        data = db.get_user_level_data(uid) or {}
        lvl, xp = data.get("level", 0), data.get("xp", 0)
        needed = self.get_xp_for_level(lvl)
        if xp >= needed:
            new_lvl = lvl + 1
            db.set_user_level(uid, new_lvl)

            ch_id = db.get_channel(message.guild.id, "leveling")
            if ch_id and (ch := message.guild.get_channel(ch_id)):
                em = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"{message.author.mention} reached **Level {new_lvl}**!",
                    color=discord.Color.fuchsia(),
                )
                em.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                await ch.send(embed=em)

            if new_lvl in LEVEL_ROLES:
                await self.update_user_roles(message.author)

    async def update_user_roles(self, member: discord.Member):
        data = db.get_user_level_data(member.id) or {}
        lvl = data.get("level", 0)
        highest = next((rid for lv, rid in sorted(LEVEL_ROLES.items(), reverse=True) if lvl >= lv), None)
        if highest is None:
            return

        lvl_role_ids = set(LEVEL_ROLES.values())
        to_remove = [r for r in member.roles if r.id in lvl_role_ids and r.id != highest]
        to_add = member.guild.get_role(highest)
        try:
            if to_remove:
                await member.remove_roles(*to_remove, reason="Level role update")
            if to_add and to_add not in member.roles:
                await member.add_roles(to_add, reason=f"Reached level {lvl}")
        except discord.Forbidden:
            print(f"[Leveling] Missing permissions for {member}")
        except Exception as exc:
            print(f"[Leveling] Role update error: {exc}")

    @commands.slash_command(name="rank", description="Check your level & XP", guild_ids=[GUILD_ID])
    @option("user", description="Target user", required=False, type=discord.Member)
    async def rank(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target = user or ctx.author
        data = db.get_user_level_data(target.id)
        if not data:
            return await ctx.respond(f"{target.display_name} has no XP yet.", ephemeral=True)

        lvl, xp = data["level"], data["xp"]
        need = self.get_xp_for_level(lvl)
        rnk = db.get_user_leveling_rank(target.id)
        prog = int((xp / need) * 20)

        em = discord.Embed(title=f"🏆 Rank for {target.display_name}", color=target.color)
        em.set_thumbnail(url=target.display_avatar.url)
        em.add_field(name="Level", value=str(lvl), inline=True)
        em.add_field(name="Rank", value=f"#{rnk}", inline=True)
        em.add_field(name="XP", value=f"`{xp}/{need}`", inline=False)
        em.add_field(name="Progress", value="🟩" * prog + "⬛" * (20 - prog), inline=False)
        await ctx.respond(embed=em)

    @commands.slash_command(name="profile", description="Show level & cookies", guild_ids=[GUILD_ID])
    @option("user", description="Target user", required=False, type=discord.Member)
    async def profile(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target = user or ctx.author
        data = db.get_user_level_data(target.id)
        cookies = db.get_cookies(target.id)
        if not data:
            return await ctx.respond(f"{target.display_name} has no profile yet.", ephemeral=True)

        lvl, xp = data["level"], data["xp"]
        need = self.get_xp_for_level(lvl)
        rnk = db.get_user_leveling_rank(target.id)
        prog = int((xp / need) * 20)

        em = discord.Embed(title=f"🌌 {target.display_name}'s Profile", color=discord.Color.blurple())
        em.set_thumbnail(url=target.display_avatar.url)
        em.add_field(name="Level", value=str(lvl), inline=True)
        em.add_field(name="Rank", value=f"#{rnk}", inline=True)
        em.add_field(name="XP", value=f"{xp}/{need}", inline=True)
        em.add_field(name="Cookies", value=str(cookies), inline=True)
        em.add_field(name="Progress", value="🟦" * prog + "⬛" * (20 - prog), inline=False)
        await ctx.respond(embed=em, ephemeral=True)

    @commands.slash_command(name="leveltop", description="Leaderboard – top 10 by level", guild_ids=[GUILD_ID])
    async def leveltop(self, ctx: discord.ApplicationContext):
        view = LevelLeaderboardView(ctx.author, ctx.interaction)
        await ctx.respond(embed=await view.embed_for_page(), view=view)

    @commands.slash_command(name="updateroles", description="Update your level role", guild_ids=[GUILD_ID])
    async def updateroles(self, ctx: discord.ApplicationContext):
        await self.update_user_roles(ctx.author)
        await ctx.respond("✅ Your roles have been updated based on your level!", ephemeral=True)

    @commands.slash_command(name="chatlvlup", description="Announce your last level up", guild_ids=[GUILD_ID])
    async def chatlvlup(self, ctx: discord.ApplicationContext):
        data = db.get_user_level_data(ctx.author.id)
        if not data:
            return await ctx.respond("You haven't gained any XP yet!", ephemeral=True)
        lvl = data.get("level", 0)
        em = discord.Embed(
            title="📢 Level-Up!",
            description=f"{ctx.author.mention} just reached **Level {lvl}**!",
            color=discord.Color.gold()
        )
        await ctx.respond(embed=em)

    @commands.slash_command(name="userinfo", description="Show user info", guild_ids=[GUILD_ID])
    @option("user", description="User to inspect", required=False, type=discord.Member)
    async def userinfo(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        user = user or ctx.author
        em = discord.Embed(title=f"👤 Info for {user}", color=discord.Color.teal())
        em.set_thumbnail(url=user.display_avatar.url)
        em.add_field(name="Username", value=str(user), inline=True)
        em.add_field(name="ID", value=user.id, inline=True)
        em.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d"), inline=True)
        em.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d"), inline=True)
        em.add_field(name="Roles", value=", ".join([r.name for r in user.roles if r.name != "@everyone"]) or "None", inline=False)
        await ctx.respond(embed=em)

    @commands.slash_command(name="serverinfo", description="Show server info", guild_ids=[GUILD_ID])
    async def serverinfo(self, ctx: discord.ApplicationContext):
        guild = ctx.guild
        em = discord.Embed(title=f"📈 Server Info: {guild.name}", color=discord.Color.green())
        em.set_thumbnail(url=guild.icon.url if guild.icon else None)
        em.add_field(name="Server ID", value=guild.id)
        em.add_field(name="Owner", value=guild.owner)
        em.add_field(name="Members", value=guild.member_count)
        em.add_field(name="Channels", value=len(guild.channels))
        em.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"))
        await ctx.respond(embed=em)

    @commands.slash_command(name="ping", description="Show bot latency", guild_ids=[GUILD_ID])
    async def ping(self, ctx: discord.ApplicationContext):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.respond(f"🏓 Pong! Latency: `{latency_ms}ms`")

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot), guilds=[guild_obj])
