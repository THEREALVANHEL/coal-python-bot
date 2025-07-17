import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
from datetime import datetime
import os, sys
import asyncio
import time

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# Define the 4 staff roles that can manage tickets
STAFF_ROLES = ["forgotten one", "overseer", "lead moderator", "moderator"]

class SimpleTicketControls(View):
    """Simple Ticket Control Panel - Claim and Close only"""
    def __init__(self, creator_id: int, original_name: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.claimed_by = None
        self.original_name = original_name
        self.last_claim_time = {}
        self.claim_cooldown = 2  # 2 second cooldown
        
    def _is_staff(self, user) -> bool:
        """Check if user is authorized staff (the 4 roles)"""
        if user.guild_permissions.administrator:
            return True
        
        # Check for special admin role
        if hasattr(user, 'roles') and user.roles:
            if any(role.id == 1376574861333495910 for role in user.roles):
                return True
        
        # Check the 4 staff roles
        user_roles = [role.name.lower().strip() for role in user.roles]
        
        for user_role in user_roles:
            for staff_role in STAFF_ROLES:
                if staff_role in user_role or user_role == staff_role:
                    return True
                    
        return False

    @discord.ui.button(label="🔴 Claim Ticket", style=discord.ButtonStyle.danger, emoji="🔴")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can claim tickets!", 
                ephemeral=True
            )
            return
            
        # Check cooldown
        user_id = interaction.user.id
        current_time = time.time()
        if user_id in self.last_claim_time:
            time_left = self.claim_cooldown - (current_time - self.last_claim_time[user_id])
            if time_left > 0:
                await interaction.response.send_message(
                    f"⏰ Please wait {time_left:.1f} seconds before claiming again.", 
                    ephemeral=True
                )
                return
        
        self.last_claim_time[user_id] = current_time
        
        # Update claimed status (transferable)
        old_claimed_by = self.claimed_by
        self.claimed_by = interaction.user
        
        # Update button to green
        button.label = f"🟢 Claimed by {interaction.user.display_name}"
        button.style = discord.ButtonStyle.success
        button.emoji = "🟢"
        
        # Change channel name
        try:
            new_name = f"🟢{interaction.user.display_name.lower()}"
            await interaction.channel.edit(name=new_name)
        except:
            pass
        
        # Send claim message
        if old_claimed_by:
            claim_msg = f"🔄 **Ticket transferred** from {old_claimed_by.mention} to {interaction.user.mention}"
        else:
            claim_msg = f"🟢 **Ticket claimed** by {interaction.user.mention}"
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(claim_msg)

    @discord.ui.button(label="🔐 Close Ticket", style=discord.ButtonStyle.secondary, emoji="🔐")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can close tickets!", 
                ephemeral=True
            )
            return
            
        # Send closing message
        await interaction.response.send_message(
            f"🔐 **Ticket closed** by {interaction.user.mention}\n"
            f"**Channel will be deleted in 5 seconds...**"
        )
        
        await asyncio.sleep(5)
        
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as e:
            print(f"Error deleting ticket channel: {e}")

class SimpleTicketButton(View):
    """Simple Ticket Creation Button"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        
        # Find or create ticket category
        category = None
        for cat in guild.categories:
            if "ticket" in cat.name.lower():
                category = cat
                break
        
        if not category:
            try:
                category = await guild.create_category("🎫 Tickets")
            except:
                pass
        
        # Create channel name
        channel_name = f"{user.display_name.lower()}ticket"
        
        try:
            # Create the ticket channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(
                    view_channel=True, 
                    send_messages=True, 
                    read_message_history=True
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True, 
                    send_messages=True, 
                    manage_messages=True
                )
            }
            
            # Add staff role permissions
            staff_roles_found = []
            for role in guild.roles:
                if any(staff_name in role.name.lower() for staff_name in STAFF_ROLES):
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        manage_messages=True
                    )
                    staff_roles_found.append(role)
            
            channel = await guild.create_text_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Support ticket | Creator: {user}"
            )
            
            # Create simple ticket embed
            ticket_embed = discord.Embed(
                title="🎫 Support Ticket",
                description=f"**Creator:** {user.mention}\n"
                           f"**Created:** <t:{int(time.time())}:F>\n\n"
                           f"Please describe your issue and wait for staff to help you.",
                color=0xff0000
            )
            
            # Create control panel
            control_panel = SimpleTicketControls(
                creator_id=user.id,
                original_name=channel_name
            )
            
            # Send welcome message to ticket channel
            welcome_msg = await channel.send(
                f"👋 {user.mention} Welcome to your support ticket!\n"
                f"📋 Please describe your issue.\n"
                f"⏰ Staff will help you shortly.",
                embed=ticket_embed,
                view=control_panel
            )
            
            # Pin the welcome message
            try:
                await welcome_msg.pin()
            except:
                pass
            
            # Ping the 4 staff roles
            if staff_roles_found:
                staff_pings = [role.mention for role in staff_roles_found]
                await channel.send(
                    f"🔔 **New Ticket Alert**\n"
                    f"{' '.join(staff_pings)}\n"
                    f"New ticket requires assistance!"
                )
            
            # Respond to user
            await interaction.response.send_message(
                f"✅ **Ticket created!** {channel.mention}", 
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ **Error creating ticket:** {str(e)}", 
                ephemeral=True
            )

class SimpleTickets(commands.Cog):
    """Simple Ticket System"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="ticket-panel", description="🎫 Create simple ticket panel")
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="**Need help?** Click the button below to create a support ticket.\n\n"
                       "**What happens:**\n"
                       "• Creates a private channel for you\n"
                       "• Staff will be notified automatically\n"
                       "• You can discuss your issue privately\n\n"
                       "**Please be patient** - staff will help you as soon as possible!",
            color=0x7289da
        )
        
        embed.set_footer(text="🎫 Simple Ticket System")
        
        view = SimpleTicketButton()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(SimpleTickets(bot))