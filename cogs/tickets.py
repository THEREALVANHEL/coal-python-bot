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
from cogs.ticket_controls import ElegantTicketControls, ElegantTicketPanel, ELEGANT_TICKET_CATEGORIES

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views for the elegant ticket system
        self.bot.add_view(ElegantTicketPanel())
        print("✅ Elegant Ticket System loaded with beautiful interface and duplicate prevention")

    @app_commands.command(name="ticketpanel", description="🎫 Create elegant ticket panel in current channel (Admin only)")
    @app_commands.describe(
        channel="Channel where the ticket panel will be posted (optional)"
    )
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Create an elegant ticket panel"""
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only administrators can create ticket panels!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
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
                    title="❌ Missing Permissions",
                    description=f"I need the following permissions in {target_channel.mention}:",
                    color=0xff6b6b
                )
                embed.add_field(name="Required Permissions", value="\n".join(f"• {perm}" for perm in missing_perms), inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Create the elegant ticket panel
            panel_embed = discord.Embed(
                title="✨ Professional Support Center",
                description="**Welcome to our Support Center!** 🎫\n\nOur professional support team is here to help you with any questions or issues. Click the category below that best matches your needs to create an instant support ticket.",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            # Add beautiful category information
            category_info = ""
            for category_key, cat_data in ELEGANT_TICKET_CATEGORIES.items():
                category_info += f"{cat_data['emoji']} **{cat_data['name']}**\n└ {cat_data['description']}\n\n"
            
            panel_embed.add_field(
                name="🎯 Support Categories",
                value=category_info,
                inline=False
            )
            
            panel_embed.add_field(
                name="⚡ How It Works",
                value="1. **Choose Category** - Click the button for your issue type\n2. **Instant Creation** - Your private ticket channel is created instantly\n3. **Describe Issue** - Provide clear details about your problem\n4. **Get Help** - Our professional staff will assist you promptly",
                inline=True
            )
            
            panel_embed.add_field(
                name="📝 Important Guidelines",
                value="• **One Ticket Rule** - Only one active ticket per person\n• **Be Specific** - Provide detailed descriptions\n• **Response Time** - Typically 15-30 minutes\n• **Stay Active** - Keep the conversation in your ticket",
                inline=True
            )
            
            panel_embed.add_field(
                name="🏆 Why Choose Our Support?",
                value="• **Professional Team** - Experienced support staff\n• **Fast Response** - Quick resolution times\n• **Private Channels** - Confidential assistance\n• **24/7 Monitoring** - Always available when you need us",
                inline=False
            )
            
            panel_embed.set_footer(text="✨ Professional Support Experience • Click any button below to get started")
            panel_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            panel_embed.set_author(
                name="Support Center", 
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            # Create the elegant panel view
            view = ElegantTicketPanel()
            
            # Send the panel
            panel_msg = await target_channel.send(embed=panel_embed, view=view)
            
            # Try to pin the panel
            try:
                await panel_msg.pin()
            except:
                pass
            
            # Success response
            success_embed = discord.Embed(
                title="✅ Elegant Ticket Panel Created!",
                description=f"The professional ticket panel has been posted in {target_channel.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            success_embed.add_field(
                name="🎯 What's Next?",
                value="• Users can now create instant tickets\n• Beautiful interface with modern design\n• Professional support experience\n• Duplicate prevention system active",
                inline=False
            )
            success_embed.add_field(
                name="🛠️ Panel Features",
                value="• **Elegant Design** - Modern, professional interface\n• **Instant Creation** - No forms, just click and go\n• **Smart Prevention** - Stops duplicate tickets\n• **Beautiful Embeds** - Consistent styling throughout",
                inline=False
            )
            success_embed.set_footer(text="🎫 Elegant Ticket System Ready")

            await interaction.response.send_message(embed=success_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Panel Creation Failed",
                description=f"Unable to create the ticket panel.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔍 Error Details",
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
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only administrators can manage ticket role permissions!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        guild_id = interaction.guild.id
        server_settings = db.get_server_settings(guild_id)
        ticket_support_roles = server_settings.get('ticket_support_roles', [])
        
        if action == "add":
            if not role:
                embed = discord.Embed(
                    title="❌ Missing Role",
                    description="Please specify a role to add!",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if role.id in ticket_support_roles:
                embed = discord.Embed(
                    title="⚠️ Role Already Configured",
                    description=f"{role.mention} already has ticket support permissions.",
                    color=0xff9966
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            ticket_support_roles.append(role.id)
            db.set_guild_setting(guild_id, 'ticket_support_roles', ticket_support_roles)
            
            embed = discord.Embed(
                title="✅ Permissions Granted Successfully",
                description=f"Successfully granted elegant ticket support permissions to {role.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🎫 Granted Permissions",
                value="• **View All Tickets** - Access to all support channels\n• **Claim/Unclaim** - Manage ticket assignments\n• **Lock/Unlock** - Control messaging permissions\n• **Close/Reopen** - Manage ticket lifecycle\n• **Set Priority** - Organize tickets by importance\n• **Professional Interface** - Access to all elegant controls",
                inline=False
            )
            
        elif action == "remove":
            if not role:
                embed = discord.Embed(
                    title="❌ Missing Role",
                    description="Please specify a role to remove!",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if role.id not in ticket_support_roles:
                embed = discord.Embed(
                    title="⚠️ Role Not Configured",
                    description=f"{role.mention} doesn't have ticket support permissions.",
                    color=0xff9966
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            ticket_support_roles.remove(role.id)
            db.set_guild_setting(guild_id, 'ticket_support_roles', ticket_support_roles)
            
            embed = discord.Embed(
                title="✅ Permissions Removed Successfully",
                description=f"Successfully removed ticket support permissions from {role.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
        elif action == "list":
            embed = discord.Embed(
                title="🎫 Ticket Support Configuration",
                description="Current roles with elegant ticket support permissions:",
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            
            if ticket_support_roles:
                role_list = []
                for role_id in ticket_support_roles:
                    role = interaction.guild.get_role(role_id)
                    if role:
                        role_list.append(f"• {role.mention} (`{role.name}`)")
                    else:
                        role_list.append(f"• <@&{role_id}> (deleted role)")
                
                embed.add_field(
                    name="👥 Configured Support Roles",
                    value="\n".join(role_list),
                    inline=False
                )
            else:
                embed.add_field(
                    name="👥 Configured Support Roles",
                    value="No ticket support roles configured.\nUse `/giveticketroleperms add` to add roles.",
                    inline=False
                )
            
            embed.add_field(
                name="💡 Automatic Permissions",
                value="• **Administrators** - Always have full access\n• **Manage Channels** - Built-in ticket permissions\n• **Role Names** - Roles with 'mod', 'staff', 'support' in name",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="closealltickets", description="🚨 Emergency: Close all open tickets")
    @app_commands.default_permissions(administrator=True)
    async def close_all_tickets(self, interaction: discord.Interaction):
        """Emergency command to close all open tickets"""
        
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only administrators can use this emergency command!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        guild = interaction.guild
        closed_count = 0
        
        # Find all ticket channels (elegant system)
        ticket_channels = []
        for channel in guild.text_channels:
            channel_name = channel.name.lower()
            # Look for elegant ticket patterns
            if any(pattern in channel_name for pattern in [
                "🟢・open・", "🟡・", "🔒・closed・", "ticket", "support"
            ]):
                ticket_channels.append(channel)
        
        if not ticket_channels:
            embed = discord.Embed(
                title="ℹ️ No Active Tickets",
                description="No open ticket channels found in the elegant system.",
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
            title="🚨 Emergency Ticket Closure Complete",
            description=f"Successfully closed **{closed_count}** ticket channels.",
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="⚠️ Important Note",
            value="This was an emergency action. Consider informing users about the closure and why it was necessary.",
            inline=False
        )
        embed.add_field(
            name="📊 Closure Summary",
            value=f"**Channels Affected:** {closed_count}\n**Action By:** {interaction.user.display_name}\n**Reason:** Emergency closure\n**System:** Elegant Ticket System",
            inline=False
        )
        embed.set_footer(text=f"Emergency action performed by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ticketdashboard", description="🎛️ View elegant ticket dashboard with real-time stats")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_dashboard(self, interaction: discord.Interaction):
        """Display a beautiful real-time ticket dashboard"""
        guild = interaction.guild
        
        # Count different types of tickets (elegant system)
        all_channels = guild.text_channels
        
        # Ticket counters
        total_tickets = 0
        claimed_tickets = 0
        unclaimed_tickets = 0
        closed_tickets = 0
        
        ticket_details = []
        
        for channel in all_channels:
            channel_name = channel.name.lower()
            
            # Check if it's an elegant ticket channel
            if any(pattern in channel_name for pattern in [
                "🟢・open・", "🟡・", "🔒・closed・"
            ]):
                total_tickets += 1
                
                # Determine status from elegant naming
                if "🟡・" in channel_name:
                    claimed_tickets += 1
                    # Extract claimer from elegant name format
                    try:
                        parts = channel_name.split("・")
                        if len(parts) >= 2:
                            claimer_name = parts[1].replace("-", " ").title()
                            status = f"🟡 Claimed by {claimer_name}"
                        else:
                            status = "🟡 Claimed"
                    except:
                        status = "🟡 Claimed"
                elif "🔒・closed・" in channel_name:
                    closed_tickets += 1
                    status = "🔒 Closed"
                else:
                    unclaimed_tickets += 1
                    status = "🟢 Open"
                
                # Extract user info from channel topic
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
                
                ticket_details.append({
                    "channel": channel,
                    "user": user_name,
                    "status": status,
                    "created": channel.created_at
                })
        
        # Create elegant dashboard embed
        embed = discord.Embed(
            title="🎛️ Elegant Ticket Dashboard",
            description=f"**Professional Support Analytics** for **{guild.name}**\n\nReal-time overview of the elegant ticket system with beautiful interface and advanced features.",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        
        # Statistics section
        embed.add_field(
            name="📊 Live Statistics",
            value=f"**🎫 Total Active:** {total_tickets}\n**🟡 Staff Claimed:** {claimed_tickets}\n**🟢 Awaiting Staff:** {unclaimed_tickets}\n**🔒 Recently Closed:** {closed_tickets}",
            inline=True
        )
        
        # Response analytics
        if unclaimed_tickets == 0:
            response_status = "🟢 Excellent"
            response_time = "< 15 minutes"
        elif unclaimed_tickets < 3:
            response_status = "🟢 Great"
            response_time = "< 30 minutes"
        elif unclaimed_tickets < 8:
            response_status = "🟡 Good"
            response_time = "< 1 hour"
        else:
            response_status = "🔴 Busy"
            response_time = "< 2 hours"
        
        embed.add_field(
            name="⏰ Response Analytics",
            value=f"**Estimated Time:** {response_time}\n**Service Level:** {response_status}\n**Load Status:** {'🟢 Normal' if total_tickets < 10 else '🟡 Busy' if total_tickets < 25 else '🔴 High'}",
            inline=True
        )
        
        embed.add_field(
            name="✨ System Status",
            value=f"**Type:** Elegant Ticket System\n**Category:** ✨ Support Center\n**Interface:** Professional & Modern\n**Status:** {'🟢 Operational' if total_tickets < 30 else '🟡 High Volume'}",
            inline=True
        )
        
        # Recent activity (last 5 tickets)
        if ticket_details:
            recent_tickets = sorted(ticket_details, key=lambda x: x["created"], reverse=True)[:5]
            recent_text = ""
            for ticket in recent_tickets:
                time_ago = f"<t:{int(ticket['created'].timestamp())}:R>"
                recent_text += f"{ticket['status']} **{ticket['user']}** • {time_ago}\n"
            
            embed.add_field(
                name="🕒 Recent Activity",
                value=recent_text or "No recent activity",
                inline=False
            )
        
        # Management actions
        embed.add_field(
            name="🛠️ Quick Management",
            value="• Use `/closealltickets` for emergency cleanup\n• Use `/ticketdashboard` to refresh this view\n• Use `/giveticketroleperms` to manage staff\n• Use `/ticketmanager` for advanced controls",
            inline=False
        )
        
        embed.set_footer(text="🎛️ Real-time dashboard • Elegant ticket system • Updates automatically")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_author(
            name="Support Dashboard", 
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ticketmanager", description="🎯 Advanced elegant ticket management interface")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_manager(self, interaction: discord.Interaction):
        """Display an advanced elegant ticket management interface"""
        guild = interaction.guild
        
        # Get all elegant ticket channels
        ticket_channels = []
        for channel in guild.text_channels:
            channel_name = channel.name.lower()
            if any(pattern in channel_name for pattern in [
                "🟢・open・", "🟡・", "🔒・closed・"
            ]):
                
                # Determine status from elegant naming
                if "🟡・" in channel_name:
                    try:
                        parts = channel_name.split("・")
                        claimer_name = parts[1].replace("-", " ").title() if len(parts) >= 2 else "Unknown"
                        status = f"🟡 {claimer_name}"
                        status_color = "🟡"
                    except:
                        status = "🟡 Claimed"
                        status_color = "🟡"
                elif "🔒・closed・" in channel_name:
                    status = "🔒 Closed"
                    status_color = "🔒"
                else:
                    status = "🟢 Open"
                    status_color = "🟢"
                
                # Extract user info from topic
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
        
        # Sort by priority (open first, then claimed, then closed)
        status_priority = {"🟢 Open": 0, "🟡": 1, "🔒 Closed": 2}
        ticket_channels.sort(key=lambda x: (status_priority.get(x["status"][:2], 3), x["created"]))
        
        if not ticket_channels:
            embed = discord.Embed(
                title="🎯 Elegant Ticket Manager",
                description="✨ **No active tickets found!**\n\nAll tickets have been resolved. Excellent work from the support team!",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🏆 System Status",
                value="• **All Clear** - No pending tickets\n• **Professional Service** - Users are being helped\n• **Elegant System** - Working perfectly\n• **Ready for Action** - Waiting for new tickets",
                inline=False
            )
            embed.set_footer(text="🎯 Elegant Ticket Management System")
            await interaction.response.send_message(embed=embed)
            return
        
        # Create elegant management embed
        embed = discord.Embed(
            title="🎯 Advanced Ticket Manager",
            description=f"**{len(ticket_channels)} active tickets** in the elegant system\n\nProfessional interface for managing support tickets with beautiful design.",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        
        # Group tickets by status
        open_tickets = [t for t in ticket_channels if t["status"] == "🟢 Open"]
        claimed_tickets = [t for t in ticket_channels if t["status_color"] == "🟡"]
        closed_tickets = [t for t in ticket_channels if t["status"] == "🔒 Closed"]
        
        # Add elegant status sections
        if open_tickets:
            open_text = ""
            for ticket in open_tickets[:5]:  # Show top 5
                time_ago = f"<t:{int(ticket['created'].timestamp())}:R>"
                open_text += f"🟢 **{ticket['user']}** • {time_ago}\n└ [{ticket['name'][:30]}...]({ticket['link']})\n\n"
            
            embed.add_field(
                name="🟢 Open Tickets (Need Immediate Attention)",
                value=open_text or "None",
                inline=False
            )
        
        if claimed_tickets:
            claimed_text = ""
            for ticket in claimed_tickets[:4]:
                time_ago = f"<t:{int(ticket['created'].timestamp())}:R>"
                claimed_text += f"🟡 **{ticket['user']}** • {time_ago}\n└ {ticket['status']}\n\n"
            
            embed.add_field(
                name="🟡 Claimed Tickets (Being Handled)",
                value=claimed_text or "None",
                inline=True
            )
        
        if closed_tickets:
            closed_text = ""
            for ticket in closed_tickets[:3]:
                time_ago = f"<t:{int(ticket['created'].timestamp())}:R>"
                closed_text += f"🔒 **{ticket['user']}** • {time_ago}\n"
            
            embed.add_field(
                name="🔒 Recently Closed",
                value=closed_text or "None",
                inline=True
            )
        
        # Elegant summary
        embed.add_field(
            name="📊 Professional Summary",
            value=f"**🟢 Needs Staff:** {len(open_tickets)}\n**🟡 Being Helped:** {len(claimed_tickets)}\n**🔒 Resolved:** {len(closed_tickets)}\n**🎯 Total Active:** {len(ticket_channels)}",
            inline=True
        )
        
        embed.set_footer(text="🎯 Elegant Ticket Management • Professional Interface")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_author(
            name="Support Manager", 
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Tickets(bot))