import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select, Modal, TextInput
from datetime import datetime
import os, sys
import asyncio
import time
import json

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# Define the 4 staff roles that can manage tickets
STAFF_ROLES = ["forgotten one", "overseer", "lead moderator", "moderator"]

# Global dictionary to track active tickets per user
active_tickets = {}

# Ticket categories for better organization
TICKET_CATEGORIES = {
    "general": {"emoji": "❓", "name": "General Support", "color": 0x7289da},
    "bug": {"emoji": "🐛", "name": "Bug Report", "color": 0xff4444},
    "appeal": {"emoji": "⚖️", "name": "Ban/Mute Appeal", "color": 0xffa500},
    "report": {"emoji": "🚨", "name": "Player Report", "color": 0xff0000},
    "suggestion": {"emoji": "💡", "name": "Suggestion", "color": 0x00ff88}
}

class TicketCategorySelect(Select):
    """Dropdown for selecting ticket category"""
    def __init__(self):
        options = []
        for key, category in TICKET_CATEGORIES.items():
            options.append(discord.SelectOption(
                label=category["name"],
                value=key,
                emoji=category["emoji"],
                description=f"Create a {category['name'].lower()} ticket"
            ))
        
        super().__init__(placeholder="🎫 Select ticket category...", options=options)
    
    async def callback(self, interaction: discord.Interaction):
        category_key = self.values[0]
        category = TICKET_CATEGORIES[category_key]
        
        # Show priority selection modal
        priority_modal = TicketPriorityModal(category_key, category)
        await interaction.response.send_modal(priority_modal)

class TicketPriorityModal(Modal):
    """Modal for selecting ticket priority and providing details"""
    def __init__(self, category_key: str, category: dict):
        super().__init__(title=f"Create {category['name']} Ticket")
        self.category_key = category_key
        self.category = category
        
        # Priority selection (High, Medium, Low)
        self.priority = TextInput(
            label="Priority Level (High/Medium/Low)",
            placeholder="Enter: High, Medium, or Low",
            default="Medium",
            max_length=10,
            required=True
        )
        
        # Issue description
        self.description = TextInput(
            label="Describe your issue in detail",
            placeholder="Please provide as much detail as possible...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        
        # Additional info
        self.additional_info = TextInput(
            label="Additional Information (Optional)",
            placeholder="Screenshots, error messages, steps to reproduce, etc.",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=False
        )
        
        self.add_item(self.priority)
        self.add_item(self.description)
        self.add_item(self.additional_info)
    
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        
        # Validate priority
        priority = self.priority.value.lower().capitalize()
        if priority not in ["High", "Medium", "Low"]:
            priority = "Medium"
        
        # Check if user already has an active ticket
        if user.id in active_tickets:
            existing_channel = active_tickets[user.id]
            try:
                existing_channel_obj = guild.get_channel(existing_channel)
                if existing_channel_obj:
                    await interaction.response.send_message(
                        f"❌ **You already have an active ticket!** {existing_channel_obj.mention}\n"
                        f"Please use your existing ticket or ask staff to close it first.",
                        ephemeral=True
                    )
                    return
                else:
                    del active_tickets[user.id]
            except:
                del active_tickets[user.id]
        
        # Find or create ticket category
        category = None
        for cat in guild.categories:
            if "ticket" in cat.name.lower():
                category = cat
                break
        
        if not category:
            try:
                category = await guild.create_category("🎫 Support Tickets")
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ **Error creating ticket category:** {str(e)}", 
                    ephemeral=True
                )
                return
        
        # Create channel name with category and priority
        priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[priority]
        channel_name = f"{priority_emoji}{self.category['emoji']}{user.display_name.lower()}-ticket"
        
        try:
            # Create the ticket channel with enhanced permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(
                    view_channel=True, 
                    send_messages=True, 
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                ),
                guild.me: discord.PermissionOverwrite(
                    view_channel=True, 
                    send_messages=True, 
                    manage_messages=True,
                    manage_channels=True
                )
            }
            
            # Add staff role permissions
            staff_roles_found = []
            for role in guild.roles:
                if any(staff_name in role.name.lower() for staff_name in STAFF_ROLES):
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        manage_messages=True,
                        manage_channels=True
                    )
                    staff_roles_found.append(role)
            
            channel = await guild.create_text_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"{self.category['name']} | Creator: {user} | Priority: {priority}"
            )
            
            # Track this ticket as active for the user
            active_tickets[user.id] = channel.id
            
            # Save ticket to database
            await self.save_ticket_to_database(user.id, channel.id, self.category_key, priority, self.description.value)
            
            # Create enhanced ticket embed
            ticket_embed = discord.Embed(
                title=f"{self.category['emoji']} {self.category['name']} Ticket",
                description=f"**Welcome {user.mention}!**\n\n"
                           f"📋 **Issue Description:**\n{self.description.value}\n\n"
                           f"{'📎 **Additional Info:**\n' + self.additional_info.value + '\n\n' if self.additional_info.value else ''}"
                           f"⏰ **Staff will assist you shortly**",
                color=self.category['color']
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
                name=f"{priority_emoji} Priority",
                value=priority,
                inline=True
            )
            ticket_embed.add_field(
                name="🏷️ Category",
                value=f"{self.category['emoji']} {self.category['name']}",
                inline=True
            )
            ticket_embed.add_field(
                name="🆔 Ticket ID",
                value=f"#{channel.id % 10000:04d}",
                inline=True
            )
            ticket_embed.add_field(
                name="🔄 Status",
                value="🟡 Waiting for staff",
                inline=True
            )
            ticket_embed.set_footer(text="🎫 Enhanced Ticket System | Use buttons below to manage this ticket")
            
            # Create enhanced control panel
            control_panel = EnhancedTicketControls(
                creator_id=user.id,
                original_name=channel_name,
                category_key=self.category_key,
                priority=priority
            )
            
            # Send welcome message to ticket channel
            welcome_msg = await channel.send(
                f"👋 **Welcome to your {self.category['name'].lower()} ticket!**\n"
                f"🎯 **Priority Level:** {priority_emoji} {priority}\n"
                f"📝 Staff have been notified and will assist you soon.",
                embed=ticket_embed,
                view=control_panel
            )
            
            # Pin the welcome message
            try:
                await welcome_msg.pin()
            except:
                pass
            
            # Send priority-based staff notification
            if staff_roles_found:
                staff_pings = [role.mention for role in staff_roles_found]
                priority_ping = "🔴 @everyone" if priority == "High" else ""
                
                await channel.send(
                    f"🔔 **New {priority} Priority Ticket Alert** {priority_ping}\n"
                    f"{' '.join(staff_pings)}\n"
                    f"**{self.category['emoji']} {self.category['name']} ticket requires assistance!**\n"
                    f"👤 **User:** {user.mention}\n"
                    f"🎯 **Priority:** {priority_emoji} {priority}\n"
                    f"📅 **Created:** <t:{int(time.time())}:R>\n"
                    f"📋 **Issue:** {self.description.value[:100]}{'...' if len(self.description.value) > 100 else ''}"
                )
            
            # Respond to user with success message
            success_embed = discord.Embed(
                title="✅ Ticket Created Successfully!",
                description=f"Your {self.category['name'].lower()} ticket has been created: {channel.mention}\n\n"
                           f"🎯 **Priority:** {priority_emoji} {priority}\n"
                           f"📋 **Category:** {self.category['emoji']} {self.category['name']}\n\n"
                           f"**Next Steps:**\n"
                           f"• Go to your ticket channel\n"
                           f"• Provide any additional information if needed\n"
                           f"• Wait for staff assistance\n\n"
                           f"⚠️ **Note:** You can only have one active ticket at a time.",
                color=self.category['color']
            )
            success_embed.set_footer(text="🎫 Enhanced Ticket System")
            
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
    
    async def save_ticket_to_database(self, user_id: int, channel_id: int, category: str, priority: str, description: str):
        """Save ticket information to database"""
        try:
            ticket_data = {
                "user_id": user_id,
                "channel_id": channel_id,
                "category": category,
                "priority": priority,
                "description": description,
                "created_at": datetime.now(),
                "status": "open",
                "claimed_by": None,
                "messages": []
            }
            await db.set_ticket_data(user_id, ticket_data)
        except Exception as e:
            print(f"Error saving ticket to database: {e}")

class EnhancedTicketControls(View):
    """Enhanced Ticket Control Panel with more features"""
    def __init__(self, creator_id: int, original_name: str, category_key: str, priority: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.claimed_by = None
        self.original_name = original_name
        self.category_key = category_key
        self.priority = priority
        self.last_claim_time = {}
        self.claim_cooldown = 2
        
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
        """Claim ticket for staff member"""
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can claim tickets!", 
                ephemeral=True
            )
            return
        
        # Check cooldown
        current_time = time.time()
        user_id = interaction.user.id
        if user_id in self.last_claim_time:
            time_diff = current_time - self.last_claim_time[user_id]
            if time_diff < self.claim_cooldown:
                remaining = self.claim_cooldown - time_diff
                await interaction.response.send_message(
                    f"⏰ Please wait {remaining:.1f} seconds before claiming again.", 
                    ephemeral=True
                )
                return
        
        self.last_claim_time[user_id] = current_time
        
        if self.claimed_by:
            await interaction.response.send_message(
                f"❌ This ticket is already claimed by {self.claimed_by.mention}!", 
                ephemeral=True
            )
            return
        
        self.claimed_by = interaction.user
        
        # Update button
        button.label = f"✅ Claimed by {interaction.user.display_name}"
        button.style = discord.ButtonStyle.success
        button.disabled = True
        
        # Update channel topic
        try:
            category = TICKET_CATEGORIES[self.category_key]
            await interaction.channel.edit(
                topic=f"{category['name']} | Creator: <@{self.creator_id}> | Priority: {self.priority} | Claimed by: {interaction.user.display_name}"
            )
        except:
            pass
        
        # Send claim message
        embed = discord.Embed(
            title="✅ Ticket Claimed",
            description=f"**{interaction.user.mention} has claimed this ticket!**\n"
                       f"They will assist you with your {TICKET_CATEGORIES[self.category_key]['name'].lower()}.",
            color=0x00ff00
        )
        embed.add_field(
            name="📅 Claimed At",
            value=f"<t:{int(time.time())}:F>",
            inline=True
        )
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=embed)
        
        # Update database
        try:
            ticket_data = await db.get_ticket_data(self.creator_id)
            if ticket_data:
                ticket_data["claimed_by"] = interaction.user.id
                ticket_data["status"] = "claimed"
                await db.set_ticket_data(self.creator_id, ticket_data)
        except:
            pass

    @discord.ui.button(label="📝 Add Note", style=discord.ButtonStyle.secondary, emoji="📝")
    async def add_note(self, interaction: discord.Interaction, button: Button):
        """Add a staff note to the ticket"""
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can add notes!", 
                ephemeral=True
            )
            return
        
        note_modal = StaffNoteModal()
        await interaction.response.send_modal(note_modal)

    @discord.ui.button(label="📊 Change Priority", style=discord.ButtonStyle.secondary, emoji="📊")
    async def change_priority(self, interaction: discord.Interaction, button: Button):
        """Change ticket priority"""
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can change priority!", 
                ephemeral=True
            )
            return
        
        priority_modal = ChangePriorityModal(self)
        await interaction.response.send_modal(priority_modal)

    @discord.ui.button(label="💾 Save Transcript", style=discord.ButtonStyle.secondary, emoji="💾")
    async def save_transcript(self, interaction: discord.Interaction, button: Button):
        """Save ticket transcript"""
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can save transcripts!", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get channel messages
            messages = []
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                messages.append({
                    "author": str(message.author),
                    "content": message.content,
                    "timestamp": message.created_at.isoformat(),
                    "attachments": [att.url for att in message.attachments]
                })
            
            # Create transcript
            transcript = {
                "ticket_id": interaction.channel.id,
                "creator_id": self.creator_id,
                "category": self.category_key,
                "priority": self.priority,
                "claimed_by": self.claimed_by.id if self.claimed_by else None,
                "created_at": datetime.now().isoformat(),
                "messages": messages
            }
            
            # Save to database
            await db.save_ticket_transcript(interaction.channel.id, transcript)
            
            await interaction.followup.send(
                f"💾 **Transcript saved successfully!**\n"
                f"📄 **Ticket ID:** #{interaction.channel.id % 10000:04d}\n"
                f"📝 **Messages:** {len(messages)}\n"
                f"💽 **Saved by:** {interaction.user.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"❌ **Error saving transcript:** {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(label="🔐 Close Ticket", style=discord.ButtonStyle.danger, emoji="🔐")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        """Close the ticket"""
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can close tickets!", 
                ephemeral=True
            )
            return
            
        # Auto-save transcript before closing
        try:
            messages = []
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                messages.append({
                    "author": str(message.author),
                    "content": message.content,
                    "timestamp": message.created_at.isoformat(),
                    "attachments": [att.url for att in message.attachments]
                })
            
            transcript = {
                "ticket_id": interaction.channel.id,
                "creator_id": self.creator_id,
                "category": self.category_key,
                "priority": self.priority,
                "claimed_by": self.claimed_by.id if self.claimed_by else None,
                "closed_by": interaction.user.id,
                "created_at": datetime.now().isoformat(),
                "messages": messages
            }
            
            await db.save_ticket_transcript(interaction.channel.id, transcript)
        except:
            pass
        
        # Remove from active tickets tracking
        creator_id = self.creator_id
        if creator_id in active_tickets:
            del active_tickets[creator_id]
            
        # Send closing message
        embed = discord.Embed(
            title="🔐 Ticket Closed",
            description=f"**Closed by:** {interaction.user.mention}\n"
                       f"**Category:** {TICKET_CATEGORIES[self.category_key]['emoji']} {TICKET_CATEGORIES[self.category_key]['name']}\n"
                       f"**Priority:** {self.priority}\n"
                       f"**Transcript:** Automatically saved\n\n"
                       f"**Channel will be deleted in 10 seconds...**",
            color=0xff4444
        )
        embed.add_field(
            name="📅 Closed At",
            value=f"<t:{int(time.time())}:F>",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
        
        await asyncio.sleep(10)
        
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as e:
            print(f"Error deleting ticket channel: {e}")

class StaffNoteModal(Modal):
    """Modal for adding staff notes"""
    def __init__(self):
        super().__init__(title="Add Staff Note")
        
        self.note = TextInput(
            label="Staff Note",
            placeholder="Add internal staff note about this ticket...",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True
        )
        self.add_item(self.note)
    
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📝 Staff Note Added",
            description=self.note.value,
            color=0x00ff88
        )
        embed.set_author(
            name=f"Note by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        embed.add_field(
            name="📅 Added At",
            value=f"<t:{int(time.time())}:F>",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

class ChangePriorityModal(Modal):
    """Modal for changing ticket priority"""
    def __init__(self, ticket_controls):
        super().__init__(title="Change Ticket Priority")
        self.ticket_controls = ticket_controls
        
        self.new_priority = TextInput(
            label="New Priority (High/Medium/Low)",
            placeholder="Enter: High, Medium, or Low",
            default=ticket_controls.priority,
            max_length=10,
            required=True
        )
        self.reason = TextInput(
            label="Reason for change (optional)",
            placeholder="Why is the priority being changed?",
            style=discord.TextStyle.paragraph,
            max_length=200,
            required=False
        )
        
        self.add_item(self.new_priority)
        self.add_item(self.reason)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Validate priority
        new_priority = self.new_priority.value.lower().capitalize()
        if new_priority not in ["High", "Medium", "Low"]:
            await interaction.response.send_message(
                "❌ Invalid priority! Please use: High, Medium, or Low",
                ephemeral=True
            )
            return
        
        old_priority = self.ticket_controls.priority
        self.ticket_controls.priority = new_priority
        
        # Update channel name and topic
        priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
        old_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[old_priority]
        new_emoji = priority_emoji[new_priority]
        
        try:
            # Update channel name
            old_name = interaction.channel.name
            new_name = old_name.replace(old_emoji, new_emoji)
            await interaction.channel.edit(name=new_name)
            
            # Update topic
            category = TICKET_CATEGORIES[self.ticket_controls.category_key]
            claimed_text = f" | Claimed by: {self.ticket_controls.claimed_by.display_name}" if self.ticket_controls.claimed_by else ""
            await interaction.channel.edit(
                topic=f"{category['name']} | Creator: <@{self.ticket_controls.creator_id}> | Priority: {new_priority}{claimed_text}"
            )
        except:
            pass
        
        embed = discord.Embed(
            title="📊 Priority Changed",
            description=f"**Priority updated:** {old_emoji} {old_priority} → {new_emoji} {new_priority}\n"
                       f"**Changed by:** {interaction.user.mention}\n"
                       f"{'**Reason:** ' + self.reason.value if self.reason.value else ''}",
            color=0x00ff88
        )
        embed.add_field(
            name="📅 Changed At",
            value=f"<t:{int(time.time())}:F>",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)

class EnhancedTicketButton(View):
    """Enhanced Ticket Creation Button with category selection"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🎫 Create Support Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        # Create category selection view
        view = View()
        select = TicketCategorySelect()
        view.add_item(select)
        
        embed = discord.Embed(
            title="🎫 Create Support Ticket",
            description="**Please select the category that best describes your issue:**\n\n"
                       "🔴 **High Priority:** Urgent issues requiring immediate attention\n"
                       "🟡 **Medium Priority:** Standard support requests\n"
                       "🟢 **Low Priority:** General questions or minor issues\n\n"
                       "⚠️ **Note:** You can only have one active ticket at a time.",
            color=0x7289da
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class SimpleTickets(commands.Cog):
    """Enhanced Simple Ticket System"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="ticket-panel", description="🎫 Create enhanced ticket panel")
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Enhanced Support System",
            description="**Need help?** Click the button below to create a support ticket.\n\n"
                       "**✨ New Features:**\n"
                       "• 📂 **Categories:** Bug reports, appeals, suggestions, and more\n"
                       "• 🎯 **Priority Levels:** High, medium, and low priority support\n"
                       "• 👥 **Staff Management:** Claim tickets and add notes\n"
                       "• 💾 **Transcripts:** Automatic conversation saving\n"
                       "• 📊 **Analytics:** Track response times and resolution\n\n"
                       "**How it works:**\n"
                       "• Select your issue category\n"
                       "• Set priority level and describe the problem\n"
                       "• Staff will be notified based on priority\n"
                       "• Get help in your private ticket channel",
            color=0x7289da
        )
        embed.add_field(
            name="📋 Ticket Categories",
            value="❓ **General Support** - Questions and general help\n"
                  "🐛 **Bug Report** - Report technical issues\n"
                  "⚖️ **Ban/Mute Appeal** - Appeal punishments\n"
                  "🚨 **Player Report** - Report rule violations\n"
                  "💡 **Suggestion** - Suggest improvements",
            inline=False
        )
        embed.add_field(
            name="🎯 Priority Levels",
            value="🔴 **High** - Urgent issues (staff pinged immediately)\n"
                  "🟡 **Medium** - Standard support requests\n"
                  "🟢 **Low** - General questions and minor issues",
            inline=False
        )
        embed.add_field(
            name="⏰ Response Times",
            value="• **High Priority:** Within 30 minutes\n"
                  "• **Medium Priority:** Within 2 hours\n"
                  "• **Low Priority:** Within 24 hours\n"
                  "• *Response times may vary during busy periods*",
            inline=False
        )
        embed.set_footer(text="🎫 Enhanced Ticket System | Professional Support Experience")
        
        view = EnhancedTicketButton()
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
        
        # Auto-save transcript
        try:
            messages = []
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                messages.append({
                    "author": str(message.author),
                    "content": message.content,
                    "timestamp": message.created_at.isoformat(),
                    "attachments": [att.url for att in message.attachments]
                })
            
            transcript = {
                "ticket_id": interaction.channel.id,
                "creator_id": creator_id,
                "closed_by": interaction.user.id,
                "created_at": datetime.now().isoformat(),
                "messages": messages
            }
            
            await db.save_ticket_transcript(interaction.channel.id, transcript)
        except:
            pass
        
        if creator_id:
            del active_tickets[creator_id]
        
        embed = discord.Embed(
            title="🔐 Ticket Closed",
            description=f"**Closed by:** {interaction.user.mention}\n"
                       f"**Transcript:** Automatically saved\n\n"
                       f"**Channel will be deleted in 10 seconds...**",
            color=0xff4444
        )
        
        await interaction.response.send_message(embed=embed)
        
        await asyncio.sleep(10)
        
        try:
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error deleting channel: {str(e)}")
    
    @app_commands.command(name="ticket-stats", description="📊 View ticket statistics (Staff only)")
    async def ticket_stats(self, interaction: discord.Interaction):
        """View ticket statistics"""
        if not self._is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Only staff can view ticket statistics!", 
                ephemeral=True
            )
            return
        
        try:
            # Get ticket stats from database
            stats = await db.get_ticket_statistics()
            
            embed = discord.Embed(
                title="📊 Ticket Statistics",
                description="**Current ticket system performance and metrics**",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🎫 Active Tickets",
                value=f"{len(active_tickets)} tickets currently open",
                inline=True
            )
            embed.add_field(
                name="📈 Total Tickets",
                value=f"{stats.get('total_tickets', 0)} tickets created",
                inline=True
            )
            embed.add_field(
                name="✅ Resolved Tickets",
                value=f"{stats.get('resolved_tickets', 0)} tickets closed",
                inline=True
            )
            embed.add_field(
                name="⏰ Avg Response Time",
                value=f"{stats.get('avg_response_time', 'N/A')} minutes",
                inline=True
            )
            embed.add_field(
                name="🎯 Priority Breakdown",
                value=f"🔴 High: {stats.get('high_priority', 0)}\n"
                      f"🟡 Medium: {stats.get('medium_priority', 0)}\n"
                      f"🟢 Low: {stats.get('low_priority', 0)}",
                inline=True
            )
            embed.add_field(
                name="📂 Category Breakdown",
                value=f"❓ General: {stats.get('general', 0)}\n"
                      f"🐛 Bug Reports: {stats.get('bug', 0)}\n"
                      f"⚖️ Appeals: {stats.get('appeal', 0)}\n"
                      f"🚨 Reports: {stats.get('report', 0)}\n"
                      f"💡 Suggestions: {stats.get('suggestion', 0)}",
                inline=True
            )
            
            embed.set_footer(text=f"📊 Statistics generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ **Error retrieving statistics:** {str(e)}",
                ephemeral=True
            )
    
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