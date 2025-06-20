import discord
from discord.ext import commands
from discord import app_commands
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class LeaderboardView(discord.ui.View):
    def __init__(self, author, initial_embed):
        super().__init__(timeout=120)
        self.author = author
        self.current_page = 0
        self.initial_embed = initial_embed
        self.message = None

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)

    async def start(self, interaction: discord.Interaction):
        await self.update_leaderboard(interaction, initial=True)

    async def update_leaderboard(self, interaction: discord.Interaction, initial: bool = False):
        if not initial:
            await interaction.response.defer()

        total_users = db.get_total_users_in_leaderboard()
        if total_users == 0:
            embed = discord.Embed(title="🍪 Cookie Leaderboard", description="No one has any cookies yet!", color=discord.Color.blue())
            if initial:
                await interaction.response.send_message(embed=embed, view=None, ephemeral=True)
            else:
                await interaction.followup.edit_message(embed=embed, view=None)
            return

        limit = 10
        leaderboard_data = db.get_leaderboard(skip=self.current_page * limit, limit=limit)
        
        description = ""
        for i, entry in enumerate(leaderboard_data):
            user_id = entry.get('user_id')
            user = interaction.guild.get_member(user_id)
            username = user.display_name if user else f"User ID: {user_id}"
            cookies = entry.get('cookies', 0)
            rank = (self.current_page * limit) + i + 1
            description += f"**{rank}.** {username} - {cookies} 🍪\n"

        if not description:
            description = "This page is empty."

        embed = discord.Embed(title="🍪 Cookie Leaderboard", description=description, color=discord.Color.gold())
        embed.set_footer(text=f"Page {self.current_page + 1} / {((total_users - 1) // limit) + 1}")
        
        self.children[0].disabled = (self.current_page == 0) # Previous button
        self.children[1].disabled = ((self.current_page + 1) * limit >= total_users) # Next button

        if initial:
            await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
            self.message = await interaction.original_response()
        else:
            await interaction.followup.edit_message(embed=embed, view=self)


    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_leaderboard(interaction)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
            
        total_users = db.get_total_users_in_leaderboard()
        if (self.current_page + 1) * 10 < total_users:
            self.current_page += 1
            await self.update_leaderboard(interaction)

class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cookie_manager_role = "🚨🚓Cookie Manager 🍪"

    async def check_is_manager(self, interaction: discord.Interaction):
        author = interaction.user
        if isinstance(author, discord.Member):
            if author.guild_permissions.administrator:
                return True
            if any(role.name == self.cookie_manager_role for role in author.roles):
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

    @app_commands.command(name="top", description="Display the cookie leaderboard.")
    @app_commands.guilds(guild_obj)
    async def top(self, interaction: discord.Interaction):
        view = LeaderboardView(interaction.user, None)
        await view.start(interaction)

    @app_commands.command(name="cookietop", description="Show the top users by cookies.")
    @app_commands.guilds(guild_obj)
    async def cookietop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        leaderboard_data = db.get_leaderboard(limit=10)
        if not leaderboard_data:
            embed = discord.Embed(
                title="🍪 Cookie Leaderboard",
                description="No one has any cookies yet! Be the first.",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
            return
            
        description = ""
        for i, entry in enumerate(leaderboard_data):
            user_id = entry.get('user_id')
            user = interaction.guild.get_member(user_id)
            username = user.display_name if user else f"User ID: {user_id} (Left Server)"
            cookies = entry.get('cookies', 0)
            description += f"**{i+1}.** {username} — **{cookies}** 🍪\n"

        embed = discord.Embed(
            title="🏆 Top 10 Cookie Hoarders",
            description=description,
            color=discord.Color.gold()
        )
        embed.set_footer(text="Powered by BLEK NEPHEW | UK Futurism")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="addcookies", description="[Manager] Add cookies to a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to give cookies to.", amount="The amount of cookies to give.")
    async def addcookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not await self.check_is_manager(interaction):
            return
        
        if amount <= 0:
            await interaction.response.send_message("Please provide a positive number of cookies.", ephemeral=True)
            return

        db.add_cookies(user.id, amount)
        await interaction.response.send_message(f"✅ Successfully added **{amount}** 🍪 to **{user.display_name}**.")

    @app_commands.command(name="removecookies", description="[Manager] Remove cookies from a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to remove cookies from.", amount="The amount of cookies to remove.")
    async def removecookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not await self.check_is_manager(interaction):
            return
            
        if amount <= 0:
            await interaction.response.send_message("Please provide a positive number of cookies.", ephemeral=True)
            return

        db.remove_cookies(user.id, amount)
        await interaction.response.send_message(f"✅ Successfully removed **{amount}** 🍪 from **{user.display_name}**.")

    @app_commands.command(name="resetusercookies", description="[Manager] Reset a user's cookies to 0.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user whose cookies you want to reset.")
    async def resetusercookies(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.check_is_manager(interaction):
            return
        
        db.set_cookies(user.id, 0)
        await interaction.response.send_message(f"🗑️ All cookies for **{user.display_name}** have been reset to 0.")

async def setup(bot):
    await bot.add_cog(Cookies(bot))
