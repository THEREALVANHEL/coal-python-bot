import discord
from discord.ext import commands
from discord import app_commands

class ExampleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[ExampleCog] Loaded successfully.")

    @app_commands.command(name="hello", description="👋 Say hello - Test command to verify bot functionality")
    async def hello(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👋 Hello!",
            description=f"Hello, {interaction.user.display_name}! The bot is working correctly!",
            color=0x00ff00
        )
        embed.add_field(name="✅ Status", value="Commands are working!", inline=True)
        embed.add_field(name="🚀 Bot", value="Online and functional", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="test", description="🧪 Test command to verify bot responsiveness")
    async def test(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🧪 Bot Test",
            description="This is a test command to verify the bot is responding correctly.",
            color=0x7289da
        )
        embed.add_field(name="📊 Response Time", value="Instant", inline=True)
        embed.add_field(name="🔧 Status", value="All systems operational", inline=True)
        embed.set_footer(text="If you see this, the bot is working perfectly!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sync", description="🔄 Manually sync slash commands (Admin only)")
    async def manual_sync(self, interaction: discord.Interaction):
        # Check if user has administrator permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command!", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Clear and sync commands
            self.bot.tree.clear_commands(guild=None)
            synced = await self.bot.tree.sync()
            
            embed = discord.Embed(
                title="✅ Commands Synced Successfully",
                description=f"Successfully synced **{len(synced)}** slash commands globally.",
                color=0x00ff00
            )
            
            if synced:
                command_names = [cmd.name for cmd in synced]
                embed.add_field(
                    name="📋 Synced Commands", 
                    value="```\n" + "\n".join(command_names) + "\n```", 
                    inline=False
                )
            
            embed.set_footer(text="Commands should now be available across all servers!")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Sync Failed",
                description=f"Failed to sync commands: {str(e)}",
                color=0xff0000
            )
            error_embed.add_field(name="🔍 Error Type", value=type(e).__name__, inline=True)
            await interaction.followup.send(embed=error_embed)

    @app_commands.command(name="botinfo", description="📊 Show bot information and status")
    async def botinfo(self, interaction: discord.Interaction):
        bot = self.bot
        
        # Calculate uptime
        import time
        try:
            # Try to get bot start time from main module
            import main
            uptime_seconds = time.time() - main.bot_start_time
        except:
            # Fallback if can't access start time
            uptime_seconds = 0
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        
        embed = discord.Embed(
            title="🤖 Bot Information",
            description=f"**{bot.user.name}** is online and operational!",
            color=0x7289da
        )
        
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        
        # Basic stats
        embed.add_field(name="🆔 Bot ID", value=bot.user.id, inline=True)
        embed.add_field(name="📊 Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="👥 Users", value=len(bot.users), inline=True)
        
        # Technical stats
        embed.add_field(name="🏓 Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="⏰ Uptime", value=f"{uptime_hours}h {uptime_minutes}m", inline=True)
        embed.add_field(name="🔧 Discord.py", value=discord.__version__, inline=True)
        
        # Commands info
        all_commands = [cmd for cmd in bot.tree.get_commands()]
        embed.add_field(name="⚡ Commands", value=len(all_commands), inline=True)
        embed.add_field(name="🎯 Cogs", value=len(bot.cogs), inline=True)
        embed.add_field(name="✅ Status", value="Fully Operational", inline=True)
        
        embed.set_footer(text="Bot developed for the community")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ExampleCog(bot))
