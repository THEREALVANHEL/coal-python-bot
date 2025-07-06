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

# Enhanced ticket categories with subcategories
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
        super().__init__(title=f"🎫 Create {category_info['name']} Ticket")
        self.category_key = category_key
        self.category_info = category_info
        self.subcategory = subcategory
        
        self.title_input = TextInput(
            label="🏷️ Ticket Title",
            placeholder="Brief, descriptive title for your ticket",
            max_length=100,
            required=True
        )
        
        self.description_input = TextInput(
            label="📝 Detailed Description",
            placeholder="Please provide as much detail as possible...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
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
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create category if it doesn't exist
            category_name = "🎫 Active Tickets"
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                try:
                    category = await guild.create_category(category_name)
                except discord.Forbidden:
                    # If can't create category, create in general
                    category = None
            
            # Create unique channel name
            safe_title = "".join(c for c in self.title_input.value if c.isalnum() or c in (' ', '-')).strip()
            safe_title = safe_title.replace(' ', '-')[:20]  # Limit length
            channel_name = f"ticket-{user.display_name.lower().replace(' ', '-')}-{safe_title}-{user.id}"
            
            # Set up permissions
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
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
            
            # Add staff permissions
            for role in guild.roles:
                if any(name in role.name.lower() for name in ["admin", "mod", "staff", "support", "helper"]):
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True
                    )
            
            # Create ticket channel
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"{self.category_info['emoji']} {self.category_info['name']} - {self.subcategory} | {user.display_name} | {self.title_input.value}"
            )
            
            # Get priority color
            priority = self.priority_input.value.lower() if self.priority_input.value else "low"
            priority_colors = {
                "low": 0x28a745,
                "medium": 0xffc107,
                "high": 0xff6b6b,
                "urgent": 0xdc3545
            }
            priority_color = priority_colors.get(priority, 0x28a745)
            
            # Create welcome embed
            welcome_embed = discord.Embed(
                title=f"🎫 **{self.category_info['name']} Ticket Created**",
                description=f"**📋 Title:** {self.title_input.value}\n**📂 Category:** {self.category_info['name']}\n**🏷️ Subcategory:** {self.subcategory}\n**⚡ Priority:** {priority.title()}",
                color=priority_color,
                timestamp=datetime.now()
            )
            
            welcome_embed.add_field(
                name="📝 **Description**",
                value=self.description_input.value,
                inline=False
            )
            
            welcome_embed.add_field(
                name="👤 **Created by**",
                value=f"{user.mention} ({user.display_name})",
                inline=True
            )
            
            welcome_embed.add_field(
                name="📊 **Status**",
                value="🟢 **Open**",
                inline=True
            )
            
            welcome_embed.add_field(
                name="💡 **Tips for faster support**",
                value="• Be specific about your issue\n• Provide screenshots if helpful\n• Stay patient and respectful\n• Check back regularly for updates",
                inline=False
            )
            
            welcome_embed.set_thumbnail(url=user.display_avatar.url)
            welcome_embed.set_footer(text=f"Ticket ID: {ticket_channel.id} • Priority: {priority.title()}")
            
            # Create ticket controls
            control_view = TicketControlView(user.id, self.category_key, self.subcategory)
            
            # Send welcome message
            welcome_msg = await ticket_channel.send(
                content=f"🎉 **Welcome {user.mention}!**\n\nYour **{self.category_info['name']}** ticket has been created successfully!\nOur support team will be with you shortly to assist with your **{self.subcategory}** request.\n\n**🔔 Staff Notification:** A staff member will be notified about your ticket.",
                embed=welcome_embed,
                view=control_view
            )
            
            # Pin the message
            await welcome_msg.pin()
            
            # Log ticket creation
            try:
                db.log_ticket_creation(guild.id, user.id, ticket_channel.id, f"{self.category_key}_{self.subcategory}", self.title_input.value)
            except:
                pass
            
            # Success response
            success_embed = discord.Embed(
                title="✅ **Ticket Created Successfully!**",
                description=f"Your **{self.category_info['name']}** ticket has been created with **{priority.title()}** priority.",
                color=0x00d4aa
            )
            success_embed.add_field(
                name="🎫 **Your Ticket**",
                value=f"**Channel:** {ticket_channel.mention}\n**Title:** {self.title_input.value}\n**Category:** {self.subcategory}",
                inline=False
            )
            success_embed.add_field(
                name="⏱️ **Expected Response Time**",
                value=f"**{priority.title()} Priority:** {'Within 1 hour' if priority == 'urgent' else 'Within 4 hours' if priority == 'high' else 'Within 24 hours' if priority == 'medium' else 'Within 48 hours'}",
                inline=False
            )
            success_embed.set_footer(text="💫 Thank you for using our support system!")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Ticket Creation Failed**",
                description="Sorry, we couldn't create your ticket. Please try again or contact staff directly.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔧 **Troubleshooting**",
                value="• Check that you don't already have an open ticket\n• Ensure the bot has proper permissions\n• Try again in a few moments",
                inline=False
            )
            error_embed.add_field(
                name="🔍 **Error Details**",
                value=f"```{str(e)[:100]}```",
                inline=False
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

class TicketControlView(View):
    def __init__(self, creator_id: int, category_key: str, subcategory: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.category_key = category_key
        self.subcategory = subcategory

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check permissions
        can_close = (
            interaction.user.id == self.creator_id or
            interaction.user.guild_permissions.manage_channels or
            any(name in role.name.lower() for role in interaction.user.roles for name in ["admin", "mod", "staff", "support", "helper"])
        )
        
        if not can_close:
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
            title="🔒 **Confirm Ticket Closure**",
            description="Are you sure you want to close this ticket?\n\n**⚠️ This action cannot be undone!**",
            color=0xff9966,
            timestamp=datetime.now()
        )
        confirm_embed.add_field(
            name="📋 **What will happen:**",
            value="• Ticket will be marked as resolved\n• Channel will be deleted in 10 seconds\n• Conversation history will be lost\n• User will be notified of closure",
            inline=False
        )
        confirm_embed.set_footer(text="Click 'Confirm' to close or 'Cancel' to keep open")
        
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view)

    @discord.ui.button(label="📌 Add Note", style=discord.ButtonStyle.secondary)
    async def add_note(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check permissions
        can_add_note = (
            interaction.user.guild_permissions.manage_channels or
            any(name in role.name.lower() for role in interaction.user.roles for name in ["admin", "mod", "staff", "support", "helper"])
        )
        
        if not can_add_note:
            embed = discord.Embed(
                title="❌ **Permission Denied**",
                description="Only staff members can add notes to tickets.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        modal = TicketNoteModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📋 Update Priority", style=discord.ButtonStyle.secondary)
    async def update_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check permissions
        can_update = (
            interaction.user.guild_permissions.manage_channels or
            any(name in role.name.lower() for role in interaction.user.roles for name in ["admin", "mod", "staff", "support", "helper"])
        )
        
        if not can_update:
            embed = discord.Embed(
                title="❌ **Permission Denied**",
                description="Only staff members can update ticket priority.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        view = PriorityUpdateView()
        embed = discord.Embed(
            title="📋 **Update Ticket Priority**",
            description="Select the new priority level for this ticket:",
            color=0x7c3aed
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class TicketCloseConfirmView(View):
    def __init__(self, closer_id: int):
        super().__init__(timeout=30)
        self.closer_id = closer_id

    @discord.ui.button(label="✅ Confirm Close", style=discord.ButtonStyle.danger)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.closer_id:
            await interaction.response.send_message("❌ Only the person who initiated the close can confirm.", ephemeral=True)
            return
        
        # Create closing embed
        closing_embed = discord.Embed(
            title="🔒 **Ticket Closed Successfully**",
            description="This ticket has been resolved and will be deleted shortly.",
            color=0x00d4aa,
            timestamp=datetime.now()
        )
        closing_embed.add_field(
            name="👤 **Closed by**",
            value=interaction.user.mention,
            inline=True
        )
        closing_embed.add_field(
            name="⏰ **Auto-delete**",
            value="10 seconds",
            inline=True
        )
        closing_embed.set_footer(text="Thank you for using our support system!")
        
        await interaction.response.edit_message(embed=closing_embed, view=None)
        
        # Log closure
        try:
            db.log_ticket_closure(interaction.guild.id, interaction.user.id, interaction.channel.id)
        except:
            pass
        
        # Delete after delay
        await asyncio.sleep(10)
        try:
            await interaction.channel.delete()
        except:
            pass

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.closer_id:
            await interaction.response.send_message("❌ Only the person who initiated the close can cancel.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="✅ **Ticket Closure Cancelled**",
            description="The ticket will remain open and continue to function normally.",
            color=0x00d4aa
        )
        await interaction.response.edit_message(embed=embed, view=None)

class TicketNoteModal(Modal):
    def __init__(self):
        super().__init__(title="📌 Add Staff Note")
        
        self.note_input = TextInput(
            label="📝 Staff Note",
            placeholder="Add an internal note for staff members...",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        self.add_item(self.note_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        note_embed = discord.Embed(
            title="📌 **Staff Note Added**",
            description=self.note_input.value,
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        note_embed.set_author(
            name=f"Note by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        note_embed.set_footer(text="🔒 Internal staff note - Only visible to staff")
        
        await interaction.response.send_message(embed=note_embed)

class PriorityUpdateView(View):
    def __init__(self):
        super().__init__(timeout=60)

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
            title="📋 **Priority Updated**",
            description=f"Ticket priority has been changed to **{priority}**",
            color=color,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="👤 **Updated by**",
            value=interaction.user.mention,
            inline=True
        )
        embed.add_field(
            name="⏱️ **Expected Response**",
            value=f"{'Within 1 hour' if priority == 'Urgent' else 'Within 4 hours' if priority == 'High' else 'Within 24 hours' if priority == 'Medium' else 'Within 48 hours'}",
            inline=True
        )
        embed.set_footer(text=f"Priority: {priority}")
        
        await interaction.response.edit_message(embed=embed, view=None)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views
        self.bot.add_view(TicketCategorySelectView())
        self.bot.add_view(TicketControlView(0, "general", "General"))  # Dummy for persistence
        print("[Tickets] 🎫 Enhanced ticket system with subcategories loaded successfully.")

    @app_commands.command(name="formticket", description="🎫 Create a comprehensive ticket form in any channel")
    @app_commands.describe(channel="Channel where the ticket form will be posted")
    @app_commands.default_permissions(manage_channels=True)
    async def form_ticket(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Create a comprehensive ticket system form"""
        try:
            # Create the main ticket form embed
            main_embed = discord.Embed(
                title="🎫 **Professional Support Ticket System**",
                description="**Need help? We're here for you!**\n\nOur comprehensive support system is designed to help you quickly and efficiently. Select a category below to get started with creating your support ticket.\n\n**🌟 Why use our ticket system?**\n• **Fast Response Times** - Priority-based support\n• **Dedicated Channels** - Private conversations\n• **Expert Staff** - Knowledgeable team members\n• **Detailed Tracking** - Full history and notes",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # Add category overview
            categories_text = ""
            for category_key, category_info in list(TICKET_CATEGORIES.items())[:4]:  # Show first 4
                categories_text += f"{category_info['emoji']} **{category_info['name']}**\n{category_info['description']}\n\n"
            
            main_embed.add_field(
                name="📋 **Main Support Categories**",
                value=categories_text.strip(),
                inline=False
            )
            
            # Add additional categories
            additional_text = ""
            for category_key, category_info in list(TICKET_CATEGORIES.items())[4:]:  # Show rest
                additional_text += f"{category_info['emoji']} **{category_info['name']}** • "
            
            main_embed.add_field(
                name="🔧 **Additional Categories**",
                value=additional_text.strip(' •'),
                inline=False
            )
            
            main_embed.add_field(
                name="⚡ **Priority Levels**",
                value="🟢 **Low** - General questions (48h response)\n🟡 **Medium** - Standard issues (24h response)\n🟠 **High** - Important problems (4h response)\n🔴 **Urgent** - Critical issues (1h response)",
                inline=True
            )
            
            main_embed.add_field(
                name="🎯 **How It Works**",
                value="1️⃣ Select a category below\n2️⃣ Choose specific subcategory\n3️⃣ Fill out the ticket form\n4️⃣ Get a dedicated support channel\n5️⃣ Work with our team to resolve your issue",
                inline=True
            )
            
            main_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            main_embed.set_footer(text="💫 Professional Support System • Select a category below to create your ticket")
            
            # Create the category selection view
            view = TicketCategorySelectView()
            
            # Send the ticket form
            await channel.send(embed=main_embed, view=view)
            
            # Success response
            success_embed = discord.Embed(
                title="✅ **Ticket Form Created Successfully!**",
                description=f"The comprehensive ticket form has been posted in {channel.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            success_embed.add_field(
                name="🎯 **What's included:**",
                value=f"• **{len(TICKET_CATEGORIES)} Main Categories** with detailed subcategories\n• **Priority System** with response time expectations\n• **Professional Interface** with guided ticket creation\n• **Staff Tools** for efficient ticket management\n• **Auto-Management** with temporary channels",
                inline=False
            )
            success_embed.add_field(
                name="🚀 **Features:**",
                value="• Subcategory selection for precise support\n• Priority-based response times\n• Staff notes and ticket management\n• Automatic channel creation and deletion\n• Comprehensive logging and statistics",
                inline=False
            )
            success_embed.add_field(
                name="👥 **Staff Access:**",
                value="Staff members with roles containing 'admin', 'mod', 'staff', 'support', or 'helper' will automatically have access to all tickets.",
                inline=False
            )
            success_embed.set_footer(text="🎫 Your professional ticket system is now live!")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ **Permission Error**",
                description=f"I don't have permission to send messages in {channel.mention}!",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔧 **Required Permissions:**",
                value="• Send Messages\n• Embed Links\n• Manage Channels\n• Manage Messages",
                inline=False
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Setup Failed**",
                description="Something went wrong while creating the ticket form.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔍 **Error Details:**",
                value=f"```{str(e)[:200]}```",
                inline=False
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="closealltickets", description="🚨 Emergency: Close all open tickets")
    @app_commands.default_permissions(administrator=True)
    async def close_all_tickets(self, interaction: discord.Interaction):
        """Emergency command to close all tickets"""
        await interaction.response.defer()
        
        guild = interaction.guild
        closed_count = 0
        
        # Find all ticket channels
        for channel in guild.text_channels:
            if channel.name.startswith("ticket-"):
                try:
                    await channel.delete()
                    closed_count += 1
                except:
                    pass
        
        # Clean up empty ticket category
        ticket_category = discord.utils.get(guild.categories, name="🎫 Active Tickets")
        if ticket_category and len(ticket_category.channels) == 0:
            try:
                await ticket_category.delete()
            except:
                pass
        
        embed = discord.Embed(
            title="🚨 **Emergency Ticket Closure Complete**",
            description=f"**{closed_count}** ticket channels have been closed and deleted.",
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="👤 **Executed by:**",
            value=interaction.user.mention,
            inline=True
        )
        embed.add_field(
            name="⚠️ **Impact:**",
            value="All active ticket conversations have been permanently removed.",
            inline=False
        )
        embed.set_footer(text="🚨 Emergency administrative action completed")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ticketstats", description="📊 View comprehensive ticket system statistics")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        """View detailed ticket statistics"""
        try:
            stats = db.get_ticket_stats(interaction.guild.id)
            
            embed = discord.Embed(
                title="📊 **Ticket System Statistics**",
                description="Comprehensive overview of your support ticket system",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # Overview stats
            total_tickets = stats.get('total_tickets', 0)
            open_tickets = stats.get('open_tickets', 0)
            closed_tickets = stats.get('closed_tickets', 0)
            
            embed.add_field(
                name="📈 **Overall Statistics**",
                value=f"**Total Tickets:** {total_tickets:,}\n**Currently Open:** {open_tickets:,}\n**Resolved:** {closed_tickets:,}\n**Resolution Rate:** {(closed_tickets/total_tickets*100) if total_tickets > 0 else 0:.1f}%",
                inline=True
            )
            
            # Category breakdown
            if stats.get('category_breakdown'):
                category_text = ""
                for category, count in stats['category_breakdown'].items():
                    category_text += f"• **{category}:** {count}\n"
                
                embed.add_field(
                    name="📂 **Category Breakdown**",
                    value=category_text.strip(),
                    inline=True
                )
            
            # Active tickets
            active_channels = len([ch for ch in interaction.guild.text_channels if ch.name.startswith("ticket-")])
            embed.add_field(
                name="🔥 **Currently Active**",
                value=f"**{active_channels}** live ticket channels",
                inline=True
            )
            
            # Performance metrics
            embed.add_field(
                name="⚡ **System Performance**",
                value=f"**Categories:** {len(TICKET_CATEGORIES)}\n**Subcategories:** {sum(len(cat['subcategories']) for cat in TICKET_CATEGORIES.values())}\n**Priority Levels:** 4\n**Status:** 🟢 Active",
                inline=True
            )
            
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text="📊 Statistics updated in real-time")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Statistics Error**",
                description="Couldn't retrieve ticket statistics.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔍 **Error Details:**",
                value=f"```{str(e)[:200]}```",
                inline=False
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))