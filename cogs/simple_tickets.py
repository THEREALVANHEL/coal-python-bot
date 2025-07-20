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

# Global dictionary to track active tickets per user
active_tickets = {}

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
            
        # Remove from active tickets tracking
        creator_id = self.creator_id
        if creator_id in active_tickets:
            del active_tickets[creator_id]
            
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
        
        # Check if user already has an active ticket
        if user.id in active_tickets:
            existing_channel = active_tickets[user.id]
            try:
                # Check if the existing channel still exists
                existing_channel_obj = guild.get_channel(existing_channel)
                if existing_channel_obj:
                    await interaction.response.send_message(
                        f"❌ **You already have an active ticket!** {existing_channel_obj.mention}\n"
                        f"Please use your existing ticket or ask staff to close it first.",
                        ephemeral=True
                    )
                    return
                else:
                    # Channel doesn't exist, remove from tracking
                    del active_tickets[user.id]
            except:
                # Error checking channel, remove from tracking
                del active_tickets[user.id]
        
        # Find or create ticket category
        category = None
        for cat in guild.categories:
            if "ticket" in cat.name.lower():
                category = cat
                break
        
        if not category:
            try:
                category = await guild.create_category("🎫 Tickets")
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ **Error creating ticket category:** {str(e)}", 
                    ephemeral=True
                )
                return
        
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
            
            # Track this ticket as active for the user
            active_tickets[user.id] = channel.id
            
            # Create enhanced ticket embed
            ticket_embed = discord.Embed(
                title="🎫 Support Ticket Created",
                description=f"**Welcome {user.mention}!**\n\n"
                           f"📋 **Please describe your issue in detail:**\n"
                           f"• What happened?\n"
                           f"• When did it occur?\n"
                           f"• Any error messages?\n"
                           f"• Screenshots if helpful\n\n"
                           f"⏰ **Staff will assist you shortly**\n"
                           f"🔄 **Ticket Status:** Waiting for staff",
                color=0x00ff00
            )
            ticket_embed.add_field(
                name="📅 Created",
                value=f"<t:{int(time.time())}:F>",
                inline=True
            )
            ticket_embed.add_field(
                name="👤 Creator",
                value=user.mention,
                inline=True
            )
            ticket_embed.add_field(
                name="🆔 Ticket ID",
                value=f"#{channel.id % 10000:04d}",
                inline=True
            )
            ticket_embed.set_footer(text="🎫 Simple & Efficient Ticket System")
            
            # Create control panel
            control_panel = SimpleTicketControls(
                creator_id=user.id,
                original_name=channel_name
            )
            
            # Send welcome message to ticket channel
            welcome_msg = await channel.send(
                f"👋 **Welcome to your support ticket!**\n"
                f"📝 Please provide details about your issue below.",
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
                    f"**New ticket requires assistance!**\n"
                    f"👤 **User:** {user.mention}\n"
                    f"📅 **Created:** <t:{int(time.time())}:R>"
                )
            
            # Respond to user with success message
            success_embed = discord.Embed(
                title="✅ Ticket Created Successfully!",
                description=f"Your support ticket has been created: {channel.mention}\n\n"
                           f"📋 **Next Steps:**\n"
                           f"• Go to your ticket channel\n"
                           f"• Describe your issue in detail\n"
                           f"• Wait for staff assistance\n\n"
                           f"⚠️ **Note:** You can only have one active ticket at a time.",
                color=0x00ff00
            )
            success_embed.set_footer(text="🎫 Simple Ticket System")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            # Remove from tracking if creation failed
            if user.id in active_tickets:
                del active_tickets[user.id]
                
            await interaction.response.send_message(
                f"❌ **Error creating ticket:** {str(e)}\n\n"
                f"Please try again or contact an administrator.",
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
                       "**How it works:**\n"
                       "• Creates a private channel just for you\n"
                       "• Staff will be notified automatically\n"
                       "• Discuss your issue privately with staff\n"
                       "• One ticket per user at a time\n\n"
                       "**Please be patient** - staff will help you as soon as possible!",
            color=0x7289da
        )
        embed.add_field(
            name="📋 Before Creating a Ticket",
            value="• Check if your question is already answered\n"
                  "• Have all relevant information ready\n"
                  "• Be specific about your issue\n"
                  "• Include any error messages or screenshots",
            inline=False
        )
        embed.add_field(
            name="⏰ Response Time",
            value="• Staff typically respond within 1-2 hours\n"
                  "• During busy times, it may take longer\n"
                  "• Please be patient and respectful",
            inline=False
        )
        embed.set_footer(text="🎫 Simple & Efficient Ticket System")
        
        view = SimpleTicketButton()
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="close-ticket", description="🔐 Close a ticket (Staff only)")
    async def close_ticket(self, interaction: discord.Interaction):
        """Close the current ticket channel"""
        # Check if user is staff
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can close tickets!", 
                ephemeral=True
            )
            return
        
        # Check if this is a ticket channel
        if not "ticket" in interaction.channel.name.lower():
            await interaction.response.send_message(
                "❌ This command can only be used in ticket channels!", 
                ephemeral=True
            )
            return
        
        # Find the ticket creator
        creator_id = None
        for user_id, channel_id in active_tickets.items():
            if channel_id == interaction.channel.id:
                creator_id = user_id
                break
        
        if creator_id:
            del active_tickets[creator_id]
        
        await interaction.response.send_message(
            f"🔐 **Ticket closed** by {interaction.user.mention}\n"
            f"**Channel will be deleted in 5 seconds...**"
        )
        
        await asyncio.sleep(5)
        
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error deleting channel: {str(e)}")
    
    def _is_staff(self, user) -> bool:
        """Check if user is authorized staff"""
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

async def setup(bot):
    await bot.add_cog(SimpleTickets(bot))