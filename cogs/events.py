import discord
from discord.ext import commands
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

async def setup(bot):
    await bot.add_cog(Events(bot))
