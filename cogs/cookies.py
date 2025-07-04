# cogs/cookies.py
import discord
from discord.ext import commands
from discord import app_commands

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# ── Config ───────────────────────────────────────────────
GUILD_ID  = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

COOKIE_ROLES = {        # balance : role-id
    100:  1370998669884788788,
    500:  1370999721593671760,
    1000: 1371000389444305017,
    1750: 1371001322131947591,
    3000: 1371001806930579518,
    5000: 1371004762761461770,
}
SORTED_TIERS = sorted(COOKIE_ROLES.keys(), reverse=True)
COOKIE_MANAGER_ROLE = "🚨🚓Cookie Manager 🍪"

# ── Pagination View ──────────────────────────────────────
class CookieLeaderboardView(discord.ui.View):
    def __init__(self, author: discord.Member, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.author = author
        self.inter  = interaction
        self.page   = 0
        self.per    = 10

    async def on_timeout(self):
        for c in self.children: c.disabled = True
        try:    await self.inter.edit_original_response(view=self)
        except discord.NotFound: pass

    async def build_embed(self) -> discord.Embed:
        total = db.get_total_users_in_leaderboard()
        if total == 0:
            return discord.Embed(
                title="🍪 Cookie Leaderboard",
                description="No one has any cookies yet!",
                color=discord.Color.blue()
            )

        pages = (total + self.per - 1) // self.per
        self.page = max(0, min(self.page, pages - 1))
        skip = self.page * self.per
        rows = db.get_leaderboard(skip=skip, limit=self.per)

        desc = ""
        for i, row in enumerate(rows):
            rank = skip + i + 1
            desc += f"**{rank}.** <@{row['user_id']}> — **{row.get('cookies',0)}** 🍪\n"

        embed = discord.Embed(title="🍪 Cookie Leaderboard", description=desc, color=discord.Color.gold())
        embed.set_footer(text=f"Page {self.page+1}/{pages} | VANHELISMYSENSEI ON TOP",
                         icon_url=self.inter.client.user.display_avatar.url)
        # button state
        self.prev.disabled = self.page == 0
        self.next.disabled = self.page >= pages - 1
        return embed

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This isn't for you!", ephemeral=True)
        self.page -= 1
        await interaction.response.edit_message(embed=await self.build_embed(), view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This isn't for you!", ephemeral=True)
        self.page += 1
        await interaction.response.edit_message(embed=await self.build_embed(), view=self)

# ── Cog ──────────────────────────────────────────────────
class Cookies(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------- helpers ----------------------------------
    @staticmethod
    async def _is_manager(inter: discord.Interaction) -> bool:
        m: discord.Member = inter.user  # type: ignore
        return (
            isinstance(m, discord.Member)
            and (m.guild_permissions.administrator
                 or any(r.name == COOKIE_MANAGER_ROLE for r in m.roles))
        )

    @staticmethod
    async def _update_cookie_roles(member: discord.Member):
        if member.bot: return
        balance = db.get_cookies(member.id)

        target_role_id = next((COOKIE_ROLES[t] for t in SORTED_TIERS if balance >= t), None)
        level_role_ids = set(COOKIE_ROLES.values())

        roles_to_remove = [r for r in member.roles if r.id in level_role_ids and r.id != target_role_id]
        role_to_add     = member.guild.get_role(target_role_id) if target_role_id else None

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Cookie role update")
            if role_to_add and role_to_add not in member.roles:
                await member.add_roles(role_to_add, reason="Cookie role update")
        except discord.Forbidden:
            print(f"[Cookies] Missing permissions for role update: {member}")
        except Exception as exc:
            print(f"[Cookies] Role update error for {member}: {exc}")

    # ---------- slash commands ----------------------------
    @app_commands.command(name="cookies", description="Show a user's cookie balance.")
    @app_commands.guilds(guild_obj)
    async def cookies(self, inter: discord.Interaction, user: discord.Member | None = None):
        tgt = user or inter.user
        bal = db.get_cookies(tgt.id)
        embed = discord.Embed(description=f"**{tgt.display_name}** has **{bal}** 🍪 cookies.",
                              color=discord.Color.gold())
        await inter.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="cookiesrank", description="Show a user's cookie leaderboard rank.")
    @app_commands.guilds(guild_obj)
    async def cookiesrank(self, inter: discord.Interaction, user: discord.Member | None = None):
        tgt = user or inter.user
        rank = db.get_user_rank(tgt.id)
        bal  = db.get_cookies(tgt.id)
        embed = discord.Embed(
            description=f"**{tgt.display_name}** is **#{rank}** with **{bal}** 🍪.",
            color=discord.Color.orange())
        await inter.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="cookietop", description="Top cookie holders (paginated).")
    @app_commands.guilds(guild_obj)
    async def cookietop(self, inter: discord.Interaction):
        view = CookieLeaderboardView(inter.user, inter)
        await inter.response.send_message(embed=await view.build_embed(), view=view, ephemeral=True)

    # ----- manager commands ------------------------------
    @app_commands.command(name="addcookies", description="[Manager] Add cookies to a user.")
    @app_commands.guilds(guild_obj)
    async def addcookies(self, inter: discord.Interaction, user: discord.Member, amount: int):
        if not await self._is_manager(inter):
            return await inter.response.send_message("No permission.", ephemeral=True)
        if amount <= 0:
            return await inter.response.send_message("Amount must be positive.", ephemeral=True)

        db.add_cookies(user.id, amount)
        await self._update_cookie_roles(user)
        await inter.response.send_message(f"✅ Added **{amount}** 🍪 to **{user.display_name}**.")

    @app_commands.command(name="removecookies", description="[Manager] Remove cookies from a user.")
    @app_commands.guilds(guild_obj)
    async def removecookies(self, inter: discord.Interaction, user: discord.Member, amount: int):
        if not await self._is_manager(inter):
            return await inter.response.send_message("No permission.", ephemeral=True)
        if amount <= 0:
            return await inter.response.send_message("Amount must be positive.", ephemeral=True)

        db.remove_cookies(user.id, amount)
        await self._update_cookie_roles(user)
        await inter.response.send_message(f"✅ Removed **{amount}** 🍪 from **{user.display_name}**.")

    @app_commands.command(name="resetusercookies", description="[Manager] Reset a user's cookies to 0.")
    @app_commands.guilds(guild_obj)
    async def resetcookies(self, inter: discord.Interaction, user: discord.Member):
        if not await self._is_manager(inter):
            return await inter.response.send_message("No permission.", ephemeral=True)

        db.set_cookies(user.id, 0)
        await self._update_cookie_roles(user)
        await inter.response.send_message(f"✅ Reset **{user.display_name}**'s cookies to 0.", ephemeral=True)

    @app_commands.command(name="cookiesgiveall", description="[Manager] Give cookies to everyone.")
    @app_commands.guilds(guild_obj)
    async def cookiesgiveall(self, inter: discord.Interaction, amount: int):
        if not await self._is_manager(inter):
            return await inter.response.send_message("No permission.", ephemeral=True)
        if amount <= 0:
            return await inter.response.send_message("Amount must be positive.", ephemeral=True)

        await inter.response.defer(ephemeral=True)
        members = [m async for m in inter.guild.fetch_members(limit=None) if not m.bot]
        ids     = [m.id for m in members]
        db.give_cookies_to_all(amount, ids)

        for m in members:
            await self._update_cookie_roles(m)

        await inter.followup.send(f"✅ Gave **{amount}** 🍪 to **{len(members)}** members.")

# ── setup ────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(Cookies(bot), guilds=[guild_obj])
