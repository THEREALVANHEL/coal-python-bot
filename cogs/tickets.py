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
from cogs.ticket_controls import CoolTicketControls, DirectTicketPanel, DIRECT_TICKET_CATEGORIES

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views for the unified direct ticket system only
        self.bot.add_view(DirectTicketPanel())
        print("✅ Tickets loaded with unified direct button system only")

    @app_commands.command(name="ticketpanel", description="🎫 Create direct ticket panel in current channel (Admin only)")
    @app_commands.describe(
        channel="Channel where the ticket panel will be posted (optional)"
    )
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Create a direct ticket panel (unified system only)"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only administrators can create ticket panels!", ephemeral=True)
            return

        try:
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
                embed.add_field(name="Required Permissions", value="\n".join(f"• {perm}" for perm in missing_perms), inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Create the unified direct ticket panel
            panel_embed = discord.Embed(
                title="🎫 **Support Ticket System**",
                description="**Need help? Create a support ticket instantly!**\n\nClick one of the buttons below to create a ticket for your specific need. Our support team will assist you shortly.",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # Add category information
            panel_embed.add_field(
                name="📋 **Available Support Categories**",
                value=(
                    "🆘 **General Support** - Questions, account help, bot commands\n"
                    "🔧 **Technical Issues** - Bug reports, Discord problems, errors\n"
                    "💳 **VIP & Billing** - Premium features, subscriptions, perks\n"
                    "🚨 **Report User/Content** - Report violations or inappropriate content\n"
                    "⚖️ **Appeals** - Appeal bans, warnings, or other punishments\n"
                    "🤝 **Partnership** - Server partnerships, business inquiries"
                ),
                inline=False
            )
            
            panel_embed.add_field(
                name="⚡ **How It Works**",
                value="1. Click the button for your issue type\n2. Your ticket channel is created instantly\n3. Describe your issue in detail\n4. Our staff will help you promptly",
                inline=True
            )
            
            panel_embed.add_field(
                name="📝 **Important Notes**",
                value="• One ticket per person at a time\n• Be specific and detailed\n• Staff typically respond within 30 minutes\n• Keep conversations in your ticket channel",
                inline=True
            )
            
            panel_embed.set_footer(text="✨ Professional Support • Click any button below to get started")
            panel_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            # Create the direct ticket panel view
            view = DirectTicketPanel()
            
            # Send the panel
            await target_channel.send(embed=panel_embed, view=view)
            
            # Success response
            success_embed = discord.Embed(
                title="✅ **Direct Ticket Panel Created!**",
                description=f"The direct ticket panel has been posted in {target_channel.mention}",
                color=0x00d4aa
            )
            success_embed.add_field(
                name="🎯 **What's Next?**",
                value="Users can now click the buttons to create instant tickets for any support needs!",
                inline=False
            )
            success_embed.set_footer(text="🎫 Unified Ticket System Ready")

            await interaction.response.send_message(embed=success_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Panel Creation Failed**",
                description=f"Unable to create the ticket panel.",
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
                value="• Can view all tickets\n• Can claim and unclaim tickets\n• Can lock/unlock tickets\n• Can close and reopen tickets\n• Can manage ticket system",
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
        
        # Find all ticket channels (unified system)
        ticket_channels = []
        for channel in guild.text_channels:
            channel_name = channel.name.lower()
            # Look for any ticket channel patterns
            if any(pattern in channel_name for pattern in [
                "open-ticket-", "claimed-by-", "ticket-", "support-"
            ]):
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

    @app_commands.command(name="ticketdashboard", description="🎛️ View live ticket dashboard with real-time stats")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        """Display a real-time ticket dashboard"""
        guild = interaction.guild
        
        # Count different types of tickets (unified system)
        all_channels = guild.text_channels
        
        # Ticket counters
        total_tickets = 0
        claimed_tickets = 0
        unclaimed_tickets = 0
        closed_tickets = 0
        
        ticket_details = []
        
        for channel in all_channels:
            channel_name = channel.name.lower()
            
            # Check if it's a ticket channel (unified system)
            if any(pattern in channel_name for pattern in [
                "open-ticket-", "claimed-by-", "closed-ticket-"
            ]):
                total_tickets += 1
                
                # Check status
                if channel_name.startswith("claimed-by-"):
                    claimed_tickets += 1
                    # Extract claimer name from channel name
                    try:
                        claimer_part = channel_name.split("claimed-by-")[1]
                        status = f"🟡 Claimed by {claimer_part.title()}"
                    except:
                        status = "🟡 Claimed"
                elif channel_name.startswith("closed-ticket-"):
                    closed_tickets += 1
                    status = "⚫ Closed"
                else:
                    unclaimed_tickets += 1
                    status = "🟢 Open"
                
                # Extract user info from channel topic if available
                user_name = "Unknown"
                if channel.topic:
                    try:
                        # Look for User: {id} in topic
                        if "User:" in channel.topic:
                            user_id = channel.topic.split("User:")[1].strip().split()[0]
                            user = guild.get_member(int(user_id))
                            if user:
                                user_name = user.display_name
                    except:
                        pass
                
                ticket_details.append({
                    "channel": channel,
                    "user": user_name,
                    "status": status,
                    "created": channel.created_at
                })
        
        # Create dashboard embed
        embed = discord.Embed(
            title="🎛️ **Live Ticket Dashboard**",
            description=f"Real-time overview of all support tickets in **{guild.name}**",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        
        # Statistics section
        embed.add_field(
            name="📊 **Ticket Statistics**",
            value=f"**Total Active:** {total_tickets}\n**🟡 Claimed:** {claimed_tickets}\n**🟢 Open:** {unclaimed_tickets}\n**⚫ Closed:** {closed_tickets}",
            inline=True
        )
        
        # Response time estimate
        avg_response = "< 30 minutes" if unclaimed_tickets < 3 else "< 1 hour" if unclaimed_tickets < 10 else "< 2 hours"
        embed.add_field(
            name="⏰ **Response Time**",
            value=f"**Estimated:** {avg_response}\n**Load:** {'🟢 Normal' if total_tickets < 5 else '🟡 Busy' if total_tickets < 15 else '🔴 High'}",
            inline=True
        )
        
        embed.add_field(
            name="🎯 **System Status**",
            value=f"**Type:** Unified Direct System\n**Category:** ✨ Support Tickets\n**Status:** {'🟢 Operational' if total_tickets < 20 else '🟡 High Load'}",
            inline=True
        )
        
        # Recent tickets (last 5)
        if ticket_details:
            recent_tickets = sorted(ticket_details, key=lambda x: x["created"], reverse=True)[:5]
            recent_text = ""
            for ticket in recent_tickets:
                time_ago = f"<t:{int(ticket['created'].timestamp())}:R>"
                recent_text += f"{ticket['status']} **{ticket['user']}** - {time_ago}\n"
            
            embed.add_field(
                name="🕒 **Recent Tickets**",
                value=recent_text or "No recent tickets",
                inline=False
            )
        
        # Action buttons for quick management
        embed.add_field(
            name="🛠️ **Quick Actions**",
            value="• Use `/closealltickets` for emergency cleanup\n• Use `/ticketdashboard` to refresh dashboard\n• Use `/giveticketroleperms` to manage staff access",
            inline=False
        )
        
        embed.set_footer(text="🎛️ Dashboard updates in real-time • Unified ticket system")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ticketmanager", description="🎯 Advanced ticket management interface for staff")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_manager(self, interaction: discord.Interaction):
        """Display an advanced ticket management interface"""
        guild = interaction.guild
        
        # Get all ticket channels (unified system)
        ticket_channels = []
        for channel in guild.text_channels:
            channel_name = channel.name.lower()
            if any(pattern in channel_name for pattern in [
                "open-ticket-", "claimed-by-", "closed-ticket-"
            ]):
                
                # Determine status
                if channel_name.startswith("claimed-by-"):
                    claimer = channel_name.split("claimed-by-")[1].title()
                    status = f"🟡 {claimer}"
                    status_color = "🟡"
                elif channel_name.startswith("closed-ticket-"):
                    status = "⚫ Closed"
                    status_color = "⚫"
                else:
                    status = "🟢 Open"
                    status_color = "🟢"
                
                # Extract user info from topic if available
                user_name = "Unknown"
                if channel.topic:
                    try:
                        if "User:" in channel.topic:
                            user_id = channel.topic.split("User:")[1].strip().split()[0]
                            user = guild.get_member(int(user_id))
                            if user:
                                user_name = user.display_name
                    except:
                        pass
                
                ticket_channels.append({
                    "channel": channel,
                    "name": channel.name,
                    "user": user_name,
                    "status": status,
                    "status_color": status_color,
                    "created": channel.created_at,
                    "link": f"https://discord.com/channels/{guild.id}/{channel.id}"
                })
        
        # Sort by status (open first, then claimed, then closed)
        status_order = {"🟢 Open": 0, "🟡": 1, "⚫ Closed": 2}
        ticket_channels.sort(key=lambda x: (status_order.get(x["status"][:2], 3), x["created"]))
        
        if not ticket_channels:
            embed = discord.Embed(
                title="🎯 **Ticket Manager**",
                description="✨ **No active tickets found!**\n\nAll tickets have been resolved. Great job, team!",
                color=0x00d4aa
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Create management embed
        embed = discord.Embed(
            title="🎯 **Advanced Ticket Manager**",
            description=f"**{len(ticket_channels)} tickets** in unified system",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        
        # Group tickets by status
        open_tickets = [t for t in ticket_channels if t["status"] == "🟢 Open"]
        claimed_tickets = [t for t in ticket_channels if t["status_color"] == "🟡"]
        closed_tickets = [t for t in ticket_channels if t["status"] == "⚫ Closed"]
        
        # Add status sections
        if open_tickets:
            open_text = ""
            for ticket in open_tickets[:5]:  # Show top 5
                time_ago = f"<t:{int(ticket['created'].timestamp())}:R>"
                open_text += f"🟢 **{ticket['user']}** • {time_ago}\n└ [{ticket['name'][:35]}...]({ticket['link']})\n\n"
            
            embed.add_field(
                name="🟢 **Open Tickets** (Need Attention)",
                value=open_text or "None",
                inline=False
            )
        
        if claimed_tickets:
            claimed_text = ""
            for ticket in claimed_tickets[:4]:
                time_ago = f"<t:{int(ticket['created'].timestamp())}:R>"
                claimed_text += f"🟡 **{ticket['user']}** • {time_ago}\n└ {ticket['status']}\n\n"
            
            embed.add_field(
                name="🟡 **Claimed Tickets** (Being Handled)",
                value=claimed_text or "None",
                inline=True
            )
        
        if closed_tickets:
            closed_text = ""
            for ticket in closed_tickets[:3]:
                time_ago = f"<t:{int(ticket['created'].timestamp())}:R>"
                closed_text += f"⚫ **{ticket['user']}** • {time_ago}\n"
            
            embed.add_field(
                name="⚫ **Recently Closed**",
                value=closed_text or "None",
                inline=True
            )
        
        # Quick stats
        embed.add_field(
            name="📊 **Summary**",
            value=f"**🟢 Open:** {len(open_tickets)}\n**🟡 Claimed:** {len(claimed_tickets)}\n**⚫ Closed:** {len(closed_tickets)}\n**🎯 Total:** {len(ticket_channels)}",
            inline=True
        )
        
        embed.set_footer(text="🎯 Unified Ticket Management System")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Tickets(bot))