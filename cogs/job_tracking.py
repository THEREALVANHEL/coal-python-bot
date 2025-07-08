import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import os, sys
import asyncio

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

# Job roles and their requirements
JOB_ROLES = {
    "intern": {
        "role_id": 1370000000000000000,  # Replace with actual role ID
        "min_hours_per_week": 10,
        "min_days_active": 3,
        "warning_threshold": 7,  # Days before demotion warning
        "demotion_threshold": 14  # Days before auto-demotion
    },
    "junior_developer": {
        "role_id": 1370000000000000001,  # Replace with actual role ID
        "min_hours_per_week": 15,
        "min_days_active": 4,
        "warning_threshold": 7,
        "demotion_threshold": 14
    },
    "developer": {
        "role_id": 1370000000000000002,  # Replace with actual role ID
        "min_hours_per_week": 20,
        "min_days_active": 4,
        "warning_threshold": 7,
        "demotion_threshold": 14
    },
    "senior_developer": {
        "role_id": 1370000000000000003,  # Replace with actual role ID
        "min_hours_per_week": 25,
        "min_days_active": 5,
        "warning_threshold": 5,
        "demotion_threshold": 10
    },
    "team_lead": {
        "role_id": 1370000000000000004,  # Replace with actual role ID
        "min_hours_per_week": 30,
        "min_days_active": 5,
        "warning_threshold": 5,
        "demotion_threshold": 10
    }
}

# Management roles that can see job stats
MANAGEMENT_ROLES = ["lead moderator", "moderator", "overseer", "forgotten one"]

class JobTracking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    async def cog_load(self):
        # Start the daily check task
        self.daily_job_check.start()
        print("✅ Job Tracking System loaded with auto-demotion")

    async def cog_unload(self):
        self.daily_job_check.cancel()

    def _is_management(self, user) -> bool:
        """Check if user is management"""
        if user.guild_permissions.administrator:
            return True
        if has_special_permissions(user):
            return True
        user_roles = [role.name.lower() for role in user.roles]
        return any(mgmt_role in user_roles for mgmt_role in MANAGEMENT_ROLES)

    def _get_user_job_role(self, member):
        """Get the user's current job role"""
        for job_name, job_data in JOB_ROLES.items():
            role = member.guild.get_role(job_data["role_id"])
            if role and role in member.roles:
                return job_name, job_data
        return None, None

    # Manual commands removed - Job tracking is now fully automatic
    # The system tracks activity based on user presence and messages
    # Daily automated checks handle warnings and demotions
    
    async def _track_user_activity(self, user_id, guild_id, activity_type="general"):
        """Automatically track user activity (called from message events)"""
        try:
            # Get user's job role
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
                
            member = guild.get_member(user_id)
            if not member:
                return
                
            job_name, job_data = self._get_user_job_role(member)
            if not job_name:
                return  # No job role, no tracking needed
            
            # Record activity in database (this would be called from message listeners)
            db.record_user_activity(user_id, guild_id, job_name, activity_type)
            
        except Exception as e:
            print(f"Error tracking activity for user {user_id}: {e}")

    @tasks.loop(hours=24)
    async def daily_job_check(self):
        """Daily task to check job performance and handle warnings/demotions"""
        try:
            print("🔍 Running daily job performance check...")
            
            for guild in self.bot.guilds:
                # Check each user with a job role
                for job_name, job_data in JOB_ROLES.items():
                    role = guild.get_role(job_data["role_id"])
                    if not role:
                        continue
                    
                    for member in role.members:
                        await self._check_user_performance(member, job_name, job_data)
                        
                        # Small delay to prevent rate limiting
                        await asyncio.sleep(0.5)
            
            print("✅ Daily job performance check completed")
            
        except Exception as e:
            print(f"❌ Error in daily job check: {e}")

    async def _check_user_performance(self, member, job_name, job_data):
        """Check individual user performance and handle warnings/demotions"""
        try:
            # Get work statistics
            weekly_stats = db.get_weekly_work_stats(member.id)
            last_work_date = db.get_last_work_date(member.id)
            
            hours_this_week = weekly_stats.get('total_hours', 0)
            days_this_week = weekly_stats.get('days_worked', 0)
            
            # Calculate days since last work
            if last_work_date:
                days_since_work = (datetime.now() - last_work_date).days
            else:
                days_since_work = 999  # Very high number if never worked
            
            # Check if user needs warning or demotion
            needs_warning = (
                hours_this_week < job_data['min_hours_per_week'] or
                days_this_week < job_data['min_days_active'] or
                days_since_work >= job_data['warning_threshold']
            )
            
            needs_demotion = days_since_work >= job_data['demotion_threshold']
            
            if needs_demotion:
                await self._demote_user(member, job_name, job_data, days_since_work)
            elif needs_warning:
                await self._warn_user(member, job_name, job_data, weekly_stats, days_since_work)
                
        except Exception as e:
            print(f"Error checking performance for {member}: {e}")

    async def _warn_user(self, member, job_name, job_data, weekly_stats, days_since_work):
        """Send performance warning to user"""
        try:
            # Check if already warned recently
            recent_warning = db.get_recent_job_warning(member.id, days=3)
            if recent_warning:
                return  # Don't spam warnings
            
            embed = discord.Embed(
                title="⚠️ Job Performance Warning",
                description=f"Your performance as **{job_name.replace('_', ' ').title()}** needs improvement.",
                color=0xffa500,
                timestamp=datetime.now()
            )
            
            hours_this_week = weekly_stats.get('total_hours', 0)
            days_this_week = weekly_stats.get('days_worked', 0)
            
            issues = []
            if hours_this_week < job_data['min_hours_per_week']:
                issues.append(f"Hours: {hours_this_week:.1f}/{job_data['min_hours_per_week']} (below requirement)")
            if days_this_week < job_data['min_days_active']:
                issues.append(f"Active days: {days_this_week}/{job_data['min_days_active']} (below requirement)")
            if days_since_work >= job_data['warning_threshold']:
                issues.append(f"Days since last work: {days_since_work} (inactive too long)")
            
            embed.add_field(
                name="📊 Performance Issues",
                value="\n".join(f"• {issue}" for issue in issues),
                inline=False
            )
            
            embed.add_field(
                name="⚡ Action Required",
                value=f"• Use `/clock-in` and `/clock-out` to track your work\n• Meet weekly requirements to avoid demotion\n• **Demotion in {job_data['demotion_threshold'] - days_since_work} days if no improvement**",
                inline=False
            )
            
            embed.set_footer(text="💼 Job Tracking System • Automatic Performance Monitor")
            
            # Try to DM user
            try:
                await member.send(embed=embed)
                # Record warning in database
                db.record_job_warning(member.id, job_name, "performance_warning")
            except:
                # DM failed, might want to log this
                pass
                
        except Exception as e:
            print(f"Error warning user {member}: {e}")

    async def _demote_user(self, member, job_name, job_data, days_since_work):
        """Demote user for poor performance"""
        try:
            # Get current role
            current_role = member.guild.get_role(job_data["role_id"])
            if not current_role or current_role not in member.roles:
                return  # User doesn't have the role anymore
            
            # Remove current role
            await member.remove_roles(current_role, reason="Auto-demotion for poor job performance")
            
            # Create demotion embed
            embed = discord.Embed(
                title="🔻 Job Demotion Notice",
                description=f"You have been demoted from **{job_name.replace('_', ' ').title()}** due to poor performance.",
                color=0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Reason",
                value=f"• {days_since_work} days without any work activity\n• Failed to meet job requirements consistently",
                inline=False
            )
            
            embed.add_field(
                name="🔄 How to Return",
                value="• Start actively working again using `/clock-in` and `/clock-out`\n• Meet performance requirements consistently\n• Contact management to discuss role restoration",
                inline=False
            )
            
            embed.set_footer(text="💼 Job Tracking System • Automatic Demotion")
            
            # Try to DM user
            try:
                await member.send(embed=embed)
            except:
                pass
            
            # Log demotion
            db.record_job_action(member.id, job_name, "auto_demotion", f"Inactive for {days_since_work} days")
            
            print(f"🔻 Auto-demoted {member.display_name} from {job_name} (inactive {days_since_work} days)")
            
        except Exception as e:
            print(f"Error demoting user {member}: {e}")

    @daily_job_check.before_loop
    async def before_daily_check(self):
        """Wait until bot is ready before starting the daily check"""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(JobTracking(bot))