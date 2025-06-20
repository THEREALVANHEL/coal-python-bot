import discord
from discord.ext import commands
from discord import option, Permissions
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Define the roles that can use these commands
        self.moderator_roles = ["Moderator 🚨🚓", "🚨 Lead moderator"]

    # --- Permission Check ---
    def check_is_moderator(self, interaction: discord.Interaction):
        """Checks if the user has a moderator role or is an admin."""
        author = interaction.user
        if isinstance(author, discord.Member):
            # Always allow administrators
            if author.guild_permissions.administrator:
                return True
            # Check if they have any of the specified moderator roles
            if any(role.name in self.moderator_roles for role in author.roles):
                return True
        return False

    # --- Commands ---

    @commands.slash_command(name="warn", description="[Moderator] Warn a user.", guild_ids=[1370009417726169250])
    @option("user", description="The user to warn.", type=discord.Member, required=True)
    @option("reason", description="The reason for the warning.", type=str, required=False)
    async def warn(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str = "No reason provided."):
        if not self.check_is_moderator(ctx.interaction):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return

        if user.bot:
            await ctx.respond("You can't warn a bot!", ephemeral=True)
            return
            
        if user.id == ctx.author.id:
            await ctx.respond("You can't warn yourself!", ephemeral=True)
            return

        db.add_warning(user_id=user.id, moderator_id=ctx.author.id, reason=reason)
        
        embed = discord.Embed(
            title="User Warned",
            description=f"**{user.mention}** has been warned by **{ctx.author.mention}**.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await ctx.respond(embed=embed)
        
        try:
            # Also send a DM to the user
            dm_embed = discord.Embed(
                title="You have been warned",
                description=f"You have received a warning in **{ctx.guild.name}**.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.set_footer(text=f"Warned by: {ctx.author.display_name}")
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            # This happens if the user has DMs disabled or has blocked the bot
            await ctx.followup.send("Could not send a DM to the user.", ephemeral=True)


    @commands.slash_command(name="warnlist", description="[Moderator] Show all warnings for a user.", guild_ids=[1370009417726169250])
    @option("user", description="The user whose warnings you want to see.", type=discord.Member, required=True)
    async def warnlist(self, ctx: discord.ApplicationContext, user: discord.Member):
        if not self.check_is_moderator(ctx.interaction):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return

        warnings = db.get_warnings(user.id)

        if not warnings:
            await ctx.respond(f"**{user.display_name}** has no warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Warnings for {user.display_name}",
            color=discord.Color.dark_orange()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for warning in warnings:
            moderator = ctx.guild.get_member(warning['moderator_id'])
            mod_name = moderator.display_name if moderator else "Unknown Moderator"
            reason = warning['reason']
            timestamp = warning['timestamp'].strftime("%Y-%m-%d %H:%M:%S UTC")
            embed.add_field(
                name=f"Warning on {timestamp}",
                value=f"**Reason:** {reason}\n**Moderator:** {mod_name}",
                inline=False
            )
        
        await ctx.respond(embed=embed, ephemeral=True)


    @commands.slash_command(name="removewarnlist", description="[Moderator] Remove all warnings for a user.", guild_ids=[1370009417726169250])
    @option("user", description="The user whose warnings you want to remove.", type=discord.Member, required=True)
    async def removewarnlist(self, ctx: discord.ApplicationContext, user: discord.Member):
        if not self.check_is_moderator(ctx.interaction):
            await ctx.respond("You don't have permission to use this command.", ephemeral=True)
            return

        warnings = db.get_warnings(user.id)
        if not warnings:
            await ctx.respond(f"**{user.display_name}** has no warnings to remove.", ephemeral=True)
            return
            
        # Add a confirmation view
        view = discord.ui.View()
        button = discord.ui.Button(label=f"Confirm Clear Warnings for {user.display_name}", style=discord.ButtonStyle.danger)
        
        async def button_callback(interaction: discord.Interaction):
            # Double check permissions
            if not self.check_is_moderator(interaction):
                await interaction.response.send_message("You don't have permission to do this.", ephemeral=True)
                return
            
            # Check if the interactor is the original command user
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("This confirmation is not for you.", ephemeral=True)
                return

            db.clear_warnings(user.id)
            await interaction.response.send_message(f"All warnings for **{user.display_name}** have been cleared.", ephemeral=True)
            
            # Disable the button after use
            button.disabled = True
            await ctx.edit(view=view)

        button.callback = button_callback
        view.add_item(button)
        
        await ctx.respond(f"Are you sure you want to clear all **{len(warnings)}** warnings for **{user.display_name}**?", view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(Moderation(bot))
