import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import random
import os, sys
import time
import asyncio
from discord.ui import Button, View, Modal, TextInput
from typing import Dict, List, Any, Optional

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

# Enhanced Job System with better balance
JOB_TIERS = {
    "entry": {
        "name": "Entry Level",
        "unlock_requirement": 0,
        "promotion_requirement": 10,
        "jobs": [
            {
                "name": "Pizza Delivery", 
                "emoji": "🍕",
                "min_pay": 15, 
                "max_pay": 30, 
                "description": "delivering hot pizzas",
                "full_description": "🍕 You hop on your delivery bike and navigate busy streets, delivering steaming hot pizzas to hungry customers.",
                "skill": "delivery",
                "success_rate": 0.9
            },
            {
                "name": "Data Entry", 
                "emoji": "📋",
                "min_pay": 20, 
                "max_pay": 35, 
                "description": "entering data accurately",
                "full_description": "📋 You carefully input information into computer systems, ensuring accuracy and attention to detail.",
                "skill": "admin",
                "success_rate": 0.85
            }
        ]
    },
    "junior": {
        "name": "Junior Level",
        "unlock_requirement": 10,
        "promotion_requirement": 25,
        "jobs": [
            {
                "name": "Junior Developer", 
                "emoji": "💻",
                "min_pay": 25, 
                "max_pay": 50, 
                "description": "writing simple code",
                "full_description": "💻 You write and test basic code, learning the fundamentals of software development.",
                "skill": "development",
                "success_rate": 0.8
            },
            {
                "name": "Content Creator", 
                "emoji": "📝",
                "min_pay": 30, 
                "max_pay": 55, 
                "description": "creating engaging content",
                "full_description": "📝 You create articles, posts, and media content that engages and informs audiences.",
                "skill": "creative",
                "success_rate": 0.82
            }
        ]
    },
    "senior": {
        "name": "Senior Level",
        "unlock_requirement": 35,
        "promotion_requirement": 60,
        "jobs": [
            {
                "name": "Senior Developer", 
                "emoji": "🔨",
                "min_pay": 60, 
                "max_pay": 100, 
                "description": "leading development projects",
                "full_description": "🔨 You lead complex development projects and mentor junior developers.",
                "skill": "development",
                "success_rate": 0.75
            },
            {
                "name": "Business Analyst", 
                "emoji": "📊",
                "min_pay": 70, 
                "max_pay": 120, 
                "description": "analyzing business processes",
                "full_description": "📊 You analyze business processes and recommend improvements for efficiency.",
                "skill": "analysis",
                "success_rate": 0.78
            }
        ]
    }
}

class EnhancedEconomy(commands.Cog):
    """Enhanced economy system with advanced features"""
    
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
        
        # Cache for frequently accessed data
        self.user_cache = {}
        self.job_cache = {}
        
    async def cog_load(self):
        print("[Enhanced Economy] Loaded successfully with core system integration.")
        
        # Start background tasks using asyncio.create_task instead of bot.loop
        import asyncio
        asyncio.create_task(self.daily_interest_task())
        asyncio.create_task(self.cache_cleanup_task())
    
    async def daily_interest_task(self):
        """Background task to apply daily interest to savings accounts"""
        while True:
            try:
                await asyncio.sleep(86400)  # 24 hours
                
                if self.db_manager:
                    # Get all users with savings
                    users_with_savings = await self.db_manager.db.users.find({
                        "savings_balance": {"$gt": 0}
                    }).to_list(None)
                    
                    updates = []
                    for user_data in users_with_savings:
                        savings = user_data.get('savings_balance', 0)
                        interest = int(savings * self.config.economy.savings_interest_rate)
                        
                        if interest > 0:
                            updates.append({
                                "user_id": user_data["user_id"],
                                "data": {
                                    "savings_balance": savings + interest,
                                    "last_interest": time.time()
                                }
                            })
                            
                            # Log interest transaction
                            await self.db_manager.log_transaction(
                                user_data["user_id"], 
                                "savings_interest", 
                                interest,
                                {"rate": self.config.economy.savings_interest_rate}
                            )
                    
                    if updates:
                        await self.db_manager.bulk_update_users(updates)
                        print(f"✅ Applied daily interest to {len(updates)} users")
                        
            except Exception as e:
                print(f"Error in daily interest task: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    async def cache_cleanup_task(self):
        """Background task to clean up expired cache entries"""
        while True:
            try:
                await asyncio.sleep(1800)  # 30 minutes
                
                current_time = time.time()
                expired_keys = []
                
                for key, (data, timestamp) in self.user_cache.items():
                    if current_time - timestamp > 300:  # 5 minutes
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.user_cache[key]
                
                if expired_keys:
                    print(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
                    
            except Exception as e:
                print(f"Error in cache cleanup: {e}")
                await asyncio.sleep(3600)
    
    async def get_user_data_enhanced(self, user_id: int) -> Dict[str, Any]:
        """Get user data with enhanced caching and fallback"""
        # Try cache first
        if user_id in self.user_cache:
            data, timestamp = self.user_cache[user_id]
            if time.time() - timestamp < 300:  # 5 minutes
                return data
        
        # Try enhanced database manager
        if self.db_manager:
            try:
                data = await self.db_manager.get_user_data_cached(user_id)
                self.user_cache[user_id] = (data, time.time())
                return data
            except Exception as e:
                print(f"Error with enhanced database: {e}")
        
        # Fallback to original database
        data = db.get_user_data(user_id)
        self.user_cache[user_id] = (data, time.time())
        return data
    
    async def update_user_data_enhanced(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update user data with enhanced database and security"""
        try:
            # Update statistics
            stats = data.get('statistics', {})
            stats['last_activity'] = time.time()
            data['statistics'] = stats
            
            # Try enhanced database manager first
            if self.db_manager:
                success = await self.db_manager.update_user_data_cached(user_id, data)
                if success:
                    # Update cache
                    self.user_cache[user_id] = (data, time.time())
                    return True
            
            # Fallback to original database
            db.update_user_data(user_id, data)
            self.user_cache[user_id] = (data, time.time())
            return True
            
        except Exception as e:
            print(f"Error updating user data: {e}")
            return False
    
    def get_work_success_rate(self, user_id: int, job: Dict[str, Any]) -> float:
        """Calculate work success rate based on user history and job difficulty"""
        try:
            user_data = self.user_cache.get(user_id, ({}, 0))[0]
            
            base_rate = job.get("success_rate", 0.8)
            
            # Adjust based on user experience
            successful_works = user_data.get("successful_works", 0)
            experience_bonus = min(0.1, successful_works * 0.001)  # Up to 10% bonus
            
            # Adjust based on work streak
            work_streak = user_data.get("work_streak", 0)
            streak_bonus = min(0.05, work_streak * 0.005)  # Up to 5% bonus
            
            # Adjust based on recent failures
            recent_failures = user_data.get("recent_failures", 0)
            failure_penalty = min(0.15, recent_failures * 0.03)  # Up to 15% penalty
            
            final_rate = base_rate + experience_bonus + streak_bonus - failure_penalty
            return max(0.1, min(0.95, final_rate))  # Keep between 10% and 95%
            
        except Exception as e:
            print(f"Error calculating success rate: {e}")
            return 0.8  # Default rate
    
    async def process_work_result(self, user_id: int, job: Dict[str, Any], success: bool, earnings: int) -> Dict[str, Any]:
        """Process work result with enhanced tracking and security"""
        try:
            user_data = await self.get_user_data_enhanced(user_id)
            
            # Update work statistics
            user_data['last_work'] = time.time()
            user_data['total_works'] = user_data.get('total_works', 0) + 1
            
            if success:
                user_data['successful_works'] = user_data.get('successful_works', 0) + 1
                user_data['work_streak'] = user_data.get('work_streak', 0) + 1
                user_data['coins'] = user_data.get('coins', 0) + earnings
                user_data['recent_failures'] = max(0, user_data.get('recent_failures', 0) - 1)
                
                # Update statistics
                stats = user_data.get('statistics', {})
                stats['total_earned'] = stats.get('total_earned', 0) + earnings
                stats['successful_jobs'] = stats.get('successful_jobs', 0) + 1
                user_data['statistics'] = stats
                
                # Check for promotions
                promotion_info = self.check_promotion_eligibility(user_data)
                
            else:
                user_data['failed_works'] = user_data.get('failed_works', 0) + 1
                user_data['work_streak'] = 0
                user_data['recent_failures'] = user_data.get('recent_failures', 0) + 1
                promotion_info = {"eligible": False}
            
            # Save data
            await self.update_user_data_enhanced(user_id, user_data)
            
            # Log transaction if successful
            if success and self.db_manager:
                await self.db_manager.log_transaction(user_id, "work_earnings", earnings, {
                    "job": job["name"],
                    "tier": job.get("tier", "unknown"),
                    "success_rate": self.get_work_success_rate(user_id, job)
                })
            
            # Security check for suspicious activity
            await self.security_manager.detect_suspicious_activity(user_id, "work", {
                "gained": earnings if success else 0,
                "success": success,
                "job": job["name"]
            })
            
            return {
                "success": True,
                "work_successful": success,
                "earnings": earnings,
                "new_streak": user_data['work_streak'],
                "total_works": user_data['total_works'],
                "successful_works": user_data['successful_works'],
                "promotion_info": promotion_info
            }
            
        except Exception as e:
            print(f"Error processing work result: {e}")
            return {"success": False, "error": str(e)}
    
    def check_promotion_eligibility(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if user is eligible for promotion"""
        try:
            current_tier = user_data.get("job_tier", "entry")
            successful_works = user_data.get("successful_works", 0)
            
            if current_tier not in JOB_TIERS:
                return {"eligible": False, "reason": "Invalid tier"}
            
            tier_data = JOB_TIERS[current_tier]
            promotion_requirement = tier_data["promotion_requirement"]
            
            if successful_works >= promotion_requirement:
                # Find next tier
                tier_order = ["entry", "junior", "senior"]
                current_index = tier_order.index(current_tier)
                
                if current_index < len(tier_order) - 1:
                    next_tier = tier_order[current_index + 1]
                    return {
                        "eligible": True,
                        "next_tier": next_tier,
                        "next_tier_name": JOB_TIERS[next_tier]["name"]
                    }
            
            return {
                "eligible": False,
                "current_progress": successful_works,
                "required": promotion_requirement,
                "remaining": promotion_requirement - successful_works
            }
            
        except Exception as e:
            print(f"Error checking promotion eligibility: {e}")
            return {"eligible": False, "error": str(e)}
    
    def get_available_jobs(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get jobs available to user based on their tier"""
        try:
            current_tier = user_data.get("job_tier", "entry")
            successful_works = user_data.get("successful_works", 0)
            
            available_jobs = []
            
            # Add jobs from all unlocked tiers
            for tier_name, tier_data in JOB_TIERS.items():
                if successful_works >= tier_data["unlock_requirement"]:
                    for job in tier_data["jobs"]:
                        job_with_tier = job.copy()
                        job_with_tier["tier"] = tier_name
                        job_with_tier["tier_name"] = tier_data["name"]
                        available_jobs.append(job_with_tier)
            
            return available_jobs
            
        except Exception as e:
            print(f"Error getting available jobs: {e}")
            return []
    
    @app_commands.command(name="work", description="💼 Enhanced work system with career progression")
    async def work(self, interaction: discord.Interaction):
        """Enhanced work command with security and analytics"""
        user_id = interaction.user.id
        start_time = time.time()
        
        try:
            # Security: Rate limiting
            rate_limit_ok, time_left = await self.security_manager.check_rate_limit(user_id, "work")
            if not rate_limit_ok:
                await interaction.response.send_message(
                    f"⏰ **Rate limit exceeded!** Please wait {time_left:.1f} seconds before working again.",
                    ephemeral=True
                )
                return
            
            # Analytics: Track command usage
            await self.analytics.track_command_usage("work", user_id, interaction.guild.id if interaction.guild else None, start_time)
            
            # Check if feature is enabled
            if not self.config.is_feature_enabled("economy"):
                await interaction.response.send_message("❌ Economy system is currently disabled.", ephemeral=True)
                return
            
            # Get user data
            user_data = await self.get_user_data_enhanced(user_id)
            last_work = user_data.get('last_work', 0)
            current_time = time.time()
            
            # Check cooldown
            work_cooldown = self.config.economy.work_cooldown
            if current_time - last_work < work_cooldown:
                remaining_time = work_cooldown - (current_time - last_work)
                hours = int(remaining_time // 3600)
                minutes = int((remaining_time % 3600) // 60)
                seconds = int(remaining_time % 60)
                
                if hours > 0:
                    time_str = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    time_str = f"{minutes}m {seconds}s"
                else:
                    time_str = f"{seconds}s"
                
                embed = discord.Embed(
                    title="⏰ **Work Cooldown**",
                    description=f"You need to rest! Come back in **{time_str}**.",
                    color=0xff9966,
                    timestamp=datetime.now()
                )
                embed.add_field(
                    name="💡 Tip", 
                    value="Use this time to check your profile or visit the shop!", 
                    inline=False
                )
                embed.set_footer(text="💼 Quality work requires proper rest!")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Track performance
                execution_time = time.time() - start_time
                await self.analytics.track_performance("work_command", execution_time, False)
                return
            
            # Get available jobs
            available_jobs = self.get_available_jobs(user_data)
            
            if not available_jobs:
                await interaction.response.send_message("❌ No jobs available! Please contact an administrator.", ephemeral=True)
                return
            
            # Create job selection embed
            embed = discord.Embed(
                title="💼 **Choose Your Work**",
                description="Select a job that matches your skills and experience level!",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            # Add job options
            job_list = ""
            for i, job in enumerate(available_jobs[:10]):  # Limit to 10 jobs
                success_rate = self.get_work_success_rate(user_id, job)
                job_list += f"**{i+1}.** {job['emoji']} **{job['name']}** ({job['tier_name']})\n"
                job_list += f"   💰 {job['min_pay']}-{job['max_pay']} coins | 📊 {success_rate:.0%} success rate\n\n"
            
            embed.add_field(name="🎯 Available Jobs", value=job_list, inline=False)
            
            # Add user stats
            stats_text = f"**Successful Works:** {user_data.get('successful_works', 0)}\n"
            stats_text += f"**Work Streak:** {user_data.get('work_streak', 0)}\n"
            stats_text += f"**Current Tier:** {user_data.get('job_tier', 'entry').title()}"
            embed.add_field(name="📊 Your Stats", value=stats_text, inline=True)
            
            # Create job selection view
            class JobSelectionView(discord.ui.View):
                def __init__(self, economy_cog, user_id, available_jobs):
                    super().__init__(timeout=120)
                    self.economy_cog = economy_cog
                    self.user_id = user_id
                    self.available_jobs = available_jobs
                
                @discord.ui.select(
                    placeholder="🎯 Choose your job opportunity...",
                    min_values=1,
                    max_values=1,
                    options=[
                        discord.SelectOption(
                            label=f"{job['name']} ({job['tier_name']})",
                            description=f"💰 {job['min_pay']}-{job['max_pay']} coins | {self.economy_cog.get_work_success_rate(user_id, job):.0%} success",
                            emoji=job.get("emoji", "💼"),
                            value=str(i)
                        ) for i, job in enumerate(available_jobs[:25])  # Discord limit
                    ]
                )
                async def job_select(self, select_interaction: discord.Interaction, select: discord.ui.Select):
                    if select_interaction.user.id != self.user_id:
                        await select_interaction.response.send_message("❌ This is not your work selection!", ephemeral=True)
                        return
                    
                    try:
                        job_index = int(select.values[0])
                        selected_job = self.available_jobs[job_index]
                        
                        # Calculate work result
                        success_rate = self.economy_cog.get_work_success_rate(self.user_id, selected_job)
                        work_successful = random.random() < success_rate
                        
                        # Calculate earnings
                        base_earnings = random.randint(selected_job["min_pay"], selected_job["max_pay"])
                        
                        # Apply bonuses
                        user_data = await self.economy_cog.get_user_data_enhanced(self.user_id)
                        streak_bonus = min(20, user_data.get('work_streak', 0) * 2)
                        total_earnings = base_earnings + streak_bonus if work_successful else 0
                        
                        # Process work result
                        result = await self.economy_cog.process_work_result(
                            self.user_id, selected_job, work_successful, total_earnings
                        )
                        
                        if not result.get("success"):
                            await select_interaction.response.send_message(
                                f"❌ Error processing work: {result.get('error', 'Unknown error')}", 
                                ephemeral=True
                            )
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
                                value=f"**Successful Works:** {result['successful_works']}\n**Work Streak:** {result['new_streak']}\n**Current Tier:** {user_data.get('job_tier', 'entry').title()}",
                                inline=True
                            )
                            
                            # Check for promotion
                            promotion_info = result.get("promotion_info", {})
                            if promotion_info.get("eligible"):
                                embed.add_field(
                                    name="🎉 **PROMOTION AVAILABLE!**",
                                    value=f"You're eligible for promotion to **{promotion_info['next_tier_name']}**!",
                                    inline=False
                                )
                        else:
                            embed = discord.Embed(
                                title="❌ **Work Failed**",
                                description=f"**{select_interaction.user.display_name}** failed at **{selected_job['name']}** - Unfortunately, the work didn't go as planned.",
                                color=0xff6b6b,
                                timestamp=datetime.now()
                            )
                            
                            embed.add_field(name="💸 Earnings", value="0 coins", inline=True)
                            embed.add_field(name="⏰ Cooldown", value=f"{work_cooldown/3600:.1f} hours", inline=True)
                            embed.add_field(name="📊 Success Rate", value=f"{success_rate:.1%}", inline=True)
                            embed.add_field(name="💡 Tip", value="Don't give up! Try again after the cooldown.", inline=False)
                        
                        embed.set_footer(text=f"💪 Better luck next time! Try again in {work_cooldown/3600:.1f} hours")
                        
                        # Make sure failure message is visible to everyone
                        await select_interaction.response.send_message(embed=embed, ephemeral=False)
                        
                        # Track performance
                        execution_time = time.time() - start_time
                        await self.economy_cog.analytics.track_performance("work_command", execution_time, True)
                        
                    except Exception as e:
                        print(f"Error in job selection: {e}")
                        await select_interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)
            
            view = JobSelectionView(self, user_id, available_jobs)
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            print(f"Error in work command: {e}")
            
            # Track error
            await self.analytics.track_error("WorkCommandError", "work", user_id, str(e))
            
            await interaction.response.send_message(
                "❌ An unexpected error occurred. Please try again later.", 
                ephemeral=True
            )
            
            # Track performance
            execution_time = time.time() - start_time
            await self.analytics.track_performance("work_command", execution_time, False)

async def setup(bot: commands.Bot):
    await bot.add_cog(EnhancedEconomy(bot))