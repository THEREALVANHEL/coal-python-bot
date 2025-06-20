import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class SettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="settings", description="Placeholder for settings command.")
    @app_commands.guilds(guild_obj)
    async def settings(self, interaction: discord.Interaction):
        await interaction.response.send_message("Settings command is working!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))
