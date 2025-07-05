import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio

class ExampleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[ExampleCog] ✅ Loaded successfully with test commands")

    @app_commands.command(name="hello", description="👋 Basic hello command - Test if bot is responding")
    async def hello(self, interaction: discord.Interaction):
        """Simple hello command with no database dependencies"""
        embed = discord.Embed(
            title="👋 Hello World!",
            description=f"Hello, {interaction.user.display_name}! The bot is working perfectly!",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="✅ Status", value="Bot is online and responding", inline=True)
        embed.add_field(name="🎯 Commands", value="All systems operational", inline=True)
        embed.set_footer(text="This proves the bot and commands are working!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="test", description="🧪 Simple test command to verify bot responsiveness")
    async def test(self, interaction: discord.Interaction):
        """Test command with minimal processing"""
        embed = discord.Embed(
            title="🧪 Bot Test Successful",
            description="✅ This command confirms the bot is responding correctly!",
            color=0x7289da,
            timestamp=datetime.now()
        )
        embed.add_field(name="📊 Response", value="Instant", inline=True)
        embed.add_field(name="🔧 Status", value="All systems go", inline=True)
        embed.add_field(name="💚 Result", value="Commands are working perfectly", inline=False)
        embed.set_footer(text="If you see this, everything is working!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="🏓 Check bot latency and response time")
    async def ping(self, interaction: discord.Interaction):
        """Simple ping command"""
        latency = round(self.bot.latency * 1000)
        
        if latency < 100:
            color = 0x00ff00
            status = "Excellent"
        elif latency < 200:
            color = 0xffff00
            status = "Good"
        else:
            color = 0xff0000
            status = "Poor"
            
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**Latency:** {latency}ms\n**Status:** {status}",
            color=color,
            timestamp=datetime.now()
        )
        embed.add_field(name="🌐 Connection", value="Stable", inline=True)
        embed.add_field(name="⚡ Response", value="Immediate", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="info", description="📊 Show bot information and status")
    async def info(self, interaction: discord.Interaction):
        """Bot information command"""
        bot = self.bot
        
        embed = discord.Embed(
            title="🤖 Bot Information",
            description=f"**{bot.user.name}** is online and fully operational!",
            color=0x7289da,
            timestamp=datetime.now()
        )
        
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        
        # Basic stats
        embed.add_field(name="🆔 Bot ID", value=bot.user.id, inline=True)
        embed.add_field(name="📊 Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="👥 Users", value=len(bot.users), inline=True)
        
        # Technical stats
        embed.add_field(name="🏓 Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🔧 Discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="✅ Status", value="Fully Operational", inline=True)
        
        # Commands info
        all_commands = [cmd for cmd in bot.tree.get_commands()]
        embed.add_field(name="⚡ Commands", value=len(all_commands), inline=True)
        embed.add_field(name="🎯 Cogs", value=len(bot.cogs), inline=True)
        embed.add_field(name="🌟 Version", value="2.0.0", inline=True)
        
        embed.set_footer(text="All systems operational • Bot is ready to serve!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sync", description="� Manually sync slash commands (Admin only)")
    async def manual_sync(self, interaction: discord.Interaction):
        """Manual command sync for administrators"""
        # Check if user has administrator permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command!", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Clear and sync commands
            self.bot.tree.clear_commands(guild=None)
            await asyncio.sleep(2)  # Small delay
            synced = await self.bot.tree.sync()
            
            embed = discord.Embed(
                title="✅ Commands Synced Successfully",
                description=f"Successfully synced **{len(synced)}** slash commands globally.",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            if synced:
                command_names = [cmd.name for cmd in synced]
                commands_text = "```\n" + "\n".join(command_names) + "\n```"
                embed.add_field(
                    name="� Synced Commands", 
                    value=commands_text, 
                    inline=False
                )
            
            embed.add_field(
                name="⏰ Timing", 
                value="Commands should appear immediately", 
                inline=True
            )
            embed.add_field(
                name="🌐 Scope", 
                value="Global (all servers)", 
                inline=True
            )
            
            embed.set_footer(text="Commands are now available across all servers!")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Sync Failed",
                description=f"Failed to sync commands: {str(e)}",
                color=0xff0000,
                timestamp=datetime.now()
            )
            error_embed.add_field(name="🔍 Error Type", value=type(e).__name__, inline=True)
            error_embed.add_field(name="💡 Solution", value="Try again in a few minutes", inline=True)
            await interaction.followup.send(embed=error_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ExampleCog(bot))
    print("[Setup] ✅ ExampleCog added to bot")
