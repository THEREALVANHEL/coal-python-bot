import discord
from discord.ext import commands
from discord import option

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class LeaderboardView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=120)
        self.author = author
        self.current_page = 0
        self.message = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
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

        total_pages = ((total_users - 1) // limit) + 1
        embed = discord.Embed(title="🏆 Cookie Leaderboard", description=description, color=discord.Color.gold())
        embed.set_footer(text=f"Page {self.current_page + 1} / {total_pages} | VANHELISMYSENSEI ON TOP", icon_url=interaction.client.user.display_avatar.url)

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

class Cookies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cookie_manager_role = "🚨🚓Cookie Manager 🍪"

    def check_is_manager(self, interaction: discord.Interaction):
        user = interaction.user
        if isinstance(user, discord.Member):
            if user.guild_permissions.administrator:
                return True
            return any(role.name == self.cookie_manager_role for role in user.roles)
        return False

    @commands.slash_command(name="cookies", description="Check your or another user's cookie balance.", guild_ids=[1370009417726169250])
    @option("user", description="The user to check.", required=False)
    async def cookies(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target = user or ctx.author
        cookies = db.get_cookies(target.id)
        embed = discord.Embed(description=f"**{target.display_name}** has **{cookies}** 🍪 cookies.", color=discord.Color.gold())
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="cookiesrank", description="Check your or another user's cookie rank.", guild_ids=[1370009417726169250])
    @option("user", description="The user to check the rank of.", required=False)
    async def cookiesrank(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target = user or ctx.author
        rank = db.get_user_rank(target.id)
        total = db.get_cookies(target.id)
        embed = discord.Embed(description=f"**{target.display_name}** is rank **#{rank}** with **{total}** 🍪 cookies.", color=discord.Color.gold())
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="cookietop", description="Show the top users by cookies.", guild_ids=[1370009417726169250])
    async def cookietop(self, ctx: discord.ApplicationContext):
        leaderboard = db.get_leaderboard(limit=10)
        if not leaderboard:
            await ctx.respond("No one has cookies yet!", ephemeral=True)
            return

        desc = ""
        for i, entry in enumerate(leaderboard):
            user = ctx.guild.get_member(entry["user_id"])
            name = user.display_name if user else f"User ID: {entry['user_id']}"
            desc += f"**{i+1}.** {name} — 🍪 `{entry['cookies']}`\n"

        embed = discord.Embed(title="🍪 Cookie Leaderboard", description=desc, color=discord.Color.gold())
        embed.set_footer(text="VANHELISMYSENSEI ON TOP", icon_url=self.bot.user.display_avatar.url)
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="top", description="Full paginated cookie leaderboard.", guild_ids=[1370009417726169250])
    async def top(self, ctx: discord.ApplicationContext):
        view = LeaderboardView(ctx.author)
        message = await ctx.respond("Loading leaderboard...", ephemeral=True, view=view)
        view.message = await message.original_response()
        await view.update_leaderboard(ctx.interaction)

    @commands.slash_command(name="addcookies", description="[Manager] Add cookies to a user.", guild_ids=[1370009417726169250])
    @option("user", type=discord.Member, required=True)
    @option("amount", type=int, required=True)
    async def addcookies(self, ctx: discord.ApplicationContext, user: discord.Member, amount: int):
        if not self.check_is_manager(ctx.interaction):
            return await ctx.respond("You don't have permission.", ephemeral=True)
        if amount <= 0:
            return await ctx.respond("Amount must be positive.", ephemeral=True)

        db.add_cookies(user.id, amount)
        await ctx.respond(embed=discord.Embed(description=f"Added **{amount}** 🍪 to **{user.display_name}**.", color=discord.Color.green()), ephemeral=True)

    @commands.slash_command(name="removecookies", description="[Manager] Remove cookies from a user.", guild_ids=[1370009417726169250])
    @option("user", type=discord.Member, required=True)
    @option("amount", type=int, required=True)
    async def removecookies(self, ctx: discord.ApplicationContext, user: discord.Member, amount: int):
        if not self.check_is_manager(ctx.interaction):
            return await ctx.respond("You don't have permission.", ephemeral=True)
        if amount <= 0:
            return await ctx.respond("Amount must be positive.", ephemeral=True)

        db.remove_cookies(user.id, amount)
        await ctx.respond(embed=discord.Embed(description=f"Removed **{amount}** 🍪 from **{user.display_name}**.", color=discord.Color.red()), ephemeral=True)

    @commands.slash_command(name="cookiesgiveall", description="[Manager] Give cookies to all non-bot members.", guild_ids=[1370009417726169250])
    @option("amount", type=int, required=True)
    async def cookiesgiveall(self, ctx: discord.ApplicationContext, amount: int):
        if not self.check_is_manager(ctx.interaction):
            return await ctx.respond("You don't have permission.", ephemeral=True)
        if amount <= 0:
            return await ctx.respond("Amount must be positive.", ephemeral=True)

        await ctx.defer(ephemeral=True)
        member_ids = [m.id for m in ctx.guild.members if not m.bot]
        db.give_cookies_to_all(amount, member_ids)
        await ctx.followup.send(embed=discord.Embed(description=f"Gave **{amount}** 🍪 to **{len(member_ids)}** users.", color=discord.Color.green()))

def setup(bot):
    bot.add_cog(Cookies(bot))
