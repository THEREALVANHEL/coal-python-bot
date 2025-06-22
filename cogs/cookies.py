import discord
from discord.ext import commands
from discord import app_commands
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# --- Role mapping: Requirements are MINIMUM cookies needed. ---
COOKIE_ROLES = {
    100: 1370998669884788788,
    500: 1370999721593671760,
    1000: 1371000389444305017,
    1750: 1371001322131947591,
    3000: 1371001806930579518,
    5000: 1371004762761461770
}
# Sorted cookie requirements, from highest to lowest
SORTED_COOKIE_TIERS = sorted(COOKIE_ROLES.keys(), reverse=True)


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

    async def update_cookie_roles(self, member: discord.Member):
        """Checks a user's cookie balance and assigns the correct role."""
        if member.bot: return

        try:
            balance = db.get_cookies(member.id)
            
            # Find the highest role the user is eligible for
            target_role_id = None
            for tier in SORTED_COOKIE_TIERS:
                if balance >= tier:
                    target_role_id = COOKIE_ROLES[tier]
                    break
            
            # Get all cookie role objects from the guild
            all_cookie_role_ids = set(COOKIE_ROLES.values())
            
            # Get the roles the user currently has that are cookie roles
            current_user_cookie_roles = [role for role in member.roles if role.id in all_cookie_role_ids]
            
            # Optimization: If the user has the correct role and no other cookie roles, do nothing
            if target_role_id and len(current_user_cookie_roles) == 1 and current_user_cookie_roles[0].id == target_role_id:
                return

            # Remove all existing cookie roles
            if current_user_cookie_roles:
                await member.remove_roles(*current_user_cookie_roles, reason="Cookie role update")

            # Add the correct new role
            if target_role_id:
                new_role = member.guild.get_role(target_role_id)
                if new_role:
                    await member.add_roles(new_role, reason=f"Cookie balance at {balance}")

        except discord.Forbidden:
            print(f"Error: Bot lacks permissions to manage cookie roles for {member.display_name}.")
        except Exception as e:
            print(f"An error occurred while updating cookie roles for {member.display_name}: {e}")

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

    @app_commands.command(name="cookietop", description="Shows a leaderboard of the top 10 users with the most cookies.")
    @app_commands.guilds(guild_obj)
    async def cookietop(self, interaction: discord.Interaction):
        """Shows a static top 10 cookie leaderboard."""
        leaderboard_data = db.get_leaderboard(limit=10)

        if not leaderboard_data:
            embed = discord.Embed(title="🍪 Cookie Leaderboard", description="No one has any cookies yet!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)
            return

        description = ""
        for i, entry in enumerate(leaderboard_data):
            rank = i + 1
            user_id = entry.get('user_id')
            cookies = entry.get('cookies', 0)
            description += f"**{rank}.** <@{user_id}> - **{cookies}** 🍪\n"

        embed = discord.Embed(
            title="🏆 Top 10 Cookie Hoarders",
            description=description,
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="top", description="Displays a paginated, interactive cookie leaderboard.")
    @app_commands.guilds(guild_obj)
    async def top(self, interaction: discord.Interaction):
        """Shows an interactive, paginated cookie leaderboard."""
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
        await self.update_cookie_roles(user)
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
        await self.update_cookie_roles(user)
        await interaction.response.send_message(f"✅ Successfully removed **{amount}** 🍪 from **{user.display_name}**.")

    @app_commands.command(name="cookiesreset", description="[Manager] Resets the cookie balance of all server members to zero.")
    @app_commands.guilds(guild_obj)
    async def cookiesreset(self, interaction: discord.Interaction):
        if not await self.check_is_manager(interaction):
            return

        # --- Confirmation View ---
        class ConfirmationView(discord.ui.View):
            def __init__(self, author):
                super().__init__(timeout=60)
                self.value = None
                self.author = author

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
                    return False
                return True

            @discord.ui.button(label="Confirm Reset", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                for item in self.children:
                    item.disabled = True
                await interaction.response.edit_message(view=self)
                self.stop()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                for item in self.children:
                    item.disabled = True
                await interaction.response.edit_message(view=self)
                self.stop()

        view = ConfirmationView(interaction.user)
        await interaction.response.send_message(
            "**⚠️ Are you absolutely sure?** This will reset all cookie balances on the server to **zero**. This action cannot be undone.",
            view=view,
            ephemeral=True
        )
        
        await view.wait()

        if view.value is True:
            await interaction.edit_original_response(content="Processing... please wait.", view=None)
            
            # Fetch all non-bot members
            all_members = [member async for member in interaction.guild.fetch_members(limit=None) if not member.bot]
            all_member_ids = [member.id for member in all_members]

            # Reset cookies in DB
            db.reset_all_cookies(all_member_ids)
            
            # Reset roles
            all_cookie_role_ids = set(COOKIE_ROLES.values())
            all_cookie_roles = [role for role in interaction.guild.roles if role.id in all_cookie_role_ids]
            
            for member in all_members:
                try:
                    await member.remove_roles(*all_cookie_roles, reason="Server-wide cookie reset")
                except discord.Forbidden:
                    print(f"No perms to remove roles from {member.display_name} during cookie reset.")
                except Exception as e:
                     print(f"Error removing roles from {member.display_name} during reset: {e}")

            await interaction.edit_original_response(content="✅ **All server cookie balances have been reset to zero.**")
        else:
            await interaction.edit_original_response(content="🚫 Cookie reset cancelled.", view=None)

    @app_commands.command(name="resetusercookies", description="[Manager] Reset a user's cookies to 0.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user whose cookies you want to reset.")
    async def resetusercookies(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.check_is_manager(interaction): return
        db.set_cookies(user.id, 0)
        await self.update_cookie_roles(user)
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

    @app_commands.command(name="cookiesgiveall", description="[Manager] Give cookies to all members in the server.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(amount="The amount of cookies to give to everyone.")
    async def cookiesgiveall(self, interaction: discord.Interaction, amount: int):
        if not await self.check_is_manager(interaction):
            return

        if amount <= 0:
            await interaction.response.send_message("You must give a positive number of cookies.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        
        # Fetch all non-bot member IDs from the guild.
        all_member_ids = [member.id async for member in interaction.guild.fetch_members(limit=None) if not member.bot]
        
        # Call the database function to give cookies
        db.give_cookies_to_all(amount, all_member_ids)
        
        await interaction.followup.send(f"✅ Successfully gave **{amount}** 🍪 to **all {len(all_member_ids)} members**.")

async def setup(bot):
    await bot.add_cog(Cookies(bot))
