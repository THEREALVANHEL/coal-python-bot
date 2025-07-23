import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
from .database import get_db_manager

logger = logging.getLogger(__name__)

class BotAnalytics:
    """Comprehensive analytics and insights system"""
    
    def __init__(self):
        self.command_usage = defaultdict(int)
        self.user_activity = defaultdict(list)
        self.error_tracking = []
        self.performance_metrics = []
        self.engagement_data = defaultdict(dict)
        
    async def track_command_usage(self, command: str, user_id: int, guild_id: int = None, execution_time: float = None):
        """Track detailed command usage statistics"""
        try:
            db_manager = get_db_manager()
            if db_manager:
                await db_manager.track_command_usage(command, user_id, guild_id)
            
            # In-memory tracking for real-time analytics
            self.command_usage[command] += 1
            
            # Track user activity patterns
            self.user_activity[user_id].append({
                "command": command,
                "timestamp": time.time(),
                "guild_id": guild_id,
                "execution_time": execution_time
            })
            
            # Clean old activity data (keep last 7 days)
            cutoff_time = time.time() - 604800  # 7 days
            self.user_activity[user_id] = [
                activity for activity in self.user_activity[user_id]
                if activity["timestamp"] > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error tracking command usage: {e}")
    
    async def track_error(self, error_type: str, command: str, user_id: int, error_details: str):
        """Track errors for analysis and improvement"""
        error_data = {
            "error_type": error_type,
            "command": command,
            "user_id": user_id,
            "error_details": error_details,
            "timestamp": datetime.now(),
            "resolved": False
        }
        
        self.error_tracking.append(error_data)
        
        # Keep only last 1000 errors
        if len(self.error_tracking) > 1000:
            self.error_tracking = self.error_tracking[-1000:]
        
        # Store in database
        try:
            db_manager = get_db_manager()
            if db_manager:
                await db_manager.db.error_logs.insert_one(error_data)
        except Exception as e:
            logger.error(f"Error storing error log: {e}")
    
    async def track_performance(self, operation: str, duration: float, success: bool):
        """Track performance metrics"""
        metric = {
            "operation": operation,
            "duration": duration,
            "success": success,
            "timestamp": time.time()
        }
        
        self.performance_metrics.append(metric)
        
        # Keep only last 10000 metrics
        if len(self.performance_metrics) > 10000:
            self.performance_metrics = self.performance_metrics[-10000:]
    
    async def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """Generate personalized insights for a user"""
        try:
            db_manager = get_db_manager()
            if not db_manager:
                return {}
            
            user_data = await db_manager.get_user_data_cached(user_id)
            user_activities = self.user_activity.get(user_id, [])
            
            # Calculate activity patterns
            recent_activities = [
                act for act in user_activities
                if time.time() - act["timestamp"] < 86400  # Last 24 hours
            ]
            
            command_frequency = Counter(act["command"] for act in recent_activities)
            avg_session_length = self._calculate_avg_session_length(user_activities)
            most_active_hours = self._get_most_active_hours(user_activities)
            
            insights = {
                "user_id": user_id,
                "total_commands": len(user_activities),
                "commands_today": len(recent_activities),
                "favorite_commands": dict(command_frequency.most_common(5)),
                "avg_session_length_minutes": round(avg_session_length / 60, 2),
                "most_active_hours": most_active_hours,
                "engagement_level": self._calculate_engagement_level(user_id),
                "achievements_unlocked": len(user_data.get("achievements", [])),
                "economic_activity": {
                    "coins": user_data.get("coins", 0),
                    "bank_balance": user_data.get("bank_balance", 0),
                    "total_earned": user_data.get("statistics", {}).get("total_earned", 0),
                    "total_spent": user_data.get("statistics", {}).get("total_spent", 0)
                },
                "gaming_stats": await self._get_gaming_statistics(user_id),
                "suggestions": await self._generate_user_suggestions(user_id, user_data)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating user insights: {e}")
            return {}
    
    async def get_server_insights(self, guild_id: int = None) -> Dict[str, Any]:
        """Generate comprehensive server insights"""
        try:
            db_manager = get_db_manager()
            if not db_manager:
                return {}
            
            server_stats = await db_manager.get_server_stats()
            
            # Calculate real-time metrics
            current_time = time.time()
            recent_activity = []
            
            for user_activities in self.user_activity.values():
                recent_activity.extend([
                    act for act in user_activities
                    if current_time - act["timestamp"] < 86400
                ])
            
            insights = {
                "timestamp": datetime.now().isoformat(),
                "user_statistics": {
                    "total_users": server_stats.get("total_users", 0),
                    "active_users_24h": server_stats.get("active_users_24h", 0),
                    "new_users_today": await self._count_new_users_today(),
                    "retention_rate": await self._calculate_retention_rate()
                },
                "economic_health": {
                    "total_coins_circulation": server_stats.get("total_coins", 0),
                    "total_bank_deposits": server_stats.get("total_bank", 0),
                    "average_user_wealth": server_stats.get("avg_coins", 0),
                    "economic_activity_score": await self._calculate_economic_activity()
                },
                "command_analytics": {
                    "total_commands_24h": len(recent_activity),
                    "most_popular_commands": dict(Counter(act["command"] for act in recent_activity).most_common(10)),
                    "command_success_rate": await self._calculate_command_success_rate(),
                    "average_response_time": self._calculate_avg_response_time()
                },
                "engagement_metrics": {
                    "daily_active_users": len(set(act["user_id"] for act in recent_activity if "user_id" in act)),
                    "average_session_length": self._calculate_global_avg_session_length(),
                    "peak_activity_hours": self._get_peak_activity_hours(recent_activity),
                    "user_engagement_score": await self._calculate_global_engagement_score()
                },
                "error_analysis": {
                    "errors_24h": len([err for err in self.error_tracking if (datetime.now() - err["timestamp"]).total_seconds() < 86400]),
                    "most_common_errors": self._get_most_common_errors(),
                    "error_rate": self._calculate_error_rate(),
                    "critical_issues": await self._identify_critical_issues()
                },
                "performance_metrics": {
                    "average_response_time": self._calculate_avg_response_time(),
                    "success_rate": self._calculate_overall_success_rate(),
                    "database_performance": await self._get_database_performance(),
                    "system_health_score": await self._calculate_system_health_score()
                }
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating server insights: {e}")
            return {}
    
    async def generate_recommendations(self, guild_id: int = None) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []
        
        try:
            server_insights = await self.get_server_insights(guild_id)
            
            # Analyze error rates
            error_rate = server_insights.get("error_analysis", {}).get("error_rate", 0)
            if error_rate > 0.05:  # More than 5% error rate
                recommendations.append({
                    "priority": "high",
                    "category": "stability",
                    "title": "High Error Rate Detected",
                    "description": f"Current error rate is {error_rate:.2%}. Consider investigating common errors.",
                    "action": "Review error logs and implement fixes for most common issues"
                })
            
            # Analyze user engagement
            engagement_score = server_insights.get("engagement_metrics", {}).get("user_engagement_score", 0)
            if engagement_score < 0.6:  # Low engagement
                recommendations.append({
                    "priority": "medium",
                    "category": "engagement",
                    "title": "Low User Engagement",
                    "description": f"User engagement score is {engagement_score:.2f}. Consider adding more interactive features.",
                    "action": "Implement new games, events, or social features to boost engagement"
                })
            
            # Analyze economic health
            economic_activity = server_insights.get("economic_health", {}).get("economic_activity_score", 0)
            if economic_activity < 0.5:  # Low economic activity
                recommendations.append({
                    "priority": "medium",
                    "category": "economy",
                    "title": "Low Economic Activity",
                    "description": "Users aren't actively participating in the economy.",
                    "action": "Consider adjusting reward rates or adding new economic features"
                })
            
            # Analyze command usage patterns
            popular_commands = server_insights.get("command_analytics", {}).get("most_popular_commands", {})
            if popular_commands:
                least_used = min(popular_commands.values())
                most_used = max(popular_commands.values())
                if most_used / least_used > 10:  # Large disparity
                    recommendations.append({
                        "priority": "low",
                        "category": "features",
                        "title": "Uneven Command Usage",
                        "description": "Some commands are rarely used while others are very popular.",
                        "action": "Consider improving or removing underused commands, or promoting them better"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _calculate_avg_session_length(self, activities: List[Dict[str, Any]]) -> float:
        """Calculate average session length for a user"""
        if len(activities) < 2:
            return 0
        
        sessions = []
        current_session_start = activities[0]["timestamp"]
        last_activity = activities[0]["timestamp"]
        
        for activity in activities[1:]:
            time_gap = activity["timestamp"] - last_activity
            
            if time_gap > 1800:  # 30 minutes gap = new session
                sessions.append(last_activity - current_session_start)
                current_session_start = activity["timestamp"]
            
            last_activity = activity["timestamp"]
        
        # Add final session
        sessions.append(last_activity - current_session_start)
        
        return sum(sessions) / len(sessions) if sessions else 0
    
    def _get_most_active_hours(self, activities: List[Dict[str, Any]]) -> List[int]:
        """Get the most active hours for a user"""
        hour_counts = defaultdict(int)
        
        for activity in activities:
            hour = datetime.fromtimestamp(activity["timestamp"]).hour
            hour_counts[hour] += 1
        
        return sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)[:3]
    
    def _calculate_engagement_level(self, user_id: int) -> str:
        """Calculate user engagement level"""
        activities = self.user_activity.get(user_id, [])
        recent_activities = [
            act for act in activities
            if time.time() - act["timestamp"] < 604800  # Last week
        ]
        
        activity_count = len(recent_activities)
        
        if activity_count >= 50:
            return "very_high"
        elif activity_count >= 25:
            return "high"
        elif activity_count >= 10:
            return "medium"
        elif activity_count >= 3:
            return "low"
        else:
            return "very_low"
    
    async def _get_gaming_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get gaming statistics for a user"""
        try:
            db_manager = get_db_manager()
            if not db_manager:
                return {}
            
            # This would typically query game-specific collections
            # For now, return basic structure
            return {
                "trivia_played": 0,
                "trivia_correct": 0,
                "slots_played": 0,
                "slots_won": 0,
                "wordchain_played": 0,
                "wordchain_longest_streak": 0
            }
            
        except Exception as e:
            logger.error(f"Error fetching gaming statistics: {e}")
            return {}
    
    async def _generate_user_suggestions(self, user_id: int, user_data: Dict[str, Any]) -> List[str]:
        """Generate personalized suggestions for a user"""
        suggestions = []
        
        coins = user_data.get("coins", 0)
        bank_balance = user_data.get("bank_balance", 0)
        pets = user_data.get("pets", [])
        
        if coins > 10000 and bank_balance == 0:
            suggestions.append("💰 Consider depositing some coins in the bank to earn interest!")
        
        if not pets:
            suggestions.append("🐾 You might enjoy adopting a pet companion!")
        
        if len(user_data.get("achievements", [])) < 5:
            suggestions.append("🏆 Try different commands to unlock achievements!")
        
        activities = self.user_activity.get(user_id, [])
        recent_commands = set(act["command"] for act in activities[-20:])
        
        if "trivia" not in recent_commands:
            suggestions.append("🧠 Test your knowledge with the trivia game!")
        
        if "work" not in recent_commands:
            suggestions.append("💼 Don't forget to work to earn coins!")
        
        return suggestions
    
    async def _count_new_users_today(self) -> int:
        """Count new users registered today"""
        try:
            db_manager = get_db_manager()
            if not db_manager:
                return 0
            
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return await db_manager.db.users.count_documents({
                "first_seen": {"$gte": today_start}
            })
        except Exception as e:
            logger.error(f"Error counting new users: {e}")
            return 0
    
    async def _calculate_retention_rate(self) -> float:
        """Calculate user retention rate"""
        try:
            db_manager = get_db_manager()
            if not db_manager:
                return 0.0
            
            # Users who joined 7 days ago
            week_ago = time.time() - 604800
            new_users_week_ago = await db_manager.db.users.count_documents({
                "first_seen": {"$gte": week_ago - 86400, "$lt": week_ago}
            })
            
            # How many of those are still active
            still_active = await db_manager.db.users.count_documents({
                "first_seen": {"$gte": week_ago - 86400, "$lt": week_ago},
                "last_updated": {"$gte": week_ago}
            })
            
            return still_active / new_users_week_ago if new_users_week_ago > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating retention rate: {e}")
            return 0.0
    
    async def _calculate_economic_activity(self) -> float:
        """Calculate economic activity score"""
        try:
            db_manager = get_db_manager()
            if not db_manager:
                return 0.0
            
            # Count transactions in last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            transaction_count = await db_manager.db.transactions.count_documents({
                "timestamp": {"$gte": yesterday}
            })
            
            # Get total users
            total_users = await db_manager.db.users.count_documents({})
            
            # Calculate activity ratio
            return min(transaction_count / max(total_users, 1), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating economic activity: {e}")
            return 0.0
    
    async def _calculate_command_success_rate(self) -> float:
        """Calculate overall command success rate"""
        if not self.performance_metrics:
            return 1.0
        
        successful = sum(1 for metric in self.performance_metrics if metric["success"])
        total = len(self.performance_metrics)
        
        return successful / total if total > 0 else 1.0
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.performance_metrics:
            return 0.0
        
        total_time = sum(metric["duration"] for metric in self.performance_metrics)
        return total_time / len(self.performance_metrics)
    
    def _calculate_global_avg_session_length(self) -> float:
        """Calculate global average session length"""
        all_session_lengths = []
        
        for user_activities in self.user_activity.values():
            session_length = self._calculate_avg_session_length(user_activities)
            if session_length > 0:
                all_session_lengths.append(session_length)
        
        return sum(all_session_lengths) / len(all_session_lengths) if all_session_lengths else 0
    
    def _get_peak_activity_hours(self, activities: List[Dict[str, Any]]) -> List[int]:
        """Get peak activity hours globally"""
        hour_counts = defaultdict(int)
        
        for activity in activities:
            hour = datetime.fromtimestamp(activity["timestamp"]).hour
            hour_counts[hour] += 1
        
        return sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)[:3]
    
    async def _calculate_global_engagement_score(self) -> float:
        """Calculate global user engagement score"""
        if not self.user_activity:
            return 0.0
        
        engagement_levels = [self._calculate_engagement_level(user_id) for user_id in self.user_activity.keys()]
        
        score_map = {
            "very_high": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "very_low": 0.2
        }
        
        scores = [score_map.get(level, 0) for level in engagement_levels]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_most_common_errors(self) -> Dict[str, int]:
        """Get most common error types"""
        error_types = [error["error_type"] for error in self.error_tracking]
        return dict(Counter(error_types).most_common(5))
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if not self.performance_metrics:
            return 0.0
        
        errors = sum(1 for metric in self.performance_metrics if not metric["success"])
        total = len(self.performance_metrics)
        
        return errors / total if total > 0 else 0.0
    
    async def _identify_critical_issues(self) -> List[str]:
        """Identify critical issues that need immediate attention"""
        issues = []
        
        # Check for high error rates
        error_rate = self._calculate_error_rate()
        if error_rate > 0.1:
            issues.append(f"High error rate: {error_rate:.2%}")
        
        # Check for slow response times
        avg_response = self._calculate_avg_response_time()
        if avg_response > 5.0:  # More than 5 seconds
            issues.append(f"Slow response times: {avg_response:.2f}s average")
        
        # Check for database issues
        try:
            db_manager = get_db_manager()
            if db_manager:
                health = await db_manager.health_check()
                if health.get("status") != "healthy":
                    issues.append("Database connectivity issues")
        except Exception:
            issues.append("Database connectivity issues")
        
        return issues
    
    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall system success rate"""
        return self._calculate_command_success_rate()
    
    async def _get_database_performance(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            db_manager = get_db_manager()
            if not db_manager:
                return {"status": "unavailable"}
            
            return await db_manager.health_check()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _calculate_system_health_score(self) -> float:
        """Calculate overall system health score"""
        score = 1.0
        
        # Deduct for high error rates
        error_rate = self._calculate_error_rate()
        score -= min(error_rate * 2, 0.5)  # Max 0.5 deduction
        
        # Deduct for slow response times
        avg_response = self._calculate_avg_response_time()
        if avg_response > 2.0:
            score -= min((avg_response - 2.0) / 10, 0.3)  # Max 0.3 deduction
        
        # Check database health
        try:
            db_manager = get_db_manager()
            if db_manager:
                health = await db_manager.health_check()
                if health.get("status") != "healthy":
                    score -= 0.2
        except Exception:
            score -= 0.3
        
        return max(score, 0.0)
    
    async def log_bot_startup(self):
        """Log bot startup event"""
        try:
            startup_data = {
                "event": "bot_startup",
                "timestamp": datetime.now(),
                "version": "4.0",
                "enhanced_core": True
            }
            await self.track_event("bot_startup", startup_data)
            print("📊 Bot startup logged to analytics")
        except Exception as e:
            print(f"⚠️ Failed to log bot startup: {e}")
    
    async def log_bot_shutdown(self):
        """Log bot shutdown event"""
        try:
            shutdown_data = {
                "event": "bot_shutdown",
                "timestamp": datetime.now(),
                "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
            }
            await self.track_event("bot_shutdown", shutdown_data)
            print("📊 Bot shutdown logged to analytics")
        except Exception as e:
            print(f"⚠️ Failed to log bot shutdown: {e}")
    
    async def log_member_join(self, member):
        """Log member join event"""
        try:
            join_data = {
                "event": "member_join",
                "user_id": member.id,
                "guild_id": member.guild.id,
                "timestamp": datetime.now()
            }
            await self.track_event("member_join", join_data)
        except Exception as e:
            print(f"⚠️ Failed to log member join: {e}")
    
    async def log_member_leave(self, member):
        """Log member leave event"""
        try:
            leave_data = {
                "event": "member_leave",
                "user_id": member.id,
                "guild_id": member.guild.id,
                "timestamp": datetime.now()
            }
            await self.track_event("member_leave", leave_data)
        except Exception as e:
            print(f"⚠️ Failed to log member leave: {e}")

# Global analytics instance
analytics = BotAnalytics()

def get_analytics() -> BotAnalytics:
    """Get the global analytics instance"""
    return analytics