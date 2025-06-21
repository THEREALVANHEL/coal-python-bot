import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# --- Custom Check ---
def is_moderator():
    """Custom check to verify if the user is a moderator or admin."""
    async def predicate(interaction: discord.Interaction) -> bool:
        # Allow administrators to bypass role check
        if interaction.user.guild_permissions.administrator:
            return True
        
        # You should ideally store these roles in a database per guild
        moderator_roles = ["Moderator 🚨🚓", "🚨 Lead moderator"]
        
        # Check if the user has any of the specified moderator roles
        has_role = any(role.name in moderator_roles for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("You don't have the required role to use this command.", ephemeral=True)
        return has_role
    return app_commands.check(predicate)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Commands ---

    @app_commands.command(name="warn", description="[Moderator] Warn a user.")
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(user="The user to warn.", reason="The reason for the warning.")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided."):
        if user.bot:
            await interaction.response.send_message("You can't warn a bot!", ephemeral=True)
            return
            
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't warn yourself!", ephemeral=True)
            return

        db.add_warning(user_id=user.id, moderator_id=interaction.user.id, reason=reason)
        
        # First, try to send DM
        dm_sent = False
        try:
            dm_embed = discord.Embed(
                title="🚨 You Have Been Warned",
                description=f"You received a warning in **{interaction.guild.name}**.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.set_footer(text=f"Please respect the server rules.")
            await user.send(embed=dm_embed)
            dm_sent = True
        except discord.Forbidden:
            # User has DMs closed or blocked the bot
            pass

        # Now, send the public confirmation
        embed = discord.Embed(
            title="⚠️ User Warned",
            description=f"**{user.mention}** has been officially warned.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Moderator: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
        if not dm_sent:
            await interaction.followup.send("(Could not send a DM to the user. Their DMs may be closed.)", ephemeral=True)


    @app_commands.command(name="warnlist", description="[Moderator] Show all warnings for a user.")
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(user="The user whose warnings you want to see.")
    async def warnlist(self, interaction: discord.Interaction, user: discord.Member):
        warnings = db.get_warnings(user.id)

        if not warnings:
            await interaction.response.send_message(f"**{user.display_name}** has no warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Warnings for {user.display_name}",
            color=discord.Color.dark_orange()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for warning in warnings:
            moderator = interaction.guild.get_member(warning['moderator_id'])
            mod_name = moderator.display_name if moderator else "Unknown Moderator"
            reason = warning['reason']
            timestamp = warning['timestamp'].strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(
                name=f"🗓️ Warning on {timestamp}",
                value=f"**Reason:** {reason}\n**Moderator:** {mod_name}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="removewarnlist", description="[Moderator] Remove all warnings for a user.")
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(user="The user whose warnings you want to remove.")
    async def removewarnlist(self, interaction: discord.Interaction, user: discord.Member):
        warnings = db.get_warnings(user.id)
        if not warnings:
            await interaction.response.send_message(f"**{user.display_name}** has no warnings to remove.", ephemeral=True)
            return
            
        # Add a confirmation view
        view = discord.ui.View(timeout=60) # Add a timeout
        
        # This check should be inside the button callback as well
        confirm_button = discord.ui.Button(label=f"Confirm Clear Warnings", style=discord.ButtonStyle.danger)
        
        async def confirm_callback(callback_interaction: discord.Interaction):
            # Re-check permissions for the person clicking the button
            if not callback_interaction.user.guild_permissions.administrator:
                 # Simple check, can be expanded to full mod check
                is_mod = any(role.name in ["Moderator 🚨🚓", "🚨 Lead moderator"] for role in callback_interaction.user.roles)
                if not is_mod:
                    await callback_interaction.response.send_message("You don't have permission to confirm this.", ephemeral=True)
                    return

            if callback_interaction.user.id != interaction.user.id:
                await callback_interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
                return

            db.clear_warnings(user.id)
            await callback_interaction.response.edit_message(content=f"✅ All warnings for **{user.display_name}** have been cleared.", view=None)

        confirm_button.callback = confirm_callback
        
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        async def cancel_callback(callback_interaction: discord.Interaction):
             await callback_interaction.response.edit_message(content="Cancelled.", view=None)

        cancel_button.callback = cancel_callback
        
        view.add_item(confirm_button)
        view.add_item(cancel_button)
        
        await interaction.response.send_message(f"Are you sure you want to clear all **{len(warnings)}** warnings for **{user.display_name}**?", view=view, ephemeral=True)

    @app_commands.command(name="announce", description="[Moderator] Create and send a server announcement.")
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(
        channel="The channel to send the announcement to.",
        title="The title of the announcement embed.",
        message="The main content of the announcement."
    )
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str):
        embed = discord.Embed(
            title=f"📢 {title}",
            description=message,
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Announcement from {interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"Announced by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Announcement sent successfully to {channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
