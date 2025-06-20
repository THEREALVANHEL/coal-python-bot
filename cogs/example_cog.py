import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1370009417726169250

guild_obj = discord.Object(id=GUILD_ID)

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hello", description="Say hello!")
    @app_commands.guilds(guild_obj)
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello from the bot!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ExampleCog(bot)) 