import discord
from discord.ext import commands
from datetime import datetime
import sys
import os

# Add root to sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database as db
from assets import media_links

AUTO_ROLE_ID = 1384141744303636610  # "OPS ✋🏻"

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Member Join
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Auto-role
        try:
            role = member.guild.get_role(AUTO_ROLE_ID)
            if role:
                await member.add_roles(role, reason="Auto role on join.")
        except Exception as e:
            print(f"[Auto-Role] Error: {e}")

        # Welcome embed
        channel_id = db.get_channel(member.guild.id, "welcome")
        if not channel_id: return
        channel = member.guild.get_channel(channel_id)
        if not channel: return

        embed = discord.Embed(
            title="😗 **WELCOME TO HELL, TOP G!** 😗",
            description=f"{member.mention}, your soul is now ours.\nEnjoy the flames 🔥",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=media_links.WELCOME_GIF)
        embed.add_field(name="🔥 You arrived at", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        try:
            await channel.send(embed=embed)
        except:
            print("[Welcome] Missing permissions.")

        # Log join
        log_id = db.get_channel(member.guild.id, "log")
        if log_id:
            log_channel = member.guild.get_channel(log_id)
            if log_channel:
                embed = discord.Embed(
                    title="😃 Member Joined",
                    description=f"{member.mention} joined.",
                    color=discord.Color.green(),
                                    timestamp=datetime.utcnow()
            )
                embed.set_footer(text=f"User ID: {member.id}")
                await log_channel.send(embed=embed)

    # Member Leave
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        log_id = db.get_channel(member.guild.id, "log")
        if not log_id: return
        channel = member.guild.get_channel(log_id)
        if not channel: return

        embed = discord.Embed(
            title="👿 **HOW DARE YOU LEAVE?!** 👿",
            description=f"{member.mention} — HOPE YOU ROT IN HELL 🔥",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_image(url=media_links.LEAVE_GIF)
        embed.add_field(name="🚪 Escaped at", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        await channel.send(embed=embed)

    # Message Deleted
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        log_id = db.get_channel(message.guild.id, "log")
        if not log_id: return
        channel = message.guild.get_channel(log_id)
        if not channel: return

        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        content = message.content or "No content (embed or attachment)"
        embed.add_field(name="Content", value=f"```{content}```", inline=False)
        embed.set_footer(text=f"Author ID: {message.author.id} | Message ID: {message.id}")
        await channel.send(embed=embed)

    # Message Edited
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        log_id = db.get_channel(before.guild.id, "log")
        if not log_id: return
        channel = before.guild.get_channel(log_id)
        if not channel: return

        embed = discord.Embed(
            title="✍️ Message Edited",
            description=f"**Author:** {before.author.mention}\n**Channel:** {before.channel.mention}\n[Jump]({after.jump_url})",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Before", value=f"```{before.content}```", inline=False)
        embed.add_field(name="After", value=f"```{after.content}```", inline=False)
        embed.set_footer(text=f"Author ID: {before.author.id} | Message ID: {before.id}")
        await channel.send(embed=embed)

    # Role Created
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        log_id = db.get_channel(role.guild.id, "log")
        if not log_id: return
        channel = role.guild.get_channel(log_id)
        if not channel: return

        embed = discord.Embed(
            title="✨ Role Created",
            description=f"{role.mention} (`{role.name}`) was created.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=embed)

    # Role Deleted
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        log_id = db.get_channel(role.guild.id, "log")
        if not log_id: return
        channel = role.guild.get_channel(log_id)
        if not channel: return

        embed = discord.Embed(
            title="🔥 Role Deleted",
            description=f"`{role.name}` was deleted.",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=embed)

    # Channel Created
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        log_id = db.get_channel(channel.guild.id, "log")
        if not log_id: return
        log = channel.guild.get_channel(log_id)
        if not log: return

        embed = discord.Embed(
            title="📁 Channel Created",
            description=f"{channel.mention} (`{channel.name}`) was created.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        await log.send(embed=embed)

    # Channel Deleted
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        log_id = db.get_channel(channel.guild.id, "log")
        if not log_id: return
        log = channel.guild.get_channel(log_id)
        if not log: return

        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            description=f"`{channel.name}` was deleted.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await log.send(embed=embed)

    # Member Role Update
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        log_id = db.get_channel(after.guild.id, "log")
        if not log_id: return
        log = after.guild.get_channel(log_id)
        if not log: return
        
        added = [r for r in after.roles if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]

        for r in added:
            embed = discord.Embed(
                title="➕ Role Added",
                description=f"{after.mention} was given `{r.name}`.",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            await log.send(embed=embed)

        for r in removed:
            embed = discord.Embed(
                title="➖ Role Removed",
                description=f"{after.mention} lost `{r.name}`.",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            await log.send(embed=embed)

    # Starboard
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id or payload.member.bot or str(payload.emoji) != "⭐":
            return
        settings = db.get_starboard_settings(payload.guild_id)
        if not settings: return
        starboard_id = settings.get("starboard_channel")
        star_threshold = settings.get("starboard_star_count", 3)

        if payload.channel_id == starboard_id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except:
            return

        if (datetime.utcnow() - message.created_at).days > 30:
            return

        for reaction in message.reactions:
            if str(reaction.emoji) == "⭐" and reaction.count >= star_threshold:
                await self.post_to_starboard(message, reaction.count)
                break

    async def post_to_starboard(self, message: discord.Message, star_count: int):
        settings = db.get_starboard_settings(message.guild.id)
        channel_id = settings["starboard_channel"]
        star_channel = self.bot.get_channel(channel_id)
        if not star_channel:
            return

        embed = discord.Embed(description=message.content, color=0xFFAC33)
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="Original", value=f"[Jump to Message]({message.jump_url})")
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        embed.set_footer(text=f"ID: {message.id} | Channel: #{message.channel.name}")
        embed.timestamp = message.created_at

        content = f"⭐ **{star_count}**"
        existing = db.get_starboard_message(message.id)
        try:
            if existing:
                old_msg = await star_channel.fetch_message(existing)
                await old_msg.edit(content=content, embed=embed)
            else:
                new_msg = await star_channel.send(content=content, embed=embed)
                db.add_starboard_message(message.id, new_msg.id)
        except discord.NotFound:
            msg = await star_channel.send(content=content, embed=embed)
            db.add_starboard_message(message.id, msg.id)


# Setup
async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
        
