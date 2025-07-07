import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime
import os, sys
import asyncio

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from permissions import has_special_permissions

class CoolTicketControls(View):
    def __init__(self, creator_id: int, category: str, subcategory: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.category = category
        self.subcategory = subcategory
        self.claimed_by = None
        self.is_closed = False

    def has_permissions(self, user, guild):
        """Check if user has ticket permissions"""
        # Ticket creator
        if user.id == self.creator_id:
            return True
        # Admin permissions
        if user.guild_permissions.administrator or user.guild_permissions.manage_channels:
            return True
        # Special admin role
        if has_special_permissions(user):
            return True
        # Support roles
        server_settings = db.get_server_settings(guild.id)
        support_roles = server_settings.get('ticket_support_roles', [])
        for role in user.roles:
            if role.id in support_roles or any(name in role.name.lower() for name in ["admin", "mod", "staff", "support"]):
                return True
        return False

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.success, emoji="🎯")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ Only staff can claim tickets!", ephemeral=True)
            return

        if self.claimed_by:
            await interaction.response.send_message(f"❌ Already claimed by **{self.claimed_by}**!", ephemeral=True)
            return

        # Simple channel rename
        channel = interaction.channel
        clean_name = interaction.user.display_name.lower().replace(' ', '')[:10]
        new_name = f"claimed-by-{clean_name}"
        
        try:
            await channel.edit(name=new_name)
        except:
            pass

        self.claimed_by = interaction.user.display_name
        
        # Update buttons
        button.label = f"Claimed by {interaction.user.display_name}"
        button.disabled = True
        button.style = discord.ButtonStyle.secondary
        
        # Add unclaim button
        unclaim_btn = discord.ui.Button(label="Unclaim", style=discord.ButtonStyle.danger, emoji="🔓")
        async def unclaim_callback(unclaim_interaction):
            if unclaim_interaction.user.id != interaction.user.id and not self.has_permissions(unclaim_interaction.user, unclaim_interaction.guild):
                await unclaim_interaction.response.send_message("❌ Only the claimer can unclaim!", ephemeral=True)
                return
            
            # Restore original name
            original_user = interaction.client.get_user(self.creator_id)
            if original_user:
                original_name = original_user.display_name.lower().replace(' ', '')[:10]
                restore_name = f"ticket-{original_name}-{self.creator_id}"
            else:
                restore_name = f"ticket-{self.creator_id}"
            
            try:
                await channel.edit(name=restore_name)
            except:
                pass
            
            self.claimed_by = None
            button.label = "Claim"
            button.disabled = False
            button.style = discord.ButtonStyle.success
            self.remove_item(unclaim_btn)
            
            embed = discord.Embed(
                title="🔓 **Ticket Unclaimed**",
                description=f"**{unclaim_interaction.user.display_name}** unclaimed this ticket.",
                color=0xffa500
            )
            await unclaim_interaction.response.edit_message(embed=embed, view=self)
        
        unclaim_btn.callback = unclaim_callback
        self.add_item(unclaim_btn)

        embed = discord.Embed(
            title="🎯 **Ticket Claimed**",
            description=f"**{interaction.user.display_name}** is now handling this ticket!",
            color=0x00d4aa,
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Staff Member", value=interaction.user.mention, inline=True)
        embed.add_field(name="⏰ Claimed At", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ Only staff or ticket creator can close!", ephemeral=True)
            return

        if self.is_closed:
            await interaction.response.send_message("❌ Ticket is already closed!", ephemeral=True)
            return

        # Create confirmation
        confirm_view = QuickConfirmView()
        await interaction.response.send_message(
            "⚠️ **Close this ticket?** This will archive the channel.",
            view=confirm_view,
            ephemeral=True
        )
        
        if await confirm_view.wait():
            return

        if confirm_view.value:
            self.is_closed = True
            
            # Update buttons
            button.label = "Closed"
            button.disabled = True
            button.style = discord.ButtonStyle.secondary
            
            # Add reopen button
            reopen_btn = discord.ui.Button(label="Reopen", style=discord.ButtonStyle.success, emoji="🔄")
            async def reopen_callback(reopen_interaction):
                if not self.has_permissions(reopen_interaction.user, reopen_interaction.guild):
                    await reopen_interaction.response.send_message("❌ Only staff can reopen!", ephemeral=True)
                    return
                
                self.is_closed = False
                button.label = "Close"
                button.disabled = False
                button.style = discord.ButtonStyle.danger
                self.remove_item(reopen_btn)
                
                embed = discord.Embed(
                    title="🔄 **Ticket Reopened**",
                    description=f"**{reopen_interaction.user.display_name}** reopened this ticket.",
                    color=0x00d4aa
                )
                await reopen_interaction.response.edit_message(embed=embed, view=self)
            
            reopen_btn.callback = reopen_callback
            self.add_item(reopen_btn)

            embed = discord.Embed(
                title="🔒 **Ticket Closed**",
                description=f"Ticket closed by **{interaction.user.display_name}**",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ Only staff can delete tickets!", ephemeral=True)
            return

        # Final confirmation
        confirm_view = QuickConfirmView()
        await interaction.response.send_message(
            "⚠️ **PERMANENTLY DELETE** this ticket? **This cannot be undone!**",
            view=confirm_view,
            ephemeral=True
        )
        
        if await confirm_view.wait():
            return

        if confirm_view.value:
            embed = discord.Embed(
                title="🗑️ **Ticket Deleted**",
                description=f"Ticket deleted by {interaction.user.mention}\n\n🕒 Channel will be deleted in 5 seconds...",
                color=0x8b0000
            )
            await interaction.edit_original_response(embed=embed, view=None)
            
            # Log deletion
            try:
                db.log_ticket_deletion(interaction.guild.id, interaction.user.id, interaction.channel.id)
            except:
                pass
            
            await asyncio.sleep(5)
            try:
                await interaction.channel.delete(reason=f"Ticket deleted by {interaction.user.display_name}")
            except:
                pass

    @discord.ui.button(label="Priority", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def update_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message("❌ Only staff can update priority!", ephemeral=True)
            return

        priority_view = PrioritySelectView()
        await interaction.response.send_message("🎯 **Select Priority Level:**", view=priority_view, ephemeral=True)

class QuickConfirmView(View):
    def __init__(self):
        super().__init__(timeout=30)
        self.value = None

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.send_message("❌ **Cancelled**", ephemeral=True)
        self.stop()

class PrioritySelectView(View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="🟢 Low", style=discord.ButtonStyle.success)
    async def low_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Low", 0x28a745, "🟢")

    @discord.ui.button(label="🟡 Medium", style=discord.ButtonStyle.secondary)
    async def medium_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Medium", 0xffc107, "🟡")

    @discord.ui.button(label="🟠 High", style=discord.ButtonStyle.secondary)
    async def high_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "High", 0xff6b6b, "🟠")

    @discord.ui.button(label="🔴 Urgent", style=discord.ButtonStyle.danger)
    async def urgent_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_priority(interaction, "Urgent", 0xdc3545, "🔴")

    async def update_priority(self, interaction: discord.Interaction, priority: str, color: int, emoji: str):
        embed = discord.Embed(
            title=f"{emoji} **Priority: {priority}**",
            description=f"Ticket priority updated to **{priority}** by {interaction.user.mention}",
            color=color,
            timestamp=datetime.now()
        )
        
        # Update channel topic
        try:
            channel = interaction.channel
            current_topic = channel.topic or ""
            # Simple topic update
            new_topic = f"{emoji} {priority} Priority • {current_topic.split('•', 1)[-1].strip() if '•' in current_topic else current_topic}"
            await channel.edit(topic=new_topic[:1024])  # Discord limit
        except:
            pass
        
        await interaction.response.send_message(embed=embed)