import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class LevelingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="level", description="Placeholder for level command.")
    @app_commands.guilds(guild_obj)
    async def level(self, interaction: discord.Interaction):
        await interaction.response.send_message("Level command is working!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LevelingCog(bot))
