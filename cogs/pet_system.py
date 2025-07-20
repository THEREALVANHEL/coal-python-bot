import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import random
import asyncio
import json
from datetime import datetime, timedelta
import database as db

class PetSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pet_types = {
            "dragon": {"name": "Dragon", "rarity": "legendary", "base_hp": 100, "base_attack": 25, "base_defense": 20, "cost": 10000},
            "phoenix": {"name": "Phoenix", "rarity": "legendary", "base_hp": 90, "base_attack": 30, "base_defense": 15, "cost": 8000},
            "unicorn": {"name": "Unicorn", "rarity": "epic", "base_hp": 80, "base_attack": 20, "base_defense": 25, "cost": 5000},
            "griffin": {"name": "Griffin", "rarity": "epic", "base_hp": 85, "base_attack": 22, "base_defense": 18, "cost": 4000},
            "wolf": {"name": "Wolf", "rarity": "rare", "base_hp": 70, "base_attack": 18, "base_defense": 15, "cost": 2000},
            "cat": {"name": "Cat", "rarity": "common", "base_hp": 50, "base_attack": 12, "base_defense": 10, "cost": 500},
            "dog": {"name": "Dog", "rarity": "common", "base_hp": 60, "base_attack": 15, "base_defense": 12, "cost": 800},
            "rabbit": {"name": "Rabbit", "rarity": "common", "base_hp": 40, "base_attack": 8, "base_defense": 8, "cost": 300}
        }
        
        self.pet_items = {
            "premium_food": {"name": "Premium Food", "cost": 100, "hunger": 50, "happiness": 20, "health": 30},
            "basic_food": {"name": "Basic Food", "cost": 25, "hunger": 20, "happiness": 5, "health": 10},
            "treat": {"name": "Pet Treat", "cost": 50, "hunger": 10, "happiness": 30, "health": 5},
            "medicine": {"name": "Medicine", "cost": 150, "hunger": 0, "happiness": 0, "health": 80},
            "toy": {"name": "Pet Toy", "cost": 75, "hunger": 0, "happiness": 40, "health": 0},
            "vitamin": {"name": "Vitamin", "cost": 200, "hunger": 0, "happiness": 10, "health": 50},
            "super_food": {"name": "Super Food", "cost": 300, "hunger": 100, "happiness": 50, "health": 100}
        }

    def get_pet_data(self, user_id: int) -> dict:
        """Get pet data from database"""
        user_data = db.get_user_data(user_id)
        return user_data.get('pet', {})

    def save_pet_data(self, user_id: int, pet_data: dict):
        """Save pet data to database"""
        user_data = db.get_user_data(user_id)
        user_data['pet'] = pet_data
        db.update_user_data(user_id, user_data)

    def create_pet(self, pet_type: str, user_id: int) -> dict:
        """Create a new pet"""
        if pet_type not in self.pet_types:
            return None
            
        pet_info = self.pet_types[pet_type]
        pet = {
            "type": pet_type,
            "name": f"{pet_info['name']}",
            "nickname": f"My {pet_info['name']}",
            "level": 1,
            "exp": 0,
            "exp_needed": 100,
            "hp": pet_info['base_hp'],
            "max_hp": pet_info['base_hp'],
            "attack": pet_info['base_attack'],
            "defense": pet_info['base_defense'],
            "hunger": 100,
            "happiness": 100,
            "health": 100,
            "last_fed": datetime.now().isoformat(),
            "last_played": datetime.now().isoformat(),
            "created": datetime.now().isoformat(),
            "rarity": pet_info['rarity'],
            "equipment": {},
            "skills": []
        }
        return pet

    @app_commands.command(name="pet", description="🐾 Manage your pet!")
    async def pet(self, interaction: discord.Interaction):
        pet_data = self.get_pet_data(interaction.user.id)
        
        if not pet_data:
            embed = discord.Embed(
                title="🐾 No Pet Found",
                description="You don't have a pet yet! Use `/adopt` to get one.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🐾 {pet_data['nickname']}",
            description=f"A level {pet_data['level']} {pet_data['name']}",
            color=0x4ecdc4
        )
        
        # Status bars
        hunger_bar = self.create_status_bar(pet_data['hunger'])
        happiness_bar = self.create_status_bar(pet_data['happiness'])
        health_bar = self.create_status_bar(pet_data['health'])
        exp_bar = self.create_status_bar((pet_data['exp'] / pet_data['exp_needed']) * 100)
        
        embed.add_field(
            name="📊 Stats",
            value=f"**HP:** {pet_data['hp']}/{pet_data['max_hp']}\n"
                  f"**Attack:** {pet_data['attack']}\n"
                  f"**Defense:** {pet_data['defense']}\n"
                  f"**Rarity:** {pet_data['rarity'].title()}",
            inline=True
        )
        
        embed.add_field(
            name="💚 Status",
            value=f"**Hunger:** {hunger_bar} {pet_data['hunger']}%\n"
                  f"**Happiness:** {happiness_bar} {pet_data['happiness']}%\n"
                  f"**Health:** {health_bar} {pet_data['health']}%\n"
                  f"**Experience:** {exp_bar} {pet_data['exp']}/{pet_data['exp_needed']}",
            inline=True
        )
        
        embed.set_footer(text=f"Created: {pet_data['created'][:10]}")
        
        # Create action buttons
        view = PetActionView(self, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    def create_status_bar(self, percentage: int) -> str:
        """Create a visual status bar"""
        filled = int(percentage / 10)
        empty = 10 - filled
        return "█" * filled + "░" * empty

    @app_commands.command(name="adopt", description="🏠 Adopt a new pet!")
    async def adopt(self, interaction: discord.Interaction, pet_type: str = None):
        pet_data = self.get_pet_data(interaction.user.id)
        
        if pet_data:
            embed = discord.Embed(
                title="🐾 Already Have a Pet",
                description="You already have a pet! Use `/pet` to manage it.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not pet_type:
            # Show available pets
            embed = discord.Embed(
                title="🏠 Available Pets",
                description="Choose a pet to adopt:",
                color=0x4ecdc4
            )
            
            for pet_id, pet_info in self.pet_types.items():
                rarity_emoji = {"common": "⚪", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}
                embed.add_field(
                    name=f"{rarity_emoji[pet_info['rarity']]} {pet_info['name']}",
                    value=f"**Cost:** {pet_info['cost']} coins\n"
                          f"**Rarity:** {pet_info['rarity'].title()}\n"
                          f"**Stats:** HP: {pet_info['base_hp']} | ATK: {pet_info['base_attack']} | DEF: {pet_info['base_defense']}",
                    inline=True
                )
            
            embed.set_footer(text="Use /adopt <pet_type> to adopt a specific pet")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if pet_type not in self.pet_types:
            embed = discord.Embed(
                title="❌ Invalid Pet Type",
                description=f"Available pets: {', '.join(self.pet_types.keys())}",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        pet_info = self.pet_types[pet_type]
        user_data = db.get_user_data(interaction.user.id)
        balance = user_data.get('coins', 0)
        
        if balance < pet_info['cost']:
            embed = discord.Embed(
                title="❌ Insufficient Coins",
                description=f"You need {pet_info['cost']} coins to adopt a {pet_info['name']}. You have {balance} coins.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create pet and deduct coins
        pet = self.create_pet(pet_type, interaction.user.id)
        self.save_pet_data(interaction.user.id, pet)
        db.remove_coins(interaction.user.id, pet_info['cost'])
        
        embed = discord.Embed(
            title="🎉 Pet Adopted!",
            description=f"You successfully adopted a {pet_info['name']}!",
            color=0x4ecdc4
        )
        embed.add_field(
            name="🐾 Your New Pet",
            value=f"**Name:** {pet['nickname']}\n"
                  f"**Level:** {pet['level']}\n"
                  f"**Rarity:** {pet['rarity'].title()}\n"
                  f"**Cost:** {pet_info['cost']} coins",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="feed", description="🍖 Feed your pet!")
    async def feed(self, interaction: discord.Interaction, item: str = "basic_food"):
        pet_data = self.get_pet_data(interaction.user.id)
        
        if not pet_data:
            embed = discord.Embed(
                title="❌ No Pet Found",
                description="You don't have a pet to feed!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if item not in self.pet_items:
            embed = discord.Embed(
                title="❌ Invalid Item",
                description=f"Available items: {', '.join(self.pet_items.keys())}",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user has the item
        user_data = db.get_user_data(interaction.user.id)
        inventory = user_data.get('inventory', {})
        
        if item not in inventory or inventory[item] <= 0:
            embed = discord.Embed(
                title="❌ Item Not Found",
                description=f"You don't have any {self.pet_items[item]['name']}!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Use item and update pet stats
        item_info = self.pet_items[item]
        pet_data['hunger'] = min(100, pet_data['hunger'] + item_info['hunger'])
        pet_data['happiness'] = min(100, pet_data['happiness'] + item_info['happiness'])
        pet_data['health'] = min(100, pet_data['health'] + item_info['health'])
        pet_data['last_fed'] = datetime.now().isoformat()
        
        # Remove item from inventory
        inventory[item] -= 1
        if inventory[item] <= 0:
            del inventory[item]
        user_data['inventory'] = inventory
        db.update_user_data(interaction.user.id, user_data)
        
        # Save pet data
        self.save_pet_data(interaction.user.id, pet_data)
        
        embed = discord.Embed(
            title="🍖 Pet Fed!",
            description=f"You fed {pet_data['nickname']} with {item_info['name']}!",
            color=0x4ecdc4
        )
        embed.add_field(
            name="📊 Updated Stats",
            value=f"**Hunger:** {pet_data['hunger']}%\n"
                  f"**Happiness:** {pet_data['happiness']}%\n"
                  f"**Health:** {pet_data['health']}%",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play", description="🎾 Play with your pet!")
    async def play(self, interaction: discord.Interaction):
        pet_data = self.get_pet_data(interaction.user.id)
        
        if not pet_data:
            embed = discord.Embed(
                title="❌ No Pet Found",
                description="You don't have a pet to play with!",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check cooldown (can play every 30 minutes)
        last_played = datetime.fromisoformat(pet_data['last_played'])
        if datetime.now() - last_played < timedelta(minutes=30):
            time_left = 30 - int((datetime.now() - last_played).total_seconds() / 60)
            embed = discord.Embed(
                title="⏰ Cooldown Active",
                description=f"Your pet is tired! Try again in {time_left} minutes.",
                color=0xff6b6b
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Play with pet
        happiness_gain = random.randint(10, 25)
        exp_gain = random.randint(5, 15)
        
        pet_data['happiness'] = min(100, pet_data['happiness'] + happiness_gain)
        pet_data['exp'] += exp_gain
        pet_data['last_played'] = datetime.now().isoformat()
        
        # Check for level up
        level_up = False
        while pet_data['exp'] >= pet_data['exp_needed']:
            pet_data['exp'] -= pet_data['exp_needed']
            pet_data['level'] += 1
            pet_data['exp_needed'] = int(pet_data['exp_needed'] * 1.5)
            pet_data['max_hp'] += 5
            pet_data['hp'] = pet_data['max_hp']
            pet_data['attack'] += 2
            pet_data['defense'] += 1
            level_up = True

        self.save_pet_data(interaction.user.id, pet_data)
        
        embed = discord.Embed(
            title="🎾 Play Time!",
            description=f"You played with {pet_data['nickname']}!",
            color=0x4ecdc4
        )
        embed.add_field(
            name="📊 Results",
            value=f"**Happiness:** +{happiness_gain} ({pet_data['happiness']}%)\n"
                  f"**Experience:** +{exp_gain} ({pet_data['exp']}/{pet_data['exp_needed']})",
            inline=False
        )
        
        if level_up:
            embed.add_field(
                name="🎉 Level Up!",
                value=f"{pet_data['nickname']} reached level {pet_data['level']}!\n"
                      f"**New Stats:** HP: {pet_data['max_hp']} | ATK: {pet_data['attack']} | DEF: {pet_data['defense']}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

class PetActionView(View):
    def __init__(self, pet_system: PetSystem, user_id: int):
        super().__init__(timeout=60)
        self.pet_system = pet_system
        self.user_id = user_id

    @discord.ui.button(label="Feed", emoji="🍖", style=discord.ButtonStyle.primary)
    async def feed_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your pet!", ephemeral=True)
            return
        
        # Show feeding options
        embed = discord.Embed(
            title="🍖 Feed Your Pet",
            description="Choose what to feed your pet:",
            color=0x4ecdc4
        )
        
        for item_id, item_info in self.pet_system.pet_items.items():
            embed.add_field(
                name=f"🍽️ {item_info['name']}",
                value=f"**Cost:** {item_info['cost']} coins\n"
                      f"**Effects:** Hunger: +{item_info['hunger']} | Happiness: +{item_info['happiness']} | Health: +{item_info['health']}",
                inline=True
            )
        
        embed.set_footer(text="Use /feed <item> to feed your pet")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Play", emoji="🎾", style=discord.ButtonStyle.success)
    async def play_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your pet!", ephemeral=True)
            return
        
        await self.pet_system.play(interaction)

    @discord.ui.button(label="Rename", emoji="✏️", style=discord.ButtonStyle.secondary)
    async def rename_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your pet!", ephemeral=True)
            return
        
        await interaction.response.send_modal(PetRenameModal(self.pet_system, self.user_id))

class PetRenameModal(Modal, title="Rename Your Pet"):
    def __init__(self, pet_system: PetSystem, user_id: int):
        super().__init__()
        self.pet_system = pet_system
        self.user_id = user_id

    new_name = TextInput(
        label="New Pet Name",
        placeholder="Enter a new name for your pet...",
        max_length=20,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        pet_data = self.pet_system.get_pet_data(self.user_id)
        if not pet_data:
            await interaction.response.send_message("You don't have a pet!", ephemeral=True)
            return

        old_name = pet_data['nickname']
        pet_data['nickname'] = self.new_name.value
        self.pet_system.save_pet_data(self.user_id, pet_data)
        
        embed = discord.Embed(
            title="✏️ Pet Renamed!",
            description=f"Your pet was renamed from **{old_name}** to **{self.new_name.value}**!",
            color=0x4ecdc4
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(PetSystem(bot))