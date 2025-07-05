import discord
from discord.ext import commands
from discord import app_commands
import random
import os
import re
from datetime import datetime, timedelta
import google.generativeai as genai
import database as db
from discord.ui import Button, View
from PIL import Image, ImageDraw, ImageFont
import asyncio
import math

def extract_urls(text):
    return re.findall(r'(https?://\S+)', text)

class LinkView(View):
    def __init__(self, urls):
        super().__init__()
        for i, url in enumerate(urls[:5]):
            self.add_item(Button(label=f"Link {i+1}", url=url))

class GiveawayView(View):
    def __init__(self, end_time, participants=None):
        super().__init__(timeout=None)
        self.end_time = end_time
        self.participants = participants or set()

    @discord.ui.button(label="🎉 Enter Giveaway", style=discord.ButtonStyle.primary)
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.participants:
            await interaction.response.send_message("❌ You're already entered in this giveaway!", ephemeral=True)
        else:
            self.participants.add(user_id)
            await interaction.response.send_message("✅ You've entered the giveaway! Good luck!", ephemeral=True)

GUILD_ID = 1370009417726169250

ANNOUNCE_ROLES = [
    "Moderator 🚨🚓",
    "🚨 Lead moderator",
    "🦥 Overseer",
    "Forgotten one"
]

class Community(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.genai_api_key = os.getenv("GEMINI_API_KEY")
        if self.genai_api_key:
            genai.configure(api_key=self.genai_api_key)
            self.model = genai.GenerativeModel('gemini-pro')

    async def cog_load(self):
        print("[Community] Loaded successfully.")

    def create_wheel_image(self, options):
        """Create a wheel image with the given options"""
        try:
            # Load the wheel background
            wheel_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'wheel.png')
            wheel_img = Image.open(wheel_path).convert('RGBA')
            
            # Create a drawing context
            draw = ImageDraw.Draw(wheel_img)
            
            # Load font
            font_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Poppins-Bold.ttf')
            try:
                font = ImageFont.truetype(font_path, 24)
            except:
                font = ImageFont.load_default()
            
            # Calculate positions for text
            center_x, center_y = wheel_img.size[0] // 2, wheel_img.size[1] // 2
            radius = min(center_x, center_y) - 50
            
            # Draw options on the wheel
            for i, option in enumerate(options):
                angle = (2 * math.pi * i) / len(options)
                text_x = center_x + (radius * 0.7) * math.cos(angle)
                text_y = center_y + (radius * 0.7) * math.sin(angle)
                
                # Draw text with outline for better visibility
                draw.text((text_x-1, text_y-1), option, font=font, fill='black')
                draw.text((text_x+1, text_y-1), option, font=font, fill='black')
                draw.text((text_x-1, text_y+1), option, font=font, fill='black')
                draw.text((text_x+1, text_y+1), option, font=font, fill='black')
                draw.text((text_x, text_y), option, font=font, fill='white')
            
            # Save the image
            output_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'temp_wheel.png')
            wheel_img.save(output_path)
            return output_path
            
        except Exception as e:
            print(f"Error creating wheel image: {e}")
            return None

    @app_commands.command(name="suggest", description="Submit a suggestion to the server")
    @app_commands.describe(suggestion="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        embed = discord.Embed(
            title="💡 New Suggestion",
            description=suggestion,
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="React with 👍 or 👎 to vote!")

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("👍")
        await message.add_reaction("👎")

    @app_commands.command(name="spinawheel", description="Spin a wheel with up to 10 options")
    @app_commands.describe(options="Comma-separated options (up to 10)")
    async def spinawheel(self, interaction: discord.Interaction, options: str):
        option_list = [opt.strip() for opt in options.split(",") if opt.strip()]
        
        if len(option_list) < 2:
            await interaction.response.send_message("❌ Please provide at least 2 options separated by commas!", ephemeral=True)
            return
        
        if len(option_list) > 10:
            await interaction.response.send_message("❌ Maximum 10 options allowed!", ephemeral=True)
            return
        
        winner = random.choice(option_list)
        
        # Create wheel image
        wheel_image_path = self.create_wheel_image(option_list)
        
        embed = discord.Embed(
            title="🎡 Wheel Spin Results",
            description=f"**Winner:** {winner}",
            color=0xffd700
        )
        embed.add_field(name="Options", value="\n".join([f"• {opt}" for opt in option_list]), inline=False)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        
        # Add wheel image if created successfully
        if wheel_image_path:
            file = discord.File(wheel_image_path, filename="wheel.png")
            embed.set_image(url="attachment://wheel.png")
            await interaction.response.send_message(embed=embed, file=file)
            
            # Clean up temporary file
            try:
                os.remove(wheel_image_path)
            except:
                pass
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="View detailed info about a server member")
    @app_commands.describe(user="The user to get info about")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        embed = discord.Embed(
            title=f"👤 User Info: {target.display_name}",
            color=target.accent_color or 0x7289da
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        embed.add_field(name="👤 Username", value=f"{target.name}#{target.discriminator}", inline=True)
        embed.add_field(name="🆔 ID", value=target.id, inline=True)
        embed.add_field(name="📅 Account Created", value=f"<t:{int(target.created_at.timestamp())}:F>", inline=False)
        embed.add_field(name="📅 Joined Server", value=f"<t:{int(target.joined_at.timestamp())}:F>", inline=False)
        
        if target.roles[1:]:  # Skip @everyone role
            roles = [role.mention for role in reversed(target.roles[1:])]
            embed.add_field(name="🎭 Roles", value=" ".join(roles[:10]), inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Shows stats and info about the server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"📈 Server Info: {guild.name}",
            color=0x7289da
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=False)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="📁 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="🚀 Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="💎 Boosts", value=guild.premium_subscription_count, inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check the bot's ping to Discord servers")
    async def ping(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**Latency:** {round(self.bot.latency * 1000)}ms",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="askblecknephew", description="THE SAINT shall clear your doubts")
    @app_commands.describe(question="Your question for the AI")
    async def askblecknephew(self, interaction: discord.Interaction, question: str):
        if not self.genai_api_key:
            await interaction.response.send_message("❌ AI service not configured!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            prompt = f"You are 'THE SAINT' - a wise and helpful AI assistant. Answer this question: {question}"
            response = self.model.generate_content(prompt)
            
            embed = discord.Embed(
                title="🤖 THE SAINT Responds",
                description=response.text[:2000],
                color=0x9932cc
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="THE SAINT • AI-powered responses")

            # Check for URLs and add buttons if found
            urls = extract_urls(response.text)
            view = LinkView(urls) if urls else None

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ Error generating response: {str(e)}", ephemeral=True)

    @app_commands.command(name="flip", description="Flip a coin - heads or tails")
    async def flip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        
        # Get the appropriate image
        image_name = "heads.jpeg" if result == "Heads" else "tails.jpeg"
        image_path = os.path.join(os.path.dirname(__file__), '..', 'assets', image_name)
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"**{result}!**",
            color=0xffd700
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        
        # Add the coin image
        if os.path.exists(image_path):
            file = discord.File(image_path, filename=image_name)
            embed.set_image(url=f"attachment://{image_name}")
            await interaction.response.send_message(embed=embed, file=file)
        else:
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="giveaway", description="Start a giveaway with specified duration and winner count")
    @app_commands.describe(
        duration="Duration in minutes (e.g., 60 for 1 hour)",
        winners="Number of winners (default: 1)",
        prize="Prize description",
        channel="Channel to post the giveaway (optional)"
    )
    async def giveaway(self, interaction: discord.Interaction, duration: int, prize: str, winners: int = 1, channel: discord.TextChannel = None):
        # Check if user has required role
        user_roles = [role.name for role in interaction.user.roles]
        if not any(role in ANNOUNCE_ROLES for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        if duration <= 0 or duration > 10080:  # Max 1 week
            await interaction.response.send_message("❌ Duration must be between 1 and 10080 minutes (1 week)!", ephemeral=True)
            return
            
        if winners <= 0 or winners > 20:
            await interaction.response.send_message("❌ Number of winners must be between 1 and 20!", ephemeral=True)
            return
        
        target_channel = channel or interaction.channel
        end_time = datetime.now() + timedelta(minutes=duration)
        
        embed = discord.Embed(
            title="🎉 GIVEAWAY! 🎉",
            description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(end_time.timestamp())}:R>",
            color=0xff6b6b,
            timestamp=end_time
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Click the button below to enter!")
        
        view = GiveawayView(end_time)
        
        try:
            giveaway_message = await target_channel.send(embed=embed, view=view)
            await interaction.response.send_message(f"✅ Giveaway started in {target_channel.mention}!", ephemeral=True)
            
            # Wait for the giveaway to end
            await asyncio.sleep(duration * 60)
            
            # Select winners
            if len(view.participants) == 0:
                embed.description = f"**Prize:** {prize}\n**Winners:** No one entered! 😢"
                embed.color = 0x999999
                await giveaway_message.edit(embed=embed, view=None)
                return
            
            actual_winners = min(winners, len(view.participants))
            winner_ids = random.sample(list(view.participants), actual_winners)
            winner_mentions = [f"<@{uid}>" for uid in winner_ids]
            
            embed.description = f"**Prize:** {prize}\n**Winners:** {', '.join(winner_mentions)}"
            embed.color = 0x00ff00
            await giveaway_message.edit(embed=embed, view=None)
            
            # Congratulate winners
            congrats_embed = discord.Embed(
                title="🎊 Giveaway Ended!",
                description=f"Congratulations to the winner(s): {', '.join(winner_mentions)}\n\n**Prize:** {prize}",
                color=0x00ff00
            )
            await target_channel.send(embed=congrats_embed)
            
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ I don't have permission to send messages in {target_channel.mention}!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error starting giveaway: {str(e)}", ephemeral=True)

    @app_commands.command(name="announce", description="Creates and sends a formatted announcement")
    @app_commands.describe(
        channel="Channel to send the announcement",
        title="Announcement title",
        message="Announcement message"
    )
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str):
        # Check if user has required role
        user_roles = [role.name for role in interaction.user.roles]
        if not any(role in ANNOUNCE_ROLES for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📢 {title}",
            description=message,
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"Announced by {interaction.user.display_name}")

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Community(bot))
        
