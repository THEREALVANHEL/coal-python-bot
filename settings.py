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
        default_member_permissions=admin_perms,
        guild_ids=[1370009417726169250]
    )
    @option("channel", description="The channel to use for welcome messages.", type=discord.TextChannel, required=True)
    async def setwelcomechannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db.set_channel(ctx.guild.id, "welcome", channel.id)
        await ctx.respond(f"✅ Welcome messages will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(
        name="setleavechannel",
        description="[Admin] Set the channel where member departures are announced.",
        default_member_permissions=admin_perms,
        guild_ids=[1370009417726169250]
    )
    @option("channel", description="The channel to use for leave messages.", type=discord.TextChannel, required=True)
    async def setleavechannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db.set_channel(ctx.guild.id, "leave", channel.id)
        await ctx.respond(f"✅ Leave messages will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(
        name="setlogchannel",
        description="[Admin] Set the channel for audit logs (edited messages, etc.).",
        default_member_permissions=admin_perms,
        guild_ids=[1370009417726169250]
    )
    @option("channel", description="The channel to use for audit logs.", type=discord.TextChannel, required=True)
    async def setlogchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db.set_channel(ctx.guild.id, "log", channel.id)
        await ctx.respond(f"✅ Audit logs will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(
        name="setlevelingchannel",
        description="[Admin] Set the channel for level-up announcements.",
        default_member_permissions=admin_perms,
        guild_ids=[1370009417726169250]
    )
    @option("channel", description="The channel to use for level-up messages.", type=discord.TextChannel, required=True)
    async def setlevelingchannel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db.set_channel(ctx.guild.id, "leveling", channel.id)
        await ctx.respond(f"✅ Level-up announcements will now be sent to {channel.mention}.", ephemeral=True)

    @commands.slash_command(name="showsettings", description="Show current configured channels.", guild_ids=[1370009417726169250])
    async def showsettings(self, ctx: discord.ApplicationContext):
        guild_id = ctx.guild.id
        welcome = db.get_channel(guild_id, "welcome")
        leave = db.get_channel(guild_id, "leave")
        log = db.get_channel(guild_id, "log")
        leveling = db.get_channel(guild_id, "leveling")
        embed = discord.Embed(
            title="🔧 Server Settings",
            description="Here are your current channel settings:",
            color=discord.Color.dark_teal()
        )
        embed.add_field(name="👋 Welcome Channel", value=f"<#{welcome}>" if welcome else "Not set", inline=False)
        embed.add_field(name="👋 Leave Channel", value=f"<#{leave}>" if leave else "Not set", inline=False)
        embed.add_field(name="📝 Log Channel", value=f"<#{log}>" if log else "Not set", inline=False)
        embed.add_field(name="🌌 Leveling Channel", value=f"<#{leveling}>" if leveling else "Not set", inline=False)
        embed.set_footer(text="Futuristic UK Settings | BLEK NEPHEW", icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Settings(bot))
