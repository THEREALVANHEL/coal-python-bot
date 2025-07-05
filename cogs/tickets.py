import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select, Modal, TextInput
from datetime import datetime
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# Default ticket categories
TICKET_CATEGORIES = {
    "general": {
        "name": "General Support",
        "description": "General help and questions",
        "emoji": "❓"
    },
    "technical": {
        "name": "Technical Issues",
        "description": "Bug reports and technical problems",
        "emoji": "🔧"
    },
    "moderation": {
        "name": "Moderation Issues",
        "description": "Report users or appeal punishments",
        "emoji": "🛡️"
    },
    "suggestions": {
        "name": "Suggestions",
        "description": "Ideas and feature requests",
        "emoji": "💡"
    },
    "partnership": {
        "name": "Partnership",
        "description": "Server partnerships and collaborations",
        "emoji": "🤝"
    }
}

class TicketModal(Modal):
    def __init__(self, category_key, category_info):
        super().__init__(title=f"Create {category_info['name']} Ticket")
        self.category_key = category_key
        self.category_info = category_info
        
        self.subject = TextInput(
            label="Subject",
            placeholder="Brief description of your issue/request",
            max_length=100,
            required=True
        )
        
        self.description = TextInput(
            label="Description",
            placeholder="Detailed explanation of your issue/request",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        
        self.add_item(self.subject)
        self.add_item(self.description)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Get ticket settings
            settings = db.get_server_settings(interaction.guild.id)
            ticket_category_id = settings.get('ticket_category', None)
            support_role_ids = settings.get('ticket_support_roles', [])
            
            if not ticket_category_id:
                await interaction.response.send_message("❌ Ticket system not configured. Please contact an admin.", ephemeral=True)
                return
            
            # Find the category
            category = interaction.guild.get_channel(ticket_category_id)
            if not category or not isinstance(category, discord.CategoryChannel):
                await interaction.response.send_message("❌ Ticket category not found. Please contact an admin.", ephemeral=True)
                return
            
            # Check if user already has an open ticket
            existing_channels = category.channels
            user_has_ticket = any(
                channel.name.endswith(f"-{interaction.user.id}") 
                for channel in existing_channels
                if isinstance(channel, discord.TextChannel)
            )
            
            if user_has_ticket:
                await interaction.response.send_message("❌ You already have an open ticket! Please use your existing ticket channel.", ephemeral=True)
                return
            
            # Create ticket channel
            channel_name = f"{self.category_key}-{interaction.user.display_name.lower().replace(' ', '-')}-{interaction.user.id}"
            
            # Set up permissions
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                )
            }
            
            # Add support roles
            for role_id in support_role_ids:
                role = interaction.guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True
                    )
            
            # Create the channel
            ticket_channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"{self.category_info['name']} ticket by {interaction.user.display_name}"
            )
            
            # Create initial embed
            embed = discord.Embed(
                title=f"{self.category_info['emoji']} {self.category_info['name']} Ticket",
                description=f"**Subject:** {self.subject.value}\n\n**Description:**\n{self.description.value}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="Created by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Category", value=self.category_info['name'], inline=True)
            embed.add_field(name="Status", value="🟢 Open", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"Ticket ID: {ticket_channel.id}")
            
            # Create ticket controls
            view = TicketControlView(interaction.user.id)
            
            # Send initial message
            await ticket_channel.send(
                content=f"👋 Welcome {interaction.user.mention}!\n\nYour ticket has been created. Our support team will be with you shortly.\n" +
                        (f"<@&{'>, <@&'.join(map(str, support_role_ids))}>" if support_role_ids else ""),
                embed=embed,
                view=view
            )
            
            # Log ticket creation
            db.log_ticket_creation(interaction.guild.id, interaction.user.id, ticket_channel.id, self.category_key, self.subject.value)
            
            await interaction.response.send_message(f"✅ Ticket created! Please check {ticket_channel.mention}", ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating ticket: {str(e)}", ephemeral=True)

class TicketCategorySelect(Select):
    def __init__(self):
        options = []
        for key, category in TICKET_CATEGORIES.items():
            options.append(
                discord.SelectOption(
                    label=category['name'],
                    description=category['description'],
                    emoji=category['emoji'],
                    value=key
                )
            )
        
        super().__init__(
            placeholder="Choose your ticket category...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        category_key = self.values[0]
        category_info = TICKET_CATEGORIES[category_key]
        
        modal = TicketModal(category_key, category_info)
        await interaction.response.send_modal(modal)

class TicketCreateView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())
    
    @discord.ui.button(label="📞 Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # This will show the dropdown
        await interaction.response.send_message("Please select a category for your ticket:", view=View().add_item(TicketCategorySelect()), ephemeral=True)

class TicketControlView(View):
    def __init__(self, ticket_creator_id):
        super().__init__(timeout=None)
        self.ticket_creator_id = ticket_creator_id
    
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check permissions
        user_roles = [role.id for role in interaction.user.roles]
        settings = db.get_server_settings(interaction.guild.id)
        support_role_ids = settings.get('ticket_support_roles', [])
        
        can_close = (
            interaction.user.id == self.ticket_creator_id or
            any(role_id in support_role_ids for role_id in user_roles) or
            interaction.user.guild_permissions.manage_channels
        )
        
        if not can_close:
            await interaction.response.send_message("❌ You don't have permission to close this ticket!", ephemeral=True)
            return
        
        # Create confirmation embed
        embed = discord.Embed(
            title="🔒 Closing Ticket",
            description="This ticket will be closed and archived. This action cannot be undone.",
            color=0xff9900,
            timestamp=datetime.now()
        )
        embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reason", value="Ticket resolved", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Log ticket closure
        db.log_ticket_closure(interaction.guild.id, interaction.user.id, interaction.channel.id)
        
        # Close the ticket after a short delay
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass
    
    @discord.ui.button(label="📋 Add User", style=discord.ButtonStyle.secondary)
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check permissions
        user_roles = [role.id for role in interaction.user.roles]
        settings = db.get_server_settings(interaction.guild.id)
        support_role_ids = settings.get('ticket_support_roles', [])
        
        can_add = (
            any(role_id in support_role_ids for role_id in user_roles) or
            interaction.user.guild_permissions.manage_channels
        )
        
        if not can_add:
            await interaction.response.send_message("❌ Only support staff can add users to tickets!", ephemeral=True)
            return
        
        modal = AddUserModal()
        await interaction.response.send_modal(modal)

class AddUserModal(Modal):
    def __init__(self):
        super().__init__(title="Add User to Ticket")
        
        self.user_input = TextInput(
            label="User ID or @mention",
            placeholder="Enter user ID or mention the user",
            max_length=100,
            required=True
        )
        
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_str = self.user_input.value.strip()
            
            # Try to get user by ID
            if user_str.isdigit():
                user = interaction.guild.get_member(int(user_str))
            else:
                # Try to get user by mention
                user_id = user_str.replace('<@', '').replace('>', '').replace('!', '')
                if user_id.isdigit():
                    user = interaction.guild.get_member(int(user_id))
                else:
                    user = None
            
            if not user:
                await interaction.response.send_message("❌ User not found!", ephemeral=True)
                return
            
            # Add user to channel
            await interaction.channel.set_permissions(
                user,
                read_messages=True,
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True
            )
            
            embed = discord.Embed(
                title="👤 User Added",
                description=f"{user.mention} has been added to this ticket.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.add_field(name="Added by", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding user: {str(e)}", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views
        self.bot.add_view(TicketCreateView())
        self.bot.add_view(TicketControlView(0))  # Dummy creator ID for persistent view
        print("[Tickets] Loaded successfully with persistent views.")

    @app_commands.command(name="setticketchannel", description="Set up the ticket system in a channel")
    @app_commands.describe(
        channel="Channel to set up ticket creation",
        category="Category for ticket channels",
        support_roles="Support role IDs (comma-separated)"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def setup_ticket_channel(self, interaction: discord.Interaction, channel: discord.TextChannel, 
                                  category: discord.CategoryChannel, support_roles: str = None):
        try:
            # Parse support roles
            support_role_ids = []
            if support_roles:
                for role_id_str in support_roles.split(','):
                    role_id_str = role_id_str.strip()
                    if role_id_str.isdigit():
                        role_id = int(role_id_str)
                        role = interaction.guild.get_role(role_id)
                        if role:
                            support_role_ids.append(role_id)
            
            # Save settings
            db.update_server_setting(interaction.guild.id, 'ticket_category', category.id)
            db.update_server_setting(interaction.guild.id, 'ticket_support_roles', support_role_ids)
            
            # Create ticket creation embed
            embed = discord.Embed(
                title="🎫 Create a Support Ticket",
                description="Need help? Click the button below to create a support ticket!\n\n" +
                           "**Available Categories:**\n" +
                           "\n".join([f"{cat['emoji']} **{cat['name']}** - {cat['description']}" 
                                    for cat in TICKET_CATEGORIES.values()]),
                color=0x5865f2
            )
            embed.add_field(
                name="📋 How it works",
                value="1️⃣ Click 'Create Ticket'\n2️⃣ Select your category\n3️⃣ Fill out the form\n4️⃣ Wait for support!",
                inline=False
            )
            embed.set_footer(text="Our support team will respond as soon as possible!")
            
            # Send setup message
            view = TicketCreateView()
            await channel.send(embed=embed, view=view)
            
            # Confirmation
            conf_embed = discord.Embed(
                title="✅ Ticket System Configured",
                description=f"**Channel:** {channel.mention}\n**Category:** {category.mention}\n**Support Roles:** {len(support_role_ids)} roles",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=conf_embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting up ticket system: {str(e)}", ephemeral=True)

    @app_commands.command(name="ticketstats", description="View ticket statistics")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        try:
            stats = db.get_ticket_stats(interaction.guild.id)
            
            embed = discord.Embed(
                title="📊 Ticket Statistics",
                color=0x5865f2,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="📈 Total Tickets", value=str(stats.get('total_tickets', 0)), inline=True)
            embed.add_field(name="🟢 Open Tickets", value=str(stats.get('open_tickets', 0)), inline=True)
            embed.add_field(name="🔒 Closed Tickets", value=str(stats.get('closed_tickets', 0)), inline=True)
            
            # Category breakdown
            category_stats = stats.get('category_breakdown', {})
            if category_stats:
                category_text = "\n".join([f"{TICKET_CATEGORIES.get(cat, {}).get('emoji', '📋')} {cat.title()}: {count}" 
                                         for cat, count in category_stats.items()])
                embed.add_field(name="📋 Categories", value=category_text, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error getting ticket stats: {str(e)}", ephemeral=True)

    @app_commands.command(name="closealltickets", description="Close all open tickets (ADMIN ONLY)")
    @app_commands.default_permissions(administrator=True)
    async def close_all_tickets(self, interaction: discord.Interaction):
        try:
            settings = db.get_server_settings(interaction.guild.id)
            ticket_category_id = settings.get('ticket_category', None)
            
            if not ticket_category_id:
                await interaction.response.send_message("❌ Ticket system not configured.", ephemeral=True)
                return
            
            category = interaction.guild.get_channel(ticket_category_id)
            if not category:
                await interaction.response.send_message("❌ Ticket category not found.", ephemeral=True)
                return
            
            ticket_channels = [ch for ch in category.channels if isinstance(ch, discord.TextChannel)]
            
            if not ticket_channels:
                await interaction.response.send_message("❌ No open tickets found.", ephemeral=True)
                return
            
            await interaction.response.send_message(f"🔒 Closing {len(ticket_channels)} ticket(s)...", ephemeral=True)
            
            closed_count = 0
            for channel in ticket_channels:
                try:
                    # Send closure message
                    embed = discord.Embed(
                        title="🔒 Ticket Closed by Admin",
                        description="This ticket has been closed by an administrator.",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                    await channel.send(embed=embed)
                    
                    # Log closure
                    db.log_ticket_closure(interaction.guild.id, interaction.user.id, channel.id)
                    
                    # Delete channel
                    await channel.delete()
                    closed_count += 1
                except:
                    continue
            
            await interaction.edit_original_response(content=f"✅ Successfully closed {closed_count} ticket(s).")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error closing tickets: {str(e)}", ephemeral=True)

import asyncio

async def setup(bot):
    await bot.add_cog(Tickets(bot))