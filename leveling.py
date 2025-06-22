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
        # A much harder formula
        return 25 * (level ** 2) + (100 * level) + 150

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
        
        # Grant XP (reduced amount)
        xp_to_add = random.randint(1, 5)
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
                await self.update_user_roles(message.author)

    async def update_user_roles(self, member: discord.Member):
        """Assigns the correct level role based on the member's current level and removes other level roles."""
        user_data = db.get_user_level_data(member.id)
        if not user_data:
            return # No data for this user

        level = user_data.get('level', 0)
        guild = member.guild

        # Find the highest role the user should have
        highest_role_to_keep_id = None
        # Iterate from highest level to lowest
        for role_level, role_id in sorted(LEVEL_ROLES.items(), key=lambda item: item[0], reverse=True):
            if level >= role_level:
                highest_role_to_keep_id = role_id
                break
        
        # Determine which roles to add and remove
        level_role_ids = set(LEVEL_ROLES.values())
        roles_to_remove = []
        
        for role in member.roles:
            if role.id in level_role_ids and role.id != highest_role_to_keep_id:
                roles_to_remove.append(role)

        role_to_add = None
        if highest_role_to_keep_id:
            highest_role = guild.get_role(highest_role_to_keep_id)
            if highest_role and highest_role not in member.roles:
                role_to_add = highest_role

        try:
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove, reason="Level role update")
            if role_to_add:
                await member.add_roles(role_to_add, reason=f"Level role update for Level {level}")
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

    @commands.slash_command(name="updateroles", description="Update your roles based on your current level.", guild_ids=[1370009417726169250])
    @option("user", description="The user whose roles you want to update.", type=discord.Member, required=False)
    async def updateroles(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target_user = user or ctx.author
        
        await ctx.defer(ephemeral=True)
        
        await self.update_user_roles(target_user)
        
        await ctx.followup.send(f"Roles have been updated for **{target_user.display_name}** based on their current level.")

    @commands.slash_command(name="chatlvlup", description="Announce your last level up in chat.", guild_ids=[1370009417726169250])
    async def chatlvlup(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target_user = user or ctx.author
        user_data = db.get_user_level_data(target_user.id)
        if not user_data:
            await ctx.respond(f"**{target_user.display_name}** hasn't chatted yet!", ephemeral=True)
            return
        level = user_data.get('level', 0)
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"Congratulations {target_user.mention}, you've reached **Level {level}**!",
            color=discord.Color.fuchsia()
        )
        await ctx.send(embed=embed)

    @commands.slash_command(name="profile", description="Show your profile: cookies, level, XP, and rank.", guild_ids=[1370009417726169250])
    @option("user", description="The user to show the profile of.", type=discord.Member, required=False)
    async def profile(self, ctx: discord.ApplicationContext, user: discord.Member = None):
        target_user = user or ctx.author
        user_data = db.get_user_level_data(target_user.id)
        cookies = db.get_cookies(target_user.id)
        if not user_data:
            embed = discord.Embed(
                title="🚀 User Profile",
                description=f"**{target_user.display_name}** hasn't chatted yet!",
                color=discord.Color.dark_purple()
            )
            embed.set_thumbnail(url=target_user.display_avatar.url)
            await ctx.respond(embed=embed, ephemeral=True)
            return
        level = user_data.get('level', 0)
        xp = user_data.get('xp', 0)
        xp_needed = self.get_xp_for_level(level)
        rank = db.get_user_leveling_rank(target_user.id)
        embed = discord.Embed(
            title=f"🌌 {target_user.display_name}'s HyperProfile",
            description=f"A glimpse into the future of Discord engagement.",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="🧬 Level", value=f"`{level}`", inline=True)
        embed.add_field(name="🏆 Rank", value=f"`#{rank}`", inline=True)
        embed.add_field(name="💠 XP", value=f"`{xp} / {xp_needed}`", inline=True)
        embed.add_field(name="🍪 Cookies", value=f"`{cookies}`", inline=True)
        progress = int((xp / xp_needed) * 20) if xp_needed else 0
        bar = "🟦" * progress + "⬛" * (20 - progress)
        embed.add_field(name="Progress", value=bar, inline=False)
        embed.set_footer(text="Powered by BLEK NEPHEW | UK Futurism", icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="leveltop", description="Show the top users by level/XP.", guild_ids=[1370009417726169250])
    async def leveltop(self, ctx: discord.ApplicationContext):
        leaderboard = db.get_leveling_leaderboard(limit=10)
        if not leaderboard:
            embed = discord.Embed(
                title="🌌 Level Leaderboard",
                description="No one has leveled up yet!",
                color=discord.Color.dark_teal()
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        description = ""
        for i, entry in enumerate(leaderboard):
            user_id = entry.get('user_id')
            user = ctx.guild.get_member(user_id)
            username = user.display_name if user else f"User ID: {user_id}"
            level = entry.get('level', 0)
            xp = entry.get('xp', 0)
            description += f"**{i+1}.** {username} — 🧬 Level `{level}` | 💠 XP `{xp}`\n"
        embed = discord.Embed(
            title="🌌 Level Leaderboard",
            description=description,
            color=discord.Color.teal()
        )
        embed.set_footer(text="Futuristic UK Leaderboard | BLEK NEPHEW", icon_url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Leveling(bot))
