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

    @app_commands.command(name="shop", description="🛒 View the premium temporary items shop")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 **Premium Temporary Shop**",
            description="✨ **Enhance your server experience with temporary perks!**\nUse `/buy <item>` to purchase items.",
            color=0x9932cc
        )
        
        # Organize items by category for better presentation
        power_items = [
            {"name": "⚡ XP Boost", "price": 200, "description": "Double XP gain for 1 hour", "duration": "1 hour", "category": "🚀 Power-Ups"},
            {"name": "🍪 Cookie Multiplier", "price": 300, "description": "Triple cookie rewards for 2 hours", "duration": "2 hours", "category": "🚀 Power-Ups"},
            {"name": "💰 Coin Boost", "price": 250, "description": "1.5x coin earnings for 3 hours", "duration": "3 hours", "category": "🚀 Power-Ups"},
            {"name": "🎯 Work Success", "price": 400, "description": "Guaranteed work success for 1 day", "duration": "24 hours", "category": "🚀 Power-Ups"}
        ]
        
        social_items = [
            {"name": "🌟 VIP Role", "price": 500, "description": "VIP status with exclusive perks", "duration": "3 days", "category": "👑 Social Status"},
            {"name": "🎨 Custom Color", "price": 800, "description": "Personalized role color", "duration": "7 days", "category": "👑 Social Status"},
            {"name": "👑 Crown Badge", "price": 600, "description": "Golden crown on your profile", "duration": "14 days", "category": "👑 Social Status"},
            {"name": "🌈 Rainbow Name", "price": 1200, "description": "Animated rainbow nickname", "duration": "5 days", "category": "👑 Social Status"}
        ]
        
        access_items = [
            {"name": "🚪 VIP Channels", "price": 1000, "description": "Access to exclusive channels", "duration": "14 days", "category": "🔑 Access"},
            {"name": "📝 Nickname Freedom", "price": 150, "description": "Change nickname anytime", "duration": "7 days", "category": "🔑 Access"},
            {"name": "🎤 Voice Priority", "price": 350, "description": "Skip voice channel queue", "duration": "10 days", "category": "🔑 Access"},
            {"name": "📱 Early Access", "price": 750, "description": "Beta features and updates", "duration": "30 days", "category": "🔑 Access"}
        ]
        
        fun_items = [
            {"name": "🎲 Luck Boost", "price": 450, "description": "Better RNG in games for 1 week", "duration": "7 days", "category": "🎮 Fun & Games"},
            {"name": "🎊 Party Mode", "price": 200, "description": "Special effects on messages", "duration": "6 hours", "category": "🎮 Fun & Games"},
            {"name": "🎯 Double Daily", "price": 300, "description": "Can claim daily rewards twice", "duration": "3 days", "category": "🎮 Fun & Games"},
            {"name": "🔮 Mystery Box", "price": 500, "description": "Random surprise reward daily", "duration": "7 days", "category": "🎮 Fun & Games"}
        ]
        
        all_items = power_items + social_items + access_items + fun_items
        
        # Group items by category
        categories = {}
        for item in all_items:
            cat = item["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        # Add category sections to embed
        for category, items in categories.items():
            item_list = []
            for item in items:
                item_list.append(f"**{item['name']}** - `{item['price']}` coins\n_{item['description']} • {item['duration']}_")
            
            embed.add_field(
                name=f"{category}",
                value="\n\n".join(item_list),
                inline=True
            )
        
        # Add helpful footer with tips
        embed.add_field(
            name="💡 **Pro Shopping Tips**",
            value="• Stack compatible boosts for maximum effect\n• VIP items unlock special server features\n• Check `/myitems` to see active purchases\n• All items are temporary but provide great value!",
            inline=False
        )
        
        embed.set_footer(text="✨ Premium Temporary Shop • All purchases enhance your experience!")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="🛒 Purchase premium temporary items from the shop")
    @app_commands.describe(item="Item to purchase from the premium shop")
    @app_commands.choices(item=[
        # Power-Ups
        app_commands.Choice(name="⚡ XP Boost (200 coins - 1 hour)", value="xp_boost"),
        app_commands.Choice(name="🍪 Cookie Multiplier (300 coins - 2 hours)", value="cookie_multiplier"),
        app_commands.Choice(name="💰 Coin Boost (250 coins - 3 hours)", value="coin_boost"),
        app_commands.Choice(name="🎯 Work Success (400 coins - 24 hours)", value="work_success"),
        # Social Status
        app_commands.Choice(name="🌟 VIP Role (500 coins - 3 days)", value="vip_role"),
        app_commands.Choice(name="🎨 Custom Color (800 coins - 7 days)", value="custom_color"),
        app_commands.Choice(name="👑 Crown Badge (600 coins - 14 days)", value="crown_badge"),
        app_commands.Choice(name="🌈 Rainbow Name (1200 coins - 5 days)", value="rainbow_name"),
        # Access
        app_commands.Choice(name="🚪 VIP Channels (1000 coins - 14 days)", value="vip_channels"),
        app_commands.Choice(name="📝 Nickname Freedom (150 coins - 7 days)", value="nickname_freedom"),
        app_commands.Choice(name="🎤 Voice Priority (350 coins - 10 days)", value="voice_priority"),
        app_commands.Choice(name="📱 Early Access (750 coins - 30 days)", value="early_access"),
        # Fun & Games
        app_commands.Choice(name="🎲 Luck Boost (450 coins - 7 days)", value="luck_boost"),
        app_commands.Choice(name="🎊 Party Mode (200 coins - 6 hours)", value="party_mode"),
        app_commands.Choice(name="🎯 Double Daily (300 coins - 3 days)", value="double_daily"),
        app_commands.Choice(name="🔮 Mystery Box (500 coins - 7 days)", value="mystery_box")
    ])
    async def buy(self, interaction: discord.Interaction, item: str):
        shop_items = {
            # Power-Ups
            "xp_boost": {"price": 200, "name": "⚡ XP Boost", "duration": 3600, "description": "1 hour", "category": "Power-Up"},
            "cookie_multiplier": {"price": 300, "name": "🍪 Cookie Multiplier", "duration": 7200, "description": "2 hours", "category": "Power-Up"},
            "coin_boost": {"price": 250, "name": "💰 Coin Boost", "duration": 10800, "description": "3 hours", "category": "Power-Up"},
            "work_success": {"price": 400, "name": "🎯 Work Success", "duration": 86400, "description": "24 hours", "category": "Power-Up"},
            # Social Status  
            "vip_role": {"price": 500, "name": "🌟 VIP Role", "duration": 259200, "description": "3 days", "category": "Social"},
            "custom_color": {"price": 800, "name": "🎨 Custom Color", "duration": 604800, "description": "7 days", "category": "Social"},
            "crown_badge": {"price": 600, "name": "👑 Crown Badge", "duration": 1209600, "description": "14 days", "category": "Social"},
            "rainbow_name": {"price": 1200, "name": "🌈 Rainbow Name", "duration": 432000, "description": "5 days", "category": "Social"},
            # Access
            "vip_channels": {"price": 1000, "name": "🚪 VIP Channels", "duration": 1209600, "description": "14 days", "category": "Access"},
            "nickname_freedom": {"price": 150, "name": "📝 Nickname Freedom", "duration": 604800, "description": "7 days", "category": "Access"},
            "voice_priority": {"price": 350, "name": "🎤 Voice Priority", "duration": 864000, "description": "10 days", "category": "Access"},
            "early_access": {"price": 750, "name": "📱 Early Access", "duration": 2592000, "description": "30 days", "category": "Access"},
            # Fun & Games
            "luck_boost": {"price": 450, "name": "🎲 Luck Boost", "duration": 604800, "description": "7 days", "category": "Fun"},
            "party_mode": {"price": 200, "name": "🎊 Party Mode", "duration": 21600, "description": "6 hours", "category": "Fun"},
            "double_daily": {"price": 300, "name": "🎯 Double Daily", "duration": 259200, "description": "3 days", "category": "Fun"},
            "mystery_box": {"price": 500, "name": "🔮 Mystery Box", "duration": 604800, "description": "7 days", "category": "Fun"}
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
            
            # Create premium purchase embed
            embed = discord.Embed(
                title="✨ **Premium Purchase Successful!**",
                description=f"**{item_data['name']}** is now active on your account!",
                color=0x9932cc
            )
            
            # Purchase details
            embed.add_field(
                name="🛒 **Purchase Details**", 
                value=f"**Item:** {item_data['name']}\n**Cost:** {item_data['price']:,} coins\n**Duration:** {item_data['description']}\n**Category:** {item_data['category']}", 
                inline=True
            )
            
            embed.add_field(
                name="💰 **Account Info**", 
                value=f"**New Balance:** {new_balance:,} coins\n**Active Until:** <t:{int((datetime.now().timestamp() + item_data['duration']))}:R>", 
                inline=True
            )
            
            # Handle specific items with enhanced features
            if item == "vip_role":
                # Find or create VIP role
                vip_role = discord.utils.get(interaction.guild.roles, name="🌟 VIP")
                if not vip_role:
                    vip_role = await interaction.guild.create_role(
                        name="🌟 VIP", 
                        color=discord.Color.gold(),
                        reason="Premium VIP role from shop"
                    )
                
                await interaction.user.add_roles(vip_role)
                db.add_temporary_role(interaction.user.id, vip_role.id, item_data['duration'])
                embed.add_field(name="🌟 **VIP Status Active**", value="• Exclusive role color\n• Special permissions\n• VIP channel access\n• Priority support", inline=False)
                
            elif item == "custom_color":
                db.add_temporary_purchase(interaction.user.id, "custom_color", item_data['duration'])
                embed.add_field(name="🎨 **Custom Color Ready**", value=f"Contact a moderator to set your personalized role color!\nActive for {item_data['description']}", inline=False)
                
            elif item == "xp_boost":
                db.add_temporary_purchase(interaction.user.id, "xp_boost", item_data['duration'])
                embed.add_field(name="⚡ **XP Boost Activated**", value="You now earn **2x XP** from all activities!", inline=False)
                
            elif item == "cookie_multiplier":
                db.add_temporary_purchase(interaction.user.id, "cookie_multiplier", item_data['duration'])
                embed.add_field(name="🍪 **Cookie Multiplier Active**", value="You now earn **3x cookies** from all sources!", inline=False)
                
            elif item == "coin_boost":
                db.add_temporary_purchase(interaction.user.id, "coin_boost", item_data['duration'])
                embed.add_field(name="💰 **Coin Boost Engaged**", value="Work earnings increased by **50%**!", inline=False)
                
            elif item == "work_success":
                db.add_temporary_purchase(interaction.user.id, "work_success", item_data['duration'])
                embed.add_field(name="🎯 **Work Success Guaranteed**", value="All work attempts will succeed for 24 hours!", inline=False)
                
            elif item == "crown_badge":
                db.add_temporary_purchase(interaction.user.id, "crown_badge", item_data['duration'])
                embed.add_field(name="👑 **Crown Badge Equipped**", value="Your profile now displays a golden crown!", inline=False)
                
            elif item == "rainbow_name":
                db.add_temporary_purchase(interaction.user.id, "rainbow_name", item_data['duration'])
                embed.add_field(name="🌈 **Rainbow Name Active**", value="Your nickname now has animated rainbow effects!", inline=False)
                
            elif item == "vip_channels":
                db.add_temporary_purchase(interaction.user.id, "vip_channels", item_data['duration'])
                embed.add_field(name="🚪 **VIP Channels Unlocked**", value="Access granted to exclusive premium channels!", inline=False)
                
            elif item == "nickname_freedom":
                db.add_temporary_purchase(interaction.user.id, "nickname_freedom", item_data['duration'])
                embed.add_field(name="📝 **Nickname Freedom Granted**", value="Change your nickname anytime using Discord's nickname feature!", inline=False)
                
            elif item == "voice_priority":
                db.add_temporary_purchase(interaction.user.id, "voice_priority", item_data['duration'])
                embed.add_field(name="🎤 **Voice Priority Enabled**", value="Skip the queue in voice channels and get priority access!", inline=False)
                
            elif item == "early_access":
                db.add_temporary_purchase(interaction.user.id, "early_access", item_data['duration'])
                embed.add_field(name="📱 **Early Access Activated**", value="Get beta features and updates before everyone else!", inline=False)
                
            elif item == "luck_boost":
                db.add_temporary_purchase(interaction.user.id, "luck_boost", item_data['duration'])
                embed.add_field(name="🎲 **Luck Boost Active**", value="Improved RNG in games, gambling, and random events!", inline=False)
                
            elif item == "party_mode":
                db.add_temporary_purchase(interaction.user.id, "party_mode", item_data['duration'])
                embed.add_field(name="🎊 **Party Mode ON**", value="Your messages now have special party effects and animations!", inline=False)
                
            elif item == "double_daily":
                db.add_temporary_purchase(interaction.user.id, "double_daily", item_data['duration'])
                embed.add_field(name="🎯 **Double Daily Active**", value="Claim daily rewards twice per day for the next 3 days!", inline=False)
                
            elif item == "mystery_box":
                db.add_temporary_purchase(interaction.user.id, "mystery_box", item_data['duration'])
                embed.add_field(name="🔮 **Mystery Box Ready**", value="Receive random surprise rewards daily for a week!", inline=False)
            
            # Add usage tips
            embed.add_field(
                name="💡 **Pro Tips**",
                value="• Use `/myitems` to check all active purchases\n• Stack compatible boosts for maximum effect\n• Premium items provide exclusive server benefits!",
                inline=False
            )
            
            embed.set_footer(text="✨ Premium Shop • Thank you for your purchase!")
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
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

    @app_commands.command(name="myitems", description="📋 View your active temporary purchases and their remaining time")
    async def myitems(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            active_purchases = db.get_active_temporary_purchases(user_id)
            active_roles = db.get_active_temporary_roles(user_id)
            
            embed = discord.Embed(
                title="📋 **Your Active Premium Items**",
                description="Here are all your currently active temporary purchases and their remaining time:",
                color=0x9932cc,
                timestamp=datetime.now()
            )
            
            if not active_purchases and not active_roles:
                embed.description = "You don't have any active premium items.\n\n💡 **Visit `/shop` to browse our premium temporary items!**"
                embed.color = 0x6c757d
                embed.add_field(
                    name="🛒 **Available Categories**",
                    value="• 🚀 **Power-Ups** - XP, Cookie & Coin boosts\n• 👑 **Social Status** - VIP roles, custom colors\n• 🔑 **Access** - Exclusive channels & features\n• 🎮 **Fun & Games** - Special effects & bonuses",
                    inline=False
                )
            else:
                current_time = datetime.now().timestamp()
                
                # Group items by category
                categories = {
                    "🚀 Power-Ups": [],
                    "👑 Social Status": [],
                    "🔑 Access": [],
                    "🎮 Fun & Games": []
                }
                
                # Map item types to categories
                category_mapping = {
                    "xp_boost": "🚀 Power-Ups",
                    "cookie_multiplier": "🚀 Power-Ups", 
                    "coin_boost": "🚀 Power-Ups",
                    "work_success": "🚀 Power-Ups",
                    "vip_role": "👑 Social Status",
                    "custom_color": "👑 Social Status",
                    "crown_badge": "👑 Social Status",
                    "rainbow_name": "👑 Social Status",
                    "vip_channels": "🔑 Access",
                    "nickname_freedom": "🔑 Access",
                    "voice_priority": "🔑 Access",
                    "early_access": "🔑 Access",
                    "luck_boost": "🎮 Fun & Games",
                    "party_mode": "🎮 Fun & Games",
                    "double_daily": "🎮 Fun & Games",
                    "mystery_box": "🎮 Fun & Games"
                }
                
                # Process temporary purchases
                for purchase in active_purchases:
                    item_type = purchase.get("item_type", "unknown")
                    end_time = purchase.get("end_time", 0)
                    
                    if end_time == 0:  # Permanent
                        time_left = "Permanent"
                    else:
                        time_left = f"<t:{int(end_time)}:R>"
                    
                    # Get item display info
                    item_names = {
                        "xp_boost": "⚡ XP Boost",
                        "cookie_multiplier": "🍪 Cookie Multiplier",
                        "coin_boost": "💰 Coin Boost", 
                        "work_success": "🎯 Work Success",
                        "custom_color": "🎨 Custom Color",
                        "crown_badge": "👑 Crown Badge",
                        "rainbow_name": "🌈 Rainbow Name",
                        "vip_channels": "🚪 VIP Channels",
                        "nickname_freedom": "📝 Nickname Freedom",
                        "voice_priority": "🎤 Voice Priority",
                        "early_access": "📱 Early Access",
                        "luck_boost": "🎲 Luck Boost",
                        "party_mode": "🎊 Party Mode",
                        "double_daily": "🎯 Double Daily",
                        "mystery_box": "🔮 Mystery Box"
                    }
                    
                    item_name = item_names.get(item_type, item_type.title())
                    category = category_mapping.get(item_type, "🎮 Fun & Games")
                    
                    categories[category].append(f"**{item_name}**\nExpires: {time_left}")
                
                # Process temporary roles
                for role_data in active_roles:
                    role_id = role_data.get("role_id")
                    end_time = role_data.get("end_time", 0)
                    
                    role = interaction.guild.get_role(role_id)
                    role_name = role.name if role else f"Role {role_id}"
                    
                    time_left = f"<t:{int(end_time)}:R>" if end_time > 0 else "Permanent"
                    categories["👑 Social Status"].append(f"**{role_name}**\nExpires: {time_left}")
                
                # Add non-empty categories to embed
                for category, items in categories.items():
                    if items:
                        embed.add_field(
                            name=category,
                            value="\n\n".join(items),
                            inline=True
                        )
                
                # Add statistics
                total_active = len(active_purchases) + len(active_roles)
                embed.add_field(
                    name="📊 **Summary**",
                    value=f"**Total Active Items:** {total_active}\n**Premium Status:** {'✨ Active' if total_active > 0 else '⏸️ None'}\n**Account Type:** {'🌟 Premium User' if total_active >= 3 else '🔰 Standard User'}",
                    inline=False
                )
            
            embed.set_author(name=f"{interaction.user.display_name}'s Premium Items", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="✨ Premium Shop • Use /shop to get more items!")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving your items: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
