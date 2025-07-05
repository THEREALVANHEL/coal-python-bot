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

class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Leveling] Loaded successfully.")

    def calculate_xp_for_level(self, level: int) -> int:
        return int(100 * (level ** 1.5))

    def calculate_level_from_xp(self, xp: int) -> int:
        return int((xp / 100) ** (2/3))

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

            embed = discord.Embed(
                title=f"📊 Rank Card - {target.display_name}",
                color=target.accent_color or 0x7289da
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            embed.add_field(name="🏆 Level", value=level, inline=True)
            embed.add_field(name="⭐ Total XP", value=f"{xp:,}", inline=True)
            embed.add_field(name="📈 Rank", value=f"#{rank}", inline=True)
            embed.add_field(name="🎯 Progress", value=f"{xp_progress}/{next_level_xp - current_level_xp} XP", inline=True)
            embed.add_field(name="🚀 XP Needed", value=f"{xp_needed:,} XP", inline=True)
            embed.add_field(name="📊 Next Level", value=level + 1, inline=True)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error getting rank data: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error getting rank data: {str(e)}", ephemeral=True)

    @app_commands.command(name="leveltop", description="Displays the top 10 users by level")
    async def leveltop(self, interaction: discord.Interaction):
        try:
            leaderboard = db.get_leaderboard('xp', limit=10)
            if not leaderboard:
                await interaction.response.send_message("❌ No leaderboard data available!", ephemeral=True)
                return

            embed = discord.Embed(
                title="🥇 Level Leaderboard - Top 10",
                color=0xffd700
            )

            leaderboard_text = []
            for i, user_data in enumerate(leaderboard, 1):
                user_id = user_data['user_id']
                xp = user_data.get('xp', 0)
                level = self.calculate_level_from_xp(xp)
                
                try:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    username = user.display_name if hasattr(user, 'display_name') else user.name
                except:
                    username = f"User {user_id}"

                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard_text.append(f"{medal} **{username}** - Level {level} ({xp:,} XP)")

            embed.description = "\n".join(leaderboard_text)
            embed.set_footer(text="Keep chatting to climb the ranks!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error getting leaderboard: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error getting leaderboard: {str(e)}", ephemeral=True)

    @app_commands.command(name="profile", description="Shows your level and cookie stats in one profile")
    @app_commands.describe(user="User to check profile for")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        try:
            user_data = db.get_user_data(target.id)
            xp = user_data.get('xp', 0)
            cookies = user_data.get('cookies', 0)
            level = self.calculate_level_from_xp(xp)
            
            # Get ranks
            xp_leaderboard = db.get_leaderboard('xp')
            cookie_leaderboard = db.get_leaderboard('cookies')
            
            xp_rank = next((i + 1 for i, u in enumerate(xp_leaderboard) if u['user_id'] == target.id), 'N/A')
            cookie_rank = next((i + 1 for i, u in enumerate(cookie_leaderboard) if u['user_id'] == target.id), 'N/A')

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
                value=f"**Level:** {level}\n**XP:** {xp:,}\n**Rank:** #{xp_rank}\n**Progress:** {progress_bar} {xp_progress}/{next_level_xp - current_level_xp}",
                inline=False
            )
            
            embed.add_field(
                name="🍪 Cookie Stats", 
                value=f"**Cookies:** {cookies:,}\n**Rank:** #{cookie_rank}",
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

            embed = discord.Embed(
                title="🎉 Level Up Announcement!",
                description=f"🎊 **{interaction.user.display_name}** has reached **Level {level}**! 🎊",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="📊 Stats", value=f"**Total XP:** {xp:,}\n**Level:** {level}", inline=True)
            embed.set_footer(text="Keep chatting to level up even more!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error announcing level: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error announcing level: {str(e)}", ephemeral=True)

    @app_commands.command(name="daily", description="Claim your daily XP bonus")
    async def daily(self, interaction: discord.Interaction):
        try:
            result = db.claim_daily_xp(interaction.user.id)
            
            if result['success']:
                embed = discord.Embed(
                    title="🎁 Daily Bonus Claimed!",
                    description=f"**XP Gained:** {result['xp_gained']}\n**Streak:** {result['streak']} day(s)",
                    color=0x00ff00
                )
                
                if result['streak'] % 7 == 0:
                    embed.add_field(name="🎉 Streak Bonus!", value="You got extra XP for your 7-day streak!", inline=False)
                
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

    @app_commands.command(name="streaktop", description="Shows the top 10 users with the highest daily streaks")
    async def streaktop(self, interaction: discord.Interaction):
        try:
            leaderboard = db.get_leaderboard('daily_streak', limit=10)
            
            if not leaderboard:
                await interaction.response.send_message("❌ No streak data available!", ephemeral=True)
                return

            embed = discord.Embed(
                title="🔥 Daily Streak Leaderboard - Top 10",
                color=0xff4500
            )

            leaderboard_text = []
            for i, user_data in enumerate(leaderboard, 1):
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
            embed.set_footer(text="Keep your daily streak alive!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error getting streak leaderboard: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error getting streak leaderboard: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
