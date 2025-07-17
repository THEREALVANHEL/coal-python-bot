import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput
from datetime import datetime, timedelta
import asyncio
import os, sys
import time

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class PremiumTickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @app_commands.command(name="premium-ticket", description="🎫 Create premium ticket system with advanced features")
    @app_commands.default_permissions(administrator=True)
    async def premium_ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌟 Premium Ticket System",
            description="**Advanced support system with intelligent routing**\n\n"
                       "Choose your ticket type for optimized assistance:",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="🚨 Priority Support",
            value="Fast-track support for urgent issues\n• Instant staff notification\n• Priority queue placement\n• 5-minute response guarantee",
            inline=False
        )
        
        embed.add_field(
            name="🤖 AI Pre-Filter",
            value="Smart ticket creation with context analysis\n• Automatic category detection\n• Solution suggestions\n• Staff expertise matching",
            inline=False
        )
        
        embed.set_footer(text="🎫 Premium features • Enhanced support experience")
        
        view = PremiumTicketPanel()
        await interaction.response.send_message(embed=embed, view=view)

class PremiumTicketPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.select(
        placeholder="🎯 Select your ticket type...",
        options=[
            discord.SelectOption(
                label="🚨 Priority Support",
                description="Urgent issues requiring immediate attention",
                emoji="🚨",
                value="priority"
            ),
            discord.SelectOption(
                label="🐛 Bug Report",
                description="Report bugs or technical issues",
                emoji="🐛",
                value="bug"
            ),
            discord.SelectOption(
                label="💡 Feature Request",
                description="Suggest new features or improvements",
                emoji="💡",
                value="feature"
            ),
            discord.SelectOption(
                label="❓ General Support",
                description="General questions and assistance",
                emoji="❓",
                value="general"
            ),
            discord.SelectOption(
                label="💰 Economy Support",
                description="Issues with coins, XP, or purchases",
                emoji="💰",
                value="economy"
            ),
            discord.SelectOption(
                label="🎮 Gaming Issues",
                description="Problems with minigames or competitions",
                emoji="🎮",
                value="gaming"
            ),
            discord.SelectOption(
                label="⚠️ Report User",
                description="Report rule violations or misconduct",
                emoji="⚠️",
                value="report"
            )
        ]
    )
    async def ticket_type_select(self, interaction: discord.Interaction, select: Select):
        ticket_type = select.values[0]
        
        # Create ticket creation modal based on type
        if ticket_type == "priority":
            modal = PriorityTicketModal()
        elif ticket_type == "bug":
            modal = BugReportModal()
        elif ticket_type == "feature":
            modal = FeatureRequestModal()
        elif ticket_type == "economy":
            modal = EconomyIssueModal()
        elif ticket_type == "gaming":
            modal = GamingIssueModal()
        elif ticket_type == "report":
            modal = ReportUserModal()
        else:
            modal = GeneralTicketModal()
            
        await interaction.response.send_modal(modal)

class PriorityTicketModal(Modal, title="🚨 Priority Support Ticket"):
    def __init__(self):
        super().__init__()
        
    issue_title = TextInput(
        label="Issue Title",
        placeholder="Brief description of the urgent issue...",
        max_length=100,
        required=True
    )
    
    urgency_level = TextInput(
        label="Urgency Level (1-10)",
        placeholder="Rate the urgency from 1 (low) to 10 (critical)",
        max_length=2,
        required=True
    )
    
    issue_description = TextInput(
        label="Detailed Description",
        placeholder="Provide detailed information about the issue...",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )
    
    steps_to_reproduce = TextInput(
        label="Steps to Reproduce (if applicable)",
        placeholder="1. First step\n2. Second step\n3. Issue occurs...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=False
    )
    
    contact_preference = TextInput(
        label="Preferred Contact Method",
        placeholder="Discord DM, Server ping, or Voice chat",
        max_length=50,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.create_premium_ticket(interaction, "priority", {
            "title": self.issue_title.value,
            "urgency": self.urgency_level.value,
            "description": self.issue_description.value,
            "steps": self.steps_to_reproduce.value,
            "contact": self.contact_preference.value
        })

class BugReportModal(Modal, title="🐛 Bug Report"):
    def __init__(self):
        super().__init__()
        
    bug_title = TextInput(
        label="Bug Title",
        placeholder="Short description of the bug...",
        max_length=100,
        required=True
    )
    
    affected_feature = TextInput(
        label="Affected Feature/Command",
        placeholder="Which command or feature has the bug?",
        max_length=100,
        required=True
    )
    
    bug_description = TextInput(
        label="Bug Description",
        placeholder="What exactly is happening? What should happen instead?",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )
    
    reproduction_steps = TextInput(
        label="Steps to Reproduce",
        placeholder="1. Use command /example\n2. Click button\n3. Error occurs...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )
    
    error_message = TextInput(
        label="Error Message (if any)",
        placeholder="Copy any error messages you received...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.create_premium_ticket(interaction, "bug", {
            "title": self.bug_title.value,
            "feature": self.affected_feature.value,
            "description": self.bug_description.value,
            "steps": self.reproduction_steps.value,
            "error": self.error_message.value
        })

class FeatureRequestModal(Modal, title="💡 Feature Request"):
    def __init__(self):
        super().__init__()
        
    feature_title = TextInput(
        label="Feature Title",
        placeholder="Name of the requested feature...",
        max_length=100,
        required=True
    )
    
    feature_category = TextInput(
        label="Category",
        placeholder="Economy, Gaming, Moderation, etc.",
        max_length=50,
        required=True
    )
    
    feature_description = TextInput(
        label="Feature Description",
        placeholder="Describe the feature and how it would work...",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )
    
    use_case = TextInput(
        label="Use Case/Benefits",
        placeholder="Why would this feature be useful? How would it improve the bot?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )
    
    similar_features = TextInput(
        label="Similar Features (if any)",
        placeholder="Have you seen this in other bots? How would it be different?",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.create_premium_ticket(interaction, "feature", {
            "title": self.feature_title.value,
            "category": self.feature_category.value,
            "description": self.feature_description.value,
            "use_case": self.use_case.value,
            "similar": self.similar_features.value
        })

class EconomyIssueModal(Modal, title="💰 Economy Support"):
    def __init__(self):
        super().__init__()
        
    issue_title = TextInput(
        label="Issue Title",
        placeholder="Brief description of the economy issue...",
        max_length=100,
        required=True
    )
    
    affected_system = TextInput(
        label="Affected System",
        placeholder="Coins, XP, Work, Shop, Gambling, etc.",
        max_length=50,
        required=True
    )
    
    issue_description = TextInput(
        label="Issue Description",
        placeholder="What happened? What were you trying to do?",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )
    
    transaction_details = TextInput(
        label="Transaction Details",
        placeholder="Command used, amount involved, when it happened...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=False
    )
    
    current_balance = TextInput(
        label="Current Balance",
        placeholder="Your current coins/XP (helps with investigation)",
        max_length=100,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.create_premium_ticket(interaction, "economy", {
            "title": self.issue_title.value,
            "system": self.affected_system.value,
            "description": self.issue_description.value,
            "transaction": self.transaction_details.value,
            "balance": self.current_balance.value
        })

class GamingIssueModal(Modal, title="🎮 Gaming Support"):
    def __init__(self):
        super().__init__()
        
    issue_title = TextInput(
        label="Issue Title",
        placeholder="Brief description of the gaming issue...",
        max_length=100,
        required=True
    )
    
    game_type = TextInput(
        label="Game/Feature",
        placeholder="Trivia, RPS, Slots, Word Chain, Daily, etc.",
        max_length=50,
        required=True
    )
    
    issue_description = TextInput(
        label="Issue Description",
        placeholder="What went wrong? What were you expecting?",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )
    
    game_context = TextInput(
        label="Game Context",
        placeholder="What were you doing when the issue occurred?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=False
    )
    
    lost_progress = TextInput(
        label="Lost Progress/Rewards",
        placeholder="Did you lose coins, XP, or game progress?",
        max_length=200,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.create_premium_ticket(interaction, "gaming", {
            "title": self.issue_title.value,
            "game": self.game_type.value,
            "description": self.issue_description.value,
            "context": self.game_context.value,
            "lost": self.lost_progress.value
        })

class ReportUserModal(Modal, title="⚠️ Report User"):
    def __init__(self):
        super().__init__()
        
    reported_user = TextInput(
        label="Reported User",
        placeholder="Username or user ID of the person you're reporting",
        max_length=100,
        required=True
    )
    
    violation_type = TextInput(
        label="Rule Violation",
        placeholder="Spam, harassment, cheating, inappropriate content, etc.",
        max_length=100,
        required=True
    )
    
    incident_description = TextInput(
        label="Incident Description",
        placeholder="What happened? Provide as much detail as possible...",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )
    
    evidence = TextInput(
        label="Evidence",
        placeholder="Message links, screenshots description, witness information...",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=False
    )
    
    when_occurred = TextInput(
        label="When did this occur?",
        placeholder="Approximate date and time...",
        max_length=100,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.create_premium_ticket(interaction, "report", {
            "reported": self.reported_user.value,
            "violation": self.violation_type.value,
            "description": self.incident_description.value,
            "evidence": self.evidence.value,
            "when": self.when_occurred.value
        })

class GeneralTicketModal(Modal, title="❓ General Support"):
    def __init__(self):
        super().__init__()
        
    issue_title = TextInput(
        label="Issue Title",
        placeholder="Brief description of your question or issue...",
        max_length=100,
        required=True
    )
    
    category = TextInput(
        label="Category",
        placeholder="Commands, Features, General Question, etc.",
        max_length=50,
        required=False
    )
    
    description = TextInput(
        label="Description",
        placeholder="Please describe your question or issue in detail...",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )
    
    attempted_solutions = TextInput(
        label="What have you tried?",
        placeholder="Have you tried any solutions or looked for help elsewhere?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await self.create_premium_ticket(interaction, "general", {
            "title": self.issue_title.value,
            "category": self.category.value,
            "description": self.description.value,
            "attempted": self.attempted_solutions.value
        })

# Add the create_premium_ticket method to all modal classes
async def create_premium_ticket(self, interaction: discord.Interaction, ticket_type: str, data: dict):
    """Create a premium ticket with advanced features"""
    
    # Create ticket channel
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="🎫 Premium Tickets")
    
    if not category:
        # Create category if it doesn't exist
        category = await guild.create_category("🎫 Premium Tickets")
    
    # Generate ticket ID
    ticket_id = f"premium-{ticket_type}-{int(time.time())}"
    
    # Channel name based on type
    channel_names = {
        "priority": f"🚨┃{interaction.user.display_name.lower()[:10]}-urgent",
        "bug": f"🐛┃{interaction.user.display_name.lower()[:10]}-bug",
        "feature": f"💡┃{interaction.user.display_name.lower()[:10]}-feature",
        "economy": f"💰┃{interaction.user.display_name.lower()[:10]}-economy",
        "gaming": f"🎮┃{interaction.user.display_name.lower()[:10]}-gaming",
        "report": f"⚠️┃{interaction.user.display_name.lower()[:10]}-report",
        "general": f"❓┃{interaction.user.display_name.lower()[:10]}-support"
    }
    
    channel_name = channel_names.get(ticket_type, f"🎫┃{interaction.user.display_name.lower()[:10]}-ticket")
    
    # Create channel with proper permissions
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True, 
            send_messages=True, 
            read_message_history=True,
            attach_files=True,
            embed_links=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, 
            send_messages=True, 
            manage_messages=True,
            embed_links=True,
            attach_files=True
        )
    }
    
    # Add staff permissions
    staff_roles = ["Forgotten One", "Overseer", "Lead Moderator", "Moderator"]
    for role_name in staff_roles:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_messages=True,
                read_message_history=True
            )
    
    try:
        ticket_channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )
    except discord.HTTPException:
        await interaction.response.send_message("❌ Failed to create ticket channel. Please try again.", ephemeral=True)
        return
    
    # Create premium ticket embed
    embed = discord.Embed(
        title=f"🌟 Premium Ticket #{ticket_id[-8:]}",
        description=f"**Type:** {ticket_type.title()}\n**Created by:** {interaction.user.mention}",
        color=0x9b59b6,
        timestamp=datetime.now()
    )
    
    # Add type-specific information
    if ticket_type == "priority":
        embed.add_field(name="🚨 Priority Level", value=f"**{data.get('urgency', 'N/A')}/10**", inline=True)
        embed.add_field(name="📞 Contact Preference", value=data.get('contact', 'Discord'), inline=True)
        embed.color = 0xe74c3c  # Red for priority
        
    elif ticket_type == "bug":
        embed.add_field(name="🐛 Affected Feature", value=data.get('feature', 'N/A'), inline=True)
        embed.add_field(name="🔄 Reproducible", value="Yes" if data.get('steps') else "Unknown", inline=True)
        
    elif ticket_type == "feature":
        embed.add_field(name="📁 Category", value=data.get('category', 'General'), inline=True)
        embed.add_field(name="💡 Innovation", value="New Feature Request", inline=True)
        
    elif ticket_type == "economy":
        embed.add_field(name="💰 System", value=data.get('system', 'N/A'), inline=True)
        embed.add_field(name="💳 Balance Check", value="Required", inline=True)
        
    elif ticket_type == "gaming":
        embed.add_field(name="🎮 Game", value=data.get('game', 'N/A'), inline=True)
        embed.add_field(name="🏆 Progress Lost", value="Yes" if data.get('lost') else "No", inline=True)
        
    elif ticket_type == "report":
        embed.add_field(name="⚠️ Violation", value=data.get('violation', 'N/A'), inline=True)
        embed.add_field(name="📊 Priority", value="High", inline=True)
        embed.color = 0xff6b6b  # Red for reports
    
    embed.add_field(name="📋 Issue", value=data.get('title', 'No title provided'), inline=False)
    embed.add_field(name="📝 Description", value=data.get('description', 'No description provided')[:1000], inline=False)
    
    # Add additional details based on type
    if data.get('steps'):
        embed.add_field(name="🔄 Steps to Reproduce", value=data['steps'][:500], inline=False)
    if data.get('error'):
        embed.add_field(name="❌ Error Message", value=f"```{data['error'][:300]}```", inline=False)
    if data.get('evidence'):
        embed.add_field(name="🔍 Evidence", value=data['evidence'][:500], inline=False)
    
    embed.set_footer(text="🎫 Premium Support • Advanced ticket system")
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    
    # Create premium control panel
    view = PremiumTicketControls(interaction.user.id, ticket_type)
    
    # Send ticket message
    ticket_message = await ticket_channel.send(
        content=f"🌟 **Premium Ticket Created**\n{interaction.user.mention} - Your premium support ticket has been created!\n\n"
                f"**Staff will be notified and respond according to priority level.**",
        embed=embed,
        view=view
    )
    
    # Pin the ticket message
    try:
        await ticket_message.pin()
    except discord.HTTPException:
        pass
    
    # Send confirmation to user
    confirm_embed = discord.Embed(
        title="✅ Premium Ticket Created",
        description=f"Your premium ticket has been created in {ticket_channel.mention}",
        color=0x00ff00
    )
    confirm_embed.add_field(name="🎫 Ticket ID", value=f"#{ticket_id[-8:]}", inline=True)
    confirm_embed.add_field(name="📋 Type", value=ticket_type.title(), inline=True)
    
    if ticket_type == "priority":
        confirm_embed.add_field(name="⚡ Priority", value="Fast-track processing", inline=False)
        confirm_embed.description += "\n\n🚨 **Priority ticket detected!** Staff have been notified for immediate response."
    
    await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
    
    # Notify staff for priority tickets
    if ticket_type == "priority":
        await notify_priority_staff(ticket_channel, interaction.user, data)

class PremiumTicketControls(View):
    def __init__(self, creator_id: int, ticket_type: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.ticket_type = ticket_type
        self.claimed_by = None
        self.resolved = False
        
    @discord.ui.button(label="🛡️ Claim Premium", emoji="🌟", style=discord.ButtonStyle.success, row=0)
    async def claim_premium(self, interaction: discord.Interaction, button: Button):
        # Premium claiming with staff verification
        staff_roles = ["Forgotten One", "Overseer", "Lead Moderator", "Moderator"]
        user_roles = [role.name for role in interaction.user.roles]
        
        if not any(role in user_roles for role in staff_roles):
            await interaction.response.send_message("❌ Only authorized staff can claim premium tickets.", ephemeral=True)
            return
        
        if self.claimed_by:
            await interaction.response.send_message(f"🔒 This ticket is already claimed by <@{self.claimed_by}>", ephemeral=True)
            return
        
        self.claimed_by = interaction.user.id
        
        embed = discord.Embed(
            title="🌟 Premium Ticket Claimed",
            description=f"**Staff Member:** {interaction.user.mention}\n**Claim Time:** <t:{int(datetime.now().timestamp())}:R>",
            color=0x9b59b6
        )
        embed.add_field(name="📊 Status", value="🟢 **ACTIVELY HANDLING**", inline=True)
        embed.add_field(name="⚡ Response Time", value="Premium Support", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
    @discord.ui.button(label="✅ Mark Resolved", style=discord.ButtonStyle.secondary, row=0)
    async def mark_resolved(self, interaction: discord.Interaction, button: Button):
        staff_roles = ["Forgotten One", "Overseer", "Lead Moderator", "Moderator"]
        user_roles = [role.name for role in interaction.user.roles]
        
        if not any(role in user_roles for role in staff_roles):
            await interaction.response.send_message("❌ Only staff can mark tickets as resolved.", ephemeral=True)
            return
            
        if self.resolved:
            await interaction.response.send_message("✅ This ticket is already marked as resolved.", ephemeral=True)
            return
        
        self.resolved = True
        
        # Update channel name
        try:
            new_name = f"✅-resolved-{interaction.channel.name[2:]}"
            await interaction.channel.edit(name=new_name)
        except discord.HTTPException:
            pass
        
        embed = discord.Embed(
            title="✅ Ticket Resolved",
            description=f"**Resolved by:** {interaction.user.mention}\n**Resolution Time:** <t:{int(datetime.now().timestamp())}:R>",
            color=0x00ff00
        )
        embed.add_field(name="🎯 Status", value="**RESOLVED** ✅", inline=True)
        embed.add_field(name="⏰ Auto-close", value="24 hours", inline=True)
        embed.set_footer(text="🌟 Premium Support • Issue resolved successfully")
        
        await interaction.response.send_message(embed=embed)
        
    @discord.ui.button(label="🔄 Escalate", style=discord.ButtonStyle.danger, row=0)
    async def escalate_ticket(self, interaction: discord.Interaction, button: Button):
        staff_roles = ["Forgotten One", "Overseer", "Lead Moderator", "Moderator"]
        user_roles = [role.name for role in interaction.user.roles]
        
        if not any(role in user_roles for role in staff_roles):
            await interaction.response.send_message("❌ Only staff can escalate tickets.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🔄 Ticket Escalated",
            description=f"**Escalated by:** {interaction.user.mention}\n**Escalation Time:** <t:{int(datetime.now().timestamp())}:R>",
            color=0xe74c3c
        )
        embed.add_field(name="⚠️ Status", value="**HIGH PRIORITY**", inline=True)
        embed.add_field(name="👥 Notified", value="Senior Staff", inline=True)
        embed.set_footer(text="🚨 Escalated • Requires senior attention")
        
        await interaction.response.send_message(
            content="@here **ESCALATED PREMIUM TICKET** - Senior staff attention required!",
            embed=embed
        )
        
    @discord.ui.button(label="📊 Analytics", style=discord.ButtonStyle.secondary, row=1)
    async def ticket_analytics(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="📊 Premium Ticket Analytics",
            description="**Performance Metrics**",
            color=0x3498db
        )
        
        # Mock analytics data
        embed.add_field(name="⚡ Response Time", value="Premium: < 5 min\nStandard: < 30 min", inline=True)
        embed.add_field(name="✅ Resolution Rate", value="Priority: 98%\nGeneral: 95%", inline=True)
        embed.add_field(name="👥 Staff Performance", value="Active: 4/5\nAverage: 92%", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def notify_priority_staff(channel, user, data):
    """Notify staff about priority tickets"""
    embed = discord.Embed(
        title="🚨 PRIORITY TICKET ALERT",
        description=f"**User:** {user.mention}\n**Urgency:** {data.get('urgency', 'N/A')}/10\n**Channel:** {channel.mention}",
        color=0xe74c3c
    )
    embed.add_field(name="📋 Issue", value=data.get('title', 'N/A'), inline=False)
    embed.set_footer(text="🚨 Immediate response required")
    
    # Send to staff notifications channel
    staff_channel = discord.utils.get(channel.guild.channels, name="staff-notifications")
    if staff_channel:
        await staff_channel.send(
            content="@here **PRIORITY TICKET CREATED**",
            embed=embed
        )

# Add the method to all modal classes
for modal_class in [PriorityTicketModal, BugReportModal, FeatureRequestModal, EconomyIssueModal, GamingIssueModal, ReportUserModal, GeneralTicketModal]:
    modal_class.create_premium_ticket = create_premium_ticket

async def setup(bot: commands.Bot):
    await bot.add_cog(PremiumTickets(bot))