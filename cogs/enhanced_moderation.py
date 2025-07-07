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

# Role ID for "Forgotten one" role
FORGOTTEN_ONE_ROLE_ID = None  # Will need to be set from user

class EnhancedModeration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    async def cog_load(self):
        print("[Enhanced Moderation] Loaded successfully with comprehensive A-Z logging.")

    async def get_mod_log_channel(self, guild):
        """Get the moderation log channel for the guild"""
        modlog_channel_id = db.get_guild_setting(guild.id, "modlog_channel", None)
        if modlog_channel_id:
            return guild.get_channel(modlog_channel_id)
        return None

    async def log_comprehensive_event(self, guild, event_type, data):
        """Enhanced logging with comprehensive details"""
        try:
            channel = await self.get_mod_log_channel(guild)
            if not channel:
                return

            embed = discord.Embed(
                title=f"🔍 {event_type.replace('_', ' ').title()}",
                color=data.get("color", 0x7289da),
                timestamp=datetime.now()
            )
            
            # Add description
            if "description" in data:
                embed.description = data["description"][:4096]  # Discord limit
            
            # Add user info if available
            if "user" in data:
                user = data["user"]
                embed.set_author(name=f"{user.display_name} ({user.name})", icon_url=user.display_avatar.url)
                embed.add_field(name="👤 User ID", value=f"`{user.id}`", inline=True)
                embed.add_field(name="📅 Account Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)
                embed.add_field(name="🏷️ Username", value=f"`{user.name}#{user.discriminator}`", inline=True)
            
            # Add channel info if available
            if "channel" in data:
                channel_obj = data["channel"]
                embed.add_field(name="📍 Channel", value=f"{channel_obj.mention} (`{channel_obj.id}`)", inline=True)
            
            # Add additional fields
            for key, value in data.items():
                if key not in ["description", "user", "channel", "color", "embed_fields"] and value:
                    if len(str(value)) <= 1024:
                        embed.add_field(name=key.replace('_', ' ').title(), value=str(value), inline=True)
            
            # Add custom embed fields
            if "embed_fields" in data:
                for field in data["embed_fields"]:
                    embed.add_field(name=field["name"], value=field["value"], inline=field.get("inline", True))
            
            # Add footer
            embed.set_footer(text=f"Enhanced Moderation • {event_type}")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error in comprehensive logging: {e}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Enhanced message deletion logging"""
        if message.author.bot:
            return
            
        try:
            embed_fields = []
            
            # Message content
            if message.content:
                content = message.content[:1500] + ("..." if len(message.content) > 1500 else "")
                embed_fields.append({"name": "📝 Message Content", "value": f"```{content}```", "inline": False})
            
            # Attachments
            if message.attachments:
                attachment_info = []
                for attachment in message.attachments:
                    attachment_info.append(f"📎 **{attachment.filename}** ({attachment.size} bytes)")
                    if attachment.url:
                        attachment_info.append(f"🔗 [Original URL]({attachment.url})")
                embed_fields.append({"name": "📎 Attachments", "value": "\n".join(attachment_info[:10]), "inline": False})
            
            # Embeds
            if message.embeds:
                embed_info = []
                for i, embed in enumerate(message.embeds[:3]):
                    embed_info.append(f"📋 **Embed {i+1}:** {embed.title or 'No title'}")
                    if embed.description:
                        embed_info.append(f"Description: {embed.description[:100]}...")
                embed_fields.append({"name": "📋 Embeds", "value": "\n".join(embed_info), "inline": False})
            
            # Reactions
            if message.reactions:
                reaction_info = []
                for reaction in message.reactions:
                    reaction_info.append(f"{reaction.emoji} x{reaction.count}")
                embed_fields.append({"name": "😀 Reactions", "value": " • ".join(reaction_info[:10]), "inline": False})
            
            # Stickers
            if message.stickers:
                sticker_info = [f"🎭 {sticker.name}" for sticker in message.stickers]
                embed_fields.append({"name": "🎭 Stickers", "value": " • ".join(sticker_info), "inline": False})
            
            await self.log_comprehensive_event(message.guild, "message_deleted", {
                "user": message.author,
                "channel": message.channel,
                "description": f"Message deleted in {message.channel.mention}",
                "color": 0xff0000,
                "embed_fields": embed_fields
            })
            
        except Exception as e:
            print(f"Error logging message deletion: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Enhanced message edit logging"""
        if before.author.bot or before.content == after.content:
            return
            
        try:
            embed_fields = [
                {"name": "📝 Before", "value": f"```{before.content[:700] if before.content else 'No content'}```", "inline": False},
                {"name": "✏️ After", "value": f"```{after.content[:700] if after.content else 'No content'}```", "inline": False}
            ]
            
            # Check for link changes
            before_links = [word for word in (before.content or "").split() if word.startswith(('http://', 'https://'))]
            after_links = [word for word in (after.content or "").split() if word.startswith(('http://', 'https://'))]
            
            if before_links != after_links:
                embed_fields.append({"name": "🔗 Link Changes", "value": f"Before: {', '.join(before_links[:3])}\nAfter: {', '.join(after_links[:3])}", "inline": False})
            
            await self.log_comprehensive_event(after.guild, "message_edited", {
                "user": after.author,
                "channel": after.channel,
                "description": f"Message edited in {after.channel.mention}\n🔗 [Jump to Message]({after.jump_url})",
                "color": 0xffa500,
                "embed_fields": embed_fields
            })
            
        except Exception as e:
            print(f"Error logging message edit: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Enhanced member join logging"""
        try:
            embed_fields = [
                {"name": "👤 Account Age", "value": f"<t:{int(member.created_at.timestamp())}:R>", "inline": True},
                {"name": "🧮 Member Count", "value": f"#{member.guild.member_count}", "inline": True},
                {"name": "🔍 Mention", "value": member.mention, "inline": True}
            ]
            
            # Check if account is new (potential spam)
            account_age = (datetime.now() - member.created_at).days
            if account_age < 7:
                embed_fields.append({"name": "⚠️ Warning", "value": f"New account (Created {account_age} days ago)", "inline": False})
            
            await self.log_comprehensive_event(member.guild, "member_joined", {
                "user": member,
                "description": f"**{member.display_name}** joined the server",
                "color": 0x00ff00,
                "embed_fields": embed_fields
            })
            
        except Exception as e:
            print(f"Error logging member join: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Enhanced member leave logging"""
        try:
            embed_fields = [
                {"name": "⏰ Join Date", "value": f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown", "inline": True},
                {"name": "🎭 Roles", "value": ", ".join([role.name for role in member.roles[1:5]]) or "No roles", "inline": True},
                {"name": "🧮 Member Count", "value": f"#{member.guild.member_count}", "inline": True}
            ]
            
            await self.log_comprehensive_event(member.guild, "member_left", {
                "user": member,
                "description": f"**{member.display_name}** left the server",
                "color": 0xff6b6b,
                "embed_fields": embed_fields
            })
            
        except Exception as e:
            print(f"Error logging member leave: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Enhanced member update logging"""
        try:
            changes = []
            embed_fields = []
            
            # Role changes
            if before.roles != after.roles:
                added_roles = [role for role in after.roles if role not in before.roles]
                removed_roles = [role for role in before.roles if role not in after.roles]
                
                if added_roles:
                    embed_fields.append({"name": "➕ Roles Added", "value": ", ".join([role.mention for role in added_roles]), "inline": False})
                if removed_roles:
                    embed_fields.append({"name": "➖ Roles Removed", "value": ", ".join([role.mention for role in removed_roles]), "inline": False})
                changes.append("roles")
            
            # Nickname change
            if before.nick != after.nick:
                embed_fields.append({"name": "🏷️ Nickname", "value": f"**Before:** {before.nick or 'None'}\n**After:** {after.nick or 'None'}", "inline": False})
                changes.append("nickname")
            
            # Avatar change (in guild)
            if before.avatar != after.avatar:
                changes.append("avatar")
                embed_fields.append({"name": "🖼️ Avatar", "value": "Guild avatar updated", "inline": True})
            
            if changes:
                await self.log_comprehensive_event(after.guild, f"member_updated_{'+'.join(changes)}", {
                    "user": after,
                    "description": f"**{after.display_name}** updated: {', '.join(changes)}",
                    "color": 0x7289da,
                    "embed_fields": embed_fields
                })
                
        except Exception as e:
            print(f"Error logging member update: {e}")

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """Enhanced user update logging"""
        try:
            changes = []
            embed_fields = []
            
            # Username change
            if before.name != after.name:
                embed_fields.append({"name": "👤 Username", "value": f"**Before:** {before.name}\n**After:** {after.name}", "inline": False})
                changes.append("username")
            
            # Avatar change
            if before.avatar != after.avatar:
                embed_fields.append({"name": "🖼️ Avatar", "value": "Profile avatar updated", "inline": True})
                changes.append("avatar")
            
            if changes:
                # Log in all mutual guilds
                for guild in self.bot.guilds:
                    if guild.get_member(after.id):
                        await self.log_comprehensive_event(guild, f"user_updated_{'+'.join(changes)}", {
                            "user": after,
                            "description": f"**{after.display_name}** updated: {', '.join(changes)}",
                            "color": 0x7289da,
                            "embed_fields": embed_fields
                        })
                        break  # Only log once
                        
        except Exception as e:
            print(f"Error logging user update: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Enhanced voice activity logging"""
        try:
            embed_fields = []
            action = ""
            
            if before.channel is None and after.channel is not None:
                # Joined voice
                action = "voice_joined"
                embed_fields.append({"name": "📍 Joined", "value": f"{after.channel.mention} ({after.channel.name})", "inline": False})
                
            elif before.channel is not None and after.channel is None:
                # Left voice
                action = "voice_left"
                embed_fields.append({"name": "📍 Left", "value": f"{before.channel.mention} ({before.channel.name})", "inline": False})
                
            elif before.channel != after.channel:
                # Moved voice
                action = "voice_moved"
                embed_fields.append({"name": "📍 Moved", "value": f"**From:** {before.channel.mention}\n**To:** {after.channel.mention}", "inline": False})
            
            # State changes
            states = []
            if before.mute != after.mute:
                states.append(f"Mute: {after.mute}")
            if before.deaf != after.deaf:
                states.append(f"Deaf: {after.deaf}")
            if before.self_mute != after.self_mute:
                states.append(f"Self Mute: {after.self_mute}")
            if before.self_deaf != after.self_deaf:
                states.append(f"Self Deaf: {after.self_deaf}")
            
            if states:
                embed_fields.append({"name": "🔧 State Changes", "value": "\n".join(states), "inline": False})
                if not action:
                    action = "voice_state_changed"
            
            if action:
                await self.log_comprehensive_event(member.guild, action, {
                    "user": member,
                    "description": f"**{member.display_name}** voice activity",
                    "color": 0x00d4aa,
                    "embed_fields": embed_fields
                })
                
        except Exception as e:
            print(f"Error logging voice state: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Enhanced reaction logging"""
        try:
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
                
            channel = guild.get_channel(payload.channel_id)
            user = guild.get_member(payload.user_id)
            
            if not channel or not user or user.bot:
                return
            
            message = await channel.fetch_message(payload.message_id)
            
            embed_fields = [
                {"name": "😀 Reaction", "value": f"{payload.emoji}", "inline": True},
                {"name": "📍 Message", "value": f"[Jump to Message]({message.jump_url})", "inline": True},
                {"name": "📝 Content Preview", "value": message.content[:100] + ("..." if len(message.content) > 100 else "") if message.content else "No text content", "inline": False}
            ]
            
            await self.log_comprehensive_event(guild, "reaction_added", {
                "user": user,
                "channel": channel,
                "description": f"**{user.display_name}** reacted to a message",
                "color": 0xffd700,
                "embed_fields": embed_fields
            })
            
        except Exception as e:
            print(f"Error logging reaction add: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Enhanced reaction removal logging"""
        try:
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return
                
            channel = guild.get_channel(payload.channel_id)
            user = guild.get_member(payload.user_id)
            
            if not channel or not user or user.bot:
                return
            
            message = await channel.fetch_message(payload.message_id)
            
            embed_fields = [
                {"name": "😀 Reaction Removed", "value": f"{payload.emoji}", "inline": True},
                {"name": "📍 Message", "value": f"[Jump to Message]({message.jump_url})", "inline": True},
                {"name": "📝 Content Preview", "value": message.content[:100] + ("..." if len(message.content) > 100 else "") if message.content else "No text content", "inline": False}
            ]
            
            await self.log_comprehensive_event(guild, "reaction_removed", {
                "user": user,
                "channel": channel,
                "description": f"**{user.display_name}** removed a reaction",
                "color": 0xff9966,
                "embed_fields": embed_fields
            })
            
        except Exception as e:
            print(f"Error logging reaction remove: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Enhanced channel creation logging"""
        try:
            embed_fields = [
                {"name": "📍 Channel", "value": f"{channel.mention} (`{channel.id}`)", "inline": True},
                {"name": "🏷️ Type", "value": str(channel.type).title(), "inline": True},
                {"name": "📁 Category", "value": channel.category.name if channel.category else "No category", "inline": True}
            ]
            
            await self.log_comprehensive_event(channel.guild, "channel_created", {
                "description": f"Channel **{channel.name}** was created",
                "color": 0x00ff00,
                "embed_fields": embed_fields
            })
            
        except Exception as e:
            print(f"Error logging channel creation: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Enhanced channel deletion logging"""
        try:
            embed_fields = [
                {"name": "🏷️ Name", "value": f"`{channel.name}`", "inline": True},
                {"name": "🆔 ID", "value": f"`{channel.id}`", "inline": True},
                {"name": "🏷️ Type", "value": str(channel.type).title(), "inline": True},
                {"name": "📁 Category", "value": channel.category.name if channel.category else "No category", "inline": True}
            ]
            
            await self.log_comprehensive_event(channel.guild, "channel_deleted", {
                "description": f"Channel **{channel.name}** was deleted",
                "color": 0xff0000,
                "embed_fields": embed_fields
            })
            
        except Exception as e:
            print(f"Error logging channel deletion: {e}")

    @app_commands.command(name="modclear", description="🧹 Enhanced bulk delete with comprehensive logging")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def mod_clear(self, interaction: discord.Interaction, amount: int):
        """Enhanced modclear with detailed logging"""
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need **Manage Messages** permission!", ephemeral=True)
            return
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
            return
        
        try:
            await interaction.response.defer()
            
            # Fetch messages
            messages = []
            async for message in interaction.channel.history(limit=amount):
                messages.append(message)
            
            if not messages:
                await interaction.followup.send("❌ No messages to delete!", ephemeral=True)
                return
            
            # Delete messages
            deleted = await interaction.channel.purge(limit=amount)
            actual_deleted = len(deleted)
            
            # Log the action
            await self.log_comprehensive_event(interaction.guild, "bulk_delete_modclear", {
                "user": interaction.user,
                "channel": interaction.channel,
                "description": f"**{interaction.user.display_name}** deleted {actual_deleted} messages in {interaction.channel.mention}",
                "color": 0xff9966,
                "embed_fields": [
                    {"name": "📊 Summary", "value": f"**Deleted:** {actual_deleted} messages\n**Channel:** {interaction.channel.mention}", "inline": False}
                ]
            })
            
            # Send confirmation
            embed = discord.Embed(
                title="🧹 **Messages Cleared**",
                description=f"Successfully deleted **{actual_deleted}** messages",
                color=0x00d4aa
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error during modclear: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EnhancedModeration(bot))