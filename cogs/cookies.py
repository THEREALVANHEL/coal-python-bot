import discord
from discord.ext import commands
from discord import app_commands

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class CookiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="cookie", description="Give a cookie to a user.")
    @app_commands.guilds(guild_obj)
    async def cookie(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(f"You gave a cookie to {user.mention}!", ephemeral=False)

async def setup(bot):
    await bot.add_cog(CookiesCog(bot))
