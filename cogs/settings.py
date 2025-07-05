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

    @app_commands.command(name="setchannel", description="Set a channel for specific bot functions")
    @app_commands.describe(
        function="The function to set the channel for",
        channel="The channel to set"
    )
    @app_commands.choices(function=[
        app_commands.Choice(name="Level Up Announcements", value="levelup"),
        app_commands.Choice(name="Welcome Messages", value="welcome"),
        app_commands.Choice(name="Goodbye Messages", value="goodbye"),
        app_commands.Choice(name="Starboard", value="starboard"),
        app_commands.Choice(name="Mod Logs", value="modlog")
    ])
    async def setchannel(self, interaction: discord.Interaction, function: str, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need 'Manage Server' permission to use this command!", ephemeral=True)
            return

        try:
            db.set_guild_setting(interaction.guild.id, f"{function}_channel", channel.id)
            
            embed = discord.Embed(
                title="⚙️ Channel Setting Updated",
                description=f"**{function.title()}** channel set to {channel.mention}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting channel: {str(e)}", ephemeral=True)

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
                    color=0xffd700
                )
                
            elif action == "toggle":
                current = db.get_guild_setting(interaction.guild.id, "starboard_enabled", False)
                new_state = not current
                db.set_guild_setting(interaction.guild.id, "starboard_enabled", new_state)
                
                embed = discord.Embed(
                    title="⭐ Starboard Toggled",
                    description=f"Starboard is now **{'enabled' if new_state else 'disabled'}**",
                    color=0x00ff00 if new_state else 0xff0000
                )
                
            elif action == "channel":
                await interaction.response.send_message(
                    "ℹ️ Use `/setchannel function:Starboard channel:#your-channel` to set the starboard channel.",
                    ephemeral=True
                )
                return
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error configuring starboard: {str(e)}", ephemeral=True)

    @app_commands.command(name="viewsettings", description="View current server settings")
    async def viewsettings(self, interaction: discord.Interaction):
        try:
            guild_id = interaction.guild.id
            
            embed = discord.Embed(
                title="⚙️ Server Settings",
                color=0x7289da,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            # Channel settings
            channels = {
                "levelup": "Level Up",
                "welcome": "Welcome", 
                "goodbye": "Goodbye",
                "starboard": "Starboard",
                "modlog": "Mod Log"
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
            
            embed.add_field(name="📁 Channels", value="\n".join(channel_settings), inline=False)
            
            # Starboard settings
            starboard_enabled = db.get_guild_setting(guild_id, "starboard_enabled", False)
            starboard_threshold = db.get_guild_setting(guild_id, "starboard_threshold", 5)
            
            starboard_info = [
                f"**Enabled:** {'Yes' if starboard_enabled else 'No'}",
                f"**Threshold:** {starboard_threshold} ⭐"
            ]
            
            embed.add_field(name="⭐ Starboard", value="\n".join(starboard_info), inline=False)
            
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting settings: {str(e)}", ephemeral=True)

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

            @discord.ui.button(label="Confirm Reset", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    db.reset_guild_settings(interaction.guild.id)
                    
                    embed = discord.Embed(
                        title="🔄 Settings Reset",
                        description="All server settings have been reset to default values",
                        color=0x00ff00
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
            description="This will reset ALL server settings to default values. This action cannot be undone!",
            color=0xff9900
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
