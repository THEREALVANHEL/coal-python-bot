import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput, Select
import asyncio
import json
from datetime import datetime, timedelta
import database as db

class ExpeditionTickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ticket_category_id = None  # Set this to your ticket category ID
        self.support_role_id = None  # Set this to your support role ID
        self.log_channel_id = None  # Set this to your log channel ID
        
        # Ticket configuration
        self.ticket_types = {
            "player_report": {
                "name": "🛡️ Player Report",
                "description": "Report other players for using third-party software (exploits) to gain unfair advantage",
                "color": 0xff0000,
                "emoji": "🛡️",
                "requirements": "Please provide clear evidence, preferably a video file, when reporting another player for using third-party software (exploits). Players that are banned for cheating cannot appeal, unless their innocence is proven."
            },
            "bug_report": {
                "name": "🐛 Bug Report",
                "description": "Report bugs that need immediate attention from developers",
                "color": 0xff6b6b,
                "emoji": "🐛",
                "requirements": "Include as much detail as possible (device type, steps to reproduce the issue and any error messages) when reporting a bug."
            },
            "suggestion": {
                "name": "💡 Suggestion",
                "description": "Suggest improvements or new features",
                "color": 0x4ecdc4,
                "emoji": "💡",
                "requirements": "Provide detailed explanation of your suggestion and how it would benefit the community."
            },
            "appeal": {
                "name": "⚖️ Appeal",
                "description": "Appeal a ban or punishment",
                "color": 0xffa500,
                "emoji": "⚖️",
                "requirements": "Explain why you believe the punishment was unjustified. Provide any evidence to support your appeal."
            },
            "general": {
                "name": "❓ General Support",
                "description": "General questions or support",
                "color": 0x9b59b6,
                "emoji": "❓",
                "requirements": "Ask your question clearly and provide any relevant context to help us assist you better."
            }
        }

    @app_commands.command(name="expeditionpanel", description="🎫 Create the EXPEDITION ticket panel")
    @app_commands.default_permissions(administrator=True)
    async def create_ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 EXPEDITION Antarctica - Support Tickets",
            description="Welcome to the EXPEDITION Antarctica support system!\n\n"
                       "**Choose the appropriate ticket type below:**\n"
                       "• 🛡️ **Player Report** - Report players using exploits/third-party software\n"
                       "• 🐛 **Bug Report** - Report bugs needing immediate developer attention\n"
                       "• 💡 **Suggestion** - Suggest improvements or new features\n"
                       "• ⚖️ **Appeal** - Appeal bans or punishments\n"
                       "• ❓ **General Support** - General questions or support\n\n"
                       "**📋 Important Guidelines:**\n"
                       "• **Player Reports**: Provide clear evidence, preferably video files\n"
                       "• **Bug Reports**: Include device type, steps to reproduce, and error messages\n"
                       "• **Cheating Bans**: Cannot be appealed unless innocence is proven\n"
                       "• Be respectful and patient with support staff\n"
                       "• One ticket per issue",
            color=0x4ecdc4
        )
        
        embed.add_field(
            name="🔒 Privacy",
            value="All ticket information is kept confidential and only visible to support staff.",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Response Time",
            value="Support staff will respond within 24 hours during business days.",
            inline=False
        )
        
        embed.set_footer(text="EXPEDITION Antarctica • Support System")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        # Create ticket selection view
        view = TicketSelectionView(self)
        await interaction.response.send_message(embed=embed, view=view)

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        """Create a new support ticket"""
        try:
            user = interaction.user
            ticket_info = self.ticket_types[ticket_type]
            
            # Check if user already has an open ticket
            existing_ticket = await self.get_user_open_ticket(user.id)
            if existing_ticket:
                embed = discord.Embed(
                    title="❌ Ticket Already Exists",
                    description=f"You already have an open ticket: {existing_ticket.mention}\n\nPlease use your existing ticket or close it first.",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get ticket category
            category = None
            if self.ticket_category_id:
                category = interaction.guild.get_channel(self.ticket_category_id)
            
            # Create ticket channel
            channel_name = f"ticket-{ticket_type}-{user.name.lower()}"
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }
            
            # Add support role permissions
            if self.support_role_id:
                support_role = interaction.guild.get_role(self.support_role_id)
                if support_role:
                    overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
            
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Support ticket for {user.mention} - Type: {ticket_info['name']}"
            )
            
            # Create ticket embed
            embed = discord.Embed(
                title=f"{ticket_info['emoji']} {ticket_info['name']}",
                description=f"Welcome {user.mention} to your support ticket!\n\n"
                           f"**Ticket Type:** {ticket_info['name']}\n"
                           f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                           f"**User:** {user.mention} ({user.id})\n\n"
                           f"**📋 Requirements:**\n"
                           f"{ticket_info.get('requirements', 'Please provide detailed information about your issue.')}\n\n"
                           f"**Please provide:**\n"
                           f"• Detailed description of your issue\n"
                           f"• Any relevant evidence (screenshots, logs, videos)\n"
                           f"• Steps to reproduce (if applicable)\n"
                           f"• What you've already tried (if applicable)\n\n"
                           f"Support staff will assist you as soon as possible.",
                color=ticket_info['color']
            )
            
            embed.add_field(
                name="📋 Ticket Guidelines",
                value="• Be clear and specific\n"
                      "• Provide evidence when possible\n"
                      "• Stay respectful and patient\n"
                      "• Don't spam or ping staff repeatedly",
                inline=False
            )
            
            embed.set_footer(text=f"Ticket ID: {ticket_channel.id} • EXPEDITION Antarctica")
            
            # Create ticket management buttons
            view = TicketManagementView(self, ticket_channel, user)
            
            await ticket_channel.send(embed=embed, view=view)
            
            # Send confirmation to user
            confirm_embed = discord.Embed(
                title="✅ Ticket Created Successfully!",
                description=f"Your ticket has been created: {ticket_channel.mention}\n\n"
                           f"**Ticket Type:** {ticket_info['name']}\n"
                           f"**Channel:** {ticket_channel.mention}\n\n"
                           f"Please provide detailed information about your issue in the ticket channel.",
                color=0x00ff00
            )
            
            await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
            
            # Log ticket creation
            await self.log_ticket_action("created", ticket_channel, user, ticket_type)
            
            # Save ticket to database
            await self.save_ticket_data(ticket_channel.id, user.id, ticket_type, "open")
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ticket Creation Failed",
                description=f"An error occurred while creating your ticket: {str(e)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    async def close_ticket(self, channel: discord.TextChannel, user: discord.Member, reason: str = "No reason provided"):
        """Close a support ticket"""
        try:
            # Update ticket status in database
            await self.save_ticket_data(channel.id, user.id, "unknown", "closed", reason)
            
            # Create closing embed
            embed = discord.Embed(
                title="🔒 Ticket Closed",
                description=f"This ticket has been closed by {user.mention}",
                color=0xff6b6b
            )
            
            if reason and reason != "No reason provided":
                embed.add_field(
                    name="📝 Reason",
                    value=reason,
                    inline=False
                )
            
            embed.add_field(
                name="📊 Ticket Summary",
                value=f"**Channel:** {channel.mention}\n"
                      f"**Closed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                      f"**Closed by:** {user.mention}",
                inline=False
            )
            
            embed.set_footer(text="EXPEDITION Antarctica • Support System")
            
            await channel.send(embed=embed)
            
            # Log ticket closure
            await self.log_ticket_action("closed", channel, user, "unknown", reason)
            
            # Archive and delete channel after delay
            await asyncio.sleep(10)  # Give time for final messages
            
            # Create transcript (optional)
            transcript = await self.create_transcript(channel)
            
            # Delete the channel
            await channel.delete()
            
            return True
            
        except Exception as e:
            print(f"Error closing ticket: {e}")
            return False

    async def create_transcript(self, channel: discord.TextChannel):
        """Create a transcript of the ticket conversation"""
        try:
            messages = []
            async for message in channel.history(limit=1000, oldest_first=True):
                messages.append(f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {message.author}: {message.content}")
            
            transcript = "\n".join(messages)
            
            # Save transcript to file
            filename = f"transcript-{channel.id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            return filename
            
        except Exception as e:
            print(f"Error creating transcript: {e}")
            return None

    async def get_user_open_ticket(self, user_id: int):
        """Get user's open ticket channel"""
        try:
            # This would typically query your database
            # For now, we'll check if the user has a ticket channel
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    if channel.name.startswith("ticket-") and str(user_id) in channel.topic:
                        return channel
            return None
        except Exception as e:
            print(f"Error getting user ticket: {e}")
            return None

    async def save_ticket_data(self, channel_id: int, user_id: int, ticket_type: str, status: str, reason: str = ""):
        """Save ticket data to database"""
        try:
            ticket_data = {
                "channel_id": channel_id,
                "user_id": user_id,
                "ticket_type": ticket_type,
                "status": status,
                "created_at": datetime.now().isoformat(),
                "closed_at": datetime.now().isoformat() if status == "closed" else None,
                "reason": reason
            }
            
            # Save to database (implement based on your database structure)
            # db.save_ticket(ticket_data)
            
        except Exception as e:
            print(f"Error saving ticket data: {e}")

    async def log_ticket_action(self, action: str, channel: discord.TextChannel, user: discord.Member, ticket_type: str, reason: str = ""):
        """Log ticket actions to log channel"""
        try:
            if not self.log_channel_id:
                return
            
            log_channel = self.bot.get_channel(self.log_channel_id)
            if not log_channel:
                return
            
            action_emojis = {
                "created": "✅",
                "closed": "🔒",
                "reopened": "🔄"
            }
            
            embed = discord.Embed(
                title=f"{action_emojis.get(action, '📝')} Ticket {action.title()}",
                description=f"**Channel:** {channel.mention}\n"
                           f"**User:** {user.mention} ({user.id})\n"
                           f"**Type:** {self.ticket_types.get(ticket_type, {}).get('name', ticket_type)}\n"
                           f"**Action:** {action.title()}",
                color=0x4ecdc4,
                timestamp=datetime.now()
            )
            
            if reason:
                embed.add_field(name="📝 Reason", value=reason, inline=False)
            
            embed.set_footer(text=f"Channel ID: {channel.id}")
            
            await log_channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging ticket action: {e}")

class TicketSelectionView(View):
    def __init__(self, ticket_system: ExpeditionTickets):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system

    @discord.ui.button(label="🛡️ Player Report", style=discord.ButtonStyle.danger, custom_id="ticket_player_report")
    async def player_report(self, interaction: discord.Interaction, button: Button):
        await self.ticket_system.create_ticket(interaction, "player_report")

    @discord.ui.button(label="🐛 Bug Report", style=discord.ButtonStyle.secondary, custom_id="ticket_bug_report")
    async def bug_report(self, interaction: discord.Interaction, button: Button):
        await self.ticket_system.create_ticket(interaction, "bug_report")

    @discord.ui.button(label="💡 Suggestion", style=discord.ButtonStyle.primary, custom_id="ticket_suggestion")
    async def suggestion(self, interaction: discord.Interaction, button: Button):
        await self.ticket_system.create_ticket(interaction, "suggestion")

    @discord.ui.button(label="⚖️ Appeal", style=discord.ButtonStyle.secondary, custom_id="ticket_appeal")
    async def appeal(self, interaction: discord.Interaction, button: Button):
        await self.ticket_system.create_ticket(interaction, "appeal")

    @discord.ui.button(label="❓ General Support", style=discord.ButtonStyle.success, custom_id="ticket_general")
    async def general_support(self, interaction: discord.Interaction, button: Button):
        await self.ticket_system.create_ticket(interaction, "general")

class TicketManagementView(View):
    def __init__(self, ticket_system: ExpeditionTickets, channel: discord.TextChannel, user: discord.Member):
        super().__init__(timeout=None)
        self.ticket_system = ticket_system
        self.channel = channel
        self.user = user

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_channels and interaction.user != self.user:
            await interaction.response.send_message("❌ You don't have permission to close this ticket!", ephemeral=True)
            return
        
        await interaction.response.send_modal(TicketCloseModal(self.ticket_system, self.channel, self.user))

    @discord.ui.button(label="📋 Add Note", style=discord.ButtonStyle.secondary, custom_id="add_note")
    async def add_note(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ You don't have permission to add notes!", ephemeral=True)
            return
        
        await interaction.response.send_modal(TicketNoteModal(self.channel))

class TicketCloseModal(Modal, title="Close Ticket"):
    def __init__(self, ticket_system: ExpeditionTickets, channel: discord.TextChannel, user: discord.Member):
        super().__init__()
        self.ticket_system = ticket_system
        self.channel = channel
        self.user = user

    reason = TextInput(
        label="Reason for closing",
        placeholder="Enter the reason for closing this ticket...",
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value if self.reason.value else "No reason provided"
        
        embed = discord.Embed(
            title="🔒 Closing Ticket",
            description="This ticket will be closed in 10 seconds...",
            color=0xff6b6b
        )
        await interaction.response.send_message(embed=embed)
        
        await self.ticket_system.close_ticket(self.channel, self.user, reason)

class TicketNoteModal(Modal, title="Add Staff Note"):
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    note = TextInput(
        label="Staff Note",
        placeholder="Enter a staff note...",
        max_length=1000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📋 Staff Note",
            description=self.note.value,
            color=0x4ecdc4,
            timestamp=datetime.now()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Staff Note")
        
        await self.channel.send(embed=embed)
        await interaction.response.send_message("✅ Note added successfully!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ExpeditionTickets(bot))