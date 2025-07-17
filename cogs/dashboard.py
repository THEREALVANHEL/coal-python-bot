import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
import os, sys
import asyncio
import random
from typing import Dict, List
from datetime import datetime, timedelta

# Matplotlib imports with fallback
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import io
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib not available - charts will be disabled")

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class Dashboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    def create_progress_chart(self, user_data: Dict, chart_type: str = "xp") -> io.BytesIO:
        """Create progress charts for users"""
        if not MATPLOTLIB_AVAILABLE:
            return None
            
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if chart_type == "xp":
                # Mock data for demonstration - in real implementation, track daily XP
                days = list(range(30))
                xp_progress = [user_data.get('xp', 0) * (i + 1) / 30 for i in days]
                
                ax.plot(days, xp_progress, color='#7289da', linewidth=3, marker='o', markersize=4)
                ax.set_title('XP Progress (Last 30 Days)', color='white', fontsize=16, fontweight='bold')
                ax.set_xlabel('Days Ago', color='white')
                ax.set_ylabel('Total XP', color='white')
                ax.grid(True, alpha=0.3)
                
            elif chart_type == "coins":
                days = list(range(30))
                coin_progress = [user_data.get('coins', 0) * (i + 1) / 30 for i in days]
                
                ax.plot(days, coin_progress, color='#f1c40f', linewidth=3, marker='s', markersize=4)
                ax.set_title('Coin Progress (Last 30 Days)', color='white', fontsize=16, fontweight='bold')
                ax.set_xlabel('Days Ago', color='white')
                ax.set_ylabel('Total Coins', color='white')
                ax.grid(True, alpha=0.3)
                
            elif chart_type == "activity":
                hours = list(range(24))
                # Mock activity data - message frequency by hour
                activity = [abs(12 - abs(h - 12)) + random.randint(0, 5) for h in hours]
                
                ax.bar(hours, activity, color='#2ecc71', alpha=0.8)
                ax.set_title('Daily Activity Pattern', color='white', fontsize=16, fontweight='bold')
                ax.set_xlabel('Hour of Day', color='white')
                ax.set_ylabel('Messages Sent', color='white')
                ax.grid(True, alpha=0.3)
            
            # Style the chart
            ax.tick_params(colors='white')
            fig.patch.set_facecolor('#2c2f33')
            ax.set_facecolor('#36393f')
            
            # Save to BytesIO
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', facecolor='#2c2f33')
            buffer.seek(0)
            plt.close()
            
            return buffer
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None

    @app_commands.command(name="dashboard", description="📊 View your comprehensive personal dashboard")
    async def dashboard(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        user_data = db.get_user_data(target_user.id)
        
        # Calculate additional stats
        level = self.calculate_level_from_xp(user_data.get('xp', 0))
        xp_for_next = self.calculate_xp_for_level(level + 1)
        current_xp = user_data.get('xp', 0)
        xp_for_current = self.calculate_xp_for_level(level)
        xp_progress = current_xp - xp_for_current
        xp_needed = xp_for_next - current_xp
        
        # Get job info
        job_info = self.get_user_job_info(target_user.id)
        
        class DashboardView(View):
            def __init__(self, dashboard_cog, user_data, target_user):
                super().__init__(timeout=300)
                self.dashboard_cog = dashboard_cog
                self.user_data = user_data
                self.target_user = target_user
                self.current_page = "overview"
                
            @discord.ui.button(label="📊 Overview", style=discord.ButtonStyle.primary, row=0)
            async def overview_page(self, button_interaction: discord.Interaction, button: Button):
                await self.show_overview(button_interaction)
                
            @discord.ui.button(label="📈 Progress", style=discord.ButtonStyle.secondary, row=0)
            async def progress_page(self, button_interaction: discord.Interaction, button: Button):
                await self.show_progress(button_interaction)
                
            @discord.ui.button(label="🎮 Gaming", style=discord.ButtonStyle.secondary, row=0)
            async def gaming_page(self, button_interaction: discord.Interaction, button: Button):
                await self.show_gaming_stats(button_interaction)
                
            @discord.ui.button(label="💼 Work", style=discord.ButtonStyle.secondary, row=0)
            async def work_page(self, button_interaction: discord.Interaction, button: Button):
                await self.show_work_stats(button_interaction)
                
            @discord.ui.button(label="🏆 Achievements", style=discord.ButtonStyle.secondary, row=1)
            async def achievements_page(self, button_interaction: discord.Interaction, button: Button):
                await self.show_achievements(button_interaction)
                
            async def show_overview(self, button_interaction: discord.Interaction):
                embed = discord.Embed(
                    title=f"📊 {self.target_user.display_name}'s Dashboard",
                    description="**📈 Quick Overview**",
                    color=0x3498db
                )
                
                # Basic stats
                embed.add_field(
                    name="🎯 Level Progress",
                    value=f"**Level:** {level}\n**XP:** {current_xp:,}\n**Next Level:** {xp_needed:,} XP needed",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Economy",
                    value=f"**Coins:** {user_data.get('coins', 0):,}\n**Cookies:** {user_data.get('cookies', 0):,}\n**Daily Streak:** {user_data.get('daily_streak', 0)}",
                    inline=True
                )
                
                embed.add_field(
                    name="💼 Career",
                    value=f"**Job:** {job_info.get('title', 'Unemployed')}\n**Works Done:** {job_info.get('total_works', 0)}\n**Success Rate:** {job_info.get('success_rate', 0)}%",
                    inline=True
                )
                
                # Activity summary
                last_active = user_data.get('last_message_time', 0)
                if last_active:
                    last_seen = datetime.fromtimestamp(last_active)
                    time_diff = datetime.now() - last_seen
                    if time_diff.days > 0:
                        activity_text = f"{time_diff.days} days ago"
                    elif time_diff.seconds > 3600:
                        activity_text = f"{time_diff.seconds // 3600} hours ago"
                    else:
                        activity_text = f"{time_diff.seconds // 60} minutes ago"
                else:
                    activity_text = "Never"
                
                embed.add_field(
                    name="⏰ Activity",
                    value=f"**Last Seen:** {activity_text}\n**Messages Today:** {self.get_daily_messages(self.target_user.id)}\n**Join Date:** {self.target_user.joined_at.strftime('%B %d, %Y') if self.target_user.joined_at else 'Unknown'}",
                    inline=False
                )
                
                embed.set_thumbnail(url=self.target_user.display_avatar.url)
                embed.timestamp = datetime.now()
                
                await button_interaction.response.edit_message(embed=embed, view=self)
                
            async def show_progress(self, button_interaction: discord.Interaction):
                await button_interaction.response.defer()
                
                embed = discord.Embed(
                    title=f"📈 {self.target_user.display_name}'s Progress",
                    description="**🚀 Growth Analytics**",
                    color=0x2ecc71
                )
                
                # Progress bars using Unicode
                xp_bar = self.create_progress_bar(xp_progress, xp_for_next - xp_for_current)
                
                embed.add_field(
                    name="🎯 Level Progress",
                    value=f"Level {level} → Level {level + 1}\n{xp_bar}\n{xp_progress:,}/{xp_for_next - xp_for_current:,} XP",
                    inline=False
                )
                
                # Ranking info
                rank_info = self.get_user_ranking(self.target_user.id)
                embed.add_field(
                    name="🏆 Server Rankings",
                    value=f"**XP Rank:** #{rank_info.get('xp_rank', 'N/A')}\n**Coin Rank:** #{rank_info.get('coin_rank', 'N/A')}\n**Cookie Rank:** #{rank_info.get('cookie_rank', 'N/A')}",
                    inline=True
                )
                
                # Goals and milestones
                next_milestones = self.get_next_milestones(user_data)
                embed.add_field(
                    name="🎯 Next Milestones",
                    value=next_milestones,
                    inline=True
                )
                
                # Try to create and attach chart
                chart_buffer = self.dashboard_cog.create_progress_chart(user_data, "xp")
                if chart_buffer:
                    file = discord.File(chart_buffer, filename="progress_chart.png")
                    embed.set_image(url="attachment://progress_chart.png")
                    await button_interaction.followup.edit_message(interaction.message.id, embed=embed, view=self, attachments=[file])
                else:
                    await button_interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
                
            async def show_gaming_stats(self, button_interaction: discord.Interaction):
                embed = discord.Embed(
                    title=f"🎮 {self.target_user.display_name}'s Gaming Stats",
                    description="**🏆 Minigame Performance**",
                    color=0x9b59b6
                )
                
                # Get gaming stats from database
                gaming_stats = self.get_gaming_stats(self.target_user.id)
                
                embed.add_field(
                    name="🧠 Trivia",
                    value=f"**Played:** {gaming_stats.get('trivia_played', 0)}\n**Correct:** {gaming_stats.get('trivia_correct', 0)}\n**Win Rate:** {gaming_stats.get('trivia_rate', 0)}%",
                    inline=True
                )
                
                embed.add_field(
                    name="🪨 Rock Paper Scissors",
                    value=f"**Played:** {gaming_stats.get('rps_played', 0)}\n**Won:** {gaming_stats.get('rps_won', 0)}\n**Win Rate:** {gaming_stats.get('rps_rate', 0)}%",
                    inline=True
                )
                
                embed.add_field(
                    name="🎰 Slots",
                    value=f"**Spins:** {gaming_stats.get('slots_played', 0)}\n**Jackpots:** {gaming_stats.get('slots_jackpots', 0)}\n**Total Won:** {gaming_stats.get('slots_won', 0):,} coins",
                    inline=True
                )
                
                embed.add_field(
                    name="🔤 Word Chain",
                    value=f"**Completed:** {gaming_stats.get('wordchain_completed', 0)}\n**Best Word:** {gaming_stats.get('longest_word', 'None')}\n**Coins Earned:** {gaming_stats.get('wordchain_coins', 0):,}",
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 Daily Challenges",
                    value=f"**Completed:** {gaming_stats.get('challenges_completed', 0)}\n**Current Streak:** {gaming_stats.get('challenge_streak', 0)}\n**Best Streak:** {gaming_stats.get('best_streak', 0)}",
                    inline=True
                )
                
                # Total gaming earnings
                total_earned = sum([
                    gaming_stats.get('trivia_coins', 0),
                    gaming_stats.get('rps_coins', 0),
                    gaming_stats.get('slots_won', 0),
                    gaming_stats.get('wordchain_coins', 0)
                ])
                
                embed.add_field(
                    name="💎 Gaming Summary",
                    value=f"**Total Games:** {gaming_stats.get('total_games', 0)}\n**Coins from Gaming:** {total_earned:,}\n**Favorite Game:** {gaming_stats.get('favorite_game', 'None')}",
                    inline=False
                )
                
                await button_interaction.response.edit_message(embed=embed, view=self)
                
            async def show_work_stats(self, button_interaction: discord.Interaction):
                embed = discord.Embed(
                    title=f"💼 {self.target_user.display_name}'s Work Stats",
                    description="**📈 Career Analytics**",
                    color=0xf39c12
                )
                
                # Get work stats
                work_stats = self.get_work_stats(self.target_user.id)
                
                embed.add_field(
                    name="🏢 Current Position",
                    value=f"**Job:** {job_info.get('title', 'Unemployed')}\n**Tier:** {job_info.get('tier', 'None')}\n**Experience:** {job_info.get('experience', 0)} points",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Performance",
                    value=f"**Total Works:** {work_stats.get('total_works', 0)}\n**Successful:** {work_stats.get('successful_works', 0)}\n**Success Rate:** {work_stats.get('success_rate', 0)}%",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 Earnings",
                    value=f"**Total Earned:** {work_stats.get('total_earned', 0):,} coins\n**Average Per Work:** {work_stats.get('avg_per_work', 0):,} coins\n**Best Single Pay:** {work_stats.get('best_pay', 0):,} coins",
                    inline=True
                )
                
                # Work frequency
                last_work = work_stats.get('last_work', 0)
                if last_work:
                    time_since = datetime.now().timestamp() - last_work
                    if time_since < 3600:
                        last_work_text = f"{int(time_since // 60)} minutes ago"
                    elif time_since < 86400:
                        last_work_text = f"{int(time_since // 3600)} hours ago"
                    else:
                        last_work_text = f"{int(time_since // 86400)} days ago"
                else:
                    last_work_text = "Never"
                
                embed.add_field(
                    name="⏰ Work Schedule",
                    value=f"**Last Work:** {last_work_text}\n**Works This Week:** {work_stats.get('week_works', 0)}\n**Consistency:** {work_stats.get('consistency', 0)}%",
                    inline=True
                )
                
                # Career progression
                embed.add_field(
                    name="🚀 Career Growth",
                    value=f"**Promotions:** {work_stats.get('promotions', 0)}\n**Time in Role:** {work_stats.get('time_in_role', 0)} days\n**Next Promotion:** {work_stats.get('next_promotion', 'Available')}",
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 Work Achievements",
                    value=f"**Perfect Week:** {work_stats.get('perfect_weeks', 0)}\n**Work Streak:** {work_stats.get('work_streak', 0)}\n**Efficiency Score:** {work_stats.get('efficiency', 0)}/100",
                    inline=True
                )
                
                await button_interaction.response.edit_message(embed=embed, view=self)
                
            async def show_achievements(self, button_interaction: discord.Interaction):
                embed = discord.Embed(
                    title=f"🏆 {self.target_user.display_name}'s Achievements",
                    description="**🎖️ Unlocked Badges & Milestones**",
                    color=0xe74c3c
                )
                
                # Get achievements
                achievements = self.get_user_achievements(self.target_user.id)
                
                # Recent achievements
                recent = achievements.get('recent', [])
                if recent:
                    recent_text = "\n".join([f"🏅 {ach['name']}" for ach in recent[:5]])
                else:
                    recent_text = "No recent achievements"
                
                embed.add_field(
                    name="🆕 Recent Achievements",
                    value=recent_text,
                    inline=True
                )
                
                # Achievement categories
                categories = {
                    "🎯": achievements.get('leveling', []),
                    "💰": achievements.get('economy', []),
                    "🎮": achievements.get('gaming', []),
                    "💼": achievements.get('work', []),
                    "🎊": achievements.get('special', [])
                }
                
                for emoji, category_achievements in categories.items():
                    if category_achievements:
                        category_text = f"{len(category_achievements)} unlocked"
                        embed.add_field(
                            name=f"{emoji} Category",
                            value=category_text,
                            inline=True
                        )
                
                # Achievement progress
                total_achievements = sum(len(cat) for cat in categories.values())
                max_achievements = 50  # Total possible achievements
                progress_bar = self.create_progress_bar(total_achievements, max_achievements)
                
                embed.add_field(
                    name="📊 Overall Progress",
                    value=f"{progress_bar}\n{total_achievements}/{max_achievements} achievements",
                    inline=False
                )
                
                # Next achievements to unlock
                next_achievements = self.get_next_achievements(self.target_user.id)
                if next_achievements:
                    next_text = "\n".join([f"🔒 {ach['name']} - {ach['requirement']}" for ach in next_achievements[:3]])
                    embed.add_field(
                        name="🎯 Coming Up Next",
                        value=next_text,
                        inline=False
                    )
                
                await button_interaction.response.edit_message(embed=embed, view=self)
                
            def create_progress_bar(self, current: int, maximum: int, length: int = 20) -> str:
                """Create a Unicode progress bar"""
                if maximum == 0:
                    return "▱" * length
                    
                percentage = current / maximum
                filled_length = int(length * percentage)
                
                bar = "▰" * filled_length + "▱" * (length - filled_length)
                return f"{bar} {percentage:.1%}"
                
            def get_daily_messages(self, user_id: int) -> int:
                """Get user's message count for today"""
                # This would need to be tracked in the database
                return 42  # Mock data
                
            def get_user_ranking(self, user_id: int) -> Dict:
                """Get user's ranking in various categories"""
                # Mock data - implement actual ranking system
                return {
                    "xp_rank": 15,
                    "coin_rank": 8,
                    "cookie_rank": 23
                }
                
            def get_next_milestones(self, user_data: Dict) -> str:
                """Get next milestones for the user"""
                milestones = []
                
                # Level milestones
                current_level = self.dashboard_cog.calculate_level_from_xp(user_data.get('xp', 0))
                if current_level < 100:
                    next_milestone = ((current_level // 10) + 1) * 10
                    milestones.append(f"Level {next_milestone}")
                
                # Coin milestones
                coins = user_data.get('coins', 0)
                coin_milestones = [1000, 5000, 10000, 25000, 50000, 100000]
                for milestone in coin_milestones:
                    if coins < milestone:
                        milestones.append(f"{milestone:,} coins")
                        break
                
                return "\n".join([f"🎯 {m}" for m in milestones[:3]]) if milestones else "All major milestones reached!"
                
            def get_gaming_stats(self, user_id: int) -> Dict:
                """Get user's gaming statistics"""
                # Mock data - implement actual tracking
                return {
                    "trivia_played": 45, "trivia_correct": 32, "trivia_rate": 71,
                    "rps_played": 28, "rps_won": 15, "rps_rate": 54,
                    "slots_played": 67, "slots_jackpots": 3, "slots_won": 1250,
                    "wordchain_completed": 23, "longest_word": "programming", "wordchain_coins": 487,
                    "challenges_completed": 12, "challenge_streak": 3, "best_streak": 7,
                    "total_games": 163, "favorite_game": "Trivia"
                }
                
            def get_work_stats(self, user_id: int) -> Dict:
                """Get user's work statistics"""
                # Mock data - implement actual tracking
                return {
                    "total_works": 156, "successful_works": 142, "success_rate": 91,
                    "total_earned": 45000, "avg_per_work": 289, "best_pay": 750,
                    "last_work": datetime.now().timestamp() - 3600,
                    "week_works": 14, "consistency": 85,
                    "promotions": 3, "time_in_role": 45, "next_promotion": "Available",
                    "perfect_weeks": 6, "work_streak": 12, "efficiency": 87
                }
                
            def get_user_achievements(self, user_id: int) -> Dict:
                """Get user's achievements"""
                # Mock data - implement actual achievement system
                return {
                    "recent": [
                        {"name": "Level 50 Reached", "date": "2 days ago"},
                        {"name": "Trivia Master", "date": "1 week ago"},
                        {"name": "First Jackpot", "date": "2 weeks ago"}
                    ],
                    "leveling": ["First Message", "Level 10", "Level 25", "Level 50"],
                    "economy": ["First Coin", "1K Coins", "5K Coins", "Big Spender"],
                    "gaming": ["Trivia Master", "Lucky Winner", "Word Wizard"],
                    "work": ["First Job", "Promotion", "Perfect Week"],
                    "special": ["Early Adopter", "Community Helper"]
                }
                
            def get_next_achievements(self, user_id: int) -> List[Dict]:
                """Get next achievements user can unlock"""
                return [
                    {"name": "Level 75", "requirement": "Reach level 75"},
                    {"name": "10K Coins", "requirement": "Accumulate 10,000 coins"},
                    {"name": "Slot Legend", "requirement": "Win 5 jackpots"}
                ]
        
        # Initial overview embed
        embed = discord.Embed(
            title=f"📊 {target_user.display_name}'s Dashboard",
            description="**📈 Loading your personalized dashboard...**",
            color=0x3498db
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        view = DashboardView(self, user_data, target_user)
        await interaction.response.send_message(embed=embed, view=view)
        
        # Automatically show overview
        await asyncio.sleep(0.5)
        try:
            await view.show_overview(interaction)
        except:
            pass

    def calculate_level_from_xp(self, xp: int) -> int:
        """Calculate level from XP - match the events.py implementation"""
        level = 0
        while self.calculate_xp_for_level(level + 1) <= xp:
            level += 1
        return level

    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP requirement for level - match the events.py implementation"""
        if level <= 10:
            return int(75 * (level ** 1.6))
        elif level <= 50:
            return int(120 * (level ** 1.9))
        elif level <= 100:
            return int(150 * (level ** 2.1))
        else:
            return int(200 * (level ** 2.3))

    def get_user_job_info(self, user_id: int) -> Dict:
        """Get user's job information"""
        # Mock data - integrate with actual job system
        return {
            "title": "Senior Developer",
            "tier": "Professional",
            "experience": 1250,
            "total_works": 156,
            "success_rate": 91
        }

async def setup(bot: commands.Bot):
    await bot.add_cog(Dashboard(bot))