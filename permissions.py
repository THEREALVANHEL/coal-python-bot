"""
Custom permission system for Coal Python Bot
Allows special roles to bypass normal permission requirements
"""

import discord
from discord.ext import commands
import functools

# Special role that can use any command
SPECIAL_ADMIN_ROLE_ID = 1376574861333495910

def has_special_permissions(interaction: discord.Interaction) -> bool:
    """Check if user has the special admin role"""
    if not interaction.user.roles:
        return False
    return any(role.id == SPECIAL_ADMIN_ROLE_ID for role in interaction.user.roles)

def special_role_or_permission(**permissions):
    """
    Decorator that allows special role OR normal permissions
    Usage: @special_role_or_permission(administrator=True)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
            # Check if user has special role first
            if has_special_permissions(interaction):
                return await func(self, interaction, *args, **kwargs)
            
            # Check normal permissions
            user_permissions = interaction.user.guild_permissions
            for perm_name, required in permissions.items():
                if required and not getattr(user_permissions, perm_name, False):
                    await interaction.response.send_message(
                        f"❌ You need the `{perm_name.replace('_', ' ').title()}` permission or the special admin role to use this command!",
                        ephemeral=True
                    )
                    return
            
            return await func(self, interaction, *args, **kwargs)
        return wrapper
    return decorator

def special_role_check():
    """Simple check function for special role"""
    def predicate(interaction: discord.Interaction):
        return has_special_permissions(interaction)
    return commands.check(predicate)