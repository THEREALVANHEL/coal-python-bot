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

class ShoutView(View):
    def __init__(self, shout_data):
        super().__init__(timeout=None)
        self.shout_data = shout_data
        self.participants = set()

    @discord.ui.button(label="🔥 Join Event", style=discord.ButtonStyle.primary, emoji="🚀")
    async def join_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.participants:
            await interaction.response.send_message("❌ You're already participating in this event!", ephemeral=True)
        else:
            self.participants.add(user_id)
            await interaction.response.send_message(f"✅ You've joined **{self.shout_data['title']}**! Get ready!", ephemeral=True)
            
            # Update the embed with new participant count
            embed = discord.Embed(
                title=f"📢 {self.shout_data['title']}",
                description=self.shout_data['description'],
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            embed.add_field(name="🎯 Host", value=self.shout_data.get('host', 'Unknown'), inline=True)
            embed.add_field(name="🤝 Co-Host", value=self.shout_data.get('co_host', 'None'), inline=True)
            embed.add_field(name="⚕️ Medic", value=self.shout_data.get('medic', 'None'), inline=True)
            embed.add_field(name="🗺️ Guide", value=self.shout_data.get('guide', 'None'), inline=True)
            embed.add_field(name="👥 Participants", value=f"{len(self.participants)} joined", inline=True)
            embed.add_field(name="⏰ Time", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
            embed.set_footer(text="Click the button below to join!")
            
            # Update the message
            try:
                await interaction.edit_original_response(embed=embed, view=self)
            except:
                pass

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

    def create_pie_wheel_image(self, options, title="Spin the Wheel!"):
        """Create a pie chart wheel image with the given options and title"""
        try:
            # Create a new image with a white background
            size = 400
            img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # Center and radius
            center = size // 2
            radius = center - 50
            
            # Colors for each slice
            colors = [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
            ]
            
            # Calculate angles for each slice
            num_options = len(options)
            angle_per_slice = 360 / num_options
            
            # Draw pie slices
            start_angle = 0
            for i, option in enumerate(options):
                end_angle = start_angle + angle_per_slice
                color = colors[i % len(colors)]
                
                # Draw the slice
                draw.pieslice(
                    [center - radius, center - radius, center + radius, center + radius],
                    start_angle, end_angle, fill=color, outline='white', width=3
                )
                
                # Calculate text position
                mid_angle = math.radians(start_angle + angle_per_slice / 2)
                text_radius = radius * 0.7
                text_x = center + text_radius * math.cos(mid_angle)
                text_y = center + text_radius * math.sin(mid_angle)
                
                # Draw text with better font handling
                try:
                    font_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Poppins-Bold.ttf')
                    font = ImageFont.truetype(font_path, 16)
                except:
                    font = ImageFont.load_default()
                
                # Get text size for centering
                bbox = draw.textbbox((0, 0), option, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Draw text with outline for better visibility
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    draw.text((text_x - text_width//2 + dx, text_y - text_height//2 + dy), 
                             option, font=font, fill='black')
                draw.text((text_x - text_width//2, text_y - text_height//2), 
                         option, font=font, fill='white')
                
                start_angle = end_angle
            
            # Draw center circle
            center_radius = 20
            draw.ellipse([center - center_radius, center - center_radius, 
                         center + center_radius, center + center_radius], 
                        fill='white', outline='black', width=2)
            
            # Draw title at the top
            try:
                title_font = ImageFont.truetype(font_path, 24)
            except:
                title_font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            title_x = center - title_width // 2
            title_y = 20
            
            # Draw title with outline
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                draw.text((title_x + dx, title_y + dy), title, font=title_font, fill='black')
            draw.text((title_x, title_y), title, font=title_font, fill='white')
            
            # Save the image
            output_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'temp_wheel.png')
            img.save(output_path)
            return output_path
            
        except Exception as e:
            print(f"Error creating pie wheel image: {e}")
            return None

    @app_commands.command(name="suggest", description="Submit a suggestion to the designated suggestions channel")
    @app_commands.describe(suggestion="Your suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        try:
            # Get the suggestion channel from settings
            suggest_channel_id = db.get_guild_setting(interaction.guild.id, "suggest_channel", None)
            
            if suggest_channel_id:
                suggest_channel = self.bot.get_channel(suggest_channel_id)
                if not suggest_channel:
                    await interaction.response.send_message("❌ Suggestion channel not found! Contact an admin.", ephemeral=True)
                    return
            else:
                await interaction.response.send_message("❌ No suggestion channel set! Use `/setup suggest_channel` to set one.", ephemeral=True)
                return

            embed = discord.Embed(
                title="💡 New Suggestion",
                description=suggestion,
                color=0x00ff00,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="Submitted by", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
            embed.set_footer(text="React with 👍 or 👎 to vote!")

            message = await suggest_channel.send(embed=embed)
            await message.add_reaction("👍")
            await message.add_reaction("👎")
            
            # Confirm to user
            await interaction.response.send_message(f"✅ Your suggestion has been forwarded to {suggest_channel.mention}!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error submitting suggestion: {str(e)}", ephemeral=True)

    @app_commands.command(name="shout", description="Create a detailed event announcement with join functionality")
    @app_commands.describe(
        title="Event title",
        description="Event description", 
        host="Event host",
        co_host="Co-host (optional)",
        medic="Medic (optional)",
        guide="Guide (optional)"
    )
    async def shout(self, interaction: discord.Interaction, title: str, description: str, host: str, 
                   co_host: str = None, medic: str = None, guide: str = None):
        # Check if user has required role
        user_roles = [role.name for role in interaction.user.roles]
        if not any(role in ANNOUNCE_ROLES for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            shout_data = {
                'title': title,
                'description': description,
                'host': host,
                'co_host': co_host or 'None',
                'medic': medic or 'None',
                'guide': guide or 'None'
            }
            
            embed = discord.Embed(
                title=f"📢 {title}",
                description=description,
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            embed.add_field(name="🎯 Host", value=host, inline=True)
            embed.add_field(name="🤝 Co-Host", value=co_host or 'None', inline=True)
            embed.add_field(name="⚕️ Medic", value=medic or 'None', inline=True)
            embed.add_field(name="🗺️ Guide", value=guide or 'None', inline=True)
            embed.add_field(name="👥 Participants", value="0 joined", inline=True)
            embed.add_field(name="⏰ Time", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
            embed.set_author(name=f"Event by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="Click the button below to join!")
            
            view = ShoutView(shout_data)
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating shout: {str(e)}", ephemeral=True)

    @app_commands.command(name="gamelog", description="Log a completed game with detailed information")
    @app_commands.describe(
        title="Game title",
        summary="Game summary",
        host="Game host",
        co_host="Co-host (optional)",
        medic="Medic (optional)",
        guide="Guide (optional)",
        participants="Participants (comma-separated)"
    )
    async def gamelog(self, interaction: discord.Interaction, title: str, summary: str, host: str,
                     co_host: str = None, medic: str = None, guide: str = None, participants: str = None):
        # Check if user has required role
        user_roles = [role.name for role in interaction.user.roles]
        if not any(role in ANNOUNCE_ROLES for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            embed = discord.Embed(
                title=f"🎮 Game Log: {title}",
                description=f"**Summary:** {summary}",
                color=0x7289da,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="🎯 Host", value=host, inline=True)
            embed.add_field(name="🤝 Co-Host", value=co_host or 'None', inline=True)
            embed.add_field(name="⚕️ Medic", value=medic or 'None', inline=True)
            embed.add_field(name="🗺️ Guide", value=guide or 'None', inline=True)
            
            # Format participants
            if participants:
                participant_list = [p.strip() for p in participants.split(',') if p.strip()]
                participant_text = ', '.join(participant_list)
                if len(participant_text) > 1024:
                    participant_text = participant_text[:1021] + "..."
                embed.add_field(name="👥 Participants", value=participant_text, inline=False)
            else:
                embed.add_field(name="👥 Participants", value="None listed", inline=False)
            
            embed.add_field(name="⏰ Game Time", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)
            embed.set_author(name=f"Logged by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="Game completed successfully!")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating game log: {str(e)}", ephemeral=True)

    @app_commands.command(name="spinwheel", description="Spin a customizable pie wheel with up to 10 options")
    @app_commands.describe(title="Wheel title", options="Comma-separated options (up to 10)")
    async def spinwheel(self, interaction: discord.Interaction, title: str, options: str):
        option_list = [opt.strip() for opt in options.split(",") if opt.strip()]
        
        if len(option_list) < 2:
            await interaction.response.send_message("❌ Please provide at least 2 options separated by commas!", ephemeral=True)
            return
        
        if len(option_list) > 10:
            await interaction.response.send_message("❌ Maximum 10 options allowed!", ephemeral=True)
            return
        
        # Select winner
        winner = random.choice(option_list)
        
        # Create pie wheel image with title
        wheel_image_path = self.create_pie_wheel_image(option_list, title)
        
        embed = discord.Embed(
            title=f"🎡 {title}",
            description=f"🎊 **Winner: {winner}** 🎊",
            color=0xffd700,
            timestamp=datetime.now()
        )
        
        # Add all options
        options_text = "\n".join([f"{'🎯 ' if opt == winner else '• '}{opt}" for opt in option_list])
        embed.add_field(name="Available Options", value=options_text, inline=False)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="The wheel has spoken!")
        
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
        
        # Get user data from database
        user_data = db.get_user_data(target.id)
        xp = user_data.get('xp', 0)
        cookies = user_data.get('cookies', 0)
        coins = user_data.get('coins', 0)
        
        # Calculate level
        level = self.calculate_level_from_xp(xp)
        
        embed = discord.Embed(
            title=f"👤 User Info: {target.display_name}",
            color=target.accent_color or 0x7289da,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Basic info
        embed.add_field(name="👤 Username", value=f"{target.name}#{target.discriminator}", inline=True)
        embed.add_field(name="🆔 ID", value=target.id, inline=True)
        embed.add_field(name="🏆 Level", value=level, inline=True)
        
        # Server stats
        embed.add_field(name="📅 Account Created", value=f"<t:{int(target.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📅 Joined Server", value=f"<t:{int(target.joined_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📱 Status", value=str(target.status).title(), inline=True)
        
        # Economy stats
        embed.add_field(name="💰 Economy", value=f"XP: {xp:,}\nCoins: {coins:,}\nCookies: {cookies:,}", inline=True)
        
        # Roles (limit to avoid hitting embed limits)
        if target.roles[1:]:  # Skip @everyone role
            roles = [role.mention for role in reversed(target.roles[1:])]
            role_text = " ".join(roles[:10])
            if len(roles) > 10:
                role_text += f" and {len(roles) - 10} more..."
            embed.add_field(name="🎭 Roles", value=role_text, inline=False)

        await interaction.response.send_message(embed=embed)

    def calculate_level_from_xp(self, xp: int) -> int:
        """Calculate level from XP"""
        level = 0
        while self.calculate_xp_for_level(level + 1) <= xp:
            level += 1
        return level

    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required for level"""
        if level <= 10:
            return int(200 * (level ** 2))
        elif level <= 50:
            return int(300 * (level ** 2.2))
        elif level <= 100:
            return int(500 * (level ** 2.5))
        else:
            return int(1000 * (level ** 2.8))

    @app_commands.command(name="serverinfo", description="Shows stats and info about the server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"📈 Server Info: {guild.name}",
            color=0x7289da,
            timestamp=datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="📁 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="🚀 Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="💎 Boosts", value=guild.premium_subscription_count, inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check the bot's ping to Discord servers")
    async def ping(self, interaction: discord.Interaction):
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
            description=f"**Latency:** {latency}ms ({status})",
            color=color
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
                color=0x9932cc,
                timestamp=datetime.now()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="THE SAINT • AI-powered responses")
            embed.add_field(name="Question", value=question[:100] + ("..." if len(question) > 100 else ""), inline=False)

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
            color=0xffd700,
            timestamp=datetime.now()
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
                color=0x00ff00,
                timestamp=datetime.now()
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
        
