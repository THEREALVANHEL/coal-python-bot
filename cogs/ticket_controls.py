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

# Global lock for preventing duplicate ticket creation
_ticket_creation_locks = {}

class ElegantTicketControls(View):
    def __init__(self, creator_id: int, category_key: str, category_name: str, is_claimed: bool = False, claimer_id: int = None):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.category_key = category_key
        self.category_name = category_name
        self.is_claimed = is_claimed
        self.is_locked = False
        self.claimer_id = claimer_id
        
        # Setup elegant buttons
        self._setup_elegant_buttons()
    
    def _setup_elegant_buttons(self):
        """Setup clean and simple button layout"""
        self.clear_items()
        
        # Row 1: Main actions - simplified
        if self.is_claimed:
            unclaim_btn = Button(
                label="Remove Claim",
                emoji="🔄",
                style=discord.ButtonStyle.secondary,
                custom_id="elegant_unclaim"
            )
            unclaim_btn.callback = self._unclaim_ticket
            self.add_item(unclaim_btn)
        else:
            claim_btn = Button(
                label="Claim", 
                emoji="👤",
                style=discord.ButtonStyle.success,
                custom_id="elegant_claim"
            )
            claim_btn.callback = self._claim_ticket
            self.add_item(claim_btn)
        
        # Lock/Unlock button
        if self.is_locked:
            unlock_btn = Button(
                label="Unlock",
                emoji="🔓", 
                style=discord.ButtonStyle.primary,
                custom_id="elegant_unlock"
            )
            unlock_btn.callback = self._unlock_ticket
            self.add_item(unlock_btn)
        else:
            lock_btn = Button(
                label="Lock",
                emoji="🔒",
                style=discord.ButtonStyle.secondary, 
                custom_id="elegant_lock"
            )
            lock_btn.callback = self._lock_ticket
            self.add_item(lock_btn)
        
        # Close button
        close_btn = Button(
            label="Close",
            emoji="🔐",
            style=discord.ButtonStyle.danger,
            custom_id="elegant_close"
        )
        close_btn.callback = self._close_ticket
        self.add_item(close_btn)

    def _has_permissions(self, user, guild):
        """Check if user has ticket permissions"""
        # Creator always has permissions
        if user.id == self.creator_id:
            return True
        
        # Administrator permissions
        if user.guild_permissions.administrator:
            return True
        
        # Check for special admin permission
        try:
            if has_special_permissions(discord.Interaction(data={}, client=user._state._get_client())):
                return True
        except:
            pass
        
        # Check configured support roles
        try:
            server_settings = db.get_server_settings(guild.id)
            ticket_support_roles = server_settings.get('ticket_support_roles', [])
            
            user_role_ids = [role.id for role in user.roles]
            if any(role_id in user_role_ids for role_id in ticket_support_roles):
                return True
        except:
            pass
        
        # Check specific staff role names (case-insensitive)
        staff_keywords = [
            "admin", "administrator", "mod", "moderator", "staff", "support", "helper", "ticket",
            "uk", "leadmoderator", "lead moderator", "overseer", "forgotten one"
        ]
        
        for role in user.roles:
            role_name_lower = role.name.lower()
            # Check for exact matches and partial matches
            if any(keyword in role_name_lower for keyword in staff_keywords):
                return True
            # Special check for emoji-containing role names
            if any(keyword in role_name_lower.replace('🚨', '').replace('🚓', '').replace('🦥', '').strip() for keyword in staff_keywords):
                return True
        
        return False

    async def _update_channel_status(self, channel, status_type, user=None):
        """Update channel name and topic based on status"""
        try:
            creator = channel.guild.get_member(self.creator_id)
            if not creator:
                return
            
            clean_username = creator.display_name.lower().replace(' ', '').replace('-', '')[:8]
            
            # Update channel name based on status
            if status_type == "claimed" and user:
                claimer_name = user.display_name.lower().replace(' ', '')[:6]
                new_name = f"🟡・{claimer_name}・{clean_username}"
            elif status_type == "closed":
                new_name = f"🔒・closed・{clean_username}"
            else:  # open
                new_name = f"🟢・open・{clean_username}"
            
            await channel.edit(name=new_name)
            
            # Update topic
            current_topic = channel.topic or ""
            base_topic = f"{self.category_name} • User: {self.creator_id}"
            
            if status_type == "claimed" and user:
                new_topic = f"🟡 CLAIMED by {user.display_name} • {base_topic}"
            elif status_type == "closed":
                new_topic = f"🔒 CLOSED • {base_topic}"
            else:
                new_topic = f"🟢 OPEN • {base_topic}"
            
            await channel.edit(topic=new_topic)
            
        except Exception as e:
            print(f"Error updating channel status: {e}")

    async def _create_elegant_embed(self, title, description, color, fields=None, footer=None):
        """Create clean and simple embed"""
        embed = discord.Embed(
            title=f"🎫 {title}",
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        
        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", False)
                )
        
        if footer:
            embed.set_footer(text=footer)
        else:
            embed.set_footer(text="🎫 Ticket System")
        
        return embed

    async def _claim_ticket(self, interaction: discord.Interaction):
        """Handle ticket claiming"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = await self._create_elegant_embed(
                "Access Denied",
                "❌ You don't have permission to claim tickets.",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if self.is_claimed:
            embed = await self._create_elegant_embed(
                "Already Claimed", 
                "⚠️ This ticket is already claimed.",
                0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Update channel
            await self._update_channel_status(interaction.channel, "claimed", interaction.user)
            
            # Update state
            self.is_claimed = True
            self.claimer_id = interaction.user.id
            self._setup_elegant_buttons()
            
            # Send claim notification (MEE6 style)
            await interaction.response.send_message(f"**@{interaction.user.display_name} claimed the ticket.**")
            
            # Edit the original pinned message with updated buttons
            try:
                async for message in interaction.channel.history(limit=50):
                    if message.pinned and message.author.bot and message.embeds:
                        await message.edit(view=self)
                        break
            except:
                pass
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Claim Failed",
                f"❌ Error: {str(e)[:50]}",
                0xff6b6b
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

    async def _unclaim_ticket(self, interaction: discord.Interaction):
        """Handle ticket unclaiming"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = await self._create_elegant_embed(
                "Access Denied",
                "❌ You don't have permission to unclaim tickets.",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if not self.is_claimed:
            embed = await self._create_elegant_embed(
                "Not Claimed",
                "⚠️ This ticket is not claimed.",
                0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Update channel
            await self._update_channel_status(interaction.channel, "open")
            
            # Update state
            self.is_claimed = False
            self.claimer_id = None
            self._setup_elegant_buttons()
            
            # Send unclaim notification
            await interaction.response.send_message(f"**@{interaction.user.display_name} unclaimed the ticket.**")
            
            # Edit the original pinned message with updated buttons
            try:
                async for message in interaction.channel.history(limit=50):
                    if message.pinned and message.author.bot and message.embeds:
                        await message.edit(view=self)
                        break
            except:
                pass
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Unclaim Failed",
                f"❌ Error: {str(e)[:50]}",
                0xff6b6b
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

    async def _lock_ticket(self, interaction: discord.Interaction):
        """Handle ticket locking"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = await self._create_elegant_embed(
                "Access Denied",
                "❌ You don't have permission to lock tickets.",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Lock permissions
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await interaction.channel.set_permissions(creator, send_messages=False)
            
            # Update state
            self.is_locked = True
            self._setup_elegant_buttons()
            
            # Simple lock embed
            embed = await self._create_elegant_embed(
                "Ticket Locked",
                f"🔒 {interaction.user.display_name} locked this ticket.",
                0x6c757d
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Lock Failed",
                f"❌ Error: {str(e)[:50]}",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _unlock_ticket(self, interaction: discord.Interaction):
        """Handle ticket unlocking"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = await self._create_elegant_embed(
                "Access Denied",
                "❌ You don't have permission to unlock tickets.",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Unlock permissions
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await interaction.channel.set_permissions(creator, send_messages=True)
            
            # Update state
            self.is_locked = False
            self._setup_elegant_buttons()
            
            # Simple unlock embed
            embed = await self._create_elegant_embed(
                "Ticket Unlocked",
                f"🔓 {interaction.user.display_name} unlocked this ticket.",
                0x28a745
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Unlock Failed",
                f"❌ Error: {str(e)[:50]}",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _close_ticket(self, interaction: discord.Interaction):
        """Handle ticket closing"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = await self._create_elegant_embed(
                "Access Denied",
                "❌ You don't have permission to close tickets.",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Update channel status
            await self._update_channel_status(interaction.channel, "closed")
            
            # Send close notification  
            await interaction.response.send_message(f"**Ticket closed by @{interaction.user.display_name}**")
            
            # Create closed ticket view
            closed_view = ElegantClosedControls(self.creator_id, self.category_key, self.category_name)
            
            # Edit the original pinned message with closed buttons
            try:
                async for message in interaction.channel.history(limit=50):
                    if message.pinned and message.author.bot and message.embeds:
                        await message.edit(view=closed_view)
                        break
            except:
                pass
            
            # Remove user permissions but keep for staff
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await interaction.channel.set_permissions(creator, read_messages=True, send_messages=False)
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Close Failed",
                f"❌ Error: {str(e)[:50]}",
                0xff6b6b
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

    async def _set_priority(self, interaction: discord.Interaction):
        """Handle priority setting"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = await self._create_elegant_embed(
                "Access Denied",
                "❌ You don't have permission to set priority.",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create priority selection view
        priority_view = ElegantPriorityView()
        
        embed = await self._create_elegant_embed(
            "Set Ticket Priority",
            "🎯 Choose the appropriate priority level for this ticket:",
            0x7c3aed,
            fields=[
                {
                    "name": "Priority Levels",
                    "value": "🟢 **Low** - General questions\n🟡 **Medium** - Standard issues\n🟠 **High** - Urgent problems\n🔴 **Critical** - Emergency situations",
                    "inline": False
                }
            ]
        )
        
        await interaction.response.send_message(embed=embed, view=priority_view, ephemeral=True)

    async def _show_admin_tools(self, interaction: discord.Interaction):
        """Show advanced admin tools panel"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = await self._create_elegant_embed(
                "🚫 Access Denied",
                "You don't have permission to access admin tools.",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create admin tools embed
        embed = discord.Embed(
            title="🛠️ **Advanced Admin Tools**",
            description="**Professional ticket management interface with advanced controls**",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎯 **Quick Actions**",
            value="""
            🔄 **Transfer Ticket** - Move to another staff member
            📝 **Add Note** - Internal staff note (invisible to user)
            🏷️ **Add Tags** - Categorize and organize
            📊 **View Analytics** - Ticket performance metrics
            """,
            inline=True
        )
        
        embed.add_field(
            name="⚙️ **Advanced Controls**",
            value="""
            🕒 **Set Timer** - Auto-close after inactivity  
            📱 **Send DM** - Direct message to ticket creator
            🔗 **Link Tickets** - Connect related issues
            📋 **Generate Report** - Detailed ticket summary
            """,
            inline=True
        )
        
        embed.add_field(
            name="🚨 **Emergency Actions**",
            value="""
            🚫 **Force Close** - Immediate closure with reason
            🔒 **Escalate** - Alert senior staff members
            ⚠️ **Flag User** - Mark for mod attention
            🗑️ **Archive** - Move to archive category
            """,
            inline=False
        )
        
        embed.set_footer(text="🛠️ Admin Tools • Ultra-Professional Interface")
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/876543210987654321.png")
        
        # Create admin tools view
        admin_view = ElegantAdminToolsView(self.creator_id, self.category_key, self.category_name)
        
        await interaction.response.send_message(embed=embed, view=admin_view, ephemeral=True)

class ElegantClosedControls(View):
    def __init__(self, creator_id: int, category_key: str, category_name: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.category_key = category_key 
        self.category_name = category_name
        
        # Reopen button
        reopen_btn = Button(
            label="Reopen Ticket",
            emoji="♻️",
            style=discord.ButtonStyle.success,
            custom_id="elegant_reopen"
        )
        reopen_btn.callback = self._reopen_ticket
        self.add_item(reopen_btn)
        
        # Delete button  
        delete_btn = Button(
            label="Delete Ticket",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id="elegant_delete"
        )
        delete_btn.callback = self._delete_ticket
        self.add_item(delete_btn)

    def _has_permissions(self, user, guild):
        """Check if user has ticket permissions"""
        # Creator always has permissions
        if user.id == self.creator_id:
            return True
        
        # Administrator permissions
        if user.guild_permissions.administrator:
            return True
        
        # Check configured support roles
        try:
            server_settings = db.get_server_settings(guild.id)
            ticket_support_roles = server_settings.get('ticket_support_roles', [])
            user_role_ids = [role.id for role in user.roles]
            if any(role_id in user_role_ids for role_id in ticket_support_roles):
                return True
        except:
            pass
        
        # Check specific staff role names (case-insensitive)
        staff_keywords = [
            "admin", "administrator", "mod", "moderator", "staff", "support", "helper", "ticket",
            "uk", "leadmoderator", "lead moderator", "overseer", "forgotten one"
        ]
        
        for role in user.roles:
            role_name_lower = role.name.lower()
            # Check for exact matches and partial matches
            if any(keyword in role_name_lower for keyword in staff_keywords):
                return True
            # Special check for emoji-containing role names
            if any(keyword in role_name_lower.replace('🚨', '').replace('🚓', '').replace('🦥', '').strip() for keyword in staff_keywords):
                return True
        
        return False

    async def _reopen_ticket(self, interaction: discord.Interaction):
        """Handle elegant ticket reopening"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You don't have permission to reopen tickets.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Update channel name back to open
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                clean_username = creator.display_name.lower().replace(' ', '').replace('-', '')[:8]
                await interaction.channel.edit(name=f"🟢・open・{clean_username}")
            
            # Restore user permissions
            if creator:
                await interaction.channel.set_permissions(creator, read_messages=True, send_messages=True)
            
            # Simple reopen embed
            embed = discord.Embed(
                title="🔓 Ticket Reopened",
                description=f"Reopened by **{interaction.user.display_name}**",
                color=0x28a745
            )
            
            # Reset to normal controls
            controls = ElegantTicketControls(self.creator_id, self.category_key, self.category_name, is_claimed=False)
            
            await interaction.response.edit_message(embed=embed, view=controls)
            
            # Notify creator if different user
            if creator and creator.id != interaction.user.id:
                await interaction.followup.send(f"{creator.mention} Your ticket has been reopened.")
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to reopen ticket",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _delete_ticket(self, interaction: discord.Interaction):
        """Handle elegant ticket deletion with confirmation"""
        if not self._has_permissions(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You don't have permission to delete tickets.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create elegant confirmation
        embed = discord.Embed(
            title="⚠️ Confirm Ticket Deletion",
            description="Are you sure you want to **permanently delete** this ticket?\n\n**This action cannot be undone!**",
            color=0xff4444,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="⚠️ Warning",
            value="• All conversation history will be lost\n• Ticket data will be permanently removed\n• Users won't be able to reference this ticket",
            inline=False
        )
        
        # Confirmation buttons
        class ElegantDeleteConfirmation(View):
            def __init__(self):
                super().__init__(timeout=30)
            
            @discord.ui.button(label="Yes, Delete Forever", style=discord.ButtonStyle.danger, emoji="🗑️")
            async def confirm_delete(self, confirm_interaction: discord.Interaction, button: discord.ui.Button):
                try:
                    await confirm_interaction.response.send_message("🗑️ Deleting ticket in 3 seconds...", ephemeral=True)
                    await asyncio.sleep(3)
                    await confirm_interaction.channel.delete(reason=f"Ticket deleted by {interaction.user.display_name}")
                except Exception as e:
                    await confirm_interaction.followup.send(f"❌ Deletion failed: {str(e)}", ephemeral=True)
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
            async def cancel_delete(self, cancel_interaction: discord.Interaction, button: discord.ui.Button):
                cancel_embed = discord.Embed(
                    title="✅ Deletion Cancelled",
                    description="The ticket has been preserved and remains accessible.",
                    color=0x28a745
                )
                await cancel_interaction.response.edit_message(embed=cancel_embed, view=None)
        
        await interaction.response.send_message(embed=embed, view=ElegantDeleteConfirmation(), ephemeral=True)

class ElegantPriorityView(View):
    def __init__(self):
        super().__init__(timeout=60)
        
        priorities = [
            {"name": "Low", "emoji": "🟢", "style": discord.ButtonStyle.success},
            {"name": "Medium", "emoji": "🟡", "style": discord.ButtonStyle.secondary},
            {"name": "High", "emoji": "🟠", "style": discord.ButtonStyle.primary},
            {"name": "Critical", "emoji": "🔴", "style": discord.ButtonStyle.danger}
        ]
        
        for priority in priorities:
            btn = Button(
                label=f"{priority['name']} Priority",
                emoji=priority['emoji'],
                style=priority['style']
            )
            btn.callback = lambda i, p=priority: self._set_priority(i, p)
            self.add_item(btn)
    
    async def _set_priority(self, interaction: discord.Interaction, priority_info):
        """Set ticket priority"""
        embed = discord.Embed(
            title="✅ Priority Updated",
            description=f"Ticket priority has been set to **{priority_info['emoji']} {priority_info['name']}**",
            color=0x00d4aa,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Priority Details",
            value=f"**Level:** {priority_info['name']}\n**Set By:** {interaction.user.display_name}\n**Updated:** <t:{int(datetime.now().timestamp())}:F>",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)

# Simplified ticket categories
ELEGANT_TICKET_CATEGORIES = {
    "general": {
        "name": "General Support",
        "description": "General questions and assistance",
        "emoji": "💬",
        "color": 0x7c3aed
    },
    "technical": {
        "name": "Technical Issues", 
        "description": "Bot problems and technical difficulties",
        "emoji": "🔧",
        "color": 0xff6b6b
    },
    "account": {
        "name": "Account Help",
        "description": "Profile issues and account problems",
        "emoji": "👤", 
        "color": 0x00d4aa
    }
}



def check_existing_ticket_strict(guild, user_id):
    """Strict checking for existing tickets to prevent duplicates"""
    for channel in guild.text_channels:
        # Check channel topic for user ID (most reliable)
        if channel.topic and f"User: {user_id}" in channel.topic:
            # Double check it's actually a ticket channel
            if any(indicator in channel.name.lower() for indicator in ["open", "claimed", "closed", "ticket"]):
                return channel
        
        # Backup check for channel permissions
        try:
            member = guild.get_member(user_id)
            if member and channel.permissions_for(member).read_messages:
                # Check if user has special permissions in this channel (indicating ownership)
                overwrites = channel.overwrites_for(member)
                if overwrites.send_messages is True and any(word in channel.name.lower() for word in ["ticket", "support"]):
                    return channel
        except:
            pass
    
    return None

class ElegantTicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self._setup_simple_buttons()
    
    def _setup_simple_buttons(self):
        """Setup simple ticket creation buttons"""
        self.clear_items()
        
        # Simple 3-button layout
        general_btn = Button(
            label="General Support",
            emoji="💬",
            style=discord.ButtonStyle.primary,
            custom_id="ticket_general"
        )
        general_btn.callback = lambda i: self._create_elegant_ticket(i, "general")
        self.add_item(general_btn)
        
        technical_btn = Button(
            label="Technical Issues",
            emoji="🔧", 
            style=discord.ButtonStyle.danger,
            custom_id="ticket_technical"
        )
        technical_btn.callback = lambda i: self._create_elegant_ticket(i, "technical")
        self.add_item(technical_btn)
        
        account_btn = Button(
            label="Account Help",
            emoji="👤",
            style=discord.ButtonStyle.success,
            custom_id="ticket_account"
        )
        account_btn.callback = lambda i: self._create_elegant_ticket(i, "account")
        self.add_item(account_btn)

    async def _create_elegant_ticket(self, interaction: discord.Interaction, category_key: str):
        """Create elegant ticket with duplicate prevention"""
        try:
            guild = interaction.guild
            user = interaction.user
            category_info = ELEGANT_TICKET_CATEGORIES[category_key]
            
            # Prevent duplicate tickets with global lock
            lock_key = f"{guild.id}_{user.id}"
            if lock_key in _ticket_creation_locks:
                embed = discord.Embed(
                    title="⏳ Ticket Creation in Progress",
                    description="Please wait, your ticket is already being created...",
                    color=0xff9966
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Set lock
            _ticket_creation_locks[lock_key] = True
            
            try:
                # Strict existing ticket check
                existing_channel = check_existing_ticket_strict(guild, user.id)
                
                if existing_channel:
                    embed = discord.Embed(
                        title="🎫 Active Ticket Found",
                        description=f"You already have an active ticket: {existing_channel.mention}",
                        color=0xff9966,
                        timestamp=datetime.now()
                    )
                    embed.add_field(
                        name="💡 What to do?",
                        value="Please continue your conversation in the existing ticket or close it first before creating a new one.",
                        inline=False
                    )
                    embed.set_footer(text="🎫 One ticket per person policy")
                    
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Create ticket
                await self._create_instant_elegant_ticket(interaction, category_key, category_info)
                
            finally:
                # Remove lock
                if lock_key in _ticket_creation_locks:
                    del _ticket_creation_locks[lock_key]
            
        except Exception as e:
            # Clean up lock on error
            lock_key = f"{guild.id}_{user.id}"
            if lock_key in _ticket_creation_locks:
                del _ticket_creation_locks[lock_key]
            
            embed = discord.Embed(
                title="❌ Ticket Creation Failed",
                description=f"An error occurred: {str(e)[:100]}",
                color=0xff6b6b
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _create_instant_elegant_ticket(self, interaction, category_key, category_info):
        """Create beautiful instant ticket"""
        try:
            guild = interaction.guild
            user = interaction.user
            
            # Get or create unified category
            category_name = "✨ Support Center"
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                try:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False)
                    }
                    category = await guild.create_category(category_name, overwrites=overwrites)
                except discord.Forbidden:
                    category = None
            
            # Elegant channel naming
            clean_username = user.display_name.lower().replace(' ', '').replace('-', '')[:8]
            channel_name = f"🟢・open・{clean_username}"
            
            # Enhanced permissions setup
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    use_external_emojis=True,
                    add_reactions=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True,
                    manage_channels=True,
                    use_external_emojis=True
                )
            }
            
            # Add staff permissions
            try:
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
                            read_message_history=True,
                            use_external_emojis=True
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
            except:
                pass
            
            # Create the elegant ticket channel
            try:
                # Generate unique ticket number using timestamp
                ticket_number = str(int(datetime.now().timestamp()))[-4:]
                
                channel = await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites,
                    topic=f"Ticket #{ticket_number} - Type: {category_info['emoji']} {category_info['name']} - Created by: @{user.display_name}"
                )
            except discord.Forbidden:
                embed = discord.Embed(
                    title="❌ Permission Error",
                    description="I don't have permission to create channels. Please contact an administrator.",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create professional MEE6-style welcome embed with BLEKNEPHEW branding
            welcome_embed = discord.Embed(
                title=f"📫 BlackOps Group Support / Ticket #{ticket_number}",
                description=f"**Ticket #{ticket_number}** - Type: {category_info['emoji']} {category_info['name']} - Created by: @{user.display_name}",
                color=0x7289da
            )
            
            # Professional welcome message
            welcome_message = (
                f"Welcome to BlackOps Group support. Your ticket has been received by us and you have entered our queue. "
                f"A dedicated staff member will be with you shortly. Response times may vary.\n\n"
                f"**❕ Important Information**\n"
                f"You can already provide a description of your question or issue to help speed-up the process. "
                f"If you provide a description before your ticket is claimed, we can address your concerns faster."
            )
            
            welcome_embed.add_field(
                name="",
                value=welcome_message,
                inline=False
            )
            
            welcome_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            # Create elegant controls
            controls = ElegantTicketControls(user.id, category_key, category_info['name'], is_claimed=False)
            
            # Send welcome message
            welcome_msg = await channel.send(embed=welcome_embed, view=controls)
            
            # Pin the welcome message
            try:
                await welcome_msg.pin()
                # Send pin notification like MEE6
                pin_notification = await channel.send(f"**BLEKNEPHEW** pinned a message to this channel.")
            except:
                pass
            
            # Ping staff - permanently visible until ticket closed
            try:
                server_settings = db.get_server_settings(guild.id)
                ticket_support_roles = server_settings.get('ticket_support_roles', [])
                
                roles_to_ping = []
                
                # Add configured support roles
                for role_id in ticket_support_roles:
                    role = guild.get_role(role_id)
                    if role:
                        roles_to_ping.append(role)
                
                # Add specific staff roles mentioned
                staff_role_names = ["uk", "leadmoderator", "lead moderator", "moderator", "overseer", "forgotten one"]
                for role in guild.roles:
                    role_name_lower = role.name.lower()
                    # Check for exact matches and partial matches
                    if any(staff_name in role_name_lower for staff_name in staff_role_names):
                        if role not in roles_to_ping:
                            roles_to_ping.append(role)
                    # Special check for emoji-containing role names
                    clean_role_name = role_name_lower.replace('🚨', '').replace('🚓', '').replace('🦥', '').strip()
                    if any(staff_name in clean_role_name for staff_name in staff_role_names):
                        if role not in roles_to_ping:
                            roles_to_ping.append(role)
                
                if roles_to_ping:
                    ping_mentions = " ".join([role.mention for role in roles_to_ping])
                    staff_ping_message = await channel.send(f"{ping_mentions} {user.mention}")
                    
                    # Pin the staff notification (like MEE6 does)
                    try:
                        await staff_ping_message.pin()
                    except:
                        pass
            except Exception as e:
                print(f"Error pinging staff: {e}")
            
            # Log ticket creation
            try:
                db.log_ticket_creation(guild.id, user.id, channel.id, category_key, category_info['name'])
            except:
                pass
            
            # Simple success response
            success_embed = discord.Embed(
                title="✅ Ticket Created",
                description=f"Your ticket: {channel.mention}",
                color=0x00d4aa
            )
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Creation Error",
                description=f"Failed to create ticket: {str(e)[:100]}",
                color=0xff6b6b
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    # Add persistent views
    bot.add_view(ElegantTicketControls(0, "general", "General Support", is_claimed=False))
    bot.add_view(ElegantTicketPanel())
    print("✅ Elegant ticket system loaded with beautiful interface and duplicate prevention")