import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime, timedelta
import os, sys
import asyncio

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

# Define the 4 staff roles that can manage tickets
STAFF_ROLES = ["forgotten one", "overseer", "leadmoderator", "moderator"]

class ModernTicketControlPanel(View):
    """🎫 Modern Ticket Control Panel - Cool & Simplistic Design"""
    def __init__(self, creator_id: int):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.claimed_by = None
        self.is_locked = False
        
    def _is_staff(self, user) -> bool:
        """Check if user is authorized staff (the 4 roles)"""
        if user.guild_permissions.administrator:
            return True
        if has_special_permissions(user):
            return True
        user_roles = [role.name.lower() for role in user.roles]
        return any(staff_role in user_roles for staff_role in STAFF_ROLES)
    
    @discord.ui.button(label="Claim", emoji="🟢", style=discord.ButtonStyle.success, custom_id="modern_claim", row=0)
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can claim tickets.", ephemeral=True)
            return
            
        try:
            # Check if already claimed by someone else
            if self.claimed_by and self.claimed_by != interaction.user.id:
                old_claimer = interaction.guild.get_member(self.claimed_by)
                old_name = old_claimer.display_name if old_claimer else "Unknown Staff"
                
                # Update channel name to new claimer
                claimer_name = interaction.user.display_name.lower().replace(' ', '-')[:10]
                new_name = f"🟢┃{claimer_name}-ticket"
                await interaction.channel.edit(name=new_name)
                
                # Update the view state
                self.claimed_by = interaction.user.id
                
                # Create transfer embed
                embed = discord.Embed(
                    title="🔄 Ticket Ownership Transferred",
                    description=f"**Previous Claimer:** {old_name}\n**New Claimer:** {interaction.user.mention}",
                    color=0x00ff7f,
                    timestamp=datetime.now()
                )
                embed.add_field(name="🎯 Status", value="**TRANSFERRED**", inline=True)
                embed.add_field(name="⏰ Time", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
                embed.add_field(name="📋 Next Steps", value="• Continue assisting the user\n• Use admin controls as needed\n• Close when resolved", inline=False)
                embed.set_footer(text="🎫 Modern Ticket System • Transfer Complete")
                
                await interaction.response.send_message(embed=embed)
                
                # Update the original message with new view state
                try:
                    # Find the original ticket message and update it
                    async for message in interaction.channel.history(limit=20):
                        if (message.author == interaction.client.user and 
                            message.embeds and 
                            "New Ticket" in message.embeds[0].title):
                            # Update the embed to show new claimer
                            original_embed = message.embeds[0]
                            original_embed.color = 0x00ff7f  # Green for claimed
                            original_embed.title = original_embed.title.replace("🔴", "🟢").replace("WAITING FOR STAFF", f"CLAIMED BY {interaction.user.display_name.upper()}")
                            
                            await message.edit(embed=original_embed, view=self)
                            break
                except Exception as e:
                    print(f"Error updating original message: {e}")
                
                return
            
            # First time claim or reclaim by same person
            claimer_name = interaction.user.display_name.lower().replace(' ', '-')[:10]
            new_name = f"🟢┃{claimer_name}-ticket"
            await interaction.channel.edit(name=new_name)
            
            self.claimed_by = interaction.user.id
            
            embed = discord.Embed(
                title="✅ Ticket Successfully Claimed",
                description=f"**Staff Member:** {interaction.user.mention}\n**Status:** 🟢 **ACTIVE**",
                color=0x00ff7f,
                timestamp=datetime.now()
            )
            embed.add_field(name="🎯 Next Steps", value="• Respond to the user's inquiry\n• Use admin controls as needed\n• Close when resolved", inline=False)
            embed.set_footer(text="🎫 Modern Ticket System • Claimed")
            
            await interaction.response.send_message(embed=embed)
            
            # Update the original message
            try:
                async for message in interaction.channel.history(limit=20):
                    if (message.author == interaction.client.user and 
                        message.embeds and 
                        "New Ticket" in message.embeds[0].title):
                        original_embed = message.embeds[0]
                        original_embed.color = 0x00ff7f  # Green for claimed
                        original_embed.title = original_embed.title.replace("🔴", "🟢").replace("WAITING FOR STAFF", f"CLAIMED BY {interaction.user.display_name.upper()}")
                        
                        await message.edit(embed=original_embed, view=self)
                        break
            except Exception as e:
                print(f"Error updating original message: {e}")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error claiming ticket: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="modern_close", row=0)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can close tickets.", ephemeral=True)
            return
            
        try:
            embed = discord.Embed(
                title="🔒 Ticket Closing",
                description=f"**Closed by:** {interaction.user.mention}\n**Time:** <t:{int(datetime.now().timestamp())}:F>",
                color=0xff4757,
                timestamp=datetime.now()
            )
            embed.add_field(name="⏰ Auto-Delete", value="Channel will be deleted in **10 seconds**", inline=True)
            embed.add_field(name="🎯 Status", value="**RESOLVED**", inline=True)
            embed.set_footer(text="🎫 Modern Ticket System • Closing")
            
            await interaction.response.send_message(embed=embed)
            
            await asyncio.sleep(10)
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error closing ticket: {str(e)}", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="Lock", emoji="🔐", style=discord.ButtonStyle.secondary, custom_id="modern_lock", row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can lock channels.", ephemeral=True)
            return
            
        try:
            if self.is_locked:
                await interaction.response.send_message("🔐 Channel is already locked!", ephemeral=True)
                return
            
            # Lock the channel - only staff can talk
            everyone_role = interaction.guild.default_role
            await interaction.channel.set_permissions(everyone_role, send_messages=False, reason=f"Channel locked by {interaction.user}")
            
            # Ensure the 4 staff roles can still message
            for role in interaction.guild.roles:
                if role.name.lower() in STAFF_ROLES or role.permissions.administrator:
                    await interaction.channel.set_permissions(role, send_messages=True, reason="Staff bypass")
            
            self.is_locked = True
            
            embed = discord.Embed(
                title="🔐 Channel Locked",
                description=f"**Locked by:** {interaction.user.mention}\n**Only staff can now send messages**",
                color=0xff6b35,
                timestamp=datetime.now()
            )
            embed.add_field(name="🛡️ Protected Roles", value="• Forgotten One\n• Overseer\n• Lead Moderator\n• Moderator", inline=True)
            embed.add_field(name="🎯 Status", value="**LOCKED**", inline=True)
            embed.set_footer(text="🎫 Modern Ticket System • Locked")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error locking channel: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Unlock", emoji="🔓", style=discord.ButtonStyle.success, custom_id="modern_unlock", row=0)
    async def unlock_channel(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can unlock channels.", ephemeral=True)
            return
            
        try:
            if not self.is_locked:
                await interaction.response.send_message("🔓 Channel is already unlocked!", ephemeral=True)
                return
            
            # Unlock the channel
            everyone_role = interaction.guild.default_role
            await interaction.channel.set_permissions(everyone_role, send_messages=None, reason=f"Channel unlocked by {interaction.user}")
            
            self.is_locked = False
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"**Unlocked by:** {interaction.user.mention}\n**Normal permissions restored**",
                color=0x00d2d3,
                timestamp=datetime.now()
            )
            embed.add_field(name="🎯 Status", value="**UNLOCKED**", inline=True)
            embed.add_field(name="✅ Access", value="All users can message", inline=True)
            embed.set_footer(text="🎫 Modern Ticket System • Unlocked")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unlocking channel: {str(e)}", ephemeral=True)

    # INTEGRATED ADMIN PANEL - Row 1
    @discord.ui.button(label="Emergency Ban", emoji="🚨", style=discord.ButtonStyle.danger, custom_id="admin_emergency_ban", row=1)
    async def emergency_ban(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can use admin controls.", ephemeral=True)
            return
            
        class QuickBanModal(Modal):
            def __init__(self):
                super().__init__(title="🚨 Emergency Ban System")
                
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
                        try:
                            user = await modal_interaction.client.fetch_user(user_id)
                        except:
                            await modal_interaction.response.send_message("❌ User not found!", ephemeral=True)
                            return
                    
                    if user == modal_interaction.user:
                        await modal_interaction.response.send_message("❌ You cannot ban yourself!", ephemeral=True)
                        return
                    
                    if isinstance(user, discord.Member) and user.top_role >= modal_interaction.user.top_role:
                        await modal_interaction.response.send_message("❌ Cannot ban user with equal or higher role!", ephemeral=True)
                        return
                    
                    reason = f"Emergency ban by {modal_interaction.user}: {self.reason.value}"
                    await modal_interaction.guild.ban(user, reason=reason, delete_message_days=1)
                    
                    embed = discord.Embed(
                        title="🚨 Emergency Ban Executed",
                        description=f"**User:** {user.mention} (`{user.id}`)\n**Reason:** {self.reason.value}\n**Banned by:** {modal_interaction.user.mention}",
                        color=0xff3838,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text="🛡️ Admin Panel • Emergency Ban")
                    await modal_interaction.response.send_message(embed=embed)
                    
                except ValueError:
                    await modal_interaction.response.send_message("❌ Invalid user ID format!", ephemeral=True)
                except discord.Forbidden:
                    await modal_interaction.response.send_message("❌ Missing permissions to ban this user!", ephemeral=True)
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(QuickBanModal())

    @discord.ui.button(label="Quick Warn", emoji="⚠️", style=discord.ButtonStyle.secondary, custom_id="admin_quick_warn", row=1)
    async def quick_warn(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can use admin controls.", ephemeral=True)
            return
            
        class QuickWarnModal(Modal):
            def __init__(self):
                super().__init__(title="⚠️ Quick Warning System")
                
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
                    
                    warnings = db.get_user_warnings(user.id)
                    warning_count = len(warnings)
                    
                    embed = discord.Embed(
                        title="⚠️ User Warning Issued",
                        description=f"**User:** {user.mention}\n**Reason:** {self.reason.value}\n**Total Warnings:** {warning_count}\n**Warned by:** {modal_interaction.user.mention}",
                        color=0xffa726,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text="🛡️ Admin Panel • Warning System")
                    await modal_interaction.response.send_message(embed=embed)
                    
                    # Try to DM the user
                    try:
                        dm_embed = discord.Embed(
                            title="⚠️ Warning Received",
                            description=f"You have been warned in **{modal_interaction.guild.name}**",
                            color=0xffa726,
                            timestamp=datetime.now()
                        )
                        dm_embed.add_field(name="Reason", value=self.reason.value, inline=False)
                        dm_embed.add_field(name="Total Warnings", value=f"{warning_count} warning(s)", inline=True)
                        dm_embed.set_footer(text="Please follow server rules to avoid further warnings")
                        await user.send(embed=dm_embed)
                    except:
                        pass
                    
                except ValueError:
                    await modal_interaction.response.send_message("❌ Invalid user ID format!", ephemeral=True)
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(QuickWarnModal())

    @discord.ui.button(label="Temp Mute", emoji="🔇", style=discord.ButtonStyle.secondary, custom_id="admin_temp_mute", row=1)
    async def temp_mute(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can use admin controls.", ephemeral=True)
            return
            
        class TempMuteModal(Modal):
            def __init__(self):
                super().__init__(title="🔇 Temporary Mute System")
                
            user_id = TextInput(
                label="User ID to Mute",
                placeholder="Enter the user ID",
                required=True,
                max_length=20
            )
            
            duration = TextInput(
                label="Duration (minutes)",
                placeholder="Duration in minutes (e.g., 30 for 30 minutes)",
                required=True,
                max_length=10
            )
            
            reason = TextInput(
                label="Mute Reason",
                placeholder="Reason for the temporary mute",
                required=True,
                max_length=500,
                style=discord.TextStyle.paragraph
            )
            
            async def on_submit(self, modal_interaction):
                try:
                    user_id = int(self.user_id.value)
                    duration_minutes = int(self.duration.value)
                    user = modal_interaction.guild.get_member(user_id)
                    
                    if not user:
                        await modal_interaction.response.send_message("❌ User not found in server!", ephemeral=True)
                        return
                    
                    if duration_minutes <= 0 or duration_minutes > 10080:  # Max 1 week
                        await modal_interaction.response.send_message("❌ Duration must be between 1 minute and 1 week (10080 minutes)!", ephemeral=True)
                        return
                    
                    # Apply timeout
                    timeout_duration = timedelta(minutes=duration_minutes)
                    await user.timeout(timeout_duration, reason=f"Temp mute by {modal_interaction.user}: {self.reason.value}")
                    
                    embed = discord.Embed(
                        title="🔇 Temporary Mute Applied",
                        description=f"**User:** {user.mention}\n**Duration:** {duration_minutes} minutes\n**Reason:** {self.reason.value}\n**Muted by:** {modal_interaction.user.mention}",
                        color=0x95a5a6,
                        timestamp=datetime.now()
                    )
                    embed.add_field(name="⏰ Expires", value=f"<t:{int((datetime.now() + timeout_duration).timestamp())}:F>", inline=True)
                    embed.set_footer(text="🛡️ Admin Panel • Temporary Mute")
                    await modal_interaction.response.send_message(embed=embed)
                    
                except ValueError:
                    await modal_interaction.response.send_message("❌ Invalid user ID or duration format!", ephemeral=True)
                except discord.Forbidden:
                    await modal_interaction.response.send_message("❌ Missing permissions to mute this user!", ephemeral=True)
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(TempMuteModal())

class ModernTicketCreator(View):
    """🎫 Modern Ticket Creation Interface"""
    def __init__(self):
        super().__init__(timeout=None)
        
    def _has_existing_ticket(self, user, guild) -> bool:
        """Check if user already has an active ticket"""
        for channel in guild.text_channels:
            if (channel.name.startswith('🔴┃') or 
                channel.name.startswith('🟢┃') or 
                channel.name.startswith('ticket-')) and str(user.id) in channel.topic:
                return True
        return False
    
    async def _ping_staff_roles(self, guild):
        """Get staff role mentions for pinging - FIXED VERSION"""
        staff_mentions = []
        
        # Get exact role names to search for
        target_roles = ["forgotten one", "overseer", "lead moderator", "moderator"]
        
        print(f"[DEBUG] Looking for roles: {target_roles}")
        
        for role in guild.roles:
            role_name_lower = role.name.lower().strip()
            
            # Check each target role
            for target_role in target_roles:
                if target_role in role_name_lower or role_name_lower in target_role:
                    staff_mentions.append(role.mention)
                    print(f"[DEBUG] Found staff role: {role.name} -> {role.mention}")
                    break
        
        # If no roles found, try alternative names
        if not staff_mentions:
            alternative_names = ["moderator", "mod", "admin", "staff", "overseer", "lead", "forgotten"]
            for role in guild.roles:
                role_name_lower = role.name.lower().strip()
                for alt_name in alternative_names:
                    if alt_name in role_name_lower:
                        staff_mentions.append(role.mention)
                        print(f"[DEBUG] Found alternative staff role: {role.name}")
                        break
        
        print(f"[DEBUG] Total staff mentions found: {len(staff_mentions)}")
        return staff_mentions
    
    @discord.ui.button(label="💬 General Support", style=discord.ButtonStyle.primary, emoji="💬", custom_id="create_general", row=0)
    async def general_support(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "general", "💬", "General Support")
    
    @discord.ui.button(label="🔧 Technical Issue", style=discord.ButtonStyle.secondary, emoji="🔧", custom_id="create_technical", row=0) 
    async def technical_issue(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "technical", "🔧", "Technical Issue")
    
    @discord.ui.button(label="👤 Account Help", style=discord.ButtonStyle.success, emoji="👤", custom_id="create_account", row=0)
    async def account_help(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "account", "👤", "Account Help")
    
    @discord.ui.button(label="🛡️ Report Issue", style=discord.ButtonStyle.danger, emoji="🛡️", custom_id="create_report", row=0)
    async def report_issue(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "report", "🛡️", "Report Issue")
    
    async def _create_ticket(self, interaction: discord.Interaction, category: str, emoji: str, title: str):
        """Create a new modern ticket with staff role pinging"""
        if self._has_existing_ticket(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ Ticket Already Exists",
                description="You already have an active ticket. Please use your existing ticket or wait for it to be closed.",
                color=0xff4757
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Create ticket channel with modern naming
            username = interaction.user.display_name.lower().replace(' ', '-')[:15]
            channel_name = f"🔴┃{username}-ticket"
            
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
            
            # Add the 4 staff roles to permissions
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
            
            # Create modern ticket embed
            embed = discord.Embed(
                title=f"🎫 New {title}",
                description=f"**Ticket Creator:** {interaction.user.mention}\n**Category:** {title}\n**Status:** 🔴 **WAITING FOR STAFF**",
                color=0x5865f2,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 What's Next?",
                value="• **Staff will respond soon**\n• **Describe your issue in detail**\n• **Only you and staff can see this**\n• **Use buttons below for quick actions**",
                inline=False
            )
            
            embed.add_field(
                name="🛡️ Staff Roles Notified",
                value="• Forgotten One\n• Overseer\n• Lead Moderator\n• Moderator",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Response Time",
                value="Usually within **30 minutes**\nDuring peak hours: **1-2 hours**",
                inline=True
            )
            
            embed.set_footer(text="🎫 Modern Ticket System • Cool & Simplistic")
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Add modern ticket control panel with integrated admin panel
            view = ModernTicketControlPanel(interaction.user.id)
            
            # Ping staff and user
            staff_ping = " ".join(staff_mentions) if staff_mentions else ""
            mention_text = f"🔔 {interaction.user.mention} {staff_ping}"
            
            await ticket_channel.send(mention_text, embed=embed, view=view)
            
            # Success message
            success_embed = discord.Embed(
                title="✅ Ticket Created Successfully",
                description=f"🎫 Your ticket: {ticket_channel.mention}\n\n🔔 **Staff have been notified!**",
                color=0x00d2d3
            )
            success_embed.add_field(name="⚡ Quick Access", value=f"Click {ticket_channel.mention} to view your ticket", inline=False)
            success_embed.set_footer(text="🎫 Modern Ticket System")
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ticket Creation Failed",
                description=f"Error: {str(e)}",
                color=0xff4757
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
        self.bot.add_view(ModernTicketControlPanel(0))  # 0 as placeholder
        self.bot.add_view(ModernTicketCreator())
        print("[Tickets] 🎫 Modern Ticket System loaded - Cool & Simplistic!")

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
        
        view = ModernTicketCreator() # Changed to ModernTicketCreator
        
        await target_channel.send(embed=embed, view=view)
        
        success_embed = discord.Embed(
            title="✅ Ticket Panel Created",
            description=f"Simple ticket panel created in {target_channel.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)





    # warnlist command removed from tickets.py to prevent duplicate registration
    # The command is available in moderation.py

async def setup(bot):
    await bot.add_cog(SimpleTickets(bot))