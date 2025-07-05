import discord
from discord.ext import commands
from discord import app_commands
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os, sys
import io
from discord.ui import Button, View

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

class PaginationView(View):
    def __init__(self, leaderboard_type, total_pages, current_page, bot):
        super().__init__(timeout=300)
        self.leaderboard_type = leaderboard_type
        self.total_pages = total_pages
        self.current_page = current_page
        self.bot = bot
        
        # Update button states
        self.first_page.disabled = current_page == 1
        self.previous_page.disabled = current_page == 1
        self.next_page.disabled = current_page == total_pages
        self.last_page.disabled = current_page == total_pages

    @discord.ui.button(label="⏪ First", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_leaderboard(interaction, 1)

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_leaderboard(interaction, max(1, self.current_page - 1))

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_leaderboard(interaction, min(self.total_pages, self.current_page + 1))

    @discord.ui.button(label="⏩ Last", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_leaderboard(interaction, self.total_pages)

    async def update_leaderboard(self, interaction: discord.Interaction, page: int):
        self.current_page = page
        
        # Update button states
        self.first_page.disabled = page == 1
        self.previous_page.disabled = page == 1
        self.next_page.disabled = page == self.total_pages
        self.last_page.disabled = page == self.total_pages

        # Get the appropriate cog and call the leaderboard function
        if self.leaderboard_type == "xp":
            leveling_cog = self.bot.get_cog('Leveling')
            embed = await leveling_cog.create_level_leaderboard_embed(page)
        elif self.leaderboard_type == "cookies":
            cookies_cog = self.bot.get_cog('Cookies')
            embed = await cookies_cog.create_cookie_leaderboard_embed(page)
        elif self.leaderboard_type == "coins":
            economy_cog = self.bot.get_cog('Economy')
            embed = await economy_cog.create_coin_leaderboard_embed(page)
        elif self.leaderboard_type == "streak":
            leveling_cog = self.bot.get_cog('Leveling')
            embed = await leveling_cog.create_streak_leaderboard_embed(page)

        await interaction.response.edit_message(embed=embed, view=self)

    async def create_level_leaderboard_embed(self, page: int):
        items_per_page = 10
        skip = (page - 1) * items_per_page
        
        all_users = db.get_leaderboard('xp')
        total_users = len(all_users)
        total_pages = (total_users + items_per_page - 1) // items_per_page
        page_users = all_users[skip:skip + items_per_page]

        # Cool animated gradient colors for XP leaderboard
        embed = discord.Embed(
            title="🏆 **LEVEL LEADERBOARD** 🏆",
            description="⚡ *The Elite XP Champions* ⚡",
            color=0x00ff88,
            timestamp=datetime.now()
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

            # Cool medal system with special effects
            if i == 1:
                medal = "👑"
                rank_style = f"**#{i} {medal} {username}**"
                style_suffix = " ✨🔥✨"
            elif i == 2:
                medal = "🥈"
                rank_style = f"**#{i} {medal} {username}**"
                style_suffix = " ⭐💎⭐"
            elif i == 3:
                medal = "🥉"
                rank_style = f"**#{i} {medal} {username}**"
                style_suffix = " 🌟⚡🌟"
            elif i <= 5:
                rank_style = f"**#{i} 🔸 {username}**"
                style_suffix = " 💫"
            elif i <= 10:
                rank_style = f"**#{i} ▫️ {username}**"
                style_suffix = " ⭐"
            else:
                rank_style = f"#{i} • {username}"
                style_suffix = ""
            
            # Create progress bar for level
            current_level_xp = self.calculate_xp_for_level(level)
            next_level_xp = self.calculate_xp_for_level(level + 1)
            progress = (xp - current_level_xp) / (next_level_xp - current_level_xp) if next_level_xp > current_level_xp else 1
            progress_bars = int(progress * 8)
            progress_display = "▰" * progress_bars + "▱" * (8 - progress_bars)
            
            # Only show job if user has worked recently
            user_full_data = db.get_user_data(user_id)
            last_work = user_full_data.get('last_work', 0)
            show_job = last_work > 0
            
            level_display = f"🎯 **Level {level}** • {xp:,} XP"
            progress_line = f"`{progress_display}` {int(progress * 100)}%"
            
            if show_job:
                job_line = f"💼 *{job['name']}*"
                entry = f"{rank_style}{style_suffix}\n{level_display}\n{progress_line}\n{job_line}"
            else:
                entry = f"{rank_style}{style_suffix}\n{level_display}\n{progress_line}"
            
            leaderboard_text.append(entry)

        embed.description = f"⚡ *The Elite XP Champions* ⚡\n\n" + "\n\n".join(leaderboard_text)
        
        # Cool footer with stats
        embed.add_field(
            name="📊 **Server Stats**",
            value=f"🔥 **{total_users}** Active Members\n⚡ **Page {page}/{total_pages}**\n🎯 **Keep Grinding!**",
            inline=True
        )
        
        embed.add_field(
            name="🎮 **Pro Tips**",
            value="💬 Chat more to gain XP\n📈 Higher levels = better rewards\n🔄 Check `/profile` for details",
            inline=True
        )
        
        embed.set_footer(text="🔥 Level Leaderboard • Keep chatting to climb the ranks! • 💫 Live Data")
        
        return embed

    async def create_streak_leaderboard_embed(self, page: int):
        items_per_page = 10
        skip = (page - 1) * items_per_page
        
        streak_data = db.get_streak_leaderboard(page, 10)
        page_users = streak_data['users']
        total_pages = streak_data['total_pages']

        # Super cool fire-themed design
        embed = discord.Embed(
            title="🔥 **STREAK CHAMPIONS** 🔥",
            description="🌟 *The Daily Dedication Masters* 🌟",
            color=0xff4500,
            timestamp=datetime.now()
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

            # Epic streak ranking system
            if i == 1:
                rank_style = f"👑 **#{i} STREAK EMPEROR {username}** 👑"
                style_suffix = " 🔥🔥🔥"
            elif i == 2:
                rank_style = f"🥈 **#{i} FLAME MASTER {username}** 🥈"
                style_suffix = " 🔥🔥"
            elif i == 3:
                rank_style = f"🥉 **#{i} FIRE KEEPER {username}** 🥉"
                style_suffix = " 🔥"
            elif i <= 5:
                rank_style = f"🔸 **#{i} EMBER LORD {username}**"
                style_suffix = " ⚡"
            else:
                rank_style = f"▫️ **#{i} {username}**"
                style_suffix = ""
            
            # Streak visualization with cool effects
            if streak >= 365:
                streak_tier = "🏆 **LEGENDARY**"
                streak_emoji = "🔥🔥🔥🔥🔥"
            elif streak >= 180:
                streak_tier = "💎 **DIAMOND**"
                streak_emoji = "🔥🔥🔥🔥"
            elif streak >= 100:
                streak_tier = "💎 **MASTER**"
                streak_emoji = "🔥🔥🔥"
            elif streak >= 50:
                streak_tier = "⭐ **EXPERT**"
                streak_emoji = "🔥🔥"
            elif streak >= 30:
                streak_tier = "⭐ **VETERAN**"
                streak_emoji = "🔥"
            elif streak >= 14:
                streak_tier = "🌟 **COMMITTED**"
                streak_emoji = "�"
            elif streak >= 7:
                streak_tier = "✨ **DEDICATED**"
                streak_emoji = "⚡"
            else:
                streak_tier = "🔰 **ROOKIE**"
                streak_emoji = "✨"
            
            # Create streak progress bar
            progress = min(streak / 365, 1)  # Max out at 1 year
            progress_bars = int(progress * 10)
            streak_bar = "🔥" * progress_bars + "▱" * (10 - progress_bars)
            
            entry = f"{rank_style}{style_suffix}\n🔥 **{streak} Days** • {streak_tier}\n`{streak_bar}` {streak_emoji}"
            leaderboard_text.append(entry)

        embed.description = f"🌟 *The Daily Dedication Masters* 🌟\n\n" + "\n\n".join(leaderboard_text) if leaderboard_text else "🔥 No streak warriors yet! Be the first to start your daily journey!"
        
        # Cool stats section
        if leaderboard_text:
            total_streaks = len(streak_data.get('users', []))
            embed.add_field(
                name="🔥 **Streak Stats**",
                value=f"⚡ **{total_streaks}** Active Streakers\n🔥 **Page {page}/{total_pages}**\n🎯 **Never Give Up!**",
                inline=True
            )
            
            embed.add_field(
                name="💡 **Streak Tips**",
                value="📅 Use `/daily` every day\n🔔 Set phone reminders\n🏆 Build the longest streak!",
                inline=True
            )
        
        embed.set_footer(text="🔥 Streak Leaderboard • Consistency is key! • ⚡ Never break the chain!")
        
        return embed

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

    # REMOVED: rank command - now use /profile
    @app_commands.command(name="rank", description="📊 View your rank (use /profile instead)")
    async def rank_redirect(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔄 **Command Updated**",
            description="The rank command has been integrated into our profile system!",
            color=0x7c3aed
        )
        embed.add_field(
            name="✨ **New Command**",
            value="Use `/profile` to see your complete stats including rank!",
            inline=False
        )
        embed.add_field(
            name="🎉 **What's Better**",
            value="• Complete overview of your progress\n• XP, level, and rank all in one place\n• Job information and streak data\n• Much more detailed information",
            inline=False
        )
        embed.set_footer(text="💫 This command will be removed soon")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="🏆 View all server leaderboards with elegant pagination")
    @app_commands.describe(
        type="Choose leaderboard type",
        page="Page number (default: 1)"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="🥇 XP & Levels", value="xp"),
        app_commands.Choice(name="🍪 Cookies", value="cookies"),
        app_commands.Choice(name="🪙 Coins", value="coins"),
        app_commands.Choice(name="🔥 Daily Streaks", value="streak")
    ])
    async def unified_leaderboard(self, interaction: discord.Interaction, 
                                type: str = "xp", page: int = 1):
        try:
            if page < 1:
                page = 1

            # Get leaderboard data based on type
            if type == "xp":
                all_users = db.get_leaderboard('xp')
                total_pages = (len(all_users) + 10 - 1) // 10
                embed_func = self.create_level_leaderboard_embed
                no_data_msg = "❌ No XP data available! Start chatting to appear on the leaderboard."
            elif type == "cookies":
                all_users = db.get_leaderboard('cookies')
                total_pages = (len(all_users) + 10 - 1) // 10
                from cogs.cookies import Cookies
                cookies_cog = self.bot.get_cog('Cookies')
                embed_func = cookies_cog.create_cookie_leaderboard_embed if cookies_cog else None
                no_data_msg = "❌ No cookie data available! Start collecting cookies to appear here."
            elif type == "coins":
                all_users = db.get_leaderboard('coins')
                total_pages = (len(all_users) + 10 - 1) // 10
                from cogs.economy import Economy
                economy_cog = self.bot.get_cog('Economy')
                embed_func = economy_cog.create_coin_leaderboard_embed if economy_cog else None
                no_data_msg = "❌ No coin data available! Use `/work` to start earning coins."
            elif type == "streak":
                streak_data = db.get_streak_leaderboard(page, 10)
                total_pages = streak_data['total_pages']
                embed_func = self.create_streak_leaderboard_embed
                no_data_msg = "❌ No streak data available! Use `/daily` to start your streak."
                all_users = streak_data['users']

            # Validate page number
            if page > total_pages and total_pages > 0:
                error_embed = discord.Embed(
                    title="❌ Page Not Found",
                    description=f"Page **{page}** doesn't exist! Maximum page: **{total_pages}**",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Check if data exists
            if not all_users:
                error_embed = discord.Embed(
                    title="📊 No Data Available",
                    description=no_data_msg,
                    color=0xff9966
                )
                error_embed.add_field(
                    name="💡 Get Started",
                    value="Be the first to appear on this leaderboard!",
                    inline=False
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Create embed
            if embed_func:
                embed = await embed_func(page)
            else:
                error_embed = discord.Embed(
                    title="❌ System Error",
                    description="Leaderboard system temporarily unavailable.",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return

            # Add elegant branding
            embed.set_footer(text="💫 Unified Leaderboard System • Use the buttons to navigate")
            
            # Create pagination view
            view = PaginationView(type, total_pages, page, self.bot)
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Oops!",
                description="Something went wrong while loading the leaderboard. Please try again.",
                color=0xff6b6b
            )
            error_embed.set_footer(text="If this persists, contact an administrator")
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)

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
            last_work = user_data.get('last_work', 0)
            level = self.calculate_level_from_xp(xp)
            
            # Get ranks
            xp_leaderboard = db.get_leaderboard('xp')
            cookie_leaderboard = db.get_leaderboard('cookies')
            coin_leaderboard = db.get_leaderboard('coins')
            
            xp_rank = next((i + 1 for i, u in enumerate(xp_leaderboard) if u['user_id'] == target.id), 'N/A')
            cookie_rank = next((i + 1 for i, u in enumerate(cookie_leaderboard) if u['user_id'] == target.id), 'N/A')
            coin_rank = next((i + 1 for i, u in enumerate(coin_leaderboard) if u['user_id'] == target.id), 'N/A')

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
            
            # Job section - only show if user has worked
            if last_work > 0:
                job = self.get_job_title(level)
                # Check if it's been more than 7 days since last work
                current_time = datetime.now().timestamp()
                days_since_work = (current_time - last_work) / 86400
                
                if days_since_work <= 7:
                    status = "Active"
                    status_emoji = "🟢"
                elif days_since_work <= 30:
                    status = "Inactive"
                    status_emoji = "🟡"
                else:
                    status = "Retired"
                    status_emoji = "🔴"
                
                embed.add_field(
                    name="💼 Career",
                    value=f"**Job Title:** {job['name']}\n**Status:** {status_emoji} {status}\n**Level Range:** {job['min_level']}-{job['max_level']}\n**Last Worked:** <t:{int(last_work)}:R>",
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

    @app_commands.command(name="daily", description="🎁 Claim your daily XP and coin bonus with streak rewards")
    async def daily(self, interaction: discord.Interaction):
        try:
            result = db.claim_daily_bonus(interaction.user.id)
            
            if result['success']:
                embed = discord.Embed(
                    title="🎁 Daily Bonus Claimed!",
                    description=f"**XP Gained:** +{result['xp_gained']}\n**Coins Gained:** +{result['coins_gained']}\n**Streak:** {result['streak']} day(s) 🔥",
                    color=0x00d4aa,
                    timestamp=datetime.now()
                )
                
                # Add streak milestone rewards
                if result['streak'] % 7 == 0:
                    embed.add_field(
                        name="🎉 Weekly Streak Bonus!", 
                        value="You got extra rewards for your 7-day streak commitment!", 
                        inline=False
                    )
                
                if result['streak'] >= 30:
                    embed.add_field(
                        name="💎 Dedication Master",
                        value="30+ day streak! You're truly dedicated.",
                        inline=False
                    )
                
                embed.set_author(
                    name=f"{interaction.user.display_name}'s Daily Reward",
                    icon_url=interaction.user.display_avatar.url
                )
                embed.set_footer(text="💫 Daily System • Come back tomorrow for more!")
                await interaction.response.send_message(embed=embed)
            else:
                time_left = result.get('time_left', 'some time')
                embed = discord.Embed(
                    title="⏰ Daily Already Claimed",
                    description=f"You can claim your next daily bonus in **{time_left}**",
                    color=0xff9966
                )
                embed.add_field(
                    name="💡 Pro Tip",
                    value="Set a daily reminder to maximize your streak rewards!",
                    inline=False
                )
                embed.set_footer(text="💫 Patience is a virtue!")
                await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Oops!",
                description="Something went wrong claiming your daily bonus. Please try again.",
                color=0xff6b6b
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)

    # REMOVED: streaktop command - now use /leaderboard streak
    @app_commands.command(name="streaktop", description="🔥 View streak leaderboard (use /leaderboard instead)")
    async def streaktop_redirect(self, interaction: discord.Interaction, page: int = 1):
        embed = discord.Embed(
            title="🔄 Command Upgraded",
            description="The streak leaderboard is now part of our unified leaderboard system!",
            color=0x7c3aed
        )
        embed.add_field(
            name="✨ New Command",
            value="Use `/leaderboard type:🔥 Daily Streaks` for the streak leaderboard",
            inline=False
        )
        embed.add_field(
            name="🎉 Enhanced Features",
            value="• Beautiful pagination\n• Special streak badges\n• Elegant design\n• All leaderboards in one place",
            inline=False
        )
        embed.set_footer(text="💫 This old command will be removed soon")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
