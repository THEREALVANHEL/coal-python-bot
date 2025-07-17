import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput, Select
from datetime import datetime, timedelta
import os, sys
import asyncio
import time
import random

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

# Define the 4 staff roles that can manage tickets
STAFF_ROLES = ["forgotten one", "overseer", "lead moderator", "moderator"]

class SuperTicketControlPanel(View):
    """🎫 Super Ticket Control Panel - Ultimate Ticket Management"""
    def __init__(self, creator_id: int = None, ticket_type: str = "general"):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.claimed_by = None
        self.ticket_type = ticket_type
        self.priority = "normal"
        self.last_claim_time = {}
        self.claim_cooldown = 3  # 3 second cooldown
        
    def _is_staff(self, user) -> bool:
        """Check if user is authorized staff (the 4 roles) - ENHANCED MATCHING"""
        if user.guild_permissions.administrator:
            return True
        
        # Check for special admin role
        if hasattr(user, 'roles') and user.roles:
            if any(role.id == 1376574861333495910 for role in user.roles):
                return True
        
        # Enhanced role matching for the 4 staff roles
        user_roles = [role.name.lower().strip() for role in user.roles]
        
        for user_role in user_roles:
            for staff_role in STAFF_ROLES:
                # Check exact match
                if user_role == staff_role:
                    return True
                # Check if staff role is contained in user role
                if staff_role in user_role:
                    return True
                # Check if user role contains all words of staff role
                if all(word in user_role for word in staff_role.split()):
                    return True
                    
        return False

    @discord.ui.button(label="🔒 Claim Ticket", style=discord.ButtonStyle.success, emoji="🔒")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ **Access Denied** - Only authorized staff can claim tickets!\n"
                f"**Required roles:** {', '.join(STAFF_ROLES)}", 
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
        
        if self.claimed_by:
            await interaction.response.send_message(
                f"❌ **Ticket already claimed** by {self.claimed_by.mention}!", 
                ephemeral=True
            )
            return
            
        self.claimed_by = interaction.user
        
        # Update button to show claimed status
        button.label = f"✅ Claimed by {interaction.user.display_name}"
        button.style = discord.ButtonStyle.primary
        button.disabled = True
        
        # Create claim embed
        claim_embed = discord.Embed(
            title="🎫 Ticket Claimed Successfully",
            description=f"**Staff Member:** {interaction.user.mention}\n"
                       f"**Ticket Type:** {self.ticket_type.title()}\n"
                       f"**Priority:** {self.priority.title()}\n"
                       f"**Claimed at:** <t:{int(time.time())}:F>",
            color=0x00ff00
        )
        
        # Send notification to channel
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=claim_embed)
        
        # Ping staff member
        await interaction.followup.send(f"🔔 {interaction.user.mention} - You have claimed this ticket!")

    @discord.ui.button(label="🔐 Close Ticket", style=discord.ButtonStyle.danger, emoji="🔐")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ **Access Denied** - Only authorized staff can close tickets!", 
                ephemeral=True
            )
            return
            
        # Close confirmation
        confirm_embed = discord.Embed(
            title="⚠️ Close Ticket Confirmation",
            description="Are you sure you want to close this ticket?\n"
                       "**This will delete the channel in 10 seconds!**",
            color=0xff6b6b
        )
        
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
        
        # Final closure message
        final_embed = discord.Embed(
            title="🎫 Ticket Closed",
            description=f"**Closed by:** {interaction.user.mention}\n"
                       f"**Closure time:** <t:{int(time.time())}:F>\n"
                       f"**Channel deletion:** <t:{int(time.time() + 10)}:R>",
            color=0xff0000
        )
        
        await interaction.followup.send(embed=final_embed)
        await asyncio.sleep(10)
        
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as e:
            print(f"Error deleting ticket channel: {e}")

    @discord.ui.button(label="🔒 Lock Channel", style=discord.ButtonStyle.secondary, emoji="🔒")
    async def lock_channel(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ **Access Denied** - Only authorized staff can lock channels!", 
                ephemeral=True
            )
            return
            
        # Lock the channel
        overwrites = interaction.channel.overwrites
        for target, overwrite in overwrites.items():
            if target == interaction.guild.default_role:
                overwrite.send_messages = False
                await interaction.channel.set_permissions(target, overwrite=overwrite)
                break
        
        lock_embed = discord.Embed(
            title="🔒 Channel Locked",
            description=f"**Locked by:** {interaction.user.mention}\n"
                       f"**Lock time:** <t:{int(time.time())}:F>",
            color=0xffa500
        )
        
        await interaction.response.send_message(embed=lock_embed)

    @discord.ui.button(label="🔓 Unlock Channel", style=discord.ButtonStyle.secondary, emoji="🔓")
    async def unlock_channel(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ **Access Denied** - Only authorized staff can unlock channels!", 
                ephemeral=True
            )
            return
            
        # Unlock the channel
        overwrites = interaction.channel.overwrites
        for target, overwrite in overwrites.items():
            if target == interaction.guild.default_role:
                overwrite.send_messages = True
                await interaction.channel.set_permissions(target, overwrite=overwrite)
                break
        
        unlock_embed = discord.Embed(
            title="🔓 Channel Unlocked",
            description=f"**Unlocked by:** {interaction.user.mention}\n"
                       f"**Unlock time:** <t:{int(time.time())}:F>",
            color=0x00ff00
        )
        
        await interaction.response.send_message(embed=unlock_embed)

    @discord.ui.button(label="⚠️ Quick Ban", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def quick_ban(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ **Access Denied** - Only authorized staff can use quick ban!", 
                ephemeral=True
            )
            return
            
        # Get the ticket creator
        if not self.creator_id:
            await interaction.response.send_message(
                "❌ Cannot determine ticket creator for ban action.", 
                ephemeral=True
            )
            return
            
        try:
            user_to_ban = interaction.guild.get_member(self.creator_id)
            if not user_to_ban:
                await interaction.response.send_message(
                    "❌ Ticket creator not found in server.", 
                    ephemeral=True
                )
                return
                
            # Create ban confirmation
            ban_embed = discord.Embed(
                title="⚠️ Quick Ban Confirmation",
                description=f"**Target:** {user_to_ban.mention} ({user_to_ban})\n"
                           f"**Staff:** {interaction.user.mention}\n"
                           f"**Reason:** Inappropriate ticket behavior\n\n"
                           f"**⚠️ This will ban the user immediately!**",
                color=0xff0000
            )
            
            class BanConfirmView(View):
                def __init__(self):
                    super().__init__(timeout=30)
                    
                @discord.ui.button(label="✅ Confirm Ban", style=discord.ButtonStyle.danger)
                async def confirm_ban(self, btn_interaction: discord.Interaction, btn: Button):
                    if btn_interaction.user.id != interaction.user.id:
                        await btn_interaction.response.send_message("Only the staff member who initiated can confirm!", ephemeral=True)
                        return
                        
                    try:
                        await user_to_ban.ban(reason=f"Quick ban by {interaction.user} - Inappropriate ticket behavior")
                        
                        success_embed = discord.Embed(
                            title="🔨 User Banned Successfully",
                            description=f"**Banned:** {user_to_ban}\n"
                                       f"**Staff:** {interaction.user.mention}\n"
                                       f"**Reason:** Inappropriate ticket behavior\n"
                                       f"**Time:** <t:{int(time.time())}:F>",
                            color=0xff0000
                        )
                        
                        await btn_interaction.response.edit_message(embed=success_embed, view=None)
                        
                        # Close ticket after ban
                        await asyncio.sleep(5)
                        try:
                            await interaction.channel.delete(reason=f"Ticket closed after ban by {interaction.user}")
                        except:
                            pass
                            
                    except Exception as e:
                        error_embed = discord.Embed(
                            title="❌ Ban Failed",
                            description=f"Failed to ban user: {str(e)}",
                            color=0xff0000
                        )
                        await btn_interaction.response.edit_message(embed=error_embed, view=None)
                
                @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
                async def cancel_ban(self, btn_interaction: discord.Interaction, btn: Button):
                    if btn_interaction.user.id != interaction.user.id:
                        await btn_interaction.response.send_message("Only the staff member who initiated can cancel!", ephemeral=True)
                        return
                        
                    cancel_embed = discord.Embed(
                        title="✅ Ban Cancelled",
                        description="Quick ban action was cancelled.",
                        color=0x00ff00
                    )
                    await btn_interaction.response.edit_message(embed=cancel_embed, view=None)
            
            ban_view = BanConfirmView()
            await interaction.response.send_message(embed=ban_embed, view=ban_view, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Quick Ban Error",
                description=f"An error occurred: {str(e)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class SuperTicketCreator(View):
    """🎫 Super Ticket Creation System"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.select(
        placeholder="🎯 Select your ticket type...",
        options=[
            discord.SelectOption(
                label="🆘 General Support",
                description="General help and questions",
                emoji="🆘",
                value="general"
            ),
            discord.SelectOption(
                label="🚨 Priority Support",
                description="Urgent issues requiring immediate attention",
                emoji="🚨", 
                value="priority"
            ),
            discord.SelectOption(
                label="🐛 Bug Report",
                description="Report bugs or technical issues",
                emoji="🐛",
                value="bug"
            ),
            discord.SelectOption(
                label="💡 Feature Request",
                description="Suggest new features or improvements",
                emoji="💡",
                value="feature"
            ),
            discord.SelectOption(
                label="🛠️ Technical Help",
                description="Programming, coding, or technical assistance",
                emoji="🛠️",
                value="technical"
            ),
            discord.SelectOption(
                label="📋 Other",
                description="Anything else not covered above",
                emoji="📋",
                value="other"
            )
        ]
    )
    async def ticket_type_select(self, interaction: discord.Interaction, select: Select):
        ticket_type = select.values[0]
        
        # Priority mapping
        priority_map = {
            "priority": "high",
            "bug": "medium", 
            "technical": "medium",
            "general": "normal",
            "feature": "low",
            "other": "normal"
        }
        
        priority = priority_map.get(ticket_type, "normal")
        
        # Create ticket channel
        guild = interaction.guild
        category = None
        
        # Try to find or create ticket category
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
        ticket_number = random.randint(1000, 9999)
        channel_name = f"ticket-{ticket_type}-{ticket_number}"
        
        try:
            # Create the ticket channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(
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
            for role in guild.roles:
                if any(staff_name in role.name.lower() for staff_name in STAFF_ROLES):
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        manage_messages=True
                    )
            
            channel = await guild.create_text_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Support ticket - {ticket_type.title()} | Creator: {interaction.user}"
            )
            
            # Create ticket embed
            ticket_embed = discord.Embed(
                title=f"🎫 New {ticket_type.title()} Ticket",
                description=f"**Creator:** {interaction.user.mention}\n"
                           f"**Type:** {ticket_type.title()}\n"
                           f"**Priority:** {priority.title()}\n"
                           f"**Created:** <t:{int(time.time())}:F>\n"
                           f"**Channel:** {channel.mention}",
                color=0x7289da
            )
            
            # Add priority-specific info
            if priority == "high":
                ticket_embed.add_field(
                    name="🚨 Priority Support",
                    value="• Staff will respond within 5 minutes\n• Urgent issues only\n• Please provide detailed information",
                    inline=False
                )
            elif priority == "medium":
                ticket_embed.add_field(
                    name="🔧 Technical Support", 
                    value="• Technical team will assist\n• Please describe the issue clearly\n• Include any error messages",
                    inline=False
                )
            
            ticket_embed.set_footer(text=f"Ticket ID: {ticket_number} | Use the buttons below for management")
            
            # Create control panel
            control_panel = SuperTicketControlPanel(
                creator_id=interaction.user.id,
                ticket_type=ticket_type
            )
            control_panel.priority = priority
            
            # Send welcome message to ticket channel
            welcome_msg = await channel.send(
                f"👋 Welcome {interaction.user.mention}!\n\n"
                f"🎫 **Your {ticket_type.title()} ticket has been created!**\n"
                f"📋 Please describe your issue in detail.\n"
                f"⏰ Staff will respond shortly based on priority level.\n"
                f"🔔 You will be notified when a staff member claims your ticket.",
                embed=ticket_embed,
                view=control_panel
            )
            
            # Pin the welcome message
            try:
                await welcome_msg.pin()
            except:
                pass
            
            # Respond to user
            response_embed = discord.Embed(
                title="✅ Ticket Created Successfully!",
                description=f"Your {ticket_type.title()} ticket has been created!\n"
                           f"**Channel:** {channel.mention}\n"
                           f"**Priority:** {priority.title()}\n"
                           f"**Ticket ID:** {ticket_number}",
                color=0x00ff00
            )
            
            await interaction.response.send_message(embed=response_embed, ephemeral=True)
            
            # Notify staff for high priority tickets
            if priority == "high":
                staff_ping = []
                for role in guild.roles:
                    if any(staff_name in role.name.lower() for staff_name in STAFF_ROLES):
                        staff_ping.append(role.mention)
                
                if staff_ping:
                    await channel.send(
                        f"🚨 **PRIORITY TICKET ALERT** 🚨\n"
                        f"{' '.join(staff_ping)}\n"
                        f"New priority ticket requires immediate attention!"
                    )
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error Creating Ticket",
                description=f"Failed to create ticket channel.\n**Error:** {str(e)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class SuperTickets(commands.Cog):
    """🎫 Super Ticket System - Ultimate Ticket Management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="super-ticket-panel", description="🎫 Create the ultimate ticket system panel")
    @app_commands.default_permissions(administrator=True)
    async def super_ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Super Ticket System",
            description="**Ultimate support system with intelligent routing**\n\n"
                       "🌟 **Features:**\n"
                       "• Smart category selection\n"
                       "• Priority-based routing\n"
                       "• Staff role integration (4 roles)\n"
                       "• Advanced ticket controls\n"
                       "• Automatic notifications\n\n"
                       "**Select your ticket type below to get started:**",
            color=0x7289da
        )
        
        embed.add_field(
            name="🚨 Priority Support",
            value="Fast-track support for urgent issues\n• Instant staff notification\n• Priority queue placement\n• 5-minute response guarantee",
            inline=True
        )
        
        embed.add_field(
            name="🐛 Bug Reports", 
            value="Report technical issues\n• Automatic categorization\n• Technical team routing\n• Progress tracking",
            inline=True
        )
        
        embed.add_field(
            name="🆘 General Support",
            value="Standard support channel\n• Comprehensive assistance\n• Staff availability\n• Solution tracking",
            inline=True
        )
        
        embed.set_footer(text="🎫 Super Ticket System • Enhanced support experience")
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/🎫.png")
        
        view = SuperTicketCreator()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(SuperTickets(bot))