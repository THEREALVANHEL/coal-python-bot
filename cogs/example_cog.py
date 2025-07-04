import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1370009417726169250  # Your development guild ID
guild_obj = discord.Object(id=GUILD_ID)

class ExampleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hello", description="Say hello!")
    @app_commands.guilds(guild_obj)  # ✅ Instant sync in this guild only
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Hello from the bot!",
            ephemeral=True  # Only visible to the user
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(ExampleCog(bot), guilds=[guild_obj])
