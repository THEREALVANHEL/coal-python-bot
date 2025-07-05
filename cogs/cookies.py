import discord
from discord.ext import commands
from discord import app_commands
import os, sys
from discord.ui import Button, View
from datetime import datetime

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250

COOKIE_ROLES = {        # balance : role-id (updated with new IDs)
    100:  1370998669884788788,
    500:  1370999721593671760,
    1000: 1371000389444305017,
    1750: 1371001322131947591,
    3000: 1371001806930579518,
    5000: 1371304693715964005
}

MANAGER_ROLES = ["🦥 Overseer", "Forgotten one", "🚨 Lead moderator"]
ADMIN_ROLES = ["🦥 Overseer", "Forgotten one"]  # Roles that can remove all cookies

def has_manager_role(interaction: discord.Interaction) -> bool:
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in MANAGER_ROLES for role in user_roles)

def has_admin_role(interaction: discord.Interaction) -> bool:
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in ADMIN_ROLES for role in user_roles)

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

    async def create_cookie_leaderboard_embed(self, page: int):
        items_per_page = 10
        skip = (page - 1) * items_per_page
        
        all_users = db.get_leaderboard('cookies')
        total_users = len(all_users)
        total_pages = (total_users + items_per_page - 1) // items_per_page
        page_users = all_users[skip:skip + items_per_page]

        # Super sweet cookie-themed design
        embed = discord.Embed(
            title="🍪 **COOKIE EMPIRE** 🍪",
            description="🌟 *The Sweet Champions of Deliciousness* 🌟",
            color=0xdaa520,
            timestamp=datetime.now()
        )

        leaderboard_text = []
        for i, user_data in enumerate(page_users, start=skip + 1):
            user_id = user_data['user_id']
            cookies = user_data.get('cookies', 0)
            
            try:
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                username = user.display_name if hasattr(user, 'display_name') else user.name
            except:
                username = f"User {user_id}"

            # Epic cookie ranking system
            if i == 1:
                rank_style = f"👑 **#{i} COOKIE EMPEROR {username}** 👑"
                style_suffix = " 🍪🍪🍪"
            elif i == 2:
                rank_style = f"🥈 **#{i} SWEET MASTER {username}** 🥈"
                style_suffix = " 🍪🍪"
            elif i == 3:
                rank_style = f"🥉 **#{i} DESSERT KING {username}** 🥉"
                style_suffix = " 🍪"
            elif i <= 5:
                rank_style = f"🔸 **#{i} SUGAR LORD {username}**"
                style_suffix = " ⭐"
            elif i <= 10:
                rank_style = f"▫️ **#{i} TREAT COLLECTOR {username}**"
                style_suffix = " 🍰"
            else:
                rank_style = f"#{i} • {username}"
                style_suffix = ""

            # Cookie tier system
            if cookies >= 10000:
                cookie_tier = "🏆 **LEGENDARY BAKER**"
                cookie_emoji = "🍪🍪🍪🍪🍪"
            elif cookies >= 5000:
                cookie_tier = "💎 **MASTER BAKER**"
                cookie_emoji = "🍪🍪🍪🍪"
            elif cookies >= 1750:
                cookie_tier = "⭐ **EXPERT BAKER**"
                cookie_emoji = "🍪🍪🍪"
            elif cookies >= 1000:
                cookie_tier = "⭐ **SKILLED BAKER**"
                cookie_emoji = "🍪🍪"
            elif cookies >= 500:
                cookie_tier = "🌟 **AMATEUR BAKER**"
                cookie_emoji = "🍪"
            elif cookies >= 100:
                cookie_tier = "✨ **COOKIE LOVER**"
                cookie_emoji = "🧁"
            else:
                cookie_tier = "🔰 **SWEET TOOTH**"
                cookie_emoji = "🍰"
            
            # Create cookie progress bar towards next milestone
            milestones = [100, 500, 1000, 1750, 3000, 5000, 10000, 25000]
            next_milestone = next((m for m in milestones if cookies < m), 25000)
            prev_milestone = max([m for m in milestones if cookies >= m] + [0])
            
            if next_milestone > prev_milestone:
                progress = (cookies - prev_milestone) / (next_milestone - prev_milestone)
                progress_bars = int(progress * 8)
                cookie_bar = "🍪" * progress_bars + "▱" * (8 - progress_bars)
                progress_text = f"`{cookie_bar}` → {next_milestone:,}"
            else:
                progress_text = "🏆 **MAX LEVEL ACHIEVED!**"
            
            entry = f"{rank_style}{style_suffix}\n🍪 **{cookies:,} Cookies** • {cookie_tier}\n{progress_text} {cookie_emoji}"
            leaderboard_text.append(entry)

        embed.description = f"🌟 *The Sweet Champions of Deliciousness* 🌟\n\n" + "\n\n".join(leaderboard_text)
        
        # Sweet stats section
        embed.add_field(
            name="🍪 **Cookie Stats**",
            value=f"🧁 **{total_users}** Cookie Collectors\n🍰 **Page {page}/{total_pages}**\n🎯 **Stay Sweet!**",
            inline=True
        )
        
        embed.add_field(
            name="💡 **Cookie Tips**",
            value="💬 Stay active to collect\n🎮 Participate in events\n🏆 Reach role milestones!",
            inline=True
        )
        
        embed.set_footer(text="🍪 Cookie Leaderboard • Sweetness overload! • 🌟 Deliciously competitive!")
        
        return embed

    @app_commands.command(name="cookies", description="💰 Check your delicious cookie balance")
    @app_commands.describe(user="User to check cookies for")
    async def cookies(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        try:
            user_data = db.get_user_data(target.id)
            cookies = user_data.get('cookies', 0)
            
            # Get user's rank
            leaderboard = db.get_leaderboard('cookies')
            rank = next((i + 1 for i, u in enumerate(leaderboard) if u['user_id'] == target.id), None)
            
            embed = discord.Embed(
                title="🍪 Cookie Balance",
                color=0xdaa520,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            # Main balance display
            embed.add_field(
                name="💰 Current Balance",
                value=f"**{cookies:,}** cookies",
                inline=True
            )
            
            # Rank display
            if rank:
                embed.add_field(
                    name="📊 Server Rank",
                    value=f"**#{rank}** of {len(leaderboard)}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="📊 Server Rank",
                    value="Not ranked yet",
                    inline=True
                )
            
            # Cookie roles progress
            achieved_roles = []
            next_role = None
            
            for role_threshold, role_id in COOKIE_ROLES.items():
                if cookies >= role_threshold:
                    achieved_roles.append(f"✅ {role_threshold:,} cookies")
                else:
                    if not next_role:
                        next_role = f"🎯 Next: {role_threshold:,} cookies ({role_threshold - cookies:,} needed)"
                    break
            
            if achieved_roles:
                embed.add_field(
                    name="🏆 Achieved Milestones",
                    value="\n".join(achieved_roles[-3:]),  # Show last 3
                    inline=False
                )
            
            if next_role:
                embed.add_field(
                    name="🎯 Next Milestone",
                    value=next_role,
                    inline=False
                )
            
            embed.set_footer(text="💫 Cookie System • Collect cookies by staying active!")
            
            pronoun = "Your" if target == interaction.user else f"{target.display_name}'s"
            embed.set_author(
                name=f"{pronoun} Cookie Stats",
                icon_url=target.display_avatar.url
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Couldn't retrieve cookie data. Please try again later.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    # REMOVED: cookietop command - now use /leaderboard cookies
    @app_commands.command(name="cookietop", description="🍪 View cookie leaderboard (use /leaderboard instead)")
    async def cookietop_redirect(self, interaction: discord.Interaction, page: int = 1):
        embed = discord.Embed(
            title="🔄 Command Updated",
            description="The cookie leaderboard has been moved to our new unified system!",
            color=0x7c3aed
        )
        embed.add_field(
            name="✨ New Command",
            value="Use `/leaderboard type:🍪 Cookies` for the cookie leaderboard",
            inline=False
        )
        embed.add_field(
            name="🎉 What's New",
            value="• Better pagination\n• Elegant design\n• All leaderboards in one place",
            inline=False
        )
        embed.set_footer(text="💫 This command will be removed in a future update")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # REMOVED: cookiesrank command - now use unified leaderboard
    @app_commands.command(name="cookiesrank", description="🍪 View your cookie rank (use /leaderboard instead)")
    async def cookiesrank_redirect(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔄 **Command Updated**",
            description="Cookie ranking has been moved to our unified leaderboard system!",
            color=0x7c3aed
        )
        embed.add_field(
            name="✨ **New Command**",
            value="Use `/leaderboard type:🍪 Cookies` for the cookie leaderboard with your rank!",
            inline=False
        )
        embed.add_field(
            name="🎉 **What's New**",
            value="• Beautiful cookie empire design\n• Progress bars and milestones\n• Smooth pagination\n• Cookie tier system with achievements",
            inline=False
        )
        embed.set_footer(text="💫 This command will be removed soon")
        await interaction.response.send_message(embed=embed, ephemeral=True)

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

    @app_commands.command(name="removeallcookies", description="Remove ALL cookies from ALL users (Admin only)")
    async def removeallcookies(self, interaction: discord.Interaction):
        if not has_admin_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command! Only Overseers and Forgotten ones can use this.", ephemeral=True)
            return

        # Confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.confirmed = False

            @discord.ui.button(label="⚠️ CONFIRM REMOVAL", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    result = db.remove_all_cookies_admin(interaction.user.id)
                    
                    if result["success"]:
                        embed = discord.Embed(
                            title="🗑️ All Cookies Removed",
                            description=f"**{result['users_affected']}** users had their cookies reset to 0",
                            color=0xff0000
                        )
                        embed.add_field(name="⚠️ Admin Action", value=f"Performed by {interaction.user.mention}", inline=False)
                        
                        # Update all cookie roles for users in the server
                        guild = interaction.guild
                        updated_members = 0
                        for member in guild.members:
                            if not member.bot:
                                try:
                                    await self.update_cookie_roles(member, 0)
                                    updated_members += 1
                                except:
                                    pass
                        
                        embed.add_field(name="🔄 Role Updates", value=f"Updated roles for {updated_members} members", inline=False)
                        await interaction.response.edit_message(embed=embed, view=None)
                    else:
                        await interaction.response.edit_message(
                            content=f"❌ Error removing cookies: {result['message']}", 
                            embed=None, 
                            view=None
                        )
                        
                except Exception as e:
                    await interaction.response.edit_message(
                        content=f"❌ Error removing cookies: {str(e)}", 
                        embed=None, 
                        view=None
                    )

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = discord.Embed(
                    title="❌ Action Cancelled",
                    description="No cookies were removed",
                    color=0x999999
                )
                await interaction.response.edit_message(embed=embed, view=None)

        view = ConfirmView()
        embed = discord.Embed(
            title="⚠️ DANGER: Remove All Cookies",
            description="This will remove ALL cookies from ALL users in the database!\n\n**This action cannot be undone!**",
            color=0xff0000
        )
        embed.add_field(name="📊 Impact", value="• All users will have 0 cookies\n• All cookie roles will be removed\n• This affects the entire server", inline=False)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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
    
