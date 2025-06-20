import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Placeholder for kick command.")
    @app_commands.guilds(guild_obj)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await interaction.response.send_message(f"Kicking {member.mention} for: {reason}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
