import discord
from discord.ext import commands
from discord import option, Permissions
import sys
import os

# Add the parent directory to the path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define a shared permission check for all commands in this cog
    admin_perms = discord.Permissions(administrator=True)

    # --- Commands ---

    @commands.slash_command(
        name="setwelcomechannel",
        description="[Admin] Set the channel where new members are welcomed.",
        default_member_permissions=admin_perms
    )
    @option("channel", description="The channel to use for welcome messages.", type=discord.TextChannel, required=True)
    async def setwelcomechannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db.set_channel(ctx.guild.id, "welcome", channel.id)
        await ctx.respond(f"✅ Welcome messages will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(
        name="setleavechannel",
        description="[Admin] Set the channel where member departures are announced.",
        default_member_permissions=admin_perms
    )
    @option("channel", description="The channel to use for leave messages.", type=discord.TextChannel, required=True)
    async def setleavechannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db.set_channel(ctx.guild.id, "leave", channel.id)
        await ctx.respond(f"✅ Leave messages will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(
        name="setlogchannel",
        description="[Admin] Set the channel for audit logs (edited messages, etc.).",
        default_member_permissions=admin_perms
    )
    @option("channel", description="The channel to use for audit logs.", type=discord.TextChannel, required=True)
    async def setlogchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db.set_channel(ctx.guild.id, "log", channel.id)
        await ctx.respond(f"✅ Audit logs will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(
        name="setlevelingchannel",
        description="[Admin] Set the channel for level-up announcements.",
        default_member_permissions=admin_perms
    )
    @option("channel", description="The channel to use for level-up messages.", type=discord.TextChannel, required=True)
    async def setlevelingchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db.set_channel(ctx.guild.id, "leveling", channel.id)
        await ctx.respond(f"✅ Level-up announcements will now be sent to {channel.mention}.", ephemeral=True)


def setup(bot):
    bot.add_cog(Settings(bot))
