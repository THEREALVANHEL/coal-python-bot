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

# Job roles and their requirements - UPDATED FOR 24-HOUR AUTO-DEMOTION
JOB_ROLES = {
    "intern": {
        "role_id": 1370000000000000000,  # Replace with actual role ID
        "min_hours_per_week": 8,
        "min_days_active": 2,
        "warning_threshold": 12,  # 12 hours before warning
        "demotion_threshold": 24   # 24 hours before auto-demotion
    },
    "junior_developer": {
        "role_id": 1370000000000000001,  # Replace with actual role ID
        "min_hours_per_week": 12,
        "min_days_active": 3,
        "warning_threshold": 18,  # 18 hours before warning
        "demotion_threshold": 24   # 24 hours before auto-demotion
    },
    "developer": {
        "role_id": 1370000000000000002,  # Replace with actual role ID
        "min_hours_per_week": 16,
        "min_days_active": 3,
        "warning_threshold": 20,  # 20 hours before warning  
        "demotion_threshold": 24   # 24 hours before auto-demotion
    },
    "senior_developer": {
        "role_id": 1370000000000000003,  # Replace with actual role ID
        "min_hours_per_week": 20,
        "min_days_active": 4,
        "warning_threshold": 18,  # 18 hours before warning
        "demotion_threshold": 24   # 24 hours before auto-demotion
    },
    "team_lead": {
        "role_id": 1370000000000000004,  # Replace with actual role ID
        "min_hours_per_week": 24,
        "min_days_active": 4,
        "warning_threshold": 16,  # 16 hours before warning
        "demotion_threshold": 24   # 24 hours before auto-demotion
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

    @tasks.loop(hours=2)  # Check every 2 hours instead of 24 for faster response
    async def daily_job_check(self):
        """Periodic task to check job performance and handle warnings/demotions - RUNS EVERY 2 HOURS"""
        try:
            print("🔍 [24h System] Running job performance check...")
            
            demoted_count = 0
            warned_count = 0
            checked_count = 0
            
            for guild in self.bot.guilds:
                # Check each user with a job role
                for job_name, job_data in JOB_ROLES.items():
                    role = guild.get_role(job_data["role_id"])
                    if not role:
                        continue
                    
                    for member in role.members:
                        checked_count += 1
                        result = await self._check_user_performance(member, job_name, job_data)
                        
                        # Track results for logging
                        if result == "demoted":
                            demoted_count += 1
                        elif result == "warned":
                            warned_count += 1
                        
                        # Small delay to prevent rate limiting
                        await asyncio.sleep(0.5)
            
            print(f"✅ [24h System] Performance check completed: {checked_count} users checked, {warned_count} warned, {demoted_count} demoted")
            
        except Exception as e:
            print(f"❌ [24h System] Error in job performance check: {e}")

    async def _check_user_performance(self, member, job_name, job_data):
        """Check individual user performance and handle warnings/demotions - UPDATED FOR 24-HOUR SYSTEM"""
        try:
            # Get work statistics
            weekly_stats = db.get_weekly_work_stats(member.id)
            last_work_date = db.get_last_work_date(member.id)
            
            hours_this_week = weekly_stats.get('total_hours', 0)
            days_this_week = weekly_stats.get('days_worked', 0)
            
            # Calculate hours since last work (changed from days to hours)
            if last_work_date:
                hours_since_work = (datetime.now() - last_work_date).total_seconds() / 3600
            else:
                hours_since_work = 999  # Very high number if never worked
            
            # Check if user needs warning or demotion (now using hours)
            needs_warning = (
                hours_this_week < job_data['min_hours_per_week'] or
                days_this_week < job_data['min_days_active'] or
                hours_since_work >= job_data['warning_threshold']
            )
            
            # AUTO-DEMOTION: 24 hours of inactivity triggers demotion
            needs_demotion = hours_since_work >= job_data['demotion_threshold']
            
            if needs_demotion:
                await self._demote_user(member, job_name, job_data, hours_since_work)
                return "demoted"
            elif needs_warning:
                await self._warn_user(member, job_name, job_data, weekly_stats, hours_since_work)
                return "warned"
            
            return "ok"
                
        except Exception as e:
            print(f"Error checking performance for {member}: {e}")
            return "error"

    async def _warn_user(self, member, job_name, job_data, weekly_stats, hours_since_work):
        """Send performance warning to user - UPDATED FOR HOURS"""
        try:
            # Check if already warned recently (changed to 6 hours instead of 3 days)
            recent_warning = db.get_recent_job_warning(member.id, hours=6)
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
            if hours_since_work >= job_data['warning_threshold']:
                issues.append(f"Hours since last work: {hours_since_work:.1f} (inactive too long)")
            
            embed.add_field(
                name="📊 Performance Issues",
                value="\n".join(f"• {issue}" for issue in issues),
                inline=False
            )
            
            hours_until_demotion = job_data['demotion_threshold'] - hours_since_work
            embed.add_field(
                name="⚡ **URGENT ACTION REQUIRED**",
                value=f"• Use `/work` command immediately\n• Complete work to reset your activity timer\n• **⏰ DEMOTION IN {hours_until_demotion:.1f} HOURS if no work completed**",
                inline=False
            )
            
            embed.add_field(
                name="🚨 **24-Hour Demotion Policy**",
                value="• Work at least once every 24 hours\n• Failure to work = automatic demotion\n• Policy applies to all job roles",
                inline=False
            )
            
            embed.set_footer(text="💼 24-Hour Activity Policy • Work Now to Keep Your Role!")
            
            # Try to DM user
            try:
                await member.send(embed=embed)
                # Record warning in database
                db.record_job_warning(member.id, job_name, f"performance_warning_hours_{hours_since_work:.1f}")
            except:
                # DM failed, might want to log this
                pass
                
        except Exception as e:
            print(f"Error warning user {member}: {e}")

    async def _demote_user(self, member, job_name, job_data, hours_since_work):
        """Demote user for poor performance - UPDATED FOR 24-HOUR SYSTEM"""
        try:
            # Get current role
            current_role = member.guild.get_role(job_data["role_id"])
            if not current_role or current_role not in member.roles:
                return  # User doesn't have the role anymore
            
            # Remove current role
            await member.remove_roles(current_role, reason=f"Auto-demotion: {hours_since_work:.1f} hours without work")
            
            # Create demotion embed
            embed = discord.Embed(
                title="🔻 **AUTOMATIC DEMOTION NOTICE**",
                description=f"You have been **demoted** from **{job_name.replace('_', ' ').title()}** due to inactivity.",
                color=0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 Reason for Demotion",
                value=f"• **{hours_since_work:.1f} hours** without any work activity\n• Exceeded the **24-hour activity requirement**\n• Failed to respond to performance warnings",
                inline=False
            )
            
            embed.add_field(
                name="🚨 **24-Hour Policy**",
                value="• All job roles require work activity every 24 hours\n• This policy ensures active participation\n• No exceptions to maintain fairness",
                inline=False
            )
            
            embed.add_field(
                name="🔄 **How to Get Your Role Back**",
                value="• Start working immediately using `/work`\n• Be consistent with daily work activity\n• Contact management after proving consistent activity\n• Work for at least 3 consecutive days",
                inline=False
            )
            
            embed.add_field(
                name="💡 **Prevention Tips**", 
                value="• Set daily reminders to work\n• Work at least once every 20 hours for safety\n• Check your work status regularly\n• Don't wait for warnings - stay active!",
                inline=False
            )
            
            embed.set_footer(text="💼 Automatic Demotion System • Stay Active to Keep Your Role!")
            
            # Try to DM user
            try:
                await member.send(embed=embed)
            except:
                pass
            
            # Log demotion
            db.record_job_action(member.id, job_name, "auto_demotion_24h", f"Inactive for {hours_since_work:.1f} hours")
            
            print(f"🔻 [24h Auto-Demotion] {member.display_name} demoted from {job_name} (inactive {hours_since_work:.1f} hours)")
            
            # Also try to notify in a staff channel if available
            try:
                # Look for staff notification channel
                for channel in member.guild.text_channels:
                    if 'staff' in channel.name.lower() or 'log' in channel.name.lower():
                        staff_embed = discord.Embed(
                            title="🔻 Automatic Demotion Alert",
                            description=f"**User:** {member.mention}\n**Role:** {job_name.replace('_', ' ').title()}\n**Reason:** {hours_since_work:.1f} hours inactive",
                            color=0xff0000,
                            timestamp=datetime.now()
                        )
                        staff_embed.set_footer(text="24-Hour Auto-Demotion System")
                        await channel.send(embed=staff_embed)
                        break
            except:
                pass
            
        except Exception as e:
            print(f"Error demoting user {member}: {e}")

    @daily_job_check.before_loop
    async def before_daily_check(self):
        """Wait until bot is ready before starting the periodic check"""
        await self.bot.wait_until_ready()
        print("🚀 [24h System] Job tracking system initialized - 24-hour auto-demotion active!")

    # COMMANDS FOR THE NEW 24-HOUR SYSTEM
    


    @app_commands.command(name="work-policy", description="📋 View the 24-hour work policy and requirements")
    async def work_policy(self, interaction: discord.Interaction):
        """Display the 24-hour work policy"""
        embed = discord.Embed(
            title="📋 24-Hour Work Activity Policy",
            description="**New automated system to ensure active participation**",
            color=0x5865f2,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🚨 **Core Policy**",
            value="• **Work at least once every 24 hours**\n• Use `/work` command to reset your timer\n• **Automatic demotion** after 24 hours of inactivity\n• Policy applies to ALL job roles",
            inline=False
        )
        
        embed.add_field(
            name="⏰ **Warning System**",
            value="• Warnings sent at 12-20 hour marks\n• Final warning before demotion\n• Check status with `/work-status`\n• DM notifications when available",
            inline=True
        )
        
        embed.add_field(
            name="🔄 **How to Stay Active**",
            value="• Use `/work` daily\n• Set phone reminders\n• Work every 20 hours for safety\n• Don't wait for warnings!",
            inline=True
        )
        
        embed.add_field(
            name="📊 **Job Role Requirements**",
            value="**Intern:** 8h/week, 2 days\n**Junior Developer:** 12h/week, 3 days\n**Developer:** 16h/week, 3 days\n**Senior Developer:** 20h/week, 4 days\n**Team Lead:** 24h/week, 4 days",
            inline=False
        )
        
        embed.add_field(
            name="🔻 **Demotion Process**",
            value="• **Automatic** after 24 hours\n• **No exceptions** for fairness\n• Role removed immediately\n• Must reapply through management\n• Prove 3+ days consistent work",
            inline=True
        )
        
        embed.add_field(
            name="💡 **Recovery Process**",
            value="• Start working immediately\n• Be consistent for 3+ days\n• Contact management\n• Show commitment to activity\n• No shortcuts - earn it back!",
            inline=True
        )
        
        embed.add_field(
            name="🎯 **Tips for Success**",
            value="• **Set daily reminders**\n• **Work in the morning**\n• **Use `/work-status` regularly**\n• **Don't push the 24h limit**\n• **Stay ahead of deadlines**",
            inline=False
        )
        
        embed.set_footer(text="💼 24-Hour Activity Policy • Stay Active, Keep Your Role!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="job-overview", description="🛠️ Management overview of all job role activity (Staff only)")
    async def job_overview(self, interaction: discord.Interaction):
        """Management command to see all job role activity"""
        if not self._is_management(interaction.user):
            await interaction.response.send_message("❌ This command is for management only.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🛠️ Job Role Activity Overview",
            description="**24-Hour Activity Tracking Summary**",
            color=0x5865f2,
            timestamp=datetime.now()
        )
        
        total_members = 0
        critical_members = 0
        warning_members = 0
        active_members = 0
        
        for job_name, job_data in JOB_ROLES.items():
            role = interaction.guild.get_role(job_data["role_id"])
            if not role:
                continue
            
            role_members = len(role.members)
            total_members += role_members
            
            role_critical = 0
            role_warning = 0
            role_active = 0
            
            for member in role.members:
                try:
                    last_work_date = db.get_last_work_date(member.id)
                    if last_work_date:
                        hours_since_work = (datetime.now() - last_work_date).total_seconds() / 3600
                    else:
                        hours_since_work = 999
                    
                    if hours_since_work >= job_data['demotion_threshold']:
                        role_critical += 1
                        critical_members += 1
                    elif hours_since_work >= job_data['warning_threshold']:
                        role_warning += 1
                        warning_members += 1
                    else:
                        role_active += 1
                        active_members += 1
                except:
                    role_critical += 1
                    critical_members += 1
            
            status_text = f"🟢 Active: {role_active} | 🟡 Warning: {role_warning} | 🔴 Critical: {role_critical}"
            
            embed.add_field(
                name=f"**{job_name.replace('_', ' ').title()}** ({role_members} members)",
                value=status_text,
                inline=False
            )
        
        # Summary
        embed.add_field(
            name="📊 **Total Summary**",
            value=f"**Total Members:** {total_members}\n🟢 **Active:** {active_members}\n🟡 **Warning:** {warning_members}\n🔴 **Critical:** {critical_members}",
            inline=False
        )
        
        embed.set_footer(text="🛠️ Management Overview • 24-Hour Tracking System")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(JobTracking(bot))