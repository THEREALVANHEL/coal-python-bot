import discord
from discord.ext import commands

GUILD_ID = 1370009417726169250
guild_obj = discord.Object(id=GUILD_ID)

class ExampleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[ExampleCog] Loaded successfully.")

    @commands.slash_command(name="hello", description="Say hello!", guild_ids=[GUILD_ID])
    async def hello(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Hello, {ctx.user.display_name}!")

async def setup(bot: commands.Bot):
    await bot.add_cog(ExampleCog(bot), guilds=[guild_obj])
