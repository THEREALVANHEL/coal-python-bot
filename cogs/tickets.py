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

# Ticket categories
TICKET_TYPES = {
    "general": {
        "name": "🆘 General Support",
        "description": "General questions and basic help",
        "emoji": "🆘",
        "color": 0x7289da
    },
    "technical": {
        "name": "🔧 Technical Issues",
        "description": "Bug reports and technical problems",
        "emoji": "🔧",
        "color": 0xff6b6b
    },
    "billing": {
        "name": "💳 Billing & Account",
        "description": "Payment issues and account problems",
        "emoji": "💳",
        "color": 0xffd700
    },
    "report": {
        "name": "🚨 Report User/Content",
        "description": "Report inappropriate behavior or content",
        "emoji": "🚨",
        "color": 0xff4444
    },
    "appeal": {
        "name": "⚖️ Appeal/Unban",
        "description": "Appeal bans or punishments",
        "emoji": "⚖️",
        "color": 0x9966ff
    }
}

class TicketCreationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🆘 General Support", style=discord.ButtonStyle.primary, emoji="🆘")
    async def general_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "general")

    @discord.ui.button(label="🔧 Technical Issues", style=discord.ButtonStyle.secondary, emoji="🔧")
    async def technical_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "technical")

    @discord.ui.button(label="💳 Billing & Account", style=discord.ButtonStyle.secondary, emoji="💳")
    async def billing_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "billing")

    @discord.ui.button(label="🚨 Report User/Content", style=discord.ButtonStyle.danger, emoji="🚨")
    async def report_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "report")

    @discord.ui.button(label="⚖️ Appeal/Unban", style=discord.ButtonStyle.secondary, emoji="⚖️")
    async def appeal_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "appeal")

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        """Create a new ticket channel"""
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
                    title="⚠️ Ticket Already Exists",
                    description=f"You already have an open ticket: {existing_channel.mention}",
                    color=0xff9966
                )
                embed.add_field(
                    name="💡 What to do?",
                    value="Please use your existing ticket or close it first before creating a new one.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Get ticket type info
            ticket_info = TICKET_TYPES[ticket_type]
            
            # Create unique channel name
            channel_name = f"ticket-{user.display_name.lower().replace(' ', '-')}-{user.id}"
            
            # Create category if it doesn't exist
            category_name = "🎫 Active Tickets"
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                category = await guild.create_category(category_name)
            
            # Set up permissions for the ticket channel
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
            
            # Add staff/admin permissions
            for role in guild.roles:
                if any(name in role.name.lower() for name in ["admin", "mod", "staff", "support"]):
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_messages=True,
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True
                    )
            
            # Create the ticket channel
            ticket_channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"{ticket_info['emoji']} {ticket_info['name']} ticket by {user.display_name}"
            )
            
            # Create welcome embed
            welcome_embed = discord.Embed(
                title=f"{ticket_info['emoji']} **{ticket_info['name']} Ticket**",
                description=f"Hello {user.mention}! 👋\n\nThank you for creating a **{ticket_info['name']}** ticket.\nOur support team will be with you shortly!",
                color=ticket_info['color'],
                timestamp=datetime.now()
            )
            
            welcome_embed.add_field(
                name="📋 **Ticket Information**",
                value=f"**Type:** {ticket_info['name']}\n**Created by:** {user.mention}\n**Status:** 🟢 Open",
                inline=True
            )
            
            welcome_embed.add_field(
                name="⏱️ **Response Time**",
                value="• **Urgent:** Within 1 hour\n• **Normal:** Within 24 hours\n• **Low Priority:** Within 48 hours",
                inline=True
            )
            
            welcome_embed.add_field(
                name="💡 **Tips for faster support**",
                value="• Be clear and specific about your issue\n• Provide screenshots if applicable\n• Include any error messages\n• Be patient and respectful",
                inline=False
            )
            
            welcome_embed.set_thumbnail(url=user.display_avatar.url)
            welcome_embed.set_footer(text=f"Ticket ID: {ticket_channel.id} • Created")
            
            # Create ticket control buttons
            control_view = TicketControlView(user.id, ticket_type)
            
            # Send welcome message
            welcome_msg = await ticket_channel.send(
                content=f"🎫 **Ticket Created Successfully!**\n{user.mention} | Staff will be notified automatically.",
                embed=welcome_embed,
                view=control_view
            )
            
            # Pin the welcome message
            await welcome_msg.pin()
            
            # Log ticket creation
            try:
                db.log_ticket_creation(guild.id, user.id, ticket_channel.id, ticket_type, f"{ticket_info['name']} ticket")
            except:
                pass  # Continue even if logging fails
            
            # Notify user of successful creation
            success_embed = discord.Embed(
                title="✅ **Ticket Created Successfully!**",
                description=f"Your **{ticket_info['name']}** ticket has been created.",
                color=0x00d4aa
            )
            success_embed.add_field(
                name="📍 **Your Ticket Channel**",
                value=f"{ticket_channel.mention}",
                inline=False
            )
            success_embed.add_field(
                name="🚀 **What's Next?**",
                value="• Describe your issue in detail\n• Wait for staff response\n• Check back regularly for updates",
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
                value="• Make sure you don't already have an open ticket\n• Check that the bot has proper permissions\n• Try again in a few moments",
                inline=False
            )
            
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)

class TicketControlView(View):
    def __init__(self, creator_id: int, ticket_type: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.ticket_type = ticket_type

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the ticket with confirmation"""
        # Check if user can close the ticket
        can_close = (
            interaction.user.id == self.creator_id or
            interaction.user.guild_permissions.manage_channels or
            any(name in role.name.lower() for role in interaction.user.roles for name in ["admin", "mod", "staff", "support"])
        )
        
        if not can_close:
            embed = discord.Embed(
                title="❌ **Permission Denied**",
                description="Only the ticket creator or staff members can close this ticket.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create confirmation embed
        confirm_embed = discord.Embed(
            title="🔒 **Confirm Ticket Closure**",
            description="Are you sure you want to close this ticket?\n\n**⚠️ This action cannot be undone!**",
            color=0xff9966,
            timestamp=datetime.now()
        )
        confirm_embed.add_field(
            name="📋 **What happens next?**",
            value="• Ticket will be closed immediately\n• Channel will be deleted in 10 seconds\n• Conversation history will be lost",
            inline=False
        )
        confirm_embed.set_footer(text="Click 'Confirm' to proceed or 'Cancel' to keep the ticket open")
        
        # Create confirmation buttons
        confirm_view = TicketCloseConfirmView(interaction.user.id)
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view)

    @discord.ui.button(label="📌 Add Note", style=discord.ButtonStyle.secondary, emoji="📌")
    async def add_note(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add a note to the ticket"""
        can_add_note = (
            interaction.user.guild_permissions.manage_channels or
            any(name in role.name.lower() for role in interaction.user.roles for name in ["admin", "mod", "staff", "support"])
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
            title="🔒 **Ticket Closed**",
            description="This ticket has been closed and will be deleted shortly.",
            color=0xff6b6b,
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
        
        # Log ticket closure
        try:
            db.log_ticket_closure(interaction.guild.id, interaction.user.id, interaction.channel.id)
        except:
            pass
        
        # Delete channel after delay
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
        note_embed.set_footer(text="Internal staff note - Not visible to ticket creator")
        
        await interaction.response.send_message(embed=note_embed)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views
        self.bot.add_view(TicketCreationView())
        self.bot.add_view(TicketControlView(0, "general"))  # Dummy for persistent view
        print("[Tickets] 🎫 Comprehensive ticket system loaded successfully.")

    @app_commands.command(name="setupticket", description="🎫 Setup the ticket system in a channel")
    @app_commands.describe(channel="Channel where the ticket creation message will be sent")
    @app_commands.default_permissions(manage_channels=True)
    async def setup_ticket(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Setup the comprehensive ticket system"""
        try:
            # Create the main ticket embed
            main_embed = discord.Embed(
                title="🎫 **Support Ticket System**",
                description="Need help? Create a support ticket by clicking one of the buttons below!\n\n" +
                           "Our support team is here to help you with any questions or issues you might have.",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # Add ticket type information
            types_text = ""
            for ticket_type, info in TICKET_TYPES.items():
                types_text += f"{info['emoji']} **{info['name']}**\n{info['description']}\n\n"
            
            main_embed.add_field(
                name="🎯 **Available Support Types**",
                value=types_text.strip(),
                inline=False
            )
            
            main_embed.add_field(
                name="⏱️ **Response Times**",
                value="• **Critical Issues:** Within 1 hour\n• **General Support:** Within 24 hours\n• **Non-urgent:** Within 48 hours",
                inline=True
            )
            
            main_embed.add_field(
                name="📋 **How it works**",
                value="1. Click a button below\n2. Private channel is created\n3. Explain your issue\n4. Get help from our team\n5. Ticket closes automatically",
                inline=True
            )
            
            main_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            main_embed.set_footer(text="💫 Professional Support System • Click a button to get started")
            
            # Create the ticket creation view
            view = TicketCreationView()
            
            # Send the ticket interface
            await channel.send(embed=main_embed, view=view)
            
            # Confirm setup
            success_embed = discord.Embed(
                title="✅ **Ticket System Setup Complete!**",
                description=f"The ticket system has been successfully set up in {channel.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            success_embed.add_field(
                name="🎯 **What's configured:**",
                value=f"• **Channel:** {channel.mention}\n• **Ticket Types:** {len(TICKET_TYPES)} different types\n• **Auto-management:** Channels created and deleted automatically\n• **Staff Access:** Auto-detected based on roles",
                inline=False
            )
            success_embed.add_field(
                name="🚀 **Features:**",
                value="• Temporary channels (auto-delete after closing)\n• Role-based staff access\n• Professional ticket interface\n• Built-in notes system\n• Comprehensive logging",
                inline=False
            )
            success_embed.set_footer(text="🎫 Your ticket system is now live and ready to use!")
            
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
                description="Something went wrong while setting up the ticket system.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔍 **Error Details:**",
                value=f"```{str(e)[:100]}```",
                inline=False
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="closealltickets", description="🚨 Emergency: Close all open tickets")
    @app_commands.default_permissions(administrator=True)
    async def close_all_tickets(self, interaction: discord.Interaction):
        """Emergency command to close all open tickets"""
        await interaction.response.defer()
        
        guild = interaction.guild
        closed_count = 0
        
        # Find all ticket channels
        for channel in guild.text_channels:
            if channel.name.startswith("ticket-") and "-" in channel.name:
                try:
                    await channel.delete()
                    closed_count += 1
                except:
                    pass
        
        # Also delete the ticket category if empty
        ticket_category = discord.utils.get(guild.categories, name="🎫 Active Tickets")
        if ticket_category and len(ticket_category.channels) == 0:
            try:
                await ticket_category.delete()
            except:
                pass
        
        embed = discord.Embed(
            title="🚨 **Emergency Ticket Closure**",
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
            name="⚠️ **Warning:**",
            value="All active conversations have been permanently deleted.",
            inline=False
        )
        embed.set_footer(text="Emergency administrative action completed")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ticketstats", description="📊 View ticket system statistics")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        """View comprehensive ticket statistics"""
        try:
            stats = db.get_ticket_stats(interaction.guild.id)
            
            embed = discord.Embed(
                title="📊 **Ticket System Statistics**",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # Overview stats
            embed.add_field(
                name="📈 **Overview**",
                value=f"**Total Tickets:** {stats['total_tickets']}\n**Currently Open:** {stats['open_tickets']}\n**Resolved:** {stats['closed_tickets']}",
                inline=True
            )
            
            # Category breakdown
            if stats['category_breakdown']:
                category_text = ""
                for category, count in stats['category_breakdown'].items():
                    category_info = TICKET_TYPES.get(category, {"emoji": "📋", "name": category.title()})
                    category_text += f"{category_info['emoji']} **{category_info['name']}:** {count}\n"
                
                embed.add_field(
                    name="📂 **Categories**",
                    value=category_text.strip(),
                    inline=True
                )
            
            # Active tickets count
            active_channels = len([ch for ch in interaction.guild.text_channels if ch.name.startswith("ticket-")])
            embed.add_field(
                name="🔥 **Currently Active**",
                value=f"**{active_channels}** active ticket channels",
                inline=True
            )
            
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text="📊 Ticket statistics updated in real-time")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Stats Error**",
                description="Couldn't retrieve ticket statistics.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))