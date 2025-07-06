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

# Enhanced ticket categories with subcategories and claim system
TICKET_CATEGORIES = {
    "general": {
        "name": "🆘 General Support",
        "description": "General questions and basic help",
        "emoji": "🆘",
        "color": 0x7289da,
        "subcategories": [
            {"name": "Account Help", "emoji": "👤", "description": "Profile and account issues"},
            {"name": "Bot Commands", "emoji": "🤖", "description": "Help with bot commands"},
            {"name": "Server Rules", "emoji": "📜", "description": "Questions about server rules"},
            {"name": "General Question", "emoji": "❓", "description": "Any other general question"}
        ]
    },
    "technical": {
        "name": "🔧 Technical Issues",
        "description": "Bug reports and technical problems",
        "emoji": "🔧",
        "color": 0xff6b6b,
        "subcategories": [
            {"name": "Bot Bug", "emoji": "🐛", "description": "Bot not working properly"},
            {"name": "Discord Issue", "emoji": "💻", "description": "Discord app problems"},
            {"name": "Server Problem", "emoji": "🌐", "description": "Server functionality issues"},
            {"name": "Permission Error", "emoji": "🚫", "description": "Can't access something"}
        ]
    },
    "billing": {
        "name": "💳 Billing & VIP",
        "description": "VIP status and premium features",
        "emoji": "💳",
        "color": 0xffd700,
        "subcategories": [
            {"name": "VIP Benefits", "emoji": "⭐", "description": "Questions about VIP perks"},
            {"name": "Premium Features", "emoji": "💎", "description": "Help with premium features"},
            {"name": "Boost Issues", "emoji": "🚀", "description": "Server boost problems"},
            {"name": "Subscription", "emoji": "📋", "description": "Membership questions"}
        ]
    },
    "report": {
        "name": "🚨 Report & Moderation",
        "description": "Report users, content, or violations",
        "emoji": "🚨",
        "color": 0xff4444,
        "subcategories": [
            {"name": "User Report", "emoji": "👤", "description": "Report problematic user"},
            {"name": "Content Report", "emoji": "📝", "description": "Report inappropriate content"},
            {"name": "Spam Report", "emoji": "📧", "description": "Report spam or scam"},
            {"name": "Rule Violation", "emoji": "⚖️", "description": "Report rule breaking"}
        ]
    },
    "appeal": {
        "name": "⚖️ Appeal & Unban",
        "description": "Appeal bans, warnings, or punishments",
        "emoji": "⚖️",
        "color": 0x9966ff,
        "subcategories": [
            {"name": "Ban Appeal", "emoji": "🔓", "description": "Appeal a ban"},
            {"name": "Warning Appeal", "emoji": "⚠️", "description": "Appeal a warning"},
            {"name": "Mute Appeal", "emoji": "🔇", "description": "Appeal a mute"},
            {"name": "Other Appeal", "emoji": "📋", "description": "Appeal other punishment"}
        ]
    },
    "regional": {
        "name": "🌍 Regional Support",
        "description": "Location-based and regional assistance",
        "emoji": "🌍",
        "color": 0x00d4aa,
        "subcategories": [
            {"name": "UK Support", "emoji": "🇬🇧", "description": "United Kingdom regional support"},
            {"name": "US Support", "emoji": "🇺🇸", "description": "United States regional support"},
            {"name": "EU Support", "emoji": "🇪🇺", "description": "European Union regional support"},
            {"name": "Other Region", "emoji": "🌎", "description": "Other regional support"}
        ]
    },
    "partnership": {
        "name": "🤝 Partnership & Business",
        "description": "Server partnerships and business inquiries",
        "emoji": "🤝",
        "color": 0x7c3aed,
        "subcategories": [
            {"name": "Server Partnership", "emoji": "🌐", "description": "Partner with our server"},
            {"name": "Business Inquiry", "emoji": "💼", "description": "Business opportunities"},
            {"name": "Collaboration", "emoji": "🤝", "description": "Work together on projects"},
            {"name": "Sponsorship", "emoji": "💰", "description": "Sponsorship opportunities"}
        ]
    },
    "feedback": {
        "name": "💡 Feedback & Suggestions",
        "description": "Share your ideas and feedback",
        "emoji": "💡",
        "color": 0x00d4aa,
        "subcategories": [
            {"name": "Server Improvement", "emoji": "🔧", "description": "Suggest server improvements"},
            {"name": "Bot Feature", "emoji": "🤖", "description": "Suggest bot features"},
            {"name": "Event Idea", "emoji": "🎉", "description": "Suggest events or activities"},
            {"name": "General Feedback", "emoji": "💭", "description": "Share your thoughts"}
        ]
    },
    "other": {
        "name": "📋 Other",
        "description": "Everything else not covered above",
        "emoji": "📋",
        "color": 0x6c757d,
        "subcategories": [
            {"name": "Custom Request", "emoji": "🎯", "description": "Special request"},
            {"name": "Information", "emoji": "ℹ️", "description": "Need information"},
            {"name": "Verification", "emoji": "✅", "description": "Account verification"},
            {"name": "Miscellaneous", "emoji": "❓", "description": "Anything else"}
        ]
    }
}

class TicketCategorySelectView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())

class TicketCategorySelect(Select):
    def __init__(self):
        options = []
        for category_key, category_info in TICKET_CATEGORIES.items():
            options.append(
                discord.SelectOption(
                    label=category_info['name'],
                    description=category_info['description'],
                    emoji=category_info['emoji'],
                    value=category_key
                )
            )
        
        super().__init__(
            placeholder="🎫 Select a ticket category to get started...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_category_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        category_key = self.values[0]
        category_info = TICKET_CATEGORIES[category_key]
        
        # Create subcategory view
        view = TicketSubcategoryView(category_key, category_info)
        
        embed = discord.Embed(
            title=f"{category_info['emoji']} **{category_info['name']}**",
            description=f"Great choice! Now please select a specific subcategory that best matches your needs:\n\n**{category_info['description']}**",
            color=category_info['color'],
            timestamp=datetime.now()
        )
        
        # Add subcategory information
        subcategory_text = ""
        for sub in category_info['subcategories']:
            subcategory_text += f"{sub['emoji']} **{sub['name']}** - {sub['description']}\n"
        
        embed.add_field(
            name="📋 Available Subcategories",
            value=subcategory_text,
            inline=False
        )
        
        embed.set_footer(text="Select a subcategory below to continue")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class TicketSubcategoryView(View):
    def __init__(self, category_key: str, category_info: dict):
        super().__init__(timeout=60)
        self.category_key = category_key
        self.category_info = category_info
        self.add_item(TicketSubcategorySelect(category_key, category_info))

class TicketSubcategorySelect(Select):
    def __init__(self, category_key: str, category_info: dict):
        self.category_key = category_key
        self.category_info = category_info
        
        options = []
        for sub in category_info['subcategories']:
            options.append(
                discord.SelectOption(
                    label=sub['name'],
                    description=sub['description'],
                    emoji=sub['emoji'],
                    value=sub['name']
                )
            )
        
        super().__init__(
            placeholder="Choose the most specific subcategory...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        subcategory = self.values[0]
        
        # Open ticket creation modal
        modal = TicketCreationModal(self.category_key, self.category_info, subcategory)
        await interaction.response.send_modal(modal)

class TicketCreationModal(Modal):
    def __init__(self, category_key: str, category_info: dict, subcategory: str):
        super().__init__(title=f"✨ Create {category_info['name']} Ticket")
        self.category_key = category_key
        self.category_info = category_info
        self.subcategory = subcategory
        
        self.title_input = TextInput(
            label="✨ Ticket Title",
            placeholder="Brief, descriptive title for your request",
            max_length=100,
            required=True
        )
        
        self.description_input = TextInput(
            label="� Detailed Description",
            placeholder="Provide clear details about your request. The more specific, the better we can help!",
            style=discord.TextStyle.paragraph,
            max_length=1500,
            required=True
        )
        
        self.priority_input = TextInput(
            label="⚡ Priority (Low/Medium/High/Urgent)",
            placeholder="Low",
            max_length=10,
            required=False
        )
        
        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.priority_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Check if user already has an open ticket
            guild = interaction.guild
            user = interaction.user
            
            # Look for existing ticket channels
            existing_channel = None
            for channel in guild.text_channels:
                if channel.name.startswith(f"ticket-{user.display_name.lower()}-") and f"-{user.id}" in channel.name:
                    existing_channel = channel
                    break
            
            if existing_channel:
                embed = discord.Embed(
                    title="⚠️ **Active Ticket Found**",
                    description=f"You already have an open ticket: {existing_channel.mention}",
                    color=0xff9966
                )
                embed.add_field(
                    name="💡 **What to do?**",
                    value="Please close your existing ticket first or continue the conversation there.",
                    inline=False
                )
                embed.set_footer(text="✨ One ticket at a time for better organization")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create category if it doesn't exist
            category_name = "✨ Support Hub"
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                try:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False)
                    }
                    category = await guild.create_category(category_name, overwrites=overwrites)
                except discord.Forbidden:
                    category = None
            
            # Create unique channel name with elegant formatting
            safe_title = "".join(c for c in self.title_input.value if c.isalnum() or c in (' ', '-')).strip()
            safe_title = safe_title.replace(' ', '-')[:25]  # Slightly longer for clarity
            channel_name = f"ticket-{user.display_name.lower().replace(' ', '-')}-{safe_title}-{user.id}"
            
            # Enhanced permissions with proper hierarchy
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
            
            # Get ticket support roles from database
            server_settings = db.get_server_settings(guild.id)
            ticket_support_roles = server_settings.get('ticket_support_roles', [])
            
            # Add ticket support roles to permissions
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
            
            # Also add admin roles as fallback with premium perms
            for role in guild.roles:
                if any(name in role.name.lower() for name in ["admin", "mod", "staff", "support", "helper"]):
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
            
            # Create ticket channel with elegant topic
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"✨ {self.category_info['emoji']} {self.category_info['name']} • {self.subcategory} • {user.display_name} • {self.title_input.value} • Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Get priority color with elegant scheme
            priority = self.priority_input.value.lower() if self.priority_input.value else "low"
            priority_colors = {
                "low": 0x28a745,     # Elegant green
                "medium": 0xffc107,  # Professional yellow  
                "high": 0xff6b6b,    # Attention orange-red
                "urgent": 0xe74c3c   # Critical red
            }
            priority_color = priority_colors.get(priority, 0x28a745)
            
            # Priority emoji mapping
            priority_emojis = {
                "low": "🟢",
                "medium": "🟡", 
                "high": "🟠",
                "urgent": "🔴"
            }
            priority_emoji = priority_emojis.get(priority, "🟢")
            
            # MEE6-style clean and simple welcome embed
            welcome_embed = discord.Embed(
                title=f"🎫 {self.title_input.value}",
                description=self.description_input.value,
                color=priority_color,
                timestamp=datetime.now()
            )
            
            welcome_embed.set_author(name=f"{user.display_name} opened a ticket", icon_url=user.display_avatar.url)
            welcome_embed.set_footer(text=f"{self.subcategory} • {priority_emoji} {priority.title()} Priority")
            
            # Create simple ticket controls
            control_view = TicketControlView(user.id, self.category_key, self.subcategory)
            
            # Simple welcome message with role pings
            support_role_mentions = []
            for role_id in ticket_support_roles:
                role = guild.get_role(role_id)
                if role:
                    support_role_mentions.append(role.mention)
            
            # Simple welcome message
            welcome_content = f"""🎫 Hello {user.mention}! Thank you for opening a support ticket.

Our support team will be with you shortly. Please explain your issue in detail below.

{' '.join(support_role_mentions) if support_role_mentions else ''}
            """.strip()
            
            welcome_msg = await ticket_channel.send(
                content=welcome_content,
                embed=welcome_embed,
                view=control_view
            )
            
            # Pin the message for easy access
            try:
                await welcome_msg.pin()
            except:
                pass
            
            # Log ticket creation
            try:
                db.log_ticket_creation(guild.id, user.id, ticket_channel.id, f"{self.category_key}_{self.subcategory}", self.title_input.value)
            except:
                pass
            
            # Simple success response like MEE6
            success_embed = discord.Embed(
                title="🎫 Ticket Created",
                description=f"Your ticket has been created in {ticket_channel.mention}\n\nOur support team will assist you shortly.",
                color=0x00d4aa
            )
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Ticket Creation Failed**",
                description="We encountered an issue creating your ticket. Please try again.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔧 **Troubleshooting Steps**",
                value="• Ensure you don't have an existing open ticket\n• Verify the bot has proper permissions\n• Try again in a few moments\n• Contact staff directly if the issue persists",
                inline=False
            )
            error_embed.add_field(
                name="🔍 **Error Details**",
                value=f"```{str(e)[:150]}...```",
                inline=False
            )
            error_embed.set_footer(text="🛠️ Technical Support")
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class ClaimedTicketView(View):
    def __init__(self, creator_id: int, category_key: str, subcategory: str, claimer_id: int):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.category_key = category_key
        self.subcategory = subcategory
        self.claimer_id = claimer_id

    def has_ticket_permissions(self, user, guild):
        """Check if user has ticket permissions"""
        if user.id == self.creator_id or user.id == self.claimer_id:
            return True
        if user.guild_permissions.manage_channels:
            return True
        
        # Check for special admin role
        if any(role.id == 1376574861333495910 for role in user.roles):
            return True
        
        # Check if user has ticket support role
        server_settings = db.get_server_settings(guild.id)
        ticket_support_roles = server_settings.get('ticket_support_roles', [])
        
        for role in user.roles:
            if role.id in ticket_support_roles:
                return True
        
        # Check for admin/mod/staff roles as fallback
        for role in user.roles:
            if any(name in role.name.lower() for name in ["admin", "mod", "staff", "support", "helper"]):
                return True
        
        return False

    @discord.ui.button(label="🔄 Unclaim Ticket", style=discord.ButtonStyle.secondary, custom_id="unclaim_ticket_btn")
    async def unclaim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ **Permission Denied**",
                description="Only staff members can unclaim tickets.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        channel = interaction.channel
        topic = channel.topic or ""
        
        # Check if ticket is claimed
        if "🔒 CLAIMED" not in topic:
            embed = discord.Embed(
                title="⚠️ **Not Claimed**",
                description="This ticket is not currently claimed.",
                color=0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Cool channel renaming back to unclaimed
        old_name = channel.name
        if old_name.startswith("🔒-claimed-"):
            # Extract original info and recreate unclaimed name
            parts = old_name.replace("🔒-claimed-", "").split("-")
            if len(parts) >= 3:
                user_part = parts[0]
                title_part = parts[1]
                user_id = parts[-1]
                new_name = f"ticket-{user_part}-{title_part}-{user_id}"[:100]
            else:
                new_name = f"ticket-{'-'.join(parts)}"[:100]
        else:
            new_name = old_name.replace("🔒-claimed-", "ticket-")[:100]
        
        try:
            # Rename channel back to unclaimed format
            await channel.edit(name=new_name)
            
            # Update topic to remove claim info
            new_topic = topic.split("🔒 CLAIMED")[1].split(" • ", 2)[-1] if "🔒 CLAIMED" in topic else topic
            await channel.edit(topic=new_topic[:1024])
            
            # Move back to main support category
            support_category = discord.utils.get(interaction.guild.categories, name="✨ Support Hub")
            if support_category:
                await channel.edit(category=support_category)
                
        except Exception as e:
            print(f"Error unclaiming ticket: {e}")
        
        # Create unclaim embed
        embed = discord.Embed(
            title="🔄 **Ticket Unclaimed**",
            description=f"**{interaction.user.display_name}** has unclaimed this ticket. It's now available for other staff members.",
            color=0x7289da,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📋 **Status**",
            value="🟡 Available for claiming\n✨ Waiting for staff assignment",
            inline=True
        )
        
        embed.add_field(
            name="⏰ **Unclaimed At**",
            value=f"<t:{int(datetime.now().timestamp())}:R>",
            inline=True
        )
        
        embed.set_footer(text="🎫 Ready for staff to claim and assist")
        
        # Back to original control view
        view = TicketControlView(self.creator_id, self.category_key, self.subcategory)
        
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔴 Close & Archive", style=discord.ButtonStyle.danger, custom_id="close_archive_btn")
    async def close_and_archive(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ **Permission Denied**",
                description="Only the ticket creator or staff can close tickets.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Confirmation view
        view = TicketCloseConfirmView(interaction.user.id)
        
        embed = discord.Embed(
            title="⚠️ **Confirm Ticket Closure**",
            description="Are you sure you want to close and archive this ticket?\n\n**This action will:**\n• Save the ticket conversation\n• Archive the channel\n• Remove access for the user\n• Generate a support summary",
            color=0xff6b6b
        )
        embed.add_field(name="⚡ **Quick Close**", value="The ticket will be archived automatically in 30 seconds if no action is taken.", inline=False)
        embed.set_footer(text="🔴 This action cannot be undone")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="⚡ Set Priority", style=discord.ButtonStyle.primary, custom_id="set_priority_btn")
    async def set_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ **Permission Denied**",
                description="Only staff members can change ticket priority.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        view = PriorityUpdateView()
        
        embed = discord.Embed(
            title="⚡ **Update Ticket Priority**",
            description="Select the new priority level for this ticket:",
            color=0x7c3aed
        )
        
        priority_info = {
            "🟢 Low": "Standard requests, general questions",
            "🟡 Medium": "Account issues, moderate problems", 
            "🟠 High": "Urgent issues, important requests",
            "🔴 Urgent": "Critical problems, immediate attention needed"
        }
        
        for priority, desc in priority_info.items():
            embed.add_field(name=priority, value=desc, inline=True)
        
        embed.set_footer(text="Priority affects response time and staff assignment")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class TicketControlView(View):
    def __init__(self, creator_id: int, category_key: str, subcategory: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.category_key = category_key
        self.subcategory = subcategory

    def has_ticket_permissions(self, user, guild):
        """Check if user has ticket permissions"""
        if user.id == self.creator_id:
            return True
        if user.guild_permissions.manage_channels:
            return True
        
        # Check for special admin role (role ID 1376574861333495910)
        if any(role.id == 1376574861333495910 for role in user.roles):
            return True
        
        # Check if user has ticket support role
        server_settings = db.get_server_settings(guild.id)
        ticket_support_roles = server_settings.get('ticket_support_roles', [])
        
        for role in user.roles:
            if role.id in ticket_support_roles:
                return True
        
        # Check for admin/mod/staff roles as fallback
        for role in user.roles:
            if any(name in role.name.lower() for name in ["admin", "mod", "staff", "support", "helper"]):
                return True
        
        return False

    @discord.ui.button(label="👤 Claim Ticket", style=discord.ButtonStyle.success, custom_id="claim_ticket_btn")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ **Permission Denied**",
                description="Only staff members can claim tickets.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        channel = interaction.channel
        topic = channel.topic or ""
        
        # Check if already claimed
        if "🔒 CLAIMED" in topic or f"👤 {interaction.user.display_name}" in topic:
            embed = discord.Embed(
                title="⚠️ **Already Claimed**",
                description=f"This ticket is already claimed by a staff member.",
                color=0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Cool channel renaming after claiming
        old_name = channel.name
        if old_name.startswith("ticket-"):
            # Extract base info
            parts = old_name.split("-")
            if len(parts) >= 4:
                user_part = parts[1]
                title_part = parts[2]
                user_id = parts[-1]
                
                # Create new cool claimed name format
                new_name = f"🔒-claimed-{user_part}-{title_part}-{interaction.user.name.lower()}-{user_id}"[:100]
            else:
                new_name = f"🔒-claimed-{old_name[7:]}-{interaction.user.name.lower()}"[:100]
        else:
            new_name = f"🔒-claimed-{channel.name}-{interaction.user.name.lower()}"[:100]
        
        try:
            # Rename channel with cool claimed format
            await channel.edit(name=new_name)
            
            # Update topic with claim info and timestamp
            claimed_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            new_topic = f"🔒 CLAIMED by {interaction.user.display_name} • {claimed_time} • " + topic
            await channel.edit(topic=new_topic[:1024])
            
            # Move to claimed category if it exists
            claimed_category = discord.utils.get(interaction.guild.categories, name="🔒 Claimed Tickets")
            if claimed_category:
                await channel.edit(category=claimed_category)
            
            # Log claim in database
            try:
                db.log_ticket_claim(interaction.guild.id, channel.id, interaction.user.id)
            except:
                pass
                
        except Exception as e:
            print(f"Error updating claimed ticket: {e}")
        
        # Create awesome claim embed
        embed = discord.Embed(
            title="🔒 **Ticket Claimed Successfully!**",
            description=f"**{interaction.user.display_name}** has claimed this ticket and will handle your request.",
            color=0x00d4aa,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👤 **Assigned Staff**",
            value=f"{interaction.user.mention}\n`{interaction.user.display_name}`",
            inline=True
        )
        
        embed.add_field(
            name="⏰ **Claimed At**",
            value=f"<t:{int(datetime.now().timestamp())}:F>",
            inline=True
        )
        
        embed.add_field(
            name="📋 **Next Steps**",
            value="• Staff will review your request\n• Please provide any additional details\n• Average response time: 5-15 minutes",
            inline=False
        )
        
        embed.set_author(name="Ticket Management System", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="✨ Professional Support • Fast Response Guaranteed")
        
        # Update the view to show claimed status
        view = ClaimedTicketView(self.creator_id, self.category_key, self.subcategory, interaction.user.id)
        
        await interaction.response.edit_message(embed=embed, view=view)
        
        # Handle unclaim if already claimed
        if "| Claimed by:" in topic:
            current_claimer = topic.split("| Claimed by:")[-1].strip()
            
            # Only allow the claimer or higher permissions to unclaim
            if current_claimer != interaction.user.display_name and not interaction.user.guild_permissions.administrator:
                embed = discord.Embed(
                    title="⚠️ **Cannot Unclaim**",
                    description=f"This ticket is claimed by **{current_claimer}**. Only they or an administrator can unclaim it.",
                    color=0xff9966
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Unclaim the ticket
            try:
                new_topic = topic.split("| Claimed by:")[0].strip()
                await channel.edit(topic=new_topic)
                
                embed = discord.Embed(
                    title="🔄 Ticket Unclaimed",
                    description="This ticket is now available for any staff member to claim.",
                    color=0x7c3aed
                )
                
                await interaction.response.send_message(embed=embed)
                
                # Update button back to claim
                button.label = "👤 Claim Ticket"
                button.style = discord.ButtonStyle.success
                await interaction.edit_original_response(view=self)
                
            except Exception as e:
                await interaction.response.send_message(f"❌ Error unclaiming ticket: {str(e)}", ephemeral=True)
            return
        
        # Claim the ticket
        try:
            new_topic = f"{topic} | Claimed by: {interaction.user.display_name}"
            await channel.edit(topic=new_topic)
            
            embed = discord.Embed(
                title="👤 Ticket Claimed",
                description=f"{interaction.user.mention} is now handling this ticket.",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            await interaction.response.send_message(embed=embed)
            
            # Update button to show unclaim option
            button.label = "🔄 Unclaim Ticket"
            button.style = discord.ButtonStyle.secondary
            await interaction.edit_original_response(view=self)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error claiming ticket: {str(e)}", ephemeral=True)

    @discord.ui.button(label="🟢 Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_ticket_permissions(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ **Permission Denied**",
                description="Only the ticket creator or staff members can close this ticket.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create confirmation view
        confirm_view = TicketCloseConfirmView(interaction.user.id)
        
        confirm_embed = discord.Embed(
            title="🔒 Close Ticket",
            description="Are you sure you want to close this ticket?\n\n⚠️ This will delete the channel.",
            color=0xff9966
        )
        
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=True)





class TicketCloseConfirmView(View):
    def __init__(self, closer_id: int):
        super().__init__(timeout=30)
        self.closer_id = closer_id

    @discord.ui.button(label="✅ Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.closer_id:
            await interaction.response.send_message("❌ Only the person who initiated the close can confirm.", ephemeral=True)
            return
        
        channel = interaction.channel
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Ticket closed by {interaction.user.mention}\n\nChannel will be deleted in 10 seconds.",
            color=0x28a745
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Log ticket closure
        try:
            db.log_ticket_closure(interaction.guild.id, interaction.user.id, channel.id)
        except:
            pass
        
        # Delete the channel after 10 seconds
        await asyncio.sleep(10)
        try:
            await channel.delete(reason=f"Ticket closed by {interaction.user.display_name}")
        except:
            pass

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="✅ **Ticket Closure Cancelled**",
            description="The ticket will remain open.",
            color=0x28a745
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)



class PriorityUpdateView(View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="🟢 Low", style=discord.ButtonStyle.success)
    async def low_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Low", 0x28a745)

    @discord.ui.button(label="🟡 Medium", style=discord.ButtonStyle.secondary)
    async def medium_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Medium", 0xffc107)

    @discord.ui.button(label="🟠 High", style=discord.ButtonStyle.secondary)
    async def high_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "High", 0xff6b6b)

    @discord.ui.button(label="🔴 Urgent", style=discord.ButtonStyle.danger)
    async def urgent_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Urgent", 0xdc3545)

    async def update_priority(self, interaction: discord.Interaction, priority: str, color: int):
        embed = discord.Embed(
            title=f"📋 **Priority Updated to {priority}**",
            description=f"This ticket's priority has been changed to **{priority}**",
            color=color,
            timestamp=datetime.now()
        )
        embed.set_author(name=f"Priority updated by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        # Update channel topic
        channel = interaction.channel
        if channel.topic:
            topic_parts = channel.topic.split(" | ")
            if len(topic_parts) >= 3:
                topic_parts[2] = f"{priority} Priority"
                new_topic = " | ".join(topic_parts)
                try:
                    await channel.edit(topic=new_topic)
                except:
                    pass
        
        await interaction.response.send_message(embed=embed)

class TicketFormView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="create_ticket_btn")
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle ticket creation button click"""
        try:
            # Create category selection view
            view = TicketCategorySelectView()
            
            embed = discord.Embed(
                title="🎫 **Create Support Ticket**",
                description="Please select the category that best matches your support need:",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 **Categories Available**",
                value="Choose from the dropdown menu below to get started with your ticket.",
                inline=False
            )
            
            embed.set_footer(text="Select a category to continue • Professional Support")
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Error**",
                description="Failed to start ticket creation. Please try again.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views
        self.bot.add_view(TicketCategorySelectView())
        self.bot.add_view(TicketFormView())
        print("[Tickets] Loaded successfully with persistent views.")

    @app_commands.command(name="createticket", description="🎫 Create a support ticket instantly")
    async def create_ticket_quick(self, interaction: discord.Interaction):
        """Quick ticket creation for everyone"""
        try:
            # Create category selection view
            view = TicketCategorySelectView()
            
            embed = discord.Embed(
                title="🎫 **Create Support Ticket**",
                description="Please select the category that best matches your support need:",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 **Categories Available**",
                value="Choose from the dropdown menu below to get started with your ticket.",
                inline=False
            )
            
            embed.set_footer(text="Select a category to continue • Professional Support")
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Error**",
                description="Failed to start ticket creation. Please try again.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="ticketpanel", description="🎫 Create ticket panel in current channel (Admin only)")
    @app_commands.describe(channel="Channel where the ticket panel will be posted (optional)")
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Create a ticket panel that everyone can use"""
        # Check permissions - allow special role or admin
        if not (interaction.user.guild_permissions.administrator or has_special_permissions(interaction)):
            await interaction.response.send_message("❌ You need administrator permissions or the special admin role to use this command!", ephemeral=True)
            return
        
        try:
            await interaction.response.defer()
            
            target_channel = channel or interaction.channel
            
            # Check bot permissions in target channel
            bot_permissions = target_channel.permissions_for(interaction.guild.me)
            if not all([bot_permissions.send_messages, bot_permissions.embed_links, bot_permissions.manage_channels]):
                missing_perms = []
                if not bot_permissions.send_messages:
                    missing_perms.append("Send Messages")
                if not bot_permissions.embed_links:
                    missing_perms.append("Embed Links")
                if not bot_permissions.manage_channels:
                    missing_perms.append("Manage Channels")
                
                embed = discord.Embed(
                    title="❌ **Missing Permissions**",
                    description=f"I need the following permissions in {target_channel.mention}:",
                    color=0xff6b6b
                )
                embed.add_field(
                    name="🔧 **Required Permissions**",
                    value="\n".join([f"• {perm}" for perm in missing_perms]),
                    inline=False
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create comprehensive ticket form embed
            embed = discord.Embed(
                title="🎫 **Support Ticket System**",
                description="Welcome to our support system! Click the button below to create a ticket for any assistance you need.",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # Add all ticket categories with their descriptions
            categories_text = ""
            for category_key, category_info in TICKET_CATEGORIES.items():
                categories_text += f"{category_info['emoji']} **{category_info['name']}**\n{category_info['description']}\n\n"
            
            embed.add_field(
                name="📋 **Available Categories**",
                value=categories_text,
                inline=False
            )
            
            embed.add_field(
                name="🚀 **How It Works**",
                value="1️⃣ Click **'Create Ticket'** below\n2️⃣ Select your ticket category\n3️⃣ Choose specific subcategory\n4️⃣ Fill out the ticket form\n5️⃣ Get help from our support team!",
                inline=False
            )
            
            embed.add_field(
                name="⚡ **Response Times**",
                value="• **Urgent:** Within 1 hour\n• **High:** Within 4 hours\n• **Medium:** Within 24 hours\n• **Low:** Within 48 hours",
                inline=True
            )
            
            embed.add_field(
                name="🛡️ **Privacy**",
                value="• Private channels created for each ticket\n• Only you and staff can see your ticket\n• Secure and confidential support",
                inline=True
            )
            
            embed.set_footer(text="🎯 Professional Ticket System • Create a ticket anytime!")
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            # Create the view with ticket button
            view = TicketFormView()
            
            # Send the ticket form
            await target_channel.send(embed=embed, view=view)
            
            # Success response
            success_embed = discord.Embed(
                title="✅ **Ticket Panel Created Successfully!**",
                description=f"The ticket panel has been posted in {target_channel.mention}",
                color=0x00d4aa
            )
            success_embed.add_field(
                name="🎯 **What's Next?**",
                value="Users can now click the button to create tickets for any support needs!",
                inline=False
            )
            success_embed.set_footer(text="🎫 Ticket System Ready")
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Failed to Create Ticket Panel**",
                description="There was an error creating the ticket panel. Please try again.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔍 **Error Details**",
                value=f"```{str(e)[:100]}```",
                inline=False
            )
            
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="giveticketroleperms", description="🎫 Grant ticket support permissions to roles (Admin only)")
    @app_commands.describe(
        action="Action to perform",
        role="Role to add or remove ticket permissions"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add Role", value="add"),
        app_commands.Choice(name="Remove Role", value="remove"),
        app_commands.Choice(name="List Roles", value="list")
    ])
    @app_commands.default_permissions(administrator=True)
    async def give_ticket_role_perms(self, interaction: discord.Interaction, action: str, role: discord.Role = None):
        """Manage ticket support role permissions"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can manage ticket role permissions!", ephemeral=True)
            return
        
        guild_id = interaction.guild.id
        server_settings = db.get_server_settings(guild_id)
        ticket_support_roles = server_settings.get('ticket_support_roles', [])
        
        if action == "add":
            if not role:
                await interaction.response.send_message("❌ Please specify a role to add!", ephemeral=True)
                return
            
            if role.id in ticket_support_roles:
                embed = discord.Embed(
                    title="⚠️ **Role Already Has Permissions**",
                    description=f"{role.mention} already has ticket support permissions.",
                    color=0xff9966
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            ticket_support_roles.append(role.id)
            db.set_guild_setting(guild_id, 'ticket_support_roles', ticket_support_roles)
            
            embed = discord.Embed(
                title="✅ **Ticket Permissions Granted**",
                description=f"Successfully granted ticket support permissions to {role.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🎫 **Permissions Granted**",
                value="• Can view all tickets\n• Can close tickets\n• Can add notes\n• Can update priority\n• Can manage ticket system",
                inline=False
            )
            
        elif action == "remove":
            if not role:
                await interaction.response.send_message("❌ Please specify a role to remove!", ephemeral=True)
                return
            
            if role.id not in ticket_support_roles:
                embed = discord.Embed(
                    title="⚠️ **Role Doesn't Have Permissions**",
                    description=f"{role.mention} doesn't have ticket support permissions.",
                    color=0xff9966
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            ticket_support_roles.remove(role.id)
            db.set_guild_setting(guild_id, 'ticket_support_roles', ticket_support_roles)
            
            embed = discord.Embed(
                title="✅ **Ticket Permissions Removed**",
                description=f"Successfully removed ticket support permissions from {role.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
        elif action == "list":
            embed = discord.Embed(
                title="🎫 **Ticket Support Roles**",
                description="Roles with ticket support permissions:",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            if ticket_support_roles:
                role_list = []
                for role_id in ticket_support_roles:
                    role = interaction.guild.get_role(role_id)
                    if role:
                        role_list.append(f"• {role.mention} ({role.name})")
                    else:
                        role_list.append(f"• <@&{role_id}> (deleted role)")
                
                embed.add_field(
                    name="👥 **Support Roles**",
                    value="\n".join(role_list),
                    inline=False
                )
            else:
                embed.add_field(
                    name="👥 **Support Roles**",
                    value="No ticket support roles configured.\nUse `/giveticketroleperms add` to add roles.",
                    inline=False
                )
            
            embed.add_field(
                name="💡 **Note**",
                value="Administrators and users with 'Manage Channels' permission always have ticket access.",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ticketstats", description="📊 View comprehensive ticket system statistics")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        """View ticket statistics for the server"""
        
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You need 'Manage Channels' permission to view ticket statistics!", ephemeral=True)
            return
        
        try:
            guild_id = interaction.guild.id
            stats = db.get_ticket_stats(guild_id)
            
            embed = discord.Embed(
                title="📊 **Ticket System Statistics**",
                description=f"Statistics for {interaction.guild.name}",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="🎫 **Total Tickets**",
                value=f"**{stats.get('total_tickets', 0)}** tickets created",
                inline=True
            )
            
            embed.add_field(
                name="🔒 **Closed Tickets**",
                value=f"**{stats.get('closed_tickets', 0)}** tickets closed",
                inline=True
            )
            
            embed.add_field(
                name="🟢 **Open Tickets**",
                value=f"**{stats.get('total_tickets', 0) - stats.get('closed_tickets', 0)}** currently open",
                inline=True
            )
            
            # Configuration status
            server_settings = db.get_server_settings(guild_id)
            ticket_support_roles = server_settings.get('ticket_support_roles', [])
            
            embed.add_field(
                name="⚙️ **Configuration**",
                value=f"**Support Roles:** {len(ticket_support_roles)} configured\n**Status:** {'✅ Active' if ticket_support_roles else '⚠️ Basic setup'}",
                inline=False
            )
            
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text="Use /giveticketroleperms to configure support roles")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting ticket stats: {str(e)}", ephemeral=True)

    @app_commands.command(name="organizetickets", description="🗂️ Auto-organize tickets by status (claimed/unclaimed)")
    @app_commands.default_permissions(manage_channels=True)
    async def organize_tickets(self, interaction: discord.Interaction):
        """Automatically organize tickets into claimed and unclaimed categories"""
        await interaction.response.defer()
        
        guild = interaction.guild
        organized_count = 0
        
        try:
            # Create categories if they don't exist
            unclaimed_category = discord.utils.get(guild.categories, name="🎫 Open Tickets")
            claimed_category = discord.utils.get(guild.categories, name="🔒 Claimed Tickets")
            
            if not unclaimed_category:
                unclaimed_category = await guild.create_category("🎫 Open Tickets")
            
            if not claimed_category:
                claimed_category = await guild.create_category("🔒 Claimed Tickets")
            
            # Find all ticket channels
            ticket_channels = [ch for ch in guild.text_channels if ch.name.startswith(("ticket-", "🔒-claimed-"))]
            
            for channel in ticket_channels:
                try:
                    if channel.name.startswith("🔒-claimed-") or "🔒 CLAIMED" in (channel.topic or ""):
                        # Move to claimed category
                        if channel.category != claimed_category:
                            await channel.edit(category=claimed_category)
                            organized_count += 1
                    else:
                        # Move to unclaimed category
                        if channel.category != unclaimed_category:
                            await channel.edit(category=unclaimed_category)
                            organized_count += 1
                            
                    await asyncio.sleep(0.5)  # Rate limit protection
                    
                except Exception as e:
                    print(f"Error organizing channel {channel.name}: {e}")
                    continue
            
            embed = discord.Embed(
                title="🗂️ **Tickets Organized Successfully!**",
                description=f"Automatically sorted **{organized_count}** ticket channels by their claim status.",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 **Organization Results**",
                value=f"• **🎫 Open Tickets**: {len([ch for ch in unclaimed_category.channels if ch.name.startswith('ticket-')])}\n• **🔒 Claimed Tickets**: {len([ch for ch in claimed_category.channels if ch.name.startswith('🔒-claimed-')])}\n• **Total Organized**: {organized_count}",
                inline=False
            )
            
            embed.add_field(
                name="✨ **Benefits**",
                value="• Easier ticket management\n• Clear status visibility\n• Improved staff workflow\n• Better user experience",
                inline=False
            )
            
            embed.set_footer(text="🎫 Ticket Organization System • Run this command regularly for best results")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ **Organization Failed**",
                description=f"Error organizing tickets: {str(e)}",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="ticketleaderboard", description="🏆 View ticket resolution leaderboard for staff")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_leaderboard(self, interaction: discord.Interaction):
        """Show ticket resolution statistics for staff members"""
        try:
            # Get ticket statistics from database
            stats = db.get_ticket_stats(interaction.guild.id)
            
            embed = discord.Embed(
                title="🏆 **Ticket Resolution Leaderboard**",
                description="Top performing staff members based on ticket handling",
                color=0xffd700,
                timestamp=datetime.now()
            )
            
            if not stats or not stats.get('staff_stats'):
                embed.add_field(
                    name="📊 **No Data Available**",
                    value="No ticket resolution data found. Start claiming and resolving tickets to see statistics!",
                    inline=False
                )
            else:
                # Sort staff by tickets resolved
                staff_stats = sorted(stats['staff_stats'].items(), key=lambda x: x[1].get('resolved', 0), reverse=True)
                
                leaderboard_text = ""
                for i, (staff_id, data) in enumerate(staff_stats[:10]):
                    user = interaction.guild.get_member(int(staff_id))
                    if user:
                        position_emoji = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
                        resolved = data.get('resolved', 0)
                        claimed = data.get('claimed', 0)
                        avg_time = data.get('avg_resolution_time', 0)
                        
                        leaderboard_text += f"{position_emoji[i]} **{user.display_name}**\n"
                        leaderboard_text += f"   • Resolved: {resolved} tickets\n"
                        leaderboard_text += f"   • Claimed: {claimed} tickets\n"
                        if avg_time > 0:
                            hours = avg_time // 3600
                            minutes = (avg_time % 3600) // 60
                            leaderboard_text += f"   • Avg Resolution: {int(hours)}h {int(minutes)}m\n"
                        leaderboard_text += "\n"
                
                embed.add_field(
                    name="🎯 **Top Staff Members**",
                    value=leaderboard_text or "No staff statistics available",
                    inline=False
                )
            
            # Add overall server stats
            total_tickets = stats.get('total_tickets', 0)
            resolved_tickets = stats.get('resolved_tickets', 0)
            open_tickets = stats.get('open_tickets', 0)
            
            embed.add_field(
                name="📈 **Server Statistics**",
                value=f"• **Total Tickets**: {total_tickets}\n• **Resolved**: {resolved_tickets}\n• **Currently Open**: {open_tickets}\n• **Resolution Rate**: {(resolved_tickets/max(1,total_tickets)*100):.1f}%",
                inline=True
            )
            
            embed.set_footer(text="🏆 Updated automatically • Use /organizetickets to optimize workflow")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ **Leaderboard Error**",
                description=f"Could not retrieve ticket statistics: {str(e)}",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="autoarchive", description="🗃️ Auto-archive old resolved tickets")
    @app_commands.describe(days="Days old for tickets to be archived (default: 7)")
    @app_commands.default_permissions(manage_channels=True)
    async def auto_archive(self, interaction: discord.Interaction, days: int = 7):
        """Automatically archive old resolved tickets"""
        await interaction.response.defer()
        
        if days < 1 or days > 30:
            embed = discord.Embed(
                title="❌ **Invalid Days**",
                description="Days must be between 1 and 30.",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        guild = interaction.guild
        archived_count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        
        try:
            # Find archive category or create it
            archive_category = discord.utils.get(guild.categories, name="🗃️ Archived Tickets")
            if not archive_category:
                archive_category = await guild.create_category("🗃️ Archived Tickets")
                # Set permissions to hide archived tickets
                await archive_category.set_permissions(guild.default_role, read_messages=False)
            
            # Find old ticket channels
            for channel in guild.text_channels:
                if not channel.name.startswith(("ticket-", "🔒-claimed-")):
                    continue
                
                # Check if channel is old enough
                if channel.created_at.timestamp() < cutoff_time:
                    try:
                        # Archive the channel
                        old_name = channel.name
                        new_name = f"archived-{old_name}"[:100]
                        
                        await channel.edit(
                            name=new_name,
                            category=archive_category,
                            topic=f"🗃️ Auto-archived on {datetime.now().strftime('%Y-%m-%d')} • " + (channel.topic or "")
                        )
                        
                        # Send archive notification
                        embed = discord.Embed(
                            title="🗃️ **Ticket Archived**",
                            description=f"This ticket has been automatically archived due to inactivity ({days} days).",
                            color=0x6c757d,
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="📅 **Archived Date**", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=True)
                        embed.add_field(name="⏰ **Reason**", value=f"Inactive for {days} days", inline=True)
                        embed.set_footer(text="Contact staff to reopen if needed")
                        
                        await channel.send(embed=embed)
                        archived_count += 1
                        
                        await asyncio.sleep(1)  # Rate limit protection
                        
                    except Exception as e:
                        print(f"Error archiving channel {channel.name}: {e}")
                        continue
            
            embed = discord.Embed(
                title="🗃️ **Auto-Archive Complete**",
                description=f"Successfully archived **{archived_count}** old ticket channels.",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📊 **Archive Summary**",
                value=f"• **Channels Archived**: {archived_count}\n• **Age Threshold**: {days} days\n• **Archive Location**: {archive_category.mention}",
                inline=False
            )
            
            embed.add_field(
                name="💡 **Pro Tip**",
                value="Run this command regularly to keep your server organized and improve performance!",
                inline=False
            )
            
            embed.set_footer(text="🗃️ Auto-Archive System • Keeping your server clean and organized")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ **Archive Failed**",
                description=f"Error during auto-archive: {str(e)}",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="closealltickets", description="🚨 Emergency: Close all open tickets")
    @app_commands.default_permissions(administrator=True)
    async def close_all_tickets(self, interaction: discord.Interaction):
        """Emergency command to close all open tickets"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can use this emergency command!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        guild = interaction.guild
        closed_count = 0
        
        # Find all ticket channels
        ticket_channels = []
        for channel in guild.text_channels:
            if channel.name.startswith("ticket-"):
                ticket_channels.append(channel)
        
        if not ticket_channels:
            embed = discord.Embed(
                title="ℹ️ **No Open Tickets**",
                description="No open ticket channels found.",
                color=0x7c3aed
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Close all tickets
        for channel in ticket_channels:
            try:
                await channel.delete(reason=f"Emergency closure by {interaction.user.display_name}")
                closed_count += 1
            except:
                pass
        
        embed = discord.Embed(
            title="🚨 **Emergency Ticket Closure Complete**",
            description=f"Successfully closed **{closed_count}** ticket channels.",
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="⚠️ **Note**",
            value="This was an emergency action. Consider informing users about the closure.",
            inline=False
        )
        embed.set_footer(text=f"Action performed by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Tickets(bot))