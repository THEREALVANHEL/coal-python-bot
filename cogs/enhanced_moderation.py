import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os, sys
import asyncio

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

class SimpleModeration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    async def cog_load(self):
        print("[Simple Moderation] Loaded with essential logging only.")

    async def get_mod_log_channel(self, guild):
        """Get the moderation log channel for the guild"""
        modlog_channel_id = db.get_guild_setting(guild.id, "modlog_channel", None)
        if modlog_channel_id:
            return guild.get_channel(modlog_channel_id)
        return None

    async def log_simple_event(self, guild, title, description, color):
        """Simple logging with clean embeds"""
        try:
            channel = await self.get_mod_log_channel(guild)
            if not channel:
                return

            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
                timestamp=datetime.now()
            )
            embed.set_footer(text="Simple Mod Log")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error in simple logging: {e}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log message deletions"""
        if message.author.bot:
            return
            
        try:
            # Track staff activity for work requirements
            if any(role.name.lower() in ["lead moderator", "moderator", "overseer", "forgotten one"] for role in message.author.roles):
                db.update_staff_activity(message.author.id, "message_delete")
            
            content = message.content[:500] + "..." if len(message.content) > 500 else message.content
            if not content:
                content = "*No text content*"
            
            description = f"**User:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Content:** {content}"
            
            await self.log_simple_event(
                message.guild,
                "🗑️ Message Deleted",
                description,
                0xff0000
            )
            
        except Exception as e:
            print(f"Error logging message deletion: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Log message edits"""
        if before.author.bot or before.content == after.content:
            return
            
        try:
            # Track staff activity for work requirements
            if any(role.name.lower() in ["lead moderator", "moderator", "overseer", "forgotten one"] for role in after.author.roles):
                db.update_staff_activity(after.author.id, "message_edit")
            
            before_content = before.content[:300] + "..." if len(before.content) > 300 else before.content
            after_content = after.content[:300] + "..." if len(after.content) > 300 else after.content
            
            if not before_content:
                before_content = "*No text content*"
            if not after_content:
                after_content = "*No text content*"
            
            description = f"**User:** {after.author.mention}\n**Channel:** {after.channel.mention}\n**Before:** {before_content}\n**After:** {after_content}\n**[Jump to Message]({after.jump_url})**"
            
            await self.log_simple_event(
                after.guild,
                "✏️ Message Edited",
                description,
                0xffa500
            )
            
        except Exception as e:
            print(f"Error logging message edit: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creation"""
        try:
            description = f"**Channel:** {channel.mention}\n**Name:** {channel.name}\n**Type:** {str(channel.type).title()}"
            if channel.category:
                description += f"\n**Category:** {channel.category.name}"
            
            await self.log_simple_event(
                channel.guild,
                "📁 Channel Created",
                description,
                0x00ff00
            )
            
        except Exception as e:
            print(f"Error logging channel creation: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletion"""
        try:
            description = f"**Name:** {channel.name}\n**Type:** {str(channel.type).title()}"
            if channel.category:
                description += f"\n**Category:** {channel.category.name}"
            
            await self.log_simple_event(
                channel.guild,
                "🗑️ Channel Deleted",
                description,
                0xff0000
            )
            
        except Exception as e:
            print(f"Error logging channel deletion: {e}")

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """Log emoji creation and deletion"""
        try:
            # Find new emojis (created)
            new_emojis = [emoji for emoji in after if emoji not in before]
            for emoji in new_emojis:
                description = f"**Emoji:** {emoji} (:{emoji.name}:)\n**Name:** {emoji.name}\n**ID:** {emoji.id}"
                
                await self.log_simple_event(
                    guild,
                    "😀 Emoji Created",
                    description,
                    0x00ff00
                )
            
            # Find deleted emojis
            deleted_emojis = [emoji for emoji in before if emoji not in after]
            for emoji in deleted_emojis:
                description = f"**Name:** {emoji.name}\n**ID:** {emoji.id}"
                
                await self.log_simple_event(
                    guild,
                    "🗑️ Emoji Deleted",
                    description,
                    0xff0000
                )
            
        except Exception as e:
            print(f"Error logging emoji changes: {e}")

    @app_commands.command(name="set-modlog", description="Set the moderation log channel")
    @app_commands.describe(channel="Channel to use for moderation logs")
    @app_commands.default_permissions(administrator=True)
    async def set_modlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the moderation log channel"""
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only administrators can set the modlog channel.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check bot permissions
        permissions = channel.permissions_for(interaction.guild.me)
        if not permissions.send_messages or not permissions.embed_links:
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description=f"I need **Send Messages** and **Embed Links** permissions in {channel.mention}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Set the channel
        db.set_guild_setting(interaction.guild.id, "modlog_channel", channel.id)
        
        embed = discord.Embed(
            title="✅ Modlog Channel Set",
            description=f"Moderation logs will now be sent to {channel.mention}",
            color=0x00ff00
        )
        embed.add_field(
            name="📋 What gets logged:",
            value="• Message deletions\n• Message edits\n• Channel creation/deletion\n• Emoji creation/deletion",
            inline=False
        )
        embed.set_footer(text="Simple and clean logging")
        
        await interaction.response.send_message(embed=embed)
        
        # Send test message
        test_embed = discord.Embed(
            title="🔧 Modlog Setup Complete",
            description="This channel is now receiving moderation logs. All logs will be simple and clean.",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        test_embed.set_footer(text="Simple Mod Log")
        await channel.send(embed=test_embed)

    @app_commands.command(name="staff-activity", description="Check staff activity for work requirements")
    @app_commands.describe(user="Staff member to check (optional)")
    async def staff_activity(self, interaction: discord.Interaction, user: discord.Member = None):
        """Check staff activity for work requirements"""
        
        # Check if user has permission
        is_staff = (
            interaction.user.guild_permissions.administrator or
            has_special_permissions(interaction.user) or
            any(role.name.lower() in ["lead moderator", "moderator", "overseer", "forgotten one"] for role in interaction.user.roles)
        )
        
        if not is_staff:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only staff can check activity requirements.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        target_user = user or interaction.user
        
        # Get activity summary
        summary = db.get_staff_activity_summary(target_user.id, 7)
        
        embed = discord.Embed(
            title="📊 Staff Activity Report",
            description=f"**Staff Member:** {target_user.mention}",
            color=0x00ff00 if summary['meets_requirements'] else 0xff0000
        )
        
        embed.add_field(
            name="📈 Weekly Activity",
            value=f"**Days Active:** {summary['days_active']}/7\n**Required:** {summary['required_days']} days\n**Status:** {'✅ Meets Requirements' if summary['meets_requirements'] else '❌ Below Requirements'}",
            inline=False
        )
        
        if summary['last_activity']:
            embed.add_field(
                name="⏰ Last Activity",
                value=f"<t:{int(summary['last_activity'].timestamp())}:R>",
                inline=True
            )
        
        embed.add_field(
            name="💡 Work Requirements",
            value="Staff must be active at least **3 days per week** to maintain their position.",
            inline=False
        )
        
        if not summary['meets_requirements']:
            embed.add_field(
                name="⚠️ Warning",
                value="This staff member may be subject to demotion if activity doesn't improve.",
                inline=False
            )
        
        embed.set_footer(text="Activity tracking helps maintain an active staff team")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SimpleModeration(bot))