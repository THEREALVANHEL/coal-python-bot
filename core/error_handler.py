import discord
from discord.ext import commands
import traceback
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .analytics import get_analytics

logger = logging.getLogger(__name__)

class BotErrorHandler:
    """Centralized error handling system with user-friendly messages"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.error_log = []
        self.error_count = {}
        self.analytics = get_analytics()
        
        # Error message templates
        self.error_messages = {
            commands.CommandOnCooldown: "⏰ **Slow down!** This command is on cooldown. Try again in {retry_after:.1f} seconds.",
            commands.MissingPermissions: "❌ **Permission Denied** - You don't have the required permissions to use this command.",
            commands.BotMissingPermissions: "🤖 **Bot Missing Permissions** - I don't have the necessary permissions to execute this command.",
            commands.MissingRequiredArgument: "📝 **Missing Argument** - Please provide all required arguments for this command.",
            commands.BadArgument: "❌ **Invalid Argument** - Please check your input and try again.",
            commands.CommandNotFound: None,  # Ignore command not found errors
            commands.DisabledCommand: "🚫 **Command Disabled** - This command is currently disabled.",
            commands.NoPrivateMessage: "🏠 **Server Only** - This command can only be used in a server.",
            commands.PrivateMessageOnly: "📨 **DM Only** - This command can only be used in direct messages.",
            discord.HTTPException: "🌐 **Connection Error** - There was a problem communicating with Discord. Please try again.",
            discord.Forbidden: "🚫 **Access Denied** - I don't have permission to perform this action.",
            discord.NotFound: "❓ **Not Found** - The requested resource could not be found.",
            TimeoutError: "⏱️ **Timeout** - The operation took too long to complete. Please try again.",
            ValueError: "📊 **Invalid Value** - Please check your input values and try again.",
            KeyError: "🔑 **Data Error** - Some required data is missing. Please try again.",
        }
    
    async def handle_command_error(self, ctx: commands.Context, error: Exception) -> bool:
        """Handle command errors with detailed logging and user feedback"""
        
        # Generate unique error ID
        error_id = str(uuid.uuid4())[:8]
        
        # Log the error
        await self._log_error(error_id, ctx, error)
        
        # Track error for analytics
        await self.analytics.track_error(
            error_type=type(error).__name__,
            command=ctx.command.name if ctx.command else "Unknown",
            user_id=ctx.author.id,
            error_details=str(error)
        )
        
        # Get user-friendly error message
        message = await self._get_error_message(error, error_id)
        
        if message:
            try:
                # Create error embed
                embed = await self._create_error_embed(error, message, error_id, ctx)
                await ctx.send(embed=embed)
                return True
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
                try:
                    # Fallback to simple message
                    await ctx.send(f"❌ An error occurred. Error ID: `{error_id}`")
                except Exception:
                    pass  # If we can't even send a simple message, give up
        
        return False
    
    async def handle_interaction_error(self, interaction: discord.Interaction, error: Exception) -> bool:
        """Handle slash command interaction errors"""
        
        error_id = str(uuid.uuid4())[:8]
        
        # Log the error
        await self._log_interaction_error(error_id, interaction, error)
        
        # Track error for analytics
        await self.analytics.track_error(
            error_type=type(error).__name__,
            command=interaction.command.name if interaction.command else "Unknown",
            user_id=interaction.user.id,
            error_details=str(error)
        )
        
        # Get user-friendly error message
        message = await self._get_error_message(error, error_id)
        
        if message:
            try:
                embed = await self._create_interaction_error_embed(error, message, error_id, interaction)
                
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return True
            except Exception as send_error:
                logger.error(f"Failed to send interaction error message: {send_error}")
                try:
                    # Fallback
                    if interaction.response.is_done():
                        await interaction.followup.send(f"❌ An error occurred. Error ID: `{error_id}`", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"❌ An error occurred. Error ID: `{error_id}`", ephemeral=True)
                except Exception:
                    pass
        
        return False
    
    async def handle_global_error(self, event: str, *args, **kwargs) -> None:
        """Handle global bot errors"""
        error_id = str(uuid.uuid4())[:8]
        
        error_data = {
            "id": error_id,
            "event": event,
            "args": str(args)[:500],  # Limit length
            "kwargs": str(kwargs)[:500],
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now()
        }
        
        self.error_log.append(error_data)
        logger.error(f"Global error in {event}: {error_data['traceback']}")
        
        # Track for analytics
        await self.analytics.track_error(
            error_type="GlobalError",
            command=event,
            user_id=0,  # System error
            error_details=error_data['traceback']
        )
    
    async def _log_error(self, error_id: str, ctx: commands.Context, error: Exception):
        """Log command error with full context"""
        error_data = {
            "id": error_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "command": ctx.command.name if ctx.command else "Unknown",
            "user_id": ctx.author.id,
            "user_name": str(ctx.author),
            "guild_id": ctx.guild.id if ctx.guild else None,
            "guild_name": ctx.guild.name if ctx.guild else "DM",
            "channel_id": ctx.channel.id,
            "message_content": ctx.message.content[:200],  # First 200 chars
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now()
        }
        
        self.error_log.append(error_data)
        
        # Keep only last 1000 errors
        if len(self.error_log) > 1000:
            self.error_log = self.error_log[-1000:]
        
        # Count error frequency
        error_key = f"{type(error).__name__}_{ctx.command.name if ctx.command else 'Unknown'}"
        self.error_count[error_key] = self.error_count.get(error_key, 0) + 1
        
        logger.error(f"Command error {error_id}: {error_data['error_type']} in {error_data['command']} - {str(error)}")
    
    async def _log_interaction_error(self, error_id: str, interaction: discord.Interaction, error: Exception):
        """Log interaction error with full context"""
        error_data = {
            "id": error_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "command": interaction.command.name if interaction.command else "Unknown",
            "user_id": interaction.user.id,
            "user_name": str(interaction.user),
            "guild_id": interaction.guild.id if interaction.guild else None,
            "guild_name": interaction.guild.name if interaction.guild else "DM",
            "channel_id": interaction.channel.id if interaction.channel else None,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now()
        }
        
        self.error_log.append(error_data)
        
        # Count error frequency
        error_key = f"{type(error).__name__}_{interaction.command.name if interaction.command else 'Unknown'}"
        self.error_count[error_key] = self.error_count.get(error_key, 0) + 1
        
        logger.error(f"Interaction error {error_id}: {error_data['error_type']} in {error_data['command']} - {str(error)}")
    
    async def _get_error_message(self, error: Exception, error_id: str) -> Optional[str]:
        """Get user-friendly error message"""
        error_type = type(error)
        
        if error_type in self.error_messages:
            template = self.error_messages[error_type]
            if template is None:
                return None  # Don't show message for this error type
            
            # Format template with error attributes
            try:
                if hasattr(error, 'retry_after'):
                    return template.format(retry_after=error.retry_after)
                elif hasattr(error, 'missing_perms'):
                    return template.format(missing_perms=', '.join(error.missing_perms))
                else:
                    return template
            except (KeyError, AttributeError):
                return template
        
        # Default message for unknown errors
        return f"❌ **Unexpected Error** - Something went wrong. Error ID: `{error_id}`"
    
    async def _create_error_embed(self, error: Exception, message: str, error_id: str, ctx: commands.Context) -> discord.Embed:
        """Create detailed error embed for commands"""
        embed = discord.Embed(
            title="⚠️ Command Error",
            description=message,
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🔍 Error Details",
            value=f"**Error ID:** `{error_id}`\n**Command:** `{ctx.command.name if ctx.command else 'Unknown'}`",
            inline=False
        )
        
        # Add helpful tips based on error type
        tips = self._get_error_tips(error, ctx)
        if tips:
            embed.add_field(
                name="💡 Helpful Tips",
                value=tips,
                inline=False
            )
        
        embed.set_footer(text="If this error persists, please report it to the bot developers")
        
        return embed
    
    async def _create_interaction_error_embed(self, error: Exception, message: str, error_id: str, interaction: discord.Interaction) -> discord.Embed:
        """Create detailed error embed for interactions"""
        embed = discord.Embed(
            title="⚠️ Command Error",
            description=message,
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🔍 Error Details",
            value=f"**Error ID:** `{error_id}`\n**Command:** `{interaction.command.name if interaction.command else 'Unknown'}`",
            inline=False
        )
        
        # Add helpful tips
        tips = self._get_interaction_error_tips(error, interaction)
        if tips:
            embed.add_field(
                name="💡 Helpful Tips",
                value=tips,
                inline=False
            )
        
        embed.set_footer(text="If this error persists, please report it to the bot developers")
        
        return embed
    
    def _get_error_tips(self, error: Exception, ctx: commands.Context) -> Optional[str]:
        """Get helpful tips based on error type"""
        error_type = type(error)
        
        tips = {
            commands.CommandOnCooldown: "• Cooldowns prevent spam and ensure fair usage\n• Different commands have different cooldown periods",
            commands.MissingPermissions: "• Check if you have the required role or permissions\n• Contact a server administrator if you think this is wrong",
            commands.BotMissingPermissions: "• The bot needs specific permissions to work properly\n• Ask a server administrator to check bot permissions",
            commands.MissingRequiredArgument: f"• Use `{ctx.prefix}help {ctx.command.name if ctx.command else ''}` to see the correct usage\n• Make sure to provide all required parameters",
            commands.BadArgument: "• Check that numbers are valid and within expected ranges\n• Ensure user mentions and channel references are correct",
            discord.HTTPException: "• This is usually a temporary Discord issue\n• Try again in a few moments",
            discord.Forbidden: "• The bot may need additional permissions\n• Check if the action is allowed in this channel",
            TimeoutError: "• The command took too long to process\n• Try again with simpler parameters",
        }
        
        return tips.get(error_type)
    
    def _get_interaction_error_tips(self, error: Exception, interaction: discord.Interaction) -> Optional[str]:
        """Get helpful tips for interaction errors"""
        # Similar to _get_error_tips but for slash commands
        return self._get_error_tips(error, None)  # Reuse the same tips
    
    async def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for debugging"""
        current_time = datetime.now()
        recent_errors = [
            error for error in self.error_log
            if (current_time - error['timestamp']).total_seconds() < 86400  # Last 24 hours
        ]
        
        return {
            "total_errors": len(self.error_log),
            "errors_24h": len(recent_errors),
            "most_common_errors": dict(sorted(self.error_count.items(), key=lambda x: x[1], reverse=True)[:10]),
            "error_rate": len(recent_errors) / max(1, len(self.error_log)) * 100,
            "recent_critical_errors": [
                error for error in recent_errors[-10:]
                if error['error_type'] in ['DatabaseError', 'ConnectionError', 'TimeoutError']
            ]
        }
    
    async def clear_old_errors(self, days: int = 7):
        """Clear errors older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        self.error_log = [
            error for error in self.error_log
            if error['timestamp'] > cutoff_time
        ]
        
        logger.info(f"Cleared errors older than {days} days")
    
    def get_error_by_id(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Get specific error by ID"""
        for error in self.error_log:
            if error['id'] == error_id:
                return error
        return None

# Global error handler instance
error_handler = None

def initialize_error_handler(bot: commands.Bot) -> BotErrorHandler:
    """Initialize the global error handler"""
    global error_handler
    error_handler = BotErrorHandler(bot)
    return error_handler

def get_error_handler() -> Optional[BotErrorHandler]:
    """Get the global error handler instance"""
    return error_handler