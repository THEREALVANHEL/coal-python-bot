import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

import google.generativeai as genai

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

    @app_commands.command(name="roleplay", description="Start an AI-powered roleplay session")
    @app_commands.describe(
        scenario="The roleplay scenario you want to start",
        character="Your character in the roleplay (optional)",
        setting="The setting/world for the roleplay (optional)"
    )
    async def roleplay(self, interaction: discord.Interaction, scenario: str, character: str = None, setting: str = None):
        """AI-powered roleplay command using Gemini"""
        genai_api_key = os.getenv("GEMINI_API_KEY")
        if not genai_api_key:
            await interaction.response.send_message("❌ AI service not available!", ephemeral=True)
            return

        try:
            genai.configure(api_key=genai_api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            # Build the roleplay prompt
            prompt_parts = [
                f"You are an expert AI Game Master running a roleplay session. ",
                f"Scenario: {scenario}",
            ]
            
            if setting:
                prompt_parts.append(f"Setting: {setting}")
            
            if character:
                prompt_parts.append(f"The player's character: {character}")
            else:
                prompt_parts.append("The player hasn't specified their character yet, so help them create one.")
            
            prompt_parts.extend([
                "Instructions:",
                "- Create an immersive, engaging roleplay experience",
                "- Respond in character as the game master",
                "- Set the scene vividly with sensory details",
                "- Present interesting choices and challenges",
                "- Keep responses engaging but not too long (under 1500 characters)",
                "- Always end with a question or prompt for the player to respond to",
                "- Be creative and adaptive to player choices",
                "- Keep content appropriate for Discord servers",
                "",
                "Begin the roleplay session now:"
            ])
            
            full_prompt = "\n".join(prompt_parts)
            
            await interaction.response.defer()
            
            response = model.generate_content(full_prompt)
            
            embed = discord.Embed(
                title="🎭 Roleplay Session",
                description=response.text[:2000],
                color=0x9932cc,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="📖 Scenario", value=scenario[:100] + ("..." if len(scenario) > 100 else ""), inline=True)
            if character:
                embed.add_field(name="👤 Character", value=character[:100] + ("..." if len(character) > 100 else ""), inline=True)
            if setting:
                embed.add_field(name="🌍 Setting", value=setting[:100] + ("..." if len(setting) > 100 else ""), inline=True)
            
            embed.set_author(name=f"GM: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="🎲 AI-Powered Roleplay • Use this as inspiration for your RP!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating roleplay: {str(e)}", ephemeral=True)

    @app_commands.command(name="dbmaintenance", description="Perform database maintenance and recovery (Admin only)")
    async def dbmaintenance(self, interaction: discord.Interaction):
        """Comprehensive database maintenance for admins"""
        # Check permissions
        user_roles = [role.name for role in interaction.user.roles]
        admin_roles = ["🦥 Overseer", "Forgotten one"]
        
        if not any(role in admin_roles for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command! Only Overseers and Forgotten ones can perform maintenance.", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            # Perform comprehensive maintenance
            result = db.maintenance_cleanup()
            
            if result["success"]:
                embed = discord.Embed(
                    title="🔧 Database Maintenance Complete",
                    description="Comprehensive database maintenance has been performed successfully!",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📊 Users Recovered", value=f"{result['recovered_users']}", inline=True)
                embed.add_field(name="🧹 Entries Cleaned", value=f"{result['cleaned_entries']}", inline=True)
                embed.add_field(name="⚡ Database Optimized", value="✅ Yes" if result['optimized'] else "❌ No", inline=True)
                embed.add_field(name="📋 Details", value=result['message'], inline=False)
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text="Database maintenance performed successfully")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Maintenance failed: {result['message']}", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error during maintenance: {str(e)}", ephemeral=True)

    @app_commands.command(name="datarecovery", description="Recover lost user data (Admin only)")
    async def datarecovery(self, interaction: discord.Interaction):
        """Recover lost user data"""
        # Check permissions
        user_roles = [role.name for role in interaction.user.roles]
        admin_roles = ["🦥 Overseer", "Forgotten one"]
        
        if not any(role in admin_roles for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            result = db.recover_lost_data()
            
            if result["success"]:
                embed = discord.Embed(
                    title="� Data Recovery Complete",
                    description=f"Successfully recovered data for **{result['recovered_count']}** users!",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📊 Recovery Details", value=result['message'], inline=False)
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Recovery failed: {result['message']}", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error during recovery: {str(e)}", ephemeral=True)

    @app_commands.command(name="dbstats", description="View comprehensive database statistics (Admin only)")
    async def dbstats(self, interaction: discord.Interaction):
        """View detailed database statistics"""
        # Check permissions
        user_roles = [role.name for role in interaction.user.roles]
        admin_roles = ["🦥 Overseer", "Forgotten one", "🚨 Lead moderator"]
        
        if not any(role in admin_roles for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            stats = db.get_database_stats()
            
            if stats["success"]:
                embed = discord.Embed(
                    title="📊 Database Statistics",
                    color=0x7289da,
                    timestamp=datetime.now()
                )
                
                # User statistics
                embed.add_field(name="👥 Total Users", value=f"{stats['total_users']:,}", inline=True)
                embed.add_field(name="⭐ Users with XP", value=f"{stats['users_with_xp']:,}", inline=True)
                embed.add_field(name="🍪 Users with Cookies", value=f"{stats['users_with_cookies']:,}", inline=True)
                embed.add_field(name="🪙 Users with Coins", value=f"{stats['users_with_coins']:,}", inline=True)
                
                # Total statistics
                embed.add_field(name="📈 Total XP", value=f"{stats['total_xp']:,}", inline=True)
                embed.add_field(name="🍪 Total Cookies", value=f"{stats['total_cookies']:,}", inline=True)
                
                # Calculate averages
                avg_xp = stats['total_xp'] // max(1, stats['users_with_xp'])
                avg_cookies = stats['total_cookies'] // max(1, stats['users_with_cookies'])
                
                embed.add_field(name="📊 Average XP", value=f"{avg_xp:,}", inline=True)
                embed.add_field(name="📊 Average Cookies", value=f"{avg_cookies:,}", inline=True)
                
                embed.set_footer(text="Database statistics • Live data")
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"❌ Error getting stats: {stats['message']}", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting database stats: {str(e)}", ephemeral=True)

    @app_commands.command(name="syncallroles", description="Sync all user roles based on current XP and cookies (Admin only)")
    async def syncallroles(self, interaction: discord.Interaction):
        """Sync all user roles in the server"""
        # Check permissions
        user_roles = [role.name for role in interaction.user.roles]
        admin_roles = ["🦥 Overseer", "Forgotten one"]
        
        if not any(role in admin_roles for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        await interaction.response.defer()
        
        try:
            # Get leveling cog for role update functions
            leveling_cog = self.bot.get_cog('Leveling')
            if not leveling_cog:
                await interaction.followup.send("❌ Leveling system not available!", ephemeral=True)
                return

            updated_members = 0
            errors = 0
            
            for member in interaction.guild.members:
                if member.bot:
                    continue
                    
                try:
                    # Get user data
                    user_data = db.get_live_user_stats(member.id)
                    level = user_data.get('level', 0)
                    cookies = user_data.get('cookies', 0)
                    
                    # Update both XP and cookie roles
                    await leveling_cog.update_xp_roles(member, level)
                    await leveling_cog.update_cookie_roles(member, cookies)
                    
                    updated_members += 1
                except Exception as e:
                    print(f"Error updating roles for {member}: {e}")
                    errors += 1
            
            embed = discord.Embed(
                title="🔄 Role Sync Complete",
                description=f"Successfully synchronized roles for **{updated_members}** members!",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="✅ Updated", value=f"{updated_members} members", inline=True)
            embed.add_field(name="❌ Errors", value=f"{errors} errors", inline=True)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="All roles synchronized with current XP and cookie levels")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error syncing roles: {str(e)}", ephemeral=True)

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
