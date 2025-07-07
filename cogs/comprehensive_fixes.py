import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput, Select
from datetime import datetime, timedelta
import os, sys
import asyncio
import random

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

# COMPREHENSIVE JOB SYSTEM - ALL SIMPLE EMOJIS ONLY
COMPREHENSIVE_JOBS = {
    "entry": {
        "name": "Entry Level",
        "unlock_requirement": 0,
        "promotion_requirement": 15,
        "jobs": [
            {"name": "Pizza Delivery", "emoji": "🍕", "min_pay": 15, "max_pay": 30, "description": "delivering hot pizzas", "skill": "delivery"},
            {"name": "Data Entry", "emoji": "📋", "min_pay": 20, "max_pay": 35, "description": "entering data accurately", "skill": "admin"},
            {"name": "Customer Support", "emoji": "📞", "min_pay": 18, "max_pay": 32, "description": "helping customers", "skill": "support"},
            {"name": "Cashier", "emoji": "💰", "min_pay": 16, "max_pay": 28, "description": "handling transactions", "skill": "retail"},
            {"name": "Cleaner", "emoji": "🧹", "min_pay": 14, "max_pay": 25, "description": "maintaining cleanliness", "skill": "maintenance"},
            {"name": "Stock Clerk", "emoji": "📦", "min_pay": 17, "max_pay": 30, "description": "organizing inventory", "skill": "warehouse"}
        ]
    },
    "junior": {
        "name": "Junior Level", 
        "unlock_requirement": 15,
        "promotion_requirement": 35,
        "jobs": [
            {"name": "Junior Developer", "emoji": "💻", "min_pay": 25, "max_pay": 50, "description": "writing simple code", "skill": "development"},
            {"name": "Content Creator", "emoji": "📝", "min_pay": 30, "max_pay": 55, "description": "creating engaging content", "skill": "creative"},
            {"name": "Sales Associate", "emoji": "💼", "min_pay": 28, "max_pay": 45, "description": "selling products", "skill": "sales"},
            {"name": "Graphic Designer", "emoji": "🎨", "min_pay": 32, "max_pay": 52, "description": "designing visuals", "skill": "creative"},
            {"name": "Lab Assistant", "emoji": "⚗️", "min_pay": 26, "max_pay": 48, "description": "assisting with research", "skill": "science"},
            {"name": "Bookkeeper", "emoji": "📊", "min_pay": 29, "max_pay": 47, "description": "maintaining financial records", "skill": "finance"}
        ]
    },
    "mid": {
        "name": "Mid Level",
        "unlock_requirement": 50,
        "promotion_requirement": 85,
        "jobs": [
            {"name": "Software Developer", "emoji": "🔨", "min_pay": 40, "max_pay": 80, "description": "developing applications", "skill": "development"},
            {"name": "Marketing Specialist", "emoji": "📈", "min_pay": 45, "max_pay": 75, "description": "promoting products", "skill": "marketing"},
            {"name": "Project Coordinator", "emoji": "📋", "min_pay": 50, "max_pay": 85, "description": "coordinating projects", "skill": "management"},
            {"name": "UX Designer", "emoji": "🖌️", "min_pay": 48, "max_pay": 82, "description": "designing user experiences", "skill": "design"},
            {"name": "Business Analyst", "emoji": "📊", "min_pay": 46, "max_pay": 78, "description": "analyzing business processes", "skill": "analysis"},
            {"name": "Network Admin", "emoji": "🌐", "min_pay": 52, "max_pay": 88, "description": "managing networks", "skill": "technical"}
        ]
    },
    "senior": {
        "name": "Senior Level",
        "unlock_requirement": 135,
        "promotion_requirement": 200,
        "jobs": [
            {"name": "Senior Engineer", "emoji": "🔧", "min_pay": 70, "max_pay": 120, "description": "architecting solutions", "skill": "engineering"},
            {"name": "Team Lead", "emoji": "👥", "min_pay": 80, "max_pay": 130, "description": "leading teams", "skill": "leadership"},
            {"name": "Product Manager", "emoji": "🎯", "min_pay": 85, "max_pay": 140, "description": "managing products", "skill": "strategy"},
            {"name": "Data Scientist", "emoji": "📊", "min_pay": 75, "max_pay": 125, "description": "analyzing big data", "skill": "data"},
            {"name": "Solutions Architect", "emoji": "🏗️", "min_pay": 88, "max_pay": 145, "description": "designing system architecture", "skill": "architecture"},
            {"name": "Security Specialist", "emoji": "🔒", "min_pay": 82, "max_pay": 135, "description": "ensuring system security", "skill": "security"}
        ]
    },
    "executive": {
        "name": "Executive Level",
        "unlock_requirement": 335,
        "promotion_requirement": 500,
        "jobs": [
            {"name": "Engineering Director", "emoji": "⚙️", "min_pay": 120, "max_pay": 200, "description": "directing engineering", "skill": "leadership"},
            {"name": "VP of Product", "emoji": "🚀", "min_pay": 150, "max_pay": 250, "description": "leading product innovation", "skill": "strategy"},
            {"name": "CTO", "emoji": "👑", "min_pay": 200, "max_pay": 350, "description": "setting technology vision", "skill": "executive"},
            {"name": "Head of Marketing", "emoji": "📢", "min_pay": 130, "max_pay": 220, "description": "leading marketing strategy", "skill": "marketing"},
            {"name": "Operations Director", "emoji": "📊", "min_pay": 125, "max_pay": 210, "description": "overseeing operations", "skill": "operations"},
            {"name": "Chief Architect", "emoji": "🏛️", "min_pay": 140, "max_pay": 240, "description": "defining system architecture", "skill": "architecture"}
        ]
    },
    "legendary": {
        "name": "Legendary Status",
        "unlock_requirement": 835,
        "promotion_requirement": 9999,
        "jobs": [
            {"name": "Industry Innovator", "emoji": "💡", "min_pay": 300, "max_pay": 500, "description": "revolutionizing industries", "skill": "innovation"},
            {"name": "Tech Visionary", "emoji": "🌟", "min_pay": 400, "max_pay": 600, "description": "shaping technology future", "skill": "visionary"},
            {"name": "Global Leader", "emoji": "🌍", "min_pay": 500, "max_pay": 800, "description": "leading worldwide initiatives", "skill": "global"},
            {"name": "Enterprise Founder", "emoji": "🏢", "min_pay": 350, "max_pay": 550, "description": "founding new enterprises", "skill": "entrepreneurship"},
            {"name": "Innovation Catalyst", "emoji": "⚡", "min_pay": 450, "max_pay": 650, "description": "catalyzing breakthrough innovations", "skill": "catalyst"},
            {"name": "Digital Transformer", "emoji": "🔄", "min_pay": 380, "max_pay": 580, "description": "transforming digital landscapes", "skill": "transformation"}
        ]
    }
}

# Enhanced Ticket Priority System
class TicketPriorityView(View):
    def __init__(self, channel_id: int, user_id: int):
        super().__init__(timeout=300)
        self.channel_id = channel_id
        self.user_id = user_id

    def has_permissions(self, user):
        """Check if user can update priority"""
        if user.guild_permissions.manage_channels or user.guild_permissions.administrator:
            return True
        if has_special_permissions(user):
            return True
        # Check for support roles
        for role in user.roles:
            if any(name in role.name.lower() for name in ["admin", "mod", "staff", "support"]):
                return True
        return False

    @discord.ui.button(label="🟢 Low", style=discord.ButtonStyle.success, emoji="🟢")
    async def low_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Low", 0x28a745, "🟢")

    @discord.ui.button(label="🟡 Medium", style=discord.ButtonStyle.secondary, emoji="🟡")
    async def medium_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Medium", 0xffc107, "🟡")

    @discord.ui.button(label="🟠 High", style=discord.ButtonStyle.secondary, emoji="🟠")
    async def high_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "High", 0xff6b6b, "🟠")

    @discord.ui.button(label="🔴 Urgent", style=discord.ButtonStyle.danger, emoji="🔴")
    async def urgent_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Urgent", 0xdc3545, "🔴")

    async def update_priority(self, interaction: discord.Interaction, priority: str, color: int, emoji: str):
        if not self.has_permissions(interaction.user):
            await interaction.response.send_message("❌ Only staff can update ticket priority!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{emoji} **Priority Updated to {priority}**",
            description=f"**{interaction.user.display_name}** changed this ticket's priority to **{priority}**",
            color=color,
            timestamp=datetime.now()
        )
        
        embed.add_field(name="👤 Updated By", value=interaction.user.mention, inline=True)
        embed.add_field(name="⏰ Updated At", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
        embed.add_field(name="🎯 New Priority", value=f"{emoji} {priority}", inline=True)
        
        # Update channel topic with new priority
        try:
            channel = interaction.channel
            current_topic = channel.topic or ""
            # Remove old priority and add new one
            import re
            topic_without_priority = re.sub(r'🟢|🟡|🟠|🔴\s*(Low|Medium|High|Urgent)\s*Priority\s*•?\s*', '', current_topic)
            new_topic = f"{emoji} {priority} Priority • {topic_without_priority.strip()}"
            await channel.edit(topic=new_topic[:1024])  # Discord limit
        except:
            pass
        
        await interaction.response.send_message(embed=embed)

class ComprehensiveFixes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Comprehensive Fixes] Loaded successfully - all bugs should be fixed!")

    @app_commands.command(name="jobs", description="💼 View all available jobs, requirements, and career progression")
    @app_commands.describe(tier="Specific tier to view (optional)")
    @app_commands.choices(tier=[
        app_commands.Choice(name="Entry Level", value="entry"),
        app_commands.Choice(name="Junior Level", value="junior"),
        app_commands.Choice(name="Mid Level", value="mid"),
        app_commands.Choice(name="Senior Level", value="senior"),
        app_commands.Choice(name="Executive Level", value="executive"),
        app_commands.Choice(name="Legendary Status", value="legendary")
    ])
    async def view_jobs(self, interaction: discord.Interaction, tier: str = None):
        """View comprehensive job information"""
        try:
            # Get user's current job stats
            user_data = db.get_user_data(interaction.user.id)
            current_tier = user_data.get('job_tier', 'entry')
            successful_works = user_data.get('successful_works', 0)
            total_works = user_data.get('total_works', 0)
            work_streak = user_data.get('work_streak', 0)
            
            if tier:
                # Show specific tier
                tier_info = COMPREHENSIVE_JOBS[tier]
                embed = discord.Embed(
                    title=f"💼 **{tier_info['name']} Jobs**",
                    description=f"Comprehensive job information for {tier_info['name']}",
                    color=0x7c3aed,
                    timestamp=datetime.now()
                )
                
                # Requirements
                embed.add_field(
                    name="📋 **Requirements**",
                    value=f"**Unlock:** {tier_info['unlock_requirement']} successful works\n**Promotion:** {tier_info['promotion_requirement']} successful works",
                    inline=True
                )
                
                # Jobs in this tier
                job_list = []
                for job in tier_info['jobs']:
                    success_rate = self.calculate_success_rate(successful_works, tier)
                    job_list.append(f"{job['emoji']} **{job['name']}**\n   💰 {job['min_pay']}-{job['max_pay']} coins\n   📝 {job['description']}\n   🎯 {success_rate:.0%} success rate")
                
                embed.add_field(
                    name="💼 **Available Jobs**",
                    value="\n\n".join(job_list),
                    inline=False
                )
                
            else:
                # Show overview of all tiers
                embed = discord.Embed(
                    title="💼 **Complete Career Progression System**",
                    description="Your path to professional success! Work consistently to advance through tiers.",
                    color=0x7c3aed,
                    timestamp=datetime.now()
                )
                
                # User's current status
                current_tier_info = COMPREHENSIVE_JOBS[current_tier]
                embed.add_field(
                    name="📊 **Your Current Status**",
                    value=f"**Current Tier:** {current_tier_info['name']}\n**Successful Works:** {successful_works}\n**Work Streak:** {work_streak}\n**Success Rate:** {(successful_works / max(1, total_works) * 100):.1f}%",
                    inline=True
                )
                
                # All tiers overview
                tier_overview = []
                for tier_key, tier_data in COMPREHENSIVE_JOBS.items():
                    status = "✅" if successful_works >= tier_data['unlock_requirement'] else "🔒"
                    current = "👑" if tier_key == current_tier else ""
                    tier_overview.append(f"{status} {current} **{tier_data['name']}** - {tier_data['unlock_requirement']} works required ({len(tier_data['jobs'])} jobs)")
                
                embed.add_field(
                    name="🎯 **Career Tiers**",
                    value="\n".join(tier_overview),
                    inline=False
                )
                
                # Promotion info
                next_tier = self.get_next_tier(current_tier)
                if next_tier:
                    next_tier_info = COMPREHENSIVE_JOBS[next_tier]
                    works_needed = next_tier_info['unlock_requirement'] - successful_works
                    if works_needed > 0:
                        embed.add_field(
                            name="🚀 **Next Promotion**",
                            value=f"**Target:** {next_tier_info['name']}\n**Progress:** {successful_works}/{next_tier_info['unlock_requirement']}\n**Works Needed:** {works_needed}",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name="🎉 **Promotion Available!**",
                            value=f"You can advance to **{next_tier_info['name']}**!\nUse `/work` to trigger promotion.",
                            inline=True
                        )
            
            # Tips for success
            embed.add_field(
                name="💡 **Career Success Tips**",
                value="• **Work consistently** - Daily work builds streaks\n• **Avoid gaps** - Missing days can cause demotion\n• **Higher tiers** = Better pay but lower success rates\n• **Streaks matter** - Consecutive work improves success",
                inline=False
            )
            
            embed.set_footer(text="💼 Use /work to start earning and advancing your career!")
            embed.set_author(name=f"{interaction.user.display_name}'s Career Guide", icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error viewing jobs: {str(e)}", ephemeral=True)

    @app_commands.command(name="setpriority", description="⚡ Update ticket priority (Staff only)")
    async def set_priority(self, interaction: discord.Interaction):
        """Set ticket priority with buttons"""
        # Check if in a ticket channel
        if not interaction.channel.name.startswith('ticket-') and not interaction.channel.name.startswith('claimed-by-'):
            await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
            return
        
        # Check permissions
        if not (interaction.user.guild_permissions.manage_channels or 
                interaction.user.guild_permissions.administrator or
                has_special_permissions(interaction.user) or
                any(name in role.name.lower() for role in interaction.user.roles for name in ["admin", "mod", "staff", "support"])):
            await interaction.response.send_message("❌ Only staff can update ticket priority!", ephemeral=True)
            return
        
        view = TicketPriorityView(interaction.channel.id, interaction.user.id)
        
        embed = discord.Embed(
            title="⚡ **Update Ticket Priority**",
            description="Select the appropriate priority level for this ticket:",
            color=0x7c3aed
        )
        
        embed.add_field(
            name="🟢 **Low Priority**",
            value="Non-urgent issues, general questions",
            inline=True
        )
        
        embed.add_field(
            name="🟡 **Medium Priority**", 
            value="Standard support requests",
            inline=True
        )
        
        embed.add_field(
            name="🟠 **High Priority**",
            value="Important issues affecting functionality",
            inline=True
        )
        
        embed.add_field(
            name="🔴 **Urgent Priority**",
            value="Critical issues requiring immediate attention",
            inline=True
        )
        
        embed.set_footer(text="Click a button below to update the priority")
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def calculate_success_rate(self, successful_works: int, tier: str) -> float:
        """Calculate success rate for a specific tier"""
        base_rates = {
            "entry": 0.90,      # 90% for entry
            "junior": 0.80,     # 80% for junior
            "mid": 0.70,        # 70% for mid
            "senior": 0.60,     # 60% for senior
            "executive": 0.50,  # 50% for executive
            "legendary": 0.40   # 40% for legendary
        }
        
        base_rate = base_rates.get(tier, 0.75)
        
        # Experience bonus (up to 15% bonus)
        experience_bonus = min(0.15, successful_works * 0.002)
        
        return min(1.0, base_rate + experience_bonus)

    def get_next_tier(self, current_tier: str) -> str:
        """Get the next tier in progression"""
        tier_order = ["entry", "junior", "mid", "senior", "executive", "legendary"]
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except:
            pass
        return None

async def setup(bot):
    await bot.add_cog(ComprehensiveFixes(bot))