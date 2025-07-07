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
    def __init__(self, creator_id: int, category_key: str, subcategory: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.category_key = category_key
        self.subcategory = subcategory
    
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
    
    async def update_channel_name(self, channel, status_emoji, claimed_by=None):
        """Update channel name with status emoji and claimed info"""
        try:
            # Get clean username for channel name
            creator = channel.guild.get_member(self.creator_id)
            if not creator:
                return
            
            clean_username = creator.display_name.lower().replace(' ', '').replace('-', '')[:10]
            
            # Build new channel name with status and claimer
            base_name = f"ticket-{clean_username}-{self.creator_id}"
            
            if claimed_by:
                claimer_name = claimed_by.display_name.lower().replace(' ', '')[:8]
                new_name = f"{status_emoji}-{base_name}-{claimer_name}"
            else:
                new_name = f"{status_emoji}-{base_name}"
            
            # Ensure name length is within Discord limits
            if len(new_name) > 100:
                new_name = new_name[:100]
            
            await channel.edit(name=new_name)
        except Exception as e:
            print(f"Error updating channel name: {e}")

    @discord.ui.button(label="👤 Claim Ticket", style=discord.ButtonStyle.success, emoji="👤")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to claim tickets!", ephemeral=True)
            return
        
        # Check if already claimed
        channel = interaction.channel
        if "claimed" in channel.topic.lower() if channel.topic else False:
            await interaction.response.send_message("⚠️ This ticket is already claimed!", ephemeral=True)
            return
        
        try:
            # Update channel topic to show claimed status
            current_topic = channel.topic or ""
            new_topic = f"🟡 CLAIMED by {interaction.user.display_name} • {current_topic}"
            await channel.edit(topic=new_topic)
            
            # Update channel name with yellow emoji and claimer
            await self.update_channel_name(channel, "🟡", interaction.user)
            
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
            
            # Update button to show unclaim option
            self.clear_items()
            self.add_item(Button(label="👤 Unclaim Ticket", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="unclaim_btn"))
            self.add_item(Button(label="🔧 Priority", style=discord.ButtonStyle.secondary, emoji="🔧", custom_id="priority_btn"))
            self.add_item(Button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_btn"))
            
            await interaction.response.edit_message(embed=claim_embed, view=self)
            
            # Send notification to ticket creator
            creator = interaction.guild.get_member(self.creator_id)
            if creator:
                await channel.send(f"👋 {creator.mention}, your ticket has been claimed by {interaction.user.mention} and they will assist you shortly!")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error claiming ticket: {str(e)}", ephemeral=True)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Handle button clicks based on custom_id
        if hasattr(interaction.data, 'custom_id'):
            custom_id = interaction.data.get('custom_id')
            
            if custom_id == "unclaim_btn":
                return await self.unclaim_ticket(interaction)
            elif custom_id == "priority_btn":
                return await self.update_priority(interaction)
            elif custom_id == "close_btn":
                return await self.close_ticket(interaction)
            elif custom_id == "reopen_btn":
                return await self.reopen_ticket(interaction)
        
        return True
    
    async def unclaim_ticket(self, interaction: discord.Interaction):
        """Handle unclaiming a ticket"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to unclaim tickets!", ephemeral=True)
            return False
        
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
            
            # Reset buttons to original state
            self.clear_items()
            self.add_item(Button(label="👤 Claim Ticket", style=discord.ButtonStyle.success, emoji="👤", custom_id="claim_btn"))
            self.add_item(Button(label="🔧 Priority", style=discord.ButtonStyle.secondary, emoji="🔧", custom_id="priority_btn"))
            self.add_item(Button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_btn"))
            
            await interaction.response.edit_message(embed=unclaim_embed, view=self)
            
            # Notify that ticket is available again
            await channel.send("📢 **Ticket Available** - This ticket is now available for any staff member to claim!")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unclaiming ticket: {str(e)}", ephemeral=True)
        
        return False
    
    async def update_priority(self, interaction: discord.Interaction):
        """Handle priority updates"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to update priority!", ephemeral=True)
            return False
        
        # Create priority selection view
        priority_view = View(timeout=60)
        
        priorities = [
            ("🟢 Low", discord.ButtonStyle.success, 0x28a745),
            ("🟡 Medium", discord.ButtonStyle.secondary, 0xffc107),
            ("🟠 High", discord.ButtonStyle.secondary, 0xff6b6b),
            ("🔴 Urgent", discord.ButtonStyle.danger, 0xe74c3c)
        ]
        
        for label, style, color in priorities:
            button = Button(label=label, style=style)
            
            async def priority_callback(btn_interaction, priority_color=color, priority_name=label):
                try:
                    channel = btn_interaction.channel
                    
                    # Update channel topic with priority
                    current_topic = channel.topic or ""
                    # Remove old priority if exists
                    topic_parts = current_topic.split(" • ")
                    clean_parts = [part for part in topic_parts if not any(p in part for p in ["🟢", "🟡", "🟠", "🔴"])]
                    new_topic = f"{priority_name} • " + " • ".join(clean_parts)
                    
                    await channel.edit(topic=new_topic)
                    
                    # Update channel name with priority emoji
                    priority_emoji = priority_name.split()[0]
                    await self.update_channel_name(channel, priority_emoji)
                    
                    # Send confirmation
                    priority_embed = discord.Embed(
                        title=f"{priority_emoji} **Priority Updated**",
                        description=f"Ticket priority has been set to **{priority_name}**",
                        color=priority_color,
                        timestamp=datetime.now()
                    )
                    priority_embed.set_footer(text="✨ Priority system helps staff prioritize urgent tickets")
                    
                    await btn_interaction.response.edit_message(embed=priority_embed, view=None)
                    
                except Exception as e:
                    await btn_interaction.response.send_message(f"❌ Error updating priority: {str(e)}", ephemeral=True)
            
            button.callback = priority_callback
            priority_view.add_item(button)
        
        priority_embed = discord.Embed(
            title="🔧 **Update Ticket Priority**",
            description="Select the priority level for this ticket:",
            color=0x7c3aed
        )
        priority_embed.add_field(
            name="Priority Levels",
            value="🟢 **Low** - General questions, non-urgent\n🟡 **Medium** - Standard support needs\n🟠 **High** - Important issues requiring attention\n🔴 **Urgent** - Critical issues requiring immediate help",
            inline=False
        )
        
        await interaction.response.send_message(embed=priority_embed, view=priority_view, ephemeral=True)
        return False
    
    async def close_ticket(self, interaction: discord.Interaction):
        """Handle ticket closing with reopen option"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to close tickets!", ephemeral=True)
            return False
        
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
            
            # Create reopen button
            self.clear_items()
            self.add_item(Button(label="♻️ Reopen Ticket", style=discord.ButtonStyle.primary, emoji="♻️", custom_id="reopen_btn"))
            self.add_item(Button(label="🗑️ Delete Channel", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="delete_btn"))
            
            await interaction.response.edit_message(embed=close_embed, view=self)
            
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
        
        return False
    
    async def reopen_ticket(self, interaction: discord.Interaction):
        """Handle ticket reopening"""
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ You don't have permission to reopen tickets!", ephemeral=True)
            return False
        
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
            
            # Reset buttons to original state
            self.clear_items()
            self.add_item(Button(label="👤 Claim Ticket", style=discord.ButtonStyle.success, emoji="👤", custom_id="claim_btn"))
            self.add_item(Button(label="🔧 Priority", style=discord.ButtonStyle.secondary, emoji="🔧", custom_id="priority_btn"))
            self.add_item(Button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_btn"))
            
            await interaction.response.edit_message(embed=reopen_embed, view=self)
            
            # Notify parties
            if creator:
                await channel.send(f"🎉 {creator.mention}, your ticket has been reopened! Please continue the conversation here.")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error reopening ticket: {str(e)}", ephemeral=True)
        
        return False

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
                if channel.name.startswith(f"ticket-") and f"-{user.id}" in channel.name:
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
            channel_name = f"🟢-ticket-{clean_username}-{user.id}"
            
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
                    manage_channels=True,
                    use_external_emojis=True
                )
            }
            
            # Add support roles
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
                        use_external_emojis=True,
                        mention_everyone=True
                    )
            
            # Create channel
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"🟢 Open • {category_info['name']} • {user.display_name} • Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Create enhanced welcome embed
            welcome_embed = discord.Embed(
                title=f"{category_info['emoji']} **{category_info['name']} Ticket**",
                description=f"**Welcome {user.display_name}!** Your ticket has been created successfully.",
                color=category_info['color'],
                timestamp=datetime.now()
            )
            
            # Ticket info
            welcome_embed.add_field(
                name="📋 **Ticket Information**",
                value=f"**Category:** {category_info['name']}\n**Created:** <t:{int(datetime.now().timestamp())}:R>\n**Status:** 🟢 Open",
                inline=True
            )
            
            # User info
            welcome_embed.add_field(
                name="👤 **User Information**", 
                value=f"**User:** {user.mention}\n**Display Name:** {user.display_name}\n**ID:** {user.id}",
                inline=True
            )
            
            # Status
            welcome_embed.add_field(
                name="📊 **Current Status**",
                value="🟢 **Open** - Waiting for staff\n👤 **Unclaimed** - Available for any staff\n⏱️ **Response Time** - Usually within 30 minutes",
                inline=False
            )
            
            # Description
            welcome_embed.add_field(
                name="📝 **About This Category**",
                value=category_info['description'],
                inline=False
            )
            
            welcome_embed.set_author(name=f"Ticket #{user.id % 10000}", icon_url=user.display_avatar.url)
            welcome_embed.set_footer(text="✨ Support Team - We're here to help!")
            welcome_embed.set_thumbnail(url=user.display_avatar.url)
            
            # Create control buttons
            control_view = CoolTicketControls(user.id, category_key, category_info['name'])
            
            # Welcome message with pings
            support_role_mentions = []
            for role_id in ticket_support_roles:
                role = guild.get_role(role_id)
                if role:
                    support_role_mentions.append(role.mention)
            
            welcome_content = f"""🎫 **New {category_info['name']} Ticket Created!**

{user.mention} has created a support ticket. Our team will assist you shortly!

**📋 Quick Info:**
• **Category:** {category_info['name']}
• **Ticket ID:** #{user.id % 10000}
• **Priority:** 🟢 Normal

**📞 What's Next:**
1. A staff member will claim this ticket
2. They'll assist you with your {category_info['name'].lower()}
3. The ticket will be resolved efficiently

**💡 While You Wait:**
• Provide any additional details that might help
• Stay patient - we typically respond within 30 minutes
• Keep the conversation in this channel

{' '.join(support_role_mentions) if support_role_mentions else ''}

---
*Use the buttons below to manage this ticket*"""

            # Send welcome message
            welcome_msg = await ticket_channel.send(
                content=welcome_content,
                embed=welcome_embed,
                view=control_view
            )
            
            # Pin the message
            try:
                await welcome_msg.pin()
            except:
                pass
            
            # Log ticket creation
            try:
                db.log_ticket_creation(guild.id, user.id, ticket_channel.id, category_key, category_info['name'])
            except:
                pass
            
            # Success response
            success_embed = discord.Embed(
                title="🎫 **Ticket Created Successfully!**",
                description=f"Your {category_info['name'].lower()} ticket has been created in {ticket_channel.mention}",
                color=0x00d4aa
            )
            success_embed.add_field(
                name="⚡ **Quick Access**",
                value=f"Click here to go to your ticket: {ticket_channel.mention}",
                inline=False
            )
            success_embed.set_footer(text="✨ Our support team will assist you shortly!")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating ticket: {str(e)}", ephemeral=True)