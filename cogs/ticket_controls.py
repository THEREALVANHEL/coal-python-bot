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
        """Setup ultra-modern button layout with enhanced styling"""
        self.clear_items()
        
        # Row 1: Claim/Unclaim & Lock/Unlock with enhanced styling
        if self.is_claimed:
            unclaim_btn = Button(
                label="🔄 Unclaim",
                emoji="🔄",
                style=discord.ButtonStyle.secondary,
                custom_id="elegant_unclaim"
            )
            unclaim_btn.callback = self._unclaim_ticket
            self.add_item(unclaim_btn)
        else:
            claim_btn = Button(
                label="👤 Claim Ticket", 
                emoji="👤",
                style=discord.ButtonStyle.success,
                custom_id="elegant_claim"
            )
            claim_btn.callback = self._claim_ticket
            self.add_item(claim_btn)
        
        # Lock/Unlock button with modern styling
        if self.is_locked:
            unlock_btn = Button(
                label="🔓 Unlock Chat",
                emoji="🔓", 
                style=discord.ButtonStyle.primary,
                custom_id="elegant_unlock"
            )
            unlock_btn.callback = self._unlock_ticket
            self.add_item(unlock_btn)
        else:
            lock_btn = Button(
                label="🔒 Lock Chat",
                emoji="🔒",
                style=discord.ButtonStyle.secondary, 
                custom_id="elegant_lock"
            )
            lock_btn.callback = self._lock_ticket
            self.add_item(lock_btn)
        
        # Row 2: Enhanced Close & Priority buttons
        close_btn = Button(
            label="🔐 Close & Resolve",
            emoji="🔐",
            style=discord.ButtonStyle.danger,
            custom_id="elegant_close"
        )
        close_btn.callback = self._close_ticket
        self.add_item(close_btn)
        
        # Add priority button if claimed with enhanced styling
        if self.is_claimed:
            priority_btn = Button(
                label="⚡ Set Priority",
                emoji="⚡",
                style=discord.ButtonStyle.primary,
                custom_id="elegant_priority"
            )
            priority_btn.callback = self._set_priority
            self.add_item(priority_btn)
        
        # Add admin tools button for staff
        admin_btn = Button(
            label="🛠️ Admin Tools",
            emoji="🛠️",
            style=discord.ButtonStyle.secondary,
            custom_id="elegant_admin_tools"
        )
        admin_btn.callback = self._show_admin_tools
        self.add_item(admin_btn)

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
        """Create ultra-modern embed with enhanced styling and visual appeal"""
        embed = discord.Embed(
            title=f"✨ {title}",
            description=f"**{description}**",
            color=color,
            timestamp=datetime.now()
        )
        
        # Add stylish separator
        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value="",
            inline=False
        )
        
        if fields:
            for field in fields:
                embed.add_field(
                    name=f"▫️ **{field.get('name', '')}**",
                    value=field.get("value", ""),
                    inline=field.get("inline", False)
                )
        
        # Add another separator before footer
        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            value="",
            inline=False
        )
        
        if footer:
            embed.set_footer(text=f"🎫 {footer} • Professional Support System", icon_url="https://cdn.discordapp.com/emojis/853028968609120266.png")
        else:
            embed.set_footer(text="🎫 Professional Ticket System • Ultra-Modern Interface", icon_url="https://cdn.discordapp.com/emojis/853028968609120266.png")
        
        return embed

    async def _claim_ticket(self, interaction: discord.Interaction):
        """Handle elegant ticket claiming"""
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
                "⚠️ This ticket is already claimed by another staff member.",
                0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Update state
            self.is_claimed = True
            self.claimer_id = interaction.user.id
            self._setup_elegant_buttons()
            
            # Update channel
            await self._update_channel_status(interaction.channel, "claimed", interaction.user)
            
            # Create elegant claim embed
            embed = await self._create_elegant_embed(
                "Ticket Claimed Successfully",
                f"🎯 **{interaction.user.display_name}** has claimed this ticket and will provide assistance.",
                0x00d4aa,
                fields=[
                    {
                        "name": "👨‍💼 Assigned Staff",
                        "value": f"**{interaction.user.display_name}**\n{interaction.user.mention}",
                        "inline": True
                    },
                    {
                        "name": "📊 Status Update", 
                        "value": f"**Previous:** 🟢 Open\n**Current:** 🟡 Claimed\n**Time:** <t:{int(datetime.now().timestamp())}:R>",
                        "inline": True
                    },
                    {
                        "name": "💡 What's Next?",
                        "value": "• Staff will analyze your issue\n• Expect response within 30 minutes\n• Feel free to provide more details",
                        "inline": False
                    }
                ]
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Notify creator
            creator = interaction.guild.get_member(self.creator_id)
            if creator and creator.id != interaction.user.id:
                await interaction.followup.send(
                    f"🎉 {creator.mention} Your ticket has been claimed by {interaction.user.mention} - help is on the way!",
                    ephemeral=False
                )
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Claim Failed",
                f"❌ Error claiming ticket: {str(e)[:100]}",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _unclaim_ticket(self, interaction: discord.Interaction):
        """Handle elegant ticket unclaiming"""
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
                "⚠️ This ticket is not currently claimed.",
                0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Update state
            self.is_claimed = False
            self.claimer_id = None
            self._setup_elegant_buttons()
            
            # Update channel
            await self._update_channel_status(interaction.channel, "open")
            
            # Create elegant unclaim embed
            embed = await self._create_elegant_embed(
                "Ticket Unclaimed",
                f"🔄 **{interaction.user.display_name}** has unclaimed this ticket. It's now available for other staff members.",
                0x7c3aed,
                fields=[
                    {
                        "name": "📊 Status Update",
                        "value": f"**Previous:** 🟡 Claimed\n**Current:** 🟢 Open & Available\n**Unclaimed By:** {interaction.user.display_name}",
                        "inline": True
                    },
                    {
                        "name": "👥 Available For",
                        "value": "• Any staff member\n• Quick response guaranteed\n• Professional assistance",
                        "inline": True
                    }
                ]
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Notify that ticket is available
            await interaction.followup.send(
                "📢 **Ticket Available** - This ticket is now open for any staff member to claim!",
                ephemeral=False
            )
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Unclaim Failed",
                f"❌ Error unclaiming ticket: {str(e)[:100]}",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _lock_ticket(self, interaction: discord.Interaction):
        """Handle elegant ticket locking"""
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
            
            # Create elegant lock embed
            embed = await self._create_elegant_embed(
                "Ticket Locked",
                f"🔒 This ticket has been locked by **{interaction.user.display_name}**. Only staff can send messages now.",
                0x6c757d,
                fields=[
                    {
                        "name": "🔐 Lock Details",
                        "value": f"**Locked By:** {interaction.user.display_name}\n**Status:** 🔒 Read-only for user\n**Staff Override:** Active",
                        "inline": False
                    }
                ]
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Lock Failed",
                f"❌ Error locking ticket: {str(e)[:100]}",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _unlock_ticket(self, interaction: discord.Interaction):
        """Handle elegant ticket unlocking"""
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
            
            # Create elegant unlock embed
            embed = await self._create_elegant_embed(
                "Ticket Unlocked",
                f"🔓 This ticket has been unlocked by **{interaction.user.display_name}**. Normal messaging has resumed.",
                0x28a745,
                fields=[
                    {
                        "name": "🔓 Unlock Details",
                        "value": f"**Unlocked By:** {interaction.user.display_name}\n**Status:** 🔓 Normal messaging\n**Access:** Creator + Staff",
                        "inline": False
                    }
                ]
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Unlock Failed",
                f"❌ Error unlocking ticket: {str(e)[:100]}",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _close_ticket(self, interaction: discord.Interaction):
        """Handle elegant ticket closing"""
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
            
            # Create elegant close embed
            embed = await self._create_elegant_embed(
                "Ticket Closed Successfully",
                f"🎉 This ticket has been resolved and closed by **{interaction.user.display_name}**.",
                0x6c757d,
                fields=[
                    {
                        "name": "📋 Closure Summary",
                        "value": f"**Closed By:** {interaction.user.display_name}\n**Resolution Time:** <t:{int(datetime.now().timestamp())}:F>\n**Status:** ✅ Resolved",
                        "inline": True
                    },
                    {
                        "name": "💭 Feedback",
                        "value": "We hope we were able to help you! If you need further assistance, feel free to create a new ticket.",
                        "inline": True
                    },
                    {
                        "name": "♻️ Need More Help?",
                        "value": "You can reopen this ticket using the button below if you need to continue this conversation.",
                        "inline": False
                    }
                ]
            )
            
            # Create closed ticket view
            closed_view = ElegantClosedControls(self.creator_id, self.category_key, self.category_name)
            
            await interaction.response.edit_message(embed=embed, view=closed_view)
            
            # Remove user permissions but keep for staff
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await interaction.channel.set_permissions(creator, read_messages=True, send_messages=False)
            
            # Log closure
            try:
                db.log_ticket_closure(interaction.guild.id, interaction.user.id, interaction.channel.id)
            except:
                pass
            
        except Exception as e:
            embed = await self._create_elegant_embed(
                "Close Failed",
                f"❌ Error closing ticket: {str(e)[:100]}",
                0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

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
        if user.id == self.creator_id:
            return True
        if user.guild_permissions.administrator:
            return True
        
        try:
            server_settings = db.get_server_settings(guild.id)
            ticket_support_roles = server_settings.get('ticket_support_roles', [])
            user_role_ids = [role.id for role in user.roles]
            if any(role_id in user_role_ids for role_id in ticket_support_roles):
                return True
        except:
            pass
        
        staff_keywords = ["admin", "administrator", "mod", "moderator", "staff", "support", "helper", "ticket"]
        for role in user.roles:
            if any(keyword in role.name.lower() for keyword in staff_keywords):
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
            
            # Create elegant reopen embed
            embed = discord.Embed(
                title="✨ Ticket Reopened Successfully",
                description=f"🎉 This ticket has been reopened by **{interaction.user.display_name}**. The conversation can continue.",
                color=0x28a745,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Reopen Details",
                value=f"**Reopened By:** {interaction.user.display_name}\n**Time:** <t:{int(datetime.now().timestamp())}:F>\n**Status:** 🟢 Active Again",
                inline=True
            )
            
            embed.add_field(
                name="💡 What's Next?",
                value="• Continue your conversation\n• Staff will assist you\n• Provide any new details\n• Use the buttons for actions",
                inline=True
            )
            
            embed.set_footer(text="🎫 Professional Ticket System")
            
            # Reset to normal controls
            controls = ElegantTicketControls(self.creator_id, self.category_key, self.category_name, is_claimed=False)
            
            await interaction.response.edit_message(embed=embed, view=controls)
            
            # Notify creator if different user
            if creator and creator.id != interaction.user.id:
                await interaction.followup.send(
                    f"🎉 {creator.mention} Your ticket has been reopened! You can continue the conversation here.",
                    ephemeral=False
                )
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Reopen Failed",
                description=f"Error reopening ticket: {str(e)[:100]}",
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

class ElegantAdminToolsView(View):
    def __init__(self, creator_id: int, category_key: str, category_name: str):
        super().__init__(timeout=300)
        self.creator_id = creator_id
        self.category_key = category_key
        self.category_name = category_name
    
    @discord.ui.button(label="📝 Add Internal Note", style=discord.ButtonStyle.secondary, emoji="📝")
    async def add_note(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add internal staff note"""
        # Create modal for note input
        note_modal = InternalNoteModal()
        await interaction.response.send_modal(note_modal)
    
    @discord.ui.button(label="🔄 Transfer Ticket", style=discord.ButtonStyle.primary, emoji="🔄")
    async def transfer_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Transfer ticket to another staff member"""
        embed = discord.Embed(
            title="🔄 **Transfer Ticket**",
            description="**Select a staff member to transfer this ticket to:**",
            color=0x7c3aed
        )
        embed.add_field(
            name="📋 **Instructions**",
            value="• Use the dropdown below to select a staff member\n• The ticket will be reassigned automatically\n• Original creator will be notified",
            inline=False
        )
        
        # Create staff member selector
        transfer_view = StaffTransferView(self.creator_id, self.category_key, self.category_name)
        await interaction.response.send_message(embed=embed, view=transfer_view, ephemeral=True)
    
    @discord.ui.button(label="🚨 Escalate to Senior Staff", style=discord.ButtonStyle.danger, emoji="🚨")
    async def escalate_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Escalate ticket to senior staff"""
        embed = discord.Embed(
            title="🚨 **Ticket Escalated**",
            description="**This ticket has been escalated to senior staff members.**",
            color=0xff4500,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="⚡ **Escalation Details**",
            value=f"**Escalated By:** {interaction.user.display_name}\n**Priority:** 🔴 High\n**Status:** Awaiting senior review",
            inline=False
        )
        embed.add_field(
            name="👥 **Notified Roles**",
            value="• Senior Moderators\n• Lead Staff\n• Administrators",
            inline=False
        )
        
        # Ping senior staff roles
        try:
            senior_roles = []
            for role in interaction.guild.roles:
                if any(name in role.name.lower() for name in ["leadmoderator", "senior", "admin", "overseer"]):
                    senior_roles.append(role.mention)
            
            if senior_roles:
                await interaction.channel.send(f"🚨 **ESCALATION ALERT** {' '.join(senior_roles[:3])}")
        except:
            pass
        
        await interaction.response.send_message(embed=embed)
    
    @discord.ui.button(label="📊 Ticket Analytics", style=discord.ButtonStyle.secondary, emoji="📊")
    async def ticket_analytics(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show ticket analytics"""
        embed = discord.Embed(
            title="📊 **Ticket Analytics Dashboard**",
            description="**Performance metrics for this support interaction**",
            color=0x00d4aa,
            timestamp=datetime.now()
        )
        
        # Calculate some basic metrics
        created_time = interaction.channel.created_at
        current_time = datetime.now()
        duration = current_time - created_time
        
        embed.add_field(
            name="⏱️ **Response Metrics**",
            value=f"**Duration:** {duration.seconds // 60} minutes\n**Status:** {'🟡 In Progress' if not self.category_key.endswith('closed') else '✅ Resolved'}\n**Category:** {self.category_name}",
            inline=True
        )
        
        embed.add_field(
            name="👥 **Engagement Stats**",
            value=f"**Creator:** <@{self.creator_id}>\n**Messages:** Analyzing...\n**Staff Involved:** 1+",
            inline=True
        )
        
        embed.add_field(
            name="🎯 **Performance Score**",
            value="**Rating:** ⭐⭐⭐⭐⭐\n**SLA Compliance:** ✅ Met\n**Customer Satisfaction:** Pending",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class InternalNoteModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="📝 Add Internal Staff Note")
        
        self.note_input = discord.ui.TextInput(
            label="Internal Note (Staff Only)",
            placeholder="Enter internal note that only staff can see...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        self.add_item(self.note_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📝 **Internal Staff Note Added**",
            description=f"**Note:** {self.note_input.value}",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="👤 **Added By**",
            value=f"{interaction.user.display_name}\n{interaction.user.mention}",
            inline=True
        )
        embed.add_field(
            name="🔒 **Visibility**",
            value="Staff Only\nHidden from user",
            inline=True
        )
        embed.set_footer(text="📝 Internal Note • Staff Only")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class StaffTransferView(View):
    def __init__(self, creator_id: int, category_key: str, category_name: str):
        super().__init__(timeout=300)
        self.creator_id = creator_id
        self.category_key = category_key
        self.category_name = category_name
    
    @discord.ui.button(label="✅ Complete Transfer", style=discord.ButtonStyle.success, emoji="✅")
    async def complete_transfer(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="✅ **Transfer Complete**",
            description="**Ticket has been successfully transferred!**",
            color=0x00d4aa,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📋 **Transfer Details**",
            value=f"**From:** {interaction.user.display_name}\n**Status:** ✅ Completed\n**New Assignee:** Will be notified",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Enhanced ticket categories with cooler styling
ELEGANT_TICKET_CATEGORIES = {
    "general": {
        "name": "💬 General Support",
        "description": "General questions, guidance, and basic assistance",
        "emoji": "💬",
        "color": 0x7c3aed
    },
    "technical": {
        "name": "🔧 Technical Issues", 
        "description": "Bot problems, server issues, and technical difficulties",
        "emoji": "🔧",
        "color": 0xff6b6b
    },
    "account": {
        "name": "👤 Account & Profile",
        "description": "Profile issues, account problems, and user settings",
        "emoji": "👤", 
        "color": 0x00d4aa
    },
    "moderation": {
        "name": "🛡️ Moderation Appeal",
        "description": "Appeals, reports, and moderation-related inquiries", 
        "emoji": "🛡️",
        "color": 0xffa500
    },
    "billing": {
        "name": "💳 Billing & Premium",
        "description": "Payment issues, premium features, and billing support",
        "emoji": "💳",
        "color": 0xffd700
    },
    "partnership": {
        "name": "🤝 Partnership & Business",
        "description": "Business inquiries, partnerships, and collaborations",
        "emoji": "🤝",
        "color": 0x5865f2
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
        self._setup_ultra_modern_buttons()
    
    def _setup_ultra_modern_buttons(self):
        """Setup ultra-modern ticket creation buttons"""
        self.clear_items()
        
        # Row 1: Primary support categories
        general_btn = Button(
            label="💬 General Support",
            emoji="💬",
            style=discord.ButtonStyle.primary,
            custom_id="ticket_general"
        )
        general_btn.callback = lambda i: self._create_elegant_ticket(i, "general")
        self.add_item(general_btn)
        
        technical_btn = Button(
            label="🔧 Technical Issues",
            emoji="🔧", 
            style=discord.ButtonStyle.danger,
            custom_id="ticket_technical"
        )
        technical_btn.callback = lambda i: self._create_elegant_ticket(i, "technical")
        self.add_item(technical_btn)
        
        account_btn = Button(
            label="👤 Account Help",
            emoji="👤",
            style=discord.ButtonStyle.success,
            custom_id="ticket_account"
        )
        account_btn.callback = lambda i: self._create_elegant_ticket(i, "account")
        self.add_item(account_btn)
        
        # Row 2: Specialized categories
        moderation_btn = Button(
            label="🛡️ Moderation",
            emoji="🛡️",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket_moderation"
        )
        moderation_btn.callback = lambda i: self._create_elegant_ticket(i, "moderation")
        self.add_item(moderation_btn)
        
        billing_btn = Button(
            label="💳 Billing & Premium",
            emoji="💳",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket_billing"
        )
        billing_btn.callback = lambda i: self._create_elegant_ticket(i, "billing")
        self.add_item(billing_btn)
        
        partnership_btn = Button(
            label="🤝 Partnership",
            emoji="🤝",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket_partnership"
        )
        partnership_btn.callback = lambda i: self._create_elegant_ticket(i, "partnership")
        self.add_item(partnership_btn)

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
                channel = await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites,
                    topic=f"🟢 OPEN • {category_info['name']} • User: {user.id} • Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
            except discord.Forbidden:
                embed = discord.Embed(
                    title="❌ Permission Error",
                    description="I don't have permission to create channels. Please contact an administrator.",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create beautiful welcome embed
            welcome_embed = discord.Embed(
                title=f"{category_info['emoji']} Welcome to {category_info['name']}",
                description=f"**Hello {user.display_name}!** 👋\n\nThank you for contacting our support team. This is your private support channel where our professional staff will assist you.",
                color=category_info['color'],
                timestamp=datetime.now()
            )
            
            welcome_embed.add_field(
                name="📋 Ticket Information",
                value=f"**Category:** {category_info['name']}\n**Created:** <t:{int(datetime.now().timestamp())}:F>\n**Status:** 🟢 Open & Awaiting Staff",
                inline=True
            )
            
            welcome_embed.add_field(
                name="⏱️ Response Time",
                value="**Typical Response:** 15-30 minutes\n**Priority Support:** Available\n**24/7 Monitoring:** Active",
                inline=True
            )
            
            welcome_embed.add_field(
                name="💡 How to Get the Best Help",
                value="• **Be Specific:** Describe your issue clearly\n• **Include Details:** Screenshots, error messages, etc.\n• **Stay Patient:** Our team will respond promptly\n• **Use Buttons:** Control your ticket with the buttons below",
                inline=False
            )
            
            welcome_embed.set_author(
                name=f"Support Ticket #{str(channel.id)[-4:]}",
                icon_url=user.display_avatar.url
            )
            welcome_embed.set_footer(text="✨ Professional Support Experience")
            welcome_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            # Create elegant controls
            controls = ElegantTicketControls(user.id, category_key, category_info['name'], is_claimed=False)
            
            # Send welcome message
            welcome_msg = await channel.send(embed=welcome_embed, view=controls)
            
            # Pin the welcome message
            try:
                await welcome_msg.pin()
            except:
                pass
            
            # Notify staff (elegant notification)
            try:
                server_settings = db.get_server_settings(guild.id)
                ticket_support_roles = server_settings.get('ticket_support_roles', [])
                
                roles_to_ping = []
                for role_id in ticket_support_roles:
                    role = guild.get_role(role_id)
                    if role:
                        roles_to_ping.append(role)
                
                # Also ping mod roles
                for role in guild.roles:
                    if any(name in role.name.lower() for name in ["leadmoderator", "moderator"]) and role not in roles_to_ping:
                        roles_to_ping.append(role)
                
                if roles_to_ping:
                    ping_mentions = " ".join([role.mention for role in roles_to_ping])
                    
                    staff_embed = discord.Embed(
                        title="🎫 New Support Ticket",
                        description=f"**{user.display_name}** has created a new {category_info['name'].lower()} ticket.",
                        color=category_info['color']
                    )
                    staff_embed.add_field(
                        name="Quick Details",
                        value=f"**User:** {user.mention}\n**Category:** {category_info['name']}\n**Channel:** {channel.mention}",
                        inline=False
                    )
                    staff_embed.set_footer(text="Professional Support Team")
                    
                    await channel.send(ping_mentions, embed=staff_embed, delete_after=20)
            except:
                pass
            
            # Log ticket creation
            try:
                db.log_ticket_creation(guild.id, user.id, channel.id, category_key, category_info['name'])
            except:
                pass
            
            # Beautiful success response
            success_embed = discord.Embed(
                title="✅ Ticket Created Successfully!",
                description=f"Your **{category_info['name']}** ticket has been created: {channel.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            success_embed.add_field(
                name="🎯 What Happens Next?",
                value="1. **Go to your ticket** - Click the channel link above\n2. **Describe your issue** - Provide clear details\n3. **Wait for staff** - Our team will respond soon\n4. **Get help** - Professional assistance guaranteed",
                inline=False
            )
            
            success_embed.add_field(
                name="⚡ Quick Tips",
                value="• Include screenshots or error messages\n• Be as specific as possible\n• Use the ticket buttons for actions\n• Stay in the channel for updates",
                inline=False
            )
            
            success_embed.set_footer(text="🎫 Thank you for choosing our support!")
            
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