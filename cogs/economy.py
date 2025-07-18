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

# Independent Job Progression System - No Level Requirements!
JOB_TIERS = {
    "entry": {
        "name": "Entry Level",
        "unlock_requirement": 0,  # Available immediately
        "promotion_requirement": 10,  # 10 successful works to promote
        "jobs": [
            {
                "name": "Pizza Delivery", 
                "emoji": "🍕",
                "min_pay": 15, 
                "max_pay": 30, 
                "description": "delivering hot pizzas",
                "full_description": "🍕 You hop on your delivery bike and navigate busy streets, delivering steaming hot pizzas to hungry customers.",
                "skill": "delivery"
            },
            {
                "name": "Data Entry", 
                "emoji": "📋",
                "min_pay": 20, 
                "max_pay": 35, 
                "description": "entering data accurately",
                "full_description": "📋 You carefully input information into computer systems, ensuring accuracy and attention to detail.",
                "skill": "admin"
            },
            {
                "name": "Customer Support", 
                "emoji": "📞",
                "min_pay": 18, 
                "max_pay": 32, 
                "description": "helping customers",
                "full_description": "📞 You assist customers with their questions and problems, providing friendly and helpful service.",
                "skill": "support"
            }
        ]
    },
    "junior": {
        "name": "Junior Level",
        "unlock_requirement": 10,  # 10 successful works from entry level
        "promotion_requirement": 25,  # 25 successful works to promote
        "jobs": [
            {
                "name": "Junior Developer", 
                "emoji": "💻",
                "min_pay": 25, 
                "max_pay": 50, 
                "description": "writing simple code",
                "full_description": "💻 You write and test basic code, learning the fundamentals of software development.",
                "skill": "development"
            },
            {
                "name": "Content Creator", 
                "emoji": "📝",
                "min_pay": 30, 
                "max_pay": 55, 
                "description": "creating engaging content",
                "full_description": "📝 You create articles, posts, and media content that engages and informs audiences.",
                "skill": "creative"
            },
            {
                "name": "Sales Associate", 
                "emoji": "💼",
                "min_pay": 28, 
                "max_pay": 45, 
                "description": "selling products and services",
                "full_description": "💼 You connect with customers to understand their needs and provide suitable solutions.",
                "skill": "sales"
            }
        ]
    },
    "mid": {
        "name": "Mid Level",
        "unlock_requirement": 35,  # 35 total successful works
        "promotion_requirement": 60,  # 60 successful works to promote
        "jobs": [
            {
                "name": "Software Developer", 
                "emoji": "🔨",
                "min_pay": 40, 
                "max_pay": 80, 
                "description": "developing applications",
                "full_description": "🔨 You build robust applications and features, solving complex problems with code.",
                "skill": "development"
            },
            {
                "name": "Marketing Specialist", 
                "emoji": "📈",
                "min_pay": 45, 
                "max_pay": 75, 
                "description": "promoting products effectively",
                "full_description": "📈 You develop and execute marketing strategies to reach target audiences.",
                "skill": "marketing"
            },
            {
                "name": "Project Coordinator", 
                "emoji": "📊",
                "min_pay": 50, 
                "max_pay": 85, 
                "description": "coordinating team projects",
                "full_description": "📊 You ensure projects run smoothly by coordinating teams and managing timelines.",
                "skill": "management"
            }
        ]
    },
    "senior": {
        "name": "Senior Level", 
        "unlock_requirement": 95,  # 95 total successful works
        "promotion_requirement": 150,  # 150 successful works to promote
        "jobs": [
            {
                "name": "Senior Engineer", 
                "emoji": "🔧",
                "min_pay": 70, 
                "max_pay": 120, 
                "description": "architecting solutions",
                "full_description": "🔧 You design and implement complex systems that form the backbone of applications.",
                "skill": "engineering"
            },
            {
                "name": "Team Lead", 
                "emoji": "👥",
                "min_pay": 80, 
                "max_pay": 130, 
                "description": "leading development teams",
                "full_description": "👥 You guide and mentor team members while delivering high-quality projects.",
                "skill": "leadership"
            },
            {
                "name": "Product Manager", 
                "emoji": "🎯",
                "min_pay": 85, 
                "max_pay": 140, 
                "description": "managing product strategy",
                "full_description": "🎯 You define product vision and strategy, working with stakeholders to deliver value.",
                "skill": "strategy"
            }
        ]
    },
    "executive": {
        "name": "Executive Level",
        "unlock_requirement": 245,  # 245 total successful works
        "promotion_requirement": 500,  # 500 successful works (prestige level)
        "jobs": [
            {
                "name": "Engineering Director", 
                "emoji": "⚙️",
                "min_pay": 120, 
                "max_pay": 200, 
                "description": "directing engineering efforts",
                "full_description": "⚙️ You oversee multiple engineering teams and set technical direction for the organization.",
                "skill": "engineering"
            },
            {
                "name": "VP of Product", 
                "emoji": "🚀",
                "min_pay": 150, 
                "max_pay": 250, 
                "description": "leading product innovation",
                "full_description": "🚀 You drive product innovation and strategy across the entire organization.",
                "skill": "strategy"
            },
            {
                "name": "Chief Technology Officer", 
                "emoji": "👑",
                "min_pay": 200, 
                "max_pay": 350, 
                "description": "setting technology vision",
                "full_description": "👑 You set the technology vision and strategy for the entire company's future.",
                "skill": "leadership"
            }
        ]
    },
    "legendary": {
        "name": "Legendary Status",
        "unlock_requirement": 745,  # 745 total successful works - rare achievement
        "promotion_requirement": 9999,  # Max level essentially
        "jobs": [
            {
                "name": "Industry Innovator", 
                "emoji": "💡",
                "min_pay": 300, 
                "max_pay": 500, 
                "description": "revolutionizing the industry",
                "full_description": "💡 You create groundbreaking innovations that change entire industries forever.",
                "skill": "innovation"
            },
            {
                "name": "Tech Visionary", 
                "emoji": "🌟",
                "min_pay": 400, 
                "max_pay": 600, 
                "description": "shaping the future of technology",
                "full_description": "🌟 You envision and create the technologies that will define the next generation.",
                "skill": "visionary"
            },
            {
                "name": "Global Leader", 
                "emoji": "🌍",
                "min_pay": 500, 
                "max_pay": 800, 
                "description": "leading worldwide initiatives",
                "full_description": "🌍 You lead global initiatives that impact millions of people worldwide.",
                "skill": "global"
            }
        ]
    }
}

# Work cooldown increased to 2.5 hours for better balance
WORK_COOLDOWN_HOURS = 2.5

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Economy] Loaded successfully.")

    def get_user_job_stats(self, user_id):
        """Get user's job statistics and progression"""
        user_data = db.get_user_data(user_id)
        return {
            "total_works": user_data.get("total_works", 0),
            "successful_works": user_data.get("successful_works", 0),
            "failed_works": user_data.get("failed_works", 0),
            "current_job": user_data.get("current_job", None),
            "current_tier": user_data.get("job_tier", "entry"),
            "consecutive_works": user_data.get("consecutive_works", 0),
            "last_work_success": user_data.get("last_work_success", True),
            "work_streak": user_data.get("work_streak", 0),
            "missed_work_days": user_data.get("missed_work_days", 0)
        }

    def get_available_jobs(self, user_id):
        """Get jobs available to user based on their work history"""
        job_stats = self.get_user_job_stats(user_id)
        successful_works = job_stats["successful_works"]
        current_tier = job_stats["current_tier"]
        
        # Start with current tier jobs
        available_tiers = [current_tier]
        
        # Check if user can access higher tiers
        for tier_name, tier_data in JOB_TIERS.items():
            if successful_works >= tier_data["unlock_requirement"]:
                if tier_name not in available_tiers:
                    available_tiers.append(tier_name)
        
        # Get all jobs from available tiers
        available_jobs = []
        for tier_name in available_tiers:
            tier_jobs = JOB_TIERS[tier_name]["jobs"]
            for job in tier_jobs:
                job_with_tier = job.copy()
                job_with_tier["tier"] = tier_name
                job_with_tier["tier_name"] = JOB_TIERS[tier_name]["name"]
                available_jobs.append(job_with_tier)
        
        return available_jobs

    def check_promotion_eligibility(self, user_id):
        """Check if user is eligible for promotion"""
        job_stats = self.get_user_job_stats(user_id)
        current_tier = job_stats["current_tier"]
        successful_works = job_stats["successful_works"]
        
        if current_tier not in JOB_TIERS:
            return False, "Invalid tier"
        
        tier_data = JOB_TIERS[current_tier]
        promotion_requirement = tier_data["promotion_requirement"]
        
        if successful_works >= promotion_requirement:
            # Find next tier
            tier_order = list(JOB_TIERS.keys())
            current_index = tier_order.index(current_tier)
            
            if current_index < len(tier_order) - 1:
                next_tier = tier_order[current_index + 1]
                return True, next_tier
        
        return False, f"Need {promotion_requirement - successful_works} more successful works"

    def process_work_result(self, user_id, job, success, earnings=0):
        """Process work result and update job statistics"""
        try:
            # Validate inputs
            if not user_id or not job:
                return {"success": False, "error": "Invalid user ID or job data"}
            
            if not isinstance(job, dict) or "name" not in job:
                return {"success": False, "error": "Invalid job data structure"}
                
            user_data = db.get_user_data(user_id)
            if not user_data:
                user_data = {}
            
            # Update work statistics
            total_works = user_data.get("total_works", 0) + 1
            successful_works = user_data.get("successful_works", 0)
            failed_works = user_data.get("failed_works", 0)
            consecutive_works = user_data.get("consecutive_works", 0)
            work_streak = user_data.get("work_streak", 0)
            missed_work_days = user_data.get("missed_work_days", 0)
            
            # Check for missed work (if last work was more than 1 day ago)
            last_work = user_data.get("last_work", 0)
            current_time = datetime.now().timestamp()
            hours_since_last_work = (current_time - last_work) / 3600
            
            if success:
                successful_works += 1
                consecutive_works += 1
                
                # Reset missed days if working consistently
                if hours_since_last_work < 48:  # Within 2 days
                    work_streak += 1
                else:
                    work_streak = 1  # Reset streak
                    
                if hours_since_last_work > 72:  # More than 3 days
                    missed_work_days += 1
                    
            else:
                failed_works += 1
                consecutive_works = 0  # Reset consecutive works on failure
                work_streak = max(0, work_streak - 1)  # Reduce streak on failure
            
            # Check for promotion
            promotion_eligible, promotion_info = self.check_promotion_eligibility(user_id)
            promoted = False
            new_tier = user_data.get("job_tier", "entry")
            
            if promotion_eligible and isinstance(promotion_info, str):
                new_tier = promotion_info
                promoted = True
            
            # Check for demotion (if too many failures or missed days)
            demoted = False
            if missed_work_days >= 7 and new_tier != "entry":  # Missed work for a week
                tier_order = list(JOB_TIERS.keys())
                current_index = tier_order.index(new_tier)
                if current_index > 0:
                    new_tier = tier_order[current_index - 1]
                    demoted = True
                    missed_work_days = 0  # Reset after demotion
            
            # Update database
            update_data = {
                "total_works": total_works,
                "successful_works": successful_works,
                "failed_works": failed_works,
                "consecutive_works": consecutive_works,
                "work_streak": work_streak,
                "missed_work_days": missed_work_days,
                "last_work_success": success,
                "current_job": job["name"],
                "job_tier": new_tier,
                "last_work": current_time
            }
            
            if earnings > 0:
                db.add_coins(user_id, earnings)
            
            # Update user data in database
            if db.users_collection is not None:
                db.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": update_data},
                    upsert=True
                )
            
            return {
                "success": success,
                "promoted": promoted,
                "demoted": demoted,
                "new_tier": new_tier,
                "earnings": earnings,
                "consecutive_works": consecutive_works,
                "work_streak": work_streak,
                "total_works": total_works,
                "successful_works": successful_works
            }
            
        except Exception as e:
            print(f"Error processing work result: {e}")
            return {"success": False, "error": str(e)}

    def get_work_success_rate(self, user_id, job):
        """Calculate work success rate based on user's experience and job difficulty"""
        job_stats = self.get_user_job_stats(user_id)
        consecutive_works = job_stats["consecutive_works"]
        work_streak = job_stats["work_streak"]
        
        # Base success rate depends on job tier
        job_tier = job.get("tier", "entry")
        base_rates = {
            "entry": 0.85,      # 85% success rate for entry jobs
            "junior": 0.75,     # 75% success rate for junior jobs  
            "mid": 0.65,        # 65% success rate for mid-level jobs
            "senior": 0.55,     # 55% success rate for senior jobs
            "executive": 0.45,  # 45% success rate for executive jobs
            "legendary": 0.35   # 35% success rate for legendary jobs
        }
        
        base_success_rate = base_rates.get(job_tier, 0.75)
        
        # Bonuses for experience and consistency
        consecutive_bonus = min(0.15, consecutive_works * 0.02)  # Up to 15% bonus
        streak_bonus = min(0.10, work_streak * 0.01)  # Up to 10% bonus
        
        # Check for active work success boost
        user_data = db.get_user_data(user_id)
        active_purchases = user_data.get("temporary_purchases", [])
        has_work_boost = any(
            purchase.get("item_type") == "work_success" and 
            purchase.get("expires_at", 0) > datetime.now().timestamp()
            for purchase in active_purchases
        )
        
        work_boost = 1.0 if has_work_boost else 0.0  # Guaranteed success with boost
        
        final_success_rate = min(1.0, base_success_rate + consecutive_bonus + streak_bonus + work_boost)
        return final_success_rate

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

    @app_commands.command(name="work", description="💼 Independent career progression system - work your way up!")
    async def work(self, interaction: discord.Interaction):
        try:
            # ALWAYS defer first to prevent timeout
            await interaction.response.defer()
            
            # Ensure database connection is available
            if not hasattr(db, 'get_user_data'):
                await interaction.followup.send("❌ Database connection error. Please try again later.", ephemeral=True)
                return
                
            user_data = db.get_user_data(interaction.user.id)
            last_work = user_data.get('last_work', 0)
            current_time = datetime.now().timestamp()
            
            # New 2.5 hour cooldown with better error handling
            try:
                cooldown_seconds = int(WORK_COOLDOWN_HOURS * 3600)
            except (NameError, TypeError):
                cooldown_seconds = 9000  # Fallback to 2.5 hours
            
            if current_time - last_work < cooldown_seconds:
                time_left = cooldown_seconds - (current_time - last_work)
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                
                embed = discord.Embed(
                    title="⏰ **Work Cooldown**",
                    description=f"You need to rest! Come back in **{hours}h {minutes}m**.",
                    color=0xff9966,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="💡 Tip", 
                    value="Use this time to check `/profile` for your career progress or `/shop` for work boosts!", 
                    inline=False
                )
                embed.set_footer(text="💼 Quality work requires proper rest!")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Get user's job stats and available jobs with error handling
            try:
                job_stats = self.get_user_job_stats(interaction.user.id)
                available_jobs = self.get_available_jobs(interaction.user.id)
            except Exception as e:
                print(f"Error getting job data for user {interaction.user.id}: {e}")
                await interaction.followup.send(
                    "❌ Error loading your job data. Please try again in a moment.", 
                    ephemeral=True
                )
                return
            
            if not available_jobs:
                # Initialize user with entry level jobs if none available
                try:
                    db.users_collection.update_one(
                        {"user_id": interaction.user.id},
                        {"$set": {"job_tier": "entry", "total_works": 0, "successful_works": 0}},
                        upsert=True
                    )
                    available_jobs = self.get_available_jobs(interaction.user.id)
                except Exception as e:
                    print(f"Error initializing user job data: {e}")
                    
                if not available_jobs:
                    await interaction.followup.send("❌ No jobs available! Please contact an administrator.", ephemeral=True)
                    return

            # Create job selection view
            class JobSelectionView(discord.ui.View):
                def __init__(self, economy_cog, user_id):
                    super().__init__(timeout=120)
                    self.economy_cog = economy_cog
                    self.user_id = user_id
                
                @discord.ui.select(
                    placeholder="🎯 Choose your job opportunity...",
                    min_values=1,
                    max_values=1,
                    options=[
                        discord.SelectOption(
                            label=f"{job['name']} ({job['tier_name']})",
                            description=f"💰 {job['min_pay']}-{job['max_pay']} coins",
                            emoji=job.get("emoji", "💼"),
                            value=str(i)
                        ) for i, job in enumerate(available_jobs[:25])  # Discord limit
                    ]
                )
                async def job_select(self, select_interaction: discord.Interaction, select: discord.ui.Select):
                    try:
                        if select_interaction.user.id != self.user_id:
                            await select_interaction.response.send_message("❌ This is not your work selection!", ephemeral=True)
                            return
                        
                        if not select.values:
                            await select_interaction.response.send_message("❌ No job selected!", ephemeral=True)
                            return
                        
                        job_index = int(select.values[0])
                        if job_index >= len(available_jobs):
                            await select_interaction.response.send_message("❌ Invalid job selection!", ephemeral=True)
                            return
                            
                        selected_job = available_jobs[job_index]
                        
                        if not selected_job or not isinstance(selected_job, dict):
                            await select_interaction.response.send_message("❌ Job data corrupted. Please try again.", ephemeral=True)
                            return
                    except Exception as e:
                        print(f"Error in job_select: {e}")
                        await select_interaction.response.send_message("❌ Work system error. Please try again.", ephemeral=True)
                        return
                    
                    # Calculate success rate
                    success_rate = self.economy_cog.get_work_success_rate(self.user_id, selected_job)
                    work_successful = random.random() < success_rate
                    
                    # Calculate earnings
                    base_earnings = random.randint(selected_job["min_pay"], selected_job["max_pay"])
                    
                    # Experience bonus based on work streak
                    streak_bonus = min(20, job_stats["work_streak"] * 2)  # Up to 20 coins bonus
                    total_earnings = base_earnings + streak_bonus if work_successful else 0
                    
                    # Process work result
                    result = self.economy_cog.process_work_result(
                        self.user_id, selected_job, work_successful, total_earnings
                    )
                    
                    if not result or result.get("success") is False:
                        error_msg = result.get("error") if result else "Unknown error"
                        await select_interaction.response.send_message(f"❌ Error processing work: {error_msg}", ephemeral=True)
                        return
                    
                    # Create result embed
                    if work_successful:
                        embed = discord.Embed(
                            title="✅ **Work Successful!**",
                            description=f"**{selected_job['name']}** - {selected_job['full_description']}",
                            color=0x00d4aa,
                            timestamp=datetime.now()
                        )
                        
                        embed.add_field(name="💰 Base Earnings", value=f"+{base_earnings} coins", inline=True)
                        if streak_bonus > 0:
                            embed.add_field(name="🔥 Streak Bonus", value=f"+{streak_bonus} coins", inline=True)
                        embed.add_field(name="💵 Total Earned", value=f"**+{total_earnings} coins**", inline=True)
                        
                        # Career progress
                        embed.add_field(
                            name="🏆 Career Progress",
                            value=f"**Successful Works:** {result['successful_works']}\n**Work Streak:** {result['work_streak']}\n**Current Tier:** {result['new_tier'].title()}",
                            inline=True
                        )
                        
                        # Check for promotions/demotions
                        if result.get("promoted"):
                            embed.add_field(
                                name="🎉 **PROMOTION!**",
                                value=f"Congratulations! You've been promoted to **{result['new_tier'].title()} Level**!",
                                inline=False
                            )
                        elif result.get("demoted"):
                            embed.add_field(
                                name="🔄 **Demotion**",
                                value=f"Due to missed work, you've been moved to **{result['new_tier'].title()} Level**.",
                                inline=False
                            )
                        
                        # AUTOMATIC PROMOTION CHECK - happens immediately
                        promotion_eligible, promotion_info = self.economy_cog.check_promotion_eligibility(self.user_id)
                        if promotion_eligible and isinstance(promotion_info, str):
                            # AUTOMATIC PROMOTION - No button needed
                            try:
                                # Update user's tier in database immediately
                                update_data = {"job_tier": promotion_info}
                                db.users_collection.update_one(
                                    {"user_id": self.user_id},
                                    {"$set": update_data},
                                    upsert=True
                                )
                                
                                # Get new tier info
                                new_tier_data = JOB_TIERS.get(promotion_info, {})
                                tier_name = new_tier_data.get("name", promotion_info.title())
                                
                                embed.add_field(
                                    name="� **AUTOMATIC PROMOTION AWARDED!**",
                                    value=f"🏆 **Promoted to {tier_name}!**\n💰 Higher paying jobs unlocked\n🎯 New responsibilities available\n✨ Career advancement achieved!",
                                    inline=False
                                )
                                
                                print(f"🎉 Automatic promotion: {select_interaction.user.display_name} promoted to {promotion_info}")
                                
                            except Exception as e:
                                print(f"Error processing automatic promotion: {e}")
                        
                        # Next promotion info for non-eligible users
                        elif not promotion_eligible and isinstance(promotion_info, str):
                            embed.add_field(
                                name="🎯 **Next Promotion**",
                                value=promotion_info,
                                inline=False
                            )
                        
                        embed.set_footer(text=f"💼 Come back in {WORK_COOLDOWN_HOURS} hours for more work!")
                        
                    else:
                        embed = discord.Embed(
                            title="⚠️ **Work Failed**",
                            description=f"**{selected_job['name']}** - The job didn't go as planned this time.",
                            color=0xff9966,
                            timestamp=datetime.now()
                        )
                        
                        embed.add_field(
                            name="💭 What Happened",
                            value=f"The {selected_job['name'].lower()} was more challenging than expected. Don't worry, this happens!",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="💪 Your Stats",
                            value=f"**Success Rate:** {success_rate:.1%}\n**Consecutive Works:** {result['consecutive_works']}\n**Total Works:** {result['total_works']}",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="💡 Improvement Tips",
                            value="• Work consistently to build your streak\n• Try easier jobs to rebuild confidence\n• Consider buying work success boost from `/shop`",
                            inline=False
                        )
                        
                        embed.set_footer(text=f"💪 Try again in {WORK_COOLDOWN_HOURS} hours!")
                    
                    embed.set_author(
                        name=f"{select_interaction.user.display_name}'s Work Report", 
                        icon_url=select_interaction.user.display_avatar.url
                    )
                    
                    await select_interaction.response.edit_message(embed=embed, view=None)
            
            # Create main work embed
            embed = discord.Embed(
                title="💼 **Career Progression System**",
                description=f"Welcome to your independent career! Progress through jobs based on your work history, not XP levels.\n\n**🏆 Your Current Status:**",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # User stats section
            current_tier_name = JOB_TIERS[job_stats["current_tier"]]["name"]
            embed.add_field(
                name="📊 **Career Stats**",
                value=f"**Current Tier:** {current_tier_name}\n**Successful Works:** {job_stats['successful_works']}\n**Work Streak:** {job_stats['work_streak']}\n**Success Rate:** {(job_stats['successful_works'] / max(1, job_stats['total_works']) * 100):.1f}%",
                inline=True
            )
            
            # Available jobs by tier
            jobs_by_tier = {}
            for job in available_jobs:
                tier_name = job["tier_name"]
                if tier_name not in jobs_by_tier:
                    jobs_by_tier[tier_name] = []
                jobs_by_tier[tier_name].append(job)
            
            job_list = []
            for tier_name, tier_jobs in jobs_by_tier.items():
                job_list.append(f"**{tier_name}:**")
                for job in tier_jobs[:3]:  # Limit display
                    success_rate = self.get_work_success_rate(interaction.user.id, job)
                    job_list.append(f"{job['emoji']} {job['name']} - {job['min_pay']}-{job['max_pay']} coins ({success_rate:.0%} success)")
                if len(tier_jobs) > 3:
                    job_list.append(f"   _...and {len(tier_jobs) - 3} more_")
                job_list.append("")
            
            embed.add_field(
                name="🎯 **Available Jobs**",
                value="\n".join(job_list[:15]) if job_list else "No jobs available",  # Limit length
                inline=False
            )
            
            # Promotion info
            promotion_eligible, promotion_info = self.check_promotion_eligibility(interaction.user.id)
            if promotion_eligible:
                embed.add_field(
                    name="🎉 **Automatic Promotion Ready!**",
                    value=f"You'll be promoted to **{promotion_info.title()} Level** when you work next!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎯 **Next Promotion**",
                    value=promotion_info,
                    inline=False
                )
            
            embed.add_field(
                name="💡 **System Features**",
                value="• **Independent progression** - No XP requirements!\n• **Work streak bonuses** - Consistent work pays off\n• **Automatic promotions** - Earned through performance\n• **Difficulty scaling** - Higher tiers = better pay, lower success rate",
                inline=False
            )
            
            embed.set_author(
                name=f"{interaction.user.display_name}'s Career Dashboard",
                icon_url=interaction.user.display_avatar.url
            )
            embed.set_footer(text="💼 Select a job from the dropdown below")
            
            view = JobSelectionView(self, interaction.user.id)
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            print(f"Work command error: {e}")
            try:
                await interaction.followup.send(f"❌ Error working: {str(e)}", ephemeral=True)
            except:
                # If followup also fails, try edit_original_response
                try:
                    await interaction.edit_original_response(content=f"❌ Error working: {str(e)}")
                except:
                    print(f"Failed to send error message: {e}")

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
        
        # Updated items: Only possible ones, prices increased moderately
        shop_items = [
            {"name": "⚡ XP Boost", "price": 300, "description": "Double XP gain for 2 hours", "duration": "2 hours", "category": "🚀 Power-Ups", "id": "xp_boost"},
            {"name": "💰 Coin Boost", "price": 400, "description": "1.5x coin earnings for 4 hours", "duration": "4 hours", "category": "🚀 Power-Ups", "id": "coin_boost"},
            {"name": "🎯 Work Success", "price": 600, "description": "Guaranteed work success for 12 hours", "duration": "12 hours", "category": "🚀 Power-Ups", "id": "work_success"},
            {"name": "🎲 Luck Boost", "price": 500, "description": "Better RNG in games for 24 hours", "duration": "24 hours", "category": "🚀 Power-Ups", "id": "luck_boost"},
            {"name": "📝 Custom Nickname", "price": 200, "description": "Change nickname anytime (7 days)", "duration": "7 days", "category": "🔑 Access", "id": "nickname_freedom"},
            {"name": "🎨 Custom Color", "price": 350, "description": "Personalized role color (5 days)", "duration": "5 days", "category": "🔑 Access", "id": "custom_color"},
            {"name": "📊 Double XP Daily", "price": 250, "description": "Claim double XP from daily for 3 days", "duration": "3 days", "category": "🎮 Fun & Games", "id": "double_daily"},
            {"name": "⏱️ Work Cooldown Reset", "price": 150, "description": "Instantly reset your work cooldown", "duration": "instant", "category": "🎮 Fun & Games", "id": "cooldown_reset"}
        ]
        
        # Group items by category
        categories = {}
        for item in shop_items:
            cat = item["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        for category, items in categories.items():
            item_list = []
            for item in items:
                item_list.append(f"**{item['name']}** - `{item['price']}` coins\n_{item['description']} • {item['duration']}_")
            embed.add_field(
                name=f"{category}",
                value="\n\n".join(item_list),
                inline=True
            )
        
        embed.add_field(
            name="💡 **Pro Shopping Tips**",
            value="• Stack compatible boosts for maximum effect\n• Check `/myitems` to see active purchases\n• All items are temporary but provide great value!",
            inline=False
        )
        
        embed.set_footer(text="✨ Premium Temporary Shop • All purchases enhance your experience!")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="🛒 Purchase simple and useful items from the shop")
    @app_commands.describe(item="Item to purchase from the shop")
    @app_commands.choices(item=[
        app_commands.Choice(name="⚡ XP Boost (300 coins - 2 hours)", value="xp_boost"),
        app_commands.Choice(name="💰 Coin Boost (400 coins - 4 hours)", value="coin_boost"),
        app_commands.Choice(name="🎯 Work Success (600 coins - 12 hours)", value="work_success"),
        app_commands.Choice(name="🎲 Luck Boost (500 coins - 24 hours)", value="luck_boost"),
        app_commands.Choice(name="📝 Custom Nickname (200 coins - 7 days)", value="nickname_freedom"),
        app_commands.Choice(name="🎨 Custom Color (350 coins - 5 days)", value="custom_color"),
        app_commands.Choice(name="📊 Double XP Daily (250 coins - 3 days)", value="double_daily"),
        app_commands.Choice(name="⏱️ Work Cooldown Reset (150 coins - instant)", value="cooldown_reset")
    ])
    async def buy(self, interaction: discord.Interaction, item: str):
        shop_items = {
            "xp_boost": {"price": 300, "name": "⚡ XP Boost", "duration": 7200, "description": "2 hours", "category": "Boost"},
            "coin_boost": {"price": 400, "name": "💰 Coin Boost", "duration": 14400, "description": "4 hours", "category": "Boost"},
            "work_success": {"price": 600, "name": "🎯 Work Success", "duration": 43200, "description": "12 hours", "category": "Boost"},
            "luck_boost": {"price": 500, "name": "🎲 Luck Boost", "duration": 86400, "description": "24 hours", "category": "Boost"},
            "nickname_freedom": {"price": 200, "name": "📝 Custom Nickname", "duration": 604800, "description": "7 days", "category": "Access"},
            "custom_color": {"price": 350, "name": "🎨 Custom Color", "duration": 432000, "description": "5 days", "category": "Access"},
            "double_daily": {"price": 250, "name": "📊 Double XP Daily", "duration": 259200, "description": "3 days", "category": "Feature"},
            "cooldown_reset": {"price": 150, "name": "⏱️ Work Cooldown Reset", "duration": 0, "description": "instant", "category": "Feature"}
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
            if item == "xp_boost":
                db.add_temporary_purchase(interaction.user.id, "xp_boost", item_data['duration'])
                embed.add_field(name="⚡ **XP Boost Activated**", value="You now earn **2x XP** from all activities!", inline=False)
                
            elif item == "coin_boost":
                db.add_temporary_purchase(interaction.user.id, "coin_boost", item_data['duration'])
                embed.add_field(name="💰 **Coin Boost Engaged**", value="Work earnings increased by **50%**!", inline=False)
                
            elif item == "work_success":
                db.add_temporary_purchase(interaction.user.id, "work_success", item_data['duration'])
                embed.add_field(name="🎯 **Work Success Guaranteed**", value="All work attempts will succeed for 24 hours!", inline=False)
                
            elif item == "luck_boost":
                db.add_temporary_purchase(interaction.user.id, "luck_boost", item_data['duration'])
                embed.add_field(name="🎲 **Luck Boost Active**", value="Improved RNG in games, gambling, and random events!", inline=False)
                
            elif item == "nickname_freedom":
                db.add_temporary_purchase(interaction.user.id, "nickname_freedom", item_data['duration'])
                embed.add_field(name="📝 **Nickname Freedom Granted**", value="Change your nickname anytime using Discord's nickname feature!", inline=False)
                
            elif item == "custom_color":
                db.add_temporary_purchase(interaction.user.id, "custom_color", item_data['duration'])
                embed.add_field(name="🎨 **Custom Color Ready**", value=f"Contact a moderator to set your personalized role color!\nActive for {item_data['description']}", inline=False)
                
            elif item == "double_daily":
                db.add_temporary_purchase(interaction.user.id, "double_daily", item_data['duration'])
                embed.add_field(name="🎯 **Double Daily Active**", value="Claim daily rewards twice per day for the next 3 days!", inline=False)
                
            elif item == "cooldown_reset":
                db.add_temporary_purchase(interaction.user.id, "cooldown_reset", item_data['duration'])
                embed.add_field(name="⏱️ **Work Cooldown Reset**", value="Your work cooldown has been reset! You can work again immediately.", inline=False)
            
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
            # DEFER IMMEDIATELY to prevent timeout
            await interaction.response.defer()
            
            user_data = db.get_user_data(interaction.user.id)
            balance = user_data.get('coins', 0)
            
            if balance < amount:
                await interaction.followup.send(
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
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error with coinflip: {str(e)}", ephemeral=True)
            except:
                pass  # Interaction might be invalid

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
                    value="• 🚀 **Power-Ups** - XP, Coin boosts\n• 👑 **Social Status** - VIP roles, custom colors\n• 🔑 **Access** - Exclusive channels & features\n• 🎮 **Fun & Games** - Special effects & bonuses",
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
                    "coin_boost": "🚀 Power-Ups", 
                    "work_success": "🚀 Power-Ups",
                    "luck_boost": "🚀 Power-Ups",
                    "nickname_freedom": "🔑 Access",
                    "custom_color": "🔑 Access",
                    "double_daily": "🎮 Fun & Games",
                    "cooldown_reset": "🎮 Fun & Games"
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
                        "coin_boost": "💰 Coin Boost", 
                        "work_success": "🎯 Work Success",
                        "luck_boost": "🎲 Luck Boost",
                        "nickname_freedom": "📝 Custom Nickname",
                        "custom_color": "🎨 Custom Color",
                        "double_daily": "📊 Double XP Daily",
                        "cooldown_reset": "⏱️ Work Cooldown Reset"
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

    @app_commands.command(name="addcoins", description="💰 Add coins to a user (Admin only)")
    @app_commands.describe(
        user="User to add coins to",
        amount="Amount of coins to add"
    )
    @app_commands.default_permissions(administrator=True)
    async def add_coins_admin(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Add coins to a user - admin only command"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can use this command!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return
        
        if amount > 1000000:  # Max limit for safety
            await interaction.response.send_message("❌ Amount too large! Maximum is 1,000,000 coins per operation.", ephemeral=True)
            return
        
        try:
            # Get user's current balance
            user_data = db.get_user_data(user.id)
            old_balance = user_data.get('coins', 0)
            
            # Add coins using database function
            success = db.add_coins(user.id, amount)
            
            if success:
                # Get new balance
                updated_data = db.get_user_data(user.id)
                new_balance = updated_data.get('coins', 0)
                
                # Create success embed
                embed = discord.Embed(
                    title="💰 **Coins Added Successfully**",
                    description=f"Successfully added **{amount:,}** coins to {user.mention}",
                    color=0x00d4aa,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="💳 **Transaction Details**",
                    value=f"**User:** {user.display_name}\n**Amount Added:** +{amount:,} coins\n**Previous Balance:** {old_balance:,} coins\n**New Balance:** {new_balance:,} coins",
                    inline=False
                )
                
                embed.add_field(
                    name="👤 **Admin Action**",
                    value=f"**Performed by:** {interaction.user.display_name}\n**Action:** Add Coins\n**Status:** ✅ Completed",
                    inline=False
                )
                
                embed.set_author(name="Admin Coin Management", icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text="💼 Administrative Action • Coins added to user account")
                
                await interaction.response.send_message(embed=embed)
                
                # Send notification to the user (optional)
                try:
                    user_embed = discord.Embed(
                        title="💰 **Coins Received!**",
                        description=f"An administrator has added **{amount:,}** coins to your account!",
                        color=0x00d4aa
                    )
                    user_embed.add_field(
                        name="💳 **Your New Balance**",
                        value=f"{new_balance:,} coins",
                        inline=False
                    )
                    user_embed.set_footer(text="💫 Enjoy your coins!")
                    
                    await user.send(embed=user_embed)
                except:
                    pass  # User might have DMs disabled
                
            else:
                await interaction.response.send_message("❌ Failed to add coins. Database error occurred.", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding coins: {str(e)}", ephemeral=True)

    @app_commands.command(name="removecoins", description="💸 Remove coins from a user (Admin only)")
    @app_commands.describe(
        user="User to remove coins from",
        amount="Amount of coins to remove"
    )
    @app_commands.default_permissions(administrator=True)
    async def remove_coins_admin(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Remove coins from a user - admin only command"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can use this command!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return
        
        try:
            # Get user's current balance
            user_data = db.get_user_data(user.id)
            old_balance = user_data.get('coins', 0)
            
            if old_balance < amount:
                await interaction.response.send_message(
                    f"❌ {user.display_name} only has {old_balance:,} coins, but you're trying to remove {amount:,} coins.",
                    ephemeral=True
                )
                return
            
            # Remove coins using database function
            success = db.remove_coins(user.id, amount)
            
            if success:
                # Get new balance
                updated_data = db.get_user_data(user.id)
                new_balance = updated_data.get('coins', 0)
                
                # Create success embed
                embed = discord.Embed(
                    title="💸 **Coins Removed Successfully**",
                    description=f"Successfully removed **{amount:,}** coins from {user.mention}",
                    color=0xff6b6b,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="💳 **Transaction Details**",
                    value=f"**User:** {user.display_name}\n**Amount Removed:** -{amount:,} coins\n**Previous Balance:** {old_balance:,} coins\n**New Balance:** {new_balance:,} coins",
                    inline=False
                )
                
                embed.add_field(
                    name="👤 **Admin Action**",
                    value=f"**Performed by:** {interaction.user.display_name}\n**Action:** Remove Coins\n**Status:** ✅ Completed",
                    inline=False
                )
                
                embed.set_author(name="Admin Coin Management", icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text="💼 Administrative Action • Coins removed from user account")
                
                await interaction.response.send_message(embed=embed)
                
                # Send notification to the user (optional)
                try:
                    user_embed = discord.Embed(
                        title="💸 **Coins Removed**",
                        description=f"An administrator has removed **{amount:,}** coins from your account.",
                        color=0xff6b6b
                    )
                    user_embed.add_field(
                        name="💳 **Your New Balance**",
                        value=f"{new_balance:,} coins",
                        inline=False
                    )
                    user_embed.set_footer(text="💼 Administrative action")
                    
                    await user.send(embed=user_embed)
                except:
                    pass  # User might have DMs disabled
                
            else:
                await interaction.response.send_message("❌ Failed to remove coins. Database error occurred.", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing coins: {str(e)}", ephemeral=True)

    @app_commands.command(name="dbhealth", description="🔍 Check database sync status (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def database_health_check(self, interaction: discord.Interaction):
        """Check MongoDB connection and data sync status - admin only"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can use this command!", ephemeral=True)
            return
        
        try:
            await interaction.response.defer()
            
            # Get database health information
            health_info = db.get_database_health()
            
            embed = discord.Embed(
                title="🔍 **Database Health Check**",
                description="Real-time MongoDB connection and sync status",
                color=0x00d4aa if health_info.get('success', True) else 0xff6b6b,
                timestamp=datetime.now()
            )
            
            # Connection status
            if db.client is not None:
                try:
                    # Test connection
                    db.client.admin.command('ping')
                    connection_status = "✅ Connected"
                    connection_color = "🟢"
                except:
                    connection_status = "❌ Connection Failed"
                    connection_color = "🔴"
            else:
                connection_status = "❌ Not Connected"
                connection_color = "🔴"
            
            embed.add_field(
                name="🔗 **MongoDB Connection**",
                value=f"**Status:** {connection_color} {connection_status}\n**Database:** {db.db.name if db.db is not None else 'None'}\n**Collections:** {'Active' if db.users_collection is not None else 'Inactive'}",
                inline=True
            )
            
            # Data sync test
            try:
                # Test user data operations
                test_user_id = interaction.user.id
                user_data = db.get_user_data(test_user_id)
                
                # Test coin operations
                original_coins = user_data.get('coins', 0)
                test_result = db.add_coins(test_user_id, 0)  # Add 0 coins (no change)
                
                sync_status = "✅ Working" if test_result else "❌ Failed"
                sync_color = "🟢" if test_result else "🔴"
                
            except Exception as e:
                sync_status = f"❌ Error: {str(e)[:50]}"
                sync_color = "🔴"
            
            embed.add_field(
                name="🔄 **Data Sync Status**",
                value=f"**Coins System:** {sync_color} {sync_status}\n**XP System:** {'🟢 Active' if hasattr(db, 'add_xp') else '🔴 Inactive'}\n**Work System:** {'🟢 Active' if hasattr(db, 'update_last_work') else '🔴 Inactive'}",
                inline=True
            )
            
            # Database statistics
            try:
                stats = db.get_database_stats()
                total_users = stats.get('total_users', 0)
                total_xp = stats.get('total_xp', 0)
                total_coins = stats.get('total_coins', 0)
                
                embed.add_field(
                    name="📊 **Database Statistics**",
                    value=f"**Total Users:** {total_users:,}\n**Total XP:** {total_xp:,}\n**Total Coins:** {total_coins:,}",
                    inline=True
                )
            except:
                embed.add_field(
                    name="📊 **Database Statistics**",
                    value="❌ Unable to retrieve stats",
                    inline=True
                )
            
            # Collection health
            collections_status = []
            collections = ['users', 'guild_settings', 'tickets', 'starboard']
            
            for collection_name in collections:
                collection = getattr(db, f"{collection_name}_collection", None)
                if collection is not None:
                    try:
                        count = collection.count_documents({})
                        collections_status.append(f"**{collection_name.title()}:** ✅ {count:,} docs")
                    except:
                        collections_status.append(f"**{collection_name.title()}:** ❌ Error")
                else:
                    collections_status.append(f"**{collection_name.title()}:** 🔴 Not loaded")
            
            embed.add_field(
                name="📂 **Collections Health**",
                value="\n".join(collections_status),
                inline=False
            )
            
            # Recent activity test
            try:
                # Check for recent user activity
                if db.users_collection is not None:
                    recent_cutoff = datetime.now().timestamp() - 3600  # Last hour
                    recent_users = db.users_collection.count_documents({
                        "last_updated": {"$gte": recent_cutoff}
                    })
                    
                    embed.add_field(
                        name="⚡ **Recent Activity**",
                        value=f"**Users active (1h):** {recent_users}\n**Last sync:** <t:{int(datetime.now().timestamp())}:R>\n**Status:** {'🟢 Live' if recent_users > 0 else '🟡 Quiet'}",
                        inline=True
                    )
            except:
                embed.add_field(
                    name="⚡ **Recent Activity**",
                    value="❌ Unable to check recent activity",
                    inline=True
                )
            
            # Overall health score
            health_score = 100
            if connection_status.startswith("❌"):
                health_score -= 50
            if sync_status.startswith("❌"):
                health_score -= 30
            if total_users == 0:
                health_score -= 20
            
            health_emoji = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
            
            embed.add_field(
                name="🎯 **Overall Health Score**",
                value=f"{health_emoji} **{health_score}/100**\n{'Excellent' if health_score >= 90 else 'Good' if health_score >= 80 else 'Fair' if health_score >= 60 else 'Poor'}",
                inline=True
            )
            
            embed.set_author(name="Database Health Monitor", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="🔍 Real-time database diagnostics • Updated every check")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Health Check Failed**",
                description=f"Unable to perform database health check.\n\n**Error:** {str(e)}",
                color=0xff6b6b
            )
            
            try:
                await interaction.followup.send(embed=error_embed)
            except:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
