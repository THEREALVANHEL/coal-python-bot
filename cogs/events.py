import discord
from discord.ext import commands
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# --- Constants ---
AUTO_ROLE_ID = 1384141744303636610 # The ID of the 'OPS ✋🏻' role

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handles new members joining the server."""
        # --- Auto-role ---
        try:
            role = member.guild.get_role(AUTO_ROLE_ID)
            if role:
                await member.add_roles(role, reason="Automatic role assignment on join.")
        except discord.Forbidden:
            print(f"Error: Bot lacks permissions to assign the auto-role in {member.guild.name}.")
        except Exception as e:
            print(f"An error occurred during auto-role assignment: {e}")

        # --- Welcome Message ---
        welcome_channel_id = db.get_channel(member.guild.id, "welcome")
        if not welcome_channel_id:
            return # No welcome channel configured

        welcome_channel = member.guild.get_channel(welcome_channel_id)
        if not welcome_channel:
            return # Channel not found

        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=f"Glad to have you here, {member.mention}! Enjoy your stay.",
            color=discord.Color.brand_green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")

        try:
            await welcome_channel.send(embed=embed)
        except discord.Forbidden:
            print(f"Error: Bot lacks permissions to send welcome messages in {welcome_channel.name}.")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return

        log_channel_id = db.get_channel(message.guild.id, "log")
        if not log_channel_id:
            return

        log_channel = message.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        content = message.content if message.content else "No message content (e.g., an embed or attachment)."
        embed.add_field(name="Content", value=f"```{content}```", inline=False)
        embed.set_footer(text=f"Author ID: {message.author.id} | Message ID: {message.id}")

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild or before.content == after.content:
            return

        log_channel_id = db.get_channel(before.guild.id, "log")
        if not log_channel_id:
            return

        log_channel = before.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="✍️ Message Edited",
            description=f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}\n[Jump to Message]({after.jump_url})",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        before_content = before.content if before.content else "N/A"
        after_content = after.content if after.content else "N/A"
        embed.add_field(name="Before", value=f"```{before_content}```", inline=False)
        embed.add_field(name="After", value=f"```{after_content}```", inline=False)
        embed.set_footer(text=f"Author ID: {before.author.id} | Message ID: {before.id}")

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        log_channel_id = db.get_channel(role.guild.id, "log")
        if not log_channel_id:
            return
        log_channel = role.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="✨ Role Created",
            description=f"The role {role.mention} (`{role.name}`) was created.",
            color=discord.Color.green(),
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
            title="🔥 Role Deleted",
            description=f"The role `{role.name}` was deleted.",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handles reactions to messages to check for starboard posts."""
        # Ignore reactions from bots or in DMs
        if not payload.guild_id or payload.member.bot:
            return
            
        # Check if it's a star emoji
        if str(payload.emoji) != '⭐':
            return

        # Fetch settings
        settings = db.get_starboard_settings(payload.guild_id)
        if not settings or "starboard_channel" not in settings:
            return # Starboard not configured
            
        starboard_channel_id = settings["starboard_channel"]
        required_stars = settings.get("starboard_star_count", 3) # Default to 3

        # Fetch the channel and message
        channel = self.bot.get_channel(payload.channel_id)
        if not channel or channel.id == starboard_channel_id:
             # Don't star messages in the starboard itself
            return
        
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return # Message was deleted

        # Ignore old messages (e.g., older than 30 days)
        if (datetime.utcnow().replace(tzinfo=None) - message.created_at.replace(tzinfo=None)).days > 30:
            return

        # Check star count on the original message
        for reaction in message.reactions:
            if str(reaction.emoji) == '⭐':
                if reaction.count >= required_stars:
                    await self.post_to_starboard(message, reaction.count)
                break

    async def post_to_starboard(self, message: discord.Message, star_count: int):
        """Creates or edits a message on the starboard."""
        starboard_channel_id = db.get_starboard_settings(message.guild.id)["starboard_channel"]
        starboard_channel = self.bot.get_channel(starboard_channel_id)
        if not starboard_channel: return

        # --- Create Embed ---
        embed = discord.Embed(
            description=message.content,
            color=0xFFAC33 # Starboard gold
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="Original", value=f"[Jump to Message]({message.jump_url})")

        # Handle images/attachments
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        
        embed.set_footer(text=f"ID: {message.id} | Channel: #{message.channel.name}")
        embed.timestamp = message.created_at

        # --- Post or Edit ---
        existing_starboard_message_id = db.get_starboard_message(message.id)
        content = f"⭐ **{star_count}**"

        if existing_starboard_message_id:
            try:
                starboard_message = await starboard_channel.fetch_message(existing_starboard_message_id)
                await starboard_message.edit(content=content, embed=embed)
            except discord.NotFound:
                # The starboard message was deleted, so we'll create a new one
                new_starboard_message = await starboard_channel.send(content=content, embed=embed)
                db.add_starboard_message(message.id, new_starboard_message.id)
        else:
            # Check if the message has already been sent, just in case
            if not db.get_starboard_message(message.id):
                starboard_message = await starboard_channel.send(content=content, embed=embed)
                db.add_starboard_message(message.id, starboard_message.id)

async def setup(bot):
    await bot.add_cog(Events(bot))
