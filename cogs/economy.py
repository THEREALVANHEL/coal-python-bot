import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Economy] Loaded successfully.")

    @app_commands.command(name="balance", description="Check your or another user's coin balance")
    @app_commands.describe(user="User to check balance for")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        try:
            user_data = db.get_user_data(target.id)
            balance = user_data.get('coins', 0)
            
            embed = discord.Embed(
                title="💰 Balance",
                description=f"**{target.display_name}** has **{balance:,}** coins",
                color=0xffd700
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting balance: {str(e)}", ephemeral=True)

    @app_commands.command(name="work", description="Work to earn some coins")
    async def work(self, interaction: discord.Interaction):
        try:
            # Check cooldown (30 minutes)
            user_data = db.get_user_data(interaction.user.id)
            last_work = user_data.get('last_work', 0)
            cooldown = 30 * 60  # 30 minutes in seconds
            
            current_time = datetime.now().timestamp()
            if current_time - last_work < cooldown:
                time_left = cooldown - (current_time - last_work)
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                await interaction.response.send_message(
                    f"⏰ You're tired! Rest for {minutes}m {seconds}s before working again.", 
                    ephemeral=True
                )
                return

            # Random earnings
            earnings = random.randint(50, 200)
            jobs = [
                "coding", "streaming", "gaming", "teaching", "cooking",
                "cleaning", "delivery", "mining", "fishing", "trading"
            ]
            job = random.choice(jobs)
            # Update database
            db.add_coins(interaction.user.id, earnings)
            db.update_last_work(interaction.user.id, current_time)
            
            new_balance = db.get_user_data(interaction.user.id).get('coins', 0)
            
            embed = discord.Embed(
                title="💼 Work Complete!",
                description=f"You worked as a **{job}** and earned **{earnings}** coins!",
                color=0x00ff00
            )
            embed.add_field(name="💰 New Balance", value=f"{new_balance:,} coins", inline=False)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error working: {str(e)}", ephemeral=True)

    @app_commands.command(name="shop", description="View the server shop")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Server Shop",
            description="Use `/buy <item>` to purchase items!",
            color=0x7289da
        )
        
        items = [
            {"name": "Cookie Pack", "price": 100, "description": "Get 10 cookies!"},
            {"name": "XP Boost", "price": 250, "description": "Double XP for 1 hour"},
            {"name": "Custom Role", "price": 1000, "description": "Create your own role"},
            {"name": "Profile Badge", "price": 500, "description": "Special badge for your profile"}
        ]
        
        for item in items:
            embed.add_field(
                name=f"{item['name']} - {item['price']} coins",
                value=item['description'],
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item="Item to purchase")
    @app_commands.choices(item=[
        app_commands.Choice(name="Cookie Pack (100 coins)", value="cookie_pack"),
        app_commands.Choice(name="XP Boost (250 coins)", value="xp_boost"),
        app_commands.Choice(name="Custom Role (1000 coins)", value="custom_role"),
        app_commands.Choice(name="Profile Badge (500 coins)", value="profile_badge")
    ])
    async def buy(self, interaction: discord.Interaction, item: str):
        shop_items = {
            "cookie_pack": {"price": 100, "name": "Cookie Pack"},
            "xp_boost": {"price": 250, "name": "XP Boost"},
            "custom_role": {"price": 1000, "name": "Custom Role"},
            "profile_badge": {"price": 500, "name": "Profile Badge"}
        }
        
        if item not in shop_items:
            await interaction.response.send_message("❌ Invalid item!", ephemeral=True)
            return

        try:
            user_data = db.get_user_data(interaction.user.id)
            balance = user_data.get('coins', 0)
            item_data = shop_items[item]
            if balance < item_data['price']:
                await interaction.response.send_message(
                    f"❌ You don't have enough coins! You need {item_data['price']} coins but only have {balance}.",
                    ephemeral=True
                )
                return

            # Process purchase
            db.remove_coins(interaction.user.id, item_data['price'])
            
            if item == "cookie_pack":
                db.add_cookies(interaction.user.id, 10)
                
            new_balance = db.get_user_data(interaction.user.id).get('coins', 0)
            
            embed = discord.Embed(
                title="🛍️ Purchase Successful!",
                description=f"You bought **{item_data['name']}** for **{item_data['price']}** coins!",
                color=0x00ff00
            )
            embed.add_field(name="💰 Remaining Balance", value=f"{new_balance:,} coins", inline=False)
            
            if item == "cookie_pack":
                embed.add_field(name="🍪 Bonus", value="You received 10 cookies!", inline=False)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error processing purchase: {str(e)}", ephemeral=True)

    @app_commands.command(name="coinflip", description="Flip a coin and bet coins")
    @app_commands.describe(
        amount="Amount to bet",
        choice="Heads or tails"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, amount: int, choice: str):
        if amount <= 0:
            await interaction.response.send_message("❌ Bet amount must be positive!", ephemeral=True)
            return

        try:
            user_data = db.get_user_data(interaction.user.id)
            balance = user_data.get('coins', 0)
            
            if balance < amount:
                await interaction.response.send_message(
                    f"❌ You don't have enough coins! You have {balance} but tried to bet {amount}.",
                    ephemeral=True
                )
                return

            # Flip the coin
            result = random.choice(["heads", "tails"])
            won = choice == result
            
            embed = discord.Embed(
                title="🪙 Coin Flip Results",
                color=0x00ff00 if won else 0xff0000
                         )
            if won:
                winnings = amount
                db.add_coins(interaction.user.id, winnings)
                new_balance = balance + winnings
                embed.description = f"🎉 **You won!** The coin landed on **{result}**!"
                embed.add_field(name="💰 Winnings", value=f"+{winnings} coins", inline=True)
            else:
                db.remove_coins(interaction.user.id, amount)
                new_balance = balance - amount
                embed.description = f"😔 **You lost!** The coin landed on **{result}**."
                embed.add_field(name="💸 Lost", value=f"-{amount} coins", inline=True)
            
            embed.add_field(name="💰 New Balance", value=f"{new_balance:,} coins", inline=True)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error with coinflip: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
