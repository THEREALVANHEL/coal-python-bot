# Permission system for Discord bot
# Provides role-based access control and permission checking

import discord
from typing import List, Union, Optional
from functools import wraps

# Default permission levels
PERMISSION_LEVELS = {
    "owner": 5,
    "admin": 4,
    "moderator": 3,
    "helper": 2,
    "member": 1,
    "everyone": 0
}

# Default role mappings (can be customized per server)
DEFAULT_ROLE_PERMISSIONS = {
    "owner": ["Owner", "Bot Owner"],
    "admin": ["Admin", "Administrator", "Server Owner"],
    "moderator": ["Moderator", "Mod", "Staff"],
    "helper": ["Helper", "Support", "Assistant"],
    "member": ["Member", "Verified"],
    "everyone": ["@everyone"]
}

def has_permission(required_level: Union[str, int] = "member"):
    """
    Decorator to check if user has required permission level
    
    Args:
        required_level: Permission level required (string or int)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            if not check_permissions(interaction.user, interaction.guild, required_level):
                await interaction.response.send_message(
                    "❌ You don't have permission to use this command!", 
                    ephemeral=True
                )
                return
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator

def check_permissions(user: discord.Member, guild: discord.Guild, required_level: Union[str, int]) -> bool:
    """
    Check if user has required permission level
    
    Args:
        user: Discord member to check
        guild: Discord guild context
        required_level: Required permission level
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user or not guild:
        return False
    
    # Convert string level to int
    if isinstance(required_level, str):
        required_level = PERMISSION_LEVELS.get(required_level.lower(), 1)
    
    # Check if user is bot owner (highest permission)
    if user.id in [123456789]:  # Replace with actual bot owner IDs
        return True
    
    # Check if user is guild owner
    if user.id == guild.owner_id:
        return True
    
    # Check if user has administrator permission
    if user.guild_permissions.administrator:
        return True
    
    # Check user's roles against permission mappings
    user_level = get_user_permission_level(user, guild)
    return user_level >= required_level

def get_user_permission_level(user: discord.Member, guild: discord.Guild) -> int:
    """
    Get user's permission level based on their roles
    
    Args:
        user: Discord member
        guild: Discord guild
        
    Returns:
        int: User's permission level
    """
    if not user or not guild:
        return 0
    
    # Check if user is bot owner
    if user.id in [123456789]:  # Replace with actual bot owner IDs
        return PERMISSION_LEVELS["owner"]
    
    # Check if user is guild owner
    if user.id == guild.owner_id:
        return PERMISSION_LEVELS["admin"]
    
    # Check if user has administrator permission
    if user.guild_permissions.administrator:
        return PERMISSION_LEVELS["admin"]
    
    # Check user's roles
    highest_level = PERMISSION_LEVELS["everyone"]
    
    for role in user.roles:
        role_name = role.name
        
        # Check each permission level
        for level_name, level_value in PERMISSION_LEVELS.items():
            role_names = DEFAULT_ROLE_PERMISSIONS.get(level_name, [])
            if role_name in role_names or role_name.lower() in [r.lower() for r in role_names]:
                highest_level = max(highest_level, level_value)
    
    return highest_level

def is_owner(user_id: int) -> bool:
    """Check if user is bot owner"""
    return user_id in [123456789]  # Replace with actual bot owner IDs

def is_admin(user: discord.Member, guild: discord.Guild) -> bool:
    """Check if user is admin"""
    return check_permissions(user, guild, "admin")

def is_moderator(user: discord.Member, guild: discord.Guild) -> bool:
    """Check if user is moderator or higher"""
    return check_permissions(user, guild, "moderator")

def is_helper(user: discord.Member, guild: discord.Guild) -> bool:
    """Check if user is helper or higher"""
    return check_permissions(user, guild, "helper")

# Legacy compatibility functions
def has_admin_role(user: discord.Member) -> bool:
    """Legacy function for admin role checking"""
    if not user or not user.guild:
        return False
    return is_admin(user, user.guild)

def has_mod_role(user: discord.Member) -> bool:
    """Legacy function for moderator role checking"""
    if not user or not user.guild:
        return False
    return is_moderator(user, user.guild)

def check_role_permissions(user: discord.Member, required_roles: List[str]) -> bool:
    """
    Check if user has any of the required roles
    
    Args:
        user: Discord member
        required_roles: List of role names to check for
        
    Returns:
        bool: True if user has any required role
    """
    if not user or not user.roles:
        return False
    
    user_role_names = [role.name.lower() for role in user.roles]
    required_roles_lower = [role.lower() for role in required_roles]
    
    return any(role in user_role_names for role in required_roles_lower)

# Permission checking decorators for different levels
def owner_only(func):
    """Decorator for owner-only commands"""
    return has_permission("owner")(func)

def admin_only(func):
    """Decorator for admin-only commands"""
    return has_permission("admin")(func)

def moderator_only(func):
    """Decorator for moderator+ commands"""
    return has_permission("moderator")(func)

def helper_only(func):
    """Decorator for helper+ commands"""
    return has_permission("helper")(func)

def has_special_permissions(user: discord.Member, guild: discord.Guild) -> bool:
    """
    Check if user has special permissions (admin or higher)
    Legacy function for compatibility with existing cogs
    """
    return check_permissions(user, guild, "admin")

def has_manage_permissions(user: discord.Member) -> bool:
    """Check if user has manage permissions"""
    if not user or not user.guild:
        return False
    return user.guild_permissions.manage_guild or is_admin(user, user.guild)

def has_kick_permissions(user: discord.Member) -> bool:
    """Check if user has kick permissions"""
    if not user or not user.guild:
        return False
    return user.guild_permissions.kick_members or is_moderator(user, user.guild)

def has_ban_permissions(user: discord.Member) -> bool:
    """Check if user has ban permissions"""
    if not user or not user.guild:
        return False
    return user.guild_permissions.ban_members or is_moderator(user, user.guild)