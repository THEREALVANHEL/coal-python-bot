# cogs/moderation.py
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os, sys

# ── Local import --------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# ── Config --------------------------------------------------------------------
GUILD_ID  = 1370009417726169250          # replace if your guild ID differs
guild_obj = discord.Object(id=GUILD_ID)

MODERATOR_ROLES = ["Moderator 🚨🚓", "🚨 Lead moderator"]   # custom mod roles
FOOTER_TXT      = "VANHELISMYSENSEI ON TOP"

# ── Permission check decorator ------------------------------------------------
def is_moderator():
    async def predicate(inter: discord.Interaction) -> bool:
        if inter.user.guild_permissions.administrator:
            return True
        if any(r.name in MODERATOR_ROLES for r in inter.user.roles):
            return True
        await inter.response.send_message(
            "You don’t have the required role to use this command.",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

# ── Cog -----------------------------------------------------------------------
class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------------------------------------------------------
    # /modclear
    # -------------------------------------------------------------------------
    @app_commands.command(
        name        ="modclear",
        description ="[Moderator] Delete a number of recent messages."
    )
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def modclear(
        self,
        inter : discord.Interaction,
        amount: app_commands.Range[int, 1, 100]
    ):
        await inter.response.defer(ephemeral=True)

        deleted = await inter.channel.purge(limit=amount)
        await inter.followup.send(
            f"🧹 Cleared **{len(deleted)}** messages.",
            ephemeral=True
        )

        # optional mod-log
        modlog_id = db.get_channel(inter.guild.id, "modlog")
        if modlog_id:
            ch = inter.guild.get_channel(modlog_id)
            if ch:
                embed = discord.Embed(
                    title       ="🧹 Messages Cleared",
                    description =f"**{len(deleted)}** messages removed in {inter.channel.mention}",
                    color       =discord.Color.orange(),
                    timestamp   =datetime.utcnow()
                )
                embed.set_footer(text=f"Moderator: {inter.user.display_name}")
                try:    await ch.send(embed=embed)
                except discord.Forbidden: pass

    # -------------------------------------------------------------------------
    # /warn
    # -------------------------------------------------------------------------
    @app_commands.command(
        name        ="warn",
        description ="[Moderator] Issue a warning to a user."
    )
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(
        user   ="User to warn",
        reason ="Reason for the warning"
    )
    async def warn(
        self,
        inter : discord.Interaction,
        user  : discord.Member,
        reason: str = "No reason provided."
    ):
        if user.bot or user == inter.user:
            return await inter.response.send_message("⚠️ Invalid target user.", ephemeral=True)

        db.add_warning(user.id, inter.user.id, reason)

        # DM (best-effort)
        dm_ok = True
        try:
            dm = discord.Embed(
                title       ="🚨 You Have Been Warned",
                description =f"You received a warning in **{inter.guild.name}**.",
                color       =discord.Color.red(),
                timestamp   =datetime.utcnow()
            )
            dm.add_field(name="Reason", value=reason, inline=False)
            await user.send(embed=dm)
        except discord.Forbidden:
            dm_ok = False

        # Public confirmation
        embed = discord.Embed(
            title       ="⚠️ User Warned",
            description =f"{user.mention} has been warned.",
            color       =discord.Color.orange(),
            timestamp   =datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"Moderator: {inter.user.display_name} • {FOOTER_TXT}")
        await inter.response.send_message(embed=embed)

        if not dm_ok:
            await inter.followup.send("(Could not DM the user.)", ephemeral=True)

    # -------------------------------------------------------------------------
    # /warnlist
    # -------------------------------------------------------------------------
    @app_commands.command(
        name        ="warnlist",
        description ="[Moderator] List a user’s warnings."
    )
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(user="User to view warnings for")
    async def warnlist(self, inter: discord.Interaction, user: discord.Member):
        warnings = db.get_warnings(user.id)
        if not warnings:
            return await inter.response.send_message(
                f"**{user.display_name}** has no warnings.",
                ephemeral=True
            )

        embed = discord.Embed(
            title =f"📜 Warnings for {user.display_name}",
            color =discord.Color.dark_orange()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for w in warnings:
            mod  = inter.guild.get_member(w["moderator_id"])
            name = mod.display_name if mod else "Unknown mod"
            ts   = w["timestamp"].strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(
                name  =f"🗓️ {ts}",
                value =f"**Reason:** {w['reason']}\n**Moderator:** {name}",
                inline=False
            )

        embed.set_footer(text=FOOTER_TXT)
        await inter.response.send_message(embed=embed, ephemeral=True)

    # -------------------------------------------------------------------------
    # /removewarnlist
    # -------------------------------------------------------------------------
    @app_commands.command(
        name        ="removewarnlist",
        description ="[Moderator] Clear all warnings for a user."
    )
    @app_commands.guilds(guild_obj)
    @is_moderator()
    @app_commands.describe(user="User whose warnings to clear")
    async def removewarnlist(self, inter: discord.Interaction, user: discord.Member):
        warnings = db.get_warnings(user.id)
        if not warnings:
            return await inter.response.send_message(
                f"**{user.display_name}** has no warnings.",
                ephemeral=True
            )

        # confirmation view
        view = discord.ui.View(timeout=60)
        btn_confirm = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
        btn_cancel  = discord.ui.Button(label="Cancel",  style=discord.ButtonStyle.secondary)

        async def confirm(btn_inter: discord.Interaction):
            if btn_inter.user != inter.user:
                return await btn_inter.response.send_message("Not your confirmation.", ephemeral=True)
            db.clear_warnings(user.id)
            await btn_inter.response.edit_message(
                content=f"✅ Cleared all warnings for **{user.display_name}**.",
                view=None
            )

        async def cancel(btn_inter: discord.Interaction):
            await btn_inter.response.edit_message(content="Cancelled.", view=None)

        btn_confirm.callback = confirm
        btn_cancel.callback  = cancel
        view.add_item(btn_confirm)
        view.add_item(btn_cancel)

        await inter.response.send_message(
            f"⚠️ Clear **{len(warnings)}** warning(s) for **{user.display_name}**?",
            view=view,
            ephemeral=True
        )

# ── setup ---------------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot), guilds=[guild_obj])
