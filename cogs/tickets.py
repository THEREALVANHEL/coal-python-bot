import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime
import os, sys
import asyncio

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

# Define the 4 staff roles that can manage tickets
STAFF_ROLES = ["lead moderator", "moderator", "overseer", "forgotten one"]
STAFF_ROLE_IDS = [1371003310223654974, 1371003310223654974, 1371003310223654974, 1371003310223654974]  # Replace with actual role IDs

class AdminControlPanel(View):
    """Private admin control panel with buttons for staff commands"""
    def __init__(self):
        super().__init__(timeout=None)
        
    def _is_staff(self, user) -> bool:
        """Check if user is authorized staff"""
        if user.guild_permissions.administrator:
            return True
        if has_special_permissions(user):
            return True
        user_roles = [role.name.lower() for role in user.roles]
        return any(staff_role in user_roles for staff_role in STAFF_ROLES)
    
    @discord.ui.button(label="🔒 Lock Channel", style=discord.ButtonStyle.danger, custom_id="admin_lock")
    async def lock_channel(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can use this!", ephemeral=True)
            return
            
        try:
            # Lock the channel
            everyone_role = interaction.guild.default_role
            await interaction.channel.set_permissions(everyone_role, send_messages=False, reason=f"Channel locked by {interaction.user}")
            
            # Ensure staff can still message
            for role in interaction.guild.roles:
                if role.name.lower() in STAFF_ROLES or role.permissions.administrator:
                    await interaction.channel.set_permissions(role, send_messages=True, reason="Staff bypass")
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"Channel locked by {interaction.user.mention}\nOnly staff can now send messages.",
                color=0xff0000,
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error locking channel: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🔓 Unlock Channel", style=discord.ButtonStyle.success, custom_id="admin_unlock")
    async def unlock_channel(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can use this!", ephemeral=True)
            return
            
        try:
            # Unlock the channel
            everyone_role = interaction.guild.default_role
            await interaction.channel.set_permissions(everyone_role, send_messages=None, reason=f"Channel unlocked by {interaction.user}")
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"Channel unlocked by {interaction.user.mention}\nNormal permissions restored.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unlocking channel: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🗑️ Close Ticket", style=discord.ButtonStyle.secondary, custom_id="admin_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can use this!", ephemeral=True)
            return
            
        # Check if in a ticket channel
        if not (interaction.channel.name.startswith('ticket-') or interaction.channel.name.startswith('🔴') or interaction.channel.name.startswith('🟢')):
            await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
            return
            
        try:
            embed = discord.Embed(
                title="🗑️ Ticket Closed",
                description=f"Ticket closed by {interaction.user.mention}\n\nChannel will be deleted in 10 seconds.",
                color=0xff0000,
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed)
            
            # Delete channel after delay
            await asyncio.sleep(10)
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error closing ticket: {str(e)}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="🚨 Emergency Ban", style=discord.ButtonStyle.danger, custom_id="admin_emergency_ban")
    async def emergency_ban(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can use this!", ephemeral=True)
            return
            
        class QuickBanModal(Modal):
            def __init__(self):
                super().__init__(title="🚨 Emergency Ban")
                
            user_id = TextInput(
                label="User ID to Ban",
                placeholder="Enter the user ID of the person to ban",
                required=True,
                max_length=20
            )
            
            reason = TextInput(
                label="Ban Reason",
                placeholder="Emergency ban reason",
                required=True,
                max_length=500,
                style=discord.TextStyle.paragraph
            )
            
            async def on_submit(self, modal_interaction):
                try:
                    user_id = int(self.user_id.value)
                    user = modal_interaction.guild.get_member(user_id)
                    
                    if not user:
                        # Try to fetch user even if not in guild
                        try:
                            user = await modal_interaction.client.fetch_user(user_id)
                        except:
                            await modal_interaction.response.send_message("❌ User not found!", ephemeral=True)
                            return
                    
                    # Check if user can be banned (hierarchy check)
                    if user == modal_interaction.user:
                        await modal_interaction.response.send_message("❌ You cannot ban yourself!", ephemeral=True)
                        return
                    
                    if isinstance(user, discord.Member) and user.top_role >= modal_interaction.user.top_role:
                        await modal_interaction.response.send_message("❌ Cannot ban user with equal or higher role!", ephemeral=True)
                        return
                    
                    # Execute ban
                    reason = f"Emergency ban by {modal_interaction.user}: {self.reason.value}"
                    await modal_interaction.guild.ban(user, reason=reason, delete_message_days=1)
                    
                    embed = discord.Embed(
                        title="🚨 Emergency Ban Executed",
                        description=f"**User:** {user.mention} (`{user.id}`)\n**Reason:** {self.reason.value}\n**Banned by:** {modal_interaction.user.mention}",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                    await modal_interaction.response.send_message(embed=embed)
                    
                except ValueError:
                    await modal_interaction.response.send_message("❌ Invalid user ID format!", ephemeral=True)
                except discord.Forbidden:
                    await modal_interaction.response.send_message("❌ Missing permissions to ban this user!", ephemeral=True)
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(QuickBanModal())

    @discord.ui.button(label="⚠️ Quick Warn", style=discord.ButtonStyle.secondary, custom_id="admin_quick_warn")
    async def quick_warn(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can use this!", ephemeral=True)
            return
            
        class QuickWarnModal(Modal):
            def __init__(self):
                super().__init__(title="⚠️ Quick Warn")
                
            user_id = TextInput(
                label="User ID to Warn",
                placeholder="Enter the user ID",
                required=True,
                max_length=20
            )
            
            reason = TextInput(
                label="Warning Reason",
                placeholder="Reason for the warning",
                required=True,
                max_length=500,
                style=discord.TextStyle.paragraph
            )
            
            async def on_submit(self, modal_interaction):
                try:
                    user_id = int(self.user_id.value)
                    user = modal_interaction.guild.get_member(user_id)
                    
                    if not user:
                        await modal_interaction.response.send_message("❌ User not found in server!", ephemeral=True)
                        return
                    
                    # Add warning to database
                    warning_data = {
                        'user_id': user.id,
                        'warned_by': modal_interaction.user.id,
                        'reason': self.reason.value,
                        'timestamp': datetime.now(),
                        'guild_id': modal_interaction.guild.id
                    }
                    
                    success = db.add_warning(warning_data)
                    if not success:
                        await modal_interaction.response.send_message("❌ Failed to add warning to database!", ephemeral=True)
                        return
                    
                    # Get total warnings
                    warnings = db.get_user_warnings(user.id)
                    warning_count = len(warnings)
                    
                    embed = discord.Embed(
                        title="⚠️ User Warned",
                        description=f"**User:** {user.mention}\n**Reason:** {self.reason.value}\n**Total Warnings:** {warning_count}\n**Warned by:** {modal_interaction.user.mention}",
                        color=0xffa500,
                        timestamp=datetime.now()
                    )
                    
                    await modal_interaction.response.send_message(embed=embed)
                    
                    # Try to DM the user
                    try:
                        dm_embed = discord.Embed(
                            title="⚠️ Warning Received",
                            description=f"You have been warned in **{modal_interaction.guild.name}**",
                            color=0xffa500,
                            timestamp=datetime.now()
                        )
                        dm_embed.add_field(
                            name="Reason",
                            value=self.reason.value,
                            inline=False
                        )
                        dm_embed.add_field(
                            name="Total Warnings",
                            value=f"{warning_count} warning(s)",
                            inline=True
                        )
                        dm_embed.set_footer(text="Please follow server rules to avoid further warnings")
                        
                        await user.send(embed=dm_embed)
                    except:
                        pass  # DM failed, but warning was still issued
                    
                except ValueError:
                    await modal_interaction.response.send_message("❌ Invalid user ID format!", ephemeral=True)
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(QuickWarnModal())

class SimpleTicketButtons(View):
    """Simple ticket control buttons for staff - FIXED VERSION"""
    def __init__(self, creator_id: int):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.claimed_by = None
        
    def _is_staff(self, user) -> bool:
        """Check if user is authorized staff"""
        if user.guild_permissions.administrator:
            return True
        if has_special_permissions(user):
            return True
        user_roles = [role.name.lower() for role in user.roles]
        return any(staff_role in user_roles for staff_role in STAFF_ROLES)
    
    @discord.ui.button(label="Claim", emoji="🟢", style=discord.ButtonStyle.primary, custom_id="simple_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can claim tickets.", ephemeral=True)
            return
            
        try:
            # Check if already claimed by someone else
            if self.claimed_by and self.claimed_by != interaction.user.id:
                old_claimer = interaction.guild.get_member(self.claimed_by)
                old_name = old_claimer.display_name if old_claimer else "Unknown"
                
                embed = discord.Embed(
                    title="🔄 Ticket Transferred",
                    description=f"**Transferred from:** {old_name}\n**Transferred to:** {interaction.user.mention}",
                    color=0xffaa00,
                    timestamp=datetime.now()
                )
                
                # Update channel name
                claimer_name = interaction.user.display_name.lower().replace(' ', '-')[:10]
                new_name = f"🟢claimed-by-{claimer_name}"
                await interaction.channel.edit(name=new_name)
                
                # Update the view state and the message
                self.claimed_by = interaction.user.id
                
                # Get the original message and update it
                async for message in interaction.channel.history(limit=10):
                    if message.author == interaction.client.user and message.embeds and message.components:
                        # Update the view in the message
                        await message.edit(view=self)
                        break
                
                await interaction.response.send_message(embed=embed)
                return
            
            # First time claim
            claimer_name = interaction.user.display_name.lower().replace(' ', '-')[:10]
            new_name = f"🟢claimed-by-{claimer_name}"
            await interaction.channel.edit(name=new_name)
            
            self.claimed_by = interaction.user.id
            
            # Update the view in the original message
            async for message in interaction.channel.history(limit=10):
                if message.author == interaction.client.user and message.embeds and message.components:
                    await message.edit(view=self)
                    break
            
            embed = discord.Embed(
                title="✅ Ticket Claimed",
                description=f"**{interaction.user.mention}** claimed this ticket\n🟢 Status: **CLAIMED**",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error claiming ticket: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="simple_close")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can close tickets.", ephemeral=True)
            return
            
        try:
            embed = discord.Embed(
                title="🔒 Ticket Closed",
                description=f"Ticket closed by **{interaction.user.mention}**\n\nChannel will be deleted in 10 seconds.",
                color=0xff0000,
                timestamp=datetime.now()
            )
            await interaction.response.send_message(embed=embed)
            
            await asyncio.sleep(10)
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error closing ticket: {str(e)}", ephemeral=True)
            except:
                pass

class TicketCreateButtons(View):
    """Simple ticket creation buttons with staff role pinging"""
    def __init__(self):
        super().__init__(timeout=None)
        
    def _has_existing_ticket(self, user, guild) -> bool:
        """Check if user already has an active ticket"""
        for channel in guild.text_channels:
            if (channel.name.startswith('🔴ticket-') or 
                channel.name.startswith('🟢claimed-') or 
                channel.name.startswith('ticket-')) and str(user.id) in channel.topic:
                return True
        return False
    
    async def _ping_staff_roles(self, guild):
        """Get staff role mentions for pinging"""
        staff_mentions = []
        for role in guild.roles:
            if role.name.lower() in STAFF_ROLES:
                staff_mentions.append(role.mention)
        return staff_mentions
    
    @discord.ui.button(label="💬 General Support", style=discord.ButtonStyle.secondary, custom_id="create_general")
    async def general_support(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "general", "💬", "General Support")
    
    @discord.ui.button(label="🔧 Technical Issue", style=discord.ButtonStyle.secondary, custom_id="create_technical") 
    async def technical_issue(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "technical", "🔧", "Technical Issue")
    
    @discord.ui.button(label="👤 Account Help", style=discord.ButtonStyle.secondary, custom_id="create_account")
    async def account_help(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "account", "👤", "Account Help")
    
    async def _create_ticket(self, interaction: discord.Interaction, category: str, emoji: str, title: str):
        """Create a new ticket with staff role pinging"""
        # Check for existing ticket
        if self._has_existing_ticket(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ Ticket Already Exists",
                description="You already have an active ticket. Please use your existing ticket or wait for it to be closed.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Create ticket channel with red emoji (unclaimed)
            username = interaction.user.display_name.lower().replace(' ', '-')[:15]
            channel_name = f"🔴ticket-{username}"
            
            # Find support category
            category_channel = None
            for cat in interaction.guild.categories:
                if 'support' in cat.name.lower() or 'ticket' in cat.name.lower():
                    category_channel = cat
                    break
            
            # Set permissions: creator + staff roles can see, everyone else cannot
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
            }
            
            # Add staff roles to permissions
            for role in interaction.guild.roles:
                if role.name.lower() in STAFF_ROLES or role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
            
            # Create the channel
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category_channel,
                overwrites=overwrites,
                topic=f"{emoji} {title} • Creator: {interaction.user.id} • Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Get staff role mentions
            staff_mentions = await self._ping_staff_roles(interaction.guild)
            
            # Send initial message with staff pings
            embed = discord.Embed(
                title=f"{emoji} New {title}",
                description=f"**Ticket Creator:** {interaction.user.mention}\n**Category:** {title}\n**Created:** <t:{int(datetime.now().timestamp())}:F>",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="📋 What happens next?",
                value="• Staff will respond as soon as possible\n• Please describe your issue in detail\n• Only you and staff can see this channel",
                inline=False
            )
            embed.set_footer(text="🎫 Simple Ticket System")
            
            # Add ticket control buttons (staff only)
            view = SimpleTicketButtons(interaction.user.id)
            
            # Create mention string
            staff_ping = " ".join(staff_mentions) if staff_mentions else ""
            mention_text = f"{interaction.user.mention} {staff_ping}"
            
            await ticket_channel.send(mention_text, embed=embed, view=view)
            
            # Success message
            success_embed = discord.Embed(
                title="✅ Ticket Created",
                description=f"Your ticket has been created: {ticket_channel.mention}\n\n🔔 Staff have been notified!",
                color=0x00ff00
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ticket Creation Failed",
                description=f"Error: {str(e)}",
                color=0xff0000
            )
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)

class SimpleTickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views for buttons to work after bot restart
        self.bot.add_view(TicketCreateButtons())
        self.bot.add_view(AdminControlPanel())
        print("✅ Simple Ticket System loaded with persistent views")

    @app_commands.command(name="ticket-panel", description="Create a simple ticket panel")
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Create a simple ticket panel"""
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only administrators can create ticket panels.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        target_channel = channel or interaction.channel
        
        # Create simple panel
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Need help? Create a ticket below!\n\n**📋 Rules:**\n• One ticket per person\n• Be clear about your issue\n• Staff will help you soon",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📞 Support Categories",
            value="💬 **General** - Questions and general help\n🔧 **Technical** - Bot issues and bugs\n👤 **Account** - Profile and account problems",
            inline=False
        )
        embed.set_footer(text="🎫 Simple Ticket System • Click a button below")
        
        view = TicketCreateButtons()
        
        await target_channel.send(embed=embed, view=view)
        
        success_embed = discord.Embed(
            title="✅ Ticket Panel Created",
            description=f"Simple ticket panel created in {target_channel.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    @app_commands.command(name="admin-panel", description="Create a private admin control panel")
    @app_commands.default_permissions(administrator=True)
    async def admin_panel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Create a private admin control panel with buttons"""
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only administrators can create admin panels.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        target_channel = channel or interaction.channel
        
        # Create admin panel
        embed = discord.Embed(
            title="🛡️ Admin Control Panel",
            description="**Staff Commands Panel**\nUse the buttons below for common moderation actions.",
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="🔒 Channel Controls",
            value="• **Lock Channel** - Prevent non-staff from messaging\n• **Unlock Channel** - Restore normal permissions",
            inline=False
        )
        embed.add_field(
            name="🎫 Ticket Controls", 
            value="• **Close Ticket** - Close and delete ticket channels",
            inline=False
        )
        embed.add_field(
            name="⚡ Quick Actions",
            value="• **Emergency Ban** - Quick ban with reason\n• **Quick Warn** - Issue warning with reason",
            inline=False
        )
        embed.add_field(
            name="👮 Authorized Users",
            value="• Lead Moderator\n• Moderator\n• Overseer\n• Forgotten One\n• Administrators",
            inline=False
        )
        embed.set_footer(text="🛡️ Admin Panel • Staff Only")
        
        view = AdminControlPanel()
        
        await target_channel.send(embed=embed, view=view)
        
        success_embed = discord.Embed(
            title="✅ Admin Panel Created",
            description=f"Admin control panel created in {target_channel.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    @app_commands.command(name="close-ticket", description="Close the current ticket (Staff only)")
    async def close_ticket_command(self, interaction: discord.Interaction):
        """Staff command to close tickets"""
        
        # Check if user is staff
        is_staff = (
            interaction.user.guild_permissions.administrator or
            has_special_permissions(interaction.user) or
            any(role.name.lower() in STAFF_ROLES for role in interaction.user.roles)
        )
        
        if not is_staff:
            embed = discord.Embed(
                title="❌ Access Denied", 
                description="Only staff can close tickets.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if in ticket channel
        if not (interaction.channel.name.startswith('ticket-') or 
                interaction.channel.name.startswith('🔴') or 
                interaction.channel.name.startswith('🟢')):
            embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Close ticket
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Ticket closed by **{interaction.user.mention}**\n\nChannel will be deleted in 10 seconds.",
            color=0xff0000,
            timestamp=datetime.now()
        )
        await interaction.response.send_message(embed=embed)
        
        await asyncio.sleep(10)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

    # warnlist command removed from tickets.py to prevent duplicate registration
    # The command is available in moderation.py

async def setup(bot):
    await bot.add_cog(SimpleTickets(bot))