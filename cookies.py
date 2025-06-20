import discord
from discord.ext import commands
from discord import option

# Assuming database.py is in the parent directory of cogs
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# --- Helper Functions / Views ---

class LeaderboardView(discord.ui.View):
    def __init__(self, author, initial_embed):
        super().__init__(timeout=120)
        self.author = author
        self.current_page = 0
        self.initial_embed = initial_embed

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        # It's good practice to edit the original message on timeout
        await self.message.edit(view=self)

    async def update_leaderboard(self, interaction: discord.Interaction):
        # Defer the response to prevent "interaction failed"
        await interaction.response.defer()

        total_users = db.get_total_users_in_leaderboard()
        if total_users == 0:
            embed = discord.Embed(title="🍪 Cookie Leaderboard", description="No one has any cookies yet!", color=discord.Color.blue())
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
        
        # Enable/disable buttons based on page number
        self.children[0].disabled = (self.current_page == 0) # Previous button
        self.children[1].disabled = ((self.current_page + 1) * limit >= total_users) # Next button

        await interaction.followup.edit_message(embed=embed, view=self)


    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def previous_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_leaderboard(interaction)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def next_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
            
        total_users = db.get_total_users_in_leaderboard()
        if (self.current_page + 1) * 10 < total_users:
            self.current_page += 1
            await self.update_leaderboard(interaction)


# --- Cog Definition ---

class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cookie_manager_role = "🚨🚓Cookie Manager 🍪" # You can change this
        self.admin_perms = discord.Permissions(administrator=True)

    # --- Role & Permission Checks ---
    def check_is_manager(self, interaction: discord.Interaction):
        """Checks if the user has the Cookie Manager role or is an admin."""
        author = interaction.user
        if isinstance(author, discord.Member):
            if author.guild_permissions.administrator:
                return True
            if any(role.name == self.cookie_manager_role for role in author.roles):
                return True
        return False


    # --- Commands ---
    
    @commands.slash_command(name="cookies", description="Check your or another user's cookie balance.", guild_ids=[1370009417726169250])
    @option("user", description="The user to check.", type=discord.Member, required=False)
    async def cookies(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target_user = user or ctx.author
        cookie_balance = db.get_cookies(target_user.id)
        await ctx.respond(f"**{target_user.display_name}** has **{cookie_balance}** 🍪 cookies.", ephemeral=True)

    @commands.slash_command(name="cookiesrank", description="Check your or another user's rank in the leaderboard.", guild_ids=[1370009417726169250])
    @option("user", description="The user to check the rank of.", type=discord.Member, required=False)
    async def cookiesrank(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target_user = user or ctx.author
        rank = db.get_user_rank(target_user.id)
        total_cookies = db.get_cookies(target_user.id)
        await ctx.respond(f"**{target_user.display_name}** is rank **#{rank}** with **{total_cookies}** 🍪 cookies.", ephemeral=True)

    @commands.slash_command(name="top", description="Display the cookie leaderboard.", guild_ids=[1370009417726169250])
    async def top(self, ctx: discord.ApplicationContext):
        # This will be handled by the LeaderboardView
        view = LeaderboardView(ctx.author, None)
        await view.update_leaderboard(ctx.interaction) # Initial creation

    @commands.slash_command(name="addcookies", description="[Manager] Add cookies to a user.", guild_ids=[1370009417726169250])
    @option("user", description="The user to give cookies to.", type=discord.Member, required=True)
    @option("amount", description="The amount of cookies to give.", type=int, required=True)
    async def addcookies(self, ctx: discord.ApplicationContext, user: discord.Member, amount: int):
        if not self.check_is_manager(ctx.interaction):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return
        
        if amount <= 0:
            await ctx.respond("Please provide a positive number of cookies.", ephemeral=True)
            return

        db.add_cookies(user.id, amount)
        await ctx.respond(f"Successfully added **{amount}** 🍪 to **{user.display_name}**.", ephemeral=True)


    @commands.slash_command(name="removecookies", description="[Manager] Remove cookies from a user.", guild_ids=[1370009417726169250])
    @option("user", description="The user to remove cookies from.", type=discord.Member, required=True)
    @option("amount", description="The amount of cookies to remove.", type=int, required=True)
    async def removecookies(self, ctx: discord.ApplicationContext, user: discord.Member, amount: int):
        if not self.check_is_manager(ctx.interaction):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return
            
        if amount <= 0:
            await ctx.respond("Please provide a positive number of cookies.", ephemeral=True)
            return

        db.remove_cookies(user.id, amount)
        await ctx.respond(f"Successfully removed **{amount}** 🍪 from **{user.display_name}**.", ephemeral=True)


    @commands.slash_command(name="cookiesgiveall", description="[Manager] Give a certain number of cookies to everyone.", guild_ids=[1370009417726169250])
    @option("amount", description="The amount of cookies to give.", type=int, required=True)
    async def cookiesgiveall(self, ctx: discord.ApplicationContext, amount: int):
        if not self.check_is_manager(ctx.interaction):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return
        
        if amount <= 0:
            await ctx.respond("Please provide a positive number of cookies to give.", ephemeral=True)
            return

        await ctx.defer(ephemeral=True) # This can take a while
        
        member_ids = [member.id for member in ctx.guild.members if not member.bot]
        db.give_cookies_to_all(amount, member_ids)
        
        await ctx.followup.send(f"Successfully gave **{amount}** 🍪 to **{len(member_ids)}** members.")


    @commands.slash_command(name="cookiesreset", description="[Manager] Reset all cookies on the server to 0.", guild_ids=[1370009417726169250])
    async def cookiesreset(self, ctx: discord.ApplicationContext):
        if not self.check_is_manager(ctx.interaction):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return
        
        # Add a confirmation step to prevent accidental resets
        view = discord.ui.View()
        button = discord.ui.Button(label="Yes, I'm sure. Reset all cookies.", style=discord.ButtonStyle.danger, custom_id="confirm_reset")
        view.add_item(button)

        async def confirmation_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            
            # Check permissions again in case they changed
            if not self.check_is_manager(interaction):
                await interaction.response.send_message("You no longer have permission to do this.", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)
            db.reset_all_cookies()
            await interaction.followup.send("All cookies on the server have been reset to 0.")
            # Disable the button after use
            for item in view.children:
                item.disabled = True
            await ctx.edit(view=view)

        button.callback = confirmation_callback
        
        await ctx.respond("**⚠️ Are you absolutely sure you want to reset all cookies to 0? This cannot be undone.**", view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(Cookies(bot))
