import discord
from discord.ext import commands
import random
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from assets.media_links import WELCOME_GIF, LEAVE_GIF

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[Events] Loaded successfully.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Ignore messages without content
        if not message.content:
            return

        # Give XP for messages
        try:
            # Random XP between 15-25
            xp_gain = random.randint(15, 25)
            
            # Check for XP cooldown (prevent spam)
            user_data = db.get_user_data(message.author.id)
            last_xp_time = user_data.get('last_xp_time', 0)
            current_time = message.created_at.timestamp()
            
            # 1 minute cooldown
            if current_time - last_xp_time >= 60:
                old_xp = user_data.get('xp', 0)
                new_xp = old_xp + xp_gain
                
                # Calculate level
                old_level = self.calculate_level_from_xp(old_xp)
                new_level = self.calculate_level_from_xp(new_xp)
                
                # Update database
                db.add_xp(message.author.id, xp_gain)
                db.update_last_xp_time(message.author.id, current_time)
                
                # Check for level up
                if new_level > old_level:
                    await self.handle_level_up(message, new_level)

        except Exception as e:
            print(f"Error processing XP for message: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            # Get welcome channel
            welcome_channel_id = db.get_guild_setting(member.guild.id, "welcome_channel", None)
            if welcome_channel_id:
                channel = self.bot.get_channel(welcome_channel_id)
                if channel:
                    embed = discord.Embed(
                        title="👋 Welcome!",
                        description=f"Welcome to **{member.guild.name}**, {member.mention}!",
                        color=0x00ff00
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(name="Member Count", value=f"You're member #{member.guild.member_count}!", inline=False)
                    embed.set_image(url=WELCOME_GIF)
                    await channel.send(embed=embed)

        except Exception as e:
            print(f"Error in on_member_join: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            # Get goodbye channel
            goodbye_channel_id = db.get_guild_setting(member.guild.id, "goodbye_channel", None)
            if goodbye_channel_id:
                channel = self.bot.get_channel(goodbye_channel_id)
                if channel:
                    embed = discord.Embed(
                        title="👋 Goodbye",
                        description=f"**{member.display_name}** has left the server",
                        color=0xff6b6b
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_image(url=LEAVE_GIF)
                    
                    await channel.send(embed=embed)

        except Exception as e:
            print(f"Error in on_member_remove: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            # Handle starboard
            if str(payload.emoji) == "⭐":
                await self.handle_starboard(payload)

        except Exception as e:
            print(f"Error in on_raw_reaction_add: {e}")

    async def handle_starboard(self, payload):
        try:
            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return

            # Check if starboard is enabled
            starboard_enabled = db.get_guild_setting(guild.id, "starboard_enabled", False)
            if not starboard_enabled:
                return

            # Get starboard channel
            starboard_channel_id = db.get_guild_setting(guild.id, "starboard_channel", None)
            if not starboard_channel_id:
                return

            starboard_channel = guild.get_channel(starboard_channel_id)
            if not starboard_channel:
                return

            # Get the message
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            # Count star reactions
            star_count = 0
            for reaction in message.reactions:
                if str(reaction.emoji) == "⭐":
                    star_count = reaction.count
                    break

            # Get threshold
            threshold = db.get_guild_setting(guild.id, "starboard_threshold", 5)

            # Check if message meets threshold
            if star_count >= threshold:
                # Check if already in starboard
                existing = db.get_starboard_message(message.id)
                if not existing:
                    # Create starboard entry
                    embed = discord.Embed(
                        description=message.content or "*No text content*",
                        color=0xffd700,
                        timestamp=message.created_at
                    )
                    embed.set_author(
                        name=message.author.display_name,
                        icon_url=message.author.display_avatar.url
                    )
                    embed.add_field(
                        name="Source",
                        value=f"[Jump to Message]({message.jump_url})",
                        inline=False
                    )

                    # Add attachments
                    if message.attachments:
                        embed.set_image(url=message.attachments[0].url)

                    starboard_msg = await starboard_channel.send(
                        content=f"⭐ **{star_count}** {channel.mention}",
                        embed=embed
                    )

                    # Save to database
                    db.add_starboard_message(message.id, starboard_msg.id, star_count)

        except Exception as e:
            print(f"Error handling starboard: {e}")

    def calculate_level_from_xp(self, xp: int) -> int:
        return int((xp / 100) ** (2/3))

    async def handle_level_up(self, message, new_level):
        try:
            # Get levelup channel
            levelup_channel_id = db.get_guild_setting(message.guild.id, "levelup_channel", None)
            
            if levelup_channel_id:
                channel = self.bot.get_channel(levelup_channel_id)
            else:
                channel = message.channel

            if channel:
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"Congratulations {message.author.mention}! You reached **Level {new_level}**!",
                    color=0x00ff00
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                
                await channel.send(embed=embed)

        except Exception as e:
            print(f"Error handling level up: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
