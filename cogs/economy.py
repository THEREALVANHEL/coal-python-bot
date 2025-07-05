import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random
import os, sys
from discord.ui import Button, View

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250

# Job opportunities with varying pay and requirements
JOB_OPPORTUNITIES = [
    {
        "name": "Pizza Delivery", 
        "emoji": "🍕",
        "min_pay": 25, 
        "max_pay": 50, 
        "cooldown": 1800, 
        "description": "delivering hot pizzas",
        "full_description": "🍕 You hop on your delivery bike and navigate through busy streets, delivering steaming hot pizzas to hungry customers. Tips depend on your speed and customer satisfaction!",
        "requirements": "No experience needed"
    },
    {
        "name": "Code Review", 
        "emoji": "👨‍💻",
        "min_pay": 40, 
        "max_pay": 80, 
        "cooldown": 2700, 
        "description": "reviewing code for bugs",
        "full_description": "👨‍💻 You carefully examine lines of code, hunting for bugs and suggesting improvements. Your attention to detail helps prevent crashes and security vulnerabilities!",
        "requirements": "Basic programming knowledge"
    },
    {
        "name": "Bug Hunting", 
        "emoji": "🐛",
        "min_pay": 60, 
        "max_pay": 120, 
        "cooldown": 3600, 
        "description": "finding and reporting bugs",
        "full_description": "🐛 Armed with testing tools, you systematically search for elusive bugs in software. Each bug you find and report earns bounty rewards from grateful developers!",
        "requirements": "Problem-solving skills"
    },
    {
        "name": "Teaching Session", 
        "emoji": "📚",
        "min_pay": 80, 
        "max_pay": 150, 
        "cooldown": 4500, 
        "description": "teaching programming",
        "full_description": "📚 You lead an engaging coding workshop, helping eager students understand complex programming concepts. Seeing that 'aha!' moment makes it all worthwhile!",
        "requirements": "Teaching experience"
    },
    {
        "name": "Freelance Project", 
        "emoji": "💼",
        "min_pay": 100, 
        "max_pay": 200, 
        "cooldown": 5400, 
        "description": "completing a freelance project",
        "full_description": "💼 You work independently on a custom software solution for a client. From requirements gathering to final delivery, you handle the entire project lifecycle!",
        "requirements": "Portfolio and experience"
    },
    {
        "name": "Consulting", 
        "emoji": "🤝",
        "min_pay": 150, 
        "max_pay": 300, 
        "cooldown": 7200, 
        "description": "providing tech consulting",
        "full_description": "🤝 You advise companies on their technology strategy, helping them make informed decisions about architecture, tools, and processes. Your expertise drives business success!",
        "requirements": "Senior level expertise"
    },
    {
        "name": "System Architecture", 
        "emoji": "🏗️",
        "min_pay": 200, 
        "max_pay": 400, 
        "cooldown": 9000, 
        "description": "designing system architecture",
        "full_description": "🏗️ You design the blueprint for complex software systems, ensuring scalability, reliability, and performance. Your architectural decisions shape the future of technology!",
        "requirements": "Expert level experience"
    },
    {
        "name": "Product Launch", 
        "emoji": "🚀",
        "min_pay": 300, 
        "max_pay": 600, 
        "cooldown": 10800, 
        "description": "launching a new product",
        "full_description": "🚀 You orchestrate the launch of a groundbreaking product, coordinating with marketing, engineering, and sales teams. The success of the launch determines the company's future!",
        "requirements": "Leadership and vision"
    }
]

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Economy] Loaded successfully.")

    async def create_coin_leaderboard_embed(self, page: int):
        items_per_page = 10
        skip = (page - 1) * items_per_page
        
        all_users = db.get_leaderboard('coins')
        total_users = len(all_users)
        total_pages = (total_users + items_per_page - 1) // items_per_page
        page_users = all_users[skip:skip + items_per_page]

        # Luxurious wealth-themed design
        embed = discord.Embed(
            title="💰 **WEALTH EMPIRE** 💰",
            description="✨ *The Financial Elite & Money Masters* ✨",
            color=0xffd700,
            timestamp=datetime.now()
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

            # Luxury wealth ranking system
            if i == 1:
                rank_style = f"👑 **#{i} FINANCIAL EMPEROR {username}** 👑"
                style_suffix = " 💰💎💰"
            elif i == 2:
                rank_style = f"🥈 **#{i} WEALTH MASTER {username}** 🥈"
                style_suffix = " 💰💰"
            elif i == 3:
                rank_style = f"🥉 **#{i} MONEY MOGUL {username}** 💰"
                style_suffix = " 💰"
            elif i <= 5:
                rank_style = f"🔸 **#{i} BUSINESS TYCOON {username}**"
                style_suffix = " 💎"
            elif i <= 10:
                rank_style = f"▫️ **#{i} ENTREPRENEUR {username}**"
                style_suffix = " 🪙"
            else:
                rank_style = f"#{i} • {username}"
                style_suffix = ""

            # Wealth tier classification
            if coins >= 50000:
                wealth_tier = "🏆 **BILLIONAIRE**"
                wealth_emoji = "💰💰💰💰💰"
            elif coins >= 25000:
                wealth_tier = "💎 **MILLIONAIRE**"
                wealth_emoji = "💰💰💰💰"
            elif coins >= 10000:
                wealth_tier = "⭐ **HIGH ROLLER**"
                wealth_emoji = "💰💰💰"
            elif coins >= 5000:
                wealth_tier = "⭐ **WEALTHY**"
                wealth_emoji = "💰💰"
            elif coins >= 2500:
                wealth_tier = "🌟 **SUCCESSFUL**"
                wealth_emoji = "💰"
            elif coins >= 1000:
                wealth_tier = "✨ **RISING STAR**"
                wealth_emoji = "🪙"
            elif coins >= 500:
                wealth_tier = "🔰 **WORKER**"
                wealth_emoji = "⚡"
            else:
                wealth_tier = "🆕 **NEWCOMER**"
                wealth_emoji = "✨"
            
            # Create wealth progress bar
            wealth_milestones = [500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
            next_milestone = next((m for m in wealth_milestones if coins < m), 100000)
            prev_milestone = max([m for m in wealth_milestones if coins >= m] + [0])
            
            if next_milestone > prev_milestone:
                progress = (coins - prev_milestone) / (next_milestone - prev_milestone)
                progress_bars = int(progress * 8)
                wealth_bar = "💰" * progress_bars + "▱" * (8 - progress_bars)
                progress_text = f"`{wealth_bar}` → {next_milestone:,}"
            else:
                progress_text = "🏆 **ULTIMATE WEALTH!**"
            
            # Format coins with comma separators
            coin_display = f"🪙 **{coins:,} Coins** • {wealth_tier}"
            
            entry = f"{rank_style}{style_suffix}\n{coin_display}\n{progress_text} {wealth_emoji}"
            leaderboard_text.append(entry)

        embed.description = f"✨ *The Financial Elite & Money Masters* ✨\n\n" + "\n\n".join(leaderboard_text)
        
        # Rich stats section
        embed.add_field(
            name="💰 **Economy Stats**",
            value=f"🏦 **{total_users}** Active Earners\n📊 **Page {page}/{total_pages}**\n🎯 **Get Rich!**",
            inline=True
        )
        
        embed.add_field(
            name="💡 **Wealth Tips**",
            value="💼 Use `/work` regularly\n📈 Higher levels = more pay\n🛒 Visit `/shop` to spend!",
            inline=True
        )
        
        embed.set_footer(text="💰 Coin Leaderboard • Work hard, earn more! • 💎 Financial success awaits!")
        
        return embed

    @app_commands.command(name="balance", description="💰 Check your shiny coin balance")
    @app_commands.describe(user="User to check balance for")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        try:
            user_data = db.get_user_data(target.id)
            coins = user_data.get('coins', 0)
            
            # Get user's rank in coin leaderboard
            leaderboard = db.get_leaderboard('coins')
            rank = next((i + 1 for i, u in enumerate(leaderboard) if u['user_id'] == target.id), 'N/A')
            
            embed = discord.Embed(
                title="💰 Coin Wallet",
                color=0xffd700,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            
            # Main balance
            embed.add_field(
                name="🪙 Current Balance",
                value=f"**{coins:,}** coins",
                inline=True
            )
            
            # Rank
            if rank != 'N/A':
                embed.add_field(
                    name="📊 Server Rank",
                    value=f"**#{rank}** of {len(leaderboard)}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="📊 Server Rank",
                    value="Not ranked",
                    inline=True
                )
            
            # Last work info
            last_work = user_data.get('last_work', 0)
            if last_work > 0:
                embed.add_field(
                    name="💼 Last Work",
                    value=f"<t:{int(last_work)}:R>",
                    inline=True
                )
            else:
                embed.add_field(
                    name="💼 Work Status",
                    value="Never worked - use `/work`!",
                    inline=True
                )
            
            # Quick tips
            embed.add_field(
                name="💡 Earning Tips",
                value="• Use `/work` every 30 minutes\n• Higher levels = better pay\n• Visit `/shop` to spend coins",
                inline=False
            )
            
            pronoun = "Your" if target == interaction.user else f"{target.display_name}'s"
            embed.set_author(
                name=f"{pronoun} Economy Stats",
                icon_url=target.display_avatar.url
            )
            embed.set_footer(text="💫 Economy System • Work hard, earn more!")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Couldn't retrieve balance data. Please try again later.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    # REMOVED: coinleaderboard command - now use /leaderboard coins
    @app_commands.command(name="coinleaderboard", description="🪙 View coin leaderboard (use /leaderboard instead)")
    async def coinleaderboard_redirect(self, interaction: discord.Interaction, page: int = 1):
        embed = discord.Embed(
            title="🔄 Command Updated",
            description="The coin leaderboard has been moved to our unified system!",
            color=0x7c3aed
        )
        embed.add_field(
            name="✨ New Command",
            value="Use `/leaderboard type:🪙 Coins` for the coin leaderboard",
            inline=False
        )
        embed.add_field(
            name="🎉 What's New",
            value="• Smooth pagination\n• Modern design\n• All leaderboards unified",
            inline=False
        )
        embed.set_footer(text="💫 This command will be removed soon")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="work", description="💼 Work various jobs to earn coins - choose your preferred job!")
    async def work(self, interaction: discord.Interaction):
        try:
            # Check cooldown 
            user_data = db.get_user_data(interaction.user.id)
            last_work = user_data.get('last_work', 0)
            current_time = datetime.now().timestamp()
            
            # Base cooldown of 30 minutes
            base_cooldown = 30 * 60  # 30 minutes in seconds
            
            if current_time - last_work < base_cooldown:
                time_left = base_cooldown - (current_time - last_work)
                minutes = int(time_left // 60)
                seconds = int(time_left % 60)
                
                embed = discord.Embed(
                    title="⏰ **Work Cooldown**",
                    description=f"You're tired! Rest for **{minutes}m {seconds}s** before working again.",
                    color=0xff9966,
                    timestamp=datetime.now()
                )
                embed.add_field(name="💡 Tip", value="Higher level jobs pay more but have lower success rates!", inline=False)
                embed.set_footer(text="💼 Come back when you're refreshed!")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Get available jobs based on user level
            xp = user_data.get('xp', 0)
            level = self.calculate_level_from_xp(xp)
            
            # Higher level users get access to better jobs
            available_jobs = JOB_OPPORTUNITIES[:min(len(JOB_OPPORTUNITIES), max(1, level // 10 + 1))]
            
            # Create job selection view
            class JobSelectionView(discord.ui.View):
                def __init__(self, user_level, current_time):
                    super().__init__(timeout=60)
                    self.user_level = user_level
                    self.current_time = current_time
                
                @discord.ui.select(
                    placeholder="🎯 Choose your job for today...",
                    min_values=1,
                    max_values=1,
                    options=[
                        discord.SelectOption(
                            label=job["name"],
                            description=f"💰 {job['min_pay']}-{job['max_pay']} coins • {job['requirements']}",
                            emoji=job.get("emoji", "💼"),
                            value=str(i)
                        ) for i, job in enumerate(available_jobs)
                    ]
                )
                async def job_select(self, select_interaction: discord.Interaction, select: discord.ui.Select):
                    if select_interaction.user.id != interaction.user.id:
                        await select_interaction.response.send_message("❌ This is not your work selection!", ephemeral=True)
                        return
                    
                    job_index = int(select.values[0])
                    selected_job = available_jobs[job_index]
                    
                    # Calculate earnings based on job and level
                    base_earnings = random.randint(selected_job["min_pay"], selected_job["max_pay"])
                    level_bonus = level * 2  # 2 coins per level bonus
                    total_earnings = base_earnings + level_bonus
                    
                    # Random success/failure for higher paying jobs (easier success for chosen jobs)
                    success_chance = max(0.8, 1.0 - (job_index * 0.05))  # Better chance when choosing
                    
                    if random.random() < success_chance:
                        # Success
                        db.add_coins(interaction.user.id, total_earnings)
                        db.update_last_work(interaction.user.id, self.current_time)
                        
                        new_balance = db.get_user_data(interaction.user.id).get('coins', 0)
                        
                        embed = discord.Embed(
                            title="✅ **Work Complete!**",
                            description=f"**{selected_job['name']}** - {selected_job['full_description']}",
                            color=0x00d4aa,
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="💰 Earnings", value=f"**+{total_earnings}** coins", inline=True)
                        embed.add_field(name="🪙 New Balance", value=f"{new_balance:,} coins", inline=True)
                        embed.add_field(name="🎯 Level Bonus", value=f"+{level_bonus} coins", inline=True)
                        embed.add_field(name="💡 Job Details", value=selected_job["requirements"], inline=False)
                        embed.set_author(name=select_interaction.user.display_name, icon_url=select_interaction.user.display_avatar.url)
                        embed.set_footer(text="💼 Great job! Come back in 30 minutes for more work.")
                        
                        # Add achievement-style message for high earnings
                        if total_earnings >= 100:
                            embed.add_field(name="🏆 Achievement", value="High Earner! You made over 100 coins!", inline=False)
                    else:
                        # Failure
                        db.update_last_work(interaction.user.id, self.current_time)
                        
                        embed = discord.Embed(
                            title="⚠️ **Work Failed**",
                            description=f"**{selected_job['name']}** - You attempted this job but it didn't go as planned.",
                            color=0xff9966,
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="💭 What happened", value=f"The {selected_job['name'].lower()} was more challenging than expected. Sometimes these things happen!", inline=False)
                        embed.add_field(name="💡 Silver Lining", value="You gained experience! Higher level jobs have better success rates when you level up.", inline=False)
                        embed.set_author(name=select_interaction.user.display_name, icon_url=select_interaction.user.display_avatar.url)
                        embed.set_footer(text="💪 Don't give up! Try again in 30 minutes.")
                    
                    await select_interaction.response.edit_message(embed=embed, view=None)
            
            # Create initial embed
            embed = discord.Embed(
                title="💼 **Work Opportunities**",
                description=f"Choose your job wisely! You have **{len(available_jobs)}** available jobs based on your level.\n\n" +
                           "**💡 Pro Tips:**\n" +
                           "• Higher level jobs pay more but have lower success rates\n" +
                           "• Choosing your job gives better success chance than random\n" +
                           "• Level bonuses apply to all jobs (+2 coins per level)",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # Add available jobs info
            jobs_info = []
            for i, job in enumerate(available_jobs):
                emoji = job.get("emoji", "💼")
                pay_range = f"{job['min_pay']}-{job['max_pay']} coins"
                level_req = job["requirements"]
                jobs_info.append(f"{emoji} **{job['name']}** - {pay_range}\n   _{level_req}_")
            
            embed.add_field(
                name="🎯 **Available Jobs**",
                value="\n\n".join(jobs_info),
                inline=False
            )
            
            embed.add_field(
                name="📊 **Your Stats**",
                value=f"**Level:** {level}\n**Level Bonus:** +{level * 2} coins\n**Jobs Unlocked:** {len(available_jobs)}/{len(JOB_OPPORTUNITIES)}",
                inline=True
            )
            
            embed.set_author(name=f"{interaction.user.display_name}'s Work Dashboard", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="💼 Select a job from the dropdown below")
            
            view = JobSelectionView(level, current_time)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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
