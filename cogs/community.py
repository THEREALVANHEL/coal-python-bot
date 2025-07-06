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
    def __init__(self, shout_data, original_message=None):
        super().__init__(timeout=None)
        self.shout_data = shout_data
        self.participants = set()
        self.original_message = original_message
        self.start_time = datetime.now()
        self.event_started = False
        self.event_ended = False

    def set_message(self, message):
        """Set the original message object for editing"""
        self.original_message = message

    def parse_time_string(self, time_str):
        """Parse time strings like '5m', '1h', '2h30m', '1d' etc."""
        if not time_str:
            return None
            
        time_str = time_str.lower().strip()
        total_seconds = 0
        
        # Extract days
        if 'd' in time_str:
            days_part = time_str.split('d')[0]
            if days_part.isdigit():
                total_seconds += int(days_part) * 86400
            time_str = time_str.split('d', 1)[1] if 'd' in time_str else ''
        
        # Extract hours  
        if 'h' in time_str:
            hours_part = time_str.split('h')[0]
            if hours_part.isdigit():
                total_seconds += int(hours_part) * 3600
            time_str = time_str.split('h', 1)[1] if 'h' in time_str else ''
            
        # Extract minutes
        if 'm' in time_str:
            minutes_part = time_str.split('m')[0]
            if minutes_part.isdigit():
                total_seconds += int(minutes_part) * 60
                
        return total_seconds if total_seconds > 0 else None

    @discord.ui.button(label="🔥 Join Event", style=discord.ButtonStyle.primary, emoji="🚀")
    async def join_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        # Check if event has ended
        if self.event_ended:
            await interaction.response.send_message("❌ This event has ended! No more participants can join.", ephemeral=True)
            return
        
        # Check if event has started (participants can still join if event hasn't started)
        if self.event_started:
            await interaction.response.send_message("❌ This event has already started! Registration is closed.", ephemeral=True)
            return
        
        if user_id in self.participants:
            await interaction.response.send_message("❌ You're already participating in this event!", ephemeral=True)
            return
        
        self.participants.add(user_id)
        await interaction.response.send_message(f"✅ You've joined **{self.shout_data['title']}**! Get ready! 🎉", ephemeral=True)
        
        # Update the embed with live participants visible to everyone
        await self.update_message_with_participants(interaction)

    @discord.ui.button(label="👋 Leave Event", style=discord.ButtonStyle.secondary, emoji="❌")
    async def leave_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        # Check if event has ended
        if self.event_ended:
            await interaction.response.send_message("❌ This event has ended! No changes can be made.", ephemeral=True)
            return
        
        # Allow leaving even if event has started (people might need to drop out)
        if user_id not in self.participants:
            await interaction.response.send_message("❌ You're not participating in this event!", ephemeral=True)
            return
        
        self.participants.discard(user_id)
        leave_message = f"👋 You've left **{self.shout_data['title']}**."
        
        if not self.event_started:
            leave_message += " You can rejoin before the event starts!"
        else:
            leave_message += " (Event already started - you won't be able to rejoin)"
            
        await interaction.response.send_message(leave_message, ephemeral=True)
        
        # Update the embed with live participants visible to everyone
        await self.update_message_with_participants(interaction)

    def is_event_organizer(self, user):
        """Check if user is the host or has organizer permissions"""
        # Check if user is the host or co-host
        user_name = user.display_name
        if (user_name == self.shout_data.get('host') or 
            user_name == self.shout_data.get('co_host')):
            return True
        
        # Check if user has announcement permissions
        return has_announce_permission(user.roles)

    @discord.ui.button(label="🟢 Start Event", style=discord.ButtonStyle.success, emoji="🚀")
    async def start_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only allow host/organizers to start event
        if not self.is_event_organizer(interaction.user):
            await interaction.response.send_message("❌ Only the event host/organizers can start the event!", ephemeral=True)
            return
        
        if self.event_started:
            await interaction.response.send_message("❌ Event has already been started!", ephemeral=True)
            return
        
        if self.event_ended:
            await interaction.response.send_message("❌ This event has already ended!", ephemeral=True)
            return
        
        # Start the event
        self.event_started = True
        self.shout_data['event_started_time'] = datetime.now()
        
        await interaction.response.send_message(
            f"🚀 **EVENT STARTED!** Registration is now closed. {len(self.participants)} participants locked in!", 
            ephemeral=False
        )
        
        # Update the embed
        await self.update_message_with_participants(interaction)

    @discord.ui.button(label="🔴 End Event", style=discord.ButtonStyle.danger, emoji="🏁")
    async def end_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only allow host/organizers to end event
        if not self.is_event_organizer(interaction.user):
            await interaction.response.send_message("❌ Only the event host/organizers can end the event!", ephemeral=True)
            return
        
        if self.event_ended:
            await interaction.response.send_message("❌ Event has already been ended!", ephemeral=True)
            return
        
        # End the event
        self.event_ended = True
        self.shout_data['event_ended_time'] = datetime.now()
        
        await interaction.response.send_message(
            f"🏁 **EVENT ENDED!** Thank you to all {len(self.participants)} participants! 🎉", 
            ephemeral=False
        )
        
        # Update the embed and disable most buttons
        await self.update_message_with_participants(interaction)

    @discord.ui.button(label="⏰ Set Time", style=discord.ButtonStyle.secondary, emoji="⏰")
    async def set_event_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Only allow event organizers to set time
        if not self.is_event_organizer(interaction.user):
            await interaction.response.send_message("❌ Only event organizers can set event times!", ephemeral=True)
            return
        
        if self.event_ended:
            await interaction.response.send_message("❌ Cannot modify an ended event!", ephemeral=True)
            return
        
        class TimeModal(discord.ui.Modal):
            def __init__(self, shout_view):
                super().__init__(title="⏰ Set Event Time")
                self.shout_view = shout_view
                
            time_input = discord.ui.TextInput(
                label="Event Time",
                placeholder="Examples: '1h', '30m', '2h30m', '1d', 'now'",
                max_length=50,
                required=True
            )
            
            async def on_submit(self, modal_interaction):
                time_str = self.time_input.value.strip().lower()
                
                if time_str == "now":
                    event_time = datetime.now()
                    time_display = "🔴 **LIVE NOW**"
                else:
                    duration = self.shout_view.parse_time_string(time_str)
                    if not duration:
                        await modal_interaction.response.send_message("❌ Invalid time format! Use examples like: 1h, 30m, 2h30m, 1d", ephemeral=True)
                        return
                    
                    event_time = datetime.now() + timedelta(seconds=duration)
                    time_display = f"⏰ <t:{int(event_time.timestamp())}:F>\n🕐 <t:{int(event_time.timestamp())}:R>"
                
                self.shout_view.shout_data['event_time'] = event_time
                self.shout_view.shout_data['time_display'] = time_display
                
                await modal_interaction.response.send_message(f"✅ Event time set to: {time_display}", ephemeral=True)
                await self.shout_view.update_message_with_participants(modal_interaction)
        
        modal = TimeModal(self)
        await interaction.response.send_modal(modal)

    async def update_message_with_participants(self, interaction):
        """Update the original message with current participants - visible to everyone"""
        if not self.original_message:
            return
        
        try:
            # Get participant names (show more participants with better formatting)
            participant_names = []
            for p_id in list(self.participants):
                try:
                    user = interaction.client.get_user(p_id)
                    if user:
                        participant_names.append(user.display_name)
                    else:
                        participant_names.append(f"User {p_id}")
                except:
                    participant_names.append(f"User {p_id}")
            
            # Format participants display
            if len(participant_names) == 0:
                participant_display = "*No participants yet - be the first to join!*"
            elif len(participant_names) <= 15:
                participant_display = "• " + "\n• ".join(participant_names)
            else:
                shown_names = participant_names[:15]
                participant_display = "• " + "\n• ".join(shown_names) + f"\n*...and {len(participant_names) - 15} more participants*"
            
            # Create updated embed with modern design and event status
            if self.event_ended:
                title_prefix = "🏁 [ENDED]"
                embed_color = 0x808080  # Gray for ended events
            elif self.event_started:
                title_prefix = "🔴 [LIVE]"
                embed_color = 0xff4444  # Red for live events
            else:
                title_prefix = "📢"
                embed_color = 0x00d4aa  # Teal for upcoming events
            
            embed = discord.Embed(
                title=f"{title_prefix} **{self.shout_data['title']}**",
                description=self.shout_data['description'],
                color=embed_color,
                timestamp=datetime.now()
            )
            
            # Event details with better formatting
            event_info = []
            if self.shout_data.get('host') != 'None':
                event_info.append(f"🎯 **Host:** {self.shout_data['host']}")
            if self.shout_data.get('co_host') != 'None':
                event_info.append(f"🤝 **Co-Host:** {self.shout_data['co_host']}")
            if self.shout_data.get('medic') != 'None':
                event_info.append(f"⚕️ **Medic:** {self.shout_data['medic']}")
            if self.shout_data.get('guide') != 'None':
                event_info.append(f"🗺️ **Guide:** {self.shout_data['guide']}")
                
            if event_info:
                embed.add_field(
                    name="👥 **Event Team**",
                    value="\n".join(event_info),
                    inline=True
                )
            
            # Time information with event status
            time_info = []
            if 'time_display' in self.shout_data:
                time_info.append(self.shout_data['time_display'])
            else:
                time_info.append(f"📅 Created: <t:{int(self.start_time.timestamp())}:R>")
            
            # Add event status timestamps
            if 'event_started_time' in self.shout_data:
                time_info.append(f"🚀 Started: <t:{int(self.shout_data['event_started_time'].timestamp())}:R>")
            if 'event_ended_time' in self.shout_data:
                time_info.append(f"🏁 Ended: <t:{int(self.shout_data['event_ended_time'].timestamp())}:R>")
                
            embed.add_field(
                name="⏰ **Event Timeline**",
                value="\n".join(time_info),
                inline=True
            )
            
            # Participants count with icon
            embed.add_field(
                name="👥 **Participation Status**",
                value=f"👥 **{len(self.participants)}** participants\n{'� Event completed!' if self.event_ended else '🔴 Event in progress!' if self.event_started else '🟢 Registration open!'}",
                inline=True
            )
            
            # Live participants list - visible to everyone
            embed.add_field(
                name="🔥 **Live Participants**",
                value=participant_display,
                inline=False
            )
            
            # Add contextual footer based on event status
            if self.event_ended:
                footer_text = f"🏁 Event ended with {len(self.participants)} participants. Thanks for joining!"
            elif self.event_started:
                footer_text = f"🔴 Event in progress with {len(self.participants)} participants!"
            elif len(self.participants) == 0:
                footer_text = "🚀 Be the first to join this epic event!"
            elif len(self.participants) < 5:
                footer_text = f"🎉 {len(self.participants)} brave souls have joined! Who's next?"
            else:
                footer_text = f"🔥 {len(self.participants)} participants and counting! The hype is real!"
                
            embed.set_footer(text=footer_text)
            
            # Disable buttons based on event status
            for item in self.children:
                if hasattr(item, 'label'):
                    if self.event_ended:
                        # Disable all buttons when event is ended except Set Time for reference
                        if item.label not in ["⏰ Set Time"]:
                            item.disabled = True
                    elif self.event_started:
                        # When event is started, disable join but allow leave and organizer controls
                        if item.label == "🔥 Join Event":
                            item.disabled = True
                        elif item.label == "🟢 Start Event":
                            item.disabled = True
            
            # Update the original message visible to everyone
            await self.original_message.edit(embed=embed, view=self)
            
        except Exception as e:
            print(f"Error updating shout message: {e}")
            # Fallback - try to send a new message if editing fails
            pass

GUILD_ID = 1370009417726169250

# Specific roles that can use shout and gamelog commands
ANNOUNCE_ROLE_IDS = [1378338515791904808, 1371003310223654974]

def has_announce_permission(user_roles):
    """Check if user has announcement permissions based on role IDs"""
    user_role_ids = [role.id for role in user_roles]
    return any(role_id in ANNOUNCE_ROLE_IDS for role_id in user_role_ids)

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
        """Create a modern, professional wheel with premium fonts and sleek design"""
        try:
            # Create ultra high-quality image
            size = 1200  # Ultra high resolution for crisp quality
            img = Image.new('RGBA', (size, size), (30, 30, 30, 255))  # Dark background
            draw = ImageDraw.Draw(img)
            
            # Center and radius
            center = size // 2
            radius = center - 150  # More margin for text
            
            # Modern vibrant color palette - professional and attractive
            colors = [
                '#FF6B6B',  # Coral Red
                '#4ECDC4',  # Teal
                '#45B7D1',  # Sky Blue
                '#96CEB4',  # Mint Green
                '#FFEAA7',  # Light Yellow
                '#DDA0DD',  # Plum
                '#98D8C8',  # Mint
                '#F7DC6F',  # Gold
                '#BB8FCE',  # Lavender
                '#85C1E9'   # Light Blue
            ]
            
            # Calculate angles for each slice
            num_options = len(options)
            angle_per_slice = 360 / num_options
            
            # Find winner index
            winner_index = options.index(winner) if winner in options else 0
            
            # Draw outer glow effect
            glow_radius = radius + 20
            for i in range(10):
                alpha = 30 - (i * 3)
                glow_color = f'rgba(255, 255, 255, {alpha})'
                current_radius = glow_radius - (i * 2)
                draw.ellipse([center - current_radius, center - current_radius, 
                             center + current_radius, center + current_radius], 
                            fill=f'#FFFFFF{alpha:02x}', outline=None)
            
            # Draw pie slices
            start_angle = 0
            for i, option in enumerate(options):
                end_angle = start_angle + angle_per_slice
                color = colors[i % len(colors)]
                
                # Enhanced winner highlighting with rainbow glow
                if i == winner_index:
                    outline_color = '#FFD700'  # Golden
                    outline_width = 15
                    # Add rainbow glowing effect for winner
                    for j in range(5):
                        glow_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFEAA7', '#DDA0DD']
                        glow_radius = radius + 15 - (j * 3)
                        draw.pieslice(
                            [center - glow_radius, center - glow_radius, center + glow_radius, center + glow_radius],
                            start_angle, end_angle, fill=f'{glow_colors[j % len(glow_colors)]}40', outline=None
                        )
                else:
                    outline_color = '#2C2C2C'
                    outline_width = 8
                
                # Draw the main slice
                draw.pieslice(
                    [center - radius, center - radius, center + radius, center + radius],
                    start_angle, end_angle, fill=color, outline=outline_color, width=outline_width
                )
                
                # Calculate text position optimally
                mid_angle = math.radians(start_angle + angle_per_slice / 2)
                text_radius = radius * 0.7  # Optimal position for readability
                text_x = center + text_radius * math.cos(mid_angle)
                text_y = center + text_radius * math.sin(mid_angle)
                
                # Load premium fonts with multiple fallbacks
                font = None
                font_size = 60  # Larger font for better visibility
                font_paths = [
                    # Try system fonts first
                    "arial.ttf",
                    "Arial.ttf", 
                    "/System/Library/Fonts/Arial.ttf",
                    "/System/Library/Fonts/Helvetica.ttc",
                    # Try custom fonts from assets
                    os.path.join(os.path.dirname(__file__), '..', 'assets', 'Poppins-Bold.ttf'),
                    os.path.join(os.path.dirname(__file__), '..', 'assets', 'Arial-Bold.ttf'),
                ]
                
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
                
                if not font:
                    # Ultimate fallback
                    font = ImageFont.load_default()
                
                # Get text size for centering
                bbox = draw.textbbox((0, 0), option, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Smart text color selection for maximum contrast
                def get_brightness(hex_color):
                    hex_color = hex_color.lstrip('#')
                    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    return (r * 299 + g * 587 + b * 114) / 1000
                
                brightness = get_brightness(color)
                text_color = '#FFFFFF' if brightness < 128 else '#000000'
                
                # Draw premium text with multiple shadow layers for depth
                shadow_colors = ['#000000BB', '#00000088', '#00000055']
                shadow_offsets = [6, 4, 2]
                
                for shadow_color, offset in zip(shadow_colors, shadow_offsets):
                    draw.text((text_x - text_width//2 + offset, text_y - text_height//2 + offset), 
                             option, font=font, fill=shadow_color)
                
                # Draw main text with stroke effect
                stroke_width = 3
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx != 0 or dy != 0:
                            draw.text((text_x - text_width//2 + dx, text_y - text_height//2 + dy), 
                                     option, font=font, fill='#000000' if text_color == '#FFFFFF' else '#FFFFFF')
                
                draw.text((text_x - text_width//2, text_y - text_height//2), 
                         option, font=font, fill=text_color)
                
                start_angle = end_angle
            
            # Draw ultra-modern center hub with gradient effect
            center_radius = 60  # Larger for better visibility
            
            # Create gradient effect for center hub
            for i in range(center_radius):
                alpha = 255 - (i * 3)
                gradient_radius = center_radius - i
                gradient_color = f'#1E1E1E{alpha:02x}' if alpha > 0 else '#1E1E1E00'
                draw.ellipse([center - gradient_radius, center - gradient_radius, 
                             center + gradient_radius, center + gradient_radius], 
                            fill=gradient_color, outline=None)
            
            # Outer ring - premium metallic look
            draw.ellipse([center - center_radius, center - center_radius, 
                         center + center_radius, center + center_radius], 
                        fill='#2C2C2C', outline='#FFD700', width=8)
            
            # Inner circle - glossy finish
            inner_radius = center_radius - 18
            draw.ellipse([center - inner_radius, center - inner_radius, 
                         center + inner_radius, center + inner_radius], 
                        fill='#1A1A1A', outline='#404040', width=4)
            
            # Ultra center dot - crystal effect
            dot_radius = 12
            draw.ellipse([center - dot_radius, center - dot_radius, 
                         center + dot_radius, center + dot_radius], 
                        fill='#FFD700', outline='#FFA500', width=2)
            
            # Draw ultra-modern arrow pointing to winner
            if winner:
                winner_angle = math.radians(winner_index * angle_per_slice + angle_per_slice / 2)
                
                # Premium arrow design
                arrow_length = 120  # Longer for better visibility
                arrow_width = 16   # Thicker for modern look
                arrow_start_radius = center_radius + 15
                arrow_end_radius = arrow_start_radius + arrow_length
                
                # Calculate arrow center line
                arrow_start_x = center + arrow_start_radius * math.cos(winner_angle)
                arrow_start_y = center + arrow_start_radius * math.sin(winner_angle)
                arrow_end_x = center + arrow_end_radius * math.cos(winner_angle)
                arrow_end_y = center + arrow_end_radius * math.sin(winner_angle)
                
                # Draw arrow with gradient effect
                gradient_colors = ['#FFD700', '#FFA500', '#FF8C00']
                for i, color in enumerate(gradient_colors):
                    width = arrow_width - (i * 4)
                    if width > 0:
                        draw.line([(arrow_start_x, arrow_start_y), (arrow_end_x, arrow_end_y)], 
                                 fill=color, width=width)
                
                # Draw premium arrowhead with glow
                arrow_head_size = 24  # Larger for impact
                head_angle1 = winner_angle + math.pi * 0.8
                head_angle2 = winner_angle - math.pi * 0.8
                
                head_x1 = arrow_end_x + arrow_head_size * math.cos(head_angle1)
                head_y1 = arrow_end_y + arrow_head_size * math.sin(head_angle1)
                head_x2 = arrow_end_x + arrow_head_size * math.cos(head_angle2)
                head_y2 = arrow_end_y + arrow_head_size * math.sin(head_angle2)
                
                # Glowing arrow head effect
                glow_colors = ['#FFD70080', '#FFD700BB', '#FFD700']
                glow_sizes = [28, 26, 24]
                
                for glow_color, glow_size in zip(glow_colors, glow_sizes):
                    head_x1_glow = arrow_end_x + glow_size * math.cos(head_angle1)
                    head_y1_glow = arrow_end_y + glow_size * math.sin(head_angle1)
                    head_x2_glow = arrow_end_x + glow_size * math.cos(head_angle2)
                    head_y2_glow = arrow_end_y + glow_size * math.sin(head_angle2)
                    
                    draw.polygon([(arrow_end_x, arrow_end_y), (head_x1_glow, head_y1_glow), (head_x2_glow, head_y2_glow)], 
                               fill=glow_color, outline=None)
            
            # Draw premium title with modern typography
            title_font = None
            title_font_size = 85  # Larger for impact
            title_font_paths = [
                "arial.ttf",
                "Arial.ttf",
                "/System/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                os.path.join(os.path.dirname(__file__), '..', 'assets', 'Poppins-Bold.ttf'),
            ]
            
            for font_path in title_font_paths:
                try:
                    title_font = ImageFont.truetype(font_path, title_font_size)
                    break
                except:
                    continue
            
            if not title_font:
                title_font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            title_x = center - title_width // 2
            title_y = 60
            
            # Create title with multiple effects
            # Outer glow
            glow_colors = ['#FFD70020', '#FFD70040', '#FFD70060', '#FFD70080']
            glow_offsets = [8, 6, 4, 2]
            
            for glow_color, offset in zip(glow_colors, glow_offsets):
                for dx in range(-offset, offset + 1):
                    for dy in range(-offset, offset + 1):
                        if dx*dx + dy*dy <= offset*offset:
                            draw.text((title_x + dx, title_y + dy), title, font=title_font, fill=glow_color)
            
            # Main title with gradient effect simulation
            gradient_colors = ['#FFD700', '#FFA500', '#FF8C00']
            for i, color in enumerate(gradient_colors):
                y_offset = i * 2
                draw.text((title_x, title_y + y_offset), title, font=title_font, fill=color)
            
            # Add modern geometric decorations
            decoration_size = 40
            decoration_thickness = 8
            decoration_color = '#FFD700'
            
            # Top decorations - modern lines
            draw.rectangle([50, 30, 50 + decoration_size * 2, 30 + decoration_thickness], fill=decoration_color)
            draw.rectangle([size - 50 - decoration_size * 2, 30, size - 50, 30 + decoration_thickness], fill=decoration_color)
            
            # Side accent lines
            draw.rectangle([30, center - decoration_size, 30 + decoration_thickness, center + decoration_size], fill=decoration_color)
            draw.rectangle([size - 30 - decoration_thickness, center - decoration_size, size - 30, center + decoration_size], fill=decoration_color)
            
            # Bottom decorations - diamond shapes
            diamond_size = 20
            diamond_points = [
                (center - 200, size - 60),  # left
                (center - 200 + diamond_size, size - 60 - diamond_size),  # top
                (center - 200 + diamond_size * 2, size - 60),  # right
                (center - 200 + diamond_size, size - 60 + diamond_size)   # bottom
            ]
            draw.polygon(diamond_points, fill=decoration_color)
            
            diamond_points_right = [
                (center + 200, size - 60),  # left
                (center + 200 + diamond_size, size - 60 - diamond_size),  # top
                (center + 200 + diamond_size * 2, size - 60),  # right
                (center + 200 + diamond_size, size - 60 + diamond_size)   # bottom
            ]
            draw.polygon(diamond_points_right, fill=decoration_color)
            
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
        if not has_announce_permission(interaction.user.roles):
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
            
            # Create initial embed with modern design
            embed = discord.Embed(
                title=f"📢 **{title}**",
                description=description,
                color=0x00d4aa,  # Modern teal color
                timestamp=datetime.now()
            )
            
            # Event details
            event_info = []
            if host != 'None':
                event_info.append(f"🎯 **Host:** {host}")
            if co_host and co_host != 'None':
                event_info.append(f"🤝 **Co-Host:** {co_host}")
            if medic and medic != 'None':
                event_info.append(f"⚕️ **Medic:** {medic}")
            if guide and guide != 'None':
                event_info.append(f"🗺️ **Guide:** {guide}")
                
            if event_info:
                embed.add_field(
                    name="👥 **Event Team**",
                    value="\n".join(event_info),
                    inline=True
                )
            
            embed.add_field(
                name="⏰ **Event Time**",
                value=f"📅 Created: <t:{int(datetime.now().timestamp())}:R>",
                inline=True
            )
            
            embed.add_field(
                name="� **Participation**",
                value=f"👥 **0** joined\n🎯 Ready for action!",
                inline=True
            )
            
            embed.add_field(
                name="�🔥 **Live Participants**",
                value="*No participants yet - be the first to join!*",
                inline=False
            )
            
            embed.set_author(name=f"Event by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="🚀 Be the first to join this epic event!")
            
            # Create view and send message
            view = ShoutView(shout_data)
            message = await interaction.response.send_message(embed=embed, view=view)
            
            # Get the message object and set it in the view for editing
            msg = await interaction.original_response()
            view.set_message(msg)
            
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
        if not has_announce_permission(interaction.user.roles):
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
            # Enhanced prompt for efficient, direct responses
            prompt = f"""You are BleckNephew, a smart and efficient AI assistant. You're tech-savvy and give PRECISE, ACTIONABLE answers.

CORE RULES:
- Be DIRECT and TO THE POINT - no unnecessary rambling
- Give PRACTICAL solutions and specific steps
- Use bullet points for clarity when appropriate  
- Keep responses under 500 words unless absolutely necessary
- Include examples when they help understanding
- For technical questions: Give specific commands, code, or settings
- For general questions: Provide clear, actionable advice
- Always end with a specific next step the user can take

RESPONSE STYLE:
- Skip lengthy introductions
- Get straight to the answer
- Use emojis sparingly (1-2 max)
- Be confident and knowledgeable
- If you're unsure, say so briefly and suggest alternatives

USER QUESTION: {question}

Provide a focused, helpful response that gets straight to the point."""

            response = self.model.generate_content(prompt)
            
            if not response.text:
                await interaction.followup.send("❌ BleckNephew couldn't generate a response. Please try rephrasing your question.", ephemeral=True)
                return
            
            # Handle responses efficiently - prioritize clarity over length
            response_text = response.text.strip()
            
            # If response is too long, try to extract the most important parts
            if len(response_text) > 1500:
                # Try to find a good breaking point
                sentences = response_text.split('. ')
                truncated_response = ""
                
                for sentence in sentences:
                    if len(truncated_response + sentence + '. ') <= 1500:
                        truncated_response += sentence + '. '
                    else:
                        break
                
                if truncated_response:
                    response_text = truncated_response.strip()
                    if not response_text.endswith('.'):
                        response_text += '.'
                    response_text += "\n\n*Response optimized for clarity*"
                else:
                    # If we can't find good sentences, just truncate
                    response_text = response_text[:1500] + "...\n\n*Response truncated for clarity*"
            
            # Create clean, professional embed
            embed = discord.Embed(
                title="🤖 **BleckNephew AI**",
                description=response_text,
                color=0x4169E1,  # Royal blue for professionalism
                timestamp=datetime.now()
            )
            
            # Only show question if it's reasonably short
            if len(question) <= 150:
                embed.add_field(name="💭 **Question**", value=f"`{question}`", inline=False)
            
            embed.set_author(name=f"Asked by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="BleckNephew AI • Precise & Helpful")

            # Check for URLs and add buttons if found
            urls = extract_urls(response_text)
            if urls:
                view = LinkView(urls[:3])  # Limit to 3 URLs max
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
        if not has_announce_permission(interaction.user.roles):
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
        if not has_announce_permission(interaction.user.roles):
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
        
