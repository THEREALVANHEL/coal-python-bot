import time
import hashlib
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import asyncio

logger = logging.getLogger(__name__)

class SecurityManager:
    """Enhanced security system for fraud detection and rate limiting"""
    
    def __init__(self):
        self.rate_limits = defaultdict(deque)
        self.suspicious_activity = defaultdict(list)
        self.blocked_users = set()
        self.transaction_patterns = defaultdict(list)
        self.command_patterns = defaultdict(deque)
        
        # Security thresholds
        self.rate_limit_configs = {
            "default": {"max_requests": 10, "window": 60},  # 10 per minute
            "work": {"max_requests": 1, "window": 3600},    # 1 per hour
            "daily": {"max_requests": 1, "window": 86400},  # 1 per day
            "trivia": {"max_requests": 5, "window": 60},    # 5 per minute
            "slots": {"max_requests": 10, "window": 60},    # 10 per minute
            "transfer": {"max_requests": 3, "window": 300}, # 3 per 5 minutes
            "buy": {"max_requests": 5, "window": 60},       # 5 per minute
        }
        
        self.fraud_thresholds = {
            "rapid_commands": 30,      # More than 30 commands per minute
            "large_transfer": 50000,   # Transfers over 50k coins
            "unusual_gains": 25000,    # Gaining more than 25k coins quickly
            "repeated_failures": 10,   # 10 failed attempts in a row
            "suspicious_patterns": 5   # 5 suspicious activities
        }
    
    async def check_rate_limit(self, user_id: int, command: str) -> Tuple[bool, float]:
        """Advanced rate limiting per command with user-specific tracking"""
        if user_id in self.blocked_users:
            return False, float('inf')
        
        current_time = time.time()
        config = self.rate_limit_configs.get(command, self.rate_limit_configs["default"])
        
        key = f"{user_id}_{command}"
        user_requests = self.rate_limits[key]
        
        # Clean old entries
        while user_requests and current_time - user_requests[0] > config["window"]:
            user_requests.popleft()
        
        # Check if limit exceeded
        if len(user_requests) >= config["max_requests"]:
            # Calculate time until next allowed request
            oldest_request = user_requests[0]
            time_left = config["window"] - (current_time - oldest_request)
            
            # Log potential abuse
            await self._log_rate_limit_violation(user_id, command)
            return False, time_left
        
        # Add current request
        user_requests.append(current_time)
        return True, 0
    
    async def detect_suspicious_activity(self, user_id: int, action: str, data: Dict[str, Any] = None) -> bool:
        """Comprehensive fraud detection system"""
        current_time = time.time()
        
        # Track the activity
        activity = {
            "action": action,
            "timestamp": current_time,
            "data": data or {}
        }
        
        self.suspicious_activity[user_id].append(activity)
        
        # Clean old activities (keep last 24 hours)
        self.suspicious_activity[user_id] = [
            act for act in self.suspicious_activity[user_id]
            if current_time - act["timestamp"] < 86400
        ]
        
        # Analyze patterns
        suspicious_score = 0
        recent_activities = [
            act for act in self.suspicious_activity[user_id]
            if current_time - act["timestamp"] < 3600  # Last hour
        ]
        
        # Check for rapid command usage
        if len(recent_activities) > self.fraud_thresholds["rapid_commands"]:
            suspicious_score += 3
            logger.warning(f"Rapid command usage detected for user {user_id}")
        
        # Check for large transactions
        if action == "transfer" and data and data.get("amount", 0) > self.fraud_thresholds["large_transfer"]:
            suspicious_score += 2
            logger.warning(f"Large transfer detected: {user_id} -> {data.get('amount')}")
        
        # Check for unusual gains
        if action in ["work", "daily", "trivia", "slots"] and data and data.get("gained", 0) > self.fraud_thresholds["unusual_gains"]:
            suspicious_score += 3
            logger.warning(f"Unusual gains detected for user {user_id}: {data.get('gained')}")
        
        # Check for repeated failures
        recent_failures = [
            act for act in recent_activities
            if act.get("data", {}).get("success") is False
        ]
        if len(recent_failures) > self.fraud_thresholds["repeated_failures"]:
            suspicious_score += 2
        
        # Check for bot-like behavior patterns
        if await self._detect_bot_behavior(user_id, recent_activities):
            suspicious_score += 4
        
        # Take action based on suspicious score
        if suspicious_score >= 5:
            await self._handle_suspicious_user(user_id, suspicious_score, recent_activities)
            return True
        
        return False
    
    async def verify_transaction(self, user_id: int, transaction_type: str, amount: int, target_user: int = None) -> Tuple[bool, str]:
        """Advanced transaction verification"""
        
        # Check if user is blocked
        if user_id in self.blocked_users:
            return False, "Account temporarily restricted due to suspicious activity"
        
        # Large transaction verification
        if amount > 10000:
            verification_needed = await self._requires_additional_verification(user_id, amount)
            if verification_needed:
                return False, f"Large transaction requires additional verification. Please contact support with code: {self._generate_verification_code(user_id, amount)}"
        
        # Check transaction patterns
        if await self._detect_unusual_transaction_pattern(user_id, transaction_type, amount):
            return False, "Unusual transaction pattern detected. Please try again later."
        
        # Verify target user for transfers
        if target_user and await self._is_suspicious_transfer(user_id, target_user, amount):
            return False, "Transfer blocked due to security concerns"
        
        # Log the transaction pattern
        self.transaction_patterns[user_id].append({
            "type": transaction_type,
            "amount": amount,
            "timestamp": time.time(),
            "target": target_user
        })
        
        return True, "Transaction verified"
    
    async def implement_two_factor_auth(self, user_id: int) -> str:
        """Generate 2FA code for sensitive operations"""
        code = str(uuid.uuid4())[:8].upper()
        # Store code with expiration (implement in database)
        return code
    
    async def verify_2fa_code(self, user_id: int, code: str) -> bool:
        """Verify 2FA code"""
        # Implement 2FA verification logic
        return True  # Placeholder
    
    async def get_security_report(self, user_id: int) -> Dict[str, Any]:
        """Generate security report for user"""
        current_time = time.time()
        
        recent_activities = [
            act for act in self.suspicious_activity[user_id]
            if current_time - act["timestamp"] < 86400
        ]
        
        return {
            "user_id": user_id,
            "is_blocked": user_id in self.blocked_users,
            "recent_activities": len(recent_activities),
            "suspicious_score": await self._calculate_suspicion_score(user_id),
            "last_violation": max([act["timestamp"] for act in recent_activities]) if recent_activities else None,
            "security_level": await self._get_security_level(user_id)
        }
    
    async def _log_rate_limit_violation(self, user_id: int, command: str):
        """Log rate limit violations"""
        violation = {
            "user_id": user_id,
            "command": command,
            "timestamp": time.time(),
            "type": "rate_limit_violation"
        }
        
        # Add to database logging (implement as needed)
        logger.warning(f"Rate limit violation: User {user_id}, Command {command}")
    
    async def _detect_bot_behavior(self, user_id: int, activities: List[Dict[str, Any]]) -> bool:
        """Detect bot-like behavior patterns"""
        if len(activities) < 10:
            return False
        
        # Check for perfectly timed intervals
        intervals = []
        for i in range(1, len(activities)):
            interval = activities[i]["timestamp"] - activities[i-1]["timestamp"]
            intervals.append(interval)
        
        # If more than 70% of intervals are identical, it's suspicious
        if len(set(round(interval, 1) for interval in intervals)) == 1 and len(intervals) > 5:
            return True
        
        # Check for repetitive command patterns
        command_sequence = [act["action"] for act in activities[-10:]]
        if len(set(command_sequence)) <= 2 and len(command_sequence) >= 8:
            return True
        
        return False
    
    async def _handle_suspicious_user(self, user_id: int, score: int, activities: List[Dict[str, Any]]):
        """Handle users with suspicious activity"""
        if score >= 8:
            # Temporary block
            self.blocked_users.add(user_id)
            logger.critical(f"User {user_id} temporarily blocked - suspicion score: {score}")
            
            # Auto-unblock after 1 hour
            asyncio.create_task(self._auto_unblock_user(user_id, 3600))
        
        elif score >= 5:
            # Increase rate limits
            for command in self.rate_limit_configs:
                self.rate_limit_configs[command]["max_requests"] = max(1, self.rate_limit_configs[command]["max_requests"] // 2)
            
            logger.warning(f"Increased rate limits for user {user_id} - suspicion score: {score}")
    
    async def _auto_unblock_user(self, user_id: int, delay: int):
        """Automatically unblock user after delay"""
        await asyncio.sleep(delay)
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            logger.info(f"User {user_id} automatically unblocked")
    
    async def _requires_additional_verification(self, user_id: int, amount: int) -> bool:
        """Check if transaction requires additional verification"""
        # Implement logic based on user history, amount, etc.
        return amount > 50000  # Require verification for amounts over 50k
    
    def _generate_verification_code(self, user_id: int, amount: int) -> str:
        """Generate unique verification code"""
        data = f"{user_id}_{amount}_{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12].upper()
    
    async def _detect_unusual_transaction_pattern(self, user_id: int, transaction_type: str, amount: int) -> bool:
        """Detect unusual transaction patterns"""
        recent_transactions = [
            t for t in self.transaction_patterns[user_id]
            if time.time() - t["timestamp"] < 3600  # Last hour
        ]
        
        # Check for rapid identical transactions
        identical_transactions = [
            t for t in recent_transactions
            if t["type"] == transaction_type and t["amount"] == amount
        ]
        
        if len(identical_transactions) > 5:
            return True
        
        # Check for unusual amounts
        if transaction_type == "transfer" and amount > 100000:
            return True
        
        return False
    
    async def _is_suspicious_transfer(self, sender_id: int, receiver_id: int, amount: int) -> bool:
        """Check if transfer is suspicious"""
        # Check if it's a back-and-forth transfer pattern
        recent_transfers = [
            t for t in self.transaction_patterns[receiver_id]
            if t["type"] == "transfer" and t["target"] == sender_id and time.time() - t["timestamp"] < 300
        ]
        
        if recent_transfers and amount > 10000:
            return True
        
        return False
    
    async def _calculate_suspicion_score(self, user_id: int) -> int:
        """Calculate overall suspicion score for user"""
        activities = self.suspicious_activity[user_id]
        current_time = time.time()
        
        score = 0
        recent_activities = [
            act for act in activities
            if current_time - act["timestamp"] < 86400
        ]
        
        # Base score on activity volume
        if len(recent_activities) > 50:
            score += 3
        elif len(recent_activities) > 30:
            score += 2
        elif len(recent_activities) > 20:
            score += 1
        
        # Add score for failed attempts
        failed_attempts = sum(1 for act in recent_activities if act.get("data", {}).get("success") is False)
        score += min(failed_attempts // 5, 3)
        
        return min(score, 10)  # Cap at 10
    
    async def _get_security_level(self, user_id: int) -> str:
        """Get user's security level"""
        score = await self._calculate_suspicion_score(user_id)
        
        if user_id in self.blocked_users:
            return "BLOCKED"
        elif score >= 7:
            return "HIGH_RISK"
        elif score >= 4:
            return "MEDIUM_RISK"
        elif score >= 2:
            return "LOW_RISK"
        else:
            return "TRUSTED"
    
    async def cleanup_old_data(self):
        """Clean up old security data"""
        current_time = time.time()
        cutoff_time = current_time - 86400  # 24 hours
        
        # Clean suspicious activities
        for user_id in list(self.suspicious_activity.keys()):
            self.suspicious_activity[user_id] = [
                act for act in self.suspicious_activity[user_id]
                if act["timestamp"] > cutoff_time
            ]
            if not self.suspicious_activity[user_id]:
                del self.suspicious_activity[user_id]
        
        # Clean transaction patterns
        for user_id in list(self.transaction_patterns.keys()):
            self.transaction_patterns[user_id] = [
                t for t in self.transaction_patterns[user_id]
                if t["timestamp"] > cutoff_time
            ]
            if not self.transaction_patterns[user_id]:
                del self.transaction_patterns[user_id]
        
        # Clean rate limits
        for key in list(self.rate_limits.keys()):
            requests = self.rate_limits[key]
            while requests and current_time - requests[0] > 3600:  # 1 hour
                requests.popleft()
            if not requests:
                del self.rate_limits[key]

# Global security manager instance
security_manager = SecurityManager()

def get_security_manager() -> SecurityManager:
    """Get the global security manager instance"""
    return security_manager