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

class ContinueTalkModal(discord.ui.Modal):
    def __init__(self, conversation_history: list):
        super().__init__(title="Continue talking with Bleky")
        self.conversation_history = conversation_history
        
        self.message_input = discord.ui.TextInput(
            label="What do you want to say to your nephew Bleky?",
            placeholder="Type your message here... Be natural, he's your nephew!",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        self.add_item(self.message_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            # Get recent channel messages for additional context
            channel_history = []
            try:
                async for message in interaction.channel.history(limit=5):
                    if not message.author.bot and len(message.content) > 0:
                        channel_history.append(f"{message.author.display_name}: {message.content[:100]}")
            except:
                pass

            user_message = self.message_input.value
            
            # Add user's message to conversation history
            self.conversation_history.append(f"Uncle/Aunt {interaction.user.display_name}: {user_message}")
            
            # Build conversation context (last 10 messages)
            recent_conversation = "\n".join(self.conversation_history[-10:])
            
            channel_context = ""
            if channel_history:
                channel_context = f"\n\nChannel context: {' | '.join(reversed(channel_history[-3:]))}"

            prompt = f"""You are Bleky, a fun-loving, energetic, and slightly mischievous nephew talking to your uncle/aunt. You're a real human teenager (around 16-17 years old) who loves gaming, memes, and hanging out. You have a close relationship with your uncle/aunt and feel comfortable being casual and playful with them.

PERSONALITY TRAITS:
- Enthusiastic and energetic
- Uses modern slang naturally (but not excessively)
- Playful and sometimes a bit cheeky
- Loves gaming, music, and technology
- Genuine care for family
- Sometimes asks for advice or help
- Can be dramatic about small things (typical teenager)
- Has inside jokes and references with uncle/aunt

CONVERSATION HISTORY:
{recent_conversation}

CURRENT MESSAGE FROM UNCLE/AUNT:
{user_message}

INSTRUCTIONS:
- Respond as Bleky would naturally respond to his uncle/aunt
- Keep it realistic and human-like
- Use casual language appropriate for family
- Reference the conversation history when relevant
- Be genuinely engaging and fun
- Keep response under 1500 characters
- Feel free to ask questions, share stories, or be playful
- React authentically to what they said{channel_context}

Respond as Bleky:"""

            # Call Gemini AI
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                embed = discord.Embed(
                    title="❌ **Bleky is Busy**",
                    description="🤖 Bleky can't talk right now! Try again later.",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(prompt)
            
            if response.text:
                # Add Bleky's response to conversation history
                self.conversation_history.append(f"Bleky: {response.text}")
                
                # Create response embed
                embed = discord.Embed(
                    title="💬 **Bleky Responds**",
                    description=response.text,
                    color=0x5865f2,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="💭 **You said**", 
                    value=f"*{user_message}*", 
                    inline=False
                )
                
                embed.add_field(
                    name="🎮 **Keep Chatting**",
                    value="Click the button below to continue your conversation with Bleky!",
                    inline=False
                )
                
                embed.set_author(
                    name=f"Chatting with Uncle/Aunt {interaction.user.display_name}", 
                    icon_url=interaction.user.display_avatar.url
                )
                embed.set_footer(text="🎯 Talk to Bleky • Your favorite nephew!")
                
                # Add the view again for continuous conversation
                view = TalkToBlekyView(self.conversation_history)
                await interaction.followup.send(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    title="❌ **Bleky Can't Respond**",
                    description="Bleky is having trouble responding right now. Try again!",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ **Connection Error**",
                description="Something went wrong while talking to Bleky. Please try again.",
                color=0xff6b6b
            )
            embed.add_field(name="🔍 Error Details", value=f"```{str(e)[:100]}```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

class TalkToBlekyView(discord.ui.View):
    def __init__(self, conversation_history: list = None):
        super().__init__(timeout=900)  # 15 minutes timeout to prevent expired interactions
        self.conversation_history = conversation_history or []

    @discord.ui.button(label="💬 Continue Talking", style=discord.ButtonStyle.primary, emoji="💬")
    async def continue_talking(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            modal = ContinueTalkModal(self.conversation_history)
            
            # Check if interaction is still valid
            if interaction.response.is_done():
                await interaction.followup.send("⏰ This conversation has expired. Please start a new one with `/talktobleky`", ephemeral=True)
            else:
                await interaction.response.send_modal(modal)
                
        except discord.errors.NotFound:
            # Interaction expired, ignore silently
            pass
        except Exception as e:
            print(f"Error in continue_talking: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ This conversation has expired. Please start a new one with `/talktobleky`", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="📱 Bleky Info", style=discord.ButtonStyle.secondary, emoji="📱")
    async def bleky_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = discord.Embed(
                title="📱 **About Your Nephew Bleky**",
                description="Get to know your favorite nephew better! 😄",
                color=0x5865f2
            )
            
            embed.add_field(
                name="🎮 **Interests**",
                value="• Gaming (especially competitive games)\n• Music and concerts\n• Technology and gadgets\n• Hanging out with friends\n• Memes and internet culture",
                inline=False
            )
            
            embed.add_field(
                name="💡 **What to Talk About**",
                value="• Ask about his day or school\n• Share family news or stories\n• Ask for tech help or advice\n• Talk about games or music\n• Just chat about anything!",
                inline=False
            )
            
            embed.add_field(
                name="😄 **His Personality**",
                value="• Energetic and fun-loving\n• Sometimes dramatic (he's a teenager!)\n• Loves inside jokes with family\n• Always up for a good conversation\n• Genuinely cares about family",
                inline=False
            )
            
            embed.add_field(
                name="🎯 **Tips for Great Conversations**",
                value="• Be natural and casual\n• Ask follow-up questions\n• Share your own stories\n• He remembers what you talked about!\n• Don't be afraid to be playful",
                inline=False
            )
            
            embed.set_footer(text="💬 Ready to chat with Bleky?")
            
            # Check if interaction is still valid
            if interaction.response.is_done():
                # Interaction already responded to, use followup
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                # Normal response
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except discord.errors.NotFound:
            # Interaction expired, ignore silently
            pass
        except Exception as e:
            print(f"Error in bleky_info: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Something went wrong. Please try again.", ephemeral=True)
            except:
                pass

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

    # Enhanced Talk to Sensei - AI Mentor with Command Access & Banking Data
    @app_commands.command(name="talktosensei", description="💬 Chat with your wise sensei - he knows all commands and can help with banking!")
    async def talk_to_sensei(self, interaction: discord.Interaction, message: str = None):
        await interaction.response.defer()

        try:
            user_id = interaction.user.id
            user_data = db.get_user_data(user_id)
            
            # Get user's banking and stats data for context
            balance = user_data.get('coins', 0)
            bank_balance = user_data.get('bank_balance', 0)
            savings = user_data.get('savings_balance', 0)
            level = user_data.get('level', 1)
            xp = user_data.get('xp', 0)
            job_role = user_data.get('current_job', 'None')
            portfolio = user_data.get('portfolio', {})
            pets = user_data.get('pets', {})
            
            # Get recent conversation history
            conversation_key = f"sensei_conversation_{user_id}"
            conversation_history = db.get_user_data(user_id).get('sensei_conversation', [])
            
            # Available commands list for Bleky to reference
            commands_list = """
            AVAILABLE COMMANDS:
            💰 Economy: /balance, /shop, /inventory, /buy, /work, /daily, /coinflip, /slots
            🏦 Banking: /atm, /deposit, /withdraw, /transfer, /savings, /loan
            📈 Stocks: /stocks, /buy-stock, /sell-stock, /portfolio
            🐾 Pets: /pet, /feed-pet, /play-pet, /pet-status
            🎮 Games: /trivia, /wordchain, /rps, /spinwheel, /flip
            📊 Profile: /profile, /leaderboard, /updateroles
            🎫 Tickets: /ticket-panel (staff)
            🛡️ Moderation: /warn, /warnlist, /removewarnlist, /modclear (staff)
            🎉 Community: /suggest, /remind, /announce, /giveaway (staff)
            ⚙️ Admin: /addxp, /removexp, /addcoins, /removecoins, /quicksetup (admin)
            """
            
            # Create enhanced prompt with command knowledge and banking access
            if message:
                user_message = message
            else:
                user_message = "Hello Sensei! I seek your wisdom."
            
            # Add conversation history context
            history_context = ""
            if conversation_history:
                recent_history = conversation_history[-6:]  # Last 3 exchanges
                history_context = "\n\nPREVIOUS CONVERSATION:\n" + "\n".join(recent_history)
            
            prompt = f"""You are Sensei, a wise, knowledgeable, and patient mentor who's also a Discord bot master! You have years of experience and wisdom, and you have access to ALL the bot's commands and the student's account data.

YOUR PERSONALITY:
- Wise, patient, and deeply knowledgeable
- Master of all Discord bot commands and features
- Uses thoughtful, encouraging language
- Provides guidance with wisdom and insight
- Can explain complex concepts with clarity
- Loves to mentor and help others grow

YOUR SPECIAL ABILITIES:
- You know ALL bot commands and can explain them
- You can see user's banking, stats, and game data
- You can give personalized advice based on their progress
- You remember previous conversations
- You can help with bot setup and troubleshooting

USER'S CURRENT STATUS:
- Name: {interaction.user.display_name}
- Wallet: {balance:,} coins
- Bank: {bank_balance:,} coins  
- Savings: {savings:,} coins
- Level: {level} (XP: {xp:,})
- Job: {job_role}
- Stocks: {len(portfolio)} different stocks
- Pets: {len(pets)} pets

{commands_list}

USER MESSAGE: "{user_message}"

{history_context}

RESPONSE INSTRUCTIONS:
- Be genuinely helpful and human-like
- Reference their stats when relevant (like suggesting they save money if they have lots of coins)
- Recommend specific commands that would help them
- If they ask about commands, explain them clearly with examples
- Keep responses under 1800 characters
- Be encouraging about their progress
- Use emojis naturally but not excessively
- End with a question or suggestion to keep conversation going

Respond as Sensei:"""

            # Call Gemini AI
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                embed = discord.Embed(
                    title="❌ **Sensei is Unavailable**",
                    description="🤖 Sensei cannot provide guidance right now! The AI service isn't configured.",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(prompt)
            
            if response.text:
                response_text = response.text.strip()
                
                # Update conversation history
                conversation_history.append(f"You: {user_message}")
                conversation_history.append(f"Sensei: {response_text}")
                
                # Keep only last 20 messages (10 exchanges)
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]
                
                # Save conversation history
                user_data['sensei_conversation'] = conversation_history
                db.update_user_data(user_id, user_data)
                
                # Create response embed with user's stats
                embed = discord.Embed(
                    title="🧘 **Sensei - Your Wise Mentor**",
                    description=response_text,
                    color=0x5865f2,
                    timestamp=datetime.now()
                )
                
                # Add user stats sidebar
                embed.add_field(
                    name="📊 **Your Stats**",
                    value=f"💰 Wallet: {balance:,}\n🏦 Bank: {bank_balance:,}\n📈 Level: {level}\n👔 Job: {job_role}",
                    inline=True
                )
                
                # Add quick help
                embed.add_field(
                    name="🔧 **Quick Help**",
                    value="Ask me about:\n• Bot commands\n• Banking advice\n• Game strategies\n• Account management",
                    inline=True
                )
                
                embed.set_author(
                    name=f"Chatting with {interaction.user.display_name}", 
                    icon_url=interaction.user.display_avatar.url
                )
                embed.set_footer(text="🧘 Enhanced Sensei • Command Master • Wise Advisor")
                
                # Create continue conversation view
                class ContinueSenseiView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=300)  # 5 minutes
                    
                    @discord.ui.button(label="Continue Chat", emoji="💬", style=discord.ButtonStyle.primary)
                    async def continue_chat(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        if button_interaction.user.id != interaction.user.id:
                            await button_interaction.response.send_message("This isn't your conversation!", ephemeral=True)
                            return
                        
                        # Create modal for user input
                        class ChatModal(discord.ui.Modal, title="Continue conversation with Sensei"):
                            message_input = discord.ui.TextInput(
                                label="What wisdom do you seek from Sensei?",
                                placeholder="Ask about commands, banking, games, or seek guidance!",
                                max_length=500,
                                style=discord.TextStyle.paragraph
                            )
                            
                            async def on_submit(self, modal_interaction: discord.Interaction):
                                await modal_interaction.response.defer()
                                
                                # Call the same function recursively with the new message
                                await talk_to_sensei(interaction, self.message_input.value)
                        
                        await button_interaction.response.send_modal(ChatModal())
                    
                    @discord.ui.button(label="Command Help", emoji="❓", style=discord.ButtonStyle.secondary)
                    async def command_help(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        if button_interaction.user.id != interaction.user.id:
                            await button_interaction.response.send_message("This isn't your conversation!", ephemeral=True)
                            return
                        
                        help_embed = discord.Embed(
                            title="🧘 **Sensei's Command Wisdom**",
                            description="I have mastered all these commands and can guide you in their use!",
                            color=0x00ff00
                        )
                        
                        help_embed.add_field(
                            name="💰 **Economy & Banking**",
                            value="`/balance` `/shop` `/inventory` `/atm`\n`/deposit` `/withdraw` `/savings`",
                            inline=True
                        )
                        
                        help_embed.add_field(
                            name="🎮 **Games & Fun**",
                            value="`/trivia` `/wordchain` `/slots`\n`/coinflip` `/rps` `/spinwheel`",
                            inline=True
                        )
                        
                        help_embed.add_field(
                            name="📈 **Stocks & Pets**",
                            value="`/stocks` `/portfolio` `/pet`\n`/feed-pet` `/play-pet`",
                            inline=True
                        )
                        
                        help_embed.set_footer(text="🧘 Ask Sensei about any command for detailed guidance!")
                        await button_interaction.response.send_message(embed=help_embed, ephemeral=True)
                
                view = ContinueSenseiView()
                await interaction.followup.send(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    title="❌ **Sensei Cannot Respond**",
                    description="Sensei is having trouble right now. Please try again!",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ **Connection Error**",
                description="Something went wrong while trying to reach Sensei. Please try again.",
                color=0xff6b6b
            )
            embed.add_field(name="🔍 Error Details", value=f"```{str(e)[:100]}```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

    # New Ask Bleky Nephew Command - Simple AI Q&A with conversation history
    @app_commands.command(name="askblecknephew", description="🤖 Ask Bleky (your nephew) any question - he's got AI powers and remembers your chats!")
    async def ask_bleky_nephew(self, interaction: discord.Interaction, question: str = None):
        await interaction.response.defer()

        try:
            user_id = interaction.user.id
            user_data = db.get_user_data(user_id)
            
            # Get conversation history for this command
            conversation_history = user_data.get('bleky_nephew_conversation', [])
            
            # Create the question
            if question:
                user_question = question
            else:
                user_question = "Hey Bleky, what's up?"
            
            # Add conversation history context
            history_context = ""
            if conversation_history:
                recent_history = conversation_history[-10:]  # Last 5 exchanges
                history_context = "\n\nPREVIOUS CONVERSATION:\n" + "\n".join(recent_history)
            
            # Create AI prompt for Bleky Nephew
            prompt = f"""You are Bleky, a smart and helpful 16-year-old nephew who loves technology and helping people! You're energetic, friendly, and knowledgeable about many topics.

YOUR PERSONALITY:
- Young, enthusiastic, and tech-savvy
- Friendly and approachable
- Loves to help and answer questions
- Uses modern slang occasionally but stays helpful
- Curious and always learning
- Remembers previous conversations

USER'S QUESTION: "{user_question}"

{history_context}

RESPONSE INSTRUCTIONS:
- Answer the question helpfully and accurately
- Be friendly and conversational
- Keep responses under 1500 characters
- Use emojis naturally but not excessively
- If you don't know something, admit it honestly
- Ask follow-up questions to keep the conversation going
- Remember you're their nephew, so be warm and caring

Respond as Bleky:"""

            # Call Gemini AI
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                embed = discord.Embed(
                    title="❌ **Bleky is Offline**",
                    description="🤖 Your nephew Bleky can't answer right now! The AI service isn't configured.",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
                
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            response = model.generate_content(prompt)
            
            if response.text:
                response_text = response.text.strip()
                
                # Update conversation history
                conversation_history.append(f"You: {user_question}")
                conversation_history.append(f"Bleky: {response_text}")
                
                # Keep only last 20 messages (10 exchanges)
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]
                
                # Save conversation history
                user_data['bleky_nephew_conversation'] = conversation_history
                db.update_user_data(user_id, user_data)
                
                # Create response embed
                embed = discord.Embed(
                    title="🤖 **Bleky - Your Smart Nephew**",
                    description=response_text,
                    color=0x00d4ff,
                    timestamp=datetime.now()
                )
                
                embed.set_author(
                    name=f"Answering {interaction.user.display_name}'s question", 
                    icon_url=interaction.user.display_avatar.url
                )
                embed.set_footer(text="🤖 Ask Bleky Nephew • AI Powered • Conversation Memory")
                
                # Create continue conversation view
                class ContinueBlekyView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=300)  # 5 minutes
                    
                    @discord.ui.button(label="Continue Chat", emoji="💬", style=discord.ButtonStyle.primary)
                    async def continue_chat(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        if button_interaction.user.id != interaction.user.id:
                            await button_interaction.response.send_message("This isn't your conversation!", ephemeral=True)
                            return
                        
                        # Create modal for user input
                        class ChatModal(discord.ui.Modal, title="Continue chatting with Bleky"):
                            message_input = discord.ui.TextInput(
                                label="What do you want to ask Bleky?",
                                placeholder="Ask anything! I remember our conversation.",
                                max_length=500,
                                style=discord.TextStyle.paragraph
                            )
                            
                            async def on_submit(self, modal_interaction: discord.Interaction):
                                await modal_interaction.response.defer()
                                
                                # Call the same function recursively with the new message
                                await ask_bleky_nephew(interaction, self.message_input.value)
                        
                        await button_interaction.response.send_modal(ChatModal())
                    
                    @discord.ui.button(label="Clear History", emoji="🗑️", style=discord.ButtonStyle.secondary)
                    async def clear_history(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        if button_interaction.user.id != interaction.user.id:
                            await button_interaction.response.send_message("This isn't your conversation!", ephemeral=True)
                            return
                        
                        # Clear conversation history
                        user_data = db.get_user_data(user_id)
                        user_data['bleky_nephew_conversation'] = []
                        db.update_user_data(user_id, user_data)
                        
                        clear_embed = discord.Embed(
                            title="🗑️ **Conversation Cleared**",
                            description="Bleky's memory of your conversation has been cleared. Start fresh!",
                            color=0x00ff00
                        )
                        await button_interaction.response.send_message(embed=clear_embed, ephemeral=True)
                
                view = ContinueBlekyView()
                await interaction.followup.send(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    title="❌ **Bleky Can't Answer**",
                    description="Your nephew Bleky is having trouble right now. Please try again!",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ **Connection Error**",
                description="Something went wrong while trying to reach Bleky. Please try again.",
                color=0xff6b6b
            )
            embed.add_field(name="🔍 Error Details", value=f"```{str(e)[:100]}```", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
