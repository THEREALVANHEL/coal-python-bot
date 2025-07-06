import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

import google.generativeai as genai

# Config
GUILD_ID = 1370009417726169250

MODERATOR_ROLES = ["Moderator 🚨🚓", "🚨 Lead moderator"]
FOOTER_TXT = "VANHELISMYSENSEI"

# Permission check helper
def has_moderator_role(interaction: discord.Interaction) -> bool:
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
        print("[Moderation] Loaded successfully.")

    @app_commands.command(name="addxp", description="Add XP to a user (Admin only)")
    @app_commands.describe(user="User to give XP to", amount="Amount of XP to add")
    @app_commands.default_permissions(administrator=True)
    async def addxp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Add XP to a user"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can use this command!", ephemeral=True)
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
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can use this command!", ephemeral=True)
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
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need 'Manage Messages' permission to use this command!", ephemeral=True)
            return

        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            deleted = await interaction.channel.purge(limit=amount)
            
            embed = discord.Embed(
                title="🗑️ Messages Cleared",
                description=f"Successfully deleted **{len(deleted)}** messages",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=FOOTER_TXT)

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

    @app_commands.command(name="checkwarnlist", description="📋 Check warnings for a user")
    @app_commands.describe(user="User to check warnings for")
    async def check_warn_list(self, interaction: discord.Interaction, user: discord.Member):
        if not has_moderator_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

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
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
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
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You need 'Manage Roles' permission to use this command!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Get user data from database
            user_data = db.get_user_data(user.id)
            level = user_data.get('level', 0)
            cookies = user_data.get('cookies', 0)

            # Define role mappings (you can adjust these)
            level_roles = {
                10: "Level 10",
                25: "Level 25", 
                50: "Level 50",
                75: "Level 75",
                100: "Level 100"
            }

            cookie_roles = {
                100: "Cookie Collector",
                500: "Cookie Enthusiast",
                1000: "Cookie Master",
                2500: "Cookie Legend"
            }

            roles_added = []
            roles_removed = []

            # Update level roles
            for required_level, role_name in level_roles.items():
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if role:
                    if level >= required_level and role not in user.roles:
                        await user.add_roles(role)
                        roles_added.append(role_name)
                    elif level < required_level and role in user.roles:
                        await user.remove_roles(role)
                        roles_removed.append(role_name)

            # Update cookie roles
            for required_cookies, role_name in cookie_roles.items():
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if role:
                    if cookies >= required_cookies and role not in user.roles:
                        await user.add_roles(role)
                        roles_added.append(role_name)
                    elif cookies < required_cookies and role in user.roles:
                        await user.remove_roles(role)
                        roles_removed.append(role_name)

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
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can use this command!", ephemeral=True)
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
