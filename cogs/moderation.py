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

    # ADMIN-ONLY DATABASE MANAGEMENT COMMANDS
    # =====================================

    @app_commands.command(name="dbstats", description="Get comprehensive database statistics (ADMIN ONLY)")
    @app_commands.default_permissions(administrator=True)
    async def dbstats(self, interaction: discord.Interaction):
        try:
            # Get basic stats
            stats = db.get_database_stats()
            health = db.get_database_health()
            server_analytics = db.get_advanced_server_analytics(interaction.guild.id)
            
            embed = discord.Embed(
                title="📊 Database Statistics",
                color=0x5865f2,
                timestamp=datetime.now()
            )
            
            # Basic stats
            if stats['success']:
                embed.add_field(
                    name="📈 User Statistics", 
                    value=f"**Total Users:** {stats.get('total_users', 0):,}\n**Total XP:** {stats.get('total_xp', 0):,}\n**Total Cookies:** {stats.get('total_cookies', 0):,}\n**Total Coins:** {stats.get('total_coins', 0):,}",
                    inline=False
                )
            
            # Health metrics
            if health and 'collections' in health:
                collections_info = "\n".join([
                    f"**{name.title()}:** {info.get('document_count', 'Error')} docs"
                    for name, info in health['collections'].items()
                    if isinstance(info, dict) and 'document_count' in info
                ])
                embed.add_field(name="🗄️ Collections", value=collections_info, inline=True)
            
            # Server analytics
            if server_analytics:
                embed.add_field(
                    name="📊 Server Analytics",
                    value=f"**Active (30d):** {server_analytics.get('active_users_30d', 0)}\n**Avg XP:** {server_analytics.get('server_totals', {}).get('avg_xp', 0):.0f}\n**Avg Coins:** {server_analytics.get('server_totals', {}).get('avg_coins', 0):.0f}",
                    inline=True
                )
            
            embed.set_footer(text="Admin-only command • Data is live and validated")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting database stats: {str(e)}", ephemeral=True)

    @app_commands.command(name="dbmaintenance", description="Perform comprehensive database maintenance (ADMIN ONLY)")
    @app_commands.default_permissions(administrator=True)
    async def db_maintenance(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            maintenance_results = []
            
            # Remove deprecated warning system
            warning_removal = db.remove_deprecated_warning_system()
            if warning_removal['success']:
                maintenance_results.append(f"✅ Removed warnings from {warning_removal['users_updated']} users")
            else:
                maintenance_results.append(f"❌ Warning removal failed: {warning_removal.get('error', 'Unknown error')}")
            
            # Optimize database
            optimization = db.optimize_database_live()
            if optimization['success']:
                maintenance_results.append(f"✅ Created {len(optimization['indexes_created'])} database indexes")
            else:
                maintenance_results.append(f"❌ Optimization failed: {optimization.get('error', 'Unknown error')}")
            
            # Auto-sync user data
            users_synced = 0
            try:
                all_users = db.get_all_users_for_maintenance()[:50]  # Limit for performance
                for user_data in all_users:
                    db.auto_sync_user_data(user_data['user_id'])
                    users_synced += 1
                maintenance_results.append(f"✅ Auto-synced {users_synced} user profiles")
            except Exception as e:
                maintenance_results.append(f"❌ User sync failed: {str(e)}")
            
            embed = discord.Embed(
                title="🔧 Database Maintenance Complete",
                description="\n".join(maintenance_results),
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_footer(text="Maintenance performed by admin")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Maintenance error: {str(e)}", ephemeral=True)

    @app_commands.command(name="datarecovery", description="Recover lost user data (ADMIN ONLY)")
    @app_commands.describe(user="User to recover data for")
    @app_commands.default_permissions(administrator=True)
    async def data_recovery(self, interaction: discord.Interaction, user: discord.Member):
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Get current user data
            current_data = db.get_user_data(user.id)
            
            # Perform auto-sync (which includes recovery)
            recovered_data = db.auto_sync_user_data(user.id)
            
            # Compare and show what was recovered
            recovery_info = []
            
            if current_data.get('xp', 0) != recovered_data.get('xp', 0):
                recovery_info.append(f"XP: {current_data.get('xp', 0)} → {recovered_data.get('xp', 0)}")
            
            if current_data.get('cookies', 0) != recovered_data.get('cookies', 0):
                recovery_info.append(f"Cookies: {current_data.get('cookies', 0)} → {recovered_data.get('cookies', 0)}")
            
            if current_data.get('coins', 0) != recovered_data.get('coins', 0):
                recovery_info.append(f"Coins: {current_data.get('coins', 0)} → {recovered_data.get('coins', 0)}")
            
            embed = discord.Embed(
                title=f"🔄 Data Recovery - {user.display_name}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            if recovery_info:
                embed.description = "**Data Changes:**\n" + "\n".join(recovery_info)
            else:
                embed.description = "✅ No data corruption found. User profile is healthy."
            
            embed.add_field(name="Current Stats", value=f"**XP:** {recovered_data.get('xp', 0):,}\n**Cookies:** {recovered_data.get('cookies', 0):,}\n**Coins:** {recovered_data.get('coins', 0):,}", inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text="Recovery performed by admin")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Recovery error: {str(e)}", ephemeral=True)

    @app_commands.command(name="syncallroles", description="Sync all user roles with current stats (ADMIN ONLY)")
    @app_commands.default_permissions(administrator=True)
    async def sync_all_roles(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            
            synced_count = 0
            error_count = 0
            
            # Get all members
            for member in interaction.guild.members:
                try:
                    # Get user data
                    user_data = db.get_user_data(member.id)
                    xp = user_data.get('xp', 0)
                    cookies = user_data.get('cookies', 0)
                    
                    # Update XP roles
                    from cogs.leveling import Leveling
                    leveling_cog = self.bot.get_cog('Leveling')
                    if leveling_cog:
                        level = leveling_cog.calculate_level_from_xp(xp)
                        await leveling_cog.update_user_roles(member, level)
                    
                    # Update cookie roles
                    from cogs.cookies import Cookies
                    cookies_cog = self.bot.get_cog('Cookies')
                    if cookies_cog:
                        await cookies_cog.update_cookie_roles(member, cookies)
                    
                    synced_count += 1
                    
                except Exception as e:
                    error_count += 1
                    continue
            
            embed = discord.Embed(
                title="🔄 Role Sync Complete",
                description=f"**Successfully synced:** {synced_count} members\n**Errors:** {error_count} members",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_footer(text="Role sync performed by admin")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Role sync error: {str(e)}", ephemeral=True)

    @app_commands.command(name="databasehealth", description="Get detailed database health report (ADMIN ONLY)")
    @app_commands.default_permissions(administrator=True)
    async def database_health(self, interaction: discord.Interaction):
        try:
            health = db.get_database_health()
            
            embed = discord.Embed(
                title="🏥 Database Health Report",
                color=0x5865f2,
                timestamp=datetime.now()
            )
            
            if 'error' in health:
                embed.description = f"❌ **Health Check Failed:** {health['error']}"
                embed.color = 0xff0000
            else:
                # Overall stats
                embed.add_field(
                    name="📊 Overview",
                    value=f"**Total Documents:** {health.get('total_documents', 0):,}\n**Collections:** {len(health.get('collections', {}))}\n**Status:** {'🟢 Healthy' if health.get('total_documents', 0) > 0 else '🟡 Warning'}",
                    inline=False
                )
                
                # Collection details
                collections_info = []
                for name, info in health.get('collections', {}).items():
                    if isinstance(info, dict) and 'document_count' in info:
                        collections_info.append(f"**{name.title()}:** {info['document_count']:,} docs, {len(info.get('indexes', []))} indexes")
                    else:
                        collections_info.append(f"**{name.title()}:** ❌ Error")
                
                if collections_info:
                    embed.add_field(name="🗄️ Collections", value="\n".join(collections_info), inline=False)
                
                # Performance
                perf = health.get('performance', {})
                embed.add_field(
                    name="⚡ Performance",
                    value=f"**Connection:** {perf.get('connection_status', 'Unknown')}\n**Response Time:** {perf.get('avg_response_time', 'N/A')}\n**Last Optimization:** {perf.get('last_optimization', 'N/A')}",
                    inline=False
                )
            
            embed.set_footer(text="Admin-only health report")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Health check error: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
