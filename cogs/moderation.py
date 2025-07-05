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

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
