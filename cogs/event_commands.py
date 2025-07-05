import discord
from discord.ext import commands
from discord import app_commands
import os, sys
from datetime import datetime

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

GUILD_ID = 1370009417726169250
HOST_ROLES = ["🦥 Overseer", "Forgotten one", "🚨 Lead moderator"]

def has_host_role(interaction: discord.Interaction) -> bool:
    user_roles = [role.name for role in interaction.user.roles]
    return any(role in HOST_ROLES for role in user_roles)

class JoinEventView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Event", style=discord.ButtonStyle.primary, emoji="🎮")
    async def join_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ You've joined the event! Check the event details above.", ephemeral=True)

class EventCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[EventCommands] Loaded successfully.")

    @app_commands.command(name="shout", description="Make the bot send a message to a specific channel (Host only)")
    @app_commands.describe(
        channel="Channel to send the message to",
        message="Message to send"
    )
    async def shout(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        if not has_host_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            # Create an embed for the shout
            embed = discord.Embed(
                title="📣 Announcement",
                description=message,
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"Sent from #{interaction.channel.name}")

            # Add join button for events
            view = JoinEventView()

            await channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Message sent to {channel.mention}!", ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error sending message: {str(e)}", ephemeral=True)
                @app_commands.command(name="gamelog", description="Log a game event or result, with image support (Host only)")
    @app_commands.describe(
        title="Event title",
        description="Event description",
        winner="Winner of the event (optional)",
        image="Image attachment (optional)"
    )
    async def gamelog(self, interaction: discord.Interaction, title: str, description: str, winner: discord.Member = None, image: discord.Attachment = None):
        if not has_host_role(interaction):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            embed = discord.Embed(
                title=f"🎮 {title}",
                description=description,
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

            if winner:
                embed.add_field(name="🏆 Winner", value=winner.mention, inline=False)

            if image:
                if image.content_type and image.content_type.startswith('image/'):
                    embed.set_image(url=image.url)
                else:
                    await interaction.response.send_message("❌ Please upload a valid image file!", ephemeral=True)
                    return

            embed.set_footer(text="Game Event Log")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating game log: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(EventCommands(bot))
