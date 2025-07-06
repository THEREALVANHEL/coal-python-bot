import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View
import os, sys
from datetime import datetime

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

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

class LeaderboardView(View):
    def __init__(self, cog, leaderboard_type, current_page=1):
        super().__init__(timeout=300)
        self.cog = cog
        self.leaderboard_type = leaderboard_type
        self.current_page = current_page
        self.members_per_page = 10
        
        # Get total pages
        self.total_pages = self.get_total_pages()
        
        # Update button states
        self.update_buttons()

    def get_total_pages(self):
        """Get total number of pages for the leaderboard"""
        try:
            if self.leaderboard_type == "streak":
                data = db.get_streak_leaderboard(1, self.members_per_page)
                return data.get('total_pages', 1)
            else:
                # Get total count with greater than 0 for the field
                data = db.get_paginated_leaderboard(self.leaderboard_type, 1, self.members_per_page)
                return data.get('total_pages', 1)
        except:
            return 1

    def update_buttons(self):
        """Update button states based on current page"""
        self.first_page.disabled = (self.current_page == 1)
        self.previous_page.disabled = (self.current_page == 1)
        self.next_page.disabled = (self.current_page >= self.total_pages)
        self.last_page.disabled = (self.current_page >= self.total_pages)

    @discord.ui.button(label="⏪ First", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(interaction, 1)

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(interaction, max(1, self.current_page - 1))

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(interaction, min(self.total_pages, self.current_page + 1))

    @discord.ui.button(label="⏩ Last", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.change_page(interaction, self.total_pages)

    async def change_page(self, interaction: discord.Interaction, new_page: int):
        """Change to a new page"""
        try:
            self.current_page = new_page
            self.update_buttons()
            
            # Get new embed
            embed = await self.cog.create_leaderboard_embed(self.leaderboard_type, new_page, self.members_per_page)
            
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Error changing page: {e}")
            error_embed = discord.Embed(
                title="❌ Error",
                description="Failed to update leaderboard page.",
                color=0xff6b6b
            )
            try:
                await interaction.response.edit_message(embed=error_embed, view=self)
            except:
                await interaction.followup.send(embed=error_embed, ephemeral=True)

class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Leveling] Loaded successfully.")

    def calculate_xp_for_level(self, level: int) -> int:
        """Moderately reduced XP requirement per level - easier but not too easy"""
        if level <= 10:
            return int(130 * (level ** 2))  # Reduced from 200 to 130 (35% reduction)
        elif level <= 50:
            return int(195 * (level ** 2.2))  # Reduced from 300 to 195 (35% reduction)
        elif level <= 100:
            return int(325 * (level ** 2.5))  # Reduced from 500 to 325 (35% reduction)
        else:
            return int(650 * (level ** 2.8))  # Reduced from 1000 to 650 (35% reduction)

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
        """Update user's XP-based roles - only give highest role, remove all others"""
        try:
            guild = member.guild
            
            # Find the highest role the user qualifies for
            highest_role_id = None
            highest_level_req = 0
            
            for level_req, role_id in XP_ROLES.items():
                if level >= level_req and level_req > highest_level_req:
                    highest_level_req = level_req
                    highest_role_id = role_id
            
            # Get all XP roles
            all_xp_roles = []
            for role_id in XP_ROLES.values():
                role = guild.get_role(role_id)
                if role:
                    all_xp_roles.append(role)
            
            # Remove all XP roles first
            roles_to_remove = [role for role in all_xp_roles if role in member.roles]
            if roles_to_remove:
                try:
                    await member.remove_roles(*roles_to_remove, reason="XP level role update - clearing old roles")
                    print(f"[Leveling] Removed {len(roles_to_remove)} XP roles from {member.display_name}")
                except Exception as e:
                    print(f"[Leveling] Error removing XP roles from {member.display_name}: {e}")
            
            # Add only the highest role if user qualifies for one
            if highest_role_id:
                highest_role = guild.get_role(highest_role_id)
                if highest_role:
                    try:
                        await member.add_roles(highest_role, reason=f"XP level role update - level {level}")
                        print(f"[Leveling] Gave {highest_role.name} role to {member.display_name} (level {level})")
                    except Exception as e:
                        print(f"[Leveling] Error adding XP role {highest_role.name} to {member.display_name}: {e}")
                        
        except Exception as e:
            print(f"[Leveling] Error updating XP roles for {member}: {e}")

    async def update_cookie_roles(self, member: discord.Member, cookies: int):
        """Update user's cookie-based roles - only give highest role, remove all others"""
        try:
            guild = member.guild
            
            # Find the highest role the user qualifies for
            highest_role_id = None
            highest_cookie_req = 0
            
            for cookie_req, role_id in COOKIE_ROLES.items():
                if cookies >= cookie_req and cookie_req > highest_cookie_req:
                    highest_cookie_req = cookie_req
                    highest_role_id = role_id
            
            # Get all cookie roles
            all_cookie_roles = []
            for role_id in COOKIE_ROLES.values():
                role = guild.get_role(role_id)
                if role:
                    all_cookie_roles.append(role)
            
            # Remove all cookie roles first
            roles_to_remove = [role for role in all_cookie_roles if role in member.roles]
            if roles_to_remove:
                try:
                    await member.remove_roles(*roles_to_remove, reason="Cookie milestone role update - clearing old roles")
                    print(f"[Leveling] Removed {len(roles_to_remove)} cookie roles from {member.display_name}")
                except Exception as e:
                    print(f"[Leveling] Error removing cookie roles from {member.display_name}: {e}")
            
            # Add only the highest role if user qualifies for one
            if highest_role_id:
                highest_role = guild.get_role(highest_role_id)
                if highest_role:
                    try:
                        await member.add_roles(highest_role, reason=f"Cookie milestone role update - {cookies} cookies")
                        print(f"[Leveling] Gave {highest_role.name} role to {member.display_name} ({cookies} cookies)")
                    except Exception as e:
                        print(f"[Leveling] Error adding cookie role {highest_role.name} to {member.display_name}: {e}")
                        
        except Exception as e:
            print(f"[Leveling] Error updating cookie roles for {member}: {e}")

    async def create_leaderboard_embed(self, leaderboard_type: str, page: int, members_per_page: int = 10):
        """Create leaderboard embed for any type"""
        try:
            if leaderboard_type == "xp":
                return await self.create_xp_leaderboard_embed(page, members_per_page)
            elif leaderboard_type == "cookies":
                return await self.create_cookies_leaderboard_embed(page, members_per_page)
            elif leaderboard_type == "coins":
                return await self.create_coins_leaderboard_embed(page, members_per_page)
            elif leaderboard_type == "streak":
                return await self.create_streak_leaderboard_embed(page, members_per_page)
            else:
                raise ValueError(f"Unknown leaderboard type: {leaderboard_type}")
        except Exception as e:
            print(f"Error creating leaderboard embed: {e}")
            return discord.Embed(
                title="❌ Error",
                description="Failed to load leaderboard data.",
                color=0xff6b6b
            )

    async def create_xp_leaderboard_embed(self, page: int, members_per_page: int = 10):
        """Create XP leaderboard embed"""
        leaderboard_data = db.get_paginated_leaderboard('xp', page, members_per_page)
        users = leaderboard_data.get('users', [])
        total_pages = leaderboard_data.get('total_pages', 1)
        total_users = leaderboard_data.get('total_users', 0)
        
        embed = discord.Embed(
            title="🏆 XP Leaderboard",
            color=0x7c3aed,
            timestamp=datetime.now()
        )

        if not users:
            embed.description = "❌ No XP data available! Start chatting to appear on the leaderboard."
            return embed

        leaderboard_text = []
        start_rank = (page - 1) * members_per_page + 1

        for i, user_data in enumerate(users):
            rank = start_rank + i
            user_id = user_data.get('user_id')
            xp = user_data.get('xp', 0)
            
            try:
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                username = user.display_name if hasattr(user, 'display_name') else user.name
            except:
                username = f"User {user_id}"

            level = self.calculate_level_from_xp(xp)
            leaderboard_text.append(f"**#{rank}** {username} - **{xp:,} XP** (Level {level})")

        embed.description = "\n".join(leaderboard_text)
        embed.set_footer(text=f"Page {page}/{total_pages} • Showing {len(users)} of {total_users} users")
        
        return embed

    async def create_cookies_leaderboard_embed(self, page: int, members_per_page: int = 10):
        """Create cookies leaderboard embed"""
        leaderboard_data = db.get_paginated_leaderboard('cookies', page, members_per_page)
        users = leaderboard_data.get('users', [])
        total_pages = leaderboard_data.get('total_pages', 1)
        total_users = leaderboard_data.get('total_users', 0)
        
        embed = discord.Embed(
            title="🍪 Cookie Leaderboard",
            color=0xdaa520,
            timestamp=datetime.now()
        )

        if not users:
            embed.description = "❌ No cookie data available! Start collecting cookies to appear here."
            return embed

        leaderboard_text = []
        start_rank = (page - 1) * members_per_page + 1

        for i, user_data in enumerate(users):
            rank = start_rank + i
            user_id = user_data.get('user_id')
            cookies = user_data.get('cookies', 0)
            
            try:
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                username = user.display_name if hasattr(user, 'display_name') else user.name
            except:
                username = f"User {user_id}"

            leaderboard_text.append(f"**#{rank}** {username} - **{cookies:,} 🍪**")

        embed.description = "\n".join(leaderboard_text)
        embed.set_footer(text=f"Page {page}/{total_pages} • Showing {len(users)} of {total_users} users")
        
        return embed

    async def create_coins_leaderboard_embed(self, page: int, members_per_page: int = 10):
        """Create coins leaderboard embed"""
        leaderboard_data = db.get_paginated_leaderboard('coins', page, members_per_page)
        users = leaderboard_data.get('users', [])
        total_pages = leaderboard_data.get('total_pages', 1)
        total_users = leaderboard_data.get('total_users', 0)
        
        embed = discord.Embed(
            title="🪙 Coin Leaderboard",
            color=0xffd700,
            timestamp=datetime.now()
        )

        if not users:
            embed.description = "❌ No coin data available! Use `/work` to start earning coins."
            return embed

        leaderboard_text = []
        start_rank = (page - 1) * members_per_page + 1

        for i, user_data in enumerate(users):
            rank = start_rank + i
            user_id = user_data.get('user_id')
            coins = user_data.get('coins', 0)
            
            try:
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                username = user.display_name if hasattr(user, 'display_name') else user.name
            except:
                username = f"User {user_id}"

            leaderboard_text.append(f"**#{rank}** {username} - **{coins:,} 🪙**")

        embed.description = "\n".join(leaderboard_text)
        embed.set_footer(text=f"Page {page}/{total_pages} • Showing {len(users)} of {total_users} users")
        
        return embed

    async def create_streak_leaderboard_embed(self, page: int, members_per_page: int = 10):
        """Create streak leaderboard embed"""
        streak_data = db.get_streak_leaderboard(page, members_per_page)
        users = streak_data.get('users', [])
        total_pages = streak_data.get('total_pages', 1)
        
        embed = discord.Embed(
            title="🔥 Daily Streak Leaderboard",
            color=0xff4500,
            timestamp=datetime.now()
        )

        if not users:
            embed.description = "❌ No streak data available! Use `/daily` to start your streak."
            return embed

        leaderboard_text = []
        start_rank = (page - 1) * members_per_page + 1

        for i, user_data in enumerate(users):
            rank = start_rank + i
            user_id = user_data.get('user_id')
            streak = user_data.get('daily_streak', 0)
            
            try:
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                username = user.display_name if hasattr(user, 'display_name') else user.name
            except:
                username = f"User {user_id}"

            streak_emoji = "🔥" * min(streak // 7, 5)  # Fire emoji for every 7 days
            leaderboard_text.append(f"**#{rank}** {username} - **{streak} days** {streak_emoji}")

        embed.description = "\n".join(leaderboard_text)
        embed.set_footer(text=f"Page {page}/{total_pages} • Showing {len(users)} users")
        
        return embed

    @app_commands.command(name="leaderboard", description="🏆 View all server leaderboards with working pagination")
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
    async def leaderboard(self, interaction: discord.Interaction, type: str = "xp", page: int = 1):
        """Fixed leaderboard command with proper pagination"""
        try:
            if page < 1:
                page = 1
                
            # Create the leaderboard embed
            embed = await self.create_leaderboard_embed(type, page, 10)
            
            # Create pagination view
            view = LeaderboardView(self, type, page)
            
            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            print(f"Leaderboard error: {e}")
            error_embed = discord.Embed(
                title="❌ Leaderboard Error",
                description="Something went wrong loading the leaderboard. Please try again.",
                color=0xff6b6b
            )
            
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
                value=f"**Level:** {level}\n**Rank:** #{xp_rank}\n**Progress:** {progress_bar} {xp_progress:,}/{next_level_xp - current_level_xp:,}",
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
                await interaction.response.send_message(embed=embed)

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

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
