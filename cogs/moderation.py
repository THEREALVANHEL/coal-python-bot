import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

import google.generativeai as genai

# Config
GUILD_ID = 1370009417726169250

MODERATOR_ROLES = ["Moderator 🚨🚓", "🚨 Lead moderator"]
FOOTER_TXT = "VANHELISMYSENSEI"

# Permission check helper
def has_moderator_role(interaction: discord.Interaction) -> bool:
    # Check for special admin role first
    if has_special_permissions(interaction):
        return True
    
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in MODERATOR_ROLES for role in user_roles)

class ContinueAdventureModal(discord.ui.Modal):
    def __init__(self, character: str, style: str):
        super().__init__(title=f"Continue Adventure as {character}")
        self.character = character
        self.style = style
        
        self.action_input = discord.ui.TextInput(
            label="What does your character do next?",
            placeholder="Describe your action, dialogue, or choice in detail...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        self.add_item(self.action_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Get recent channel messages for context
            channel_history = []
            try:
                async for message in interaction.channel.history(limit=10):
                    if not message.author.bot and len(message.content) > 0:
                        channel_history.append(f"{message.author.display_name}: {message.content[:100]}")
            except:
                pass

            # Build enhanced prompt with context
            style_prompts = {
                "fantasy": "magical medieval fantasy world with dragons, magic, and kingdoms",
                "scifi": "futuristic space setting with advanced technology and alien worlds", 
                "modern": "contemporary modern-day setting with realistic scenarios",
                "mystery": "mysterious detective story with clues and puzzles to solve",
                "comedy": "humorous and funny situation with light-hearted comedy",
                "creative": "unique and artistic scenario that breaks traditional boundaries"
            }

            context_text = ""
            if channel_history:
                context_text = f"\n\nRecent channel context (for reference): {' | '.join(reversed(channel_history[-3:]))}"

            user_action = self.action_input.value

            prompt = f"""You are an interactive roleplay AI assistant. Continue the adventure based on the user's action.

ROLEPLAY CONTINUATION:
- User's Character: {self.character}
- Setting: {style_prompts.get(self.style, 'fantasy adventure')}
- User's Action: {user_action}

INSTRUCTIONS:
- Respond to the user's action as both narrator and NPCs
- Describe the consequences of their action and what happens next
- Include vivid details about the environment, characters, and atmosphere
- Keep responses engaging and descriptive but not too long (under 1500 chars)
- Continue the story naturally based on their choice
- Include dialogue from NPCs if relevant
- End with what the character sees/feels/encounters next{context_text}

Continue the adventure:"""

            # Call Gemini AI
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                embed = discord.Embed(
                    title="❌ **AI Service Unavailable**",
                    description="🤖 The roleplay AI is currently offline. Please contact an administrator!",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(prompt)
            
            if response.text:
                # Create adventure continuation embed
                embed = discord.Embed(
                    title=f"🎭 **Adventure Continues - {self.character}**",
                    description=response.text,
                    color=0x7c3aed,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="🎯 **Your Action**", 
                    value=f"*{user_action}*", 
                    inline=False
                )
                
                embed.add_field(
                    name="� **Continue Playing**",
                    value="Click 'Continue Adventure' again to keep the story going, or use `/roleplay` to start fresh!",
                    inline=False
                )
                
                embed.set_author(
                    name=f"Adventure for {interaction.user.display_name}", 
                    icon_url=interaction.user.display_avatar.url
                )
                embed.set_footer(text="🎮 Interactive Roleplay System")
                
                # Add the view again for continuous play
                view = RoleplayView(self.character, self.style)
                await interaction.followup.send(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    title="❌ **AI Response Error**",
                    description="The AI couldn't generate a response. Please try again with a different action.",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ **Adventure Error**",
                description="Something went wrong continuing your adventure. Please try again.",
                color=0xff6b6b
            )
            embed.add_field(name="🔍 Error Details", value=f"```{str(e)[:100]}```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

class RoleplayView(discord.ui.View):
    def __init__(self, character: str, style: str):
        super().__init__(timeout=1800)  # 30 minutes
        self.character = character
        self.style = style

    @discord.ui.button(label="🎲 Continue Adventure", style=discord.ButtonStyle.primary, emoji="🎲")
    async def continue_adventure(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ContinueAdventureModal(self.character, self.style)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📖 Story Tips", style=discord.ButtonStyle.secondary, emoji="📖")
    async def story_tips(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📖 **Roleplay Tips & Guide**",
            description="Make your roleplay experience even better! 🌟",
            color=0x7c3aed
        )
        
        embed.add_field(
            name="🎭 **Great Roleplay Actions**",
            value="• Describe what your character does\n• Include dialogue in quotes\n• Ask questions to NPCs\n• Make choices about your path\n• React to the environment",
            inline=False
        )
        
        embed.add_field(
            name="💡 **Example Responses**",
            value='• "I approach the mysterious door and listen carefully"\n• "Hello there! Can you tell me about this place?"\n• "I choose to go left toward the forest"\n• "I cast a healing spell on the injured traveler"',
            inline=False
        )
        
        embed.add_field(
            name="🎯 **Pro Tips**",
            value="• Be specific in your actions\n• Ask questions to learn more\n• Don't be afraid to be creative\n• The AI remembers your choices!",
            inline=False
        )
        
        embed.set_footer(text="🎲 Ready to continue your adventure?")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Moderation] Loaded successfully with comprehensive A-Z logging.")

    async def get_log_channel(self, guild):
        """Get the moderation log channel for the guild"""
        try:
            server_settings = db.get_server_settings(guild.id)
            log_channel_id = server_settings.get('mod_log_channel')
            
            if log_channel_id:
                return guild.get_channel(log_channel_id)
            
            # Look for common log channel names
            for channel in guild.text_channels:
                if any(name in channel.name.lower() for name in ['mod-log', 'modlog', 'audit-log', 'logs']):
                    return channel
            
            return None
        except:
            return None

    async def log_moderation_action(self, guild, action_type, embed):
        """Send moderation log to appropriate channel"""
        try:
            log_channel = await self.get_log_channel(guild)
            if log_channel:
                await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to log moderation action: {e}")

    # === COMPREHENSIVE EVENT LOGGING ===
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log message deletions including attachments, embeds, etc."""
        if message.author.bot:
            return
        
        try:
            embed = discord.Embed(
                title="🗑️ **Message Deleted**",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 **User**",
                value=f"{message.author.mention}\n`{message.author}` (ID: {message.author.id})",
                inline=True
            )
            
            embed.add_field(
                name="📍 **Channel**",
                value=f"{message.channel.mention}\n`#{message.channel.name}`",
                inline=True
            )
            
            embed.add_field(
                name="🕒 **Deleted At**",
                value=f"<t:{int(datetime.now().timestamp())}:R>",
                inline=True
            )
            
            # Message content
            if message.content:
                content = message.content[:1000] + ("..." if len(message.content) > 1000 else "")
                embed.add_field(
                    name="📝 **Content**",
                    value=f"```{content}```",
                    inline=False
                )
            
            # Attachments
            if message.attachments:
                attachment_info = []
                for attachment in message.attachments:
                    attachment_info.append(f"📎 **{attachment.filename}** ({attachment.size} bytes)")
                embed.add_field(
                    name="📁 **Attachments**",
                    value="\n".join(attachment_info),
                    inline=False
                )
            
            # Embeds
            if message.embeds:
                embed.add_field(
                    name="🔗 **Embeds**",
                    value=f"Message contained {len(message.embeds)} embed(s)",
                    inline=False
                )
            
            # Reactions
            if message.reactions:
                reactions = [f"{reaction.emoji} ({reaction.count})" for reaction in message.reactions]
                embed.add_field(
                    name="😀 **Reactions**",
                    value=" • ".join(reactions),
                    inline=False
                )
            
            embed.set_author(
                name=f"Message by {message.author.display_name}",
                icon_url=message.author.display_avatar.url
            )
            embed.set_footer(text=f"Message ID: {message.id}")
            
            await self.log_moderation_action(message.guild, "message_delete", embed)
            
        except Exception as e:
            print(f"Error logging message deletion: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Log message edits"""
        if before.author.bot:
            return
        
        if before.content == after.content:
            return  # No content change
        
        try:
            embed = discord.Embed(
                title="✏️ **Message Edited**",
                color=0xffa500,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 **User**",
                value=f"{after.author.mention}\n`{after.author}` (ID: {after.author.id})",
                inline=True
            )
            
            embed.add_field(
                name="📍 **Channel**",
                value=f"{after.channel.mention}\n`#{after.channel.name}`",
                inline=True
            )
            
            embed.add_field(
                name="🔗 **Jump to Message**",
                value=f"[Click here]({after.jump_url})",
                inline=True
            )
            
            # Before content
            if before.content:
                before_content = before.content[:500] + ("..." if len(before.content) > 500 else "")
                embed.add_field(
                    name="📝 **Before**",
                    value=f"```{before_content}```",
                    inline=False
                )
            
            # After content
            if after.content:
                after_content = after.content[:500] + ("..." if len(after.content) > 500 else "")
                embed.add_field(
                    name="📝 **After**",
                    value=f"```{after_content}```",
                    inline=False
                )
            
            embed.set_author(
                name=f"Edit by {after.author.display_name}",
                icon_url=after.author.display_avatar.url
            )
            embed.set_footer(text=f"Message ID: {after.id}")
            
            await self.log_moderation_action(after.guild, "message_edit", embed)
            
        except Exception as e:
            print(f"Error logging message edit: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Log member joins"""
        try:
            embed = discord.Embed(
                title="📥 **Member Joined**",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 **Member**",
                value=f"{member.mention}\n`{member}` (ID: {member.id})",
                inline=True
            )
            
            embed.add_field(
                name="📅 **Account Created**",
                value=f"<t:{int(member.created_at.timestamp())}:R>",
                inline=True
            )
            
            embed.add_field(
                name="📊 **Member Count**",
                value=f"{member.guild.member_count} total members",
                inline=True
            )
            
            embed.set_author(
                name=f"{member.display_name} joined the server",
                icon_url=member.display_avatar.url
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await self.log_moderation_action(member.guild, "member_join", embed)
            
        except Exception as e:
            print(f"Error logging member join: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log member leaves/kicks"""
        try:
            embed = discord.Embed(
                title="📤 **Member Left**",
                color=0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 **Member**",
                value=f"`{member}` (ID: {member.id})",
                inline=True
            )
            
            embed.add_field(
                name="📅 **Joined**",
                value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown",
                inline=True
            )
            
            embed.add_field(
                name="📊 **Member Count**",
                value=f"{member.guild.member_count} total members",
                inline=True
            )
            
            # Show roles they had
            if member.roles[1:]:  # Exclude @everyone
                roles = [role.mention for role in member.roles[1:]]
                embed.add_field(
                    name="🎭 **Roles**",
                    value=" • ".join(roles[:10]),  # Limit to 10 roles
                    inline=False
                )
            
            embed.set_author(
                name=f"{member.display_name} left the server",
                icon_url=member.display_avatar.url
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await self.log_moderation_action(member.guild, "member_leave", embed)
            
        except Exception as e:
            print(f"Error logging member leave: {e}")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Log member bans"""
        try:
            embed = discord.Embed(
                title="🔨 **Member Banned**",
                color=0x8b0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 **Banned User**",
                value=f"`{user}` (ID: {user.id})",
                inline=True
            )
            
            # Try to get ban reason from audit log
            try:
                async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=5):
                    if entry.target.id == user.id:
                        embed.add_field(
                            name="👮 **Banned By**",
                            value=f"{entry.user.mention}\n`{entry.user}`",
                            inline=True
                        )
                        if entry.reason:
                            embed.add_field(
                                name="📝 **Reason**",
                                value=entry.reason,
                                inline=False
                            )
                        break
            except:
                pass
            
            embed.set_author(
                name=f"{user.display_name} was banned",
                icon_url=user.display_avatar.url
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"User ID: {user.id}")
            
            await self.log_moderation_action(guild, "member_ban", embed)
            
        except Exception as e:
            print(f"Error logging member ban: {e}")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Log member unbans"""
        try:
            embed = discord.Embed(
                title="🔓 **Member Unbanned**",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 **Unbanned User**",
                value=f"`{user}` (ID: {user.id})",
                inline=True
            )
            
            # Try to get unban info from audit log
            try:
                async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=5):
                    if entry.target.id == user.id:
                        embed.add_field(
                            name="👮 **Unbanned By**",
                            value=f"{entry.user.mention}\n`{entry.user}`",
                            inline=True
                        )
                        if entry.reason:
                            embed.add_field(
                                name="📝 **Reason**",
                                value=entry.reason,
                                inline=False
                            )
                        break
            except:
                pass
            
            embed.set_author(
                name=f"{user.display_name} was unbanned",
                icon_url=user.display_avatar.url
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"User ID: {user.id}")
            
            await self.log_moderation_action(guild, "member_unban", embed)
            
        except Exception as e:
            print(f"Error logging member unban: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creation"""
        try:
            embed = discord.Embed(
                title="📝 **Channel Created**",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📍 **Channel**",
                value=f"{channel.mention}\n`#{channel.name}` (ID: {channel.id})",
                inline=True
            )
            
            embed.add_field(
                name="🏷️ **Type**",
                value=str(channel.type).title(),
                inline=True
            )
            
            # Try to get creator from audit log
            try:
                async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=5):
                    if entry.target.id == channel.id:
                        embed.add_field(
                            name="👮 **Created By**",
                            value=f"{entry.user.mention}\n`{entry.user}`",
                            inline=True
                        )
                        break
            except:
                pass
            
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="📁 **Category**",
                    value=channel.category.name,
                    inline=True
                )
            
            embed.set_footer(text=f"Channel ID: {channel.id}")
            
            await self.log_moderation_action(channel.guild, "channel_create", embed)
            
        except Exception as e:
            print(f"Error logging channel creation: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletion"""
        try:
            embed = discord.Embed(
                title="🗑️ **Channel Deleted**",
                color=0xff0000,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📍 **Channel**",
                value=f"`#{channel.name}` (ID: {channel.id})",
                inline=True
            )
            
            embed.add_field(
                name="🏷️ **Type**",
                value=str(channel.type).title(),
                inline=True
            )
            
            # Try to get deleter from audit log
            try:
                async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=5):
                    if entry.target.id == channel.id:
                        embed.add_field(
                            name="👮 **Deleted By**",
                            value=f"{entry.user.mention}\n`{entry.user}`",
                            inline=True
                        )
                        if entry.reason:
                            embed.add_field(
                                name="📝 **Reason**",
                                value=entry.reason,
                                inline=False
                            )
                        break
            except:
                pass
            
            if hasattr(channel, 'category') and channel.category:
                embed.add_field(
                    name="📁 **Category**",
                    value=channel.category.name,
                    inline=True
                )
            
            embed.set_footer(text=f"Channel ID: {channel.id}")
            
            await self.log_moderation_action(channel.guild, "channel_delete", embed)
            
        except Exception as e:
            print(f"Error logging channel deletion: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log member updates (roles, nickname, etc.)"""
        try:
            changes = []
            
            # Check nickname change
            if before.nick != after.nick:
                changes.append({
                    "type": "nickname",
                    "before": before.nick or before.name,
                    "after": after.nick or after.name
                })
            
            # Check role changes
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            
            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles
            
            if added_roles:
                changes.append({
                    "type": "roles_added",
                    "roles": [role.mention for role in added_roles]
                })
            
            if removed_roles:
                changes.append({
                    "type": "roles_removed",
                    "roles": [role.mention for role in removed_roles]
                })
            
            # If no significant changes, don't log
            if not changes:
                return
            
            embed = discord.Embed(
                title="👤 **Member Updated**",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 **Member**",
                value=f"{after.mention}\n`{after}` (ID: {after.id})",
                inline=True
            )
            
            # Log changes
            for change in changes:
                if change["type"] == "nickname":
                    embed.add_field(
                        name="📝 **Nickname Changed**",
                        value=f"**Before:** {change['before']}\n**After:** {change['after']}",
                        inline=False
                    )
                elif change["type"] == "roles_added":
                    embed.add_field(
                        name="➕ **Roles Added**",
                        value=" • ".join(change["roles"]),
                        inline=False
                    )
                elif change["type"] == "roles_removed":
                    embed.add_field(
                        name="➖ **Roles Removed**",
                        value=" • ".join(change["roles"]),
                        inline=False
                    )
            
            embed.set_author(
                name=f"Update for {after.display_name}",
                icon_url=after.display_avatar.url
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text=f"User ID: {after.id}")
            
            await self.log_moderation_action(after.guild, "member_update", embed)
            
        except Exception as e:
            print(f"Error logging member update: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Log voice channel activity"""
        try:
            if before.channel == after.channel:
                return  # No channel change
            
            embed = discord.Embed(
                title="🔊 **Voice Activity**",
                color=0x9b59b6,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 **Member**",
                value=f"{member.mention}\n`{member}` (ID: {member.id})",
                inline=True
            )
            
            if before.channel is None and after.channel is not None:
                # Joined voice channel
                embed.title = "🔊 **Voice Channel Joined**"
                embed.color = 0x00ff00
                embed.add_field(
                    name="📍 **Joined**",
                    value=f"{after.channel.mention}\n`{after.channel.name}`",
                    inline=True
                )
            elif before.channel is not None and after.channel is None:
                # Left voice channel
                embed.title = "🔇 **Voice Channel Left**"
                embed.color = 0xff0000
                embed.add_field(
                    name="📍 **Left**",
                    value=f"`{before.channel.name}`",
                    inline=True
                )
            else:
                # Moved between channels
                embed.title = "🔄 **Voice Channel Moved**"
                embed.color = 0xffa500
                embed.add_field(
                    name="📍 **From**",
                    value=f"`{before.channel.name}`",
                    inline=True
                )
                embed.add_field(
                    name="📍 **To**",
                    value=f"{after.channel.mention}\n`{after.channel.name}`",
                    inline=True
                )
            
            embed.set_author(
                name=f"Voice activity by {member.display_name}",
                icon_url=member.display_avatar.url
            )
            embed.set_footer(text=f"User ID: {member.id}")
            
            await self.log_moderation_action(member.guild, "voice_update", embed)
            
        except Exception as e:
            print(f"Error logging voice activity: {e}")

    # === ENHANCED MODCLEAR COMMAND ===

    @app_commands.command(name="addxp", description="Add XP to a user (Admin only)")
    @app_commands.describe(user="User to give XP to", amount="Amount of XP to add")
    @app_commands.default_permissions(administrator=True)
    async def addxp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Add XP to a user"""
        if not (interaction.user.guild_permissions.administrator or has_special_permissions(interaction)):
            await interaction.response.send_message("❌ You need administrator permissions or the special admin role to use this command!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return

        try:
            await interaction.response.defer()
            
            # Get current XP
            old_user_data = db.get_user_data(user.id)
            old_xp = old_user_data.get('xp', 0)
            
            # Calculate levels
            leveling_cog = self.bot.get_cog('Leveling')
            old_level = leveling_cog.calculate_level_from_xp(old_xp) if leveling_cog else 0
            
            # Add XP
            db.add_xp(user.id, amount)
            new_xp = old_xp + amount
            new_level = leveling_cog.calculate_level_from_xp(new_xp) if leveling_cog else 0
            
            # Update roles
            if leveling_cog and hasattr(user, 'guild'):
                await leveling_cog.update_xp_roles(user, new_level)
            
            # Check for level up
            level_up_text = ""
            if new_level > old_level:
                level_up_text = f"\n🎉 **Level Up!** {old_level} → {new_level}"
            
            embed = discord.Embed(
                title="⚡ **XP Boost Added!**",
                description=f"Successfully added **{amount:,} XP** to {user.mention}!{level_up_text}",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Previous XP", value=f"⚡ {old_xp:,}", inline=True)
            embed.add_field(name="➕ XP Added", value=f"🎁 {amount:,}", inline=True)
            embed.add_field(name="💫 New XP", value=f"✨ {new_xp:,}", inline=True)
            embed.add_field(name="� Level", value=f"🏆 Level {new_level}", inline=True)
            
            embed.set_author(name=f"XP boost by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="⚡ XP Management System")
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error adding XP: {str(e)}", ephemeral=True)
            except:
                await interaction.response.send_message(f"❌ Error adding XP: {str(e)}", ephemeral=True)

    @app_commands.command(name="removexp", description="Remove XP from a user (Admin only)")
    @app_commands.describe(user="User to remove XP from", amount="Amount of XP to remove")
    @app_commands.default_permissions(administrator=True)
    async def removexp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Remove XP from a user"""
        if not (interaction.user.guild_permissions.administrator or has_special_permissions(interaction)):
            await interaction.response.send_message("❌ You need administrator permissions or the special admin role to use this command!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return

        try:
            await interaction.response.defer()
            
            # Get current XP
            old_user_data = db.get_user_data(user.id)
            old_xp = old_user_data.get('xp', 0)
            
            if old_xp <= 0:
                embed = discord.Embed(
                    title="⚡ **No XP to Remove**",
                    description=f"{user.mention} doesn't have any XP to remove!",
                    color=0xff9966
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Don't remove more than they have
            amount_to_remove = min(amount, old_xp)
            
            # Calculate levels
            leveling_cog = self.bot.get_cog('Leveling')
            old_level = leveling_cog.calculate_level_from_xp(old_xp) if leveling_cog else 0
            
            # Remove XP
            db.remove_xp(user.id, amount_to_remove)
            new_xp = old_xp - amount_to_remove
            new_level = leveling_cog.calculate_level_from_xp(new_xp) if leveling_cog else 0
            
            # Update roles
            if leveling_cog and hasattr(user, 'guild'):
                await leveling_cog.update_xp_roles(user, new_level)
            
            # Check for level down
            level_change_text = ""
            if new_level < old_level:
                level_change_text = f"\n📉 **Level Down:** {old_level} → {new_level}"
            
            embed = discord.Embed(
                title="⚡ **XP Removed**",
                description=f"Successfully removed **{amount_to_remove:,} XP** from {user.mention}!{level_change_text}",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Previous XP", value=f"⚡ {old_xp:,}", inline=True)
            embed.add_field(name="➖ XP Removed", value=f"🗑️ {amount_to_remove:,}", inline=True)
            embed.add_field(name="💫 New XP", value=f"📉 {new_xp:,}", inline=True)
            embed.add_field(name="📈 Level", value=f"🏆 Level {new_level}", inline=True)
            
            if amount_to_remove < amount:
                embed.add_field(
                    name="ℹ️ Note", 
                    value=f"Only removed {amount_to_remove:,} XP (user only had {old_xp:,} XP)", 
                    inline=False
                )
            
            embed.set_author(name=f"XP removal by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="⚡ XP Management System")
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error removing XP: {str(e)}", ephemeral=True)
            except:
                await interaction.response.send_message(f"❌ Error removing XP: {str(e)}", ephemeral=True)

    @app_commands.command(name="modclear", description="Deletes a specified number of messages from a channel")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def modclear(self, interaction: discord.Interaction, amount: int):
        # Check permissions
        if not (interaction.user.guild_permissions.manage_messages or has_special_permissions(interaction)):
            await interaction.response.send_message("❌ You need 'Manage Messages' permission or the special admin role to use this command!", ephemeral=True)
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Store message info before deletion for logging
            messages_to_delete = []
            async for message in interaction.channel.history(limit=amount):
                message_info = {
                    "author": str(message.author),
                    "author_id": message.author.id,
                    "content": message.content[:100] + ("..." if len(message.content) > 100 else ""),
                    "attachments": len(message.attachments),
                    "embeds": len(message.embeds),
                    "created_at": message.created_at
                }
                messages_to_delete.append(message_info)
            
            deleted = await interaction.channel.purge(limit=amount)
            
            # Create comprehensive logging embed
            log_embed = discord.Embed(
                title="🗑️ **Bulk Message Deletion**",
                description=f"**{len(deleted)}** messages were deleted from {interaction.channel.mention}",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            
            log_embed.add_field(
                name="👮 **Moderator**",
                value=f"{interaction.user.mention}\n`{interaction.user}` (ID: {interaction.user.id})",
                inline=True
            )
            
            log_embed.add_field(
                name="📍 **Channel**",
                value=f"{interaction.channel.mention}\n`#{interaction.channel.name}` (ID: {interaction.channel.id})",
                inline=True
            )
            
            log_embed.add_field(
                name="🔢 **Amount**",
                value=f"**{len(deleted)}** messages deleted",
                inline=True
            )
            
            # Analyze deleted messages
            if messages_to_delete:
                authors = {}
                total_attachments = 0
                total_embeds = 0
                
                for msg in messages_to_delete:
                    author_name = msg["author"]
                    authors[author_name] = authors.get(author_name, 0) + 1
                    total_attachments += msg["attachments"]
                    total_embeds += msg["embeds"]
                
                # Top authors
                sorted_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)
                top_authors = sorted_authors[:5]  # Top 5 authors
                author_text = "\n".join([f"**{author}**: {count} message(s)" for author, count in top_authors])
                
                log_embed.add_field(
                    name="👥 **Top Message Authors**",
                    value=author_text if author_text else "No messages found",
                    inline=False
                )
                
                # Content summary
                if total_attachments > 0 or total_embeds > 0:
                    content_summary = []
                    if total_attachments > 0:
                        content_summary.append(f"📎 {total_attachments} attachment(s)")
                    if total_embeds > 0:
                        content_summary.append(f"🔗 {total_embeds} embed(s)")
                    
                    log_embed.add_field(
                        name="📊 **Content Summary**",
                        value=" • ".join(content_summary),
                        inline=False
                    )
                
                # Recent messages preview (last 3)
                recent_messages = messages_to_delete[:3]
                if recent_messages:
                    preview_text = ""
                    for msg in recent_messages:
                        if msg["content"]:
                            preview_text += f"**{msg['author']}**: {msg['content']}\n"
                    
                    if preview_text:
                        log_embed.add_field(
                            name="👁️ **Recent Messages Preview**",
                            value=preview_text[:500] + ("..." if len(preview_text) > 500 else ""),
                            inline=False
                        )
            
            log_embed.set_author(
                name=f"Bulk deletion by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            log_embed.set_footer(text=f"Moderation Action • {len(deleted)} messages removed")
            
            # Send to log channel
            await self.log_moderation_action(interaction.guild, "bulk_delete", log_embed)
            
            # Response to moderator
            embed = discord.Embed(
                title="🗑️ **Messages Cleared Successfully**",
                description=f"Successfully deleted **{len(deleted)}** messages from {interaction.channel.mention}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 **Deletion Summary**",
                value=f"• **Messages Deleted**: {len(deleted)}\n• **Channel**: {interaction.channel.mention}\n• **Moderator**: {interaction.user.mention}",
                inline=False
            )
            
            if len(deleted) != amount:
                embed.add_field(
                    name="ℹ️ **Note**",
                    value=f"Requested {amount} messages, but only {len(deleted)} were available/deleted.",
                    inline=False
                )
            
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="✨ Professional Moderation System")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to delete messages in this channel!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(
        user="User to warn",
        reason="Reason for the warning"
        )
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        # Add warning to database
        try:
            db.add_warning(user.id, reason, interaction.user.id)
            warnings = db.get_user_warnings(user.id)
            
            embed = discord.Embed(
                title="⚠️ User Warned",
                description=f"**User:** {user.mention}\n**Reason:** {reason}\n**Total Warnings:** {len(warnings)}",
                color=0xff9900,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=FOOTER_TXT)

            await interaction.response.send_message(embed=embed)

            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="⚠️ Warning Received",
                    description=f"You have been warned in **{interaction.guild.name}**\n\n**Reason:** {reason}",
                    color=0xff9900
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled

        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding warning: {str(e)}", ephemeral=True)

    @app_commands.command(name="warnlist", description="📋 Check warnings for a user (visible to everyone)")
    @app_commands.describe(user="User to check warnings for")
    async def warn_list(self, interaction: discord.Interaction, user: discord.Member):
        # Anyone can check warnings now - no permission check needed

        try:
            warnings = db.get_user_warnings(user.id)
            
            embed = discord.Embed(
                title="⚠️ Warning List",
                description=f"**User:** {user.mention}\n**Total Warnings:** {len(warnings)}",
                color=0xff9900 if warnings else 0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
            if warnings:
                warning_text = []
                for i, warning in enumerate(warnings[-10:], 1):  # Show last 10 warnings
                    timestamp = datetime.fromtimestamp(warning.get('timestamp', 0))
                    moderator_id = warning.get('moderator_id', 'Unknown')
                    reason = warning.get('reason', 'No reason provided')
                    
                    try:
                        moderator = self.bot.get_user(moderator_id)
                        mod_name = moderator.display_name if moderator else f"Unknown ({moderator_id})"
                    except:
                        mod_name = f"Unknown ({moderator_id})"
                    
                    warning_text.append(f"**{i}.** {reason}\n*By {mod_name} on {timestamp.strftime('%Y-%m-%d %H:%M')}*")
                
                embed.add_field(
                    name="📝 Recent Warnings",
                    value="\n\n".join(warning_text),
                    inline=False
                )
                
                if len(warnings) > 10:
                    embed.set_footer(text=f"Showing 10 most recent warnings out of {len(warnings)} total")
                else:
                    embed.set_footer(text=FOOTER_TXT)
            else:
                embed.add_field(
                    name="✅ Clean Record",
                    value="This user has no warnings on record.",
                    inline=False
                )
                embed.set_footer(text=FOOTER_TXT)
            
            # Make warnlist PUBLIC - everyone can see warnings now
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error retrieving warnings: {str(e)}", ephemeral=True)

    @app_commands.command(name="removewarnlist", description="🗑️ Remove specific warning or clear all warnings for a user")
    @app_commands.describe(
        user="User to remove warnings from",
        warning_index="Warning number to remove (leave empty to clear all)",
        reason="Reason for removing warning(s)"
    )
    async def remove_warn_list(self, interaction: discord.Interaction, user: discord.Member, warning_index: int = None, reason: str = "No reason provided"):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            warnings = db.get_user_warnings(user.id)
            
            if not warnings:
                embed = discord.Embed(
                    title="ℹ️ No Warnings",
                    description=f"{user.mention} has no warnings to remove.",
                    color=0x7289da
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if warning_index is None:
                # Remove all warnings
                db.clear_user_warnings(user.id)
                
                embed = discord.Embed(
                    title="🗑️ All Warnings Cleared",
                    description=f"Cleared **{len(warnings)}** warning(s) for {user.mention}",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📝 Reason", value=reason, inline=False)
                embed.add_field(name="👮 Moderator", value=interaction.user.mention, inline=True)
                embed.set_footer(text=FOOTER_TXT)
                
                await interaction.response.send_message(embed=embed)
            else:
                # Remove specific warning
                if warning_index < 1 or warning_index > len(warnings):
                    await interaction.response.send_message(f"❌ Invalid warning index! User has {len(warnings)} warning(s). Use `/checkwarnlist` to see warning numbers.", ephemeral=True)
                    return
                
                removed_warning = warnings[warning_index - 1]
                db.remove_specific_warning(user.id, warning_index - 1)
                
                embed = discord.Embed(
                    title="🗑️ Warning Removed",
                    description=f"Removed warning #{warning_index} from {user.mention}",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📝 Removed Warning", value=removed_warning.get('reason', 'No reason'), inline=False)
                embed.add_field(name="📝 Removal Reason", value=reason, inline=False)
                embed.add_field(name="👮 Moderator", value=interaction.user.mention, inline=True)
                embed.add_field(name="📊 Remaining", value=f"{len(warnings) - 1} warning(s)", inline=True)
                embed.set_footer(text=FOOTER_TXT)
                
                await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing warning(s): {str(e)}", ephemeral=True)

    @app_commands.command(name="updateroles", description="Updates roles based on a user's current level and cookies")
    @app_commands.describe(user="User to update roles for")
    async def updateroles(self, interaction: discord.Interaction, user: discord.Member):
        if not (interaction.user.guild_permissions.manage_roles or has_special_permissions(interaction)):
            await interaction.response.send_message("❌ You need 'Manage Roles' permission or the special admin role to use this command!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Import leveling cog to access role mappings and utility functions
            leveling_cog = self.bot.get_cog('Leveling')
            if not leveling_cog:
                await interaction.followup.send("❌ Leveling system not loaded!", ephemeral=True)
                return

            # Get user data from database
            user_data = db.get_user_data(user.id)
            xp = user_data.get('xp', 0)
            cookies = user_data.get('cookies', 0)
            
            # Calculate level from XP using leveling cog method
            level = leveling_cog.calculate_level_from_xp(xp)

            # Get role mappings from the leveling cog for consistency
            cookies_cog = self.bot.get_cog('Cookies')
            
            # XP roles from leveling cog
            XP_ROLES = {
                30: 1371003310223654974,   # Level 30
                50: 1371003359263871097,   # Level 50  
                100: 1371003394106654780,  # Level 100
                150: 1371003437574082620,  # Level 150
                250: 1371003475851796530,  # Level 250
                450: 1371003513755852890   # Level 450
            }

            # Cookie roles - import from cookies cog to ensure consistency
            COOKIE_ROLES = {
                100: 1370998669884788788,   # 100 cookies
                500: 1370999721593671760,   # 500 cookies
                1000: 1371000389444305017,  # 1000 cookies
                1750: 1371001322131947591,  # 1750 cookies
                3000: 1371001806930579518,  # 3000 cookies
                5000: 1371304693715964005   # 5000 cookies
            }

            roles_added = []
            roles_removed = []

            # Store original roles for comparison
            original_roles = set(user.roles)

            # Update XP roles - find highest eligible XP role
            user_xp_roles = [role for role in user.roles if role.id in XP_ROLES.values()]
            highest_xp_role_id = None
            highest_xp_req = 0
            
            for level_req, role_id in XP_ROLES.items():
                if level >= level_req and level_req > highest_xp_req:
                    highest_xp_req = level_req
                    highest_xp_role_id = role_id
            
            # Remove all XP roles first
            if user_xp_roles:
                try:
                    await user.remove_roles(*user_xp_roles, reason="XP role update - clearing old roles")
                    for role in user_xp_roles:
                        roles_removed.append(f"Level {[k for k, v in XP_ROLES.items() if v == role.id][0]}")
                except Exception as e:
                    print(f"Error removing XP roles: {e}")
            
            # Add the highest XP role if eligible
            if highest_xp_role_id:
                highest_xp_role = interaction.guild.get_role(highest_xp_role_id)
                if highest_xp_role:
                    try:
                        await user.add_roles(highest_xp_role, reason=f"XP role update - Level {level}")
                        roles_added.append(f"Level {highest_xp_req}")
                    except Exception as e:
                        print(f"Error adding XP role: {e}")
            
            # Update cookie roles - use cookies cog method for consistency
            if cookies_cog:
                # Store original cookie roles
                user_cookie_roles = [role for role in user.roles if role.id in COOKIE_ROLES.values()]
                
                # Update using cookies cog method
                await cookies_cog.update_cookie_roles(user, cookies)
                
                # Check what changed for cookie roles
                new_cookie_roles = [role for role in user.roles if role.id in COOKIE_ROLES.values()]
                
                # Track changes
                for role in user_cookie_roles:
                    if role not in new_cookie_roles:
                        roles_removed.append(f"{[k for k, v in COOKIE_ROLES.items() if v == role.id][0]} Cookies")
                
                for role in new_cookie_roles:
                    if role not in user_cookie_roles:
                        roles_added.append(f"{[k for k, v in COOKIE_ROLES.items() if v == role.id][0]} Cookies")

            # Create response embed
            embed = discord.Embed(
                title="🔄 **Role Update Complete!**",
                description=f"**User:** {user.mention}\n**Level:** {level} 🎯\n**Cookies:** {cookies:,} 🍪",
                color=0x00d4aa if roles_added or roles_removed else 0x7289da,
                timestamp=datetime.now()
            )
            
            if roles_added:
                role_list = "\n".join([f"🎉 **{role}**" for role in roles_added])
                embed.add_field(
                    name="➕ **Roles Added**", 
                    value=role_list, 
                    inline=False
                )
            if roles_removed:
                role_list = "\n".join([f"🗑️ **{role}**" for role in roles_removed])
                embed.add_field(
                    name="➖ **Roles Removed**", 
                    value=role_list, 
                    inline=False
                )
            if not roles_added and not roles_removed:
                embed.add_field(
                    name="✅ **Perfect Match!**", 
                    value="🎯 User already has all the appropriate roles for their level and cookies!", 
                    inline=False
                )
            
            # Add detailed stats
            embed.add_field(
                name="📊 **Update Summary**",
                value=f"➕ **Added:** {len(roles_added)} role(s)\n➖ **Removed:** {len(roles_removed)} role(s)",
                inline=True
            )
            
            # Add role breakdown if changes were made
            if roles_added or roles_removed:
                status_text = "✨ **Role updates successfully applied!**"
                if roles_added and roles_removed:
                    status_text = "🔄 **Roles updated - added new milestones and removed outdated ones**"
                elif roles_added:
                    status_text = "🎉 **Congratulations! New milestone roles earned**"
                elif roles_removed:
                    status_text = "🧹 **Cleaned up outdated roles**"
                
                embed.add_field(
                    name="🎯 **Status**",
                    value=status_text,
                    inline=False
                )
            
            embed.set_author(name=f"Updated by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"✨ {FOOTER_TXT} • Role management system")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ Error updating roles: {str(e)}", ephemeral=True)

    # Enhanced Interactive Roleplay Command
    @app_commands.command(name="roleplay", description="🎭 Interactive AI roleplay with chat history and character persistence")
    @app_commands.describe(
        character="Character you want to roleplay as (e.g., 'wise wizard', 'space pirate')",
        scenario="Starting scenario or situation",
        style="Roleplay style (optional)"
    )
    @app_commands.choices(style=[
        app_commands.Choice(name="🏰 Fantasy Adventure", value="fantasy"),
        app_commands.Choice(name="🚀 Sci-Fi Space", value="scifi"),
        app_commands.Choice(name="🏫 Modern Day", value="modern"),
        app_commands.Choice(name="🕵️ Mystery/Detective", value="mystery"),
        app_commands.Choice(name="😄 Comedy/Funny", value="comedy"),
        app_commands.Choice(name="🎨 Creative/Artistic", value="creative")
    ])
    async def roleplay(self, interaction: discord.Interaction, character: str, scenario: str, style: str = "fantasy"):
        await interaction.response.defer()

        try:
            # Get recent channel messages for context
            channel_history = []
            try:
                async for message in interaction.channel.history(limit=10):
                    if not message.author.bot and len(message.content) > 0:
                        channel_history.append(f"{message.author.display_name}: {message.content[:100]}")
            except:
                pass

            # Build enhanced prompt with context
            style_prompts = {
                "fantasy": "magical medieval fantasy world with dragons, magic, and kingdoms",
                "scifi": "futuristic space setting with advanced technology and alien worlds", 
                "modern": "contemporary modern-day setting with realistic scenarios",
                "mystery": "mysterious detective story with clues and puzzles to solve",
                "comedy": "humorous and funny situation with light-hearted comedy",
                "creative": "unique and artistic scenario that breaks traditional boundaries"
            }

            context_text = ""
            if channel_history:
                context_text = f"\n\nRecent channel context (for reference): {' | '.join(reversed(channel_history[-3:]))}"

            prompt = f"""You are an interactive roleplay AI assistant. Create an engaging roleplay scenario and respond as both narrator and NPCs.

ROLEPLAY SETUP:
- User's Character: {character}
- Scenario: {scenario}
- Style: {style_prompts.get(style, 'fantasy adventure')}
- Setting: {style_prompts[style]}

INSTRUCTIONS:
- Start the scenario by setting the scene and describing what {character} sees/encounters
- Include 2-3 interactive choices or questions for the user to respond to
- Keep responses engaging, descriptive but not too long (under 1500 chars)
- Make it feel like a real interactive story where the user's choices matter
- Include some NPCs or characters they can interact with
- End with a clear prompt for what the user should do next{context_text}

Create an immersive opening scene:"""

            # Call Gemini AI
            import google.generativeai as genai
            
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                embed = discord.Embed(
                    title="❌ **AI Service Unavailable**",
                    description="🤖 The roleplay AI is currently offline. Please contact an administrator!",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(prompt)
            
            if response.text:
                # Create interactive roleplay embed
                embed = discord.Embed(
                    title=f"🎭 **Interactive Roleplay Started!**",
                    description=response.text,
                    color=0x7c3aed,
                    timestamp=datetime.now()
                )
                
                embed.add_field(name="🎭 **Your Character**", value=f"🎭 {character}", inline=True)
                embed.add_field(name="🌍 **Setting**", value=f"📍 {style_prompts[style].title()}", inline=True)
                embed.add_field(name="🎯 **Scenario**", value=f"🎯 {scenario}", inline=True)
                
                embed.add_field(
                    name="🎮 **How to Continue**",
                    value="Click the **'Continue Adventure'** button below to type your character's next action!\n🎭 The AI will respond to your actions and continue the story.",
                    inline=False
                )
                
                embed.set_author(name=f"Roleplay Master for {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text="🎮 Interactive Roleplay System • Use the button to continue!")
                
                # Create view with continue button
                view = RoleplayView(character, style)
                await interaction.followup.send(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    title="❌ **AI Response Error**",
                    description="The AI couldn't create your adventure. Please try again.",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ **Roleplay Error**",
                description="Failed to start roleplay session. Please try again.",
                color=0xff6b6b
            )
            embed.add_field(name="🔍 Error Details", value=f"```{str(e)[:100]}```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="sync", description="Force sync all slash commands (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        """Force sync all slash commands - Admin only"""
        if not (interaction.user.guild_permissions.administrator or has_special_permissions(interaction)):
            await interaction.response.send_message("❌ You need administrator permissions or the special admin role to use this command!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Clear existing commands
            self.bot.tree.clear_commands(guild=None)
            await asyncio.sleep(2)
            
            # Sync to current guild first (faster)
            guild = discord.Object(id=interaction.guild.id)
            synced_guild = await self.bot.tree.sync(guild=guild)
            
            # Sync globally
            synced_global = await self.bot.tree.sync()
            
            embed = discord.Embed(
                title="✅ **Commands Synced Successfully!**",
                description="All slash commands have been force synced.",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 **Sync Results**",
                value=f"**Guild Sync:** {len(synced_guild)} commands\n**Global Sync:** {len(synced_global)} commands",
                inline=False
            )
            
            embed.add_field(
                name="⏰ **Availability**",
                value="• **Guild commands:** Available immediately\n• **Global commands:** May take up to 1 hour",
                inline=False
            )
            
            # List new commands
            tree_commands = [cmd.name for cmd in self.bot.tree.get_commands()]
            if tree_commands:
                commands_text = ", ".join(tree_commands[:20])  # Limit to prevent overflow
                if len(tree_commands) > 20:
                    commands_text += f" and {len(tree_commands) - 20} more..."
                
                embed.add_field(
                    name="🔧 **Available Commands**",
                    value=f"`{commands_text}`",
                    inline=False
                )
            
            embed.set_footer(text="🎯 Command synchronization complete")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Sync Failed**",
                description="Failed to sync commands. Please try again.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔍 **Error Details**",
                value=f"```{str(e)[:200]}```",
                inline=False
            )
            await interaction.followup.send(embed=error_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
