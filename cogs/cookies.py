# cogs/cookies.py
# Slash-only Cookie Economy cog (Pycord 2.x)
# – Instant guild-scoped sync in cog_load()
# – Role rewards for cookie milestones
# – Manager-only admin actions

import os
import sys
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime

# ── project imports ───────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db  # noqa: E402

# ── Config ───────────────────────────────────────────────
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

COOKIE_ROLES = {
    50: "Cookie Novice",
    100: "Cookie Enthusiast", 
    250: "Cookie Collector",
    500: "Cookie Master",
    1000: "Cookie Legend"
}

MANAGER_ROLES = ["Manager", "Admin", "Administrator", "Cookie Manager"]

# ── Pagination View ──────────────────────────────────────
class CookieLeaderboardView(discord.ui.View):
    def __init__(self, author: discord.Member, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.author = author
        self.interaction = interaction
        self.current_page = 0
        self.per_page = 10

    async def embed_for_page(self) -> discord.Embed:
        # Get total cookie users
        total_users = len(db.get_all_cookie_users())
        if total_users == 0:
            return discord.Embed(
                title="🍪 Cookie Leaderboard", 
                description="No cookies earned yet!", 
                color=discord.Color.blue()
            )

        # Calculate pagination
        pages = (total_users + self.per_page - 1) // self.per_page
        self.current_page = max(0, min(self.current_page, pages - 1))
        skip = self.current_page * self.per_page
        
        # Get leaderboard data
        rows = db.get_cookie_leaderboard(skip=skip, limit=self.per_page)

        description = ""
        for i, row in enumerate(rows):
            user_id = row['user_id']
            cookies = row.get('cookies', 0)
            
            # Try to get user from guild
            user = self.interaction.guild.get_member(user_id)
            user_name = user.display_name if user else f"Unknown User ({user_id})"
            
            rank = skip + i + 1
            medal = ["🥇", "🥈", "🥉"][i] if rank <= 3 and skip == 0 else f"**{rank}.**"
            description += f"{medal} {user_name} — **{cookies}** 🍪\n"

        embed = discord.Embed(
            title="🍪 Cookie Leaderboard", 
            description=description, 
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Page {self.current_page + 1}/{pages} • BLECKOPS ON TOP")
        
        # Update button states
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
    async def prev(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This leaderboard isn't for you!", ephemeral=True)
        
        self.current_page -= 1
        await interaction.response.edit_message(embed=await self.embed_for_page(), view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)  
    async def next(self, interaction: discord.Interaction, button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("This leaderboard isn't for you!", ephemeral=True)
        
        self.current_page += 1
        await interaction.response.edit_message(embed=await self.embed_for_page(), view=self)

# ── Cog ──────────────────────────────────────────────────
class Cookies(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Load cog without syncing (main.py handles syncing)
    async def cog_load(self):
        print("[Cookies] Cog loaded successfully.")

    # ---------- helpers ----------------------------------
    async def _is_manager(self, interaction: discord.Interaction) -> bool:
        """Check if user has permission to manage cookies."""
        return (
            interaction.user.guild_permissions.administrator
            or any(role.name in MANAGER_ROLES for role in interaction.user.roles)
        )

    async def _update_cookie_roles(self, member: discord.Member):
        """Update a member's cookie roles based on their balance."""
        cookies = db.get_cookies(member.id)
        
        # Determine which role they should have
        target_role = None
        for required_cookies, role_name in sorted(COOKIE_ROLES.items(), reverse=True):
            if cookies >= required_cookies:
                target_role = discord.utils.get(member.guild.roles, name=role_name)
                break
        
        # Get all cookie roles
        cookie_roles = [discord.utils.get(member.guild.roles, name=role_name) for role_name in COOKIE_ROLES.values()]
        cookie_roles = [role for role in cookie_roles if role is not None]
        
        # Remove old cookie roles
        roles_to_remove = [role for role in member.roles if role in cookie_roles]
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason="Cookie role update")
            except discord.Forbidden:
                pass
        
        # Add new role if applicable
        if target_role and target_role not in member.roles:
            try:
                await member.add_roles(target_role, reason=f"Reached {cookies} cookies")
            except discord.Forbidden:
                pass

    # ---------- slash commands ----------------------------
    @app_commands.command(name="cookies", description="Show a user's cookie balance.")
    @app_commands.describe(user="User to check (optional)")
    @app_commands.guilds(guild_obj)
    async def cookies(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        balance = db.get_cookies(target.id)
        
        embed = discord.Embed(
            title="🍪 Cookie Balance",
            description=f"{target.display_name} has **{balance}** cookies!",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cookiesrank", description="Show a user's cookie leaderboard rank.")
    @app_commands.describe(user="User to check (optional)")
    @app_commands.guilds(guild_obj)
    async def cookiesrank(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        balance = db.get_cookies(target.id)
        rank = db.get_user_cookie_rank(target.id)
        
        embed = discord.Embed(
            title="🏅 Cookie Rank",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=target.display_name, inline=True)
        embed.add_field(name="Cookies", value=f"{balance} 🍪", inline=True)
        embed.add_field(name="Rank", value=f"#{rank}", inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cookietop", description="Top cookie holders (paginated).")
    @app_commands.guilds(guild_obj)
    async def cookietop(self, interaction: discord.Interaction):
        view = CookieLeaderboardView(interaction.user, interaction)
        embed = await view.embed_for_page()
        await interaction.response.send_message(embed=embed, view=view)

    # ----- manager commands ------------------------------
    @app_commands.command(name="addcookies", description="[Manager] Add cookies to a user.")
    @app_commands.describe(user="User to give cookies to", amount="Number of cookies to add")
    @app_commands.guilds(guild_obj)
    async def addcookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        # Check permissions
        if not await self._is_manager(interaction):
            return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        
        if amount <= 0:
            return await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
        
        if amount > 10000:
            return await interaction.response.send_message("❌ Maximum 10,000 cookies at a time.", ephemeral=True)
        
        # Add cookies
        old_balance = db.get_cookies(user.id)
        db.add_cookies(user.id, amount)
        new_balance = old_balance + amount
        
        # Update roles
        await self._update_cookie_roles(user)
        
        embed = discord.Embed(
            title="✅ Cookies Added!",
            description=f"Added **{amount}** 🍪 to {user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Previous Balance", value=f"{old_balance} 🍪", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance} 🍪", inline=True)
        embed.set_footer(text=f"Action by {interaction.user.display_name} • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removecookies", description="[Manager] Remove cookies from a user.")
    @app_commands.describe(user="User to remove cookies from", amount="Number of cookies to remove")
    @app_commands.guilds(guild_obj)
    async def removecookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        # Check permissions
        if not await self._is_manager(interaction):
            return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        
        if amount <= 0:
            return await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
        
        # Remove cookies
        old_balance = db.get_cookies(user.id)
        db.remove_cookies(user.id, amount)
        new_balance = max(0, old_balance - amount)
        
        # Update roles
        await self._update_cookie_roles(user)
        
        embed = discord.Embed(
            title="✅ Cookies Removed!",
            description=f"Removed **{amount}** 🍪 from {user.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Previous Balance", value=f"{old_balance} 🍪", inline=True)
        embed.add_field(name="New Balance", value=f"{new_balance} 🍪", inline=True)
        embed.set_footer(text=f"Action by {interaction.user.display_name} • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resetusercookies", description="[Manager] Reset a user's cookies to 0.")
    @app_commands.describe(user="User to reset")
    @app_commands.guilds(guild_obj)
    async def resetusercookies(self, interaction: discord.Interaction, user: discord.Member):
        # Check permissions
        if not await self._is_manager(interaction):
            return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        
        old_balance = db.get_cookies(user.id)
        db.set_cookies(user.id, 0)
        
        # Update roles
        await self._update_cookie_roles(user)
        
        embed = discord.Embed(
            title="🔄 Cookies Reset!",
            description=f"Reset {user.mention}'s cookies to 0",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Previous Balance", value=f"{old_balance} 🍪", inline=True)
        embed.add_field(name="New Balance", value="0 🍪", inline=True)
        embed.set_footer(text=f"Action by {interaction.user.display_name} • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cookiesgiveall", description="[Manager] Give cookies to everyone.")
    @app_commands.describe(amount="Number of cookies to give each member")
    @app_commands.guilds(guild_obj)
    async def cookiesgiveall(self, interaction: discord.Interaction, amount: int):
        # Check permissions
        if not await self._is_manager(interaction):
            return await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        
        if amount <= 0:
            return await interaction.response.send_message("❌ Amount must be positive.", ephemeral=True)
        
        if amount > 1000:
            return await interaction.response.send_message("❌ Maximum 1,000 cookies per person for bulk operations.", ephemeral=True)
        
        await interaction.response.defer()
        
        # Get all members (exclude bots)
        members = [member for member in interaction.guild.members if not member.bot]
        member_ids = [member.id for member in members]
        
        # Give cookies to all
        db.give_cookies_to_all(amount, member_ids)
        
        # Update roles for a sample (to avoid rate limits)
        for member in members[:10]:  # Update first 10 to avoid hitting rate limits
            try:
                await self._update_cookie_roles(member)
                await asyncio.sleep(0.5)  # Rate limit protection
            except:
                continue
        
        embed = discord.Embed(
            title="🎉 Cookies for Everyone!",
            description=f"Gave **{amount}** 🍪 to **{len(members)}** members!",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Mass gift by {interaction.user.display_name} • BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        
        await interaction.followup.send(embed=embed)

# ── setup ────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(Cookies(bot), guilds=[guild_obj])
