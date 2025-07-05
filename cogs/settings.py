import discord
from discord.ext import commands
from discord import app_commands
import os, sys
from datetime import datetime

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250

class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Settings] Loaded successfully.")

    @app_commands.command(name="setup", description="Comprehensive server setup for all bot functions")
    @app_commands.describe(
        function="The function to set the channel for",
        channel="The channel to set"
    )
    @app_commands.choices(function=[
        app_commands.Choice(name="Level Up Announcements", value="levelup"),
        app_commands.Choice(name="Welcome Messages", value="welcome"),
        app_commands.Choice(name="Goodbye Messages", value="goodbye"),
        app_commands.Choice(name="Starboard", value="starboard"),
        app_commands.Choice(name="Mod Logs", value="modlog"),
        app_commands.Choice(name="Suggestion Channel", value="suggest")
    ])
    async def setup(self, interaction: discord.Interaction, function: str, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command!", ephemeral=True)
            return

        try:
            db.set_guild_setting(interaction.guild.id, f"{function}_channel", channel.id)
            
            # Function descriptions
            descriptions = {
                "levelup": "Level up announcements will be sent here when users reach new levels",
                "welcome": "Welcome messages will be sent here when new members join",
                "goodbye": "Goodbye messages will be sent here when members leave",
                "starboard": "Starred messages will be posted here when they reach the threshold",
                "modlog": "All moderation actions and server events will be logged here",
                "suggest": "User suggestions will be automatically forwarded to this channel"
            }
            
            embed = discord.Embed(
                title="⚙️ Setup Complete!",
                description=f"**{function.title()} Channel** configured successfully!",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="📍 Channel", value=channel.mention, inline=True)
            embed.add_field(name="🔧 Function", value=function.title(), inline=True)
            embed.add_field(name="📝 Description", value=descriptions.get(function, "Channel configured"), inline=False)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="Use /viewsettings to see all current configurations")
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting up channel: {str(e)}", ephemeral=True)

    @app_commands.command(name="setchannel", description="Set a channel for specific bot functions (legacy command)")
    @app_commands.describe(
        function="The function to set the channel for",
        channel="The channel to set"
    )
    @app_commands.choices(function=[
        app_commands.Choice(name="Level Up Announcements", value="levelup"),
        app_commands.Choice(name="Welcome Messages", value="welcome"),
        app_commands.Choice(name="Goodbye Messages", value="goodbye"),
        app_commands.Choice(name="Starboard", value="starboard"),
        app_commands.Choice(name="Mod Logs", value="modlog"),
        app_commands.Choice(name="Suggestion Channel", value="suggest")
    ])
    async def setchannel(self, interaction: discord.Interaction, function: str, channel: discord.TextChannel):
        # Redirect to setup command
        await self.setup(interaction, function, channel)

    @app_commands.command(name="starboard", description="Configure the starboard settings")
    @app_commands.describe(
        action="Action to perform",
        value="Value for the setting"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Set Star Threshold", value="threshold"),
        app_commands.Choice(name="Toggle Starboard", value="toggle"),
        app_commands.Choice(name="Set Starboard Channel", value="channel")
    ])
    async def starboard(self, interaction: discord.Interaction, action: str, value: str = None):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command!", ephemeral=True)
            return

        try:
            if action == "threshold":
                if not value or not value.isdigit():
                    await interaction.response.send_message("❌ Please provide a valid number for the threshold!", ephemeral=True)
                    return
                
                threshold = int(value)
                if threshold < 1 or threshold > 50:
                    await interaction.response.send_message("❌ Threshold must be between 1 and 50!", ephemeral=True)
                    return
                
                db.set_guild_setting(interaction.guild.id, "starboard_threshold", threshold)
                
                embed = discord.Embed(
                    title="⭐ Starboard Threshold Updated",
                    description=f"Messages now need **{threshold}** ⭐ reactions to be added to starboard",
                    color=0xffd700,
                    timestamp=datetime.now()
                )
                
            elif action == "toggle":
                current = db.get_guild_setting(interaction.guild.id, "starboard_enabled", False)
                new_state = not current
                db.set_guild_setting(interaction.guild.id, "starboard_enabled", new_state)
                
                embed = discord.Embed(
                    title="⭐ Starboard Toggled",
                    description=f"Starboard is now **{'enabled' if new_state else 'disabled'}**",
                    color=0x00ff00 if new_state else 0xff0000,
                    timestamp=datetime.now()
                )
                
                if new_state:
                    embed.add_field(
                        name="📝 Next Steps", 
                        value="Don't forget to set a starboard channel using `/setup starboard #channel`",
                        inline=False
                    )
                
            elif action == "channel":
                await interaction.response.send_message(
                    "ℹ️ Use `/setup starboard #your-channel` to set the starboard channel.",
                    ephemeral=True
                )
                return
            
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error configuring starboard: {str(e)}", ephemeral=True)

    @app_commands.command(name="viewsettings", description="View current server settings and configuration")
    async def viewsettings(self, interaction: discord.Interaction):
        try:
            guild_id = interaction.guild.id
            
            embed = discord.Embed(
                title="⚙️ Server Configuration",
                description="Current bot settings for this server",
                color=0x7289da,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            # Channel settings
            channels = {
                "levelup": "🎉 Level Up",
                "welcome": "👋 Welcome", 
                "goodbye": "👋 Goodbye",
                "starboard": "⭐ Starboard",
                "modlog": "📋 Mod Log",
                "suggest": "💡 Suggestions"
            }
            channel_settings = []
            for key, name in channels.items():
                channel_id = db.get_guild_setting(guild_id, f"{key}_channel", None)
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    channel_text = channel.mention if channel else f"<#{channel_id}> (deleted)"
                else:
                    channel_text = "Not set"
                channel_settings.append(f"**{name}:** {channel_text}")
            
            embed.add_field(name="📁 Channel Configuration", value="\n".join(channel_settings), inline=False)
            
            # Starboard settings
            starboard_enabled = db.get_guild_setting(guild_id, "starboard_enabled", False)
            starboard_threshold = db.get_guild_setting(guild_id, "starboard_threshold", 5)
            
            starboard_info = [
                f"**Status:** {'✅ Enabled' if starboard_enabled else '❌ Disabled'}",
                f"**Threshold:** {starboard_threshold} ⭐"
            ]
            
            embed.add_field(name="⭐ Starboard Settings", value="\n".join(starboard_info), inline=False)
            
            # Setup tips
            not_configured = [name for key, name in channels.items() 
                            if not db.get_guild_setting(guild_id, f"{key}_channel", None)]
            
            if not_configured:
                embed.add_field(
                    name="💡 Setup Tips",
                    value=f"Consider configuring: {', '.join(not_configured)}\nUse `/setup <function> #channel` to configure them!",
                    inline=False
                )
            
            embed.set_footer(text="Use /setup to configure channels • Use /starboard to configure starboard")
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting settings: {str(e)}", ephemeral=True)

    @app_commands.command(name="quicksetup", description="Quick setup wizard for essential bot functions")
    async def quicksetup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command!", ephemeral=True)
            return

        class QuickSetupView(discord.ui.View):
            def __init__(self, bot):
                super().__init__(timeout=300)
                self.bot = bot
                self.configured = []

            @discord.ui.button(label="📋 Mod Logs", style=discord.ButtonStyle.primary)
            async def setup_modlog(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("modlog", "Mod Log"))

            @discord.ui.button(label="💡 Suggestions", style=discord.ButtonStyle.primary)
            async def setup_suggest(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("suggest", "Suggestions"))

            @discord.ui.button(label="🎉 Level Up", style=discord.ButtonStyle.secondary)
            async def setup_levelup(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("levelup", "Level Up"))

            @discord.ui.button(label="👋 Welcome", style=discord.ButtonStyle.secondary)
            async def setup_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("welcome", "Welcome"))

            @discord.ui.button(label="⭐ Starboard", style=discord.ButtonStyle.secondary)
            async def setup_starboard(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("starboard", "Starboard"))

        class ChannelModal(discord.ui.Modal):
            def __init__(self, function, display_name):
                super().__init__(title=f"Setup {display_name} Channel")
                self.function = function
                self.display_name = display_name

            channel_input = discord.ui.TextInput(
                label="Channel ID or Name",
                placeholder="Enter channel ID (e.g., 123456789) or #channel-name",
                min_length=1,
                max_length=100
            )

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    channel_text = self.channel_input.value.strip()
                    
                    # Try to find channel
                    channel = None
                    if channel_text.startswith('#'):
                        channel_name = channel_text[1:]
                        channel = discord.utils.get(interaction.guild.channels, name=channel_name)
                    elif channel_text.isdigit():
                        channel = interaction.guild.get_channel(int(channel_text))
                    else:
                        channel = discord.utils.get(interaction.guild.channels, name=channel_text)
                    
                    if not channel:
                        await interaction.response.send_message(f"❌ Channel '{channel_text}' not found!", ephemeral=True)
                        return
                    
                    if not isinstance(channel, discord.TextChannel):
                        await interaction.response.send_message("❌ Please select a text channel!", ephemeral=True)
                        return
                    
                    # Configure the channel
                    db.set_guild_setting(interaction.guild.id, f"{self.function}_channel", channel.id)
                    
                    embed = discord.Embed(
                        title=f"✅ {self.display_name} Configured!",
                        description=f"{self.display_name} channel set to {channel.mention}",
                        color=0x00ff00
                    )
                    
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

        embed = discord.Embed(
            title="🚀 Quick Setup Wizard",
            description="Click the buttons below to quickly configure essential bot functions!\n\n**Primary Functions (Recommended):**\n📋 **Mod Logs** - Track all server activity\n💡 **Suggestions** - User suggestion system\n\n**Optional Functions:**\n🎉 Level Up, 👋 Welcome, ⭐ Starboard",
            color=0x7289da
        )
        embed.set_footer(text="Each button will open a form to configure that function")
        
        view = QuickSetupView(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="resetsettings", description="Reset all server settings to default")
    async def resetsettings(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need 'Administrator' permission to use this command!", ephemeral=True)
            return

        # Confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.confirmed = False

            @discord.ui.button(label="⚠️ CONFIRM RESET", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    db.reset_guild_settings(interaction.guild.id)
                    
                    embed = discord.Embed(
                        title="🔄 Settings Reset Complete",
                        description="All server settings have been reset to default values",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="📝 Next Steps",
                        value="Use `/setup` or `/quicksetup` to reconfigure your bot settings",
                        inline=False
                    )
                    
                    await interaction.response.edit_message(embed=embed, view=None)
                    self.confirmed = True
                    
                except Exception as e:
                    await interaction.response.edit_message(
                        content=f"❌ Error resetting settings: {str(e)}", 
                        embed=None, 
                        view=None
                    )

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = discord.Embed(
                    title="❌ Reset Cancelled",
                    description="Server settings were not changed",
                    color=0xff0000
                )
                await interaction.response.edit_message(embed=embed, view=None)

        view = ConfirmView()
        embed = discord.Embed(
            title="⚠️ Confirm Settings Reset",
            description="This will reset ALL server settings to default values!\n\n**This will affect:**\n• All channel configurations\n• Starboard settings\n• All other bot preferences\n\n**This action cannot be undone!**",
            color=0xff9900
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
