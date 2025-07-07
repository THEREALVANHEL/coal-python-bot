import discord
from discord.ext import commands, tasks
import random
import os, sys
import asyncio
from datetime import datetime
import io

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db
from assets.media_links import WELCOME_GIF, LEAVE_GIF

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cleanup_expired_items.start()

    async def cog_load(self):
        print("[Events] Loaded successfully.")

    def cog_unload(self):
        self.cleanup_expired_items.cancel()

    @tasks.loop(hours=1)  # Run every hour
    async def cleanup_expired_items(self):
        """Clean up expired temporary roles and purchases"""
        try:
            db.cleanup_expired_items()
            
            # Also remove expired roles from users in Discord
            for guild in self.bot.guilds:
                for member in guild.members:
                    if member.bot:
                        continue
                    
                    active_roles = db.get_active_temporary_roles(member.id)
                    active_role_ids = {role_data["role_id"] for role_data in active_roles}
                    
                    # Get all user's roles that might be temporary
                    user_data = db.get_user_data(member.id)
                    if "temporary_roles" in user_data:
                        for role_data in user_data["temporary_roles"]:
                            role_id = role_data["role_id"]
                            
                            # IMPORTANT: Only remove roles that are explicitly temporary purchases
                            # Never remove XP roles, Cookie roles, or other permanent roles
                            if role_id not in active_role_ids:
                                role = guild.get_role(role_id)
                                if role and role in member.roles:
                                    # Safety check: Don't remove important roles
                                    role_name = role.name.lower()
                                    if any(keyword in role_name for keyword in [
                                        'xp', 'level', 'cookie', 'admin', 'mod', 'staff', 
                                        'vip', 'member', 'verified', 'booster'
                                    ]):
                                        continue  # Skip removing important roles
                                    
                                    try:
                                        await member.remove_roles(role, reason="Temporary role expired")
                                    except:
                                        pass  # Role might have been deleted or no permission
            
            print("✅ Cleaned up expired temporary items")
        except Exception as e:
            print(f"❌ Error in cleanup task: {e}")

    @cleanup_expired_items.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

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
            # Reduced XP range from 15-25 to 5-10
            base_xp_gain = random.randint(5, 10)
            
            # Check for XP boost
            active_purchases = db.get_active_temporary_purchases(message.author.id)
            xp_boost_active = any(purchase["item_type"] == "xp_boost" for purchase in active_purchases)
            
            # Double XP if boost is active
            xp_gain = base_xp_gain * 2 if xp_boost_active else base_xp_gain
            
            # Use live user stats for accurate data
            user_stats = db.get_live_user_stats(message.author.id)
            last_xp_time = user_stats.get('last_xp_time', 0)
            current_time = message.created_at.timestamp()
            
            # 1 minute cooldown
            if current_time - last_xp_time >= 60:
                old_xp = user_stats.get('xp', 0)
                old_cookies = user_stats.get('cookies', 0)
                new_xp = old_xp + xp_gain
                
                # Calculate level
                old_level = self.calculate_level_from_xp(old_xp)
                new_level = self.calculate_level_from_xp(new_xp)
                
                # Update database
                db.add_xp(message.author.id, xp_gain)
                db.update_last_xp_time(message.author.id, current_time)
                
                # Update XP roles
                try:
                    from cogs.leveling import Leveling
                    leveling_cog = self.bot.get_cog('Leveling')
                    if leveling_cog and hasattr(message.author, 'guild'):
                        await leveling_cog.update_xp_roles(message.author, new_level)
                        
                        # Update cookie roles using the cookies cog
                        cookies_cog = self.bot.get_cog('Cookies')
                        if cookies_cog:
                            await cookies_cog.update_cookie_roles(message.author, old_cookies)
                except Exception as e:
                    print(f"Error updating roles: {e}")
                
                # Check for level up
                if new_level > old_level:
                    await self.handle_level_up(message, new_level, old_level)

        except Exception as e:
            print(f"Error processing XP for message: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            # Initialize user data when they join
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
                    embed.add_field(name="🎮 Get Started", value="Start chatting to earn XP and level up!\nUse `/help` to see all commands.", inline=False)
                    embed.set_image(url=WELCOME_GIF)
                    await channel.send(embed=embed)

            # Sync roles on join (in case they're returning)
            try:
                user_stats = db.get_live_user_stats(member.id)
                level = user_stats.get('level', 0)
                cookies = user_stats.get('cookies', 0)
                
                leveling_cog = self.bot.get_cog('Leveling')
                if leveling_cog:
                    await leveling_cog.update_xp_roles(member, level)
                    
                    # Update cookie roles using the cookies cog
                    cookies_cog = self.bot.get_cog('Cookies')
                    if cookies_cog:
                        await cookies_cog.update_cookie_roles(member, cookies)
            except Exception as e:
                print(f"Error syncing roles for new member {member}: {e}")

            # Log to mod log
            await self.log_to_modlog(member.guild, "member_join", {
                "user": member,
                "description": f"{member.mention} joined the server\n**Account Created:** <t:{int(member.created_at.timestamp())}:R>",
                "color": 0x00ff00
            })

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

            # Log to mod log
            await self.log_to_modlog(member.guild, "member_leave", {
                "user": member,
                "description": f"**{member.display_name}** left the server",
                "color": 0xff6b6b
            })

        except Exception as e:
            print(f"Error in on_member_remove: {e}")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log member updates (role changes, nickname changes, etc.)"""
        try:
            if before.roles != after.roles:
                # Role changes
                added_roles = [role for role in after.roles if role not in before.roles]
                removed_roles = [role for role in before.roles if role not in after.roles]
                
                if added_roles or removed_roles:
                    description = []
                    if added_roles:
                        description.append(f"**Added:** {', '.join([role.mention for role in added_roles])}")
                    if removed_roles:
                        description.append(f"**Removed:** {', '.join([role.mention for role in removed_roles])}")
                    
                    await self.log_to_modlog(after.guild, "role_update", {
                        "user": after,
                        "description": f"{after.mention} role changes:\n" + "\n".join(description),
                        "color": 0x7289da
                    })

            if before.nick != after.nick:
                # Nickname change
                await self.log_to_modlog(after.guild, "nickname_update", {
                    "user": after,
                    "description": f"{after.mention} nickname changed\n**Before:** {before.nick or 'None'}\n**After:** {after.nick or 'None'}",
                    "color": 0xffa500
                })

        except Exception as e:
            print(f"Error in on_member_update: {e}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log message deletions"""
        if message.author.bot:
            return
            
        try:
            await self.log_to_modlog(message.guild, "message_delete", {
                "user": message.author,
                "description": f"Message deleted in {message.channel.mention}\n**Content:** {message.content[:1000] if message.content else 'No text content'}",
                "color": 0xff0000
            })
        except Exception as e:
            print(f"Error in on_message_delete: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Log message edits"""
        if before.author.bot or before.content == after.content:
            return
            
        try:
            await self.log_to_modlog(after.guild, "message_edit", {
                "user": after.author,
                "description": f"Message edited in {after.channel.mention}\n**Before:** {before.content[:500] if before.content else 'No content'}\n**After:** {after.content[:500] if after.content else 'No content'}",
                "color": 0xffa500
            })
        except Exception as e:
            print(f"Error in on_message_edit: {e}")

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """Log user updates (username, avatar changes)"""
        try:
            # Find mutual guilds to log in
            for guild in self.bot.guilds:
                if guild.get_member(after.id):
                    if before.name != after.name:
                        await self.log_to_modlog(guild, "username_update", {
                            "user": after,
                            "description": f"{after.mention} username changed\n**Before:** {before.name}\n**After:** {after.name}",
                            "color": 0x7289da
                        })
                    
                    if before.avatar != after.avatar:
                        await self.log_to_modlog(guild, "avatar_update", {
                            "user": after,
                            "description": f"{after.mention} changed their avatar",
                            "color": 0x7289da
                        })
                    break
        except Exception as e:
            print(f"Error in on_user_update: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creation"""
        try:
            await self.log_to_modlog(channel.guild, "channel_create", {
                "description": f"Channel created: {channel.mention} ({channel.type})",
                "color": 0x00ff00
            })
        except Exception as e:
            print(f"Error in on_guild_channel_create: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletion"""
        try:
            await self.log_to_modlog(channel.guild, "channel_delete", {
                "description": f"Channel deleted: **{channel.name}** ({channel.type})",
                "color": 0xff0000
            })
        except Exception as e:
            print(f"Error in on_guild_channel_delete: {e}")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Log role creation"""
        try:
            await self.log_to_modlog(role.guild, "role_create", {
                "description": f"Role created: {role.mention}",
                "color": 0x00ff00
            })
        except Exception as e:
            print(f"Error in on_guild_role_create: {e}")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Log role deletion"""
        try:
            await self.log_to_modlog(role.guild, "role_delete", {
                "description": f"Role deleted: **{role.name}**",
                "color": 0xff0000
            })
        except Exception as e:
            print(f"Error in on_guild_role_delete: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            # Handle starboard
            if str(payload.emoji) == "⭐":
                await self.handle_starboard(payload)

        except Exception as e:
            print(f"Error in on_raw_reaction_add: {e}")

    async def log_to_modlog(self, guild, event_type, data):
        """Log events to mod log channel"""
        try:
            modlog_channel_id = db.get_guild_setting(guild.id, "modlog_channel", None)
            if not modlog_channel_id:
                return
                
            channel = guild.get_channel(modlog_channel_id)
            if not channel:
                return

            embed = discord.Embed(
                title=f"📋 {event_type.replace('_', ' ').title()}",
                description=data.get("description", "No description"),
                color=data.get("color", 0x7289da),
                timestamp=datetime.now()
            )
            
            if "user" in data:
                embed.set_author(name=data["user"].display_name, icon_url=data["user"].display_avatar.url)
                embed.add_field(name="User ID", value=data["user"].id, inline=True)
            
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging to modlog: {e}")

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

            # Don't star bot messages or messages in starboard channel
            if message.author.bot or message.channel.id == starboard_channel.id:
                return

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
                    # Forward the complete message with all content
                    await self.forward_complete_message_to_starboard(
                        message, starboard_channel, star_count
                    )

        except Exception as e:
            print(f"Error handling starboard: {e}")

    async def forward_complete_message_to_starboard(self, original_message, starboard_channel, star_count):
        """Simplified starboard forwarding - just forward the message and attachments"""
        try:
            # Main starboard embed - just the message content
            main_embed = discord.Embed(
                color=0xffd700,
                timestamp=original_message.created_at
            )
            
            main_embed.set_author(
                name=f"{original_message.author.display_name}",
                icon_url=original_message.author.display_avatar.url
            )
            
            # Clean message content
            if original_message.content:
                # Limit content to prevent overly long embeds
                content = original_message.content[:2000]
                if len(original_message.content) > 2000:
                    content += "... (message truncated)"
                main_embed.description = content
            else:
                main_embed.description = "*This message contains media or embeds*"
            
            main_embed.set_footer(text=f"✨ Starred Message")
            
            # Send main embed first
            starboard_msg = await starboard_channel.send(embed=main_embed)

            # Forward all attachments with perfect preservation
            if original_message.attachments:
                files_to_send = []
                
                for attachment in original_message.attachments:
                    try:
                        # Download and re-upload to preserve permanently
                        file_data = await attachment.read()
                        discord_file = discord.File(
                            io.BytesIO(file_data), 
                            filename=attachment.filename
                        )
                        files_to_send.append(discord_file)
                        
                        # Send files in batches of 10 (Discord limit)
                        if len(files_to_send) >= 10:
                            await starboard_channel.send(files=files_to_send)
                            files_to_send = []
                    except Exception as e:
                        print(f"Error processing attachment {attachment.filename}: {e}")
                
                # Send remaining files
                if files_to_send:
                    await starboard_channel.send(files=files_to_send)

            # Forward original embeds (like from bots or rich content)
            if original_message.embeds:
                embed_count = 0
                for embed in original_message.embeds:
                    if embed_count >= 3:  # Limit to prevent spam
                        break
                    
                    try:
                        # Recreate embed to avoid reference issues
                        new_embed = discord.Embed.from_dict(embed.to_dict())
                        await starboard_channel.send(embed=new_embed)
                        embed_count += 1
                    except Exception as e:
                        print(f"Error forwarding embed: {e}")

            # Handle stickers
            if original_message.stickers:
                sticker_names = [f"🎮 **{sticker.name}**" for sticker in original_message.stickers]
                sticker_embed = discord.Embed(
                    title="🎭 **Stickers Used**",
                    description=" • ".join(sticker_names),
                    color=0x5865f2
                )
                await starboard_channel.send(embed=sticker_embed)

            # Add separator for visual spacing between different starred messages
            separator_embed = discord.Embed(description="⭐ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ⭐", color=0x2f3136)
            await starboard_channel.send(embed=separator_embed)

            # Save to database
            db.add_starboard_message(original_message.id, starboard_msg.id, star_count)

        except Exception as e:
            print(f"Error in simplified starboard forwarding: {e}")
            # Fallback to simplified version
            await self.fallback_starboard_embed(original_message, starboard_channel, star_count)

    async def fallback_starboard_embed(self, original_message, starboard_channel, star_count):
        """Clean fallback method for starboard if complete forwarding fails"""
        try:
            embed = discord.Embed(
                description=original_message.content[:2000] if original_message.content else "*Media or embed content*",
                color=0xffd700,
                timestamp=original_message.created_at
            )
            embed.set_author(
                name=original_message.author.display_name,
                icon_url=original_message.author.display_avatar.url
            )

            # Add first attachment preview if available
            if original_message.attachments:
                first_attachment = original_message.attachments[0]
                if any(first_attachment.filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    embed.set_image(url=first_attachment.url)

            embed.set_footer(text=f"✨ Starred Message")

            starboard_msg = await starboard_channel.send(embed=embed)

            # Add separator for visual spacing
            separator_embed = discord.Embed(description="⭐ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ⭐", color=0x2f3136)
            await starboard_channel.send(embed=separator_embed)

            # Save to database
            db.add_starboard_message(original_message.id, starboard_msg.id, star_count)

        except Exception as e:
            print(f"Error in fallback starboard embed: {e}")

    def calculate_level_from_xp(self, xp: int) -> int:
        """Calculate level from XP using binary search for efficiency"""
        level = 0
        while self.calculate_xp_for_level(level + 1) <= xp:
            level += 1
        return level

    def calculate_xp_for_level(self, level: int) -> int:
        """Increased XP requirement per level - much harder progression"""
        if level <= 10:
            return int(200 * (level ** 2))
        elif level <= 50:
            return int(300 * (level ** 2.2))
        elif level <= 100:
            return int(500 * (level ** 2.5))
        else:
            return int(1000 * (level ** 2.8))

    async def handle_level_up(self, message, new_level, old_level):
        try:
            # Get levelup channel
            levelup_channel_id = db.get_guild_setting(message.guild.id, "levelup_channel", None)
            
            if levelup_channel_id:
                channel = self.bot.get_channel(levelup_channel_id)
            else:
                channel = message.channel

            if channel:
                # Get job title
                from cogs.leveling import JOB_TITLES
                job = None
                for job_data in JOB_TITLES:
                    if job_data["min_level"] <= new_level <= job_data["max_level"]:
                        job = job_data
                        break
                if not job:
                    job = JOB_TITLES[-1]

                # Check for promotion
                promotion_happened = False
                for job_data in JOB_TITLES:
                    if job_data["min_level"] == new_level and new_level > 0:
                        # User got promoted, give bonus coins
                        db.add_coins(message.author.id, job_data["promotion_bonus"])
                        promotion_happened = True
                        break

                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"Congratulations {message.author.mention}! You reached **Level {new_level}**!",
                    color=0x00ff00
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                
                if promotion_happened:
                    embed.add_field(
                        name="🎊 Promotion!",
                        value=f"You've been promoted to **{job['name']}**!\nBonus: +{job['promotion_bonus']} coins",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="💼 Current Position",
                        value=job['name'],
                        inline=True
                    )
                
                await channel.send(embed=embed)

        except Exception as e:
            print(f"Error handling level up: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
