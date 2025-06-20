import discord
from discord.ext import commands
from discord import option
import sys
import os
import random
import asyncio

# Add parent directory to path to import database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

# --- Configuration ---
LEVEL_ROLES = {
    5: 1371032270361853962,
    10: 1371032537740214302,
    20: 1371032664026382427,
    35: 1371032830217289748,
    50: 1371032964938600521,
    75: 1371033073038266429,
}

# Cooldown for XP gain (in seconds)
XP_COOLDOWN = 60

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns = {} # user_id: timestamp

    def get_xp_for_level(self, level):
        """Calculate the XP needed to reach a certain level."""
        # Using a common formula: 5 * (lvl^2) + 50 * lvl + 100
        return 5 * (level ** 2) + (50 * level) + 100

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        current_time = asyncio.get_event_loop().time()

        # Check for cooldown
        if user_id in self.xp_cooldowns:
            if current_time - self.xp_cooldowns[user_id] < XP_COOLDOWN:
                return # User is on cooldown
        
        # Update cooldown timestamp
        self.xp_cooldowns[user_id] = current_time
        
        # Grant XP
        xp_to_add = random.randint(5, 15)
        db.update_user_xp(user_id, xp_to_add)

        # Check for level up
        user_data = db.get_user_level_data(user_id)
        user_level = user_data.get('level', 0)
        user_xp = user_data.get('xp', 0)

        xp_needed = self.get_xp_for_level(user_level)

        if user_xp >= xp_needed:
            # LEVEL UP!
            new_level = user_level + 1
            db.set_user_level(user_id, new_level)
            
            # Announce it
            level_channel_id = db.get_channel(message.guild.id, "leveling")
            if level_channel_id:
                level_channel = message.guild.get_channel(level_channel_id)
                if level_channel:
                    embed = discord.Embed(
                        title="🎉 Level Up!",
                        description=f"Congratulations {message.author.mention}, you've reached **Level {new_level}**!",
                        color=discord.Color.fuchsia()
                    )
                    await level_channel.send(embed=embed)
            
            # Handle role rewards
            if new_level in LEVEL_ROLES:
                await self.update_user_roles(message.author, new_level)

    async def update_user_roles(self, member: discord.Member, new_level: int):
        """Assigns the new role and removes any previous level roles."""
        guild = member.guild
        
        # Get the new role to add
        role_to_add_id = LEVEL_ROLES.get(new_level)
        if not role_to_add_id: return
        role_to_add = guild.get_role(role_to_add_id)
        if not role_to_add: 
            print(f"Error: Role ID {role_to_add_id} not found.")
            return

        # Get a list of all level roles to remove
        roles_to_remove_ids = [role_id for level, role_id in LEVEL_ROLES.items() if level < new_level]
        roles_to_remove = [guild.get_role(rid) for rid in roles_to_remove_ids if guild.get_role(rid)]

        try:
            # Remove old roles first
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Level up")
            # Add new role
            await member.add_roles(role_to_add, reason=f"Reached Level {new_level}")
        except discord.Forbidden:
            print(f"Error: Bot does not have permissions to manage roles for {member.display_name}.")
        except Exception as e:
            print(f"An error occurred while updating roles for {member.display_name}: {e}")

    # --- Commands ---
    
    @commands.slash_command(name="rank", description="Check your or another user's level and XP.", guild_ids=[1370009417726169250])
    @option("user", description="The user to check the rank of.", type=discord.Member, required=False)
    async def rank(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target_user = user or ctx.author
        
        user_data = db.get_user_level_data(target_user.id)
        if not user_data:
            await ctx.respond(f"**{target_user.display_name}** hasn't chatted yet!", ephemeral=True)
            return

        level = user_data.get('level', 0)
        xp = user_data.get('xp', 0)
        xp_needed = self.get_xp_for_level(level)
        rank = db.get_user_leveling_rank(target_user.id)

        embed = discord.Embed(title=f"Rank for {target_user.display_name}", color=target_user.color)
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="Rank", value=f"**#{rank}**", inline=True)
        embed.add_field(name="XP", value=f"`{xp} / {xp_needed}`", inline=False)
        
        # Progress bar
        progress = int((xp / xp_needed) * 20)
        bar = "🟩" * progress + "⬛" * (20 - progress)
        embed.add_field(name="Progress", value=bar, inline=False)

        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Leveling(bot))
