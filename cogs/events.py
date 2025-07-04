import discord
from discord.ext import commands
from datetime import datetime
import sys
import os

# ------------------------------------------------------------------
# Ensure the project root is on sys.path so reloaded cogs
# can still import database.py and the assets package.
# ------------------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database as db
from assets import media_links  # centralized GIF links

# === Constants ====================================================
AUTO_ROLE_ID = 1384141744303636610  # “OPS ✋🏻” role ID


class Events(commands.Cog):
    """Server-wide event listeners (welcome, leave, logging, starboard, etc.)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------------------------------------------
    # MEMBER JOIN
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # 1) Auto-assign role
        try:
            role = member.guild.get_role(AUTO_ROLE_ID)
            if role:
                await member.add_roles(role, reason="Automatic role assignment on join.")
        except discord.Forbidden:
            print(f"[Auto-Role] Missing permissions in {member.guild.name}")
        except Exception as e:
            print(f"[Auto-Role] Unexpected error: {e}")

        # 2) Welcome channel
        welcome_channel_id = db.get_channel(member.guild.id, "welcome")
        if not welcome_channel_id:
            return
        welcome_channel = member.guild.get_channel(welcome_channel_id)
        if not welcome_channel:
            return

        embed = discord.Embed(
            title="😗 **WELCOME TO HELL, TOP G!** 😗",
            description=f"{member.mention}, your soul is now ours.\nEnjoy the flames 🔥",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=media_links.WELCOME_GIF)
        embed.add_field(
            name="🔥 You arrived at",
            value=f"<t:{int(datetime.utcnow().timestamp())}:F>",
            inline=False,
        )
        embed.set_footer(text=f"User ID: {member.id}")

        try:
            await welcome_channel.send(embed=embed)
        except discord.Forbidden:
            print(f"[Welcome] Missing send perms in #{welcome_channel.name}")

        # 3) Log join
        log_channel_id = db.get_channel(member.guild.id, "log")
        if log_channel_id:
            log_channel = member.guild.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="😃 Member Joined",
                    description=f"{member.mention} joined the server.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow(),
                )
                log_embed.set_footer(text=f"User ID: {member.id}")
                await log_channel.send(embed=log_embed)

    # --------------------------------------------------------------
    # MEMBER LEAVE
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        log_channel_id = db.get_channel(member.guild.id, "log")
        if not log_channel_id:
            return
        log_channel = member.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="👿 **HOW DARE YOU LEAVE?!** 👿",
            description=f"{member.mention} — HOPE YOU ROT IN HELL 🔥",
            color=discord.Color.red(),
            timestamp=datetime.utcnow(),
        )
        embed.set_image(url=media_links.LEAVE_GIF)
        embed.add_field(
            name="🚪 Escaped at",
            value=f"<t:{int(datetime.utcnow().timestamp())}:F>",
            inline=False,
        )
        embed.set_footer(text=f"User ID: {member.id}")

        await log_channel.send(embed=embed)

    # --------------------------------------------------------------
    # MESSAGE DELETE
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
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
            description=(
                f"**Author:** {message.author.mention}\n"
                f"**Channel:** {message.channel.mention}"
            ),
            color=discord.Color.red(),
            timestamp=datetime.utcnow(),
        )
        content = (
            message.content
            if message.content
            else "No message content (e.g., an embed or attachment)."
        )
        embed.add_field(name="Content", value=f"```{content}```", inline=False)
        embed.set_footer(
            text=f"Author ID: {message.author.id} | Message ID: {message.id}"
        )
        await log_channel.send(embed=embed)

    # --------------------------------------------------------------
    # MESSAGE EDIT
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
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
            description=(
                f"**Author:** {before.author.mention}\n"
                f"**Channel:** {before.channel.mention}\n"
                f"[Jump to Message]({after.jump_url})"
            ),
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="Before", value=f"```{before.content}```", inline=False)
        embed.add_field(name="After", value=f"```{after.content}```", inline=False)
        embed.set_footer(
            text=f"Author ID: {before.author.id} | Message ID: {before.id}"
        )
        await log_channel.send(embed=embed)

    # --------------------------------------------------------------
    # ROLE CREATED
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
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
            timestamp=datetime.utcnow(),
        )
        await log_channel.send(embed=embed)

    # --------------------------------------------------------------
    # ROLE DELETED
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
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
            timestamp=datetime.utcnow(),
        )
        await log_channel.send(embed=embed)

    # --------------------------------------------------------------
    # CHANNEL CREATED
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_channel_id = db.get_channel(channel.guild.id, "log")
        if not log_channel_id:
            return
        log_channel = channel.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="📁 Channel Created",
            description=f"Channel {channel.mention} (`{channel.name}`) was created.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
        )
        await log_channel.send(embed=embed)

    # --------------------------------------------------------------
    # CHANNEL DELETED
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        log_channel_id = db.get_channel(channel.guild.id, "log")
        if not log_channel_id:
            return
        log_channel = channel.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            description=f"Channel `{channel.name}` was deleted.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow(),
        )
        await log_channel.send(embed=embed)

    # --------------------------------------------------------------
    # MEMBER ROLE UPDATES
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        log_channel_id = db.get_channel(after.guild.id, "log")
        if not log_channel_id:
            return
        log_channel = after.guild.get_channel(log_channel_id)
        if not log_channel:
            return

        added_roles = [r for r in after.roles if r not in before.roles]
        removed_roles = [r for r in before.roles if r not in after.roles]

        for role in added_roles:
            embed = discord.Embed(
                title="➕ Role Added",
                description=f"{after.mention} was given the role `{role.name}`.",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow(),
            )
            await log_channel.send(embed=embed)

        for role in removed_roles:
            embed = discord.Embed(
                title="➖ Role Removed",
                description=f"{after.mention} lost the role `{role.name}`.",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow(),
            )
            await log_channel.send(embed=embed)

    # --------------------------------------------------------------
    # STARBOARD (⭐ reactions)
    # --------------------------------------------------------------
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id or payload.member.bot or str(payload.emoji) != "⭐":
            return

        settings = db.get_starboard_settings(payload.guild_id)
        if not settings or "starboard_channel" not in settings:
            return

        starboard_channel_id = settings["starboard_channel"]
        required_stars = settings.get("starboard_star_count", 3)

        channel = self.bot.get_channel(payload.channel_id)
        if not channel or channel.id == starboard_channel_id:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        # Ignore messages older than 30 days
        if (
            datetime.utcnow().replace(tzinfo=None)
            - message.created_at.replace(tzinfo=None)
        ).days > 30:
            return

        for reaction in message.reactions:
            if str(reaction.emoji) == "⭐" and reaction.count >= required_stars:
                await self.post_to_starboard(message, reaction.count)
                break

    async def post_to_starboard(self, message: discord.Message, star_count: int):
        starboard_channel_id = db.get_starboard_settings(message.guild.id)[
            "starboard_channel"
        ]
        starboard_channel = self.bot.get_channel(starboard_channel_id)
        if not starboard_channel:
            return

        embed = discord.Embed(description=message.content, color=0xFFAC33)
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url,
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="Original", value=f"[Jump to Message]({message.jump_url})")
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        embed.set_footer(
            text=f"ID: {message.id} | Channel: #{message.channel.name}"
        )
        embed.timestamp = message.created_at

        content = f"⭐ **{star_count}**"
        existing_starboard_id = db.get_starboard_message(message.id)

        try:
            if existing_starboard_id:
                star_msg = await starboard_channel.fetch_message(existing_starboard_id)
                await star_msg.edit(content=content, embed=embed)
            else:
                star_msg = await starboard_channel.send(content=content, embed=embed)
                db.add_starboard_message(message.id, star_msg.id)
        except discord.NotFound:
            # Original starboard message deleted; post anew
            star_msg = await starboard_channel.send(content=content, embed=embed)
            db.add_starboard_message(message.id, star_msg.id)


# --------------------------------------------------------------
# SETUP for dynamic cog loading
# --------------------------------------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
