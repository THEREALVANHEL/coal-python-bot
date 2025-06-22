import discord
from discord.ext import commands
from discord import app_commands
import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily", description="Claim your daily XP and build a streak!")
    @app_commands.guilds(guild_obj)
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        daily_data = db.get_daily_data(user_id)
        
        # Cooldown: 22 hours
        cooldown_hours = 22 
        
        if daily_data and 'last_checkin' in daily_data:
            last_checkin = daily_data['last_checkin']
            time_since_checkin = datetime.utcnow() - last_checkin
            
            if time_since_checkin < timedelta(hours=cooldown_hours):
                time_left = timedelta(hours=cooldown_hours) - time_since_checkin
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                await interaction.response.send_message(f"You've already claimed your daily reward! Try again in **{hours}h {minutes}m**.", ephemeral=True)
                return

        # --- Check and update streak ---
        current_streak = daily_data.get('streak', 0) if daily_data else 0
        
        # If last check-in was more than 44 hours ago (22*2), reset streak
        if daily_data and (datetime.utcnow() - daily_data['last_checkin']) > timedelta(hours=cooldown_hours * 2):
            new_streak = 1
        else:
            new_streak = current_streak + 1

        # --- Calculate reward ---
        reward = 20
        bonus_message = ""
        
        if new_streak == 7:
            bonus = 50
            reward += bonus
            bonus_message = f"🎉 You've reached a 7-day streak! You get a bonus of **{bonus} XP**."
            # Reset streak after claiming the bonus
            db.update_daily_checkin(user_id, 0) 
        else:
            db.update_daily_checkin(user_id, new_streak)

        db.update_user_xp(user_id, reward)

        leveling_cog = self.bot.get_cog("Leveling")
        if leveling_cog:
            user_data = db.get_user_level_data(user_id)
            user_level = user_data.get('level', 0)
            user_xp = user_data.get('xp', 0)
            xp_needed = leveling_cog.get_xp_for_level(user_level)
            if user_xp >= xp_needed:
                 # Announce level up
                level_channel_id = db.get_channel(interaction.guild.id, "leveling")
                if level_channel_id:
                    level_channel = interaction.guild.get_channel(level_channel_id)
                    if level_channel:
                        embed = discord.Embed(
                            title="🎉 Level Up!",
                            description=f"Congratulations {interaction.user.mention}, you've reached **Level {user_level + 1}**!",
                            color=discord.Color.fuchsia()
                        )
                        await level_channel.send(embed=embed)
                await leveling_cog.update_user_roles(interaction.user, user_level + 1)


        embed = discord.Embed(
            title="🌞 Daily Reward Claimed!",
            description=f"You received **{reward} XP**!\nYour current streak is now **{new_streak if new_streak != 7 else 0}** days.",
            color=discord.Color.green()
        )
        if bonus_message:
            embed.add_field(name="Streak Bonus!", value=bonus_message)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="donatecookies", description="Give some of your cookies to another user.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(
        user="The user you want to give cookies to.",
        amount="The amount of cookies to give."
    )
    async def donatecookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        sender_id = interaction.user.id
        receiver_id = user.id

        if amount <= 0:
            await interaction.response.send_message("You must donate a positive number of cookies.", ephemeral=True)
            return

        if sender_id == receiver_id:
            await interaction.response.send_message("You can't donate cookies to yourself!", ephemeral=True)
            return

        if user.bot:
            await interaction.response.send_message("You can't donate cookies to a bot!", ephemeral=True)
            return

        sender_balance = db.get_cookies(sender_id)
        if sender_balance < amount:
            await interaction.response.send_message(f"You don't have enough cookies to donate that much. Your balance is **{sender_balance}** 🍪.", ephemeral=True)
            return

        # Perform the transaction
        db.remove_cookies(sender_id, amount)
        db.add_cookies(receiver_id, amount)

        # Update cookie roles for both users
        cookies_cog = self.bot.get_cog("Cookies")
        if cookies_cog:
            # Fetch the member objects to pass to the update function
            sender_member = interaction.guild.get_member(sender_id)
            receiver_member = user
            if sender_member:
                await cookies_cog.update_cookie_roles(sender_member)
            if receiver_member:
                await cookies_cog.update_cookie_roles(receiver_member)

        embed = discord.Embed(
            title="🎁 Cookies Donated!",
            description=f"{interaction.user.mention} has donated **{amount}** 🍪 to {user.mention}!",
            color=discord.Color.from_rgb(255, 182, 193) # Light pink
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot)) 