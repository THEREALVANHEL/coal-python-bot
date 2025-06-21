import discord
from discord.ext import commands
from discord import app_commands
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# --- New Paginated Leaderboard View ---
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
            pass # Message might have been deleted

    async def get_page_embed(self):
        """Creates an embed for the current page of the leaderboard."""
        total_users = db.get_total_users_in_leaderboard()
        if total_users == 0:
            return discord.Embed(title="🍪 Cookie Leaderboard", description="No one has any cookies yet!", color=discord.Color.blue())

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
            title="🏆 Top Cookie Hoarders",
            description=description,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages}")
        
        # Disable/enable buttons
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

    async def check_is_manager(self, interaction: discord.Interaction):
        author = interaction.user
        if isinstance(author, discord.Member):
            if author.guild_permissions.administrator or any(role.name == self.cookie_manager_role for role in author.roles):
                return True
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        return False

    @app_commands.command(name="cookies", description="Check your or another user's cookie balance.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to check.")
    async def cookies(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        cookie_balance = db.get_cookies(target_user.id)
        embed = discord.Embed(
            title=f"🍪 Cookie Balance for {target_user.display_name}",
            description=f"They have **{cookie_balance}** delicious cookies.",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cookiesrank", description="Check your or another user's rank in the leaderboard.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to check the rank of.")
    async def cookiesrank(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        rank = db.get_user_rank(target_user.id)
        total_cookies = db.get_cookies(target_user.id)
        embed = discord.Embed(
            title=f"🏆 Cookie Rank for {target_user.display_name}",
            description=f"They are **Rank #{rank}** with **{total_cookies}** 🍪 cookies.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="cookietop", description="Show the interactive cookie leaderboard.")
    @app_commands.guilds(guild_obj)
    async def cookietop(self, interaction: discord.Interaction):
        view = CookieLeaderboardView(interaction.user, interaction)
        embed = await view.get_page_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="addcookies", description="[Manager] Add cookies to a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to give cookies to.", amount="The amount of cookies to give.")
    async def addcookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not await self.check_is_manager(interaction): return
        if amount <= 0:
            await interaction.response.send_message("Please provide a positive number of cookies.", ephemeral=True)
            return
        db.add_cookies(user.id, amount)
        await interaction.response.send_message(f"✅ Successfully added **{amount}** 🍪 to **{user.display_name}**.")

    @app_commands.command(name="removecookies", description="[Manager] Remove cookies from a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to remove cookies from.", amount="The amount of cookies to remove.")
    async def removecookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not await self.check_is_manager(interaction): return
        if amount <= 0:
            await interaction.response.send_message("Please provide a positive number of cookies.", ephemeral=True)
            return
        db.remove_cookies(user.id, amount)
        await interaction.response.send_message(f"✅ Successfully removed **{amount}** 🍪 from **{user.display_name}**.")

    @app_commands.command(name="resetusercookies", description="[Manager] Reset a user's cookies to 0.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user whose cookies you want to reset.")
    async def resetusercookies(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.check_is_manager(interaction): return
        db.set_cookies(user.id, 0)
        await interaction.response.send_message(f"🗑️ All cookies for **{user.display_name}** have been reset to 0.")

    @app_commands.command(name="updatecookies", description="[Manager] Syncs the cookie database with current server members.")
    @app_commands.guilds(guild_obj)
    async def updatecookies(self, interaction: discord.Interaction):
        if not await self.check_is_manager(interaction): return

        await interaction.response.defer(ephemeral=True, thinking=True)
        
        # Fetch all member IDs from the guild. This can be slow in large servers.
        all_member_ids = [member.id async for member in interaction.guild.fetch_members(limit=None)]
        
        # Synchronize the database
        removed_count = db.synchronize_cookies(all_member_ids)

        if removed_count > 0:
            await interaction.followup.send(f"✅ Database synchronized. Removed **{removed_count}** user(s) from the cookie leaderboard who were no longer in the server.")
        else:
            await interaction.followup.send("✅ Database is already up-to-date. No users were removed.")

async def setup(bot):
    await bot.add_cog(Cookies(bot))
