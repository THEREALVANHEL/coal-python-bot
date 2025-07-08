import discord
from discord.ext import commands
from discord import app_commands
import os, sys
import asyncio
from discord.ui import Button, View
from datetime import datetime

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

GUILD_ID = 1370009417726169250

COOKIE_ROLES = {        # balance : role-id (updated with new IDs)
    100:  1370998669884788788,
    500:  1370999721593671760,
    1000: 1371000389444305017,
    1750: 1371001322131947591,
    3000: 1371001806930579518,
    5000: 1371304693715964005
}

# Specific role that can manage cookies
COOKIE_MANAGER_ROLE_ID = 1372121024841125888

def has_cookie_manager_role(interaction: discord.Interaction) -> bool:
    """Check if user has cookie manager role or special admin role"""
    # Check for special admin role first (role ID 1376574861333495910)
    if has_special_permissions(interaction):
        return True
    
    return any(role.id == COOKIE_MANAGER_ROLE_ID for role in interaction.user.roles)

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
        """Update user's cookie-based roles - only give highest role, remove all others"""
        try:
            guild = user.guild
            
            # Find the highest role the user qualifies for
            highest_role_id = None
            highest_cookie_req = 0
            
            for cookie_req, role_id in COOKIE_ROLES.items():
                if cookies >= cookie_req and cookie_req > highest_cookie_req:
                    highest_cookie_req = cookie_req
                    highest_role_id = role_id
            
            # Get all cookie roles
            all_cookie_roles = []
            for role_id in COOKIE_ROLES.values():
                role = guild.get_role(role_id)
                if role:
                    all_cookie_roles.append(role)
            
            # Remove all cookie roles first
            roles_to_remove = [role for role in all_cookie_roles if role in user.roles]
            if roles_to_remove:
                try:
                    await user.remove_roles(*roles_to_remove, reason="Cookie milestone role update - clearing old roles")
                    print(f"[Cookies] Removed {len(roles_to_remove)} cookie roles from {user.display_name}")
                except Exception as e:
                    print(f"[Cookies] Error removing cookie roles from {user.display_name}: {e}")
            
            # Add only the highest role if user qualifies for one
            if highest_role_id:
                highest_role = guild.get_role(highest_role_id)
                if highest_role:
                    try:
                        await user.add_roles(highest_role, reason=f"Cookie milestone role update - {cookies} cookies")
                        print(f"[Cookies] Gave {highest_role.name} role to {user.display_name} ({cookies} cookies)")
                    except Exception as e:
                        print(f"[Cookies] Error adding cookie role {highest_role.name} to {user.display_name}: {e}")
                        
        except Exception as e:
            print(f"[Cookies] Error updating cookie roles for {user}: {e}")



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
        if not has_cookie_manager_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return

        try:
            # Defer immediately for all amounts
            await interaction.response.defer()
            
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
            await interaction.followup.send(embed=embed)

        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error adding cookies: {str(e)}", ephemeral=True)
            except:
                await interaction.response.send_message(f"❌ Error adding cookies: {str(e)}", ephemeral=True)

    @app_commands.command(name="removecookies", description="Remove cookies from a user with selection options (Manager only)")
    @app_commands.describe(
        user="User to remove cookies from", 
        option="Select removal option",
        custom_amount="Custom amount to remove (numbers, percentages like '25%', or special codes)"
    )
    @app_commands.choices(option=[
        app_commands.Choice(name="💔 Remove All Cookies", value="all"),
        app_commands.Choice(name="📉 Remove Half", value="half"),
        app_commands.Choice(name="🔢 Custom Amount", value="custom"),
        app_commands.Choice(name="📊 Custom Percentage", value="percentage"),
        app_commands.Choice(name="🎯 Special Code", value="special")
    ])
    async def removecookies(self, interaction: discord.Interaction, user: discord.Member, option: str, custom_amount: str = None):
        if not has_cookie_manager_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            # Defer immediately to prevent timeout
            await interaction.response.defer()
            
            old_data = db.get_user_data(user.id)
            old_cookies = old_data.get('cookies', 0)
            
            if old_cookies <= 0:
                embed = discord.Embed(
                    title="🍪 **No Cookies to Remove**",
                    description=f"{user.mention} doesn't have any cookies to remove! 🤷‍♂️",
                    color=0xff9966
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            amount = 0
            removal_type = ""
            
            if option == "custom":
                if not custom_amount:
                    embed = discord.Embed(
                        title="❌ **Missing Custom Amount**",
                        description="You must provide a custom amount to remove!",
                        color=0xff6b6b
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                try:
                    # Support both numbers and formatted strings
                    clean_amount = custom_amount.strip().replace(",", "").replace("k", "000").replace("K", "000")
                    amount = int(clean_amount)
                    if amount <= 0 or amount > old_cookies:
                        embed = discord.Embed(
                            title="❌ **Invalid Custom Amount**",
                            description=f"Custom amount must be between 1 and {old_cookies:,}!",
                            color=0xff6b6b
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    removal_type = f"🎯 Custom: {custom_amount}"
                except ValueError:
                    embed = discord.Embed(
                        title="❌ **Invalid Custom Amount**",
                        description="Please enter a valid number! Examples: `1000`, `5k`, `2,500`",
                        color=0xff6b6b
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                    
            elif option == "percentage":
                if not custom_amount:
                    embed = discord.Embed(
                        title="❌ **Missing Percentage**",
                        description="You must provide a percentage to remove! (e.g., 25%, 50%)",
                        color=0xff6b6b
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                try:
                    # Handle percentage input
                    percentage_str = custom_amount.strip().replace("%", "")
                    percentage = float(percentage_str)
                    if percentage <= 0 or percentage > 100:
                        raise ValueError("Invalid percentage")
                    amount = int(old_cookies * (percentage / 100))
                    if amount <= 0:
                        amount = 1
                    removal_type = f"📊 {percentage}% removal"
                except ValueError:
                    embed = discord.Embed(
                        title="❌ **Invalid Percentage**",
                        description="Please enter a valid percentage! Examples: `25%`, `50`, `75%`",
                        color=0xff6b6b
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                    
            elif option == "special":
                if not custom_amount:
                    embed = discord.Embed(
                        title="❌ **Missing Special Code**",
                        description="You must provide a special code! Examples: `reset`, `penalty`, `violation`",
                        color=0xff6b6b
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                
                # Handle special codes
                code = custom_amount.lower().strip()
                if code in ["reset", "clear", "zero"]:
                    amount = old_cookies
                    removal_type = "🔄 Account reset"
                elif code in ["penalty", "violation", "warning"]:
                    amount = min(1000, old_cookies // 4)  # Remove 25% or 1000, whichever is smaller
                    removal_type = "⚠️ Penalty removal"
                elif code in ["mild", "light", "small"]:
                    amount = min(500, old_cookies // 10)  # Remove 10% or 500, whichever is smaller
                    removal_type = "💫 Light penalty"
                elif code in ["severe", "major", "heavy"]:
                    amount = min(5000, old_cookies // 2)  # Remove 50% or 5000, whichever is smaller
                    removal_type = "🚨 Major penalty"
                else:
                    embed = discord.Embed(
                        title="❌ **Unknown Special Code**",
                        description="Valid codes: `reset`, `penalty`, `violation`, `mild`, `severe`",
                        color=0xff6b6b
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                    
            elif option == "all":
                amount = old_cookies
                removal_type = "🚨 Complete removal"
            elif option == "half":
                amount = old_cookies // 2
                removal_type = "⚖️ 50% reduction"
            
            # Process the removal
            db.remove_cookies(user.id, amount)
            new_cookies = old_cookies - amount
            
            # Update roles
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
            
            # Add removal type
            embed.add_field(name="📋 Removal Type", value=removal_type, inline=True)
            
            # Add custom amount info if provided
            if custom_amount and option in ["custom", "percentage", "special"]:
                embed.add_field(name="🎯 Input Used", value=f"`{custom_amount}`", inline=True)
            
            embed.set_author(name=f"Cookie removal by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="🍪 Enhanced Cookie Management System • Flexible removal options")
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error removing cookies: {str(e)}", ephemeral=True)
            except:
                await interaction.response.send_message(f"❌ Error removing cookies: {str(e)}", ephemeral=True)



    @app_commands.command(name="cookiesgiveall", description="Gives cookies to everyone in the server (Manager only)")
    @app_commands.describe(amount="Amount of cookies to give to each member")
    async def cookiesgiveall(self, interaction: discord.Interaction, amount: int):
        if not has_cookie_manager_role(interaction):
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

    @app_commands.command(name="removecookiesall", description="Remove cookies from everyone in the server (Manager only)")
    @app_commands.describe(amount="Amount to remove (number, percentage like '50%', or 'all' for complete removal)")
    async def removecookiesall(self, interaction: discord.Interaction, amount: str = "all"):
        if not has_cookie_manager_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        # Parse amount parameter
        try:
            amount_type = "all"
            removal_amount = 0
            percentage = 0
            
            amount_str = amount.strip().lower()
            
            if amount_str in ["all", "everything", "complete", "reset"]:
                amount_type = "all"
                description_text = "remove **ALL COOKIES** from **EVERY MEMBER**"
            elif amount_str.endswith("%"):
                # Percentage removal
                percentage = float(amount_str.replace("%", ""))
                if percentage <= 0 or percentage > 100:
                    raise ValueError("Percentage must be between 1-100")
                amount_type = "percentage"
                description_text = f"remove **{percentage}%** of cookies from **EVERY MEMBER**"
            else:
                # Fixed amount removal
                clean_amount = amount_str.replace(",", "").replace("k", "000").replace("K", "000")
                removal_amount = int(clean_amount)
                if removal_amount <= 0:
                    raise ValueError("Amount must be positive")
                amount_type = "fixed"
                description_text = f"remove **{removal_amount:,} cookies** from **EVERY MEMBER**"
                
        except ValueError as e:
            embed = discord.Embed(
                title="❌ **Invalid Amount**",
                description=f"Please provide a valid amount!\n\n**Examples:**\n• `all` - Remove all cookies\n• `50%` - Remove 50% of cookies\n• `1000` - Remove 1000 cookies\n• `5k` - Remove 5000 cookies",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Get current server stats first
        members = [member for member in interaction.guild.members if not member.bot]
        total_members = len(members)
        total_cookies_current = 0
        members_with_cookies = 0
        total_cookies_to_remove = 0
        
        for member in members:
            user_data = db.get_user_data(member.id)
            cookies = user_data.get('cookies', 0)
            if cookies > 0:
                total_cookies_current += cookies
                members_with_cookies += 1
                
                # Calculate removal amount for this member
                if amount_type == "all":
                    total_cookies_to_remove += cookies
                elif amount_type == "percentage":
                    member_removal = int(cookies * (percentage / 100))
                    total_cookies_to_remove += member_removal
                elif amount_type == "fixed":
                    member_removal = min(removal_amount, cookies)
                    total_cookies_to_remove += member_removal
        
        # Confirmation check with detailed stats
        embed = discord.Embed(
            title="⚠️ **MASS COOKIE REMOVAL**",
            description=f"This will {description_text} in the server!\n\n**⚠️ THIS ACTION CANNOT BE UNDONE!**",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📊 **Current Server Stats**",
            value=f"**Total Members:** {total_members:,}\n**Members with Cookies:** {members_with_cookies:,}\n**Current Total Cookies:** {total_cookies_current:,}",
            inline=False
        )
        embed.add_field(
            name="🎯 **Removal Details**",
            value=f"**Amount Type:** {amount_type.title()}\n**Cookies to Remove:** {total_cookies_to_remove:,}\n**Remaining After:** {total_cookies_current - total_cookies_to_remove:,}",
            inline=False
        )
        
        confirmation_text = "CONFIRM REMOVAL" if amount_type != "all" else "CONFIRM RESET"
        embed.add_field(
            name="⏰ **Confirmation Required**",
            value=f"You have **30 seconds** to confirm this action.\nType **{confirmation_text}** in the next message to proceed.",
            inline=False
        )
        embed.set_footer(text="🛑 Admin Action • Use with extreme caution")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        def check(m):
            return (m.author == interaction.user and 
                   m.channel == interaction.channel and 
                   m.content.upper() in ["CONFIRM RESET", "CONFIRM REMOVAL"])
        
        try:
            # Wait for confirmation
            confirmation = await interaction.client.wait_for('message', timeout=30.0, check=check)
            
            # Delete the confirmation message for cleanliness
            try:
                await confirmation.delete()
            except:
                pass
            
            # Process the removal
            processing_embed = discord.Embed(
                title="🔄 **Processing Cookie Removal...**",
                description=f"Removing cookies from server members ({amount_type} removal)...",
                color=0xffaa00
            )
            await interaction.edit_original_response(embed=processing_embed)
            
            members = [member for member in interaction.guild.members if not member.bot]
            affected_count = 0
            total_cookies_removed = 0
            
            for member in members:
                try:
                    user_data = db.get_user_data(member.id)
                    old_cookies = user_data.get('cookies', 0)
                    
                    if old_cookies > 0:
                        # Calculate removal amount for this member
                        removal_for_member = 0
                        
                        if amount_type == "all":
                            removal_for_member = old_cookies
                        elif amount_type == "percentage":
                            removal_for_member = int(old_cookies * (percentage / 100))
                        elif amount_type == "fixed":
                            removal_for_member = min(removal_amount, old_cookies)
                        
                        if removal_for_member > 0:
                            new_cookies = old_cookies - removal_for_member
                            db.set_cookies(member.id, new_cookies)
                            await self.update_cookie_roles(member, new_cookies)
                            total_cookies_removed += removal_for_member
                            affected_count += 1
                            
                except Exception as e:
                    print(f"[RemoveCookiesAll] Error processing {member.display_name}: {e}")
                    continue
            
            # Final confirmation embed
            operation_title = "MASS COOKIE REMOVAL COMPLETE" if amount_type != "all" else "COOKIE RESET COMPLETE"
            success_embed = discord.Embed(
                title=f"✅ **{operation_title}**",
                description=f"Successfully processed cookies for **{affected_count}** members!",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            success_embed.add_field(
                name="📊 **Removal Statistics**",
                value=f"**Members Affected:** {affected_count:,}\n**Total Cookies Removed:** {total_cookies_removed:,}\n**Removal Type:** {amount_type.title()}",
                inline=False
            )
            
            if amount_type == "percentage":
                success_embed.add_field(
                    name="🎯 **Removal Details**",
                    value=f"• Removed {percentage}% from each member\n• Cookie roles updated automatically\n• Members keep their remaining cookies",
                    inline=False
                )
            elif amount_type == "fixed":
                success_embed.add_field(
                    name="🎯 **Removal Details**",
                    value=f"• Removed up to {removal_amount:,} cookies per member\n• Members with fewer cookies had all removed\n• Cookie roles updated automatically",
                    inline=False
                )
            else:  # all
                success_embed.add_field(
                    name="🔄 **Next Steps**",
                    value="• All cookie-based roles have been removed\n• Members can start earning cookies again\n• Cookie leaderboard is now clean",
                    inline=False
                )
            
            success_embed.set_author(
                name=f"Mass removal by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            success_embed.set_footer(text=f"🍪 Cookie Management System • {amount_type.title()} removal executed")
            
            await interaction.edit_original_response(embed=success_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ **Confirmation Timeout**",
                description=f"Cookie removal cancelled - no confirmation received within 30 seconds.\n**Operation:** {amount_type.title()} removal",
                color=0x999999
            )
            timeout_embed.set_footer(text="🛡️ Safety feature - operation cancelled")
            await interaction.edit_original_response(embed=timeout_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Reset Failed**",
                description=f"An error occurred during the cookie reset process: {str(e)}",
                color=0xff6b6b
            )
            await interaction.edit_original_response(embed=error_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Cookies(bot))
    
