import discord
from discord.ext import commands
from discord import app_commands
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250

COOKIE_ROLES = {        # balance : role-id
    100:  1370998669884788788,
    500:  1370999721593671760,
    1000: 1371000389444305017,
    1750: 1371001322131947591,
    3000: 1371001806930579518,
    5000: 1371002217737842779,
    7500: 1371002618477568050,
    10000: 1371003018494550056,
}

MANAGER_ROLES = ["🦥 Overseer", "Forgotten one", "🚨 Lead moderator"]

def has_manager_role(interaction: discord.Interaction) -> bool:
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in MANAGER_ROLES for role in user_roles)

class Cookies(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Cookies] Loaded successfully.")

    async def update_cookie_roles(self, user: discord.Member, cookies: int):
        """Update user's cookie milestone roles"""
        try:
            roles_to_add = []
            roles_to_remove = []
            
            for threshold, role_id in COOKIE_ROLES.items():
                role = user.guild.get_role(role_id)
                if role:
                    if cookies >= threshold and role not in user.roles:
                        roles_to_add.append(role)
                    elif cookies < threshold and role in user.roles:
                        roles_to_remove.append(role)
            
            if roles_to_add:
                await user.add_roles(*roles_to_add)
            if roles_to_remove:
                await user.remove_roles(*roles_to_remove)
                
        except Exception as e:
            print(f"Error updating cookie roles for {user}: {e}")

    @app_commands.command(name="cookies", description="View your or another user's cookie balance")
    @app_commands.describe(user="User to check cookies for")
    async def cookies(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        try:
            user_data = db.get_user_data(target.id)
            cookies = user_data.get('cookies', 0)
            
            # Get next milestone
            next_milestone = None
            for threshold in sorted(COOKIE_ROLES.keys()):
                if cookies < threshold:
                    next_milestone = threshold
                    break
            embed = discord.Embed(
                title="🍪 Cookie Balance",
                description=f"**{target.display_name}** has **{cookies:,}** cookies!",
                color=0xdaa520
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            if next_milestone:
                needed = next_milestone - cookies
                embed.add_field(
                    name="🎯 Next Milestone", 
                    value=f"{next_milestone:,} cookies ({needed:,} needed)", 
                    inline=False
                )
            else:
                embed.add_field(name="🏆 Status", value="All milestones achieved!", inline=False)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting cookie data: {str(e)}", ephemeral=True)

    @app_commands.command(name="cookietop", description="Shows the top 10 users with the most cookies")
    async def cookietop(self, interaction: discord.Interaction):
        try:
            leaderboard = db.get_leaderboard('cookies', limit=10)
            
            if not leaderboard:
                await interaction.response.send_message("❌ No cookie data available!", ephemeral=True)
                return

            embed = discord.Embed(
                title="🍪 Cookie Leaderboard - Top 10",
                color=0xdaa520
            )

            leaderboard_text = []
            for i, user_data in enumerate(leaderboard, 1):
                user_id = user_data['user_id']
                cookies = user_data.get('cookies', 0)
                
                try:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    username = user.display_name if hasattr(user, 'display_name') else user.name
                except:
                    username = f"User {user_id}"

                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard_text.append(f"{medal} **{username}** - {cookies:,} cookies")

            embed.description = "\n".join(leaderboard_text)
            embed.set_footer(text="Keep collecting those cookies!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting leaderboard: {str(e)}", ephemeral=True)

    @app_commands.command(name="cookiesrank", description="Displays your current rank in the cookie leaderboard")
    async def cookiesrank(self, interaction: discord.Interaction):
        try:
            leaderboard = db.get_leaderboard('cookies')
            user_data = db.get_user_data(interaction.user.id)
            cookies = user_data.get('cookies', 0)
            
            rank = next((i + 1 for i, u in enumerate(leaderboard) if u['user_id'] == interaction.user.id), None)
            if rank is None:
                await interaction.response.send_message("❌ You're not on the leaderboard yet! Start collecting cookies!", ephemeral=True)
                return

            embed = discord.Embed(
                title="🏅 Your Cookie Rank",
                description=f"**Rank:** #{rank}\n**Cookies:** {cookies:,}",
                color=0xdaa520
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            # Show users around their rank
            start_idx = max(0, rank - 3)
            end_idx = min(len(leaderboard), rank + 2)
            context_users = []
            
            for i in range(start_idx, end_idx):
                user_data = leaderboard[i]
                user_cookies = user_data.get('cookies', 0)
                try:
                    user = self.bot.get_user(user_data['user_id'])
                    username = user.display_name if user else f"User {user_data['user_id']}"
                except:
                    username = f"User {user_data['user_id']}"
                
                prefix = "**" if i + 1 == rank else ""
                suffix = "** ⬅️" if i + 1 == rank else ""
                context_users.append(f"{prefix}#{i + 1} {username} - {user_cookies:,}{suffix}")
            
            embed.add_field(name="📊 Around Your Rank", value="\n".join(context_users), inline=False)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting rank: {str(e)}", ephemeral=True)

    @app_commands.command(name="addcookies", description="Adds cookies to a user (Manager only)")
    @app_commands.describe(user="User to give cookies to", amount="Amount of cookies to add")
    async def addcookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not has_manager_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return

        try:
            old_data = db.get_user_data(user.id)
            old_cookies = old_data.get('cookies', 0)
            
            db.add_cookies(user.id, amount)
            new_cookies = old_cookies + amount
            
            await self.update_cookie_roles(user, new_cookies)
            
            embed = discord.Embed(
                title="🍪 Cookies Added",
                description=f"Added **{amount:,}** cookies to {user.mention}",
                color=0x00ff00
            )
            embed.add_field(name="Previous", value=f"{old_cookies:,}", inline=True)
            embed.add_field(name="New Balance", value=f"{new_cookies:,}", inline=True)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding cookies: {str(e)}", ephemeral=True)

    @app_commands.command(name="removecookies", description="Removes cookies from a user (Manager only)")
    @app_commands.describe(user="User to remove cookies from", amount="Amount of cookies to remove")
    async def removecookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not has_manager_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return

        try:
            old_data = db.get_user_data(user.id)
            old_cookies = old_data.get('cookies', 0)
            
            if old_cookies < amount:
                await interaction.response.send_message(f"❌ User only has {old_cookies:,} cookies!", ephemeral=True)
                return
            
            db.remove_cookies(user.id, amount)
            new_cookies = old_cookies - amount
            
            await self.update_cookie_roles(user, new_cookies)
            
            embed = discord.Embed(
                title="🍪 Cookies Removed",
                description=f"Removed **{amount:,}** cookies from {user.mention}",
                color=0xff6b6b
            )
            embed.add_field(name="Previous", value=f"{old_cookies:,}", inline=True)
            embed.add_field(name="New Balance", value=f"{new_cookies:,}", inline=True)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing cookies: {str(e)}", ephemeral=True)

    @app_commands.command(name="cookiesgiveall", description="Gives cookies to everyone in the server (Manager only)")
    @app_commands.describe(amount="Amount of cookies to give to each member")
    async def cookiesgiveall(self, interaction: discord.Interaction, amount: int):
        if not has_manager_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            members = [member for member in interaction.guild.members if not member.bot]
            total_given = 0
            for member in members:
                db.add_cookies(member.id, amount)
                user_data = db.get_user_data(member.id)
                new_cookies = user_data.get('cookies', 0)
                await self.update_cookie_roles(member, new_cookies)
                total_given += amount

            embed = discord.Embed(
                title="🍪 Mass Cookie Distribution",
                description=f"Gave **{amount:,}** cookies to **{len(members)}** members!",
                color=0x00ff00
            )
            embed.add_field(name="📊 Total Distributed", value=f"{total_given:,} cookies", inline=False)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error distributing cookies: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Cookies(bot))
    
