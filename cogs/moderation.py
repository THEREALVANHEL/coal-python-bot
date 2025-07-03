import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
from datetime import datetime

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250          # replace with your guild ID if different
guild_obj = discord.Object(id=GUILD_ID)

# ─────────────────────────────────────────────────────────────
# Permission check
# ─────────────────────────────────────────────────────────────
def is_moderator():
    """Allow administrators, or members with specific mod roles."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True

        moderator_roles = ["Moderator 🚨🚓", "🚨 Lead moderator"]
        if any(role.name in moderator_roles for role in interaction.user.roles):
            return True

        await interaction.response.send_message(
            "You don't have the required role to use this command.",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

# ─────────────────────────────────────────────────────────────
class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------------------------------------------------
    # /modclear
    # ---------------------------------------------------------
    @app_commands.command(
        name="modclear",
        description="[Moderator] Delete a number of recent messages (1-100)."
    )
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def modclear(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100]
    ):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(
            f"✅ Successfully deleted **{len(deleted)}** messages.",
            ephemeral=True
        )

        # Optional: log to modlog channel
        modlog_id = db.get_channel(interaction.guild.id, "modlog")
        if modlog_id:
            channel = interaction.guild.get_channel(modlog_id)
            if channel:
                embed = discord.Embed(
                    title="🧹 Messages Cleared",
                    description=(
                        f"**{len(deleted)}** messages deleted in "
                        f"{interaction.channel.mention}"
                    ),
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Moderator: {interaction.user.display_name}")
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    print("[modclear] Cannot write to modlog channel.")

    # ---------------------------------------------------------
    # /warn
    # ---------------------------------------------------------
    @app_commands.command(
        name="warn",
        description="[Moderator] Issue a warning to a user."
    )
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(
        user="User to warn",
        reason="Reason for the warning"
    )
    async def warn(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "No reason provided."
    ):
        if user.bot or user == interaction.user:
            await interaction.response.send_message(
                "⚠️ Invalid target user.", ephemeral=True
            )
            return

        db.add_warning(user_id=user.id, moderator_id=interaction.user.id, reason=reason)

        # DM the user (best effort)
        dm_sent = False
        try:
            dm = discord.Embed(
                title="🚨 You Have Been Warned",
                description=(
                    f"You received a warning in **{interaction.guild.name}**."
                ),
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            dm.add_field(name="Reason", value=reason, inline=False)
            dm.set_footer(text="Please review the server rules.")
            await user.send(embed=dm)
            dm_sent = True
        except discord.Forbidden:
            pass

        # Public confirmation
        embed = discord.Embed(
            title="⚠️ User Warned",
            description=f"{user.mention} has been warned.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Moderator: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

        if not dm_sent:
            await interaction.followup.send(
                "(Could not DM the user.)",
                ephemeral=True
            )

    # ---------------------------------------------------------
    # /warnlist
    # ---------------------------------------------------------
    @app_commands.command(
        name="warnlist",
        description="[Moderator] Show a user’s warnings."
    )
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(user="User to view warnings for")
    async def warnlist(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        warnings = db.get_warnings(user.id)
        if not warnings:
            await interaction.response.send_message(
                f"**{user.display_name}** has no warnings.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"Warnings for {user.display_name}",
            color=discord.Color.dark_orange()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for warn in warnings:
            mod = interaction.guild.get_member(warn["moderator_id"])
            moderator = mod.display_name if mod else "Unknown"
            ts = warn["timestamp"].strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(
                name=f"📅 {ts}",
                value=f"**Reason:** {warn['reason']}\n**Moderator:** {moderator}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    # ---------------------------------------------------------
    # /removewarnlist
    # ---------------------------------------------------------
    @app_commands.command(
        name="removewarnlist",
        description="[Moderator] Clear all warnings for a user."
    )
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(user="User whose warnings to clear")
    async def removewarnlist(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        warnings = db.get_warnings(user.id)
        if not warnings:
            await interaction.response.send_message(
                f"**{user.display_name}** has no warnings.",
                ephemeral=True
            )
            return

        # Confirm via buttons
        view = discord.ui.View(timeout=60)

        confirm_btn = discord.ui.Button(
            label="Confirm",
            style=discord.ButtonStyle.danger
        )
        cancel_btn = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary
        )

        async def confirm(btn_inter: discord.Interaction):
            if btn_inter.user != interaction.user:
                await btn_inter.response.send_message(
                    "This confirmation is not for you.",
                    ephemeral=True
                )
                return
            db.clear_warnings(user.id)
            await btn_inter.response.edit_message(
                content=f"✅ Cleared all warnings for **{user.display_name}**.",
                view=None
            )

        async def cancel(btn_inter: discord.Interaction):
            await btn_inter.response.edit_message(
                content="Cancelled.",
                view=None
            )

        confirm_btn.callback = confirm
        cancel_btn.callback = cancel
        view.add_item(confirm_btn)
        view.add_item(cancel_btn)

        await interaction.response.send_message(
            f"Are you sure you want to clear **{len(warnings)}** warnings for **{user.display_name}**?",
            view=view,
            ephemeral=True
        )

# ─────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot), guilds=[guild_obj])
