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

    @app_commands.command(name="checkwarnlist", description="📋 Check warnings for a user")
    @app_commands.describe(user="User to check warnings for")
    async def check_warn_list(self, interaction: discord.Interaction, user: discord.Member):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            warnings = db.get_user_warnings(user.id)
            
            embed = discord.Embed(
                title="⚠️ Warning List",
                description=f"**User:** {user.mention}\n**Total Warnings:** {len(warnings)}",
                color=0xff9900 if warnings else 0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
            if warnings:
                warning_text = []
                for i, warning in enumerate(warnings[-10:], 1):  # Show last 10 warnings
                    timestamp = datetime.fromtimestamp(warning.get('timestamp', 0))
                    moderator_id = warning.get('moderator_id', 'Unknown')
                    reason = warning.get('reason', 'No reason provided')
                    
                    try:
                        moderator = self.bot.get_user(moderator_id)
                        mod_name = moderator.display_name if moderator else f"Unknown ({moderator_id})"
                    except:
                        mod_name = f"Unknown ({moderator_id})"
                    
                    warning_text.append(f"**{i}.** {reason}\n*By {mod_name} on {timestamp.strftime('%Y-%m-%d %H:%M')}*")
                
                embed.add_field(
                    name="📝 Recent Warnings",
                    value="\n\n".join(warning_text),
                    inline=False
                )
                
                if len(warnings) > 10:
                    embed.set_footer(text=f"Showing 10 most recent warnings out of {len(warnings)} total")
                else:
                    embed.set_footer(text=FOOTER_TXT)
            else:
                embed.add_field(
                    name="✅ Clean Record",
                    value="This user has no warnings on record.",
                    inline=False
                )
                embed.set_footer(text=FOOTER_TXT)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving warnings: {str(e)}", ephemeral=True)

    @app_commands.command(name="removewarnlist", description="🗑️ Remove specific warning or clear all warnings for a user")
    @app_commands.describe(
        user="User to remove warnings from",
        warning_index="Warning number to remove (leave empty to clear all)",
        reason="Reason for removing warning(s)"
    )
    async def remove_warn_list(self, interaction: discord.Interaction, user: discord.Member, warning_index: int = None, reason: str = "No reason provided"):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            warnings = db.get_user_warnings(user.id)
            
            if not warnings:
                embed = discord.Embed(
                    title="ℹ️ No Warnings",
                    description=f"{user.mention} has no warnings to remove.",
                    color=0x7289da
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if warning_index is None:
                # Remove all warnings
                db.clear_user_warnings(user.id)
                
                embed = discord.Embed(
                    title="🗑️ All Warnings Cleared",
                    description=f"Cleared **{len(warnings)}** warning(s) for {user.mention}",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="� Reason", value=reason, inline=False)
                embed.add_field(name="👮 Moderator", value=interaction.user.mention, inline=True)
                embed.set_footer(text=FOOTER_TXT)
                
                await interaction.response.send_message(embed=embed)
            else:
                # Remove specific warning
                if warning_index < 1 or warning_index > len(warnings):
                    await interaction.response.send_message(f"❌ Invalid warning index! User has {len(warnings)} warning(s). Use `/checkwarnlist` to see warning numbers.", ephemeral=True)
                    return
                
                removed_warning = warnings[warning_index - 1]
                db.remove_specific_warning(user.id, warning_index - 1)
                
                embed = discord.Embed(
                    title="🗑️ Warning Removed",
                    description=f"Removed warning #{warning_index} from {user.mention}",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📝 Removed Warning", value=removed_warning.get('reason', 'No reason'), inline=False)
                embed.add_field(name="� Removal Reason", value=reason, inline=False)
                embed.add_field(name="👮 Moderator", value=interaction.user.mention, inline=True)
                embed.add_field(name="📊 Remaining", value=f"{len(warnings) - 1} warning(s)", inline=True)
                embed.set_footer(text=FOOTER_TXT)
                
                await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing warning(s): {str(e)}", ephemeral=True)

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

    # AI-Powered Roleplay Command
    @app_commands.command(name="roleplay", description="🎭 Generate AI-powered roleplay scenarios using Gemini AI")
    @app_commands.describe(
        scenario="Type of roleplay scenario",
        character="Character or role to play",
        setting="Setting or environment"
    )
    async def roleplay(self, interaction: discord.Interaction, scenario: str, character: str = None, setting: str = None):
        # Check permissions - only admins can use this
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="This command is restricted to administrators only.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Build prompt for Gemini AI
            prompt = f"Create an engaging roleplay scenario for Discord. Scenario: {scenario}"
            if character:
                prompt += f", Character: {character}"
            if setting:
                prompt += f", Setting: {setting}"
            prompt += ". Keep it appropriate for all ages and under 1500 characters. Make it immersive and fun."

            # Call Gemini AI
            import google.generativeai as genai
            
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                await interaction.followup.send("❌ Gemini AI service not configured. Please contact an administrator.", ephemeral=True)
                return
                
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            response = model.generate_content(prompt)
            
            if response.text:
                embed = discord.Embed(
                    title="🎭 AI Roleplay Scenario",
                    description=response.text,
                    color=0x7c3aed,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📝 Scenario", value=scenario, inline=True)
                if character:
                    embed.add_field(name="👤 Character", value=character, inline=True)
                if setting:
                    embed.add_field(name="🏛️ Setting", value=setting, inline=True)
                
                embed.set_author(name=f"Generated for {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text="✨ Powered by Gemini AI • Be creative and have fun!")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Failed to generate roleplay scenario. Please try again with different parameters.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Error generating roleplay: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
