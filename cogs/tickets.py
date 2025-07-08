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

# Define the 4 staff roles that can manage tickets
STAFF_ROLES = [
    "lead moderator",
    "moderator", 
    "overseer",
    "forgotten one"
]

class SimpleTicketView(View):
    """Simple MEE6-style ticket buttons for staff only"""
    def __init__(self, creator_id: int):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        
    def _is_staff(self, user) -> bool:
        """Check if user is authorized staff"""
        # Administrator always has access
        if user.guild_permissions.administrator:
            return True
            
        # Check for special admin role
        if has_special_permissions(user):
            return True
            
        # Check for the 4 specific staff roles
        user_roles = [role.name.lower() for role in user.roles]
        for staff_role in STAFF_ROLES:
            if staff_role in user_roles:
                return True
                
        return False
    
    @discord.ui.button(label="Claim", emoji="👤", style=discord.ButtonStyle.primary, custom_id="ticket_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can claim tickets.", ephemeral=True)
            return
            
        try:
            # Update channel name to show claimer
            creator = interaction.guild.get_member(self.creator_id)
            creator_name = creator.display_name.lower().replace(' ', '-')[:10] if creator else "unknown"
            claimer_name = interaction.user.display_name.lower().replace(' ', '-')[:10]
            
            new_name = f"ticket-{creator_name}-{claimer_name}"
            await interaction.channel.edit(name=new_name)
            
            # Simple response
            embed = discord.Embed(
                title="✅ Ticket Claimed",
                description=f"**{interaction.user.mention}** claimed this ticket",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error claiming ticket: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can close tickets.", ephemeral=True)
            return
            
        try:
            embed = discord.Embed(
                title="🔒 Ticket Closed",
                description=f"Ticket closed by **{interaction.user.mention}**\n\nThis channel will be deleted in 10 seconds.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
            
            # Delete channel after 10 seconds
            await asyncio.sleep(10)
            await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Error closing ticket: {str(e)}", ephemeral=True)
            except:
                pass

class TicketCreateView(View):
    """Simple ticket creation buttons"""
    def __init__(self):
        super().__init__(timeout=None)
        
    def _has_existing_ticket(self, user, guild) -> bool:
        """Check if user already has an active ticket"""
        for channel in guild.text_channels:
            if channel.name.startswith('ticket-') and str(user.id) in channel.topic:
                return True
        return False
    
    @discord.ui.button(label="💬 General Support", style=discord.ButtonStyle.secondary, custom_id="ticket_general")
    async def general_support(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "general", "💬")
    
    @discord.ui.button(label="🔧 Technical Issue", style=discord.ButtonStyle.secondary, custom_id="ticket_technical") 
    async def technical_issue(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "technical", "🔧")
    
    @discord.ui.button(label="👤 Account Help", style=discord.ButtonStyle.secondary, custom_id="ticket_account")
    async def account_help(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "account", "👤")
    
    async def _create_ticket(self, interaction: discord.Interaction, category: str, emoji: str):
        """Create a new ticket"""
        # Check for existing ticket
        if self._has_existing_ticket(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ Ticket Already Exists",
                description="You already have an active ticket. Please use your existing ticket or wait for it to be closed.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Create ticket channel
            username = interaction.user.display_name.lower().replace(' ', '-')[:15]
            channel_name = f"ticket-{username}"
            
            # Find support category or create in general area
            category_channel = None
            for cat in interaction.guild.categories:
                if 'support' in cat.name.lower() or 'ticket' in cat.name.lower():
                    category_channel = cat
                    break
            
            # Set permissions: creator + staff roles can see, everyone else cannot
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
            }
            
            # Add staff roles to permissions
            for role in interaction.guild.roles:
                if role.name.lower() in STAFF_ROLES or role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
            
            # Create the channel
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category_channel,
                overwrites=overwrites,
                topic=f"{emoji} {category.title()} ticket • Creator: {interaction.user.id} • Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Send initial message
            embed = discord.Embed(
                title=f"{emoji} New {category.title()} Ticket",
                description=f"**Ticket Creator:** {interaction.user.mention}\n**Category:** {category.title()}\n**Created:** <t:{int(datetime.now().timestamp())}:F>",
                color=0x7c3aed
            )
            embed.add_field(
                name="📋 What happens next?",
                value="• Staff will respond as soon as possible\n• Please describe your issue in detail\n• Only you and staff can see this channel",
                inline=False
            )
            embed.set_footer(text="🎫 Simple Ticket System")
            
            # Add ticket control buttons (staff only)
            view = SimpleTicketView(interaction.user.id)
            
            await ticket_channel.send(f"{interaction.user.mention}", embed=embed, view=view)
            
            # Success message
            success_embed = discord.Embed(
                title="✅ Ticket Created",
                description=f"Your ticket has been created: {ticket_channel.mention}",
                color=0x00ff00
            )
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ticket Creation Failed",
                description=f"Error: {str(e)}",
                color=0xff0000
            )
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views
        self.bot.add_view(TicketCreateView())
        print("✅ Simple Ticket System loaded")

    @app_commands.command(name="ticket-panel", description="Create a simple ticket panel")
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Create a simple MEE6-style ticket panel"""
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only administrators can create ticket panels.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        target_channel = channel or interaction.channel
        
        # Create simple panel
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Need help? Create a ticket below!\n\n**Rules:**\n• One ticket per person\n• Be clear about your issue\n• Staff will help you soon",
            color=0x7c3aed
        )
        embed.add_field(
            name="📞 Support Categories",
            value="💬 **General** - Questions and general help\n🔧 **Technical** - Bot issues and bugs\n👤 **Account** - Profile and account problems",
            inline=False
        )
        embed.set_footer(text="🎫 Simple Ticket System • Click a button below")
        
        view = TicketCreateView()
        
        await target_channel.send(embed=embed, view=view)
        
        success_embed = discord.Embed(
            title="✅ Ticket Panel Created",
            description=f"Simple ticket panel created in {target_channel.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    @app_commands.command(name="close-ticket", description="Close the current ticket (Staff only)")
    async def close_ticket_command(self, interaction: discord.Interaction):
        """Staff command to close tickets"""
        
        # Check if user is staff
        is_staff = (
            interaction.user.guild_permissions.administrator or
            has_special_permissions(interaction.user) or
            any(role.name.lower() in STAFF_ROLES for role in interaction.user.roles)
        )
        
        if not is_staff:
            embed = discord.Embed(
                title="❌ Access Denied", 
                description="Only staff can close tickets.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if in ticket channel
        if not interaction.channel.name.startswith('ticket-'):
            embed = discord.Embed(
                title="❌ Invalid Channel",
                description="This command can only be used in ticket channels.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Close ticket
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Ticket closed by **{interaction.user.mention}**\n\nChannel will be deleted in 10 seconds.",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        
        await asyncio.sleep(10)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

async def setup(bot):
    await bot.add_cog(Tickets(bot))