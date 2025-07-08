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

    @app_commands.command(name="clock-in", description="Clock in to start working")
    async def clock_in(self, interaction: discord.Interaction):
        """Clock in to start working"""
        try:
            # Check if user has a job role
            job_name, job_data = self._get_user_job_role(interaction.user)
            if not job_name:
                embed = discord.Embed(
                    title="❌ No Job Role",
                    description="You need a job role to use the time tracking system!",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Check if already clocked in
            current_session = db.get_active_work_session(interaction.user.id)
            if current_session:
                start_time = current_session.get('start_time')
                if isinstance(start_time, datetime):
                    time_str = f"<t:{int(start_time.timestamp())}:R>"
                else:
                    time_str = "some time ago"
                
                embed = discord.Embed(
                    title="⚠️ Already Clocked In",
                    description=f"You're already working! Started {time_str}",
                    color=0xffa500
                )
                embed.add_field(
                    name="💡 Tip",
                    value="Use `/clock-out` to finish your work session.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Clock in
            session_data = {
                'user_id': interaction.user.id,
                'guild_id': interaction.guild.id,
                'job_role': job_name,
                'start_time': datetime.now(),
                'active': True
            }
            
            success = db.start_work_session(session_data)
            if not success:
                embed = discord.Embed(
                    title="❌ System Error",
                    description="Failed to clock in. Please try again.",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title="✅ Clocked In",
                description=f"**Job Role:** {job_name.replace('_', ' ').title()}\n**Started:** <t:{int(datetime.now().timestamp())}:F>",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="📊 Requirements",
                value=f"**Min Hours/Week:** {job_data['min_hours_per_week']}\n**Min Days Active:** {job_data['min_days_active']}",
                inline=True
            )
            embed.set_footer(text="💼 Job Tracking System • Remember to clock out!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Clock In Error",
                description="Failed to clock in. Please try again.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clock-out", description="Clock out to finish working")
    async def clock_out(self, interaction: discord.Interaction):
        """Clock out to finish working"""
        try:
            # Check if clocked in
            current_session = db.get_active_work_session(interaction.user.id)
            if not current_session:
                embed = discord.Embed(
                    title="❌ Not Clocked In",
                    description="You're not currently working! Use `/clock-in` to start.",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Calculate work duration
            start_time = current_session.get('start_time')
            if not isinstance(start_time, datetime):
                start_time = datetime.now() - timedelta(hours=1)  # Fallback
            
            end_time = datetime.now()
            duration = end_time - start_time
            hours_worked = duration.total_seconds() / 3600

            # Minimum 15 minutes to count
            if hours_worked < 0.25:
                embed = discord.Embed(
                    title="⚠️ Session Too Short",
                    description="Work sessions must be at least 15 minutes to count.",
                    color=0xffa500
                )
                # End the session but don't record it
                db.end_work_session(interaction.user.id, end_time, 0)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # End the session and record the time
            success = db.end_work_session(interaction.user.id, end_time, hours_worked)
            if not success:
                embed = discord.Embed(
                    title="❌ System Error",
                    description="Failed to clock out. Please try again.",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Get job role for context
            job_name, job_data = self._get_user_job_role(interaction.user)
            
            embed = discord.Embed(
                title="✅ Clocked Out",
                description=f"**Work Session Completed**\n**Duration:** {hours_worked:.1f} hours",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="⏰ Session Details",
                value=f"**Started:** <t:{int(start_time.timestamp())}:t>\n**Ended:** <t:{int(end_time.timestamp())}:t>",
                inline=True
            )
            
            # Get weekly stats
            weekly_stats = db.get_weekly_work_stats(interaction.user.id)
            hours_this_week = weekly_stats.get('total_hours', 0)
            days_this_week = weekly_stats.get('days_worked', 0)
            
            if job_data:
                status = "✅" if hours_this_week >= job_data['min_hours_per_week'] else "⚠️"
                embed.add_field(
                    name="📊 Weekly Progress",
                    value=f"**Hours:** {hours_this_week:.1f}/{job_data['min_hours_per_week']} {status}\n**Days:** {days_this_week}/{job_data['min_days_active']}",
                    inline=True
                )
            
            embed.set_footer(text="💼 Job Tracking System • Great work!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Clock Out Error",
                description="Failed to clock out. Please try again.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="work-stats", description="View your work statistics")
    @app_commands.describe(user="User to check stats for (management only)")
    async def work_stats(self, interaction: discord.Interaction, user: discord.Member = None):
        """View work statistics"""
        try:
            target_user = user or interaction.user
            
            # Check permissions for viewing other users
            if user and user != interaction.user and not self._is_management(interaction.user):
                embed = discord.Embed(
                    title="❌ Access Denied",
                    description="Only management can view other users' work stats.",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Get job role
            job_name, job_data = self._get_user_job_role(target_user)
            if not job_name:
                embed = discord.Embed(
                    title="❌ No Job Role",
                    description=f"{target_user.display_name} doesn't have a job role.",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Get work statistics
            weekly_stats = db.get_weekly_work_stats(target_user.id)
            monthly_stats = db.get_monthly_work_stats(target_user.id)
            
            # Check if currently working
            current_session = db.get_active_work_session(target_user.id)
            
            embed = discord.Embed(
                title=f"💼 Work Stats: {target_user.display_name}",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Job info
            embed.add_field(
                name="👔 Job Information",
                value=f"**Role:** {job_name.replace('_', ' ').title()}\n**Status:** {'🟢 Working' if current_session else '🔴 Off Duty'}",
                inline=True
            )
            
            # Weekly stats
            weekly_hours = weekly_stats.get('total_hours', 0)
            weekly_days = weekly_stats.get('days_worked', 0)
            weekly_status = "✅" if weekly_hours >= job_data['min_hours_per_week'] else "⚠️"
            
            embed.add_field(
                name="📊 This Week",
                value=f"**Hours:** {weekly_hours:.1f}/{job_data['min_hours_per_week']} {weekly_status}\n**Days:** {weekly_days}/{job_data['min_days_active']}",
                inline=True
            )
            
            # Monthly stats
            monthly_hours = monthly_stats.get('total_hours', 0)
            monthly_days = monthly_stats.get('days_worked', 0)
            
            embed.add_field(
                name="📅 This Month",
                value=f"**Hours:** {monthly_hours:.1f}\n**Days:** {monthly_days}",
                inline=True
            )
            
            # Current session info
            if current_session:
                start_time = current_session.get('start_time')
                if isinstance(start_time, datetime):
                    current_duration = (datetime.now() - start_time).total_seconds() / 3600
                    embed.add_field(
                        name="⏰ Current Session",
                        value=f"**Started:** <t:{int(start_time.timestamp())}:R>\n**Duration:** {current_duration:.1f} hours",
                        inline=False
                    )
            
            # Performance status
            performance_issues = []
            if weekly_hours < job_data['min_hours_per_week']:
                performance_issues.append(f"Below weekly hour requirement ({weekly_hours:.1f}/{job_data['min_hours_per_week']})")
            if weekly_days < job_data['min_days_active']:
                performance_issues.append(f"Below weekly day requirement ({weekly_days}/{job_data['min_days_active']})")
            
            if performance_issues:
                embed.add_field(
                    name="⚠️ Performance Alerts",
                    value="\n".join(f"• {issue}" for issue in performance_issues),
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ Performance Status",
                    value="Meeting all job requirements!",
                    inline=False
                )
            
            embed.set_footer(text="💼 Job Tracking System")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Stats Error",
                description="Failed to retrieve work statistics.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="job-leaderboard", description="View the job performance leaderboard")
    async def job_leaderboard(self, interaction: discord.Interaction):
        """View job performance leaderboard"""
        try:
            # Get leaderboard data
            leaderboard = db.get_job_performance_leaderboard(limit=10)
            
            if not leaderboard:
                embed = discord.Embed(
                    title="📊 Job Performance Leaderboard",
                    description="No work data available yet!",
                    color=0x7c3aed
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🏆 Job Performance Leaderboard",
                description="Top performers this week",
                color=0xffd700,
                timestamp=datetime.now()
            )
            
            leaderboard_text = []
            for i, entry in enumerate(leaderboard, 1):
                user = interaction.guild.get_member(entry.get('user_id'))
                if not user:
                    continue
                
                hours = entry.get('weekly_hours', 0)
                job_role = entry.get('job_role', 'Unknown').replace('_', ' ').title()
                
                # Add trophy emojis for top 3
                if i == 1:
                    emoji = "🥇"
                elif i == 2:
                    emoji = "🥈"
                elif i == 3:
                    emoji = "🥉"
                else:
                    emoji = f"**#{i}**"
                
                leaderboard_text.append(f"{emoji} {user.display_name} - **{hours:.1f}h** ({job_role})")
            
            if leaderboard_text:
                embed.add_field(
                    name="👥 Top Performers",
                    value="\n".join(leaderboard_text),
                    inline=False
                )
            
            embed.set_footer(text="💼 Job Tracking System • Keep up the great work!")
            
            await interaction.response.send_message(embed=embed, ephemeral=False)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Leaderboard Error",
                description="Failed to load leaderboard data.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

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