import discord
from discord.ext import commands
from discord import app_commands
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os, sys
import io

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250

# XP Roles based on levels
XP_ROLES = {
    30: 1371032270361853962,   # Lv 30
    60: 1371032537740214302,   # Lv 60  
    120: 1371032664026382427,  # Lv 120
    210: 1371032830217289748,  # Lv 210
    300: 1371032964938600521,  # Lv 300
    450: 1371033073038266429   # Lv 450
}

# Cookie Roles based on cookie count
COOKIE_ROLES = {
    100: 1370998669884788788,   # 100 cookies
    500: 1370999721593671760,   # 500 cookies
    1000: 1371000389444305017,  # 1000 cookies
    1750: 1371001322131947591,  # 1750 cookies
    3000: 1371001806930579518,  # 3000 cookies
    5000: 1371304693715964005   # 5000 cookies
}

# Job titles with promotion system
JOB_TITLES = [
    {"name": "Intern", "min_level": 0, "max_level": 9, "promotion_bonus": 50},
    {"name": "Junior Developer", "min_level": 10, "max_level": 19, "promotion_bonus": 100},
    {"name": "Software Developer", "min_level": 20, "max_level": 29, "promotion_bonus": 150},
    {"name": "Senior Developer", "min_level": 30, "max_level": 49, "promotion_bonus": 200},
    {"name": "Team Lead", "min_level": 50, "max_level": 99, "promotion_bonus": 300},
    {"name": "Engineering Manager", "min_level": 100, "max_level": 199, "promotion_bonus": 500},
    {"name": "Director", "min_level": 200, "max_level": 299, "promotion_bonus": 750},
    {"name": "VP of Engineering", "min_level": 300, "max_level": 449, "promotion_bonus": 1000},
    {"name": "CTO", "min_level": 450, "max_level": 999, "promotion_bonus": 1500},
    {"name": "Tech Legend", "min_level": 1000, "max_level": 9999, "promotion_bonus": 2000}
]

class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Leveling] Loaded successfully.")

    def calculate_xp_for_level(self, level: int) -> int:
        """Increased XP requirement per level - much harder progression"""
        if level <= 10:
            return int(200 * (level ** 2))
        elif level <= 50:
            return int(300 * (level ** 2.2))
        elif level <= 100:
            return int(500 * (level ** 2.5))
        else:
            return int(1000 * (level ** 2.8))

    def calculate_level_from_xp(self, xp: int) -> int:
        """Calculate level from XP using binary search for efficiency"""
        level = 0
        while self.calculate_xp_for_level(level + 1) <= xp:
            level += 1
        return level

    def get_job_title(self, level: int) -> dict:
        """Get job title based on level"""
        for job in JOB_TITLES:
            if job["min_level"] <= level <= job["max_level"]:
                return job
        return JOB_TITLES[-1]  # Default to highest title

    async def update_xp_roles(self, member: discord.Member, level: int):
        """Update user's XP-based roles"""
        try:
            guild = member.guild
            roles_to_add = []
            roles_to_remove = []
            
            for level_req, role_id in XP_ROLES.items():
                role = guild.get_role(role_id)
                if role:
                    if level >= level_req and role not in member.roles:
                        roles_to_add.append(role)
                    elif level < level_req and role in member.roles:
                        roles_to_remove.append(role)
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="XP level role update")
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="XP level role update")
                
        except Exception as e:
            print(f"Error updating XP roles for {member}: {e}")

    async def update_cookie_roles(self, member: discord.Member, cookies: int):
        """Update user's cookie-based roles"""
        try:
            guild = member.guild
            roles_to_add = []
            roles_to_remove = []
            
            for cookie_req, role_id in COOKIE_ROLES.items():
                role = guild.get_role(role_id)
                if role:
                    if cookies >= cookie_req and role not in member.roles:
                        roles_to_add.append(role)
                    elif cookies < cookie_req and role in member.roles:
                        roles_to_remove.append(role)
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Cookie milestone role update")
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Cookie milestone role update")
                
        except Exception as e:
            print(f"Error updating cookie roles for {member}: {e}")

    @app_commands.command(name="rank", description="Shows your current level, XP, and server rank")
    @app_commands.describe(user="User to check rank for")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        try:
            user_data = db.get_user_data(target.id)
            xp = user_data.get('xp', 0)
            level = self.calculate_level_from_xp(xp)
            
            # Calculate XP for current and next level
            current_level_xp = self.calculate_xp_for_level(level)
            next_level_xp = self.calculate_xp_for_level(level + 1)
            xp_needed = next_level_xp - xp
            xp_progress = xp - current_level_xp

            # Get rank
            all_users = db.get_leaderboard('xp')
            rank = next((i + 1 for i, u in enumerate(all_users) if u['user_id'] == target.id), 'N/A')

            # Get job title
            job = self.get_job_title(level)

            embed = discord.Embed(
                title=f"📊 Rank Card - {target.display_name}",
                color=target.accent_color or 0x7289da
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            embed.add_field(name="🏆 Level", value=level, inline=True)
            embed.add_field(name="⭐ Total XP", value=f"{xp:,}", inline=True)
            embed.add_field(name="📈 Rank", value=f"#{rank}", inline=True)
            embed.add_field(name="💼 Job Title", value=job["name"], inline=True)
            embed.add_field(name="🎯 Progress", value=f"{xp_progress:,}/{next_level_xp - current_level_xp:,} XP", inline=True)
            embed.add_field(name="🚀 XP Needed", value=f"{xp_needed:,} XP", inline=True)

            # Progress bar
            progress_percentage = (xp_progress / (next_level_xp - current_level_xp)) * 100
            progress_bar_length = 20
            progress_filled = int((progress_percentage / 100) * progress_bar_length)
            progress_bar = "█" * progress_filled + "░" * (progress_bar_length - progress_filled)
            embed.add_field(name="📊 Progress Bar", value=f"`{progress_bar}` {progress_percentage:.1f}%", inline=False)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error getting rank data: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error getting rank data: {str(e)}", ephemeral=True)

    @app_commands.command(name="leveltop", description="Displays paginated level leaderboard")
    @app_commands.describe(page="Page number (default: 1)")
    async def leveltop(self, interaction: discord.Interaction, page: int = 1):
        try:
            if page < 1:
                page = 1
                
            items_per_page = 10
            skip = (page - 1) * items_per_page
            
            # Get total users for pagination
            all_users = db.get_leaderboard('xp')
            total_users = len(all_users)
            total_pages = (total_users + items_per_page - 1) // items_per_page
            
            if page > total_pages:
                await interaction.response.send_message(f"❌ Page {page} doesn't exist! Max page: {total_pages}", ephemeral=True)
                return

            # Get users for this page
            page_users = all_users[skip:skip + items_per_page]
            
            if not page_users:
                await interaction.response.send_message("❌ No leaderboard data available!", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🥇 Level Leaderboard - Page {page}/{total_pages}",
                color=0xffd700
            )

            leaderboard_text = []
            for i, user_data in enumerate(page_users, start=skip + 1):
                user_id = user_data['user_id']
                xp = user_data.get('xp', 0)
                level = self.calculate_level_from_xp(xp)
                job = self.get_job_title(level)
                
                try:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    username = user.display_name if hasattr(user, 'display_name') else user.name
                except:
                    username = f"User {user_id}"

                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard_text.append(f"{medal} **{username}** - Level {level} ({xp:,} XP)\n`{job['name']}`")

            embed.description = "\n\n".join(leaderboard_text)
            embed.set_footer(text=f"Page {page}/{total_pages} • Keep chatting to climb the ranks!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error getting leaderboard: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error getting leaderboard: {str(e)}", ephemeral=True)

    @app_commands.command(name="profile", description="Shows comprehensive profile with level, cookies, job, and daily streak")
    @app_commands.describe(user="User to check profile for")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        try:
            user_data = db.get_user_data(target.id)
            xp = user_data.get('xp', 0)
            cookies = user_data.get('cookies', 0)
            coins = user_data.get('coins', 0)
            daily_streak = user_data.get('daily_streak', 0)
            level = self.calculate_level_from_xp(xp)
            
            # Get ranks
            xp_leaderboard = db.get_leaderboard('xp')
            cookie_leaderboard = db.get_leaderboard('cookies')
            coin_leaderboard = db.get_leaderboard('coins')
            
            xp_rank = next((i + 1 for i, u in enumerate(xp_leaderboard) if u['user_id'] == target.id), 'N/A')
            cookie_rank = next((i + 1 for i, u in enumerate(cookie_leaderboard) if u['user_id'] == target.id), 'N/A')
            coin_rank = next((i + 1 for i, u in enumerate(coin_leaderboard) if u['user_id'] == target.id), 'N/A')

            # Get job title
            job = self.get_job_title(level)

            embed = discord.Embed(
                title=f"👤 Profile - {target.display_name}",
                color=target.accent_color or 0x7289da,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            # Level section
            current_level_xp = self.calculate_xp_for_level(level)
            next_level_xp = self.calculate_xp_for_level(level + 1)
            xp_progress = xp - current_level_xp
            progress_bar_length = 10
            progress_filled = int((xp_progress / (next_level_xp - current_level_xp)) * progress_bar_length)
            progress_bar = "█" * progress_filled + "░" * (progress_bar_length - progress_filled)
            embed.add_field(
                name="📊 Level Stats",
                value=f"**Level:** {level}\n**XP:** {xp:,}\n**Rank:** #{xp_rank}\n**Progress:** {progress_bar} {xp_progress:,}/{next_level_xp - current_level_xp:,}",
                inline=False
            )
            
            # Job section
            embed.add_field(
                name="💼 Career",
                value=f"**Job Title:** {job['name']}\n**Level Range:** {job['min_level']}-{job['max_level']}\n**Promotion Bonus:** {job['promotion_bonus']} coins",
                inline=False
            )
            
            # Currency section
            embed.add_field(
                name="💰 Currency Stats", 
                value=f"**🍪 Cookies:** {cookies:,} (Rank #{cookie_rank})\n**🪙 Coins:** {coins:,} (Rank #{coin_rank})",
                inline=False
            )

            # Daily streak section
            streak_emoji = "🔥" * min(daily_streak // 7, 5)  # Fire emoji for every 7 days
            embed.add_field(
                name="🔥 Daily Streak",
                value=f"**Current Streak:** {daily_streak} days {streak_emoji}\n**Streak Bonus:** {'Active' if daily_streak >= 7 else 'Inactive'}",
                inline=False
            )

            # Additional stats
            embed.add_field(name="📅 Account Created", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="📅 Joined Server", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error getting profile data: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error getting profile data: {str(e)}", ephemeral=True)

    @app_commands.command(name="chatlvlup", description="Announces your latest level-up in chat")
    async def chatlvlup(self, interaction: discord.Interaction):
        try:
            user_data = db.get_user_data(interaction.user.id)
            xp = user_data.get('xp', 0)
            level = self.calculate_level_from_xp(xp)
            job = self.get_job_title(level)

            embed = discord.Embed(
                title="🎉 Level Up Announcement!",
                description=f"🎊 **{interaction.user.display_name}** has reached **Level {level}**! 🎊\n\n💼 **New Job Title:** {job['name']}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="📊 Stats", value=f"**Total XP:** {xp:,}\n**Level:** {level}", inline=True)
            embed.add_field(name="💼 Career", value=f"**Position:** {job['name']}\n**Range:** Lv{job['min_level']}-{job['max_level']}", inline=True)
            embed.set_footer(text="Keep chatting to level up even more!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error announcing level: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error announcing level: {str(e)}", ephemeral=True)

    @app_commands.command(name="daily", description="Claim your daily XP and coin bonus")
    async def daily(self, interaction: discord.Interaction):
        try:
            result = db.claim_daily_bonus(interaction.user.id)
            
            if result['success']:
                level = self.calculate_level_from_xp(result.get('total_xp', 0))
                job = self.get_job_title(level)
                
                embed = discord.Embed(
                    title="🎁 Daily Bonus Claimed!",
                    description=f"**XP Gained:** {result['xp_gained']}\n**Coins Gained:** {result['coins_gained']}\n**Streak:** {result['streak']} day(s)",
                    color=0x00ff00
                )
                
                if result['streak'] % 7 == 0:
                    embed.add_field(name="🎉 Streak Bonus!", value="You got extra rewards for your 7-day streak!", inline=False)
                
                embed.add_field(name="💼 Current Job", value=job['name'], inline=True)
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                await interaction.response.send_message(embed=embed)
            else:
                time_left = result.get('time_left', 'some time')
                embed = discord.Embed(
                    title="⏰ Daily Already Claimed",
                    description=f"You can claim your next daily bonus in {time_left}",
                    color=0xff9900
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error claiming daily: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error claiming daily: {str(e)}", ephemeral=True)

    @app_commands.command(name="streaktop", description="Shows paginated daily streak leaderboard")
    @app_commands.describe(page="Page number (default: 1)")
    async def streaktop(self, interaction: discord.Interaction, page: int = 1):
        try:
            if page < 1:
                page = 1
                
            items_per_page = 10
            skip = (page - 1) * items_per_page
            
            all_users = db.get_leaderboard('daily_streak')
            total_users = len(all_users)
            total_pages = (total_users + items_per_page - 1) // items_per_page
            
            if page > total_pages:
                await interaction.response.send_message(f"❌ Page {page} doesn't exist! Max page: {total_pages}", ephemeral=True)
                return

            page_users = all_users[skip:skip + items_per_page]
            
            if not page_users:
                await interaction.response.send_message("❌ No streak data available!", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🔥 Daily Streak Leaderboard - Page {page}/{total_pages}",
                color=0xff4500
            )

            leaderboard_text = []
            for i, user_data in enumerate(page_users, start=skip + 1):
                user_id = user_data['user_id']
                streak = user_data.get('daily_streak', 0)
                
                try:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    username = user.display_name if hasattr(user, 'display_name') else user.name
                except:
                    username = f"User {user_id}"

                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                fire_emoji = "🔥" * min(streak // 7, 5)  # Show fire emojis for every 7 days, max 5
                leaderboard_text.append(f"{medal} **{username}** - {streak} day streak {fire_emoji}")

            embed.description = "\n".join(leaderboard_text)
            embed.set_footer(text=f"Page {page}/{total_pages} • Keep your daily streak alive!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error getting streak leaderboard: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error getting streak leaderboard: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
