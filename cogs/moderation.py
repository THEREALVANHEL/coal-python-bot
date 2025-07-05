import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# Config
GUILD_ID = 1370009417726169250

MODERATOR_ROLES = ["Moderator 🚨🚓", "🚨 Lead moderator"]
FOOTER_TXT = "VANHELISMYSENSEI"

# Permission check helper
def has_moderator_role(interaction: discord.Interaction) -> bool:
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in MODERATOR_ROLES for role in user_roles)

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Moderation] Loaded successfully.")

    @app_commands.command(name="modclear", description="Deletes a specified number of messages from a channel")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def modclear(self, interaction: discord.Interaction, amount: int):
        # Check permissions
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need 'Manage Messages' permission to use this command!", ephemeral=True)
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            deleted = await interaction.channel.purge(limit=amount)
            
            embed = discord.Embed(
                title="🗑️ Messages Cleared",
                description=f"Successfully deleted **{len(deleted)}** messages",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=FOOTER_TXT)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to delete messages in this channel!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(
        user="User to warn",
        reason="Reason for the warning"
        )
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        # Add warning to database
        try:
            db.add_warning(user.id, reason, interaction.user.id)
            warnings = db.get_user_warnings(user.id)
            
            embed = discord.Embed(
                title="⚠️ User Warned",
                description=f"**User:** {user.mention}\n**Reason:** {reason}\n**Total Warnings:** {len(warnings)}",
                color=0xff9900,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=FOOTER_TXT)

            await interaction.response.send_message(embed=embed)

            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="⚠️ Warning Received",
                    description=f"You have been warned in **{interaction.guild.name}**\n\n**Reason:** {reason}",
                    color=0xff9900
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled

        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding warning: {str(e)}", ephemeral=True)

    @app_commands.command(name="warnings", description="View warnings for a user")
    @app_commands.describe(user="User to check warnings for")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            warnings = db.get_user_warnings(user.id)
            
            if not warnings:
                embed = discord.Embed(
                    title="⚠️ User Warnings",
                    description=f"{user.mention} has no warnings!",
                    color=0x00ff00
                )
            else:
                warning_list = []
                for i, warning in enumerate(warnings[-10:], 1):  # Show last 10 warnings
                    warning_list.append(f"**{i}.** {warning.get('reason', 'No reason')} - <t:{warning.get('timestamp', 0)}:R>")
                
                embed = discord.Embed(
                    title="⚠️ User Warnings",
                    description=f"**User:** {user.mention}\n**Total Warnings:** {len(warnings)}\n\n" + "\n".join(warning_list),
                    color=0xff9900
                )

            embed.set_footer(text=FOOTER_TXT)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving warnings: {str(e)}", ephemeral=True)

    @app_commands.command(name="updateroles", description="Updates roles based on a user's current level and cookies")
    @app_commands.describe(user="User to update roles for")
    async def updateroles(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need 'Manage Roles' permission to use this command!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Get user data from database
            user_data = db.get_user_data(user.id)
            level = user_data.get('level', 0)
            cookies = user_data.get('cookies', 0)

            # Define role mappings (you can adjust these)
            level_roles = {
                10: "Level 10",
                25: "Level 25", 
                50: "Level 50",
                75: "Level 75",
                100: "Level 100"
            }

            cookie_roles = {
                100: "Cookie Collector",
                500: "Cookie Enthusiast",
                1000: "Cookie Master",
                2500: "Cookie Legend"
            }

            roles_added = []
            roles_removed = []

            # Update level roles
            for required_level, role_name in level_roles.items():
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if role:
                    if level >= required_level and role not in user.roles:
                        await user.add_roles(role)
                        roles_added.append(role_name)
                    elif level < required_level and role in user.roles:
                        await user.remove_roles(role)
                        roles_removed.append(role_name)

            # Update cookie roles
            for required_cookies, role_name in cookie_roles.items():
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if role:
                    if cookies >= required_cookies and role not in user.roles:
                        await user.add_roles(role)
                        roles_added.append(role_name)
                    elif cookies < required_cookies and role in user.roles:
                        await user.remove_roles(role)
                        roles_removed.append(role_name)

            # Create response embed
            embed = discord.Embed(
                title="🔄 Roles Updated",
                description=f"**User:** {user.mention}\n**Level:** {level}\n**Cookies:** {cookies}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            if roles_added:
                embed.add_field(name="➕ Roles Added", value="\n".join(roles_added), inline=False)
            if roles_removed:
                embed.add_field(name="➖ Roles Removed", value="\n".join(roles_removed), inline=False)
            if not roles_added and not roles_removed:
                embed.add_field(name="ℹ️ No Changes", value="User already has appropriate roles", inline=False)

            embed.set_footer(text=FOOTER_TXT)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error updating roles: {str(e)}", ephemeral=True)

    @app_commands.command(name="dbstats", description="View database statistics and data overview")
    async def dbstats(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need 'Administrator' permission to use this command!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            stats = db.get_database_stats()
            
            if not stats["success"]:
                await interaction.followup.send(f"❌ Error getting database stats: {stats['message']}", ephemeral=True)
                return

            embed = discord.Embed(
                title="📊 Database Statistics",
                color=0x7289da,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👥 Users",
                value=f"**Total Users:** {stats['total_users']}\n**With XP:** {stats['users_with_xp']}\n**With Cookies:** {stats['users_with_cookies']}\n**With Coins:** {stats['users_with_coins']}",
                inline=True
            )
            
            embed.add_field(
                name="📊 Totals",
                value=f"**Total XP:** {stats['total_xp']:,}\n**Total Cookies:** {stats['total_cookies']:,}",
                inline=True
            )
            
            embed.set_footer(text=f"{FOOTER_TXT} • Database Health Check")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error checking database: {str(e)}", ephemeral=True)

    @app_commands.command(name="restoredata", description="Restore all user data from MongoDB (Administrator only)")
    async def restoredata(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need 'Administrator' permission to use this command!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            result = db.restore_all_data()
            
            if result["success"]:
                embed = discord.Embed(
                    title="✅ Data Restoration Complete",
                    description=f"Successfully restored data for **{result['restored_count']}** users!",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📋 Details", value=result['message'], inline=False)
                embed.add_field(name="🔄 Next Steps", value="All previous XP, cookies, and other data should now be accessible through bot commands.", inline=False)
            else:
                embed = discord.Embed(
                    title="❌ Data Restoration Failed",
                    description=f"Error: {result['message']}",
                    color=0xff0000
                )
            
            embed.set_footer(text=f"{FOOTER_TXT} • Data Restoration")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error restoring data: {str(e)}", ephemeral=True)

    @app_commands.command(name="syncuser", description="Sync specific user's data from MongoDB")
    @app_commands.describe(user="User to sync data for")
    async def syncuser(self, interaction: discord.Interaction, user: discord.Member):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Sync user data
            success = db.sync_user_data(user.id)
            
            if success:
                # Get updated user data
                user_data = db.get_user_data(user.id)
                
                embed = discord.Embed(
                    title="🔄 User Data Synced",
                    description=f"Successfully synced data for {user.mention}",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="📊 Current Data",
                    value=f"**XP:** {user_data.get('xp', 0):,}\n**Cookies:** {user_data.get('cookies', 0):,}\n**Coins:** {user_data.get('coins', 0):,}\n**Daily Streak:** {user_data.get('daily_streak', 0)}",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="❌ Sync Failed",
                    description=f"Failed to sync data for {user.mention}",
                    color=0xff0000
                )
            
            embed.set_footer(text=f"{FOOTER_TXT} • User Data Sync")
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Error syncing user: {str(e)}", ephemeral=True)

    @app_commands.command(name="userdata", description="View raw user data from MongoDB")
    @app_commands.describe(user="User to check data for")
    async def userdata(self, interaction: discord.Interaction, user: discord.Member):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            user_data = db.get_user_data(user.id)
            
            if not user_data:
                await interaction.response.send_message(f"❌ No data found for {user.mention} in MongoDB!", ephemeral=True)
                return

            embed = discord.Embed(
                title="🗄️ Raw User Data",
                description=f"MongoDB data for {user.mention}",
                color=0x7289da,
                timestamp=datetime.now()
            )
            
            # Main stats
            embed.add_field(
                name="📊 Core Stats",
                value=f"**XP:** {user_data.get('xp', 0):,}\n**Level:** {user_data.get('level', 'Not calculated')}\n**Cookies:** {user_data.get('cookies', 0):,}\n**Coins:** {user_data.get('coins', 0):,}",
                inline=True
            )
            
            # Time data
            embed.add_field(
                name="⏰ Timestamps",
                value=f"**Last XP:** <t:{int(user_data.get('last_xp_time', 0))}:R>\n**Last Work:** <t:{int(user_data.get('last_work', 0))}:R>\n**Last Daily:** <t:{int(user_data.get('last_daily', 0))}:R>",
                inline=True
            )
            
            # Daily streak
            embed.add_field(
                name="🔥 Daily System",
                value=f"**Streak:** {user_data.get('daily_streak', 0)} days",
                inline=True
            )
            
            # Temporary items
            temp_roles = user_data.get('temporary_roles', [])
            temp_purchases = user_data.get('temporary_purchases', [])
            
            if temp_roles or temp_purchases:
                temp_info = []
                if temp_roles:
                    temp_info.append(f"**Roles:** {len(temp_roles)} active")
                if temp_purchases:
                    temp_info.append(f"**Purchases:** {len(temp_purchases)} active")
                
                embed.add_field(
                    name="⚡ Temporary Items",
                    value="\n".join(temp_info),
                    inline=True
                )
            
            embed.set_footer(text=f"{FOOTER_TXT} • MongoDB Raw Data")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting user data: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
