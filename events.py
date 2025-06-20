import discord
from discord.ext import commands
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Welcome Message ---
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Ignore bots joining
        if member.bot:
            return

        # --- Auto-role assignment ---
        try:
            role_id = 1384141744303636610  # The "OPS ✋🏻" role
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role, reason="Automatic role on join")
            else:
                print(f"Warning: Auto-role with ID {role_id} not found in guild {member.guild.name}.")
        except discord.Forbidden:
            print(f"Error: Bot lacks 'Manage Roles' permission in {member.guild.name}.")
        except Exception as e:
            print(f"An error occurred during auto-role assignment for {member.name}: {e}")


        # --- Welcome Message ---
        welcome_channel_id = db.get_channel(member.guild.id, "welcome")
        if welcome_channel_id:
            welcome_channel = member.guild.get_channel(welcome_channel_id)
            if welcome_channel:
                embed = discord.Embed(
                    title=f"Welcome to {member.guild.name}!",
                    description=f"Hello {member.mention}, we're glad to have you here.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"You are member #{member.guild.member_count}")
                await welcome_channel.send(embed=embed)


    # --- Leave Message ---
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return

        # Get the leave channel from the database
        leave_channel_id = db.get_channel(member.guild.id, "leave")
        if not leave_channel_id:
            return

        leave_channel = member.guild.get_channel(leave_channel_id)
        if not leave_channel:
            return

        embed = discord.Embed(
            title="Goodbye!",
            description=f"{member.display_name} has left the server.",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await leave_channel.send(embed=embed)

    # --- Message Delete Log ---
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Ignore partial messages, DMs, and bot messages
        if not message.guild or message.author.bot:
            return

        log_channel_id = db.get_channel(message.guild.id, "log")
        if not log_channel_id:
            return

        log_channel = message.guild.get_channel(log_channel_id)
        if not log_channel:
            return
            
        embed = discord.Embed(
            title="Message Deleted",
            description=f"A message from **{message.author.mention}** was deleted in **{message.channel.mention}**.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        # Add content if it exists
        if message.content:
            embed.add_field(name="Content", value=f"```{message.content}```", inline=False)
        embed.set_footer(text=f"Author ID: {message.author.id} | Message ID: {message.id}")

        await log_channel.send(embed=embed)

    # --- Message Edit Log ---
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Ignore messages with no content change, DMs, and bot messages
        if not after.guild or after.author.bot or before.content == after.content:
            return

        log_channel_id = db.get_channel(after.guild.id, "log")
        if not log_channel_id:
            return

        log_channel = after.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="Message Edited",
            description=f"**{after.author.mention}** edited a message in **{after.channel.mention}**.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Original", value=f"```{before.content}```", inline=False)
        embed.add_field(name="Edited", value=f"```{after.content}```", inline=False)
        embed.add_field(name="Go to message", value=f"[Click here]({after.jump_url})", inline=False)
        embed.set_footer(text=f"Author ID: {after.author.id} | Message ID: {after.id}")
        
        await log_channel.send(embed=embed)

    # --- Role Create/Delete Logs ---
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        log_channel_id = db.get_channel(role.guild.id, "log")
        if not log_channel_id:
            return

        log_channel = role.guild.get_channel(log_channel_id)
        if not log_channel:
            return
            
        embed = discord.Embed(
            title="Role Created",
            description=f"The role **{role.name}** was created.",
            color=discord.Color.teal(),
            timestamp=datetime.utcnow()
        )
        await log_channel.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        log_channel_id = db.get_channel(role.guild.id, "log")
        if not log_channel_id:
            return

        log_channel = role.guild.get_channel(log_channel_id)
        if not log_channel:
            return
            
        embed = discord.Embed(
            title="Role Deleted",
            description=f"The role **{role.name}** was deleted.",
            color=discord.Color.dark_teal(),
            timestamp=datetime.utcnow()
        )
        await log_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Events(bot))
