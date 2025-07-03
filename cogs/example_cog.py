import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1370009417726169250               # replace with your guild ID if different
guild_obj = discord.Object(id=GUILD_ID)

class ExampleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ─────────────────────────────────────────────────────────────
    # Slash-command: /hello
    # ─────────────────────────────────────────────────────────────
    @app_commands.command(
        name="hello",
        description="Say hello!"
    )
    @app_commands.guilds(guild_obj)           # registers instantly in this guild
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Hello from the bot!",
            ephemeral=True                       # visible only to the user
        )

# ─────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    """Loads the cog and binds all commands to the target guild."""
    await bot.add_cog(ExampleCog(bot), guilds=[guild_obj])
