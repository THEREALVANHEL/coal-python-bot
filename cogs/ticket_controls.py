import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select, Modal, TextInput
from datetime import datetime
import os, sys
import asyncio

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

class CoolTicketControls(View):
    def __init__(self, creator_id: int, category_key: str, subcategory: str, is_claimed: bool = False):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.category_key = category_key
        self.subcategory = subcategory
        self.is_claimed = is_claimed
        self.is_locked = False
        
        # Set up initial buttons based on state
        self.setup_buttons()
    
    def setup_buttons(self):
        """Setup buttons based on current ticket state"""
        self.clear_items()
        
        if self.is_claimed:
            # Claimed state: Unclaim, Lock/Unlock, Close
            self.add_item(Button(label="👤 Unclaim", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="unclaim_btn"))
            
            if self.is_locked:
                self.add_item(Button(label="🔓 Unlock", style=discord.ButtonStyle.secondary, emoji="🔓", custom_id="unlock_btn"))
            else:
                self.add_item(Button(label="🔒 Lock", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="lock_btn"))
                
            self.add_item(Button(label="🔐 Close", style=discord.ButtonStyle.danger, emoji="🔐", custom_id="close_btn"))
        else:
            # Unclaimed state: Claim, Lock/Unlock, Close
            self.add_item(Button(label="👤 Claim", style=discord.ButtonStyle.success, emoji="👤", custom_id="claim_btn"))
            
            if self.is_locked:
                self.add_item(Button(label="🔓 Unlock", style=discord.ButtonStyle.secondary, emoji="🔓", custom_id="unlock_btn"))
            else:
                self.add_item(Button(label="🔒 Lock", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="lock_btn"))
                
            self.add_item(Button(label="🔐 Close", style=discord.ButtonStyle.danger, emoji="🔐", custom_id="close_btn"))
    
    def has_ticket_permissions(self, user, guild):
        """Check if user has ticket permissions"""
        # Check if user is the ticket creator
        if user.id == self.creator_id:
            return True
        
        # Check if user has admin/mod permissions
        if user.guild_permissions.administrator:
            return True
        
        # Check if user has ticket support roles
        server_settings = db.get_server_settings(guild.id)
        ticket_support_roles = server_settings.get('ticket_support_roles', [])
        
        user_role_ids = [role.id for role in user.roles]
        if any(role_id in user_role_ids for role_id in ticket_support_roles):
            return True
        
        # Check for mod/admin roles by name
        mod_role_names = ["admin", "administrator", "mod", "moderator", "staff", "support", "helper", "ticket"]
        for role in user.roles:
            if any(name in role.name.lower() for name in mod_role_names):
                return True
        
        return False
    
    def is_staff_member(self, user, guild):
        """Check if user is staff (can override locks)"""
        # Check if user has admin/mod permissions
        if user.guild_permissions.administrator:
            return True
        
        # Check if user has ticket support roles
        server_settings = db.get_server_settings(guild.id)
        ticket_support_roles = server_settings.get('ticket_support_roles', [])
        
        user_role_ids = [role.id for role in user.roles]
        if any(role_id in user_role_ids for role_id in ticket_support_roles):
            return True
        
        # Check for mod/admin roles by name
        mod_role_names = ["admin", "administrator", "mod", "moderator", "staff", "support", "helper"]
        for role in user.roles:
            if any(name in role.name.lower() for name in mod_role_names):
                return True
        
        return False

    async def update_channel_name(self, channel, status_emoji, claimed_by=None):
        """Update channel name with status emoji and claimed info"""
        try:
            # Get clean username for channel name
            creator = channel.guild.get_member(self.creator_id)
            if not creator:
                return
            
            clean_username = creator.display_name.lower().replace(' ', '').replace('-', '')[:10]
            
            # Build new channel name with status and claimer
            if claimed_by:
                claimer_name = claimed_by.display_name.lower().replace(' ', '')[:8]
                new_name = f"{status_emoji}-claimed-by-{claimer_name}"
            else:
                new_name = f"{status_emoji}-ticket-{clean_username}"
            
            # Ensure name length is within Discord limits
            if len(new_name) > 100:
                new_name = new_name[:100]
            
            await channel.edit(name=new_name)
        except Exception as e:
            print(f"Error updating channel name: {e}")

    async def ping_support_roles(self, channel, claimer):
        """Ping roles that can view private ticket channels"""
        try:
            guild = channel.guild
            server_settings = db.get_server_settings(guild.id)
            ticket_support_roles = server_settings.get('ticket_support_roles', [])
            
            # Get all roles that can view this channel
            roles_to_ping = []
            
            # Add configured support roles
            for role_id in ticket_support_roles:
                role = guild.get_role(role_id)
                if role:
                    roles_to_ping.append(role)
            
            # Add admin roles by permission
            for role in guild.roles:
                if role.permissions.administrator and role not in roles_to_ping:
                    roles_to_ping.append(role)
            
            # Add roles by name that typically handle tickets
            ticket_role_names = ["support", "staff", "helper", "moderator", "mod"]
            for role in guild.roles:
                if any(name in role.name.lower() for name in ticket_role_names) and role not in roles_to_ping:
                    roles_to_ping.append(role)
            
            if roles_to_ping:
                ping_mentions = " ".join([role.mention for role in roles_to_ping])
                embed = discord.Embed(
                    title="📢 **Ticket Claimed - Staff Notification**",
                    description=f"**{claimer.display_name}** has claimed this ticket and is now handling it.",
                    color=0xffc107
                )
                embed.add_field(
                    name="🎯 **Action Required**",
                    value="Other staff members can now focus on other tickets while this one is being handled.",
                    inline=False
                )
                
                await channel.send(f"{ping_mentions}", embed=embed, delete_after=10)
                
        except Exception as e:
            print(f"Error pinging support roles: {e}")

    async def ping_creation_roles(self, channel, creator):
        """Ping leadmoderator and moderator roles when ticket is created"""
        try:
            guild = channel.guild
            roles_to_ping = []
            
            # Look for leadmoderator and moderator roles
            creation_role_names = ["leadmoderator", "moderator"]
            for role in guild.roles:
                if any(name in role.name.lower() for name in creation_role_names):
                    roles_to_ping.append(role)
            
            # Also add admin roles
            for role in guild.roles:
                if role.permissions.administrator and role not in roles_to_ping:
                    roles_to_ping.append(role)
            
            if roles_to_ping:
                ping_mentions = " ".join([role.mention for role in roles_to_ping])
                embed = discord.Embed(
                    title="🎫 **New Ticket Created**",
                    description=f"**{creator.display_name}** has created a new support ticket.",
                    color=0x00d4aa
                )
                embed.add_field(
                    name="� **Ticket Details**",
                    value=f"**Creator:** {creator.mention}\n**Category:** {self.subcategory}\n**Status:** 🟢 Open & Waiting",
                    inline=False
                )
                
                await channel.send(f"{ping_mentions} {creator.mention}", embed=embed, delete_after=15)
                
        except Exception as e:
            print(f"Error pinging creation roles: {e}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Handle button interactions"""
        if not hasattr(interaction.data, 'custom_id'):
            return True
            
        custom_id = interaction.data.get('custom_id', '')
        
        # Route to appropriate handler
        if custom_id == "claim_btn":
            await self.claim_ticket(interaction)
        elif custom_id == "unclaim_btn":
            await self.unclaim_ticket(interaction)
        elif custom_id == "lock_btn":
            await self.lock_ticket(interaction)
        elif custom_id == "unlock_btn":
            await self.unlock_ticket(interaction)
        elif custom_id == "close_btn":
            await self.close_ticket(interaction)
        elif custom_id == "reopen_btn":
            await self.reopen_ticket(interaction)
        elif custom_id == "delete_btn":
            await self.delete_ticket(interaction)
        
        return False  # Prevent default handling

    async def claim_ticket(self, interaction: discord.Interaction):
        """Handle ticket claiming"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to claim tickets!", ephemeral=True)
            return
        
        # Check if already claimed
        if self.is_claimed:
            await interaction.response.send_message("⚠️ This ticket is already claimed!", ephemeral=True)
            return
        
        try:
            channel = interaction.channel
            
            # Update channel topic to show claimed status
            current_topic = channel.topic or ""
            new_topic = f"🟡 CLAIMED by {interaction.user.display_name} • {current_topic}"
            await channel.edit(topic=new_topic)
            
            # Update channel name with yellow emoji and claimer name
            await self.update_channel_name(channel, "🟡", interaction.user)
            
            # Update state and buttons
            self.is_claimed = True
            self.setup_buttons()
            
            # Create claim embed
            claim_embed = discord.Embed(
                title="🟡 **Ticket Claimed**",
                description=f"This ticket has been claimed by {interaction.user.mention}",
                color=0xffc107,
                timestamp=datetime.now()
            )
            claim_embed.add_field(
                name="📋 **Claim Details**",
                value=f"**Staff Member:** {interaction.user.display_name}\n**Claimed At:** <t:{int(datetime.now().timestamp())}:F>\n**Status:** 🟡 Active",
                inline=False
            )
            claim_embed.set_author(name=f"{interaction.user.display_name} is handling this ticket", icon_url=interaction.user.display_avatar.url)
            claim_embed.set_footer(text="✨ Ticket Management System")
            
            await interaction.response.edit_message(embed=claim_embed, view=self)
            
            # Ping support roles
            await self.ping_support_roles(channel, interaction.user)
            
            # Send notification to ticket creator
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await channel.send(f"👋 {creator.mention}, your ticket has been claimed by {interaction.user.mention} and they will assist you shortly!")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error claiming ticket: {str(e)}", ephemeral=True)

    async def unclaim_ticket(self, interaction: discord.Interaction):
        """Handle ticket unclaiming"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to unclaim tickets!", ephemeral=True)
            return
        
        # Check if actually claimed
        if not self.is_claimed:
            await interaction.response.send_message("⚠️ This ticket is not currently claimed!", ephemeral=True)
            return
        
        try:
            channel = interaction.channel
            
            # Reset channel topic
            current_topic = channel.topic or ""
            # Remove claim info from topic
            parts = current_topic.split(" • ")
            if len(parts) > 1:
                new_topic = " • ".join(parts[1:])
            else:
                new_topic = f"🟢 Open • {self.subcategory} • Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            await channel.edit(topic=new_topic)
            
            # Update channel name back to green (open)
            await self.update_channel_name(channel, "🟢")
            
            # Update state and buttons
            self.is_claimed = False
            self.setup_buttons()
            
            # Create unclaim embed
            unclaim_embed = discord.Embed(
                title="🟢 **Ticket Unclaimed**",
                description=f"This ticket has been unclaimed by {interaction.user.mention} and is now available for other staff members.",
                color=0x28a745,
                timestamp=datetime.now()
            )
            unclaim_embed.add_field(
                name="📋 **Status Update**",
                value=f"**Unclaimed By:** {interaction.user.display_name}\n**Status:** 🟢 Open & Available\n**Available For:** Any staff member",
                inline=False
            )
            unclaim_embed.set_footer(text="✨ Ticket Management System")
            
            await interaction.response.edit_message(embed=unclaim_embed, view=self)
            
            # Notify that ticket is available again
            await channel.send("📢 **Ticket Available** - This ticket is now available for any staff member to claim!")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unclaiming ticket: {str(e)}", ephemeral=True)

    async def lock_ticket(self, interaction: discord.Interaction):
        """Handle ticket locking"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to lock tickets!", ephemeral=True)
            return
        
        try:
            channel = interaction.channel
            
            # Lock channel for non-staff
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await channel.set_permissions(creator, send_messages=False)
            
            # Lock for @everyone
            await channel.set_permissions(interaction.guild.default_role, send_messages=False)
            
            # Update state and buttons
            self.is_locked = True
            self.setup_buttons()
            
            # Update embed
            lock_embed = discord.Embed(
                title="🔒 **Ticket Locked**",
                description=f"This ticket has been locked by {interaction.user.mention}. Only staff can send messages.",
                color=0x6c757d,
                timestamp=datetime.now()
            )
            lock_embed.add_field(
                name="🔐 **Lock Details**",
                value=f"**Locked By:** {interaction.user.display_name}\n**Status:** 🔒 Read-only for non-staff\n**Staff Override:** Active",
                inline=False
            )
            
            await interaction.response.edit_message(embed=lock_embed, view=self)
            
            # Notify about lock
            await channel.send("🔒 **Channel Locked** - Only staff members can send messages now.")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error locking ticket: {str(e)}", ephemeral=True)

    async def unlock_ticket(self, interaction: discord.Interaction):
        """Handle ticket unlocking"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to unlock tickets!", ephemeral=True)
            return
        
        try:
            channel = interaction.channel
            
            # Unlock channel
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await channel.set_permissions(creator, send_messages=True)
            
            # Update state and buttons
            self.is_locked = False
            self.setup_buttons()
            
            # Update embed
            unlock_embed = discord.Embed(
                title="🔓 **Ticket Unlocked**",
                description=f"This ticket has been unlocked by {interaction.user.mention}. Normal messaging resumed.",
                color=0x28a745,
                timestamp=datetime.now()
            )
            unlock_embed.add_field(
                name="🔓 **Unlock Details**",
                value=f"**Unlocked By:** {interaction.user.display_name}\n**Status:** 🔓 Normal messaging\n**Access:** Ticket creator + staff",
                inline=False
            )
            
            await interaction.response.edit_message(embed=unlock_embed, view=self)
            
            # Notify about unlock
            await channel.send("🔓 **Channel Unlocked** - Normal messaging has resumed.")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unlocking ticket: {str(e)}", ephemeral=True)

    async def close_ticket(self, interaction: discord.Interaction):
        """Handle ticket closing"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to close tickets!", ephemeral=True)
            return
        
        try:
            channel = interaction.channel
            
            # Update channel name with black emoji (closed)
            await self.update_channel_name(channel, "⚫")
            
            # Update channel topic
            current_topic = channel.topic or ""
            new_topic = f"⚫ CLOSED by {interaction.user.display_name} • {current_topic}"
            await channel.edit(topic=new_topic)
            
            # Create close confirmation embed
            close_embed = discord.Embed(
                title="⚫ **Ticket Closed**",
                description=f"This ticket has been closed by {interaction.user.mention}",
                color=0x6c757d,
                timestamp=datetime.now()
            )
            close_embed.add_field(
                name="📋 **Closure Details**",
                value=f"**Closed By:** {interaction.user.display_name}\n**Closed At:** <t:{int(datetime.now().timestamp())}:F>\n**Status:** ⚫ Resolved",
                inline=False
            )
            close_embed.add_field(
                name="♻️ **Need to Reopen?**",
                value="If you need to continue this conversation, click the **Reopen Ticket** button below.",
                inline=False
            )
            close_embed.set_footer(text="✨ Ticket closed - Use reopen button if needed")
            
            # Create closed state view
            closed_view = View(timeout=None)
            closed_view.add_item(Button(label="♻️ Reopen", style=discord.ButtonStyle.primary, emoji="♻️", custom_id="reopen_btn"))
            closed_view.add_item(Button(label="🗑️ Delete", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="delete_btn"))
            
            # Copy necessary attributes for closed view
            closed_view.creator_id = self.creator_id
            closed_view.category_key = self.category_key
            closed_view.subcategory = self.subcategory
            
            # Add interaction check for closed view
            async def closed_interaction_check(closed_interaction):
                custom_id = closed_interaction.data.get('custom_id', '')
                if custom_id == "reopen_btn":
                    await self.reopen_ticket(closed_interaction)
                elif custom_id == "delete_btn":
                    await self.delete_ticket(closed_interaction)
                return False
            
            closed_view.interaction_check = closed_interaction_check
            
            await interaction.response.edit_message(embed=close_embed, view=closed_view)
            
            # Log closure
            try:
                db.log_ticket_closure(interaction.guild.id, interaction.user.id, channel.id)
            except:
                pass
            
            # Remove permissions for ticket creator (but keep for staff)
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await channel.set_permissions(creator, read_messages=False, send_messages=False)
                await channel.send(f"📬 {creator.mention}, your ticket has been closed. If you need further assistance, please create a new ticket or ask staff to reopen this one.")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error closing ticket: {str(e)}", ephemeral=True)

    async def reopen_ticket(self, interaction: discord.Interaction):
        """Handle ticket reopening"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to reopen tickets!", ephemeral=True)
            return
        
        try:
            channel = interaction.channel
            
            # Update channel name back to green (reopened)
            await self.update_channel_name(channel, "🟢")
            
            # Update channel topic
            current_topic = channel.topic or ""
            new_topic = f"🟢 REOPENED by {interaction.user.display_name} • {current_topic}"
            await channel.edit(topic=new_topic)
            
            # Restore permissions for ticket creator
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await channel.set_permissions(creator, read_messages=True, send_messages=True)
            
            # Reset state
            self.is_claimed = False
            self.is_locked = False
            self.setup_buttons()
            
            # Create reopen embed
            reopen_embed = discord.Embed(
                title="🟢 **Ticket Reopened**",
                description=f"This ticket has been reopened by {interaction.user.mention}",
                color=0x28a745,
                timestamp=datetime.now()
            )
            reopen_embed.add_field(
                name="📋 **Reopen Details**",
                value=f"**Reopened By:** {interaction.user.display_name}\n**Reopened At:** <t:{int(datetime.now().timestamp())}:F>\n**Status:** 🟢 Active",
                inline=False
            )
            reopen_embed.set_footer(text="✨ Ticket reopened - Continue the conversation")
            
            await interaction.response.edit_message(embed=reopen_embed, view=self)
            
            # Notify parties
            if creator:
                await channel.send(f"🎉 {creator.mention}, your ticket has been reopened! Please continue the conversation here.")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error reopening ticket: {str(e)}", ephemeral=True)

    async def delete_ticket(self, interaction: discord.Interaction):
        """Handle ticket deletion"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to delete tickets!", ephemeral=True)
            return
        
        # Confirmation embed
        confirm_embed = discord.Embed(
            title="⚠️ **Confirm Deletion**",
            description="Are you sure you want to permanently delete this ticket channel?\n\n**This action cannot be undone!**",
            color=0xff4444
        )
        
        # Confirmation view
        class ConfirmDeleteView(View):
            def __init__(self):
                super().__init__(timeout=30)
            
            @discord.ui.button(label="✅ Yes, Delete", style=discord.ButtonStyle.danger)
            async def confirm_delete(self, confirm_interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    await confirm_interaction.response.send_message("🗑️ Deleting ticket channel in 3 seconds...", ephemeral=True)
                    await asyncio.sleep(3)
                    await confirm_interaction.channel.delete()
                except Exception as e:
                    await confirm_interaction.followup.send(f"❌ Error deleting channel: {str(e)}", ephemeral=True)
            
            @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
            async def cancel_delete(self, cancel_interaction: discord.Interaction, button: discord.ui.Button):
                await cancel_interaction.response.edit_message(content="🚫 Deletion cancelled.", embed=None, view=None)
        
        await interaction.response.send_message(embed=confirm_embed, view=ConfirmDeleteView(), ephemeral=True)

# Enhanced Direct Category Ticket Creation
DIRECT_TICKET_CATEGORIES = {
    "general_support": {
        "name": "🆘 General Support",
        "emoji": "🆘",
        "color": 0x7289da,
        "description": "Quick help with general questions and basic support needs"
    },
    "technical_bug": {
        "name": "🔧 Technical Issues", 
        "emoji": "🔧",
        "color": 0xff6b6b,
        "description": "Report bugs, technical problems, or bot issues"
    },
    "billing_vip": {
        "name": "💳 VIP & Billing",
        "emoji": "💳", 
        "color": 0xffd700,
        "description": "VIP membership, premium features, and billing support"
    },
    "report_user": {
        "name": "🚨 Report User/Content",
        "emoji": "🚨",
        "color": 0xff4444,
        "description": "Report users, inappropriate content, or rule violations"
    },
    "appeal_ban": {
        "name": "⚖️ Appeals",
        "emoji": "⚖️",
        "color": 0x9966ff,
        "description": "Appeal bans, warnings, or other moderation actions"
    },
    "partnership": {
        "name": "🤝 Partnership",
        "emoji": "🤝",
        "color": 0x7c3aed,
        "description": "Server partnerships, collaborations, and business inquiries"
    }
}

class DirectTicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Create direct buttons for each category
        row = 0
        for category_key, category_info in DIRECT_TICKET_CATEGORIES.items():
            button = Button(
                label=category_info["name"],
                emoji=category_info["emoji"],
                style=discord.ButtonStyle.secondary,
                custom_id=f"direct_ticket_{category_key}",
                row=row
            )
            button.callback = self.create_direct_ticket
            self.add_item(button)
            
            row += 1
            if row > 4:  # Discord max 5 rows
                break
    
    async def create_direct_ticket(self, interaction: discord.Interaction):
        """Create ticket directly without forms"""
        try:
            # Extract category from button custom_id
            category_key = interaction.data["custom_id"].replace("direct_ticket_", "")
            category_info = DIRECT_TICKET_CATEGORIES[category_key]
            
            # Check for existing ticket
            guild = interaction.guild
            user = interaction.user
            
            existing_channel = None
            for channel in guild.text_channels:
                if channel.name.startswith(f"🟢-ticket-") and f"-{user.id}" in channel.name:
                    existing_channel = channel
                    break
            
            if existing_channel:
                embed = discord.Embed(
                    title="⚠️ **Active Ticket Found**",
                    description=f"You already have an open ticket: {existing_channel.mention}",
                    color=0xff9966
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create ticket instantly
            await self.create_instant_ticket(interaction, category_key, category_info)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating ticket: {str(e)}", ephemeral=True)
    
    async def create_instant_ticket(self, interaction, category_key, category_info):
        """Create ticket instantly without forms"""
        try:
            guild = interaction.guild
            user = interaction.user
            
            # Create category if needed
            category_name = "✨ Support Tickets"
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                try:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False)
                    }
                    category = await guild.create_category(category_name, overwrites=overwrites)
                except discord.Forbidden:
                    category = None
            
            # Simple channel naming with status emoji
            clean_username = user.display_name.lower().replace(' ', '').replace('-', '')[:10]
            channel_name = f"🟢-ticket-{clean_username}"
            
            # Enhanced permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    use_external_emojis=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    manage_channels=True
                )
            }
            
            # Add permissions for staff roles
            server_settings = db.get_server_settings(guild.id)
            ticket_support_roles = server_settings.get('ticket_support_roles', [])
            
            for role_id in ticket_support_roles:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True
                    )
            
            # Add admin permissions
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True,
                        manage_channels=True
                    )
            
            # Create the channel
            try:
                channel = await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites,
                    topic=f"🟢 Open • {category_info['name']} • Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            except discord.Forbidden:
                await interaction.response.send_message("❌ I don't have permission to create channels!", ephemeral=True)
                return
            
            # Send welcome message with ticket controls
            welcome_embed = discord.Embed(
                title=f"{category_info['emoji']} **{category_info['name']} Ticket**",
                description=f"**Hello {user.mention}!** 👋\n\nYour ticket has been created successfully. Please describe your issue below and our support team will assist you shortly.",
                color=category_info['color'],
                timestamp=datetime.now()
            )
            
            welcome_embed.add_field(
                name="📋 **Ticket Information**",
                value=f"**Category:** {category_info['name']}\n**Created:** <t:{int(datetime.now().timestamp())}:F>\n**Status:** 🟢 Open & Waiting for staff",
                inline=True
            )
            
            welcome_embed.add_field(
                name="⏱️ **What to Expect**",
                value="• Staff will respond soon\n• Keep this channel active\n• Be patient and detailed\n• Use the buttons below for actions",
                inline=True
            )
            
            welcome_embed.add_field(
                name="🎯 **Quick Tips**",
                value="• Be specific about your issue\n• Include screenshots if helpful\n• Stay in this channel for updates\n• Our staff team is here to help!",
                inline=False
            )
            
            welcome_embed.set_author(name=f"Support Ticket #{channel.id}", icon_url=guild.icon.url if guild.icon else None)
            welcome_embed.set_footer(text="✨ Thank you for contacting support!")
            
            # Create ticket controls (initially unclaimed)
            controls = CoolTicketControls(user.id, category_key, category_info['name'], is_claimed=False)
            
            await channel.send(embed=welcome_embed, view=controls)
            
            # Ping creation roles (leadmoderator, moderator + creator)
            await controls.ping_creation_roles(channel, user)
            
            # Log ticket creation
            try:
                db.log_ticket_creation(guild.id, user.id, channel.id, category_key, category_info['name'])
            except:
                pass
            
            # Success response
            success_embed = discord.Embed(
                title="✅ **Ticket Created Successfully!**",
                description=f"Your {category_info['name'].lower()} ticket has been created: {channel.mention}",
                color=0x00d4aa
            )
            success_embed.add_field(
                name="🎯 **Next Steps**",
                value="1. Go to your ticket channel\n2. Describe your issue in detail\n3. Wait for staff to respond\n4. Use the buttons for ticket actions",
                inline=False
            )
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating instant ticket: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    # Add persistent views
    bot.add_view(CoolTicketControls(0, "general", "General", is_claimed=False))
    bot.add_view(DirectTicketPanel())
    print("✅ Ticket controls loaded with enhanced state management and creation role pings")