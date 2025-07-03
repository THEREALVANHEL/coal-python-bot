import discord
from discord.ext import commands
from discord import app_commands
import sys
import os

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

COOKIE_ROLES = {
    100: 1370998669884788788,
    500: 1370999721593671760,
    1000: 1371000389444305017,
    1750: 1371001322131947591,
    3000: 1371001806930579518,
    5000: 1371004762761461770
}
SORTED_COOKIE_TIERS = sorted(COOKIE_ROLES.keys(), reverse=True)

class CookieLeaderboardView(discord.ui.View):
    def __init__(self, author, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.author = author
        self.interaction = interaction
        self.current_page = 0
        self.users_per_page = 10

    async def on_timeout(self):
        try:
            for item in self.children:
                item.disabled = True
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

    async def get_page_embed(self):
        total_users = db.get_total_users_in_leaderboard()
        if total_users == 0:
            return discord.Embed(
                title="🍪 Cookie Leaderboard",
                description="No one has any cookies yet!",
                color=discord.Color.blue()
            )

        total_pages = (total_users + self.users_per_page - 1) // self.users_per_page
        self.current_page = max(0, min(self.current_page, total_pages - 1))
        start_index = self.current_page * self.users_per_page
        leaderboard_data = db.get_leaderboard(skip=start_index, limit=self.users_per_page)

        description = ""
        for i, entry in enumerate(leaderboard_data):
            rank = start_index + i + 1
            user_id = entry.get('user_id')
            cookies = entry.get('cookies', 0)
            description += f"**{rank}.** <@{user_id}> - **{cookies}** 🍪\n"

        embed = discord.Embed(
            title="🍪 Cookie Leaderboard",
            description=description,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages}")
        self.children[0].disabled = (self.current_page == 0)
        self.children[1].disabled = (self.current_page >= total_pages - 1)
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = await self.get_page_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        self.current_page += 1
        await self.update_message(interaction)

class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cookie_manager_role = "🚨🚓Cookie Manager 🍪"

    # Utility -----------------------------------------------------------------
    async def update_cookie_roles(self, member: discord.Member):
        if member.bot:
            return
        try:
            balance = db.get_cookies(member.id)
            target_role_id = None
            for tier in SORTED_COOKIE_TIERS:
                if balance >= tier:
                    target_role_id = COOKIE_ROLES[tier]
                    break

            all_cookie_role_ids = set(COOKIE_ROLES.values())
            current_user_cookie_roles = [r for r in member.roles if r.id in all_cookie_role_ids]

            if target_role_id and len(current_user_cookie_roles) == 1 and current_user_cookie_roles[0].id == target_role_id:
                return  # already correct role

            if current_user_cookie_roles:
                await member.remove_roles(*current_user_cookie_roles, reason="Cookie role update")

            if target_role_id:
                new_role = member.guild.get_role(target_role_id)
                if new_role:
                    await member.add_roles(new_role, reason=f"Cookie balance at {balance}")

        except discord.Forbidden:
            print(f"Permission error updating cookie roles for {member.display_name}")
        except Exception as e:
            print(f"Error updating cookie roles for {member.display_name}: {e}")

    async def check_is_manager(self, interaction: discord.Interaction) -> bool:
        author = interaction.user
        if isinstance(author, discord.Member):
            if author.guild_permissions.administrator or any(role.name == self.cookie_manager_role for role in author.roles):
                return True
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return False

    # Slash Commands ----------------------------------------------------------
    @app_commands.command(name="cookies", description="Check cookie balance.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to check.")
    async def cookies(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        balance = db.get_cookies(target.id)
        embed = discord.Embed(
            title=f"🍪 Cookie Balance for {target.display_name}",
            description=f"They have **{balance}** delicious cookies.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cookiesrank", description="Check cookie leaderboard rank.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to check the rank of.")
    async def cookiesrank(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        rank = db.get_user_rank(target.id)
        balance = db.get_cookies(target.id)
        embed = discord.Embed(
            title=f"🏆 Cookie Rank for {target.display_name}",
            description=f"They are **Rank #{rank}** with **{balance}** 🍪 cookies.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cookietop", description="Show top cookie holders.")
    @app_commands.guilds(guild_obj)
    async def cookietop(self, interaction: discord.Interaction):
        view  = CookieLeaderboardView(interaction.user, interaction)
        embed = await view.get_page_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="addcookies", description="Add cookies to a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to give cookies to.", amount="Amount of cookies.")
    async def addcookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not await self.check_is_manager(interaction):
            return
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return
        db.add_cookies(user.id, amount)
        await self.update_cookie_roles(user)
        await interaction.response.send_message(f"✅ Added **{amount}** 🍪 to **{user.display_name}**.")

    @app_commands.command(name="removecookies", description="Remove cookies from a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to remove cookies from.", amount="Amount of cookies.")
    async def removecookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not await self.check_is_manager(interaction):
            return
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return
        db.remove_cookies(user.id, amount)
        await self.update_cookie_roles(user)
        await interaction.response.send_message(f"✅ Removed **{amount}** 🍪 from **{user.display_name}**.")

    @app_commands.command(name="resetusercookies", description="Reset a user's cookies to 0.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to reset.")
    async def resetusercookies(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.check_is_manager(interaction):
            return
        db.set_cookies(user.id, 0)
        await self.update_cookie_roles(user)
        await interaction.response.send_message(f"✅ Reset **{user.display_name}**'s cookies to 0.", ephemeral=True)

    @app_commands.command(name="updatecookies", description="Sync DB with server members.")
    @app_commands.guilds(guild_obj)
    async def updatecookies(self, interaction: discord.Interaction):
        if not await self.check_is_manager(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        db_users = {u['user_id'] for u in db.get_all_users_data()}
        server_members = {m.id for m in interaction.guild.members if not m.bot}
        removed = db_users - server_members
        added   = server_members - db_users
        for uid in removed:
            db.remove_user(uid)
        for uid in added:
            db.add_user(uid)
        await interaction.followup.send(f"✅ Added {len(added)} users, removed {len(removed)} users.")

    @app_commands.command(name="cookiesgiveall", description="Give cookies to everyone.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(amount="Cookies to give each member.")
    async def cookiesgiveall(self, interaction: discord.Interaction, amount: int):
        if not await self.check_is_manager(interaction):
            return
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        members = [m async for m in interaction.guild.fetch_members(limit=None) if not m.bot]
        member_ids = [m.id for m in members]
        db.give_cookies_to_all(amount, member_ids)
        for m in members:
            await self.update_cookie_roles(m)
        await interaction.edit_original_response(
            content=f"✅ Gave {amount} cookies to {len(members)} members."
        )

# ─────────────────────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(Cookies(bot), guilds=[guild_obj])
