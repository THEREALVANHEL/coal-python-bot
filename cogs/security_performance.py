import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import time
import os, sys
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import json

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class SecurityPerformance(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Rate limiting system
        self.rate_limits = defaultdict(lambda: defaultdict(deque))
        self.command_cooldowns = {}
        
        # Anti-spam protection
        self.user_message_history = defaultdict(deque)
        self.spam_warnings = defaultdict(int)
        
        # Performance monitoring
        self.command_performance = defaultdict(list)
        self.db_query_times = deque(maxlen=1000)
        
        # Security tracking
        self.failed_attempts = defaultdict(int)
        self.suspicious_activities = []
        
        # Start monitoring tasks
        self.cleanup_rate_limits.start()
        self.performance_monitor.start()
        self.security_audit.start()
        
    @tasks.loop(minutes=5)
    async def cleanup_rate_limits(self):
        """Clean up old rate limit entries"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 1 hour ago
        
        # Clean rate limits
        for user_id in list(self.rate_limits.keys()):
            for command in list(self.rate_limits[user_id].keys()):
                # Remove old entries
                while (self.rate_limits[user_id][command] and 
                       self.rate_limits[user_id][command][0] < cutoff_time):
                    self.rate_limits[user_id][command].popleft()
                
                # Remove empty deques
                if not self.rate_limits[user_id][command]:
                    del self.rate_limits[user_id][command]
            
            # Remove empty user entries
            if not self.rate_limits[user_id]:
                del self.rate_limits[user_id]
        
        # Clean message history for spam detection
        for user_id in list(self.user_message_history.keys()):
            while (self.user_message_history[user_id] and 
                   self.user_message_history[user_id][0][1] < cutoff_time):
                self.user_message_history[user_id].popleft()
            
            if not self.user_message_history[user_id]:
                del self.user_message_history[user_id]
        
        print("🧹 Cleaned up rate limiting and spam detection data")
    
    @tasks.loop(minutes=10)
    async def performance_monitor(self):
        """Monitor bot performance and optimize"""
        try:
            # Calculate average command response times
            total_commands = 0
            total_time = 0
            
            for command_name, times in self.command_performance.items():
                if times:
                    avg_time = sum(times) / len(times)
                    total_time += avg_time
                    total_commands += 1
                    
                    # Alert for slow commands
                    if avg_time > 3.0:  # Commands taking more than 3 seconds
                        print(f"⚠️ Slow command detected: {command_name} averaging {avg_time:.2f}s")
            
            # Calculate average DB query time
            if self.db_query_times:
                avg_db_time = sum(self.db_query_times) / len(self.db_query_times)
                if avg_db_time > 1.0:  # DB queries taking more than 1 second
                    print(f"⚠️ Slow database queries detected: averaging {avg_db_time:.2f}s")
            
            # Memory usage check (simplified)
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            
            if memory_usage > 500:  # Alert if using more than 500MB
                print(f"⚠️ High memory usage detected: {memory_usage:.1f}MB")
                # Clear old performance data to free memory
                for command_name in self.command_performance:
                    if len(self.command_performance[command_name]) > 100:
                        self.command_performance[command_name] = self.command_performance[command_name][-50:]
                        
        except Exception as e:
            print(f"Error in performance monitor: {e}")
    
    @tasks.loop(hours=1)
    async def security_audit(self):
        """Perform security audits and threat detection"""
        try:
            current_time = time.time()
            
            # Check for users with excessive failed attempts
            for user_id, attempts in self.failed_attempts.items():
                if attempts > 10:  # More than 10 failed attempts in an hour
                    self.suspicious_activities.append({
                        "type": "excessive_failures",
                        "user_id": user_id,
                        "attempts": attempts,
                        "timestamp": current_time
                    })
                    print(f"🚨 Security Alert: User {user_id} has {attempts} failed attempts")
            
            # Reset failed attempts counter
            self.failed_attempts.clear()
            
            # Clean old suspicious activities
            cutoff = current_time - 86400  # 24 hours ago
            self.suspicious_activities = [
                activity for activity in self.suspicious_activities
                if activity["timestamp"] > cutoff
            ]
            
        except Exception as e:
            print(f"Error in security audit: {e}")
    
    def check_rate_limit(self, user_id: int, command_name: str, limit: int = 5, window: int = 60) -> bool:
        """Check if user is rate limited for a command"""
        current_time = time.time()
        user_commands = self.rate_limits[user_id][command_name]
        
        # Remove old entries
        while user_commands and user_commands[0] < current_time - window:
            user_commands.popleft()
        
        # Check if limit exceeded
        if len(user_commands) >= limit:
            return False
        
        # Add current attempt
        user_commands.append(current_time)
        return True
    
    def detect_spam(self, user_id: int, message_content: str) -> bool:
        """Detect spam patterns in user messages"""
        current_time = time.time()
        user_history = self.user_message_history[user_id]
        
        # Add current message
        message_hash = hashlib.md5(message_content.encode()).hexdigest()
        user_history.append((message_hash, current_time))
        
        # Keep only last 10 messages
        if len(user_history) > 10:
            user_history.popleft()
        
        # Check for spam patterns
        if len(user_history) >= 5:
            recent_messages = list(user_history)[-5:]
            
            # Check for identical messages
            hashes = [msg[0] for msg in recent_messages]
            if len(set(hashes)) <= 2:  # Only 1-2 unique messages in last 5
                return True
            
            # Check for rapid fire (5 messages in 30 seconds)
            time_diff = recent_messages[-1][1] - recent_messages[0][1]
            if time_diff < 30:
                return True
        
        return False
    
    def log_command_performance(self, command_name: str, execution_time: float):
        """Log command execution time for performance monitoring"""
        self.command_performance[command_name].append(execution_time)
        
        # Keep only last 50 entries per command
        if len(self.command_performance[command_name]) > 50:
            self.command_performance[command_name] = self.command_performance[command_name][-25:]
    
    def log_db_query_time(self, query_time: float):
        """Log database query time"""
        self.db_query_times.append(query_time)
    
    def validate_input(self, input_string: str, max_length: int = 2000, allow_special_chars: bool = True) -> bool:
        """Validate user input for security"""
        if not input_string or len(input_string) > max_length:
            return False
        
        # Check for potentially malicious patterns
        dangerous_patterns = [
            'javascript:', 'data:', 'vbscript:',
            '<script', '</script>', 'eval(', 'function(',
            'document.', 'window.', 'alert('
        ]
        
        input_lower = input_string.lower()
        for pattern in dangerous_patterns:
            if pattern in input_lower:
                return False
        
        if not allow_special_chars:
            # Only allow alphanumeric, spaces, and basic punctuation
            allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-_')
            if not all(char in allowed_chars for char in input_string):
                return False
        
        return True
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitor messages for spam and security threats"""
        if message.author.bot:
            return
        
        # Spam detection
        if self.detect_spam(message.author.id, message.content):
            self.spam_warnings[message.author.id] += 1
            
            # Take action based on warning level
            if self.spam_warnings[message.author.id] >= 3:
                # Mute user for 10 minutes
                try:
                    mute_role = discord.utils.get(message.guild.roles, name="Muted")
                    if mute_role:
                        await message.author.add_roles(mute_role, reason="Anti-spam: Excessive spam detected")
                        
                        # Remove mute after 10 minutes
                        await asyncio.sleep(600)
                        await message.author.remove_roles(mute_role, reason="Anti-spam: Mute expired")
                        
                        self.spam_warnings[message.author.id] = 0
                except discord.HTTPException:
                    pass
            else:
                # Just delete the message and warn
                try:
                    await message.delete()
                    await message.channel.send(
                        f"⚠️ {message.author.mention} Please slow down! Warning {self.spam_warnings[message.author.id]}/3",
                        delete_after=5
                    )
                except discord.HTTPException:
                    pass
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Track command errors for security monitoring"""
        if isinstance(error, commands.CommandOnCooldown):
            return
        
        # Log failed command attempts
        self.failed_attempts[ctx.author.id] += 1
        
        # Log error for analysis
        error_data = {
            "user_id": ctx.author.id,
            "command": ctx.command.name if ctx.command else "unknown",
            "error": str(error),
            "timestamp": time.time()
        }
        
        print(f"⚠️ Command error: {error_data}")
    
    @app_commands.command(name="security-status", description="🛡️ View bot security and performance status")
    @app_commands.default_permissions(administrator=True)
    async def security_status(self, interaction: discord.Interaction):
        """Display security and performance status"""
        
        embed = discord.Embed(
            title="🛡️ Security & Performance Status",
            description="**Real-time monitoring dashboard**",
            color=0x2ecc71
        )
        
        # Rate limiting stats
        total_rate_limited_users = len(self.rate_limits)
        embed.add_field(
            name="⚡ Rate Limiting",
            value=f"**Active Users:** {total_rate_limited_users}\n**Status:** {'🟢 Operational' if total_rate_limited_users < 100 else '🟡 High Load'}",
            inline=True
        )
        
        # Spam detection stats
        spam_warnings_count = len(self.spam_warnings)
        embed.add_field(
            name="🚫 Anti-Spam",
            value=f"**Users with Warnings:** {spam_warnings_count}\n**Status:** {'🟢 Clean' if spam_warnings_count < 10 else '🟡 Active Threats'}",
            inline=True
        )
        
        # Performance stats
        if self.command_performance:
            total_commands = sum(len(times) for times in self.command_performance.values())
            avg_response = sum(sum(times) for times in self.command_performance.values()) / max(total_commands, 1)
        else:
            total_commands = 0
            avg_response = 0
        
        embed.add_field(
            name="📊 Performance",
            value=f"**Commands Executed:** {total_commands}\n**Avg Response:** {avg_response:.2f}s",
            inline=True
        )
        
        # Database performance
        if self.db_query_times:
            avg_db_time = sum(self.db_query_times) / len(self.db_query_times)
            db_status = "🟢 Fast" if avg_db_time < 0.5 else "🟡 Slow" if avg_db_time < 2.0 else "🔴 Very Slow"
        else:
            avg_db_time = 0
            db_status = "🟢 No Data"
        
        embed.add_field(
            name="🗄️ Database",
            value=f"**Avg Query Time:** {avg_db_time:.3f}s\n**Status:** {db_status}",
            inline=True
        )
        
        # Security threats
        recent_threats = len([
            activity for activity in self.suspicious_activities
            if activity["timestamp"] > time.time() - 3600  # Last hour
        ])
        
        embed.add_field(
            name="🚨 Security Threats",
            value=f"**Recent Threats:** {recent_threats}\n**Status:** {'🟢 Secure' if recent_threats == 0 else '🟡 Monitor' if recent_threats < 5 else '🔴 High Alert'}",
            inline=True
        )
        
        # System health
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            health_status = "🟢 Healthy" if cpu_percent < 70 and memory_percent < 80 else "🟡 Stressed" if cpu_percent < 90 and memory_percent < 90 else "🔴 Critical"
        except:
            health_status = "🟡 Unknown"
            cpu_percent = 0
            memory_percent = 0
        
        embed.add_field(
            name="💻 System Health",
            value=f"**CPU:** {cpu_percent:.1f}%\n**Memory:** {memory_percent:.1f}%\n**Status:** {health_status}",
            inline=False
        )
        
        embed.set_footer(text="🛡️ Security monitoring • Updated in real-time")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="clear-rate-limits", description="🧹 Clear rate limits for all users")
    @app_commands.default_permissions(administrator=True)
    async def clear_rate_limits(self, interaction: discord.Interaction):
        """Clear all rate limits"""
        
        cleared_users = len(self.rate_limits)
        self.rate_limits.clear()
        self.command_cooldowns.clear()
        
        embed = discord.Embed(
            title="🧹 Rate Limits Cleared",
            description=f"Cleared rate limits for **{cleared_users}** users",
            color=0x00ff00
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="security-audit", description="🔍 Perform manual security audit")
    @app_commands.default_permissions(administrator=True)
    async def manual_security_audit(self, interaction: discord.Interaction):
        """Perform a manual security audit"""
        
        await interaction.response.defer()
        
        # Analyze current threats
        threats_found = []
        
        # Check for excessive failed attempts
        for user_id, attempts in self.failed_attempts.items():
            if attempts > 5:
                threats_found.append(f"User <@{user_id}>: {attempts} failed attempts")
        
        # Check for spam patterns
        for user_id, warnings in self.spam_warnings.items():
            if warnings > 0:
                threats_found.append(f"User <@{user_id}>: {warnings} spam warnings")
        
        # Check performance issues
        slow_commands = []
        for command_name, times in self.command_performance.items():
            if times:
                avg_time = sum(times) / len(times)
                if avg_time > 2.0:
                    slow_commands.append(f"`{command_name}`: {avg_time:.2f}s")
        
        embed = discord.Embed(
            title="🔍 Security Audit Results",
            description="**Manual security audit completed**",
            color=0x3498db
        )
        
        if threats_found:
            embed.add_field(
                name="🚨 Threats Detected",
                value="\n".join(threats_found[:10]) + ("\n..." if len(threats_found) > 10 else ""),
                inline=False
            )
        else:
            embed.add_field(
                name="✅ Security Status",
                value="No immediate threats detected",
                inline=False
            )
        
        if slow_commands:
            embed.add_field(
                name="⚠️ Performance Issues",
                value="\n".join(slow_commands[:5]) + ("\n..." if len(slow_commands) > 5 else ""),
                inline=False
            )
        
        embed.add_field(
            name="📊 Audit Summary",
            value=f"**Total Users Monitored:** {len(self.rate_limits)}\n"
                  f"**Commands Tracked:** {len(self.command_performance)}\n"
                  f"**Suspicious Activities:** {len(self.suspicious_activities)}",
            inline=False
        )
        
        embed.set_footer(text="🔍 Manual audit • Review and take action as needed")
        embed.timestamp = datetime.now()
        
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityPerformance(bot))