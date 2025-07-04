# cogs/economy.py
# Pycord 2.x  •  Slash-only economy (daily XP & cookie donation)
# – Uses @commands.slash_command with guild_ids for **instant sync**
# – Keeps everything in-memory (no global sync delay)

import os
import sys
from datetime import datetime, timedelta

import discord
from discord import option                # ⬅️ Pycord slash-option helper
from discord.ext import commands

# ── project imports ───────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import database as db  # noqa: E402

# ── Config ───────────────────────────────────────────────
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# ── Cog ──────────────────────────────────────────────────
class Economy(commands.Cog):
    """Daily XP + cookie-donation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Load cog without syncing (main.py handles syncing)
    async def cog_load(self):
        print("[Economy] Cog loaded successfully.")

    # ──────────────────────────────────────────────────────
    # /daily
    # ──────────────────────────────────────────────────────
    @commands.slash_command(
        name="daily",
        description="Claim your daily XP and build a streak!",
        guild_ids=[GUILD_ID],
    )
    async def daily(self, ctx: discord.ApplicationContext):
        user_id = ctx.author.id
        daily_data = db.get_daily_data(user_id)

        cooldown_hours = 22
        now = datetime.utcnow()

        # cooldown
        if daily_data and "last_checkin" in daily_data:
            time_since = now - daily_data["last_checkin"]
            if time_since < timedelta(hours=cooldown_hours):
                time_left = timedelta(hours=cooldown_hours) - time_since
                h, rem = divmod(int(time_left.total_seconds()), 3600)
                m, _ = divmod(rem, 60)
                return await ctx.respond(
                    f"⏳ {ctx.author.mention}, you've already claimed your daily reward!\n"
                    f"Try again in **{h}h {m}m**."
                )
# streak
        current_streak = daily_data.get("streak", 0) if daily_data else 0
        if daily_data and (now - daily_data["last_checkin"]) > timedelta(
            hours=cooldown_hours * 2
        ):
            new_streak = 1
        else:
            new_streak = current_streak + 1

        # reward
        reward = 20
        bonus_msg = ""
        if new_streak == 7:
            bonus = 50
            reward += bonus
            bonus_msg = f"🎉 7-day streak bonus! +**{bonus} XP**."
            db.update_daily_checkin(user_id, 0)  # reset
        else:
            db.update_daily_checkin(user_id, new_streak)

        db.update_user_xp(user_id, reward)

        # level-up check
        leveling_cog: commands.Cog | None = self.bot.get_cog("Leveling")
        if leveling_cog:
            udata = db.get_user_level_data(user_id)
            lvl, xp = udata.get("level", 0), udata.get("xp", 0)
            need = leveling_cog.get_xp_for_level(lvl)
            if xp >= need:
                lvl_channel_id = db.get_channel(ctx.guild.id, "leveling")
                if lvl_channel_id and (lvl_channel := ctx.guild.get_channel(lvl_channel_id)):
                    embed_lvl = discord.Embed(
                        title="🎉 Level Up!",
                        description=f"Congrats {ctx.author.mention}, you reached **Level {lvl + 1}**!",
                        color=discord.Color.fuchsia(),
                    )
                    await lvl_channel.send(embed=embed_lvl)

                # update roles (Leveling cog's method takes just member)
                await leveling_cog.update_user_roles(ctx.author)

        # response embed
        embed = discord.Embed(
            title="🌞 Daily Reward Claimed!",
            description=(
                f"{ctx.author.mention} gained **{reward} XP**!\n"
                f"Current streak: **{new_streak if new_streak != 7 else 0}** days."
            ),
            color=discord.Color.green(),
        )
        if bonus_msg:
            embed.add_field(name="Streak Bonus", value=bonus_msg)

        await ctx.respond(embed=embed)
# ──────────────────────────────────────────────────────
    # /donatecookies
    # ──────────────────────────────────────────────────────
    @commands.slash_command(
        name="donatecookies",
        description="Give some of your cookies to another user.",
        guild_ids=[GUILD_ID],
    )
    @option("user", description="User to receive cookies", type=discord.Member)
    @option("amount", description="Number of cookies to give", type=int)
    async def donatecookies(
        self, ctx: discord.ApplicationContext, user: discord.Member, amount: int
    ):
        sender_id = ctx.author.id
        receiver_id = user.id

        if amount <= 0:
            return await ctx.respond("Amount must be positive.", ephemeral=True)
        if sender_id == receiver_id:
            return await ctx.respond("You can't donate to yourself.", ephemeral=True)
        if user.bot:
            return await ctx.respond("You can't donate to a bot.", ephemeral=True)

        sender_balance = db.get_cookies(sender_id)
        if sender_balance < amount:
            return await ctx.respond(
                f"Not enough cookies. Your balance: **{sender_balance}** 🍪.", ephemeral=True
            )

        # transfer
        db.remove_cookies(sender_id, amount)
        db.add_cookies(receiver_id, amount)

        # update cookie roles
        cookies_cog: commands.Cog | None = self.bot.get_cog("Cookies")
        if cookies_cog:
            sender_member = ctx.guild.get_member(sender_id)
            if sender_member:
                await cookies_cog._update_cookie_roles(sender_member)  # type: ignore
            await cookies_cog._update_cookie_roles(user)  # type: ignore

        embed = discord.Embed(
            title="🎁 Cookies Donated!",
            description=f"{ctx.author.mention} gave **{amount}** 🍪 to {user.mention}!",
            color=discord.Color.from_rgb(255, 182, 193),
        )
        await ctx.respond(embed=embed)


# ─────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot), guilds=[guild_obj])
