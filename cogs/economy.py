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

# Job opportunities with varying pay and requirements
JOB_OPPORTUNITIES = [
    {"name": "Pizza Delivery", "min_pay": 25, "max_pay": 50, "cooldown": 1800, "description": "delivering hot pizzas"},
    {"name": "Code Review", "min_pay": 40, "max_pay": 80, "cooldown": 2700, "description": "reviewing code for bugs"},
    {"name": "Bug Hunting", "min_pay": 60, "max_pay": 120, "cooldown": 3600, "description": "finding and reporting bugs"},
    {"name": "Teaching Session", "min_pay": 80, "max_pay": 150, "cooldown": 4500, "description": "teaching programming"},
    {"name": "Freelance Project", "min_pay": 100, "max_pay": 200, "cooldown": 5400, "description": "completing a freelance project"},
    {"name": "Consulting", "min_pay": 150, "max_pay": 300, "cooldown": 7200, "description": "providing tech consulting"},
    {"name": "System Architecture", "min_pay": 200, "max_pay": 400, "cooldown": 9000, "description": "designing system architecture"},
    {"name": "Product Launch", "min_pay": 300, "max_pay": 600, "cooldown": 10800, "description": "launching a new product"}
]

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
            
            # Get rank
            leaderboard = db.get_leaderboard('coins')
            rank = next((i + 1 for i, u in enumerate(leaderboard) if u['user_id'] == target.id), 'N/A')
            
            embed = discord.Embed(
                title="💰 Balance",
                description=f"**{target.display_name}** has **{balance:,}** coins",
                color=0xffd700
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(name="📈 Rank", value=f"#{rank}", inline=True)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting balance: {str(e)}", ephemeral=True)

    @app_commands.command(name="coinleaderboard", description="Shows paginated coin leaderboard")
    @app_commands.describe(page="Page number (default: 1)")
    async def coinleaderboard(self, interaction: discord.Interaction, page: int = 1):
        try:
            if page < 1:
                page = 1
                
            items_per_page = 10
            skip = (page - 1) * items_per_page
            
            all_users = db.get_leaderboard('coins')
            total_users = len(all_users)
            total_pages = (total_users + items_per_page - 1) // items_per_page
            
            if page > total_pages:
                await interaction.response.send_message(f"❌ Page {page} doesn't exist! Max page: {total_pages}", ephemeral=True)
                return

            page_users = all_users[skip:skip + items_per_page]
            
            if not page_users:
                await interaction.response.send_message("❌ No coin data available!", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"🪙 Coin Leaderboard - Page {page}/{total_pages}",
                color=0xffd700
            )

            leaderboard_text = []
            for i, user_data in enumerate(page_users, start=skip + 1):
                user_id = user_data['user_id']
                coins = user_data.get('coins', 0)
                
                try:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    username = user.display_name if hasattr(user, 'display_name') else user.name
                except:
                    username = f"User {user_id}"

                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard_text.append(f"{medal} **{username}** - {coins:,} coins")

            embed.description = "\n".join(leaderboard_text)
            embed.set_footer(text=f"Page {page}/{total_pages} • Work hard to earn more coins!")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Error getting leaderboard: {str(e)}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Error getting leaderboard: {str(e)}", ephemeral=True)

    @app_commands.command(name="work", description="Work various jobs to earn coins")
    async def work(self, interaction: discord.Interaction):
        try:
            # Check cooldown (varies by job)
            user_data = db.get_user_data(interaction.user.id)
            last_work = user_data.get('last_work', 0)
            current_time = datetime.now().timestamp()
            
            # Base cooldown of 30 minutes
            base_cooldown = 30 * 60  # 30 minutes in seconds
            
            if current_time - last_work < base_cooldown:
                time_left = base_cooldown - (current_time - last_work)
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                await interaction.response.send_message(
                    f"⏰ You're tired! Rest for {minutes}m {seconds}s before working again.", 
                    ephemeral=True
                )
                return

            # Select random job based on user level
            xp = user_data.get('xp', 0)
            level = self.calculate_level_from_xp(xp)
            
            # Higher level users get access to better jobs
            available_jobs = JOB_OPPORTUNITIES[:min(len(JOB_OPPORTUNITIES), max(1, level // 10 + 1))]
            job = random.choice(available_jobs)
            
            # Calculate earnings based on job and level
            base_earnings = random.randint(job["min_pay"], job["max_pay"])
            level_bonus = level * 2  # 2 coins per level bonus
            total_earnings = base_earnings + level_bonus
            
            # Random success/failure for higher paying jobs
            success_chance = max(0.7, 1.0 - (len(available_jobs) - 1) * 0.1)
            
            if random.random() < success_chance:
                # Success
                db.add_coins(interaction.user.id, total_earnings)
                db.update_last_work(interaction.user.id, current_time)
                
                new_balance = db.get_user_data(interaction.user.id).get('coins', 0)
                
                embed = discord.Embed(
                    title="💼 Work Complete!",
                    description=f"You worked as **{job['name']}** {job['description']} and earned **{total_earnings}** coins!",
                    color=0x00ff00
                )
                embed.add_field(name="💰 Breakdown", value=f"Base Pay: {base_earnings}\nLevel Bonus: {level_bonus}\nTotal: {total_earnings}", inline=True)
                embed.add_field(name="💰 New Balance", value=f"{new_balance:,} coins", inline=True)
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            else:
                # Failure
                db.update_last_work(interaction.user.id, current_time)
                
                embed = discord.Embed(
                    title="💼 Work Failed!",
                    description=f"You attempted **{job['name']}** but it didn't go well. Better luck next time!",
                    color=0xff9900
                )
                embed.add_field(name="💡 Tip", value="Higher level jobs have lower success rates but better pay!", inline=False)
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error working: {str(e)}", ephemeral=True)

    def calculate_level_from_xp(self, xp: int) -> int:
        """Calculate level from XP"""
        level = 0
        while self.calculate_xp_for_level(level + 1) <= xp:
            level += 1
        return level

    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required for level"""
        if level <= 10:
            return int(200 * (level ** 2))
        elif level <= 50:
            return int(300 * (level ** 2.2))
        elif level <= 100:
            return int(500 * (level ** 2.5))
        else:
            return int(1000 * (level ** 2.8))

    @app_commands.command(name="shop", description="View the server shop")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Server Shop",
            description="Use `/buy <item>` to purchase items!\n**⏰ All items are temporary!**",
            color=0x7289da
        )
        
        items = [
            {"name": "XP Boost", "price": 200, "description": "Double XP for 1 hour", "duration": "1 hour"},
            {"name": "VIP Role", "price": 500, "description": "VIP access and perks", "duration": "3 days"},
            {"name": "Custom Color", "price": 800, "description": "Custom role color", "duration": "7 days"},
            {"name": "Profile Badge", "price": 300, "description": "Special profile badge", "duration": "30 days"},
            {"name": "Nickname Change", "price": 150, "description": "Custom nickname privilege", "duration": "7 days"},
            {"name": "Channel Access", "price": 1000, "description": "Access to exclusive channels", "duration": "14 days"}
        ]
        
        for item in items:
            embed.add_field(
                name=f"{item['name']} - {item['price']} coins",
                value=f"{item['description']}\n⏰ Duration: {item['duration']}",
                inline=False
            )
        
        embed.set_footer(text="⚠️ All purchases are temporary and will expire after the specified time!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item="Item to purchase")
    @app_commands.choices(item=[
        app_commands.Choice(name="XP Boost (200 coins - 1 hour)", value="xp_boost"),
        app_commands.Choice(name="VIP Role (500 coins - 3 days)", value="vip_role"),
        app_commands.Choice(name="Custom Color (800 coins - 7 days)", value="custom_color"),
        app_commands.Choice(name="Profile Badge (300 coins - 30 days)", value="profile_badge"),
        app_commands.Choice(name="Nickname Change (150 coins - 7 days)", value="nickname_change"),
        app_commands.Choice(name="Channel Access (1000 coins - 14 days)", value="channel_access")
    ])
    async def buy(self, interaction: discord.Interaction, item: str):
        shop_items = {
            "xp_boost": {"price": 200, "name": "XP Boost", "duration": 3600, "description": "1 hour"},
            "vip_role": {"price": 500, "name": "VIP Role", "duration": 259200, "description": "3 days"},
            "custom_color": {"price": 800, "name": "Custom Color", "duration": 604800, "description": "7 days"},
            "profile_badge": {"price": 300, "name": "Profile Badge", "duration": 2592000, "description": "30 days"},
            "nickname_change": {"price": 150, "name": "Nickname Change", "duration": 604800, "description": "7 days"},
            "channel_access": {"price": 1000, "name": "Channel Access", "duration": 1209600, "description": "14 days"}
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

            # Check if user already has this item
            active_purchases = db.get_active_temporary_purchases(interaction.user.id)
            has_item = any(purchase["item_type"] == item for purchase in active_purchases)
            
            if has_item:
                await interaction.response.send_message(
                    f"❌ You already have an active {item_data['name']}! Wait for it to expire before purchasing again.",
                    ephemeral=True
                )
                return

            # Process purchase
            db.remove_coins(interaction.user.id, item_data['price'])
            new_balance = db.get_user_data(interaction.user.id).get('coins', 0)
            
            embed = discord.Embed(
                title="🛍️ Purchase Successful!",
                description=f"You bought **{item_data['name']}** for **{item_data['price']}** coins!",
                color=0x00ff00
            )
            embed.add_field(name="💰 Remaining Balance", value=f"{new_balance:,} coins", inline=True)
            embed.add_field(name="⏰ Duration", value=item_data['description'], inline=True)
            
            # Handle specific items
            if item == "vip_role":
                # Find or create VIP role
                vip_role = discord.utils.get(interaction.guild.roles, name="🌟 VIP")
                if not vip_role:
                    vip_role = await interaction.guild.create_role(
                        name="🌟 VIP", 
                        color=discord.Color.gold(),
                        reason="VIP role from shop purchase"
                    )
                
                await interaction.user.add_roles(vip_role)
                db.add_temporary_role(interaction.user.id, vip_role.id, item_data['duration'])
                embed.add_field(name="🌟 VIP Role", value=f"You've been granted VIP status for {item_data['description']}!", inline=False)
                
            elif item == "custom_color":
                embed.add_field(name="🎨 Custom Color", value=f"Contact a moderator to set your custom role color! Valid for {item_data['description']}.", inline=False)
                db.add_temporary_purchase(interaction.user.id, "custom_color", item_data['duration'])
                
            elif item == "xp_boost":
                db.add_temporary_purchase(interaction.user.id, "xp_boost", item_data['duration'])
                embed.add_field(name="⚡ XP Boost", value=f"You'll get double XP for {item_data['description']}!", inline=False)
                
            elif item == "profile_badge":
                db.add_temporary_purchase(interaction.user.id, "profile_badge", item_data['duration'])
                embed.add_field(name="🏆 Badge", value=f"You've unlocked a special profile badge for {item_data['description']}!", inline=False)
                
            elif item == "nickname_change":
                db.add_temporary_purchase(interaction.user.id, "nickname_change", item_data['duration'])
                embed.add_field(name="📝 Nickname", value=f"You can change your nickname for {item_data['description']}! Use Discord's nickname feature.", inline=False)
                
            elif item == "channel_access":
                db.add_temporary_purchase(interaction.user.id, "channel_access", item_data['duration'])
                embed.add_field(name="🚪 Access", value=f"You now have access to exclusive channels for {item_data['description']}!", inline=False)
            
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
            
            # Get the appropriate coin image
            image_name = "heads.jpeg" if result == "heads" else "tails.jpeg"
            image_path = os.path.join(os.path.dirname(__file__), '..', 'assets', image_name)
            
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
            
            # Add the coin image
            if os.path.exists(image_path):
                file = discord.File(image_path, filename=image_name)
                embed.set_image(url=f"attachment://{image_name}")
                await interaction.response.send_message(embed=embed, file=file)
            else:
                await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error with coinflip: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
