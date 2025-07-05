import discord
from discord.ext import commands
from discord import app_commands
import os, sys
from datetime import datetime

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Settings] ⚙️ Loaded successfully.")

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
                        value="Don't forget to set a starboard channel using `/quicksetup`",
                        inline=False
                    )
                
            elif action == "channel":
                await interaction.response.send_message(
                    "ℹ️ Use `/quicksetup` to set the starboard channel through our enhanced setup system.",
                    ephemeral=True
                )
                return
            
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error configuring starboard: {str(e)}", ephemeral=True)

    @app_commands.command(name="viewsettings", description="🔍 View current server settings and configuration")
    async def viewsettings(self, interaction: discord.Interaction):
        try:
            guild_id = interaction.guild.id
            
            embed = discord.Embed(
                title="⚙️ **Server Configuration**",
                description="Current bot settings for this server",
                color=0x7c3aed,
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
                "suggest": "💡 Suggestions",
                "ticket_category": "🎫 Tickets"
            }
            channel_settings = []
            for key, name in channels.items():
                if key == "ticket_category":
                    channel_id = db.get_server_settings(guild_id).get('ticket_category', None)
                else:
                    channel_id = db.get_guild_setting(guild_id, f"{key}_channel", None)
                
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    channel_text = channel.mention if channel else f"<#{channel_id}> (deleted)"
                else:
                    channel_text = "Not set"
                channel_settings.append(f"**{name}:** {channel_text}")
            
            embed.add_field(name="📁 **Channel Configuration**", value="\n".join(channel_settings), inline=False)
            
            # Starboard settings
            starboard_enabled = db.get_guild_setting(guild_id, "starboard_enabled", False)
            starboard_threshold = db.get_guild_setting(guild_id, "starboard_threshold", 5)
            
            starboard_info = [
                f"**Status:** {'✅ Enabled' if starboard_enabled else '❌ Disabled'}",
                f"**Threshold:** {starboard_threshold} ⭐"
            ]
            
            embed.add_field(name="⭐ **Starboard Settings**", value="\n".join(starboard_info), inline=False)
            
            # Ticket settings
            ticket_settings = db.get_server_settings(guild_id)
            support_roles = ticket_settings.get('ticket_support_roles', [])
            
            ticket_info = [
                f"**Category:** {'✅ Configured' if ticket_settings.get('ticket_category') else '❌ Not set'}",
                f"**Support Roles:** {len(support_roles)} configured"
            ]
            
            embed.add_field(name="🎫 **Ticket System**", value="\n".join(ticket_info), inline=False)
            
            # Setup tips
            not_configured = []
            for key, name in channels.items():
                if key == "ticket_category":
                    if not ticket_settings.get('ticket_category'):
                        not_configured.append(name)
                else:
                    if not db.get_guild_setting(guild_id, f"{key}_channel", None):
                        not_configured.append(name)
            
            if not_configured:
                embed.add_field(
                    name="💡 **Setup Suggestions**",
                    value=f"Consider configuring: {', '.join(not_configured)}\nUse `/quicksetup` to configure them quickly!",
                    inline=False
                )
            
            embed.set_footer(text="✨ Use /quicksetup for easy configuration • /starboard for starboard settings")
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting settings: {str(e)}", ephemeral=True)

    @app_commands.command(name="quicksetup", description="🚀 Enhanced setup wizard for all bot functions")
    async def quicksetup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command!", ephemeral=True)
            return

        class QuickSetupView(discord.ui.View):
            def __init__(self, bot):
                super().__init__(timeout=300)
                self.bot = bot

            @discord.ui.button(label="📋 Mod Logs", style=discord.ButtonStyle.primary, emoji="📋")
            async def setup_modlog(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("modlog", "Mod Log"))

            @discord.ui.button(label="💡 Suggestions", style=discord.ButtonStyle.primary, emoji="💡")
            async def setup_suggest(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("suggest", "Suggestions"))

            @discord.ui.button(label="🎫 Ticket Category", style=discord.ButtonStyle.primary, emoji="🎫")
            async def setup_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(TicketCategoryModal())

            @discord.ui.button(label="🎉 Level Up", style=discord.ButtonStyle.secondary, emoji="🎉")
            async def setup_levelup(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("levelup", "Level Up"))

            @discord.ui.button(label="👋 Welcome", style=discord.ButtonStyle.secondary, emoji="👋")
            async def setup_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("welcome", "Welcome"))

            @discord.ui.button(label="⭐ Starboard", style=discord.ButtonStyle.secondary, emoji="⭐")
            async def setup_starboard(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(ChannelModal("starboard", "Starboard"))

        class ChannelModal(discord.ui.Modal):
            def __init__(self, function, display_name):
                super().__init__(title=f"🔧 Setup {display_name} Channel")
                self.function = function
                self.display_name = display_name

            channel_input = discord.ui.TextInput(
                label="📍 Channel ID or Name",
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
                        embed = discord.Embed(
                            title="❌ Channel Not Found",
                            description=f"Channel '{channel_text}' not found!",
                            color=0xff6b6b
                        )
                        embed.add_field(
                            name="💡 Tip",
                            value="Use channel ID or #channel-name format",
                            inline=False
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    
                    if not isinstance(channel, discord.TextChannel):
                        await interaction.response.send_message("❌ Please select a text channel!", ephemeral=True)
                        return
                    
                    # Configure the channel
                    db.set_guild_setting(interaction.guild.id, f"{self.function}_channel", channel.id)
                    
                    embed = discord.Embed(
                        title=f"✅ **{self.display_name} Configured!**",
                        description=f"{self.display_name} channel set to {channel.mention}",
                        color=0x00d4aa,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text="✨ Configuration saved successfully!")
                    
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

        class TicketCategoryModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="🎫 Setup Ticket System")

            category_input = discord.ui.TextInput(
                label="📂 Category ID or Name",
                placeholder="Enter category ID or name where ticket channels will be created",
                min_length=1,
                max_length=100
            )

            support_roles_input = discord.ui.TextInput(
                label="👥 Support Role IDs (Optional)",
                placeholder="Enter role IDs separated by commas (e.g., 123456789, 987654321)",
                required=False,
                max_length=500
            )

            async def on_submit(self, interaction: discord.Interaction):
                try:
                    category_text = self.category_input.value.strip()
                    
                    # Find category
                    category = None
                    if category_text.isdigit():
                        category = interaction.guild.get_channel(int(category_text))
                    else:
                        category = discord.utils.get(interaction.guild.categories, name=category_text)
                    
                    if not category or not isinstance(category, discord.CategoryChannel):
                        await interaction.response.send_message("❌ Category not found! Please provide a valid category channel.", ephemeral=True)
                        return
                    
                    # Parse support roles
                    support_role_ids = []
                    if self.support_roles_input.value:
                        for role_id_str in self.support_roles_input.value.split(','):
                            role_id_str = role_id_str.strip()
                            if role_id_str.isdigit():
                                role_id = int(role_id_str)
                                role = interaction.guild.get_role(role_id)
                                if role:
                                    support_role_ids.append(role_id)
                    
                    # Save settings
                    db.update_server_setting(interaction.guild.id, 'ticket_category', category.id)
                    db.update_server_setting(interaction.guild.id, 'ticket_support_roles', support_role_ids)
                    
                    embed = discord.Embed(
                        title="✅ **Ticket System Configured!**",
                        description=f"Ticket system has been set up successfully!",
                        color=0x00d4aa,
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="� Ticket Category",
                        value=f"{category.mention} ({category.name})",
                        inline=False
                    )
                    embed.add_field(
                        name="👥 Support Roles",
                        value=f"{len(support_role_ids)} role(s) configured" if support_role_ids else "None configured",
                        inline=False
                    )
                    embed.add_field(
                        name="🚀 Next Step",
                        value="Use `/setuptickets` to create the ticket interface!",
                        inline=False
                    )
                    embed.set_footer(text="🎫 Ticket system ready to use!")
                    
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

        embed = discord.Embed(
            title="🚀 **Enhanced Quick Setup Wizard**",
            description="Configure all essential bot functions with just a few clicks!\n\n" +
                       "**🎯 Essential Functions:**\n" +
                       "📋 **Mod Logs** - Complete server activity tracking\n" +
                       "💡 **Suggestions** - Community feedback system\n" +
                       "🎫 **Ticket System** - Professional support center\n\n" +
                       "**⭐ Optional Functions:**\n" +
                       "🎉 Level Up • 👋 Welcome • ⭐ Starboard",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="💡 **Pro Tip**",
            value="Configure essential functions first, then add optional ones based on your community needs!",
            inline=False
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="🔧 Click any button below to configure that function")
        
        view = QuickSetupView(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
