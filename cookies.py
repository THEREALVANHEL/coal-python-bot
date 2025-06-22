import discord
from discord.ext import commands
from discord import option

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# --- Helper Functions / Views ---

class LeaderboardView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=120)
        self.author = author
        self.current_page = 0

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    async def update_leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        total_users = db.get_total_users_in_leaderboard()
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

        embed = discord.Embed(title="🏆 Cookie Leaderboard", description=description, color=discord.Color.gold())
        total_pages = ((total_users - 1) // limit) + 1
        embed.set_footer(text=f"Page {self.current_page + 1} / {total_pages} | BLECKOPS ON TOP", icon_url=interaction.client.user.display_avatar.url)

        self.children[0].disabled = (self.current_page == 0)
        self.children[1].disabled = ((self.current_page + 1) * limit >= total_users)

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
        self.cookie_manager_role = "🚨🚓Cookie Manager 🍪"

    def check_is_manager(self, interaction: discord.Interaction):
        author = interaction.user
        if isinstance(author, discord.Member):
            if author.guild_permissions.administrator:
                return True
            if any(role.name == self.cookie_manager_role for role in author.roles):
                return True
        return False

    @commands.slash_command(name="cookies", description="Check your or another user's cookie balance.", guild_ids=[1370009417726169250])
    @option("user", description="The user to check.", type=discord.Member, required=False)
    async def cookies(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target_user = user or ctx.author
        cookie_balance = db.get_cookies(target_user.id)
        embed = discord.Embed(description=f"**{target_user.display_name}** has **{cookie_balance}** 🍪 cookies.", color=discord.Color.gold())
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="cookiesrank", description="Check your or another user's rank in the leaderboard.", guild_ids=[1370009417726169250])
    @option("user", description="The user to check the rank of.", type=discord.Member, required=False)
    async def cookiesrank(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target_user = user or ctx.author
        rank = db.get_user_rank(target_user.id)
        total_cookies = db.get_cookies(target_user.id)
        embed = discord.Embed(description=f"**{target_user.display_name}** is rank **#{rank}** with **{total_cookies}** 🍪 cookies.", color=discord.Color.gold())
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="cookietop", description="Show the top users by cookies.", guild_ids=[1370009417726169250])
    async def cookietop(self, ctx: discord.ApplicationContext):
        leaderboard_data = db.get_leaderboard(limit=10)
        if not leaderboard_data:
            embed = discord.Embed(title="🍪 Cookie Leaderboard", description="No one has any cookies yet!", color=discord.Color.dark_gold())
            await ctx.respond(embed=embed, ephemeral=True)
            return
        description = ""
        for i, entry in enumerate(leaderboard_data):
            user_id = entry.get('user_id')
            user = ctx.guild.get_member(user_id)
            username = user.display_name if user else f"User ID: {user_id}"
            cookies = entry.get('cookies', 0)
            description += f"**{i+1}.** {username} — 🍪 `{cookies}`\n"
        embed = discord.Embed(title="🍪 Cookie Leaderboard", description=description, color=discord.Color.gold())
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="top", description="Display the full leaderboard.", guild_ids=[1370009417726169250])
    async def top(self, ctx: discord.ApplicationContext):
        view = LeaderboardView(ctx.author)
        await view.update_leaderboard(ctx.interaction)

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
        embed = discord.Embed(description=f"Successfully added **{amount}** 🍪 to **{user.display_name}**.", color=discord.Color.green())
        await ctx.respond(embed=embed, ephemeral=True)

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
        embed = discord.Embed(description=f"Successfully removed **{amount}** 🍪 from **{user.display_name}**.", color=discord.Color.red())
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="cookiesgiveall", description="[Manager] Give cookies to all members.", guild_ids=[1370009417726169250])
    @option("amount", description="The amount of cookies to give.", type=int, required=True)
    async def cookiesgiveall(self, ctx: discord.ApplicationContext, amount: int):
        if not self.check_is_manager(ctx.interaction):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return
        if amount <= 0:
            await ctx.respond("Please provide a positive number of cookies to give.", ephemeral=True)
            return
        await ctx.defer(ephemeral=True)
        member_ids = [member.id for member in ctx.guild.members if not member.bot]
        db.give_cookies_to_all(amount, member_ids)
        embed = discord.Embed(description=f"Successfully gave **{amount}** 🍪 to **{len(member_ids)}** members.", color=discord.Color.green())
        await ctx.followup.send(embed=embed)


def setup(bot):
    bot.add_cog(Cookies(bot))
