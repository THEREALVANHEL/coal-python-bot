import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    mongodb_uri: str
    database_name: str = "coal_bot"
    connection_pool_size: int = 50
    cache_ttl: int = 300  # 5 minutes
    backup_interval: int = 3600  # 1 hour
    max_backup_age: int = 604800  # 7 days

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    enable_rate_limiting: bool = True
    enable_fraud_detection: bool = True
    max_login_attempts: int = 5
    session_timeout: int = 3600  # 1 hour
    enable_2fa: bool = False
    
    # Rate limit configurations
    rate_limits: Dict[str, Dict[str, int]] = None
    
    def __post_init__(self):
        if self.rate_limits is None:
            self.rate_limits = {
                "default": {"max_requests": 10, "window": 60},
                "work": {"max_requests": 1, "window": 3600},
                "daily": {"max_requests": 1, "window": 86400},
                "trivia": {"max_requests": 5, "window": 60},
                "slots": {"max_requests": 10, "window": 60},
                "transfer": {"max_requests": 3, "window": 300},
                "buy": {"max_requests": 5, "window": 60},
            }

@dataclass
class EconomyConfig:
    """Economy system configuration"""
    starting_coins: int = 100
    max_bank_balance: int = 1000000
    max_savings_balance: int = 5000000
    savings_interest_rate: float = 0.02  # 2% daily
    transfer_fee_rate: float = 0.01  # 1% of transfer amount
    min_transfer_fee: int = 1
    max_transfer_fee: int = 1000
    
    # Work system
    work_cooldown: int = 3600  # 1 hour
    daily_cooldown: int = 86400  # 24 hours
    
    # Shop categories and items
    enable_shop: bool = True
    enable_banking: bool = True
    enable_stock_market: bool = True

@dataclass
class GamingConfig:
    """Gaming system configuration"""
    enable_trivia: bool = True
    enable_slots: bool = True
    enable_wordchain: bool = True
    
    # Trivia settings
    trivia_rewards: Dict[str, int] = None
    trivia_cooldown: int = 60
    
    # Slots settings
    slots_min_bet: int = 10
    slots_max_bet: int = 1000
    slots_cooldown: int = 30
    
    # Word chain settings
    wordchain_cooldown: int = 30
    wordchain_timeout: int = 60
    
    def __post_init__(self):
        if self.trivia_rewards is None:
            self.trivia_rewards = {
                "easy": 1,
                "normal": 2,
                "hard": 3
            }

@dataclass
class AIConfig:
    """AI system configuration"""
    enable_ai_chat: bool = True
    enable_ai_trivia: bool = True
    enable_ai_wordchain: bool = True
    
    gemini_api_key: str = ""
    max_conversation_history: int = 20
    ai_response_timeout: int = 30
    context_window_size: int = 4000
    
    def __post_init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

@dataclass
class AnalyticsConfig:
    """Analytics system configuration"""
    enable_analytics: bool = True
    enable_performance_tracking: bool = True
    enable_user_insights: bool = True
    
    # Data retention
    analytics_retention_days: int = 30
    error_log_retention_days: int = 7
    performance_metrics_retention: int = 10000
    
    # Reporting
    daily_reports: bool = True
    weekly_reports: bool = True
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "error_rate": 0.05,  # 5%
                "response_time": 5.0,  # 5 seconds
                "database_latency": 1000.0,  # 1 second
                "memory_usage": 0.8,  # 80%
            }

@dataclass
class FeatureFlags:
    """Feature flag configuration"""
    # Core features
    enable_economy: bool = True
    enable_leveling: bool = True
    enable_pets: bool = True
    enable_stocks: bool = True
    enable_banking: bool = True
    
    # Gaming features
    enable_minigames: bool = True
    enable_trivia: bool = True
    enable_slots: bool = True
    enable_wordchain: bool = True
    
    # Social features
    enable_tickets: bool = True
    enable_moderation: bool = True
    enable_community: bool = True
    
    # Advanced features
    enable_ai_features: bool = True
    enable_analytics: bool = True
    enable_security: bool = True
    enable_notifications: bool = True
    
    # Beta features
    enable_beta_features: bool = False
    enable_experimental_ai: bool = False
    enable_advanced_banking: bool = True

class BotConfig:
    """Main bot configuration class"""
    
    def __init__(self):
        # Core settings
        self.discord_token = os.getenv("DISCORD_TOKEN")
        self.mongodb_uri = os.getenv("MONGODB_URI")
        self.guild_id = int(os.getenv("GUILD_ID", "1370009417726169250"))
        
        # Environment
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Server settings
        self.port = int(os.getenv("PORT", "10000"))
        self.host = os.getenv("HOST", "0.0.0.0")
        
        # Component configurations
        self.database = DatabaseConfig(
            mongodb_uri=self.mongodb_uri,
            connection_pool_size=int(os.getenv("DB_POOL_SIZE", "50")),
            cache_ttl=int(os.getenv("CACHE_TTL", "300"))
        )
        
        self.security = SecurityConfig(
            enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
            enable_fraud_detection=os.getenv("ENABLE_FRAUD_DETECTION", "true").lower() == "true"
        )
        
        self.economy = EconomyConfig(
            starting_coins=int(os.getenv("STARTING_COINS", "100")),
            max_bank_balance=int(os.getenv("MAX_BANK_BALANCE", "1000000")),
            savings_interest_rate=float(os.getenv("SAVINGS_INTEREST_RATE", "0.02"))
        )
        
        self.gaming = GamingConfig(
            enable_trivia=os.getenv("ENABLE_TRIVIA", "true").lower() == "true",
            enable_slots=os.getenv("ENABLE_SLOTS", "true").lower() == "true",
            enable_wordchain=os.getenv("ENABLE_WORDCHAIN", "true").lower() == "true"
        )
        
        self.ai = AIConfig(
            enable_ai_chat=os.getenv("ENABLE_AI_CHAT", "true").lower() == "true",
            enable_ai_trivia=os.getenv("ENABLE_AI_TRIVIA", "true").lower() == "true"
        )
        
        self.analytics = AnalyticsConfig(
            enable_analytics=os.getenv("ENABLE_ANALYTICS", "true").lower() == "true",
            enable_performance_tracking=os.getenv("ENABLE_PERFORMANCE_TRACKING", "true").lower() == "true"
        )
        
        self.features = FeatureFlags(
            enable_economy=os.getenv("ENABLE_ECONOMY", "true").lower() == "true",
            enable_pets=os.getenv("ENABLE_PETS", "true").lower() == "true",
            enable_ai_features=os.getenv("ENABLE_AI_FEATURES", "true").lower() == "true",
            enable_beta_features=os.getenv("ENABLE_BETA_FEATURES", "false").lower() == "true"
        )
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings"""
        if not self.discord_token:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is required")
        
        if self.features.enable_ai_features and not self.ai.gemini_api_key:
            print("⚠️  Warning: AI features enabled but GEMINI_API_KEY not provided")
        
        # Validate numeric ranges
        if self.economy.starting_coins < 0:
            raise ValueError("Starting coins cannot be negative")
        
        if self.economy.savings_interest_rate < 0 or self.economy.savings_interest_rate > 1:
            raise ValueError("Savings interest rate must be between 0 and 1")
        
        if self.database.connection_pool_size < 1:
            raise ValueError("Database connection pool size must be at least 1")
    
    def get_command_config(self, command_name: str) -> Dict[str, Any]:
        """Get configuration for a specific command"""
        command_configs = {
            "work": {
                "enabled": self.features.enable_economy,
                "cooldown": self.economy.work_cooldown,
                "rate_limit": self.security.rate_limits.get("work", {})
            },
            "daily": {
                "enabled": self.features.enable_economy,
                "cooldown": self.economy.daily_cooldown,
                "rate_limit": self.security.rate_limits.get("daily", {})
            },
            "trivia": {
                "enabled": self.features.enable_trivia and self.gaming.enable_trivia,
                "cooldown": self.gaming.trivia_cooldown,
                "rewards": self.gaming.trivia_rewards,
                "rate_limit": self.security.rate_limits.get("trivia", {})
            },
            "slots": {
                "enabled": self.features.enable_slots and self.gaming.enable_slots,
                "cooldown": self.gaming.slots_cooldown,
                "min_bet": self.gaming.slots_min_bet,
                "max_bet": self.gaming.slots_max_bet,
                "rate_limit": self.security.rate_limits.get("slots", {})
            },
            "wordchain": {
                "enabled": self.features.enable_wordchain and self.gaming.enable_wordchain,
                "cooldown": self.gaming.wordchain_cooldown,
                "timeout": self.gaming.wordchain_timeout
            },
            "talktobleky": {
                "enabled": self.features.enable_ai_features and self.ai.enable_ai_chat,
                "timeout": self.ai.ai_response_timeout,
                "max_history": self.ai.max_conversation_history
            },
            "banking": {
                "enabled": self.features.enable_banking and self.economy.enable_banking,
                "max_balance": self.economy.max_bank_balance,
                "transfer_fee_rate": self.economy.transfer_fee_rate
            },
            "stocks": {
                "enabled": self.features.enable_stocks and self.economy.enable_stock_market
            },
            "pets": {
                "enabled": self.features.enable_pets
            }
        }
        
        return command_configs.get(command_name, {"enabled": True})
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return getattr(self.features, f"enable_{feature_name}", False)
    
    def get_rate_limit_config(self, command_name: str) -> Dict[str, int]:
        """Get rate limit configuration for a command"""
        return self.security.rate_limits.get(command_name, self.security.rate_limits["default"])
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """Update configuration at runtime"""
        try:
            if hasattr(self, section):
                section_obj = getattr(self, section)
                if hasattr(section_obj, key):
                    setattr(section_obj, key, value)
                    return True
            return False
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "discord_token": "***HIDDEN***",
            "mongodb_uri": "***HIDDEN***",
            "guild_id": self.guild_id,
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "database": {
                "database_name": self.database.database_name,
                "connection_pool_size": self.database.connection_pool_size,
                "cache_ttl": self.database.cache_ttl
            },
            "security": {
                "enable_rate_limiting": self.security.enable_rate_limiting,
                "enable_fraud_detection": self.security.enable_fraud_detection,
                "rate_limits": self.security.rate_limits
            },
            "economy": {
                "starting_coins": self.economy.starting_coins,
                "max_bank_balance": self.economy.max_bank_balance,
                "savings_interest_rate": self.economy.savings_interest_rate
            },
            "gaming": {
                "enable_trivia": self.gaming.enable_trivia,
                "enable_slots": self.gaming.enable_slots,
                "trivia_rewards": self.gaming.trivia_rewards
            },
            "ai": {
                "enable_ai_chat": self.ai.enable_ai_chat,
                "gemini_api_key": "***HIDDEN***" if self.ai.gemini_api_key else "NOT_SET"
            },
            "features": {
                "enable_economy": self.features.enable_economy,
                "enable_pets": self.features.enable_pets,
                "enable_ai_features": self.features.enable_ai_features,
                "enable_beta_features": self.features.enable_beta_features
            }
        }

# Global configuration instance
config = None

def initialize_config() -> BotConfig:
    """Initialize the global configuration"""
    global config
    config = BotConfig()
    return config

def get_config() -> BotConfig:
    """Get the global configuration instance"""
    if config is None:
        return initialize_config()
    return config

# Convenience functions
def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return get_config().is_feature_enabled(feature_name)

def get_command_config(command_name: str) -> Dict[str, Any]:
    """Get configuration for a specific command"""
    return get_config().get_command_config(command_name)

def get_rate_limit_config(command_name: str) -> Dict[str, int]:
    """Get rate limit configuration for a command"""
    return get_config().get_rate_limit_config(command_name)