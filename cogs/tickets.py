import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime, timedelta
import os, sys
import asyncio

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

# Define the 4 staff roles that can manage tickets
STAFF_ROLES = ["forgotten one", "overseer", "lead moderator", "moderator"]

class ModernTicketControlPanel(View):
    """🎫 Modern Ticket Control Panel - Simple & Elegant Design"""
    def __init__(self, creator_id: int):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.claimed_by = None
        
    def _is_staff(self, user) -> bool:
        """Check if user is authorized staff (the 4 roles) - ENHANCED MATCHING"""
        if user.guild_permissions.administrator:
            return True
        
        # Check for special admin role (if user has roles)
        if hasattr(user, 'roles') and user.roles:
            if any(role.id == 1376574861333495910 for role in user.roles):
                return True
        
        # Enhanced role matching for staff roles
        user_roles = [role.name.lower().strip() for role in user.roles]
        
        for user_role in user_roles:
            for staff_role in STAFF_ROLES:
                # Check exact match
                if user_role == staff_role:
                    return True
                # Check if staff role is contained in user role
                if staff_role in user_role:
                    return True
                # Check if user role contains all words of staff role
                if all(word in user_role for word in staff_role.split()):
                    return True
        
        return False
    
    @discord.ui.button(label="Claim", emoji="🟢", style=discord.ButtonStyle.success, custom_id="modern_claim", row=0)
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can claim tickets.", ephemeral=True)
            return
            
        try:
            # Allow unlimited claims/transfers - no restrictions
            current_claimer_id = self.claimed_by
            current_user_id = interaction.user.id
            
            # Check if this is a transfer/reclaim situation
            if current_claimer_id and current_claimer_id != current_user_id:
                # This is a transfer from another staff member
                old_claimer = interaction.guild.get_member(current_claimer_id)
                old_name = old_claimer.display_name if old_claimer else "Unknown Staff"
                
                # Update channel name to new claimer
                claimer_name = interaction.user.display_name.lower().replace(' ', '-')[:10]
                new_name = f"🟢┃{claimer_name}-ticket"
                
                try:
                    await interaction.channel.edit(name=new_name)
                except discord.HTTPException:
                    # If name change fails, continue anyway
                    pass
                
                # Update the view state
                self.claimed_by = current_user_id
                
                # Create transfer embed
                embed = discord.Embed(
                    title="🔄 Ticket Ownership Transferred",
                    description=f"**Previous Claimer:** {old_name}\n**New Claimer:** {interaction.user.mention}",
                    color=0x00ff7f,
                    timestamp=datetime.now()
                )
                embed.add_field(name="🎯 Status", value="**TRANSFERRED**", inline=True)
                embed.add_field(name="⏰ Time", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
                embed.add_field(name="📋 Next Steps", value="• Continue assisting the user\n• Use /close when resolved", inline=False)
                embed.set_footer(text="🎫 Modern Ticket System • Transfer Complete")
                
                await interaction.response.send_message(embed=embed)
                
            elif current_claimer_id == current_user_id:
                # This is a reclaim by the same person - always allow
                embed = discord.Embed(
                    title="🔄 Ticket Reclaimed",
                    description=f"**Staff Member:** {interaction.user.mention}\n**Status:** 🟢 **ACTIVE (Reclaimed)**",
                    color=0x00ff7f,
                    timestamp=datetime.now()
                )
                embed.add_field(name="🎯 Status", value="**RECLAIMED**", inline=True)
                embed.add_field(name="⏰ Time", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
                embed.add_field(name="📋 Next Steps", value="• Continue assisting the user\n• Use /close when resolved", inline=False)
                embed.set_footer(text="🎫 Modern Ticket System • Reclaimed")
                
                await interaction.response.send_message(embed=embed)
                
            else:
                # First time claim
                claimer_name = interaction.user.display_name.lower().replace(' ', '-')[:10]
                new_name = f"🟢┃{claimer_name}-ticket"
                
                try:
                    await interaction.channel.edit(name=new_name)
                except discord.HTTPException:
                    # If name change fails, continue anyway
                    pass
                
                self.claimed_by = current_user_id
                
                embed = discord.Embed(
                    title="✅ Ticket Successfully Claimed",
                    description=f"**Staff Member:** {interaction.user.mention}\n**Status:** 🟢 **ACTIVE**",
                    color=0x00ff7f,
                    timestamp=datetime.now()
                )
                embed.add_field(name="🎯 Next Steps", value="• Respond to the user's inquiry\n• Use /close when resolved", inline=False)
                embed.set_footer(text="🎫 Modern Ticket System • Claimed")
                
                await interaction.response.send_message(embed=embed)
            
            # Update the original ticket message in all cases
            try:
                async for message in interaction.channel.history(limit=20):
                    if (message.author == interaction.client.user and 
                        message.embeds and 
                        "New Ticket" in message.embeds[0].title):
                        # Update the embed to show new claimer
                        original_embed = message.embeds[0]
                        original_embed.color = 0x00ff7f  # Green for claimed
                        original_embed.title = original_embed.title.replace("🔴", "🟢").replace("WAITING FOR STAFF", f"CLAIMED BY {interaction.user.display_name.upper()}")
                        
                        # Create a new view instance to avoid state conflicts
                        new_view = ModernTicketControlPanel(self.creator_id)
                        new_view.claimed_by = current_user_id
                        
                        await message.edit(embed=original_embed, view=new_view)
                        break
            except Exception as e:
                print(f"Error updating original message: {e}")
            
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error claiming ticket: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error claiming ticket: {str(e)}", ephemeral=True)
            except:
                print(f"Critical error in claim_ticket: {e}")
    
    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="modern_close", row=0)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        if not self._is_staff(interaction.user):
            await interaction.response.send_message("❌ Only **Forgotten One**, **Overseer**, **Lead Moderator**, and **Moderator** can close tickets.", ephemeral=True)
            return
            
        try:
            embed = discord.Embed(
                title="🔒 Ticket Closing",
                description=f"**Closed by:** {interaction.user.mention}\n**Time:** <t:{int(datetime.now().timestamp())}:F>",
                color=0xff4757,
                timestamp=datetime.now()
            )
            embed.add_field(name="⏰ Auto-Delete", value="Channel will be deleted in **10 seconds**", inline=True)
            embed.add_field(name="🎯 Status", value="**RESOLVED**", inline=True)
            embed.set_footer(text="🎫 Modern Ticket System • Closing")
            
            await interaction.response.send_message(embed=embed)
            
            # Add rate limit protection
            await asyncio.sleep(10)
            
            try:
                await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
            except discord.HTTPException as e:
                if "rate limit" in str(e).lower():
                    await asyncio.sleep(60)  # Wait 1 minute if rate limited
                    await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
                else:
                    raise
            
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ Error closing ticket: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ Error closing ticket: {str(e)}", ephemeral=True)
            except:
                print(f"Critical error in close_ticket: {e}")

class ModernTicketCreator(View):
    """🎫 Modern Ticket Creation Interface"""
    def __init__(self):
        super().__init__(timeout=None)
        
    def _has_existing_ticket(self, user, guild) -> bool:
        """Check if user already has an active ticket"""
        for channel in guild.text_channels:
            if (channel.name.startswith('🔴┃') or 
                channel.name.startswith('🟢┃') or 
                channel.name.startswith('ticket-')) and str(user.id) in channel.topic:
                return True
        return False
    
    async def _ping_staff_roles(self, guild):
        """Get staff role mentions for pinging - FIXED VERSION"""
        staff_mentions = []
        
        # Get exact role names to search for
        target_roles = ["forgotten one", "overseer", "lead moderator", "moderator"]
        
        print(f"[DEBUG] Looking for roles: {target_roles}")
        
        for role in guild.roles:
            role_name_lower = role.name.lower().strip()
            
            # Check each target role
            for target_role in target_roles:
                if target_role in role_name_lower or role_name_lower in target_role:
                    staff_mentions.append(role.mention)
                    print(f"[DEBUG] Found staff role: {role.name} -> {role.mention}")
                    break
        
        # If no roles found, try alternative names
        if not staff_mentions:
            alternative_names = ["moderator", "mod", "admin", "staff", "overseer", "lead", "forgotten"]
            for role in guild.roles:
                role_name_lower = role.name.lower().strip()
                for alt_name in alternative_names:
                    if alt_name in role_name_lower:
                        staff_mentions.append(role.mention)
                        print(f"[DEBUG] Found alternative staff role: {role.name}")
                        break
        
        print(f"[DEBUG] Total staff mentions found: {len(staff_mentions)}")
        return staff_mentions
    
    @discord.ui.button(label="💬 General Support", style=discord.ButtonStyle.primary, emoji="💬", custom_id="create_general", row=0)
    async def general_support(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "general", "💬", "General Support")
    
    @discord.ui.button(label="🔧 Technical Issue", style=discord.ButtonStyle.secondary, emoji="🔧", custom_id="create_technical", row=0) 
    async def technical_issue(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "technical", "🔧", "Technical Issue")
    
    @discord.ui.button(label="👤 Account Help", style=discord.ButtonStyle.success, emoji="👤", custom_id="create_account", row=0)
    async def account_help(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "account", "👤", "Account Help")
    
    @discord.ui.button(label="🛡️ Report Issue", style=discord.ButtonStyle.danger, emoji="🛡️", custom_id="create_report", row=0)
    async def report_issue(self, interaction: discord.Interaction, button: Button):
        await self._create_ticket(interaction, "report", "🛡️", "Report Issue")
    
    async def _create_ticket(self, interaction: discord.Interaction, category: str, emoji: str, title: str):
        """Create a new modern ticket with staff role pinging"""
        if self._has_existing_ticket(interaction.user, interaction.guild):
            embed = discord.Embed(
                title="❌ Ticket Already Exists",
                description="You already have an active ticket. Please use your existing ticket or wait for it to be closed.",
                color=0xff4757
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Create ticket channel with modern naming
            username = interaction.user.display_name.lower().replace(' ', '-')[:15]
            channel_name = f"🔴┃{username}-ticket"
            
            # Find support category
            category_channel = None
            for cat in interaction.guild.categories:
                if 'support' in cat.name.lower() or 'ticket' in cat.name.lower():
                    category_channel = cat
                    break
            
            # STRICT PERMISSION SYSTEM - ONLY 4 STAFF ROLES + TICKET CREATOR + BOT
            overwrites = {
                # DENY EVERYONE by default
                interaction.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False,
                    send_messages=False,
                    view_channel=False
                ),
                # ALLOW ticket creator
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True, 
                    view_channel=True
                ),
                # ALLOW bot
                interaction.guild.me: discord.PermissionOverwrite(
                    read_messages=True, 
                    send_messages=True, 
                    manage_messages=True,
                    view_channel=True
                )
            }
            
            # STRICTLY ADD ONLY THE 4 REQUIRED STAFF ROLES
            staff_role_names = ["forgotten one", "overseer", "lead moderator", "moderator"]
            staff_roles_added = []
            
            for role in interaction.guild.roles:
                role_name_lower = role.name.lower().strip()
                
                # EXACT MATCHING for staff roles
                is_staff_role = False
                
                # Check exact matches first
                for staff_role in staff_role_names:
                    if role_name_lower == staff_role:
                        is_staff_role = True
                        break
                
                # Check partial matches if no exact match
                if not is_staff_role:
                    for staff_role in staff_role_names:
                        if staff_role in role_name_lower:
                            # Additional verification for partial matches
                            words = staff_role.split()
                            if all(word in role_name_lower for word in words):
                                is_staff_role = True
                                break
                
                # Administrator override (but still log it)
                if role.permissions.administrator and not is_staff_role:
                    is_staff_role = True
                    print(f"[TICKET PERMS] Added admin role: {role.name}")
                
                if is_staff_role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True, 
                        send_messages=True, 
                        manage_messages=True,
                        manage_channels=True,
                        mention_everyone=True,
                        view_channel=True
                    )
                    staff_roles_added.append(role.name)
                    print(f"[TICKET PERMS] ✅ Added staff role: {role.name}")
            
            print(f"[TICKET PERMS] Total staff roles added: {len(staff_roles_added)} - {staff_roles_added}")
            
            # Ensure we found at least some staff roles
            if len(staff_roles_added) == 0:
                print("[TICKET PERMS] ⚠️ WARNING: No staff roles found! Checking for alternatives...")
                # Emergency fallback - look for any roles with manage_messages permission
                for role in interaction.guild.roles:
                    if role.permissions.manage_messages or role.permissions.administrator:
                        overwrites[role] = discord.PermissionOverwrite(
                            read_messages=True, 
                            send_messages=True, 
                            manage_messages=True,
                            view_channel=True
                        )
                        staff_roles_added.append(f"{role.name} (fallback)")
                        print(f"[TICKET PERMS] 🆘 Fallback added: {role.name}")
            
            # Create the channel
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category_channel,
                overwrites=overwrites,
                topic=f"{emoji} {title} • Creator: {interaction.user.id} • Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Get staff role mentions
            staff_mentions = await self._ping_staff_roles(interaction.guild)
            
            # Create modern ticket embed
            embed = discord.Embed(
                title=f"🎫 New {title}",
                description=f"**Ticket Creator:** {interaction.user.mention}\n**Category:** {title}\n**Status:** 🔴 **WAITING FOR STAFF**",
                color=0x5865f2,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 What's Next?",
                value="• **Staff will respond soon**\n• **Describe your issue in detail**\n• **Only you and staff can see this**\n• **Use buttons below for quick actions**",
                inline=False
            )
            
            embed.add_field(
                name="🛡️ Staff Roles Notified",
                value="• Forgotten One\n• Overseer\n• Lead Moderator\n• Moderator",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Response Time",
                value="Usually within **30 minutes**\nDuring peak hours: **1-2 hours**",
                inline=True
            )
            
            embed.set_footer(text="🎫 Modern Ticket System • Cool & Simplistic")
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Add modern ticket control panel with integrated admin panel
            view = ModernTicketControlPanel(interaction.user.id)
            
            # Ping staff and user
            staff_ping = " ".join(staff_mentions) if staff_mentions else ""
            mention_text = f"🔔 {interaction.user.mention} {staff_ping}"
            
            await ticket_channel.send(mention_text, embed=embed, view=view)
            
            # Success message with permission confirmation
            success_embed = discord.Embed(
                title="✅ Ticket Created Successfully",
                description=f"🎫 Your ticket: {ticket_channel.mention}\n\n🔔 **Staff have been notified!**",
                color=0x00d2d3
            )
            success_embed.add_field(name="⚡ Quick Access", value=f"Click {ticket_channel.mention} to view your ticket", inline=False)
            success_embed.add_field(
                name="🔒 Privacy Confirmed", 
                value=f"**👁️ Can View:** Only you + {len(staff_roles_added)} staff roles\n**🚫 Cannot View:** Everyone else", 
                inline=False
            )
            success_embed.set_footer(text="🎫 Private Ticket System • Strictly Controlled Access")
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ticket Creation Failed",
                description=f"Error: {str(e)}",
                color=0xff4757
            )
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)

class SimpleTickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Add persistent views for buttons to work after bot restart
        self.bot.add_view(ModernTicketControlPanel(0))  # 0 as placeholder
        self.bot.add_view(ModernTicketCreator())
        print("[Tickets] 🎫 Modern Ticket System loaded - Cool & Simplistic!")

    @app_commands.command(name="ticket-panel", description="Create a simple ticket panel")
    @app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Create a simple ticket panel"""
        
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
            description="Need help? Create a ticket below!\n\n**📋 Rules:**\n• One ticket per person\n• Be clear about your issue\n• Staff will help you soon",
            color=0x7c3aed,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="📞 Support Categories",
            value="💬 **General** - Questions and general help\n🔧 **Technical** - Bot issues and bugs\n👤 **Account** - Profile and account problems",
            inline=False
        )
        embed.set_footer(text="🎫 Simple Ticket System • Click a button below")
        
        view = ModernTicketCreator() # Changed to ModernTicketCreator
        
        await target_channel.send(embed=embed, view=view)
        
        success_embed = discord.Embed(
            title="✅ Ticket Panel Created",
            description=f"Simple ticket panel created in {target_channel.mention}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)





    # warnlist command removed from tickets.py to prevent duplicate registration
    # The command is available in moderation.py

async def setup(bot):
    await bot.add_cog(SimpleTickets(bot))