import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random
import os, sys
import time
from discord.ui import Button, View, Modal, TextInput

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# Import enhanced core systems with fallbacks
try:
    from core.database import get_db_manager
    from core.security import get_security_manager
    from core.analytics import get_analytics
    from core.config import get_config
    CORE_SYSTEMS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Core systems not available: {e}")
    CORE_SYSTEMS_AVAILABLE = False
    # Provide fallback functions
    def get_db_manager(): return None
    def get_security_manager(): return None
    def get_analytics(): return None
    def get_config(): return None

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
        
        # Initialize core systems with fallbacks
        if CORE_SYSTEMS_AVAILABLE:
            self.db_manager = get_db_manager()
            self.security_manager = get_security_manager()
            self.analytics = get_analytics()
            self.config = get_config()
        else:
            self.db_manager = None
            self.security_manager = None
            self.analytics = None
            self.config = None

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
                            title="❌ **Work Failed**",
                            description=f"**{selected_job['name']}** - The job didn't go as planned this time.",
                            color=0xff6b6b,
                            timestamp=datetime.now()
                        )
                        
                        embed.add_field(
                            name="💭 What Happened",
                            value=f"The {selected_job['name'].lower()} was more challenging than expected. Better luck next time!",
                            inline=False
                        )
                        
                        embed.add_field(
                            name="📊 Your Performance",
                            value=f"**Success Rate:** {success_rate:.1%}\n**Consecutive Works:** {result['consecutive_works']}\n**Total Works:** {result['total_works']}",
                            inline=True
                        )
                        
                        # Calculate cooldown display
                        try:
                            cooldown_hours = int(WORK_COOLDOWN_HOURS)
                        except (NameError, TypeError):
                            cooldown_hours = 2.5
                        
                        embed.add_field(
                            name="⏰ Cooldown",
                            value=f"**{cooldown_hours} hours** until next attempt",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="💡 Improvement Tips",
                            value="• Work consistently to build your streak\n• Try easier jobs to rebuild confidence\n• Consider buying work success boost from `/shop`",
                            inline=False
                        )
                        
                        embed.set_footer(text=f"💪 Try again in {cooldown_hours} hours! Don't give up!")
                    
                    embed.set_author(
                        name=f"{select_interaction.user.display_name}'s Work Report", 
                        icon_url=select_interaction.user.display_avatar.url
                    )
                    
                    # For failed work, send a public message so everyone can see
                    if not work_successful:
                        # Create a simpler public failure message
                        public_embed = discord.Embed(
                            title="💼 Work Attempt Failed",
                            description=f"**{select_interaction.user.display_name}** failed at **{selected_job['name']}** and needs to wait {cooldown_hours} hours before trying again.",
                            color=0xff6b6b,
                            timestamp=datetime.now()
                        )
                        public_embed.add_field(
                            name="📊 Performance", 
                            value=f"Success Rate: {success_rate:.1%}", 
                            inline=True
                        )
                        public_embed.add_field(
                            name="⏰ Cooldown", 
                            value=f"{cooldown_hours} hours", 
                            inline=True
                        )
                        public_embed.set_footer(text="💪 Better luck next time!")
                        
                        # Send public failure message
                        await select_interaction.followup.send(embed=public_embed, ephemeral=False)
                        
                        # Still send the detailed private message
                        await select_interaction.response.edit_message(embed=embed, view=None)
                    else:
                        # For successful work, keep the existing behavior
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

    @app_commands.command(name="shop", description="🛒 Enhanced shop with banking, slots, and premium items")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 **Enhanced Premium Shop**",
            description="✨ **Your one-stop shop for everything!**\nUse `/buy <item>` to purchase items.",
            color=0x9932cc
        )
        
        # Enhanced shop items with new categories
        shop_items = [
            # Slots & Gambling
            {"name": "🎰 Slot Spins (5x)", "price": 50, "description": "5 slot machine spins with custom amounts", "duration": "instant", "category": "🎰 Gambling", "id": "slot_spins_5"},
            {"name": "🎰 Slot Spins (10x)", "price": 90, "description": "10 slot machine spins with custom amounts", "duration": "instant", "category": "🎰 Gambling", "id": "slot_spins_10"},
            {"name": "🎰 Slot Spins (25x)", "price": 200, "description": "25 slot machine spins with custom amounts", "duration": "instant", "category": "🎰 Gambling", "id": "slot_spins_25"},
            {"name": "🎰 Lucky Slot Pass", "price": 300, "description": "Increased jackpot chances for 24 hours", "duration": "24 hours", "category": "🎰 Gambling", "id": "lucky_slots"},
            
            # Pet Items
            {"name": "🍖 Premium Food", "price": 100, "description": "High-quality pet food (+50 hunger, +20 happiness, +30 health)", "duration": "permanent", "category": "🐾 Pet Supplies", "id": "premium_food"},
            {"name": "🍖 Basic Food", "price": 25, "description": "Standard pet food (+20 hunger, +5 happiness, +10 health)", "duration": "permanent", "category": "🐾 Pet Supplies", "id": "basic_food"},
            {"name": "🍪 Pet Treat", "price": 50, "description": "Delicious treat (+10 hunger, +30 happiness, +5 health)", "duration": "permanent", "category": "🐾 Pet Supplies", "id": "treat"},
            {"name": "💊 Medicine", "price": 150, "description": "Pet medicine (+80 health)", "duration": "permanent", "category": "🐾 Pet Supplies", "id": "medicine"},
            {"name": "🎾 Pet Toy", "price": 75, "description": "Interactive toy (+40 happiness)", "duration": "permanent", "category": "🐾 Pet Supplies", "id": "toy"},
            
            # Banking & Financial
            {"name": "🏦 ATM Card", "price": 500, "description": "Access to ATM services and banking features", "duration": "permanent", "category": "🏦 Banking", "id": "atm_card"},
            {"name": "💳 Premium Account", "price": 1000, "description": "Premium banking with higher limits and bonuses", "duration": "30 days", "category": "🏦 Banking", "id": "premium_account"},
            {"name": "📊 Stock Analysis", "price": 300, "description": "Advanced stock market insights for 7 days", "duration": "7 days", "category": "🏦 Banking", "id": "stock_analysis"},
            {"name": "💰 Interest Booster", "price": 400, "description": "2x interest on savings for 14 days", "duration": "14 days", "category": "🏦 Banking", "id": "interest_boost"},
            
            # Power-Ups
            {"name": "⚡ XP Boost", "price": 300, "description": "Double XP gain for 2 hours", "duration": "2 hours", "category": "🚀 Power-Ups", "id": "xp_boost"},
            {"name": "💰 Coin Boost", "price": 400, "description": "1.5x coin earnings for 4 hours", "duration": "4 hours", "category": "🚀 Power-Ups", "id": "coin_boost"},
            {"name": "🎯 Work Success", "price": 600, "description": "Guaranteed work success for 12 hours", "duration": "12 hours", "category": "🚀 Power-Ups", "id": "work_success"},
            {"name": "🎲 Luck Boost", "price": 500, "description": "Better RNG in games for 24 hours", "duration": "24 hours", "category": "🚀 Power-Ups", "id": "luck_boost"},
            
            # Access & Customization
            {"name": "📝 Custom Nickname", "price": 200, "description": "Change nickname anytime (7 days)", "duration": "7 days", "category": "🔑 Access", "id": "nickname_freedom"},
            {"name": "🎨 Custom Color", "price": 350, "description": "Personalized role color (5 days)", "duration": "5 days", "category": "🔑 Access", "id": "custom_color"},
            {"name": "🌟 VIP Status", "price": 800, "description": "Exclusive VIP role and perks (3 days)", "duration": "3 days", "category": "🔑 Access", "id": "vip_status"},
            
            # Premium Items
            {"name": "💎 Diamond Pack", "price": 1500, "description": "Exclusive diamond role and 500 bonus coins", "duration": "7 days", "category": "💎 Premium", "id": "diamond_pack"},
            {"name": "👑 Royal Pass", "price": 2000, "description": "Royal role, 1000 bonus coins, and exclusive commands", "duration": "14 days", "category": "💎 Premium", "id": "royal_pass"},
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
            value="• Stack compatible boosts for maximum effect\n• Check `/inventory` to see active purchases\n• Visit `/atm` for banking services\n• Use `/slots <amount>` for custom slot betting!",
            inline=False
        )
        
        embed.set_footer(text="✨ Enhanced Shop • Banking • Slots • Premium Items!")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="inventory", description="📋 View your active items, purchases, and banking status")
    async def inventory(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            user_data = db.get_user_data(user_id)
            active_purchases = db.get_active_temporary_purchases(user_id)
            active_roles = db.get_active_temporary_roles(user_id)
            
            embed = discord.Embed(
                title="📋 **Your Inventory & Status**",
                description="Here's your complete inventory, active items, and banking information:",
                color=0x9932cc,
                timestamp=datetime.now()
            )
            
            # Banking Status
            balance = user_data.get('coins', 0)
            bank_balance = user_data.get('bank_balance', 0)
            savings_balance = user_data.get('savings_balance', 0)
            has_atm = user_data.get('atm_card', False)
            
            embed.add_field(
                name="🏦 **Banking Status**",
                value=f"💰 **Wallet:** {balance:,} coins\n"
                      f"🏦 **Bank:** {bank_balance:,} coins\n"
                      f"💎 **Savings:** {savings_balance:,} coins\n"
                      f"💳 **ATM Access:** {'✅ Yes' if has_atm else '❌ No'}",
                inline=True
            )
            
            # Pet Status (if user has pets)
            pets = user_data.get('pets', {})
            if pets:
                active_pet = None
                for pet_id, pet_data in pets.items():
                    if pet_data.get('active', False):
                        active_pet = pet_data
                        break
                
                if active_pet:
                    embed.add_field(
                        name="🐾 **Active Pet**",
                        value=f"**{active_pet['name']}** ({active_pet['species']})\n"
                              f"❤️ Health: {active_pet.get('health', 100)}/100\n"
                              f"😊 Happiness: {active_pet.get('happiness', 100)}/100\n"
                              f"🍖 Hunger: {active_pet.get('hunger', 100)}/100",
                        inline=True
                    )
            
            # Stock Portfolio
            portfolio = user_data.get('portfolio', {})
            if portfolio:
                total_value = sum(stock_data.get('shares', 0) * stock_data.get('avg_price', 0) for stock_data in portfolio.values())
                embed.add_field(
                    name="📈 **Stock Portfolio**",
                    value=f"**Total Value:** {total_value:,.2f} coins\n"
                          f"**Stocks Owned:** {len(portfolio)}\n"
                          f"Use `/stocks` to manage portfolio",
                    inline=True
                )
            
            # Active Purchases
            if not active_purchases and not active_roles:
                embed.add_field(
                    name="🛍️ **Active Items**",
                    value="No active premium items.\n💡 Visit `/shop` to browse items!",
                    inline=False
                )
            else:
                current_time = datetime.now().timestamp()
                
                # Group items by category
                categories = {
                    "🚀 Power-Ups": [],
                    "🎰 Gambling": [],
                    "🔑 Access": [],
                    "🎮 Fun & Games": []
                }
                
                # Process temporary purchases
                for purchase in active_purchases:
                    item_type = purchase.get("item_type", "unknown")
                    end_time = purchase.get("end_time", 0)
                    
                    if end_time == 0:
                        time_left = "Permanent"
                    else:
                        time_left = f"<t:{int(end_time)}:R>"
                    
                    # Get item display info
                    item_names = {
                        "xp_boost": "⚡ XP Boost",
                        "coin_boost": "💰 Coin Boost", 
                        "work_success": "🎯 Work Success",
                        "luck_boost": "🎲 Luck Boost",
                        "lucky_slots": "🎰 Lucky Slots",
                        "slot_spins_5": "🎰 Slot Spins (5x)",
                        "slot_spins_10": "🎰 Slot Spins (10x)",
                        "slot_spins_25": "🎰 Slot Spins (25x)",
                        "nickname_freedom": "📝 Custom Nickname",
                        "custom_color": "🎨 Custom Color",
                        "atm_card": "💳 ATM Card",
                        "premium_account": "🏦 Premium Account"
                    }
                    
                    item_name = item_names.get(item_type, item_type.title())
                    
                    # Categorize
                    if item_type in ["lucky_slots", "slot_spins_5", "slot_spins_10", "slot_spins_25"]:
                        category = "🎰 Gambling"
                    elif item_type in ["xp_boost", "coin_boost", "work_success", "luck_boost"]:
                        category = "🚀 Power-Ups"
                    elif item_type in ["nickname_freedom", "custom_color", "atm_card", "premium_account"]:
                        category = "🔑 Access"
                    else:
                        category = "🎮 Fun & Games"
                    
                    categories[category].append(f"**{item_name}**\nExpires: {time_left}")
                
                # Display active items by category
                for category, items in categories.items():
                    if items:
                        embed.add_field(
                            name=category,
                            value="\n\n".join(items),
                            inline=True
                        )
            
            embed.add_field(
                name="🔧 **Quick Actions**",
                value="• `/atm` - Banking services\n• `/shop` - Browse items\n• `/slots <amount>` - Play slots\n• `/stocks` - Stock market\n• `/pet` - Pet management",
                inline=False
            )
            
            embed.set_footer(text="📋 Complete Inventory • Updated in real-time")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="There was an error loading your inventory. Please try again.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"Inventory error: {e}")

    @app_commands.command(name="buy", description="🛒 Purchase items from the enhanced shop")
    @app_commands.describe(item="Item to purchase from the shop")
    @app_commands.choices(item=[
        # Slots & Gambling
        app_commands.Choice(name="🎰 Slot Spins (5x) - 50 coins", value="slot_spins_5"),
        app_commands.Choice(name="🎰 Slot Spins (10x) - 90 coins", value="slot_spins_10"),
        app_commands.Choice(name="🎰 Slot Spins (25x) - 200 coins", value="slot_spins_25"),
        app_commands.Choice(name="🎰 Lucky Slot Pass (24h) - 300 coins", value="lucky_slots"),
        # Banking & Financial
        app_commands.Choice(name="🏦 ATM Card - 500 coins", value="atm_card"),
        app_commands.Choice(name="💳 Premium Account (30 days) - 1000 coins", value="premium_account"),
        app_commands.Choice(name="📊 Stock Analysis (7 days) - 300 coins", value="stock_analysis"),
        app_commands.Choice(name="💰 Interest Booster (14 days) - 400 coins", value="interest_boost"),
        # Pet Items
        app_commands.Choice(name="🍖 Premium Food - 100 coins", value="premium_food"),
        app_commands.Choice(name="🍖 Basic Food - 25 coins", value="basic_food"),
        app_commands.Choice(name="🍪 Pet Treat - 50 coins", value="treat"),
        app_commands.Choice(name="💊 Medicine - 150 coins", value="medicine"),
        app_commands.Choice(name="🎾 Pet Toy - 75 coins", value="toy"),
        # Power-Ups
        app_commands.Choice(name="⚡ XP Boost (2 hours) - 300 coins", value="xp_boost"),
        app_commands.Choice(name="💰 Coin Boost (4 hours) - 400 coins", value="coin_boost"),
        app_commands.Choice(name="🎯 Work Success (12 hours) - 600 coins", value="work_success"),
        app_commands.Choice(name="🎲 Luck Boost (24 hours) - 500 coins", value="luck_boost"),
        # Access & Customization
        app_commands.Choice(name="📝 Custom Nickname (7 days) - 200 coins", value="nickname_freedom"),
        app_commands.Choice(name="🎨 Custom Color (5 days) - 350 coins", value="custom_color"),
        app_commands.Choice(name="🌟 VIP Status (3 days) - 800 coins", value="vip_status"),
        # Premium Items
        app_commands.Choice(name="💎 Diamond Pack (7 days) - 1500 coins", value="diamond_pack"),
        app_commands.Choice(name="👑 Royal Pass (14 days) - 2000 coins", value="royal_pass")
    ])
    async def buy(self, interaction: discord.Interaction, item: str):
        shop_items = {
            # Slots & Gambling
            "slot_spins_5": {"price": 50, "name": "🎰 Slot Spins (5x)", "duration": 0, "description": "instant", "category": "Gambling"},
            "slot_spins_10": {"price": 90, "name": "🎰 Slot Spins (10x)", "duration": 0, "description": "instant", "category": "Gambling"},
            "slot_spins_25": {"price": 200, "name": "🎰 Slot Spins (25x)", "duration": 0, "description": "instant", "category": "Gambling"},
            "lucky_slots": {"price": 300, "name": "🎰 Lucky Slot Pass", "duration": 86400, "description": "24 hours", "category": "Gambling"},
            # Banking & Financial
            "atm_card": {"price": 500, "name": "🏦 ATM Card", "duration": 0, "description": "permanent", "category": "Banking"},
            "premium_account": {"price": 1000, "name": "💳 Premium Account", "duration": 2592000, "description": "30 days", "category": "Banking"},
            "stock_analysis": {"price": 300, "name": "📊 Stock Analysis", "duration": 604800, "description": "7 days", "category": "Banking"},
            "interest_boost": {"price": 400, "name": "💰 Interest Booster", "duration": 1209600, "description": "14 days", "category": "Banking"},
            # Pet Items
            "premium_food": {"price": 100, "name": "🍖 Premium Food", "duration": 0, "description": "permanent", "category": "Pet Supply"},
            "basic_food": {"price": 25, "name": "🍖 Basic Food", "duration": 0, "description": "permanent", "category": "Pet Supply"},
            "treat": {"price": 50, "name": "🍪 Pet Treat", "duration": 0, "description": "permanent", "category": "Pet Supply"},
            "medicine": {"price": 150, "name": "💊 Medicine", "duration": 0, "description": "permanent", "category": "Pet Supply"},
            "toy": {"price": 75, "name": "🎾 Pet Toy", "duration": 0, "description": "permanent", "category": "Pet Supply"},
            # Power-Ups
            "xp_boost": {"price": 300, "name": "⚡ XP Boost", "duration": 7200, "description": "2 hours", "category": "Boost"},
            "coin_boost": {"price": 400, "name": "💰 Coin Boost", "duration": 14400, "description": "4 hours", "category": "Boost"},
            "work_success": {"price": 600, "name": "🎯 Work Success", "duration": 43200, "description": "12 hours", "category": "Boost"},
            "luck_boost": {"price": 500, "name": "🎲 Luck Boost", "duration": 86400, "description": "24 hours", "category": "Boost"},
            # Access & Customization
            "nickname_freedom": {"price": 200, "name": "📝 Custom Nickname", "duration": 604800, "description": "7 days", "category": "Access"},
            "custom_color": {"price": 350, "name": "🎨 Custom Color", "duration": 432000, "description": "5 days", "category": "Access"},
            "vip_status": {"price": 800, "name": "🌟 VIP Status", "duration": 259200, "description": "3 days", "category": "Access"},
            # Premium Items
            "diamond_pack": {"price": 1500, "name": "💎 Diamond Pack", "duration": 604800, "description": "7 days", "category": "Premium"},
            "royal_pass": {"price": 2000, "name": "👑 Royal Pass", "duration": 1209600, "description": "14 days", "category": "Premium"}
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

            # Handle pet items (permanent inventory items)
            if item_data['category'] == "Pet Supply":
                # Add to inventory instead of temporary purchases
                user_data = db.get_user_data(interaction.user.id)
                inventory = user_data.get('inventory', {})
                inventory[item] = inventory.get(item, 0) + 1
                user_data['inventory'] = inventory
                db.update_user_data(interaction.user.id, user_data)
                
                # Process purchase
                db.remove_coins(interaction.user.id, item_data['price'])
                new_balance = db.get_user_data(interaction.user.id).get('coins', 0)
                
                embed = discord.Embed(
                    title="🛒 **Pet Item Purchased!**",
                    description=f"**{item_data['name']}** has been added to your inventory!",
                    color=0x4ecdc4
                )
                
                embed.add_field(
                    name="🛒 **Purchase Details**", 
                    value=f"**Item:** {item_data['name']}\n**Cost:** {item_data['price']:,} coins\n**Type:** Pet Supply\n**Quantity:** 1", 
                    inline=True
                )
                
                embed.add_field(
                    name="💰 **Account Info**", 
                    value=f"**New Balance:** {new_balance:,} coins\n**Total {item_data['name']}:** {inventory[item]}", 
                    inline=True
                )
                
                embed.add_field(
                    name="🐾 **Usage**",
                    value=f"Use `/feed {item}` to feed your pet with this item!",
                    inline=False
                )
                
                embed.set_footer(text="🐾 Pet Shop • Thank you for your purchase!")
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                
                await interaction.response.send_message(embed=embed)
                return
            
            # Check if user already has this temporary item
            active_purchases = db.get_active_temporary_purchases(interaction.user.id)
            has_item = any(purchase["item_type"] == item for purchase in active_purchases)
            
            if has_item:
                await interaction.response.send_message(
                    f"❌ You already have an active {item_data['name']}! Wait for it to expire before purchasing again.",
                    ephemeral=True
                )
                return

            # Process purchase for temporary items
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
            
            # Handle special items first
            if item == "atm_card":
                # Give permanent ATM access
                user_data = db.get_user_data(interaction.user.id)
                user_data['atm_card'] = True
                db.update_user_data(interaction.user.id, user_data)
                embed.add_field(name="🏦 **ATM Card Issued**", value="You now have permanent access to ATM banking services!\nUse `/atm` to access all banking features.", inline=False)
                
            elif item in ["slot_spins_5", "slot_spins_10", "slot_spins_25"]:
                # Handle slot spins - give them as usable items
                spins_count = {"slot_spins_5": 5, "slot_spins_10": 10, "slot_spins_25": 25}
                user_data = db.get_user_data(interaction.user.id)
                user_data['slot_spins'] = user_data.get('slot_spins', 0) + spins_count[item]
                db.update_user_data(interaction.user.id, user_data)
                embed.add_field(name="🎰 **Slot Spins Added**", value=f"Added {spins_count[item]} slot spins to your account!\nTotal spins: {user_data['slot_spins']}\nUse `/slots` to play!", inline=False)
                
            elif item == "premium_account":
                db.add_temporary_purchase(interaction.user.id, "premium_account", item_data['duration'])
                embed.add_field(name="💳 **Premium Account Activated**", value="Higher banking limits, reduced fees, and exclusive features for 30 days!", inline=False)
                
            elif item == "stock_analysis":
                db.add_temporary_purchase(interaction.user.id, "stock_analysis", item_data['duration'])
                embed.add_field(name="📊 **Stock Analysis Enabled**", value="Advanced market insights and predictions for 7 days!", inline=False)
                
            elif item == "interest_boost":
                db.add_temporary_purchase(interaction.user.id, "interest_boost", item_data['duration'])
                embed.add_field(name="💰 **Interest Booster Active**", value="2x interest on all savings for 14 days!", inline=False)
                
            elif item == "lucky_slots":
                db.add_temporary_purchase(interaction.user.id, "lucky_slots", item_data['duration'])
                embed.add_field(name="🎰 **Lucky Slots Active**", value="Increased jackpot chances and better odds for 24 hours!", inline=False)
                
            # Handle specific items with enhanced features
            elif item == "xp_boost":
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
                
            elif item == "mega_boost":
                db.add_temporary_purchase(interaction.user.id, "mega_boost", item_data['duration'])
                embed.add_field(name="🔥 **Mega Boost Activated**", value="You now earn **2x XP** and **2x coins** from all activities!", inline=False)
                
            elif item == "vip_status":
                db.add_temporary_purchase(interaction.user.id, "vip_status", item_data['duration'])
                embed.add_field(name="🌟 **VIP Status Granted**", value="You now have exclusive VIP perks and access!", inline=False)
                
            elif item == "casino_pass":
                db.add_temporary_purchase(interaction.user.id, "casino_pass", item_data['duration'])
                embed.add_field(name="🎰 **Casino Pass Active**", value="Free access to all casino games for 24 hours!", inline=False)
                
            elif item == "diamond_pack":
                db.add_temporary_purchase(interaction.user.id, "diamond_pack", item_data['duration'])
                db.add_coins(interaction.user.id, 500)  # Bonus coins
                embed.add_field(name="💎 **Diamond Pack Activated**", value="Exclusive diamond role + 500 bonus coins!", inline=False)
                
            elif item == "royal_pass":
                db.add_temporary_purchase(interaction.user.id, "royal_pass", item_data['duration'])
                db.add_coins(interaction.user.id, 1000)  # Bonus coins
                embed.add_field(name="👑 **Royal Pass Activated**", value="Royal role + 1000 bonus coins + exclusive commands!", inline=False)
                
            elif item == "legendary_boost":
                db.add_temporary_purchase(interaction.user.id, "legendary_boost", item_data['duration'])
                embed.add_field(name="🚀 **Legendary Boost Activated**", value="3x XP + 3x coins + guaranteed success for 6 hours!", inline=False)
            
            # Add usage tips
            embed.add_field(
                name="💡 **Pro Tips**",
                value="• Use `/inventory` to check all active purchases\n• Stack compatible boosts for maximum effect\n• Use `/atm` for banking services\n• Premium items provide exclusive server benefits!",
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

    @app_commands.command(name="deposit", description="🏦 Deposit coins into your bank account")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        """Deposit coins into bank account"""
        if amount <= 0:
            await interaction.response.send_message("❌ You must deposit a positive amount!", ephemeral=True)
            return
        
        user_data = db.get_user_data(interaction.user.id)
        current_coins = user_data.get('coins', 0)
        current_bank = user_data.get('bank', 0)
        
        if current_coins < amount:
            await interaction.response.send_message(f"❌ You don't have enough coins! You have {current_coins} coins.", ephemeral=True)
            return
        
        # Remove coins from wallet and add to bank
        new_coins = current_coins - amount
        new_bank = current_bank + amount
        
        # Update database
        success = db.update_user_data(interaction.user.id, {'coins': new_coins, 'bank': new_bank})
        
        if success:
            embed = discord.Embed(
                title="🏦 Deposit Successful!",
                description=f"You deposited **{amount:,}** coins into your bank account.",
                color=0x00ff00
            )
            embed.add_field(
                name="💰 Wallet Balance",
                value=f"{new_coins:,} coins",
                inline=True
            )
            embed.add_field(
                name="🏦 Bank Balance", 
                value=f"{new_bank:,} coins",
                inline=True
            )
            embed.add_field(
                name="💎 Total Worth",
                value=f"{new_coins + new_bank:,} coins",
                inline=True
            )
            embed.set_footer(text="💡 Your bank account is safe from gambling losses!")
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Failed to deposit coins. Please try again.", ephemeral=True)

    @app_commands.command(name="withdraw", description="🏦 Withdraw coins from your bank account")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        """Withdraw coins from bank account"""
        if amount <= 0:
            await interaction.response.send_message("❌ You must withdraw a positive amount!", ephemeral=True)
            return
        
        user_data = db.get_user_data(interaction.user.id)
        current_coins = user_data.get('coins', 0)
        current_bank = user_data.get('bank', 0)
        
        if current_bank < amount:
            await interaction.response.send_message(f"❌ You don't have enough coins in your bank! You have {current_bank} coins in the bank.", ephemeral=True)
            return
        
        # Remove coins from bank and add to wallet
        new_coins = current_coins + amount
        new_bank = current_bank - amount
        
        # Update database
        success = db.update_user_data(interaction.user.id, {'coins': new_coins, 'bank': new_bank})
        
        if success:
            embed = discord.Embed(
                title="🏦 Withdrawal Successful!",
                description=f"You withdrew **{amount:,}** coins from your bank account.",
                color=0x00ff00
            )
            embed.add_field(
                name="💰 Wallet Balance",
                value=f"{new_coins:,} coins",
                inline=True
            )
            embed.add_field(
                name="🏦 Bank Balance",
                value=f"{new_bank:,} coins", 
                inline=True
            )
            embed.add_field(
                name="💎 Total Worth",
                value=f"{new_coins + new_bank:,} coins",
                inline=True
            )
            embed.set_footer(text="💰 Use your coins wisely!")
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Failed to withdraw coins. Please try again.", ephemeral=True)

    @app_commands.command(name="bank", description="🏦 Check your bank account balance")
    async def bank_balance(self, interaction: discord.Interaction):
        """Check bank account balance"""
        user_data = db.get_user_data(interaction.user.id)
        wallet_coins = user_data.get('coins', 0)
        bank_coins = user_data.get('bank', 0)
        total_worth = wallet_coins + bank_coins
        
        embed = discord.Embed(
            title="🏦 Bank Account Summary",
            description=f"**{interaction.user.display_name}'s Financial Overview**",
            color=0x7289da
        )
        
        embed.add_field(
            name="💰 Wallet Balance",
            value=f"**{wallet_coins:,}** coins\n*Available for spending*",
            inline=True
        )
        
        embed.add_field(
            name="🏦 Bank Balance", 
            value=f"**{bank_coins:,}** coins\n*Safe from gambling*",
            inline=True
        )
        
        embed.add_field(
            name="💎 Total Net Worth",
            value=f"**{total_worth:,}** coins\n*Combined wealth*",
            inline=True
        )
        
        # Add some banking tips
        if bank_coins == 0:
            embed.add_field(
                name="💡 Banking Tip",
                value="Consider depositing some coins to keep them safe from gambling losses!",
                inline=False
            )
        elif bank_coins > wallet_coins * 2:
            embed.add_field(
                name="💡 Banking Tip", 
                value="You have most of your wealth in the bank - very safe strategy!",
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="🏦 Use /deposit and /withdraw to manage your money")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loan", description="🏦 Apply for loans with different interest rates")
    async def loan(self, interaction: discord.Interaction, amount: int, loan_type: str = "personal"):
        """Apply for a loan"""
        if amount <= 0:
            await interaction.response.send_message("❌ Loan amount must be positive!", ephemeral=True)
            return
        
        if amount > 50000:
            await interaction.response.send_message("❌ Maximum loan amount is 50,000 coins!", ephemeral=True)
            return
        
        user_data = db.get_user_data(interaction.user.id)
        current_loans = user_data.get('loans', [])
        
        # Check if user already has a loan
        if len(current_loans) >= 3:
            await interaction.response.send_message("❌ You can only have 3 active loans at a time!", ephemeral=True)
            return
        
        # Loan types with different interest rates
        loan_types = {
            "personal": {"rate": 0.15, "term": 30, "name": "Personal Loan"},
            "business": {"rate": 0.12, "term": 60, "name": "Business Loan"}, 
            "emergency": {"rate": 0.20, "term": 14, "name": "Emergency Loan"}
        }
        
        if loan_type not in loan_types:
            loan_type = "personal"
        
        loan_info = loan_types[loan_type]
        interest = amount * loan_info["rate"]
        total_repayment = amount + interest
        daily_payment = total_repayment / loan_info["term"]
        
        # Add loan to user data
        new_loan = {
            "amount": amount,
            "type": loan_type,
            "interest": interest,
            "total_repayment": total_repayment,
            "daily_payment": daily_payment,
            "days_remaining": loan_info["term"],
            "taken_date": datetime.now().timestamp()
        }
        
        current_loans.append(new_loan)
        
        # Give coins to user
        success = db.update_user_data(interaction.user.id, {
            'coins': user_data.get('coins', 0) + amount,
            'loans': current_loans
        })
        
        if success:
            embed = discord.Embed(
                title="🏦 Loan Approved!",
                description=f"Your **{loan_info['name']}** has been approved!",
                color=0x00ff00
            )
            embed.add_field(
                name="💰 Loan Amount",
                value=f"{amount:,} coins",
                inline=True
            )
            embed.add_field(
                name="📈 Interest Rate",
                value=f"{loan_info['rate']*100:.1f}%",
                inline=True
            )
            embed.add_field(
                name="💳 Total Repayment",
                value=f"{total_repayment:,} coins",
                inline=True
            )
            embed.add_field(
                name="📅 Loan Term",
                value=f"{loan_info['term']} days",
                inline=True
            )
            embed.add_field(
                name="💸 Daily Payment",
                value=f"{daily_payment:.0f} coins/day",
                inline=True
            )
            embed.add_field(
                name="⚠️ Warning",
                value="Failure to repay may affect your credit score!",
                inline=True
            )
            embed.set_footer(text="🏦 Loan funds have been added to your wallet")
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Failed to process loan. Please try again.", ephemeral=True)

    @app_commands.command(name="creditcard", description="💳 Apply for credit cards with spending limits")
    async def creditcard(self, interaction: discord.Interaction):
        """Apply for a credit card"""
        user_data = db.get_user_data(interaction.user.id)
        current_cards = user_data.get('credit_cards', [])
        
        if len(current_cards) >= 2:
            await interaction.response.send_message("❌ You can only have 2 credit cards!", ephemeral=True)
            return
        
        # Credit card types based on user's wealth
        total_wealth = user_data.get('coins', 0) + user_data.get('bank', 0)
        
        if total_wealth < 1000:
            card_type = "Basic"
            limit = 2000
            apr = 0.25
        elif total_wealth < 10000:
            card_type = "Silver"
            limit = 7500
            apr = 0.20
        elif total_wealth < 50000:
            card_type = "Gold"
            limit = 20000
            apr = 0.15
        else:
            card_type = "Platinum"
            limit = 50000
            apr = 0.12
        
        new_card = {
            "type": card_type,
            "limit": limit,
            "balance": 0,
            "apr": apr,
            "issued_date": datetime.now().timestamp(),
            "last_payment": datetime.now().timestamp()
        }
        
        current_cards.append(new_card)
        
        success = db.update_user_data(interaction.user.id, {'credit_cards': current_cards})
        
        if success:
            embed = discord.Embed(
                title="💳 Credit Card Approved!",
                description=f"Congratulations! Your **{card_type} Credit Card** has been approved!",
                color=0x00ff00
            )
            embed.add_field(
                name="💎 Card Type",
                value=card_type,
                inline=True
            )
            embed.add_field(
                name="💰 Credit Limit",
                value=f"{limit:,} coins",
                inline=True
            )
            embed.add_field(
                name="📈 APR",
                value=f"{apr*100:.1f}%",
                inline=True
            )
            embed.add_field(
                name="💳 Current Balance",
                value="0 coins",
                inline=True
            )
            embed.add_field(
                name="✅ Benefits",
                value="• Build credit history\n• Emergency spending\n• Purchase protection",
                inline=False
            )
            embed.set_footer(text="💳 Use responsibly and pay on time!")
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Failed to process credit card application.", ephemeral=True)

    @app_commands.command(name="creditscore", description="📊 View your detailed credit analysis")
    async def creditscore(self, interaction: discord.Interaction):
        """View credit score and analysis"""
        user_data = db.get_user_data(interaction.user.id)
        
        # Calculate credit score based on various factors
        base_score = 300
        
        # Wealth factor (max +200 points)
        total_wealth = user_data.get('coins', 0) + user_data.get('bank', 0)
        wealth_score = min(200, total_wealth // 500)
        
        # Banking history factor (max +150 points)
        bank_balance = user_data.get('bank', 0)
        banking_score = min(150, bank_balance // 300)
        
        # Activity factor (max +100 points)
        daily_streak = user_data.get('daily_streak', 0)
        activity_score = min(100, daily_streak * 2)
        
        # Loan history factor (max +100 points or -200 for bad history)
        loans = user_data.get('loans', [])
        loan_score = 50  # Default neutral
        if len(loans) == 0:
            loan_score = 25  # No credit history
        elif len(loans) > 3:
            loan_score = -100  # Too much debt
        
        # Credit card factor (max +50 points)
        cards = user_data.get('credit_cards', [])
        card_score = len(cards) * 25
        
        total_score = base_score + wealth_score + banking_score + activity_score + loan_score + card_score
        total_score = max(300, min(850, total_score))  # Clamp between 300-850
        
        # Determine credit rating
        if total_score >= 750:
            rating = "Excellent"
            color = 0x00ff00
        elif total_score >= 700:
            rating = "Good"
            color = 0x90EE90
        elif total_score >= 650:
            rating = "Fair"
            color = 0xffff00
        elif total_score >= 600:
            rating = "Poor"
            color = 0xffa500
        else:
            rating = "Very Poor"
            color = 0xff0000
        
        embed = discord.Embed(
            title="📊 Credit Score Analysis",
            description=f"**{interaction.user.display_name}'s Credit Report**",
            color=color
        )
        
        embed.add_field(
            name="🎯 Credit Score",
            value=f"**{total_score}/850**\n*{rating}*",
            inline=True
        )
        
        embed.add_field(
            name="📈 Score Breakdown",
            value=f"💰 Wealth: +{wealth_score}\n🏦 Banking: +{banking_score}\n⚡ Activity: +{activity_score}\n💳 Loans: {'+' if loan_score >= 0 else ''}{loan_score}\n💎 Cards: +{card_score}",
            inline=True
        )
        
        embed.add_field(
            name="💼 Financial Profile",
            value=f"**Total Wealth:** {total_wealth:,} coins\n**Bank Balance:** {bank_balance:,} coins\n**Active Loans:** {len(loans)}\n**Credit Cards:** {len(cards)}",
            inline=True
        )
        
        # Recommendations
        recommendations = []
        if total_score < 650:
            recommendations.append("• Build wealth by working daily")
            recommendations.append("• Maintain a bank account")
        if bank_balance < 5000:
            recommendations.append("• Increase your bank savings")
        if daily_streak < 30:
            recommendations.append("• Maintain daily activity streak")
        if len(cards) == 0 and total_wealth > 1000:
            recommendations.append("• Consider applying for a credit card")
        
        if recommendations:
            embed.add_field(
                name="💡 Recommendations",
                value="\n".join(recommendations),
                inline=False
            )
        
        embed.set_footer(text="📊 Credit scores update daily based on your financial activity")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="atm", description="🏦 Access ATM services - deposit, withdraw, transfer, and more!")
    async def atm(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_data = db.get_user_data(user_id)
        
        # Check if user has ATM card
        has_atm_card = user_data.get('atm_card', False)
        if not has_atm_card:
            embed = discord.Embed(
                title="❌ **ATM Access Denied**",
                description="You need an ATM card to use banking services!\n\n💳 **Get an ATM Card:**\nPurchase one from `/shop` for 500 coins.",
                color=0xff0000
            )
            embed.add_field(
                name="🏦 **Available Services**",
                value="• Deposit coins to bank\n• Withdraw from bank\n• Transfer to other users\n• Open savings account\n• Apply for loans\n• View transaction history",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        # Get user's financial data
        wallet = user_data.get('coins', 0)
        bank_balance = user_data.get('bank_balance', 0)
        savings_balance = user_data.get('savings_balance', 0)
        loan_amount = user_data.get('loan_amount', 0)
        is_premium = user_data.get('premium_account', False)
        
        # Create ATM interface
        embed = discord.Embed(
            title="🏦 **Coal Bank ATM**",
            description="Welcome to your personal banking center!",
            color=0x2f3136,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="💰 **Account Overview**",
            value=f"**Wallet:** {wallet:,} coins\n"
                  f"**Bank:** {bank_balance:,} coins\n"
                  f"**Savings:** {savings_balance:,} coins\n"
                  f"**Total:** {(wallet + bank_balance + savings_balance):,} coins",
            inline=True
        )
        
        embed.add_field(
            name="💳 **Account Status**",
            value=f"**Type:** {'Premium' if is_premium else 'Standard'}\n"
                  f"**Loan:** {loan_amount:,} coins\n"
                  f"**Credit:** {'Good' if loan_amount == 0 else 'Active Loan'}\n"
                  f"**ATM Card:** ✅ Active",
            inline=True
        )
        
        embed.add_field(
            name="🏦 **Banking Services**",
            value="Use the buttons below to access banking services:",
            inline=False
        )
        
        embed.set_footer(text="🏦 Coal Bank • Secure Banking Since 2024")
        
        # Create ATM view with buttons that expire after use
        class ATMView(View):
            def __init__(self):
                super().__init__(timeout=300)  # 5 minutes
                self.used = False
            
            async def disable_view(self, interaction):
                """Disable the view after first use"""
                if not self.used:
                    self.used = True
                    for item in self.children:
                        item.disabled = True
                    try:
                        await interaction.edit_original_response(view=self)
                    except:
                        pass
            
            @discord.ui.button(label="Deposit", emoji="📥", style=discord.ButtonStyle.green)
            async def deposit_button(self, button_interaction: discord.Interaction, button: Button):
                if button_interaction.user.id != user_id:
                    await button_interaction.response.send_message("This isn't your ATM session!", ephemeral=True)
                    return
                
                await self.disable_view(button_interaction)
                
                class DepositModal(Modal, title="Deposit Coins to Bank"):
                    amount_input = TextInput(
                        label="Amount to deposit",
                        placeholder="Enter amount (e.g., 1000)",
                        max_length=10
                    )
                    
                    async def on_submit(self, modal_interaction: discord.Interaction):
                        try:
                            amount = int(self.amount_input.value.replace(',', ''))
                            if amount <= 0:
                                await modal_interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
                                return
                            
                            current_data = db.get_user_data(user_id)
                            current_wallet = current_data.get('coins', 0)
                            
                            if current_wallet < amount:
                                await modal_interaction.response.send_message(
                                    f"❌ Insufficient funds! You have {current_wallet:,} coins in wallet.",
                                    ephemeral=True
                                )
                                return
                            
                            # Process deposit
                            db.add_coins(user_id, -amount)  # Remove from wallet
                            current_data['bank_balance'] = current_data.get('bank_balance', 0) + amount
                            db.update_user_data(user_id, current_data)
                            
                            success_embed = discord.Embed(
                                title="✅ **Deposit Successful**",
                                description=f"Successfully deposited {amount:,} coins to your bank account!",
                                color=0x00ff00
                            )
                            success_embed.add_field(
                                name="💰 **Updated Balance**",
                                value=f"Bank: {current_data['bank_balance']:,} coins",
                                inline=True
                            )
                            await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                            
                        except ValueError:
                            await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
                
                await button_interaction.response.send_modal(DepositModal())
            
            @discord.ui.button(label="Withdraw", emoji="📤", style=discord.ButtonStyle.red)
            async def withdraw_button(self, button_interaction: discord.Interaction, button: Button):
                if button_interaction.user.id != user_id:
                    await button_interaction.response.send_message("This isn't your ATM session!", ephemeral=True)
                    return
                
                await self.disable_view(button_interaction)
                
                class WithdrawModal(Modal, title="Withdraw Coins from Bank"):
                    amount_input = TextInput(
                        label="Amount to withdraw",
                        placeholder="Enter amount (e.g., 500)",
                        max_length=10
                    )
                    
                    async def on_submit(self, modal_interaction: discord.Interaction):
                        try:
                            amount = int(self.amount_input.value.replace(',', ''))
                            if amount <= 0:
                                await modal_interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
                                return
                            
                            current_data = db.get_user_data(user_id)
                            current_bank = current_data.get('bank_balance', 0)
                            
                            if current_bank < amount:
                                await modal_interaction.response.send_message(
                                    f"❌ Insufficient bank funds! You have {current_bank:,} coins in bank.",
                                    ephemeral=True
                                )
                                return
                            
                            # Process withdrawal
                            db.add_coins(user_id, amount)  # Add to wallet
                            current_data['bank_balance'] = current_data.get('bank_balance', 0) - amount
                            db.update_user_data(user_id, current_data)
                            
                            success_embed = discord.Embed(
                                title="✅ **Withdrawal Successful**",
                                description=f"Successfully withdrew {amount:,} coins from your bank account!",
                                color=0x00ff00
                            )
                            success_embed.add_field(
                                name="💰 **Updated Balance**",
                                value=f"Bank: {current_data['bank_balance']:,} coins",
                                inline=True
                            )
                            await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                            
                        except ValueError:
                            await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
                
                await button_interaction.response.send_modal(WithdrawModal())
            
            @discord.ui.button(label="Transfer", emoji="💸", style=discord.ButtonStyle.primary)
            async def transfer_button(self, button_interaction: discord.Interaction, button: Button):
                if button_interaction.user.id != user_id:
                    await button_interaction.response.send_message("This isn't your ATM session!", ephemeral=True)
                    return
                
                await self.disable_view(button_interaction)
                
                class TransferModal(Modal, title="Transfer Coins to Another User"):
                    user_input = TextInput(
                        label="User to transfer to",
                        placeholder="@username or user ID",
                        max_length=50
                    )
                    amount_input = TextInput(
                        label="Amount to transfer",
                        placeholder="Enter amount (e.g., 250)",
                        max_length=10
                    )
                    
                    async def on_submit(self, modal_interaction: discord.Interaction):
                        try:
                            amount = int(self.amount_input.value.replace(',', ''))
                            if amount <= 0:
                                await modal_interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
                                return
                            
                            # Find target user
                            user_input = self.user_input.value.strip()
                            target_user = None
                            
                            # Try to find user by mention or ID
                            if user_input.startswith('<@') and user_input.endswith('>'):
                                user_id_str = user_input[2:-1]
                                if user_id_str.startswith('!'):
                                    user_id_str = user_id_str[1:]
                                try:
                                    target_user = interaction.guild.get_member(int(user_id_str))
                                except:
                                    pass
                            else:
                                # Try to find by username
                                for member in interaction.guild.members:
                                    if member.display_name.lower() == user_input.lower() or member.name.lower() == user_input.lower():
                                        target_user = member
                                        break
                            
                            if not target_user:
                                await modal_interaction.response.send_message("❌ User not found! Try using @mention or exact username.", ephemeral=True)
                                return
                            
                            if target_user.id == user_id:
                                await modal_interaction.response.send_message("❌ You can't transfer to yourself!", ephemeral=True)
                                return
                            
                            # Check sender's balance
                            current_data = db.get_user_data(user_id)
                            current_bank = current_data.get('bank_balance', 0)
                            
                            transfer_fee = max(1, amount // 100)  # 1% fee, minimum 1 coin
                            total_cost = amount + transfer_fee
                            
                            if current_bank < total_cost:
                                await modal_interaction.response.send_message(
                                    f"❌ Insufficient bank funds! You need {total_cost:,} coins (including {transfer_fee:,} transfer fee).\n"
                                    f"You have {current_bank:,} coins in bank.",
                                    ephemeral=True
                                )
                                return
                            
                            # Process transfer
                            current_data['bank_balance'] -= total_cost
                            db.update_user_data(user_id, current_data)
                            
                            # Add to recipient's bank
                            recipient_data = db.get_user_data(target_user.id)
                            recipient_data['bank_balance'] = recipient_data.get('bank_balance', 0) + amount
                            db.update_user_data(target_user.id, recipient_data)
                            
                            success_embed = discord.Embed(
                                title="✅ **Transfer Successful**",
                                description=f"Successfully transferred {amount:,} coins to {target_user.display_name}!",
                                color=0x00ff00
                            )
                            success_embed.add_field(
                                name="💰 **Transaction Details**",
                                value=f"Amount: {amount:,} coins\nFee: {transfer_fee:,} coins\nTotal: {total_cost:,} coins",
                                inline=True
                            )
                            success_embed.add_field(
                                name="🏦 **Your Bank Balance**",
                                value=f"{current_data['bank_balance']:,} coins",
                                inline=True
                            )
                            await modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                            
                        except ValueError:
                            await modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
                
                await button_interaction.response.send_modal(TransferModal())
            
            @discord.ui.button(label="Savings", emoji="💎", style=discord.ButtonStyle.secondary)
            async def savings_button(self, button_interaction: discord.Interaction, button: Button):
                if button_interaction.user.id != user_id:
                    await button_interaction.response.send_message("This isn't your ATM session!", ephemeral=True)
                    return
                
                await self.disable_view(button_interaction)
                
                current_data = db.get_user_data(user_id)
                savings = current_data.get('savings_balance', 0)
                bank = current_data.get('bank_balance', 0)
                
                savings_embed = discord.Embed(
                    title="💎 **Savings Account**",
                    description="High-yield savings with 2% daily interest!",
                    color=0x9932cc
                )
                
                savings_embed.add_field(
                    name="💰 **Current Savings**",
                    value=f"{savings:,} coins",
                    inline=True
                )
                
                savings_embed.add_field(
                    name="📈 **Daily Interest**",
                    value=f"{int(savings * 0.02):,} coins (2%)",
                    inline=True
                )
                
                savings_embed.add_field(
                    name="🏦 **Available to Save**",
                    value=f"{bank:,} coins (from bank)",
                    inline=True
                )
                
                savings_embed.add_field(
                    name="ℹ️ **How it Works**",
                    value="• Transfer from bank to savings\n• Earn 2% interest daily\n• Minimum 100 coins to start\n• No withdrawal fees",
                    inline=False
                )
                
                class SavingsView(View):
                    def __init__(self):
                        super().__init__(timeout=180)
                    
                    @discord.ui.button(label="Deposit to Savings", style=discord.ButtonStyle.green)
                    async def deposit_savings(self, savings_interaction: discord.Interaction, button: Button):
                        class SavingsDepositModal(Modal, title="Deposit to Savings"):
                            amount_input = TextInput(
                                label="Amount to save (from bank)",
                                placeholder="Minimum 100 coins",
                                max_length=10
                            )
                            
                            async def on_submit(self, savings_modal_interaction: discord.Interaction):
                                try:
                                    amount = int(self.amount_input.value.replace(',', ''))
                                    if amount < 100:
                                        await savings_modal_interaction.response.send_message("❌ Minimum savings deposit is 100 coins!", ephemeral=True)
                                        return
                                    
                                    current_data = db.get_user_data(user_id)
                                    current_bank = current_data.get('bank_balance', 0)
                                    
                                    if current_bank < amount:
                                        await savings_modal_interaction.response.send_message(
                                            f"❌ Insufficient bank funds! You have {current_bank:,} coins in bank.",
                                            ephemeral=True
                                        )
                                        return
                                    
                                    # Transfer to savings
                                    current_data['bank_balance'] -= amount
                                    current_data['savings_balance'] = current_data.get('savings_balance', 0) + amount
                                    db.update_user_data(user_id, current_data)
                                    
                                    success_embed = discord.Embed(
                                        title="✅ **Savings Deposit Successful**",
                                        description=f"Deposited {amount:,} coins to savings!",
                                        color=0x00ff00
                                    )
                                    success_embed.add_field(
                                        name="💎 **New Savings Balance**",
                                        value=f"{current_data['savings_balance']:,} coins",
                                        inline=True
                                    )
                                    await savings_modal_interaction.response.send_message(embed=success_embed, ephemeral=True)
                                    
                                except ValueError:
                                    await savings_modal_interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
                        
                        await savings_interaction.response.send_modal(SavingsDepositModal())
                
                await button_interaction.response.send_message(embed=savings_embed, view=SavingsView(), ephemeral=True)
        
        view = ATMView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
