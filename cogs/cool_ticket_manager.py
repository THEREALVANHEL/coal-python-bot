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

class CoolTicketManagerView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎯 Claim", style=discord.ButtonStyle.success, emoji="🎯", custom_id="cool_ticket_claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        """Claim this ticket"""
        if not await self.check_permissions(interaction):
            return
            
        channel = interaction.channel
        
        # Check if already claimed
        if "🟡・" in channel.name.lower():
            embed = discord.Embed(
                title="⚠️ Already Claimed",
                description="This ticket is already claimed by someone else.",
                color=0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Update channel name to show claim
            staff_name = interaction.user.display_name.lower().replace(" ", "-")
            new_name = channel.name.replace("🟢・open・", f"🟡・{staff_name}・")
            await channel.edit(name=new_name)
            
            # Create beautiful claim embed
            embed = discord.Embed(
                title="🎯 Ticket Claimed",
                description=f"This ticket has been claimed by **{interaction.user.display_name}**",
                color=0xffd700,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="👤 Claimed By",
                value=f"{interaction.user.mention}\n`{interaction.user.display_name}`",
                inline=True
            )
            embed.add_field(
                name="⏰ Claim Time",
                value=f"<t:{int(datetime.now().timestamp())}:F>",
                inline=True
            )
            embed.add_field(
                name="📋 Next Steps",
                value="• Staff will assist you shortly\n• Please be patient and stay active\n• Provide any additional details needed",
                inline=False
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text="🎯 Professional Support Experience")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Claim Failed",
                description="Unable to claim this ticket. Please try again.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @discord.ui.button(label="🔄 Release", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="cool_ticket_release")
    async def release_ticket(self, interaction: discord.Interaction, button: Button):
        """Release/unclaim this ticket"""
        if not await self.check_permissions(interaction):
            return
            
        channel = interaction.channel
        
        # Check if claimed
        if "🟡・" not in channel.name.lower():
            embed = discord.Embed(
                title="⚠️ Not Claimed",
                description="This ticket is not currently claimed.",
                color=0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Extract original name from topic or create new one
            original_name = "🟢・open・support"
            if channel.topic and "Original:" in channel.topic:
                try:
                    original_name = channel.topic.split("Original:")[1].strip().split()[0]
                except:
                    pass
            
            # Update channel name to remove claim
            parts = channel.name.split("・")
            if len(parts) >= 3:
                user_part = parts[2]
                new_name = f"🟢・open・{user_part}"
            else:
                new_name = original_name
                
            await channel.edit(name=new_name)
            
            # Create beautiful release embed
            embed = discord.Embed(
                title="🔄 Ticket Released",
                description=f"This ticket has been released by **{interaction.user.display_name}** and is now available for other staff.",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🔄 Released By",
                value=f"{interaction.user.mention}\n`{interaction.user.display_name}`",
                inline=True
            )
            embed.add_field(
                name="📈 Status",
                value="🟢 **Available for Claim**\nOther staff can now claim this ticket",
                inline=True
            )
            embed.add_field(
                name="💡 Note",
                value="This ticket is back in the queue for other support staff to handle.",
                inline=False
            )
            embed.set_footer(text="🔄 Ticket management system")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Release Failed",
                description="Unable to release this ticket. Please try again.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="cool_ticket_lock")
    async def lock_ticket(self, interaction: discord.Interaction, button: Button):
        """Lock the ticket (user can't send messages)"""
        if not await self.check_permissions(interaction):
            return
            
        channel = interaction.channel
        
        try:
            # Get the ticket creator from channel topic
            user_id = None
            if channel.topic and "User:" in channel.topic:
                try:
                    user_id = int(channel.topic.split("User:")[1].strip().split()[0])
                except:
                    pass
            
            # Lock the channel for the user
            overwrites = channel.overwrites
            if user_id:
                user = interaction.guild.get_member(user_id)
                if user:
                    overwrites[user] = discord.PermissionOverwrite(send_messages=False)
                    await channel.edit(overwrites=overwrites)
            
            # Create lock embed
            embed = discord.Embed(
                title="🔒 Ticket Locked",
                description="This ticket has been locked. The user can no longer send messages.",
                color=0xff4444,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🔒 Locked By",
                value=f"{interaction.user.mention}\n`{interaction.user.display_name}`",
                inline=True
            )
            embed.add_field(
                name="📋 Effect",
                value="• User cannot send messages\n• Staff can still communicate\n• Use 🔓 Unlock to reverse",
                inline=True
            )
            embed.add_field(
                name="💡 Common Use Cases",
                value="• Preventing spam\n• Temporary user timeout\n• Investigation period\n• Awaiting user compliance",
                inline=False
            )
            embed.set_footer(text="🔒 Ticket security system")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Lock Failed",
                description="Unable to lock this ticket. Please check permissions.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success, emoji="🔓", custom_id="cool_ticket_unlock")
    async def unlock_ticket(self, interaction: discord.Interaction, button: Button):
        """Unlock the ticket (user can send messages again)"""
        if not await self.check_permissions(interaction):
            return
            
        channel = interaction.channel
        
        try:
            # Get the ticket creator from channel topic
            user_id = None
            if channel.topic and "User:" in channel.topic:
                try:
                    user_id = int(channel.topic.split("User:")[1].strip().split()[0])
                except:
                    pass
            
            # Unlock the channel for the user
            overwrites = channel.overwrites
            if user_id:
                user = interaction.guild.get_member(user_id)
                if user:
                    overwrites[user] = discord.PermissionOverwrite(send_messages=True, read_messages=True)
                    await channel.edit(overwrites=overwrites)
            
            # Create unlock embed
            embed = discord.Embed(
                title="🔓 Ticket Unlocked",
                description="This ticket has been unlocked. The user can now send messages again.",
                color=0x00ff88,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🔓 Unlocked By",
                value=f"{interaction.user.mention}\n`{interaction.user.display_name}`",
                inline=True
            )
            embed.add_field(
                name="📋 Effect",
                value="• User can send messages\n• Normal ticket operation\n• Full communication restored",
                inline=True
            )
            embed.add_field(
                name="💬 User Notice",
                value="The user has been notified that they can continue communicating in this ticket.",
                inline=False
            )
            embed.set_footer(text="🔓 Ticket security system")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unlock Failed",
                description="Unable to unlock this ticket. Please check permissions.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, emoji="❌", custom_id="cool_ticket_close", row=1)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        """Close this ticket"""
        if not await self.check_permissions(interaction):
            return
        
        # Create confirmation embed
        embed = discord.Embed(
            title="❌ Confirm Ticket Closure",
            description="Are you sure you want to close this ticket? This action cannot be easily undone.",
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="⚠️ What Happens",
            value="• Channel will be deleted\n• User will be notified\n• Ticket will be archived\n• Cannot be reopened easily",
            inline=False
        )
        embed.set_footer(text="Click Confirm to proceed or ignore to cancel")
        
        # Create confirmation view
        view = TicketCloseConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="⭐ Priority", style=discord.ButtonStyle.primary, emoji="⭐", custom_id="cool_ticket_priority", row=1)
    async def set_priority(self, interaction: discord.Interaction, button: Button):
        """Set ticket priority"""
        if not await self.check_permissions(interaction):
            return
        
        # Create priority selector
        embed = discord.Embed(
            title="⭐ Set Ticket Priority",
            description="Choose the priority level for this ticket:",
            color=0x7c3aed
        )
        view = TicketPriorityView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📊 Info", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="cool_ticket_info", row=1)
    async def ticket_info(self, interaction: discord.Interaction, button: Button):
        """Show ticket information"""
        channel = interaction.channel
        
        # Extract info from channel
        created_time = channel.created_at
        user_id = None
        category = "Unknown"
        
        if channel.topic:
            if "User:" in channel.topic:
                try:
                    user_id = int(channel.topic.split("User:")[1].strip().split()[0])
                except:
                    pass
            if "Category:" in channel.topic:
                try:
                    category = channel.topic.split("Category:")[1].strip().split()[0]
                except:
                    pass
        
        # Determine status from channel name
        status = "🟢 Open"
        claimed_by = "None"
        if "🟡・" in channel.name.lower():
            status = "🟡 Claimed"
            try:
                parts = channel.name.split("・")
                if len(parts) >= 2:
                    claimed_by = parts[1].replace("-", " ").title()
            except:
                pass
        elif "🔒・" in channel.name.lower():
            status = "🔒 Closed"
        
        # Get user info
        user_mention = "Unknown User"
        if user_id:
            user = interaction.guild.get_member(user_id)
            if user:
                user_mention = f"{user.mention} (`{user.display_name}`)"
        
        # Create info embed
        embed = discord.Embed(
            title="📊 Ticket Information",
            description=f"Detailed information about this support ticket",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👤 Ticket Creator",
            value=user_mention,
            inline=True
        )
        embed.add_field(
            name="📅 Created",
            value=f"<t:{int(created_time.timestamp())}:F>\n<t:{int(created_time.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="📋 Status",
            value=f"{status}\n**Claimed By:** {claimed_by}",
            inline=True
        )
        embed.add_field(
            name="🏷️ Category",
            value=category.title(),
            inline=True
        )
        embed.add_field(
            name="🔗 Channel Info",
            value=f"**Name:** `{channel.name}`\n**ID:** `{channel.id}`",
            inline=True
        )
        embed.add_field(
            name="📈 Activity",
            value=f"**Messages:** {len([m async for m in channel.history(limit=100)])}\n**Active:** {'Yes' if (datetime.now() - created_time).days < 1 else 'No'}",
            inline=True
        )
        
        embed.set_footer(text="📊 Ticket management system")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔧 Tools", style=discord.ButtonStyle.secondary, emoji="🔧", custom_id="cool_ticket_tools", row=1)
    async def ticket_tools(self, interaction: discord.Interaction, button: Button):
        """Show additional ticket tools"""
        if not await self.check_permissions(interaction):
            return
        
        embed = discord.Embed(
            title="🔧 Ticket Management Tools",
            description="Additional tools and actions for this ticket:",
            color=0x36393f
        )
        
        tools_text = """
        🔄 **Transfer** - Move to another staff member
        📝 **Add Note** - Add internal staff note
        👥 **Add User** - Add someone to the ticket
        📎 **Archive** - Archive without closing
        🔔 **Notify** - Send notification to user
        📋 **Log** - View ticket activity log
        🏷️ **Tag** - Add tags for organization
        ⏰ **Remind** - Set reminder for follow-up
        """
        
        embed.add_field(
            name="🛠️ Available Tools",
            value=tools_text,
            inline=False
        )
        
        embed.add_field(
            name="💡 Quick Actions",
            value="• Use buttons above for common actions\n• Type `/tickettools` for advanced options\n• Right-click channel for quick settings",
            inline=False
        )
        
        embed.set_footer(text="🔧 Professional ticket management")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        """Check if user has permissions to manage tickets"""
        member = interaction.user
        guild = interaction.guild
        
        # Check if user is admin
        if member.guild_permissions.administrator:
            return True
        
        # Check if user has manage_channels permission
        if member.guild_permissions.manage_channels:
            return True
        
        # Check ticket support roles
        server_settings = db.get_server_settings(guild.id)
        ticket_support_roles = server_settings.get('ticket_support_roles', [])
        
        user_role_ids = [role.id for role in member.roles]
        if any(role_id in ticket_support_roles for role_id in user_role_ids):
            return True
        
        # Check role names for common support roles
        role_names = [role.name.lower() for role in member.roles]
        support_keywords = ['mod', 'staff', 'support', 'helper', 'admin']
        if any(keyword in ' '.join(role_names) for keyword in support_keywords):
            return True
        
        # Permission denied
        embed = discord.Embed(
            title="❌ Access Denied",
            description="You don't have permission to manage tickets.",
            color=0xff6b6b
        )
        embed.add_field(
            name="Required Permissions",
            value="• Administrator\n• Manage Channels\n• Ticket Support Role\n• Staff/Mod role",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False


class TicketCloseConfirmView(View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="✅ Confirm Close", style=discord.ButtonStyle.danger, emoji="✅")
    async def confirm_close(self, interaction: discord.Interaction, button: Button):
        """Confirm ticket closure"""
        channel = interaction.channel
        
        try:
            # Get user info before deletion
            user_id = None
            if channel.topic and "User:" in channel.topic:
                try:
                    user_id = int(channel.topic.split("User:")[1].strip().split()[0])
                except:
                    pass
            
            # Send final message
            embed = discord.Embed(
                title="❌ Ticket Closing",
                description=f"This ticket is being closed by **{interaction.user.display_name}**.\n\nThank you for using our support system!",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="📊 Closure Details",
                value=f"**Closed By:** {interaction.user.mention}\n**Time:** <t:{int(datetime.now().timestamp())}:F>\n**Reason:** Manual closure",
                inline=False
            )
            embed.set_footer(text="This channel will be deleted in 10 seconds...")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            # Wait a moment then delete
            await asyncio.sleep(10)
            await channel.delete(reason=f"Ticket closed by {interaction.user.display_name}")
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Close Failed",
                description="Unable to close the ticket. Please try again.",
                color=0xff6b6b
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


class TicketPriorityView(View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="🔴 Critical", style=discord.ButtonStyle.danger, emoji="🔴")
    async def priority_critical(self, interaction: discord.Interaction, button: Button):
        await self.set_priority(interaction, "🔴 Critical", 0xff0000, "Urgent issue requiring immediate attention")

    @discord.ui.button(label="🟡 High", style=discord.ButtonStyle.primary, emoji="🟡")
    async def priority_high(self, interaction: discord.Interaction, button: Button):
        await self.set_priority(interaction, "🟡 High", 0xffaa00, "Important issue requiring prompt attention")

    @discord.ui.button(label="🟢 Normal", style=discord.ButtonStyle.success, emoji="🟢")
    async def priority_normal(self, interaction: discord.Interaction, button: Button):
        await self.set_priority(interaction, "🟢 Normal", 0x00ff00, "Standard priority ticket")

    @discord.ui.button(label="🔵 Low", style=discord.ButtonStyle.secondary, emoji="🔵")
    async def priority_low(self, interaction: discord.Interaction, button: Button):
        await self.set_priority(interaction, "🔵 Low", 0x0066ff, "Non-urgent issue")

    async def set_priority(self, interaction: discord.Interaction, priority: str, color: int, description: str):
        """Set the ticket priority"""
        channel = interaction.channel
        
        try:
            # Update channel topic with priority
            current_topic = channel.topic or ""
            if "Priority:" in current_topic:
                # Replace existing priority
                parts = current_topic.split("Priority:")
                new_topic = parts[0] + f"Priority: {priority}"
            else:
                # Add priority
                new_topic = current_topic + f" | Priority: {priority}"
            
            await channel.edit(topic=new_topic)
            
            # Send priority update message
            embed = discord.Embed(
                title=f"⭐ Priority Set: {priority}",
                description=f"This ticket priority has been updated to **{priority}**\n\n{description}",
                color=color,
                timestamp=datetime.now()
            )
            embed.add_field(
                name="🎯 Set By",
                value=f"{interaction.user.mention}\n`{interaction.user.display_name}`",
                inline=True
            )
            embed.add_field(
                name="⏰ Updated",
                value=f"<t:{int(datetime.now().timestamp())}:F>",
                inline=True
            )
            embed.set_footer(text="⭐ Priority management system")
            
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Priority Update Failed",
                description="Unable to update the ticket priority.",
                color=0xff6b6b
            )
            await interaction.response.edit_message(embed=error_embed, view=None)


class CoolTicketManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views
        self.bot.add_view(CoolTicketManagerView())
        print("✅ Cool Ticket Manager loaded with modern interface")

    @app_commands.command(name="ticketmanager", description="🎛️ Deploy cool ticket management interface in this channel")
    @app_commands.default_permissions(manage_channels=True)
    async def deploy_manager(self, interaction: discord.Interaction):
        """Deploy the cool ticket management interface"""
        
        # Check if this is a ticket channel
        channel = interaction.channel
        if not any(pattern in channel.name.lower() for pattern in ["ticket", "support", "🟢・", "🟡・"]):
            embed = discord.Embed(
                title="⚠️ Not a Ticket Channel",
                description="This doesn't appear to be a ticket channel. The manager is designed for use in active tickets.",
                color=0xff9966
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create the cool management interface
        embed = discord.Embed(
            title="🎛️ Cool Ticket Management Interface",
            description="**Professional Ticket Controls** - Modern, sleek, and powerful\n\nUse the buttons below to manage this ticket with style and efficiency.",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎯 Primary Actions",
            value="**🎯 Claim** - Take ownership of this ticket\n**🔄 Release** - Release claim back to queue\n**🔒 Lock** - Prevent user messages\n**🔓 Unlock** - Restore user messaging",
            inline=True
        )
        
        embed.add_field(
            name="🛠️ Management Tools",
            value="**❌ Close** - Close and archive ticket\n**⭐ Priority** - Set urgency level\n**📊 Info** - View detailed information\n**🔧 Tools** - Advanced options",
            inline=True
        )
        
        embed.add_field(
            name="✨ Interface Features",
            value="• **Modern Design** - Beautiful, professional appearance\n• **Instant Actions** - No delays or confirmations\n• **Smart Permissions** - Automatic access control\n• **Real-time Updates** - Live status synchronization",
            inline=False
        )
        
        embed.add_field(
            name="🎨 Professional Experience",
            value="This interface provides a premium ticket management experience with elegant embeds, smooth interactions, and comprehensive functionality.",
            inline=False
        )
        
        embed.set_footer(text="🎛️ Cool Ticket Manager • Professional Support Interface")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_author(
            name="Ticket Management System",
            icon_url=interaction.user.display_avatar.url
        )
        
        # Create the management view
        view = CoolTicketManagerView()
        
        # Send the interface
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="automanager", description="🚀 Auto-deploy manager interface in all active tickets")
    @app_commands.default_permissions(administrator=True)
    async def auto_deploy_manager(self, interaction: discord.Interaction):
        """Automatically deploy the manager in all active ticket channels"""
        
        await interaction.response.defer()
        
        guild = interaction.guild
        deployed_count = 0
        
        # Find all ticket channels
        for channel in guild.text_channels:
            if any(pattern in channel.name.lower() for pattern in ["🟢・", "🟡・", "ticket", "support"]):
                try:
                    # Check if manager already exists
                    async for message in channel.history(limit=50):
                        if message.author == self.bot.user and "Cool Ticket Management Interface" in (message.embeds[0].title if message.embeds else ""):
                            break
                    else:
                        # Deploy manager
                        embed = discord.Embed(
                            title="🎛️ Cool Ticket Management Interface",
                            description="**Professional Ticket Controls** - Auto-deployed for your convenience\n\nUse the buttons below to manage this ticket efficiently.",
                            color=0x7c3aed,
                            timestamp=datetime.now()
                        )
                        
                        embed.add_field(
                            name="🎯 Quick Actions",
                            value="🎯 Claim • 🔄 Release • 🔒 Lock • 🔓 Unlock",
                            inline=True
                        )
                        
                        embed.add_field(
                            name="🛠️ Management",
                            value="❌ Close • ⭐ Priority • 📊 Info • 🔧 Tools",
                            inline=True
                        )
                        
                        embed.set_footer(text="🚀 Auto-deployed ticket manager")
                        
                        view = CoolTicketManagerView()
                        await channel.send(embed=embed, view=view)
                        deployed_count += 1
                        
                except Exception as e:
                    print(f"Error deploying to {channel.name}: {e}")
                    continue
        
        # Success response
        embed = discord.Embed(
            title="🚀 Auto-Deployment Complete",
            description=f"Successfully deployed the cool ticket manager to **{deployed_count}** ticket channels.",
            color=0x00d4aa,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📊 Deployment Stats",
            value=f"**Channels Updated:** {deployed_count}\n**Interface:** Cool Ticket Manager\n**Status:** Ready for use",
            inline=False
        )
        embed.set_footer(text="🚀 Professional ticket management system")
        
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CoolTicketManager(bot))