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

    @app_commands.command(name="daily", description="Claim your daily cookies and build a streak!")
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
        reward = 1
        bonus_message = ""
        if new_streak > 0 and new_streak % 7 == 0:
            reward += 1 # Weekly streak bonus
            bonus_message = f"🎉 **+1** bonus cookie for your **{new_streak}-day** streak!"

        db.add_cookies(user_id, reward)
        db.update_daily_checkin(user_id, new_streak)

        embed = discord.Embed(
            title="🌞 Daily Reward Claimed!",
            description=f"You received **{reward}** 🍪 cookie(s)!\nYour current streak is now **{new_streak}** days.",
            color=discord.Color.green()
        )
        if bonus_message:
            embed.add_field(name="Streak Bonus!", value=bonus_message)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gamble", description="Gamble your cookies for a chance to win more.")
    @app_commands.guilds(guild_obj)
    @app_commands.describe(amount="The amount of cookies to bet.")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("You must bet a positive number of cookies.", ephemeral=True)
            return

        user_id = interaction.user.id
        balance = db.get_cookies(user_id)

        if amount > balance:
            await interaction.response.send_message(f"You can't bet more cookies than you have! Your balance is **{balance}** 🍪.", ephemeral=True)
            return

        # 50/50 chance
        is_win = random.choice([True, False])

        if is_win:
            db.add_cookies(user_id, amount)
            result_message = f"🎉 **You won!**\nYou won **{amount}** 🍪 cookies and now have **{balance + amount}** 🍪."
            color = discord.Color.green()
        else:
            db.remove_cookies(user_id, amount)
            result_message = f"💔 **You lost!**\nYou lost **{amount}** 🍪 cookies and now have **{balance - amount}** 🍪."
            color = discord.Color.red()
        
        embed = discord.Embed(title="🎰 Cookie Gamble", description=result_message, color=color)
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

        embed = discord.Embed(
            title="🎁 Cookies Donated!",
            description=f"{interaction.user.mention} has donated **{amount}** 🍪 to {user.mention}!",
            color=discord.Color.from_rgb(255, 182, 193) # Light pink
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot)) 