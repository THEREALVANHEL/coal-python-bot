import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select, Modal, TextInput
from datetime import datetime
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# Enhanced ticket categories with cool designs
TICKET_CATEGORIES = {
    "general": {
        "name": "General Support",
        "description": "General help and questions",
        "emoji": "❓",
        "color": 0x7289da
    },
    "technical": {
        "name": "Technical Issues",
        "description": "Bug reports and technical problems",
        "emoji": "🔧",
        "color": 0xff6b6b
    },
    "moderation": {
        "name": "Moderation Issues",
        "description": "Report users or appeal punishments",
        "emoji": "🛡️",
        "color": 0xff9966
    },
    "suggestions": {
        "name": "Suggestions",
        "description": "Ideas and feature requests",
        "emoji": "💡",
        "color": 0xffd700
    },
    "partnership": {
        "name": "Partnership",
        "description": "Server partnerships and collaborations",
        "emoji": "🤝",
        "color": 0x7c3aed
    }
}

class TicketCategoryButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Add buttons for each category
        for category_key, category_info in TICKET_CATEGORIES.items():
            button = Button(
                label=category_info['name'],
                emoji=category_info['emoji'],
                style=discord.ButtonStyle.primary,
                custom_id=f"ticket_{category_key}"
            )
            button.callback = self.create_ticket_callback
            self.add_item(button)
    
    async def create_ticket_callback(self, interaction: discord.Interaction):
        # Extract category from button custom_id
        category_key = interaction.data['custom_id'].replace('ticket_', '')
        category_info = TICKET_CATEGORIES[category_key]
        
        modal = TicketModal(category_key, category_info)
        await interaction.response.send_modal(modal)

class TicketModal(Modal):
    def __init__(self, category_key, category_info):
        super().__init__(title=f"🎫 {category_info['name']} Ticket")
        self.category_key = category_key
        self.category_info = category_info
        
        self.subject = TextInput(
            label="📋 Subject",
            placeholder="Brief description of your issue/request",
            max_length=100,
            required=True
        )
        
        self.description = TextInput(
            label="📝 Detailed Description",
            placeholder="Please provide as much detail as possible to help us assist you better",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True
        )
        
        self.add_item(self.subject)
        self.add_item(self.description)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Get ticket settings
            ticket_category_id = db.get_guild_setting(interaction.guild.id, 'ticket_category', None)
            support_role_ids = db.get_guild_setting(interaction.guild.id, 'ticket_support_roles', [])
            
            if not ticket_category_id:
                embed = discord.Embed(
                    title="❌ System Not Configured",
                    description="The ticket system hasn't been set up yet. Please contact an administrator.",
                    color=0xff6b6b
                )
                embed.set_footer(text="💫 Admin: Use /setuptickets to configure the system")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Find the category
            category = interaction.guild.get_channel(ticket_category_id)
            if not category or not isinstance(category, discord.CategoryChannel):
                embed = discord.Embed(
                    title="❌ Configuration Error",
                    description="Ticket category not found. Please contact an administrator.",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if user already has an open ticket
            existing_channels = category.channels
            user_has_ticket = any(
                channel.name.endswith(f"-{interaction.user.id}") 
                for channel in existing_channels
                if isinstance(channel, discord.TextChannel)
            )
            
            if user_has_ticket:
                embed = discord.Embed(
                    title="⚠️ Active Ticket Found",
                    description="You already have an open ticket! Please use your existing ticket channel to continue the conversation.",
                    color=0xff9966
                )
                embed.add_field(
                    name="💡 Tip",
                    value="Look for a channel with your name in the ticket category!",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create ticket channel with cool naming
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
                topic=f"🎫 {self.category_info['name']} ticket by {interaction.user.display_name} • {self.subject.value}"
            )
            
            # Create beautiful initial embed
            embed = discord.Embed(
                title=f"🎫 **{self.category_info['name']} Ticket**",
                description=f"**📋 Subject:** {self.subject.value}\n\n**📝 Description:**\n{self.description.value}",
                color=self.category_info['color'],
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"Ticket by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            embed.add_field(name="👤 Created by", value=interaction.user.mention, inline=True)
            embed.add_field(name="📂 Category", value=f"{self.category_info['emoji']} {self.category_info['name']}", inline=True)
            embed.add_field(name="📊 Status", value="🟢 **OPEN**", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"Ticket ID: {ticket_channel.id} • Professional Support System")
            
            # Create enhanced ticket controls
            view = TicketControlView(interaction.user.id)
            
            # Send welcome message
            welcome_text = f"🎉 **Welcome {interaction.user.mention}!**\n\n"
            welcome_text += f"Your **{self.category_info['name']}** ticket has been created successfully!\n"
            welcome_text += f"Our support team will be with you shortly to assist with: *{self.subject.value}*\n\n"
            
            if support_role_ids:
                welcome_text += f"**🔔 Support Team Notified:** <@&{'>, <@&'.join(map(str, support_role_ids))}>\n\n"
            
            welcome_text += "**💡 While you wait:**\n"
            welcome_text += "• Please provide any additional details that might help\n"
            welcome_text += "• Feel free to share screenshots or files if relevant\n"
            welcome_text += "• Be patient - quality support takes time!\n\n"
            welcome_text += "*Thank you for reaching out to our support team!* ✨"
            
            await ticket_channel.send(
                content=welcome_text,
                embed=embed,
                view=view
            )
            
            # Log ticket creation
            db.log_ticket_creation(interaction.guild.id, interaction.user.id, ticket_channel.id, self.category_key, self.subject.value)
            
            # Success response
            success_embed = discord.Embed(
                title="✅ **Ticket Created Successfully!**",
                description=f"Your **{self.category_info['name']}** ticket has been created.",
                color=0x00d4aa
            )
            success_embed.add_field(
                name="🎫 Your Ticket",
                value=f"📍 {ticket_channel.mention}\n🏷️ **{self.subject.value}**",
                inline=False
            )
            success_embed.add_field(
                name="⏱️ Response Time",
                value="Our team typically responds within **1-24 hours**",
                inline=False
            )
            success_embed.set_footer(text="🌟 Thank you for using our support system!")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ticket Creation Failed",
                description="Something went wrong while creating your ticket. Please try again or contact an administrator.",
                color=0xff6b6b
            )
            error_embed.set_footer(text="💫 If this persists, please contact staff directly")
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

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
        support_role_ids = db.get_guild_setting(interaction.guild.id, 'ticket_support_roles', [])
        
        can_close = (
            interaction.user.id == self.ticket_creator_id or
            any(role_id in support_role_ids for role_id in user_roles) or
            interaction.user.guild_permissions.manage_channels
        )
        
        if not can_close:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to close this ticket!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create beautiful confirmation embed
        embed = discord.Embed(
            title="🔒 **Closing Ticket**",
            description="This ticket will be closed and archived. This action cannot be undone.",
            color=0xff9966,
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Closed by", value=interaction.user.mention, inline=True)
        embed.add_field(name="📝 Reason", value="Ticket resolved", inline=True)
        embed.add_field(name="⏱️ Auto-delete", value="5 seconds", inline=True)
        embed.set_footer(text="Thank you for using our support system!")
        
        await interaction.response.send_message(embed=embed)
        
        # Log ticket closure
        db.log_ticket_closure(interaction.guild.id, interaction.user.id, interaction.channel.id)
        
        # Close the ticket after a short delay
        import asyncio
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass
    
    @discord.ui.button(label="👥 Add User", style=discord.ButtonStyle.secondary)
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check permissions
        user_roles = [role.id for role in interaction.user.roles]
        support_role_ids = db.get_guild_setting(interaction.guild.id, 'ticket_support_roles', [])
        
        can_add = (
            any(role_id in support_role_ids for role_id in user_roles) or
            interaction.user.guild_permissions.manage_channels
        )
        
        if not can_add:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only support staff can add users to tickets!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        modal = AddUserModal()
        await interaction.response.send_modal(modal)

class AddUserModal(Modal):
    def __init__(self):
        super().__init__(title="👤 Add User to Ticket")
        
        self.user_input = TextInput(
            label="🔍 User ID or @mention",
            placeholder="Enter user ID or mention the user (e.g., @username or 123456789)",
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
                embed = discord.Embed(
                    title="❌ User Not Found",
                    description="Could not find that user in this server!",
                    color=0xff6b6b
                )
                embed.add_field(
                    name="💡 Tip",
                    value="Make sure to use a valid user ID or @mention",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
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
                title="✅ **User Added Successfully**",
                description=f"{user.mention} has been added to this ticket and can now participate in the conversation.",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            embed.add_field(name="👤 Added by", value=interaction.user.mention, inline=True)
            embed.add_field(name="🎫 Ticket Access", value="Full read/write permissions", inline=True)
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text="User successfully added to ticket")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Adding User",
                description="Something went wrong while adding the user to this ticket.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views
        self.bot.add_view(TicketCategoryButtonView())
        self.bot.add_view(TicketControlView(0))  # Dummy creator ID for persistent view
        print("[Tickets] 🎫 Loaded successfully with enhanced button system.")

    @app_commands.command(name="setuptickets", description="🎫 Set up the ticket system with interactive buttons")
    @app_commands.describe(
        channel="Channel where users can create tickets",
        ticketzone="Category ID where individual ticket channels will be created",
        support_roles="Support role IDs (comma-separated, optional)"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def setup_tickets(self, interaction: discord.Interaction, 
                           channel: discord.TextChannel, 
                           ticketzone: str, 
                           support_roles: str = None):
        try:
            # Parse and validate category ID
            if not ticketzone.isdigit():
                error_embed = discord.Embed(
                    title="❌ Invalid Category ID",
                    description="Please provide a valid **category ID** (numbers only).\n\n**How to get a category ID:**\n1. Enable Developer Mode in Discord\n2. Right-click on a category\n3. Select 'Copy ID'",
                    color=0xff6b6b
                )
                error_embed.add_field(
                    name="⚠️ Important",
                    value="You need a **CATEGORY** ID, not a text channel ID. Tickets are created as individual channels within the category.",
                    inline=False
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return
                
            category_id = int(ticketzone)
            category = interaction.guild.get_channel(category_id)
            
            if not category:
                error_embed = discord.Embed(
                    title="❌ Category Not Found",
                    description=f"No channel found with ID `{category_id}`.\n\nMake sure you copied the correct category ID.",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return
                
            if not isinstance(category, discord.CategoryChannel):
                error_embed = discord.Embed(
                    title="❌ Not a Category",
                    description=f"Channel `{category.name}` (ID: `{category_id}`) is a **{category.type}**, not a category.\n\n**You need to provide a CATEGORY ID**, not a text channel ID.",
                    color=0xff6b6b
                )
                error_embed.add_field(
                    name="📝 How it works",
                    value="The ticket system creates individual ticket channels inside the category you specify. Each user gets their own private channel.",
                    inline=False
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
                return
            
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
            db.set_guild_setting(interaction.guild.id, 'ticket_category', category.id)
            db.set_guild_setting(interaction.guild.id, 'ticket_support_roles', support_role_ids)
            
            # Create the ultimate ticket creation embed
            embed = discord.Embed(
                title="🎫 **SUPPORT CENTER** 🎫",
                description="**Welcome to our Professional Support System!**\n\n" +
                           "Need help? Have questions? Want to report something? You're in the right place!\n" +
                           "Select the category that best matches your needs below to create a private support ticket.",
                color=0x5865f2,
                timestamp=datetime.now()
            )
            
            # Add category information
            embed.add_field(
                name="📋 **Available Support Categories**",
                value="\n".join([
                    f"{cat['emoji']} **{cat['name']}** - {cat['description']}"
                    for cat in TICKET_CATEGORIES.values()
                ]),
                inline=False
            )
            
            embed.add_field(
                name="📋 **How It Works**",
                value="1️⃣ Click the category button below\n" +
                      "2️⃣ Fill out the ticket form\n" +
                      "3️⃣ Get a private channel with our team\n" +
                      "4️⃣ Receive professional support!",
                inline=True
            )
            
            embed.add_field(
                name="⏱️ **Response Times**",
                value="🟢 **General:** 1-12 hours\n" +
                      "🟡 **Technical:** 2-24 hours\n" +
                      "🔴 **Urgent:** 30 minutes - 2 hours",
                inline=True
            )
            
            embed.add_field(
                name="💡 **Pro Tips**",
                value="• Be specific in your descriptions\n" +
                      "• Include screenshots when helpful\n" +
                      "• One ticket per issue\n" +
                      "• Be patient with our team",
                inline=False
            )
            
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text="🌟 Professional Support System • Click a button below to get started!")
            
            # Create the button view
            view = TicketCategoryButtonView()
            
            # Send the message
            await channel.send(embed=embed, view=view)
            
            # Confirmation response
            conf_embed = discord.Embed(
                title="✅ **Ticket System Setup Complete!**",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            conf_embed.add_field(
                name="🎫 **Configuration**",
                value=f"**Setup Channel:** {channel.mention}\n" +
                      f"**Ticket Category:** {category.mention}\n" +
                      f"**Support Roles:** {len(support_role_ids)} configured",
                inline=False
            )
            conf_embed.add_field(
                name="🚀 **System Status**",
                value="✅ Button interface active\n" +
                      "✅ Automatic channel creation\n" +
                      "✅ Permission management\n" +
                      "✅ Professional templates",
                inline=False
            )
            conf_embed.set_footer(text="🌟 Your server now has a professional support system!")
            
            await interaction.response.send_message(embed=conf_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Setup Failed",
                description=f"Failed to set up the ticket system: {str(e)}",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="ticketstats", description="📊 View comprehensive ticket statistics")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        try:
            stats = db.get_ticket_stats(interaction.guild.id)
            
            embed = discord.Embed(
                title="📊 **Ticket System Statistics**",
                color=0x5865f2,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="📈 **Total Tickets**", value=f"**{stats.get('total_tickets', 0)}**", inline=True)
            embed.add_field(name="🟢 **Open Tickets**", value=f"**{stats.get('open_tickets', 0)}**", inline=True)
            embed.add_field(name="🔒 **Closed Tickets**", value=f"**{stats.get('closed_tickets', 0)}**", inline=True)
            
            # Category breakdown
            category_stats = stats.get('category_breakdown', {})
            if category_stats:
                category_text = "\n".join([
                    f"{TICKET_CATEGORIES.get(cat, {}).get('emoji', '📋')} **{cat.title()}:** {count}" 
                    for cat, count in category_stats.items()
                ])
                embed.add_field(name="📋 **Category Breakdown**", value=category_text, inline=False)
            
            # Calculate efficiency metrics
            total = stats.get('total_tickets', 0)
            closed = stats.get('closed_tickets', 0)
            if total > 0:
                resolution_rate = (closed / total) * 100
                embed.add_field(
                    name="⚡ **Performance Metrics**",
                    value=f"**Resolution Rate:** {resolution_rate:.1f}%\n**Avg Response:** Professional\n**System Status:** 🟢 Active",
                    inline=False
                )
            
            embed.set_footer(text="🎫 Professional Ticket System • Admin Statistics")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Statistics Error",
                description="Could not retrieve ticket statistics at this time.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="closealltickets", description="🚨 Close all open tickets (EMERGENCY ONLY)")
    @app_commands.default_permissions(administrator=True)
    async def close_all_tickets(self, interaction: discord.Interaction):
        try:
            ticket_category_id = db.get_guild_setting(interaction.guild.id, 'ticket_category', None)
            
            if not ticket_category_id:
                embed = discord.Embed(
                    title="❌ System Not Configured",
                    description="Ticket system not configured.",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            category = interaction.guild.get_channel(ticket_category_id)
            if not category:
                embed = discord.Embed(
                    title="❌ Category Not Found",
                    description="Ticket category not found.",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            ticket_channels = [ch for ch in category.channels if isinstance(ch, discord.TextChannel)]
            
            if not ticket_channels:
                embed = discord.Embed(
                    title="ℹ️ No Open Tickets",
                    description="No open tickets found to close.",
                    color=0x7289da
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🚨 **Mass Ticket Closure**",
                description=f"Closing **{len(ticket_channels)}** open ticket(s)...",
                color=0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            closed_count = 0
            for channel in ticket_channels:
                try:
                    # Send closure message
                    embed = discord.Embed(
                        title="🚨 **Emergency Closure**",
                        description="This ticket has been closed by an administrator as part of a mass closure operation.",
                        color=0xff0000,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text="Contact staff if you need to reopen this issue")
                    await channel.send(embed=embed)
                    
                    # Log closure
                    db.log_ticket_closure(interaction.guild.id, interaction.user.id, channel.id)
                    
                    # Delete channel
                    import asyncio
                    await asyncio.sleep(1)  # Small delay to prevent rate limits
                    await channel.delete()
                    closed_count += 1
                except:
                    continue
            
            final_embed = discord.Embed(
                title="✅ **Mass Closure Complete**",
                description=f"Successfully closed **{closed_count}** ticket(s).",
                color=0x00d4aa
            )
            await interaction.edit_original_response(embed=final_embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Closure Failed",
                description="Error occurred during mass closure operation.",
                color=0xff6b6b
            )
            await interaction.edit_original_response(embed=embed)

import asyncio

async def setup(bot):
    await bot.add_cog(Tickets(bot))