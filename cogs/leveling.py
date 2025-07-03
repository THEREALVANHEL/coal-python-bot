import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
import random
import asyncio

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# --- Configuration ------------------------------------------------------------
LEVEL_ROLES = {
    5:  1371032270361853962,
    10: 1371032537740214302,
    20: 1371032664026382427,
    35: 1371032830217289748,
    50: 1371032964938600521,
    75: 1371033073038266429,
}
XP_COOLDOWN = 60                     # seconds
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# ───────────────────────────────────────────────────────────────────────────────
# Paginated Level Leaderboard View (unchanged)
# ───────────────────────────────────────────────────────────────────────────────
class LevelLeaderboardView(discord.ui.View):
    def __init__(self, author, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.author = author
        self.interaction = interaction
        self.current_page = 0
        self.users_per_page = 10

    async def on_timeout(self):
        try:
            for item in self.children:
                item.disabled = True
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

    async def get_page_embed(self):
        total_users = db.get_total_users_in_leveling()
        if total_users == 0:
            return discord.Embed(
                title="🚀 Level Leaderboard",
                description="No one has gained any XP yet!",
                color=discord.Color.blue()
            )

        total_pages = (total_users + self.users_per_page - 1) // self.users_per_page
        self.current_page = max(0, min(self.current_page, total_pages - 1))
        start_index = self.current_page * self.users_per_page

        leaderboard_data = db.get_leveling_leaderboard(
            skip=start_index,
            limit=self.users_per_page
        )

        desc = ""
        for i, entry in enumerate(leaderboard_data):
            rank = start_index + i + 1
            user_id = entry['user_id']
            level  = entry.get('level', 0)
            xp     = entry.get('xp', 0)
            desc += f"**{rank}.** <@{user_id}> – **Lvl {level}** ({xp} XP)\n"

        embed = discord.Embed(
            title="🚀 Top Adventurers",
            description=desc,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Page {self.current_page+1}/{total_pages}")

        # enable/disable buttons
        self.children[0].disabled = (self.current_page == 0)
        self.children[1].disabled = (self.current_page >= total_pages - 1)
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = await self.get_page_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        self.current_page += 1
        await self.update_message(interaction)

# ───────────────────────────────────────────────────────────────────────────────
# NEW: Paginated Daily-Streak Leaderboard View
# ───────────────────────────────────────────────────────────────────────────────
class DailyStreakLeaderboardView(discord.ui.View):
    def __init__(self, author, interaction: discord.Interaction):
        super().__init__(timeout=180)
        self.author = author
        self.interaction = interaction
        self.current_page = 0
        self.users_per_page = 10

    async def on_timeout(self):
        try:
            for item in self.children:
                item.disabled = True
            await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass

    async def get_page_embed(self):
        total_users = db.get_total_users_in_dailies()          # implement or use len(...)
        if total_users == 0:
            return discord.Embed(
                title="🔥 Daily-Streak Leaderboard",
                description="No streaks yet – be the first to /daily!",
                color=discord.Color.orange()
            )

        total_pages = (total_users + self.users_per_page - 1) // self.users_per_page
        self.current_page = max(0, min(self.current_page, total_pages - 1))
        start_index = self.current_page * self.users_per_page

        leaderboard = db.get_top_daily_streaks(
            skip=start_index,
            limit=self.users_per_page
        )

        desc = ""
        for i, entry in enumerate(leaderboard):
            rank   = start_index + i + 1
            user   = entry['user_id']
            streak = entry.get('streak', 0)
            desc += f"**{rank}.** <@{user}> – **{streak} day streak** 🔥\n"

        embed = discord.Embed(
            title="🔥 Daily-Streak Leaderboard",
            description=desc,
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Page {self.current_page+1}/{total_pages}")
        self.children[0].disabled = (self.current_page == 0)
        self.children[1].disabled = (self.current_page >= total_pages - 1)
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = await self.get_page_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.grey)
    async def nxt(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This isn't for you!", ephemeral=True)
            return
        self.current_page += 1
        await self.update_message(interaction)

# ───────────────────────────────────────────────────────────────────────────────
class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns = {}

    # (all existing listeners/commands remain unchanged) ────────────────────────
    # ... on_message, rank, updateroles, profile, leveltop, etc ...
    # (code omitted here for brevity — keep yours as-is)

    # ───────────────────────────────────────────────────────────────────────────
    # NEW slash-command: /streaktop
    # ───────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="streaktop",
        description="Show the top users by current daily streak."
    )
    @app_commands.guilds(guild_obj)
    async def streaktop(self, interaction: discord.Interaction):
        view = DailyStreakLeaderboardView(interaction.user, interaction)
        embed = await view.get_page_embed()
        await interaction.response.send_message(embed=embed, view=view)

# ───────────────────────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(Leveling(bot))
