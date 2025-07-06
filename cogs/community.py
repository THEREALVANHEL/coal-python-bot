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
            
            # Update the embed with new participant names (live update)
            participant_names = []
            for p_id in list(self.participants)[:10]:  # Show max 10 names to avoid embed limits
                try:
                    user = interaction.client.get_user(p_id)
                    if user:
                        participant_names.append(user.display_name)
                    else:
                        participant_names.append(f"User {p_id}")
                except:
                    participant_names.append(f"User {p_id}")
            
            if len(self.participants) > 10:
                participant_display = ", ".join(participant_names) + f" and {len(self.participants) - 10} more..."
            else:
                participant_display = ", ".join(participant_names) if participant_names else "None yet"
            
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
            embed.add_field(name="👥 Participants", value=f"**{len(self.participants)} joined**", inline=True)
            embed.add_field(name="⏰ Time", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
            embed.add_field(name="🔥 Live Participants", value=participant_display, inline=False)
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
        self.model = None
        if self.genai_api_key:
            try:
                genai.configure(api_key=self.genai_api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                print(f"[Community] Failed to initialize Gemini AI: {e}")
                self.model = None

    async def cog_load(self):
        print("[Community] Loaded successfully.")

    def create_pie_wheel_image(self, options, title="Spin the Wheel!", winner=None):
        """Create a professional and elegant wheel with larger options and golden title"""
        try:
            # Create a high-quality image - increased size for better quality
            size = 900  # Increased from 700 to 900
            img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # Center and radius
            center = size // 2
            radius = center - 120  # Increased margin for larger text
            
            # Simple elegant color palette - white, black, grays
            colors = [
                '#FFFFFF',  # Pure White
                '#000000',  # Pure Black  
                '#F5F5F5',  # Light Gray
                '#2C2C2C',  # Dark Gray
                '#E8E8E8',  # Lighter Gray
                '#404040',  # Medium Dark Gray
                '#FAFAFA',  # Off White
                '#1A1A1A',  # Near Black
                '#DDDDDD',  # Light Gray 2
                '#333333'   # Charcoal
            ]
            
            # Calculate angles for each slice
            num_options = len(options)
            angle_per_slice = 360 / num_options
            
            # Find winner index
            winner_index = options.index(winner) if winner in options else 0
            
            # Draw outer ring (shadow effect)
            shadow_radius = radius + 12
            draw.ellipse([center - shadow_radius, center - shadow_radius, 
                         center + shadow_radius, center + shadow_radius], 
                        fill='#00000030', outline=None)
            
            # Draw pie slices
            start_angle = 0
            for i, option in enumerate(options):
                end_angle = start_angle + angle_per_slice
                color = colors[i % len(colors)]
                
                # Enhanced winner highlighting with golden glow
                if i == winner_index:
                    outline_color = '#FFD700'  # Golden
                    outline_width = 10
                    # Add golden glowing effect for winner
                    glow_radius = radius + 8
                    draw.pieslice(
                        [center - glow_radius, center - glow_radius, center + glow_radius, center + glow_radius],
                        start_angle, end_angle, fill='#FFD70060', outline=None
                    )
                else:
                    outline_color = '#CCCCCC'
                    outline_width = 4
                
                # Draw the main slice
                draw.pieslice(
                    [center - radius, center - radius, center + radius, center + radius],
                    start_angle, end_angle, fill=color, outline=outline_color, width=outline_width
                )
                
                # Calculate text position - closer to edge for better visibility
                mid_angle = math.radians(start_angle + angle_per_slice / 2)
                text_radius = radius * 0.75  # Moved closer to edge
                text_x = center + text_radius * math.cos(mid_angle)
                text_y = center + text_radius * math.sin(mid_angle)
                
                # Load bigger font for options - much larger now
                try:
                    font_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'Poppins-Bold.ttf')
                    font = ImageFont.truetype(font_path, 48)  # Increased from 34 to 48
                except:
                    font = ImageFont.load_default()
                
                # Get text size for centering
                bbox = draw.textbbox((0, 0), option, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Choose text color based on background for better contrast
                text_color = '#000000' if color in ['#FFFFFF', '#F5F5F5', '#E8E8E8', '#FAFAFA', '#DDDDDD'] else '#FFFFFF'
                
                # Draw text with better shadow for visibility
                shadow_offset = 4
                draw.text((text_x - text_width//2 + shadow_offset, text_y - text_height//2 + shadow_offset), 
                         option, font=font, fill='#00000080')
                draw.text((text_x - text_width//2, text_y - text_height//2), 
                         option, font=font, fill=text_color)
                
                start_angle = end_angle
            
            # Draw modern center hub
            center_radius = 45  # Increased from 35 to 45
            # Outer ring - elegant black
            draw.ellipse([center - center_radius, center - center_radius, 
                         center + center_radius, center + center_radius], 
                        fill='#000000', outline='#333333', width=5)
            # Inner circle - clean white
            inner_radius = center_radius - 12
            draw.ellipse([center - inner_radius, center - inner_radius, 
                         center + inner_radius, center + inner_radius], 
                        fill='#FFFFFF', outline='#CCCCCC', width=3)
            
            # Draw sleek, smaller arrow pointing to winner
            if winner:
                winner_angle = math.radians(winner_index * angle_per_slice + angle_per_slice / 2)
                
                # Slightly larger arrow for better visibility
                arrow_length = 90  # Increased from 70 to 90
                arrow_width = 12  # Increased from 10 to 12
                arrow_start_radius = center_radius + 10
                arrow_end_radius = arrow_start_radius + arrow_length
                
                # Calculate arrow center line
                arrow_start_x = center + arrow_start_radius * math.cos(winner_angle)
                arrow_start_y = center + arrow_start_radius * math.sin(winner_angle)
                arrow_end_x = center + arrow_end_radius * math.cos(winner_angle)
                arrow_end_y = center + arrow_end_radius * math.sin(winner_angle)
                
                # Draw arrow shaft (elegant black)
                draw.line([(arrow_start_x, arrow_start_y), (arrow_end_x, arrow_end_y)], 
                         fill='#000000', width=arrow_width)
                
                # Draw smaller, more professional arrowhead
                arrow_head_size = 15  # Increased from 12 to 15
                head_angle1 = winner_angle + math.pi * 0.75
                head_angle2 = winner_angle - math.pi * 0.75
                
                head_x1 = arrow_end_x + arrow_head_size * math.cos(head_angle1)
                head_y1 = arrow_end_y + arrow_head_size * math.sin(head_angle1)
                head_x2 = arrow_end_x + arrow_head_size * math.cos(head_angle2)
                head_y2 = arrow_end_y + arrow_head_size * math.sin(head_angle2)
                
                # Arrow head with black fill
                draw.polygon([(arrow_end_x, arrow_end_y), (head_x1, head_y1), (head_x2, head_y2)], 
                           fill='#000000', outline='#333333', width=1)
            
            # Draw GOLDEN title with larger font
            try:
                title_font = ImageFont.truetype(font_path, 65)  # Increased from 48 to 65
            except:
                title_font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            title_x = center - title_width // 2
            title_y = 40
            
            # Golden title with elegant shadow
            draw.text((title_x + 4, title_y + 4), title, font=title_font, fill='#00000040')
            draw.text((title_x, title_y), title, font=title_font, fill='#FFD700')  # Golden color
            
            # Add simple elegant corner decorations
            corner_size = 30  # Increased from 25 to 30
            decoration_color = '#FFD700'  # Golden decorations
            # Top-left
            draw.arc([20, 20, 20 + corner_size, 20 + corner_size], 180, 270, fill=decoration_color, width=5)
            # Top-right  
            draw.arc([size - corner_size - 20, 20, size - 20, 20 + corner_size], 270, 360, fill=decoration_color, width=5)
            # Bottom-left
            draw.arc([20, size - corner_size - 20, 20 + corner_size, size - 20], 90, 180, fill=decoration_color, width=5)
            # Bottom-right
            draw.arc([size - corner_size - 20, size - corner_size - 20, size - 20, size - 20], 0, 90, fill=decoration_color, width=5)
            
            # Save the image
            output_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'temp_wheel.png')
            img.save(output_path)
            return output_path
            
        except Exception as e:
            print(f"Error creating elegant wheel image: {e}")
            return None

    @app_commands.command(name="suggest", description="💡 Submit suggestions to improve the server (with optional media)")
    @app_commands.describe(
        suggestion="Your suggestion to improve the server",
        image="Optional image/GIF attachment",
        additional_notes="Additional notes or context (optional)"
    )
    async def suggest(self, interaction: discord.Interaction, suggestion: str, 
                      image: discord.Attachment = None, additional_notes: str = None):
        try:
            # Get the suggestion channel from settings
            suggest_channel_id = db.get_guild_setting(interaction.guild.id, "suggest_channel", None)
            
            if suggest_channel_id:
                suggest_channel = self.bot.get_channel(suggest_channel_id)
                if not suggest_channel:
                    embed = discord.Embed(
                        title="❌ Configuration Error",
                        description="Suggestion channel not found! Please contact an administrator.",
                        color=0xff6b6b
                    )
                    embed.set_footer(text="💫 Admin: Use /quicksetup to configure the suggestion channel")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
            else:
                embed = discord.Embed(
                    title="❌ Setup Required",
                    description="No suggestion channel configured! Ask an admin to set up the suggestion system.",
                    color=0xff9966
                )
                embed.add_field(
                    name="🔧 For Admins",
                    value="Use `/quicksetup` to configure the suggestions channel quickly!",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Create enhanced suggestion embed
            embed = discord.Embed(
                title="💡 **Community Suggestion**",
                description=suggestion,
                color=0x7c3aed,
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"Suggested by {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Add additional notes if provided
            if additional_notes:
                embed.add_field(
                    name="📝 **Additional Notes**",
                    value=additional_notes,
                    inline=False
                )
            
            embed.add_field(
                name="📊 **Community Voting**",
                value="React with ✅ to support or ❌ if you disagree",
                inline=False
            )
            embed.set_footer(text=f"User ID: {interaction.user.id} • Enhanced Suggestion System")
            
            # Handle image attachment
            files = []
            has_media = False
            if image:
                # Validate image
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov', '.webm']
                if any(image.filename.lower().endswith(ext) for ext in valid_extensions):
                    embed.set_image(url=f"attachment://{image.filename}")
                    files.append(await image.to_file())
                    has_media = True
                    
                    # Add media info
                    file_type = "🎥 Video" if any(image.filename.lower().endswith(ext) for ext in ['.mp4', '.mov', '.webm']) else "🖼️ Image"
                    embed.add_field(
                        name="📎 **Media Attachment**",
                        value=f"{file_type} - {image.filename}",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="⚠️ **Attachment Warning**",
                        value="Unsupported file type. Use: .jpg, .png, .gif, .webp, .mp4",
                        inline=False
                    )
            
            # Send complete suggestion with attachments
            if files:
                message = await suggest_channel.send(embed=embed, files=files)
            else:
                message = await suggest_channel.send(embed=embed)
            
            # Add voting reactions
            await message.add_reaction("✅")
            await message.add_reaction("❌")
            
            # Success response with modern design
            success_embed = discord.Embed(
                title="✨ **Suggestion Submitted Successfully**",
                description=f"Your suggestion has been forwarded to {suggest_channel.mention} for community review.",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            # Add what was included
            included_items = ["📝 Main suggestion"]
            if has_media:
                included_items.append("📎 Media attachment")
            if additional_notes:
                included_items.append("📋 Additional notes")
            
            success_embed.add_field(
                name="📦 **What's Included**",
                value="\n".join(included_items),
                inline=True
            )
            
            success_embed.add_field(
                name="🚀 **What Happens Next?**",
                value="The community will vote on your suggestion using reactions. Popular suggestions may be implemented!",
                inline=False
            )
            success_embed.set_footer(text="💡 Thank you for helping improve our community!")
            await interaction.response.send_message(embed=success_embed, ephemeral=True)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Submission Failed",
                description="Failed to submit your suggestion. Please try again later.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="💡 Troubleshooting",
                value="• Check if your file is under Discord's size limit\n• Ensure the image format is supported\n• Try again without attachments if issues persist",
                inline=False
            )
            error_embed.set_footer(text="💫 If this persists, contact an administrator")
            await interaction.response.send_message(embed=error_embed, ephemeral=True)



    @app_commands.command(name="shout", description="Create a detailed event announcement with live participant tracking")
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
            embed.add_field(name="👥 Participants", value="**0 joined**", inline=True)
            embed.add_field(name="⏰ Time", value=f"<t:{int(datetime.now().timestamp())}:R>", inline=True)
            embed.add_field(name="🔥 Live Participants", value="None yet - be the first to join!", inline=False)
            embed.set_author(name=f"Event by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="Click the button below to join!")
            
            view = ShoutView(shout_data)
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating shout: {str(e)}", ephemeral=True)

    @app_commands.command(name="gamelog", description="Log a completed game with detailed information and optional picture")
    @app_commands.describe(
        title="Game title",
        summary="Game summary",
        host="Game host",
        co_host="Co-host (optional)",
        medic="Medic (optional)",
        guide="Guide (optional)",
        participants="Participants (comma-separated)",
        picture="Picture URL (optional)"
    )
    async def gamelog(self, interaction: discord.Interaction, title: str, summary: str, host: str,
                     co_host: str = None, medic: str = None, guide: str = None, participants: str = None, picture: str = None):
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
            
            # Add picture if provided
            if picture:
                # Basic URL validation
                if picture.startswith(('http://', 'https://')) and any(picture.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    embed.set_image(url=picture)
                    embed.add_field(name="📸 Game Picture", value="Picture attached above", inline=False)
                else:
                    embed.add_field(name="⚠️ Picture", value="Invalid picture URL provided", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating game log: {str(e)}", ephemeral=True)

    @app_commands.command(name="spinwheel", description="Spin an enhanced wheel with arrow pointing to winner")
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
        
        # Create enhanced pie wheel image with arrow pointing to winner
        wheel_image_path = self.create_pie_wheel_image(option_list, title, winner)
        
        embed = discord.Embed(
            title=f"🎡 {title}",
            description=f"🎊 **WINNER: {winner}** 🎊",
            color=0xffd700,
            timestamp=datetime.now()
        )
        
        # Add all options with winner highlighted
        options_text = "\n".join([f"{'🏆 **' + opt + '**' if opt == winner else '• ' + opt}" for opt in option_list])
        embed.add_field(name="🎯 All Options", value=options_text, inline=False)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="🎯 The arrow points to the winner!")
        
        # Add wheel image if created successfully
        if wheel_image_path:
            file = discord.File(wheel_image_path, filename="enhanced_wheel.png")
            embed.set_image(url="attachment://enhanced_wheel.png")
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
        embed.add_field(name="👤 Username", value=f"{target.name}", inline=True)
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

    @app_commands.command(name="askblecknephew", description="Ask your nephew BleckNephew anything!")
    @app_commands.describe(question="Your question for BleckNephew")
    async def askblecknephew(self, interaction: discord.Interaction, question: str):
        if not self.genai_api_key or not self.model:
            embed = discord.Embed(
                title="❌ AI Service Unavailable",
                description="BleckNephew is currently unavailable. The Gemini AI service is not configured properly.",
                color=0xff6b6b
            )
            embed.add_field(
                name="🔧 Admin Note",
                value="Please set the `GEMINI_API_KEY` environment variable with a valid Google Gemini API key.",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Enhanced prompt for comprehensive responses
            prompt = f"""You are 'BleckNephew' - a helpful, knowledgeable, and friendly AI assistant. You are someone's nephew who's really good with technology and answering questions. 

INSTRUCTIONS:
- Always respond in a helpful, friendly manner as if you're actually their nephew
- For complex topics, provide detailed explanations
- For simple questions, give concise but complete answers
- Include relevant links when helpful (use full URLs)
- Use emojis appropriately to make responses engaging
- If asked about images, explain what you would show if you could generate images
- Break down complex topics into easy-to-understand parts
- Be conversational and approachable

Question: {question}

Please provide a comprehensive, helpful response."""

            response = self.model.generate_content(prompt)
            
            if not response.text:
                await interaction.followup.send("❌ BleckNephew couldn't generate a response. Please try rephrasing your question.", ephemeral=True)
                return
            
            # Handle long responses by splitting them
            response_text = response.text
            if len(response_text) > 2000:
                # Split into chunks
                chunks = []
                current_chunk = ""
                words = response_text.split()
                
                for word in words:
                    if len(current_chunk + word + " ") <= 2000:
                        current_chunk += word + " "
                    else:
                        chunks.append(current_chunk.strip())
                        current_chunk = word + " "
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Send first chunk as main response
                embed = discord.Embed(
                    title="🤖 BleckNephew Responds",
                    description=chunks[0],
                    color=0x9932cc,
                    timestamp=datetime.now()
                )
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text="BleckNephew • Your helpful AI nephew")
                embed.add_field(name="❓ Your Question", value=f"```{question[:500] + ('...' if len(question) > 500 else '')}```", inline=False)
                
                if len(chunks) > 1:
                    embed.add_field(name="📄 Response", value=f"Part 1 of {len(chunks)}", inline=False)
                
                # Check for URLs and add buttons if found
                urls = extract_urls(response_text)
                if urls:
                    view = LinkView(urls)
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    await interaction.followup.send(embed=embed)
                
                # Send additional chunks
                for i, chunk in enumerate(chunks[1:], 2):
                    embed = discord.Embed(
                        title=f"🤖 BleckNephew Responds (Part {i})",
                        description=chunk,
                        color=0x9932cc,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text="BleckNephew • Your helpful AI nephew")
                    await interaction.followup.send(embed=embed)
                    
            else:
                # Short response - send normally
                embed = discord.Embed(
                    title="🤖 BleckNephew Responds",
                    description=response_text,
                    color=0x9932cc,
                    timestamp=datetime.now()
                )
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
                embed.set_footer(text="BleckNephew • Your helpful AI nephew")
                embed.add_field(name="❓ Your Question", value=f"```{question[:500] + ('...' if len(question) > 500 else '')}```", inline=False)

                # Check for URLs and add buttons if found
                urls = extract_urls(response_text)
                if urls:
                    view = LinkView(urls)
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    await interaction.followup.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error generating response",
                description="BleckNephew encountered an issue while processing your question.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="Error Details",
                value=f"```{str(e)[:500]}```",
                inline=False
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

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

    @app_commands.command(name="announce", description="Creates a professional pointwise announcement with optional attachments")
    @app_commands.describe(
        channel="Channel to send the announcement",
        title="📢 Main announcement title",
        points="Announcement points separated by commas (e.g., 'Point 1, Point 2, Point 3')",
        additional_info="Optional additional information or context",
        attachment_url="Optional image/video URL to include"
    )
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, title: str, points: str, 
                      additional_info: str = None, attachment_url: str = None):
        # Check if user has required role
        user_roles = [role.name for role in interaction.user.roles]
        if not any(role in ANNOUNCE_ROLES for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return

        try:
            # Process points into a formatted list
            point_list = [point.strip() for point in points.split(',') if point.strip()]
            
            if len(point_list) == 0:
                await interaction.response.send_message("❌ Please provide at least one announcement point!", ephemeral=True)
                return
            
            if len(point_list) > 15:
                await interaction.response.send_message("❌ Maximum 15 points allowed for readability!", ephemeral=True)
                return

            # Create professional announcement embed
            embed = discord.Embed(
                title=f"📢 **{title}**",
                color=0x3498db,
                timestamp=datetime.now()
            )
            
            # Format points with professional styling using numbers
            formatted_points = []
            
            for i, point in enumerate(point_list, 1):
                formatted_points.append(f"**{i}.** {point}")
            
            # Add main points section
            points_text = "\n".join(formatted_points)
            embed.add_field(
                name="📋 **Key Points**",
                value=points_text,
                inline=False
            )
            
            # Add additional info if provided
            if additional_info:
                embed.add_field(
                    name="ℹ️ **Additional Information**",
                    value=additional_info,
                    inline=False
                )
            
            # Add attachment if provided
            if attachment_url:
                # Basic URL validation
                if attachment_url.startswith(('http://', 'https://')):
                    # Check if it's an image/video
                    if any(attachment_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mov', '.webm']):
                        embed.set_image(url=attachment_url)
                        embed.add_field(
                            name="📎 **Attachment**",
                            value="Media attachment included above",
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="🔗 **Link**",
                            value=f"[Click here to view]({attachment_url})",
                            inline=False
                        )
                else:
                    embed.add_field(
                        name="⚠️ **Attachment Warning**",
                        value="Invalid attachment URL format",
                        inline=False
                    )
            
            # Set author and footer
            embed.set_author(
                name=f"{interaction.guild.name} • Official Announcement",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            embed.set_footer(text=f"📢 Announced by {interaction.user.display_name} • {datetime.now().strftime('%B %d, %Y')}")
            
            # Send the announcement
            await channel.send(embed=embed)
            
            # Success response with preview
            success_embed = discord.Embed(
                title="✅ **Announcement Posted Successfully!**",
                description=f"Your announcement has been posted in {channel.mention}",
                color=0x00d4aa,
                timestamp=datetime.now()
            )
            
            success_embed.add_field(
                name="📊 **Announcement Summary**",
                value=f"**Title:** {title}\n**Points:** {len(point_list)}\n**Additional Info:** {'✅ Yes' if additional_info else '❌ No'}\n**Attachment:** {'✅ Yes' if attachment_url else '❌ No'}",
                inline=False
            )
            
            success_embed.set_footer(text="🎯 Professional announcement system")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}!", ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ **Announcement Failed**",
                description="Failed to create announcement. Please check your inputs and try again.",
                color=0xff6b6b
            )
            error_embed.add_field(
                name="🔍 **Error Details**",
                value=f"```{str(e)[:200]}```",
                inline=False
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)

    @app_commands.command(name="remind", description="Set a reminder for yourself")
    @app_commands.describe(
        time="Time to remind you (e.g., 5m, 1h, 2d)",
        reminder="What to remind you about"
    )
    async def remind(self, interaction: discord.Interaction, time: str, reminder: str):
        """Set a reminder for the user"""
        try:
            # Parse time
            time_seconds = self.parse_time(time)
            if time_seconds is None:
                embed = discord.Embed(
                    title="❌ Invalid Time Format",
                    description="Please use formats like: `5m`, `1h`, `2d`, `1w`",
                    color=0xff6b6b
                )
                embed.add_field(
                    name="📝 Examples",
                    value="• `5m` = 5 minutes\n• `1h` = 1 hour\n• `2d` = 2 days\n• `1w` = 1 week",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            if time_seconds > 604800:  # 1 week max
                embed = discord.Embed(
                    title="❌ Time Too Long",
                    description="Maximum reminder time is 1 week (7 days).",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Confirm reminder set
            reminder_time = datetime.now() + timedelta(seconds=time_seconds)
            embed = discord.Embed(
                title="⏰ Reminder Set!",
                description=f"I'll remind you about: **{reminder}**",
                color=0x00d4aa,
                timestamp=reminder_time
            )
            embed.add_field(
                name="⏱️ Reminder Time",
                value=f"<t:{int(reminder_time.timestamp())}:R>",
                inline=False
            )
            embed.set_footer(text="Reminder will be sent")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Wait and send reminder
            await asyncio.sleep(time_seconds)
            
            reminder_embed = discord.Embed(
                title="⏰ Reminder!",
                description=f"**{reminder}**",
                color=0xffd700,
                timestamp=datetime.now()
            )
            reminder_embed.set_author(
                name=f"Reminder for {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            reminder_embed.add_field(
                name="⏱️ Set",
                value=f"<t:{int((datetime.now() - timedelta(seconds=time_seconds)).timestamp())}:R>",
                inline=False
            )
            reminder_embed.set_footer(text="🔔 Reminder System")
            
            try:
                await interaction.user.send(embed=reminder_embed)
            except discord.Forbidden:
                # If DMs are disabled, send in the channel
                await interaction.followup.send(f"{interaction.user.mention}", embed=reminder_embed)
                
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Reminder Error",
                description="Failed to set reminder. Please try again.",
                color=0xff6b6b
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    def parse_time(self, time_str: str) -> int:
        """Parse time string into seconds"""
        try:
            time_str = time_str.lower().strip()
            
            # Extract number and unit
            import re
            match = re.match(r'^(\d+)([smhdw])$', time_str)
            if not match:
                return None
                
            amount = int(match.group(1))
            unit = match.group(2)
            
            multipliers = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400,
                'w': 604800
            }
            
            return amount * multipliers.get(unit, 0)
        except:
            return None

async def setup(bot: commands.Bot):
    await bot.add_cog(Community(bot))
        
