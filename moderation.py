import discord
from discord.ext import commands
from discord import option
import sys
import os
from datetime import datetime

# Add parent directory to path for database import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderator_roles = ["Moderator 🚨🚓", "🚨 Lead moderator"]

    # --- Permissions ---
    def check_is_moderator(self, interaction: discord.Interaction) -> bool:
        """Check if the user has a mod role or admin."""
        user = interaction.user
        if isinstance(user, discord.Member):
            if user.guild_permissions.administrator:
                return True
            return any(role.name in self.moderator_roles for role in user.roles)
        return False

    # --- Clear Command ---
    @commands.slash_command(name="modclear", description="[Moderator] Clears a number of messages.", guild_ids=[1370009417726169250])
    @option("amount", description="Number of messages to clear", type=int, required=True)
    async def modclear(self, ctx: discord.ApplicationContext, amount: int):
        if not self.check_is_moderator(ctx.interaction):
            return await ctx.respond("You don't have permission to use this command.", ephemeral=True)

        if amount <= 0:
            return await ctx.respond("Please specify a positive number of messages.", ephemeral=True)

        try:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.respond(f"🧹 Cleared **{len(deleted)}** messages.", ephemeral=True)
        except discord.Forbidden:
            await ctx.respond("I don't have permission to manage messages.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.respond(f"An error occurred: {e}", ephemeral=True)

    # --- Warn Command ---
    @commands.slash_command(name="warn", description="[Moderator] Warn a user.", guild_ids=[1370009417726169250])
    @option("user", description="The user to warn", type=discord.Member, required=True)
    @option("reason", description="Reason for the warning", type=str, required=False)
    async def warn(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str = "No reason provided."):
        if not self.check_is_moderator(ctx.interaction):
            return await ctx.respond("You don't have permission.", ephemeral=True)
        if user.bot:
            return await ctx.respond("You can't warn a bot.", ephemeral=True)
        if user.id == ctx.author.id:
            return await ctx.respond("You can't warn yourself.", ephemeral=True)

        db.add_warning(user.id, ctx.author.id, reason)

        embed = discord.Embed(
            title="🛡️ User Warned",
            description=f"**{user.mention}** was warned by **{ctx.author.mention}**.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        await ctx.respond(embed=embed)

        try:
            dm_embed = discord.Embed(
                title="🚨 You Have Been Warned",
                description=f"You were warned in **{ctx.guild.name}**.",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.set_footer(text=f"Warned by: {ctx.author.display_name}")
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            await ctx.followup.send("Couldn't send a DM to the user.", ephemeral=True)

    # --- Warnlist Command ---
    @commands.slash_command(name="warnlist", description="[Moderator] Show warnings for a user.", guild_ids=[1370009417726169250])
    @option("user", description="User to check", type=discord.Member, required=True)
    async def warnlist(self, ctx: discord.ApplicationContext, user: discord.Member):
        if not self.check_is_moderator(ctx.interaction):
            return await ctx.respond("You don't have permission.", ephemeral=True)

        warnings = db.get_warnings(user.id)
        if not warnings:
            return await ctx.respond(f"**{user.display_name}** has no warnings.", ephemeral=True)

        embed = discord.Embed(
            title=f"📜 Warnings for {user.display_name}",
            color=discord.Color.dark_orange()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for warning in warnings:
            moderator = ctx.guild.get_member(warning['moderator_id'])
            mod_name = moderator.display_name if moderator else "Unknown"
            timestamp = warning['timestamp'].strftime("%Y-%m-%d %H:%M:%S UTC")
            embed.add_field(
                name=f"Warning on {timestamp}",
                value=f"**Reason:** {warning['reason']}\n**Moderator:** {mod_name}",
                inline=False
            )

        embed.set_footer(text="BLECKOPS ON TOP", icon_url=self.bot.user.display_avatar.url)
        await ctx.respond(embed=embed, ephemeral=True)

    # --- Remove Warns Command ---
    @commands.slash_command(name="removewarnlist", description="[Moderator] Clear warnings for a user.", guild_ids=[1370009417726169250])
    @option("user", description="User to clear warnings", type=discord.Member, required=True)
    async def removewarnlist(self, ctx: discord.ApplicationContext, user: discord.Member):
        if not self.check_is_moderator(ctx.interaction):
            return await ctx.respond("You don't have permission.", ephemeral=True)

        warnings = db.get_warnings(user.id)
        if not warnings:
            return await ctx.respond(f"**{user.display_name}** has no warnings.", ephemeral=True)

        # Confirmation view
        view = discord.ui.View()
        button = discord.ui.Button(label=f"Confirm Clear Warnings for {user.display_name}", style=discord.ButtonStyle.danger)

        async def button_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("This button isn't for you.", ephemeral=True)
            if not self.check_is_moderator(interaction):
                return await interaction.response.send_message("You don't have permission.", ephemeral=True)

            db.clear_warnings(user.id)
            await interaction.response.send_message(f"✅ Cleared all warnings for **{user.display_name}**.", ephemeral=True)

            button.disabled = True
            await ctx.edit(view=view)

        button.callback = button_callback
        view.add_item(button)

        await ctx.respond(f"⚠️ Are you sure you want to clear **{len(warnings)}** warning(s) for **{user.display_name}**?", view=view, ephemeral=True)

# --- Setup ---
def setup(bot):
    bot.add_cog(Moderation(bot))
