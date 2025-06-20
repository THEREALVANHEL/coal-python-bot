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

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Define the roles that can use these commands
        self.moderator_roles = ["Moderator 🚨🚓", "🚨 Lead moderator"]

    # --- Permission Check ---
    async def check_is_moderator(self, interaction: discord.Interaction):
        """Checks if the user has a moderator role or is an admin."""
        author = interaction.user
        if isinstance(author, discord.Member):
            # Always allow administrators
            if author.guild_permissions.administrator:
                return True
            # Check if they have any of the specified moderator roles
            if any(role.name in self.moderator_roles for role in author.roles):
                return True
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return False

    # --- Commands ---

    @app_commands.command(name="warn", description="[Moderator] Warn a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to warn.", reason="The reason for the warning.")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided."):
        if not await self.check_is_moderator(interaction):
            return

        if user.bot:
            await interaction.response.send_message("You can't warn a bot!", ephemeral=True)
            return
            
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't warn yourself!", ephemeral=True)
            return

        db.add_warning(user_id=user.id, moderator_id=interaction.user.id, reason=reason)
        
        embed = discord.Embed(
            title="⚠️ User Warned",
            description=f"**{user.mention}** has been officially warned.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Moderator: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
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
        except discord.Forbidden:
            await interaction.followup.send("(Could not send a DM to the user. Their DMs may be closed.)", ephemeral=True)


    @app_commands.command(name="warnlist", description="[Moderator] Show all warnings for a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user whose warnings you want to see.")
    async def warnlist(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.check_is_moderator(interaction):
            return

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
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="removewarnlist", description="[Moderator] Remove all warnings for a user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user whose warnings you want to remove.")
    async def removewarnlist(self, interaction: discord.Interaction, user: discord.Member):
        if not await self.check_is_moderator(interaction):
            return

        warnings = db.get_warnings(user.id)
        if not warnings:
            await interaction.response.send_message(f"**{user.display_name}** has no warnings to remove.", ephemeral=True)
            return
            
        # Add a confirmation view
        view = discord.ui.View()
        button = discord.ui.Button(label=f"Confirm Clear Warnings for {user.display_name}", style=discord.ButtonStyle.danger)
        
        async def button_callback(callback_interaction: discord.Interaction):
            if not await self.check_is_moderator(callback_interaction):
                return
            
            if callback_interaction.user.id != interaction.user.id:
                await callback_interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
                return

            db.clear_warnings(user.id)
            await callback_interaction.response.send_message(f"✅ All warnings for **{user.display_name}** have been cleared.", ephemeral=True)
            
            button.disabled = True
            await interaction.edit_original_response(view=view)

        button.callback = button_callback
        view.add_item(button)
        
        await interaction.response.send_message(f"Are you sure you want to clear all **{len(warnings)}** warnings for **{user.display_name}**?", view=view, ephemeral=True)

    @app_commands.command(name="announce", description="[Moderator] Create and send a server announcement.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(
        channel="The channel to send the announcement to.",
        title="The title of the announcement embed.",
        message="The main content of the announcement."
    )
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str):
        if not await self.check_is_moderator(interaction):
            return

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
