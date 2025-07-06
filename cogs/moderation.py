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

class RoleplayView(discord.ui.View):
    def __init__(self, character: str, style: str):
        super().__init__(timeout=1800)  # 30 minutes
        self.character = character
        self.style = style

    @discord.ui.button(label="🎲 Continue Adventure", style=discord.ButtonStyle.primary, emoji="🎲")
    async def continue_adventure(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🎭 **{interaction.user.display_name}** is continuing their adventure as **{self.character}**!\n\n" +
            "💬 Just type your next action or dialogue in the chat, and the AI will respond to continue the story! 🌟",
            ephemeral=True
        )

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
                embed.add_field(name="� Reason", value=reason, inline=False)
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
                embed.add_field(name="� Removal Reason", value=reason, inline=False)
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
                embed.add_field(
                    name="➕ **Roles Added**", 
                    value="🎉 " + "\n🎉 ".join(roles_added), 
                    inline=False
                )
            if roles_removed:
                embed.add_field(
                    name="➖ **Roles Removed**", 
                    value="🗑️ " + "\n🗑️ ".join(roles_removed), 
                    inline=False
                )
            if not roles_added and not roles_removed:
                embed.add_field(
                    name="✅ **Perfect Match!**", 
                    value="🎯 User already has all the appropriate roles for their level and cookies!", 
                    inline=False
                )
            
            # Add stats
            embed.add_field(
                name="📊 **Update Summary**",
                value=f"➕ Added: **{len(roles_added)}** roles\n➖ Removed: **{len(roles_removed)}** roles",
                inline=True
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
                
                embed.add_field(name="� **Your Character**", value=f"🎭 {character}", inline=True)
                embed.add_field(name="🌍 **Setting**", value=f"📍 {style_prompts[style].title()}", inline=True)
                embed.add_field(name="� **Scenario**", value=f"🎯 {scenario}", inline=True)
                
                embed.add_field(
                    name="� **How to Continue**",
                    value="💬 Simply type your response in this channel as your character!\n🎭 The AI will respond to your actions and continue the story.\n🔄 Use `/roleplay` again anytime to start a new adventure!",
                    inline=False
                )
                
                embed.set_author(name=f"Roleplay Master for {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text="✨ Interactive AI Roleplay • Your choices shape the story!")
                
                # Add continue button for easy interaction
                view = RoleplayView(character, style)
                await interaction.followup.send(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    title="❌ **Roleplay Creation Failed**",
                    description="🎭 Couldn't generate your roleplay scenario. Try different parameters!",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Roleplay Error**",
                description=f"🤖 Something went wrong: {str(e)[:200]}",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
