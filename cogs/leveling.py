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

# --- Configuration ---
LEVEL_ROLES = {
    30: 1371032270361853962,
    60: 1371032537740214302,
    120: 1371032664026382427,
    210: 1371032830217289748,
    300: 1371032964938600521,
    450: 1371033073038266429,
}

# Cooldown for XP gain (in seconds)
XP_COOLDOWN = 60
GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

# --- Paginated Leaderboard View ---
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
            return discord.Embed(title="🚀 Level Leaderboard", description="No one has gained any XP yet!", color=discord.Color.blue())

        total_pages = (total_users + self.users_per_page - 1) // self.users_per_page
        self.current_page = max(0, min(self.current_page, total_pages - 1))

        start_index = self.current_page * self.users_per_page
        leaderboard_data = db.get_leveling_leaderboard(skip=start_index, limit=self.users_per_page)

        description = ""
        for i, entry in enumerate(leaderboard_data):
            rank = start_index + i + 1
            user_id = entry.get('user_id')
            level = entry.get('level', 0)
            xp = entry.get('xp', 0)
            description += f"**{rank}.** <@{user_id}> - **Level {level}** ({xp} XP)\n"

        embed = discord.Embed(
            title="🚀 Top Adventurers",
            description=description,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages}")
        
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


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns = {}

    def get_xp_for_level(self, level):
        return 10 * (5 * (level ** 2) + (50 * level) + 100)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        current_time = asyncio.get_event_loop().time()

        if user_id in self.xp_cooldowns:
            if current_time - self.xp_cooldowns[user_id] < XP_COOLDOWN:
                return

        self.xp_cooldowns[user_id] = current_time

        xp_to_add = random.randint(1, 3)
        db.update_user_xp(user_id, xp_to_add)

        user_data = db.get_user_level_data(user_id)
        user_level = user_data.get('level', 0)
        user_xp = user_data.get('xp', 0)
        xp_needed = self.get_xp_for_level(user_level)

        if user_xp >= xp_needed:
            new_level = user_level + 1
            db.set_user_level(user_id, new_level)

            level_channel_id = db.get_channel(message.guild.id, "leveling")
            if level_channel_id:
                level_channel = message.guild.get_channel(level_channel_id)
                if level_channel:
                    embed = discord.Embed(
                        title="🎉 Level Up!",
                        description=f"Congratulations {message.author.mention}, you've reached **Level {new_level}**!",
                        color=discord.Color.fuchsia()
                    )
                    await level_channel.send(embed=embed)

            if new_level in LEVEL_ROLES:
                await self.update_user_roles(message.author, new_level)

    async def update_user_roles(self, member: discord.Member, new_level: int):
        guild = member.guild
        role_to_add_id = LEVEL_ROLES.get(new_level)
        if not role_to_add_id:
            return
        role_to_add = guild.get_role(role_to_add_id)
        if not role_to_add:
            print(f"Error: Role ID {role_to_add_id} not found.")
            return

        roles_to_remove_ids = [role_id for level, role_id in LEVEL_ROLES.items() if level < new_level]
        roles_to_remove = [guild.get_role(rid) for rid in roles_to_remove_ids if guild.get_role(rid)]

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Level up")
            await member.add_roles(role_to_add, reason=f"Reached Level {new_level}")
        except discord.Forbidden:
            print(f"Error: Cannot manage roles for {member.display_name}.")
        except Exception as e:
            print(f"An error occurred while updating roles: {e}")

    # --- Slash Commands ---

    @app_commands.command(name="rank", description="Check your or another user's level and XP.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to check the rank of.")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        user_data = db.get_user_level_data(target_user.id)
        if not user_data:
            await interaction.response.send_message(f"**{target_user.display_name}** hasn't generated any XP yet!", ephemeral=True)
            return

        level = user_data.get('level', 0)
        xp = user_data.get('xp', 0)
        xp_needed = self.get_xp_for_level(level)
        rank = db.get_user_leveling_rank(target_user.id)

        embed = discord.Embed(title=f"🚀 Level Rank for {target_user.display_name}", color=target_user.color)
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="🧬 Level", value=f"**{level}**", inline=True)
        embed.add_field(name="🏆 Rank", value=f"**#{rank}**", inline=True)
        embed.add_field(name="💠 XP", value=f"`{xp} / {xp_needed}`", inline=False)
        progress = int((xp / xp_needed) * 20) if xp_needed else 0
        bar = "🟩" * progress + "⬛" * (20 - progress)
        embed.add_field(name="Progress to Next Level", value=bar, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="updateroles", description="Update your roles based on your current level.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user whose roles you want to update.")
    async def updateroles(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        user_data = db.get_user_level_data(target_user.id)
        if not user_data:
            await interaction.response.send_message(f"**{target_user.display_name}** hasn't chatted yet.", ephemeral=True)
            return

        current_level = user_data.get('level', 0)
        highest_achieved_role_id = None
        sorted_roles = sorted(LEVEL_ROLES.items(), key=lambda item: item[0], reverse=True)

        for level_req, role_id in sorted_roles:
            if current_level >= level_req:
                highest_achieved_role_id = role_id
                break

        all_level_role_ids = set(LEVEL_ROLES.values())
        roles_to_add, roles_to_remove = [], []

        for role_id in all_level_role_ids:
            role = interaction.guild.get_role(role_id)
            if not role:
                continue
            has_role = role in target_user.roles
            if role_id == highest_achieved_role_id and not has_role:
                roles_to_add.append(role)
            elif has_role:
                roles_to_remove.append(role)

        if roles_to_remove:
            await target_user.remove_roles(*roles_to_remove, reason="Manual role update")
        if roles_to_add:
            await target_user.add_roles(*roles_to_add, reason="Manual role update")

        if not roles_to_add and not roles_to_remove:
            await interaction.response.send_message(f"✅ **{target_user.display_name}**'s roles are already up-to-date.", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ Roles updated for **{target_user.display_name}**.", ephemeral=True)

    @app_commands.command(name="chatlvlup", description="Announce your last level up in chat.")
    @app_commands.guilds(guild_obj)
    async def chatlvlup(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        user_data = db.get_user_level_data(target_user.id)
        if not user_data:
            await interaction.response.send_message(f"**{target_user.display_name}** hasn't chatted yet!", ephemeral=True)
            return
        level = user_data.get('level', 0)
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"Congratulations {target_user.mention}, you've reached **Level {level}**!",
            color=discord.Color.fuchsia()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="Show your profile: cookies, level, XP, and rank.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(user="The user to show the profile of.")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        user_data = db.get_user_level_data(target_user.id)
        level = user_data.get('level', 0) if user_data else 0
        xp = user_data.get('xp', 0) if user_data else 0
        xp_needed = self.get_xp_for_level(level)
        rank = db.get_user_leveling_rank(target_user.id) if user_data else 'Unranked'

        cookie_balance = db.get_cookies(target_user.id)
        cookie_rank = db.get_user_rank(target_user.id)

        embed = discord.Embed(
            title=f"🚀 Profile for {target_user.display_name}",
            color=target_user.color
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        level_info = f"**Level:** {level}\n**Rank:** #{rank}\n**XP:** {xp} / {xp_needed}"
        embed.add_field(name="🧬 Leveling Stats", value=level_info, inline=True)
        cookie_info = f"**Balance:** {cookie_balance} 🍪\n**Rank:** #{cookie_rank}"
        embed.add_field(name="🍪 Cookie Stats", value=cookie_info, inline=True)
        if user_data:
            progress = int((xp / xp_needed) * 20) if xp_needed > 0 else 0
            bar = "🟩" * progress + "⬛" * (20 - progress)
            embed.add_field(name="Progress to Next Level", value=bar, inline=False)
        embed.set_footer(text=f"Joined: {target_user.joined_at.strftime('%b %d, %Y')}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leveltop", description="Show the top users by level/XP.")
    @app_commands.guilds(guild_obj)
    async def leveltop(self, interaction: discord.Interaction):
        view = LevelLeaderboardView(interaction.user, interaction)
        embed = await view.get_page_embed()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Leveling(bot))
