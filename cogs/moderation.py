# cogs/moderation.py
import discord
from discord.ext import commands
from discord import option  # Added for Pycord slash command options
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

# ── Permission check helper ---------------------------------------------------
def has_moderator_role(ctx: discord.ApplicationContext) -> bool:
    """Check if user has moderator permissions"""
    if ctx.user.guild_permissions.administrator:
        return True
    if any(r.name in MODERATOR_ROLES for r in ctx.user.roles):
        return True
    return False

# ── Cog -----------------------------------------------------------------------
class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Moderation] Cog loaded successfully.")

    # -------------------------------------------------------------------------
    # /modclear
    # -------------------------------------------------------------------------
    @commands.slash_command(
        name="modclear",
        description="[Moderator] Delete a number of recent messages.",
        guild_ids=[GUILD_ID]
    )
    @option("amount", description="Number of messages to delete (1-100)", min_value=1, max_value=100)
    async def modclear(
        self,
        ctx: discord.ApplicationContext,
        amount: int
    ):
        if not has_moderator_role(ctx):
            await ctx.respond("You don't have the required role to use this command.", ephemeral=True)
            return

        await ctx.response.defer(ephemeral=True)

        deleted = await ctx.channel.purge(limit=amount)
        await ctx.followup.send(
            f"🧹 Cleared **{len(deleted)}** messages.",
            ephemeral=True
        )

        # optional mod-log
        modlog_id = db.get_channel(ctx.guild.id, "modlog")
        if modlog_id:
            ch = ctx.guild.get_channel(modlog_id)
            if ch:
                embed = discord.Embed(
                    title       ="🧹 Messages Cleared",
                    description =f"**{len(deleted)}** messages removed in {ctx.channel.mention}",
                    color       =discord.Color.orange(),
                    timestamp   =datetime.utcnow()
                )
                embed.set_footer(text=f"Moderator: {ctx.user.display_name}")
                try:    await ch.send(embed=embed)
                except discord.Forbidden: pass

    # -------------------------------------------------------------------------
    # /warn
    # -------------------------------------------------------------------------
    @commands.slash_command(
        name="warn",
        description="[Moderator] Issue a warning to a user.",
        guild_ids=[GUILD_ID]
    )
    @option("user", description="User to warn", type=discord.Member)
    @option("reason", description="Reason for the warning", default="No reason provided.")
    async def warn(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member,
        reason: str = "No reason provided."
    ):
        if not has_moderator_role(ctx):
            await ctx.respond("You don't have the required role to use this command.", ephemeral=True)
            return

        if user.bot or user == ctx.user:
            return await ctx.respond("⚠️ Invalid target user.", ephemeral=True)

        db.add_warning(user.id, ctx.user.id, reason)

        # DM (best-effort)
        dm_ok = True
        try:
            dm = discord.Embed(
                title       ="🚨 You Have Been Warned",
                description =f"You received a warning in **{ctx.guild.name}**.",
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
        embed.set_footer(text=f"Moderator: {ctx.user.display_name} • {FOOTER_TXT}")
        await ctx.respond(embed=embed)

        if not dm_ok:
            await ctx.followup.send("(Could not DM the user.)", ephemeral=True)

    # -------------------------------------------------------------------------
    # /warnlist
    # -------------------------------------------------------------------------
    @commands.slash_command(
        name="warnlist",
        description="[Moderator] List a user's warnings.",
        guild_ids=[GUILD_ID]
    )
    @option("user", description="User to view warnings for", type=discord.Member)
    async def warnlist(self, ctx: discord.ApplicationContext, user: discord.Member):
        if not has_moderator_role(ctx):
            await ctx.respond("You don't have the required role to use this command.", ephemeral=True)
            return

        warnings = db.get_warnings(user.id)
        if not warnings:
            return await ctx.respond(
                f"**{user.display_name}** has no warnings.",
                ephemeral=True
            )

        embed = discord.Embed(
            title =f"📜 Warnings for {user.display_name}",
            color =discord.Color.dark_orange()
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for w in warnings:
            mod  = ctx.guild.get_member(w["moderator_id"])
            name = mod.display_name if mod else "Unknown mod"
            ts   = w["timestamp"].strftime("%Y-%m-%d %H:%M UTC")
            embed.add_field(
                name  =f"🗓️ {ts}",
                value =f"**Reason:** {w['reason']}\n**Moderator:** {name}",
                inline=False
            )

        embed.set_footer(text=FOOTER_TXT)
        await ctx.respond(embed=embed, ephemeral=True)

    # -------------------------------------------------------------------------
    # /removewarnlist
    # -------------------------------------------------------------------------
    @commands.slash_command(
        name="removewarnlist",
        description="[Moderator] Clear all warnings for a user.",
        guild_ids=[GUILD_ID]
    )
    @option("user", description="User whose warnings to clear", type=discord.Member)
    async def removewarnlist(self, ctx: discord.ApplicationContext, user: discord.Member):
        if not has_moderator_role(ctx):
            await ctx.respond("You don't have the required role to use this command.", ephemeral=True)
            return

        warnings = db.get_warnings(user.id)
        if not warnings:
            return await ctx.respond(
                f"**{user.display_name}** has no warnings.",
                ephemeral=True
            )

        # confirmation view
        view = discord.ui.View(timeout=60)
        btn_confirm = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
        btn_cancel  = discord.ui.Button(label="Cancel",  style=discord.ButtonStyle.secondary)

        async def confirm(btn_inter: discord.Interaction):
            if btn_inter.user != ctx.user:
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

        await ctx.respond(
            f"⚠️ Clear **{len(warnings)}** warning(s) for **{user.display_name}**?",
            view=view,
            ephemeral=True
        )

# ── setup ---------------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot), guilds=[guild_obj])
