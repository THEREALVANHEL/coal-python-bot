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

class CustomRemovalModal(discord.ui.Modal):
    def __init__(self, user: discord.Member, max_cookies: int):
        super().__init__(title="🔢 Custom Cookie Removal")
        self.user = user
        self.max_cookies = max_cookies
        
        self.amount_input = discord.ui.TextInput(
            label="Amount to Remove",
            placeholder=f"Enter amount (1 - {max_cookies:,})",
            max_length=10,
            required=True
        )
        
        self.reason_input = discord.ui.TextInput(
            label="Reason (Optional)",
            placeholder="Why are you removing these cookies?",
            style=discord.TextStyle.paragraph,
            max_length=200,
            required=False
        )
        
        self.add_item(self.amount_input)
        self.add_item(self.reason_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
            
            if amount <= 0 or amount > self.max_cookies:
                embed = discord.Embed(
                    title="❌ **Invalid Amount**",
                    description=f"Amount must be between 1 and {self.max_cookies:,}!",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Remove the cookies
            db.remove_cookies(self.user.id, amount)
            new_cookies = self.max_cookies - amount
            
            # Update roles
            cookies_cog = interaction.client.get_cog("Cookies")
            if cookies_cog:
                await cookies_cog.update_cookie_roles(self.user, new_cookies)
            
            # Check for role downgrades
            role_lost = ""
            for threshold in sorted(COOKIE_ROLES.keys(), reverse=True):
                if new_cookies < threshold <= self.max_cookies:
                    role_lost = f"\n💔 **Role Lost:** Below {threshold:,} cookies threshold"
                    break
            
            embed = discord.Embed(
                title="🗑️ **Custom Cookie Removal Complete**",
                description=f"Removed **{amount:,}** cookies from {self.user.mention} 📉{role_lost}",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Previous Balance", value=f"🍪 {self.max_cookies:,}", inline=True)
            embed.add_field(name="➖ Amount Removed", value=f"🗑️ {amount:,}", inline=True)
            embed.add_field(name="💰 New Balance", value=f"📉 {new_cookies:,}", inline=True)
            
            # Add percentage decrease
            percentage = (amount / self.max_cookies) * 100
            embed.add_field(name="📉 Decrease", value=f"📊 -{percentage:.1f}%", inline=True)
            
            if self.reason_input.value:
                embed.add_field(name="📋 Reason", value=f"💭 {self.reason_input.value}", inline=False)
            
            embed.set_author(name=f"Custom removal by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="🍪 Cookie Management System • Custom action")
            
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ **Invalid Input**",
                description="Please enter a valid number!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

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
            
            # Check for milestone achievements
            milestone_achieved = ""
            for threshold in COOKIE_ROLES.keys():
                if old_cookies < threshold <= new_cookies:
                    milestone_achieved = f"\n🎉 **Milestone Achieved!** Reached {threshold:,} cookies!"
                    break
            
            embed = discord.Embed(
                title="🍪 **Cookie Boost Delivered!**",
                description=f"Successfully added **{amount:,}** delicious cookies to {user.mention}! 🎉{milestone_achieved}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Previous Balance", value=f"🍪 {old_cookies:,}", inline=True)
            embed.add_field(name="➕ Amount Added", value=f"🎁 {amount:,}", inline=True)
            embed.add_field(name="💰 New Balance", value=f"✨ {new_cookies:,}", inline=True)
            
            # Add percentage increase
            if old_cookies > 0:
                percentage = ((new_cookies - old_cookies) / old_cookies) * 100
                embed.add_field(name="📈 Increase", value=f"📊 +{percentage:.1f}%", inline=True)
            
            embed.set_author(name=f"Cookie boost by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="🍪 Cookie Management System • Sweet success!")
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding cookies: {str(e)}", ephemeral=True)

    @app_commands.command(name="removecookies", description="Remove cookies from a user with selection options (Manager only)")
    @app_commands.describe(user="User to remove cookies from", option="Select removal option")
    @app_commands.choices(option=[
        app_commands.Choice(name="💔 Remove All Cookies", value="all"),
        app_commands.Choice(name="📉 Remove Half", value="half"),
        app_commands.Choice(name="🔢 Custom Amount", value="custom")
    ])
    async def removecookies(self, interaction: discord.Interaction, user: discord.Member, option: str):
        if not has_manager_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            old_data = db.get_user_data(user.id)
            old_cookies = old_data.get('cookies', 0)
            
            if old_cookies <= 0:
                embed = discord.Embed(
                    title="🍪 **No Cookies to Remove**",
                    description=f"{user.mention} doesn't have any cookies to remove! 🤷‍♂️",
                    color=0xff9966
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if option == "custom":
                # Show modal for custom amount
                modal = CustomRemovalModal(user, old_cookies)
                await interaction.response.send_modal(modal)
                return
            elif option == "all":
                amount = old_cookies
            elif option == "half":
                amount = old_cookies // 2
            
            db.remove_cookies(user.id, amount)
            new_cookies = old_cookies - amount
            
            await self.update_cookie_roles(user, new_cookies)
            
            # Check for role downgrades
            role_lost = ""
            for threshold in sorted(COOKIE_ROLES.keys(), reverse=True):
                if new_cookies < threshold <= old_cookies:
                    role_lost = f"\n💔 **Role Lost:** Below {threshold:,} cookies threshold"
                    break
            
            embed = discord.Embed(
                title="🗑️ **Cookies Removed Successfully**",
                description=f"Removed **{amount:,}** cookies from {user.mention} 📉{role_lost}",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Previous Balance", value=f"🍪 {old_cookies:,}", inline=True)
            embed.add_field(name="➖ Amount Removed", value=f"🗑️ {amount:,}", inline=True)
            embed.add_field(name="💰 New Balance", value=f"📉 {new_cookies:,}", inline=True)
            
            # Add percentage decrease
            if old_cookies > 0:
                percentage = ((old_cookies - new_cookies) / old_cookies) * 100
                embed.add_field(name="📉 Decrease", value=f"📊 -{percentage:.1f}%", inline=True)
            
            # Add removal reason
            removal_reasons = {
                "all": "🚨 Complete removal",
                "half": "⚖️ 50% reduction",
                "custom": "🎯 Custom amount"
            }
            embed.add_field(name="📋 Removal Type", value=removal_reasons[option], inline=True)
            
            embed.set_author(name=f"Cookie removal by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="🍪 Cookie Management System • Disciplinary action")
            
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
    
