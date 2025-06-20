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
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return False

    @app_commands.command(name="cookies", description="Check your or another user's cookie balance.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to check.")
    async def cookies(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        cookie_balance = db.get_cookies(target_user.id)
        await interaction.response.send_message(f"**{target_user.display_name}** has **{cookie_balance}** 🍪 cookies.", ephemeral=True)

    @app_commands.command(name="cookiesrank", description="Check your or another user's rank in the leaderboard.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to check the rank of.")
    async def cookiesrank(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        rank = db.get_user_rank(target_user.id)
        total_cookies = db.get_cookies(target_user.id)
        await interaction.response.send_message(f"**{target_user.display_name}** is rank **#{rank}** with **{total_cookies}** 🍪 cookies.", ephemeral=True)

    @app_commands.command(name="top", description="Display the cookie leaderboard.")
    @app_commands.guilds(guild_obj)
    async def top(self, interaction: discord.Interaction):
        view = LeaderboardView(interaction.user, None)
        await view.start(interaction)

    @app_commands.command(name="cookietop", description="Show the top users by cookies.")
    @app_commands.guilds(guild_obj)
    async def cookietop(self, interaction: discord.Interaction):
        leaderboard_data = db.get_leaderboard(limit=10)
        if not leaderboard_data:
            embed = discord.Embed(
                title="🍪 Cookie Leaderboard",
                description="No one has any cookies yet!",
                color=discord.Color.dark_gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        description = ""
        for i, entry in enumerate(leaderboard_data):
            user_id = entry.get('user_id')
            user = interaction.guild.get_member(user_id)
            username = user.display_name if user else f"User ID: {user_id}"
            cookies = entry.get('cookies', 0)
            description += f"**{i+1}.** {username} — 🍪 `{cookies}`\n"
        embed = discord.Embed(
            title="🍪 Cookie Leaderboard",
            description=description,
            color=discord.Color.gold()
        )
        embed.set_footer(text="Futuristic UK Cookieboard | BLEK NEPHEW", icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        await interaction.response.send_message(embed=embed, ephemeral=True)

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
        await interaction.response.send_message(f"Successfully added **{amount}** 🍪 to **{user.display_name}**.", ephemeral=True)

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
        await interaction.response.send_message(f"Successfully removed **{amount}** 🍪 from **{user.display_name}**.", ephemeral=True)

    @app_commands.command(name="cookiesgiveall", description="[Manager] Give a certain number of cookies to everyone.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(amount="The amount of cookies to give.")
    async def cookiesgiveall(self, interaction: discord.Interaction, amount: int):
        if not await self.check_is_manager(interaction):
            return
        
        if amount <= 0:
            await interaction.response.send_message("Please provide a positive number of cookies to give.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        member_ids = [member.id for member in interaction.guild.members if not member.bot]
        db.give_cookies_to_all(amount, member_ids)
        
        await interaction.followup.send(f"Successfully gave **{amount}** 🍪 to **{len(member_ids)}** members.")

    @app_commands.command(name="cookiesreset", description="[Manager] Reset all cookies on the server to 0.")
    @app_commands.guilds(guild_obj)
    async def cookiesreset(self, interaction: discord.Interaction):
        if not await self.check_is_manager(interaction):
            return
        
        view = self.create_reset_confirmation_view(interaction.user.id)
        await interaction.response.send_message("**⚠️ Are you absolutely sure you want to reset all cookies to 0? This cannot be undone.**", view=view, ephemeral=True)
    
    def create_reset_confirmation_view(self, author_id):
        view = discord.ui.View()
        button = discord.ui.Button(label="Yes, I'm sure. Reset all cookies.", style=discord.ButtonStyle.danger)

        async def confirmation_callback(interaction: discord.Interaction):
            if interaction.user.id != author_id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            if not await self.check_is_manager(interaction):
                return

            await interaction.response.defer(ephemeral=True)
            db.reset_all_cookies()
            await interaction.followup.send("All cookies on the server have been reset to 0.")
            
            button.disabled = True
            await interaction.message.edit(view=view)

        button.callback = confirmation_callback
        view.add_item(button)
        return view


async def setup(bot):
    await bot.add_cog(Cookies(bot))
