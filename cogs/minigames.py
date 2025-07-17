import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput
import random
import asyncio
import time
from datetime import datetime, timedelta
import os, sys

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class MiniGames(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Anti-spam protection
        self.game_cooldowns = {}
        self.trivia_questions = self.load_trivia_questions()
        
    def load_trivia_questions(self):
        """Load trivia questions - mix of programming, general knowledge, and fun facts"""
        return [
            {"question": "What does 'API' stand for?", "options": ["Application Programming Interface", "Automated Program Integration", "Advanced Programming Instructions", "Application Process Interface"], "correct": 0, "difficulty": "easy", "reward": 15},
            {"question": "Which programming language is known as the 'mother of all languages'?", "options": ["C", "Assembly", "FORTRAN", "COBOL"], "correct": 0, "difficulty": "medium", "reward": 25},
            {"question": "What is the largest planet in our solar system?", "options": ["Saturn", "Jupiter", "Neptune", "Earth"], "correct": 1, "difficulty": "easy", "reward": 10},
            {"question": "In what year was Discord founded?", "options": ["2013", "2014", "2015", "2016"], "correct": 2, "difficulty": "medium", "reward": 20},
            {"question": "What does 'HTTP' stand for?", "options": ["HyperText Transfer Protocol", "High Technology Transfer Process", "HyperText Translation Protocol", "High Tech Transfer Protocol"], "correct": 0, "difficulty": "easy", "reward": 15},
            {"question": "Which data structure follows LIFO principle?", "options": ["Queue", "Stack", "Array", "Linked List"], "correct": 1, "difficulty": "medium", "reward": 30},
            {"question": "What is the speed of light in vacuum?", "options": ["299,792,458 m/s", "300,000,000 m/s", "299,000,000 m/s", "301,000,000 m/s"], "correct": 0, "difficulty": "hard", "reward": 50},
            {"question": "Which company created Python?", "options": ["Google", "Microsoft", "Guido van Rossum", "Facebook"], "correct": 2, "difficulty": "medium", "reward": 25},
            {"question": "What does 'RAM' stand for?", "options": ["Random Access Memory", "Rapid Access Memory", "Real Access Memory", "Remote Access Memory"], "correct": 0, "difficulty": "easy", "reward": 15},
            {"question": "Which planet is known as the Red Planet?", "options": ["Venus", "Mars", "Jupiter", "Saturn"], "correct": 1, "difficulty": "easy", "reward": 10},
        ]

    def check_cooldown(self, user_id: int, game_type: str, cooldown_seconds: int = 30) -> bool:
        """Check if user is on cooldown for specific game"""
        current_time = time.time()
        cooldown_key = f"{user_id}_{game_type}"
        
        if cooldown_key in self.game_cooldowns:
            time_left = self.game_cooldowns[cooldown_key] - current_time
            if time_left > 0:
                return False, time_left
                
        self.game_cooldowns[cooldown_key] = current_time + cooldown_seconds
        return True, 0

    @app_commands.command(name="trivia", description="🧠 Test your knowledge and earn coins!")
    async def trivia(self, interaction: discord.Interaction):
        # Check cooldown
        can_play, time_left = self.check_cooldown(interaction.user.id, "trivia", 60)
        if not can_play:
            await interaction.response.send_message(
                f"🕐 You can play trivia again in {int(time_left)} seconds!", 
                ephemeral=True
            )
            return

        question = random.choice(self.trivia_questions)
        
        class TriviaView(View):
            def __init__(self, question_data, user_id):
                super().__init__(timeout=30)
                self.question_data = question_data
                self.user_id = user_id
                self.answered = False
                
                # Add answer buttons
                for i, option in enumerate(question_data["options"]):
                    button = Button(
                        label=f"{chr(65+i)}) {option}", 
                        style=discord.ButtonStyle.secondary,
                        custom_id=str(i)
                    )
                    button.callback = self.answer_callback
                    self.add_item(button)
            
            async def answer_callback(self, button_interaction: discord.Interaction):
                if button_interaction.user.id != self.user_id:
                    await button_interaction.response.send_message("This isn't your trivia question!", ephemeral=True)
                    return
                    
                if self.answered:
                    await button_interaction.response.send_message("You already answered!", ephemeral=True)
                    return
                
                self.answered = True
                selected = int(button_interaction.custom_id)
                correct = selected == self.question_data["correct"]
                
                # Clear all buttons
                for item in self.children:
                    item.disabled = True
                
                if correct:
                    # Give coins based on difficulty
                    reward = self.question_data["reward"]
                    db.add_coins(self.user_id, reward)
                    
                    embed = discord.Embed(
                        title="🎉 Correct!",
                        description=f"Great job! You earned **{reward} coins**!",
                        color=0x00ff00
                    )
                    embed.add_field(
                        name="💡 Answer", 
                        value=self.question_data["options"][self.question_data["correct"]], 
                        inline=False
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Wrong Answer",
                        description="Better luck next time!",
                        color=0xff0000
                    )
                    embed.add_field(
                        name="💡 Correct Answer", 
                        value=self.question_data["options"][self.question_data["correct"]], 
                        inline=False
                    )
                
                await button_interaction.response.edit_message(embed=embed, view=self)
        
        embed = discord.Embed(
            title="🧠 Trivia Challenge",
            description=f"**Difficulty:** {question['difficulty'].title()}\n**Reward:** {question['reward']} coins\n\n**{question['question']}**",
            color=0x3498db
        )
        embed.set_footer(text="You have 30 seconds to answer!")
        
        view = TriviaView(question, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="rps", description="🪨 Rock Paper Scissors tournament - compete against others!")
    async def rock_paper_scissors(self, interaction: discord.Interaction, bet: int = 10):
        if bet < 5:
            await interaction.response.send_message("Minimum bet is 5 coins!", ephemeral=True)
            return
        if bet > 100:
            await interaction.response.send_message("Maximum bet is 100 coins!", ephemeral=True)
            return
            
        # Check if user has enough coins
        user_data = db.get_user_data(interaction.user.id)
        if user_data.get('coins', 0) < bet:
            await interaction.response.send_message("You don't have enough coins!", ephemeral=True)
            return

        can_play, time_left = self.check_cooldown(interaction.user.id, "rps", 20)
        if not can_play:
            await interaction.response.send_message(
                f"🕐 You can play RPS again in {int(time_left)} seconds!", 
                ephemeral=True
            )
            return

        class RPSView(View):
            def __init__(self, user_id, bet_amount):
                super().__init__(timeout=30)
                self.user_id = user_id
                self.bet_amount = bet_amount
                self.played = False
                
            @discord.ui.button(emoji="🪨", label="Rock", style=discord.ButtonStyle.secondary)
            async def rock(self, button_interaction: discord.Interaction, button: Button):
                await self.play_game(button_interaction, "rock")
                
            @discord.ui.button(emoji="📄", label="Paper", style=discord.ButtonStyle.secondary)
            async def paper(self, button_interaction: discord.Interaction, button: Button):
                await self.play_game(button_interaction, "paper")
                
            @discord.ui.button(emoji="✂️", label="Scissors", style=discord.ButtonStyle.secondary)
            async def scissors(self, button_interaction: discord.Interaction, button: Button):
                await self.play_game(button_interaction, "scissors")
            
            async def play_game(self, button_interaction: discord.Interaction, choice: str):
                if button_interaction.user.id != self.user_id:
                    await button_interaction.response.send_message("This isn't your game!", ephemeral=True)
                    return
                    
                if self.played:
                    await button_interaction.response.send_message("You already played!", ephemeral=True)
                    return
                
                self.played = True
                bot_choice = random.choice(["rock", "paper", "scissors"])
                
                # Determine winner
                emoji_map = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
                
                if choice == bot_choice:
                    result = "tie"
                    winnings = 0
                elif (choice == "rock" and bot_choice == "scissors") or \
                     (choice == "paper" and bot_choice == "rock") or \
                     (choice == "scissors" and bot_choice == "paper"):
                    result = "win"
                    winnings = self.bet_amount
                    db.add_coins(self.user_id, winnings)
                else:
                    result = "lose"
                    winnings = -self.bet_amount
                    db.remove_coins(self.user_id, self.bet_amount)
                
                # Create result embed
                if result == "win":
                    embed = discord.Embed(title="🎉 You Won!", color=0x00ff00)
                    embed.description = f"You gained **{winnings} coins**!"
                elif result == "lose":
                    embed = discord.Embed(title="😢 You Lost!", color=0xff0000)
                    embed.description = f"You lost **{self.bet_amount} coins**!"
                else:
                    embed = discord.Embed(title="🤝 It's a Tie!", color=0xffff00)
                    embed.description = "No coins lost or gained!"
                
                embed.add_field(name="Your Choice", value=f"{emoji_map[choice]} {choice.title()}", inline=True)
                embed.add_field(name="Bot Choice", value=f"{emoji_map[bot_choice]} {bot_choice.title()}", inline=True)
                
                # Disable all buttons
                for item in self.children:
                    item.disabled = True
                
                await button_interaction.response.edit_message(embed=embed, view=self)
        
        embed = discord.Embed(
            title="🪨📄✂️ Rock Paper Scissors",
            description=f"**Bet:** {bet} coins\n\nChoose your weapon!",
            color=0x3498db
        )
        
        view = RPSView(interaction.user.id, bet)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="wordchain", description="🔤 Word chain game - build words from the last letter!")
    async def word_chain(self, interaction: discord.Interaction):
        can_play, time_left = self.check_cooldown(interaction.user.id, "wordchain", 45)
        if not can_play:
            await interaction.response.send_message(
                f"🕐 You can play word chain again in {int(time_left)} seconds!", 
                ephemeral=True
            )
            return

        # Start words
        start_words = ["apple", "computer", "discord", "python", "gaming", "music", "coding", "robot"]
        current_word = random.choice(start_words)
        last_letter = current_word[-1].lower()
        
        class WordChainModal(Modal, title="Word Chain Challenge"):
            def __init__(self, current_word, last_letter, user_id):
                super().__init__()
                self.current_word = current_word
                self.last_letter = last_letter
                self.user_id = user_id
                
            word_input = TextInput(
                label="Enter a word starting with the last letter:",
                placeholder="Type your word here...",
                max_length=20,
                min_length=3
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                user_word = self.word_input.value.lower().strip()
                
                # Validate word
                if not user_word.startswith(self.last_letter):
                    embed = discord.Embed(
                        title="❌ Invalid Word",
                        description=f"Your word must start with '{self.last_letter.upper()}'!",
                        color=0xff0000
                    )
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                if len(user_word) < 3:
                    embed = discord.Embed(
                        title="❌ Too Short",
                        description="Word must be at least 3 letters long!",
                        color=0xff0000
                    )
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Calculate reward based on word length and difficulty
                base_reward = len(user_word) * 2
                bonus = 5 if len(user_word) >= 7 else 0
                total_reward = base_reward + bonus
                
                db.add_coins(self.user_id, total_reward)
                
                embed = discord.Embed(
                    title="✅ Great Word!",
                    description=f"**'{user_word.title()}'** is a valid word!",
                    color=0x00ff00
                )
                embed.add_field(name="💰 Reward", value=f"{total_reward} coins", inline=True)
                embed.add_field(name="📏 Length Bonus", value=f"{len(user_word)} letters", inline=True)
                if bonus > 0:
                    embed.add_field(name="🎉 Length Bonus", value=f"+{bonus} coins", inline=True)
                
                await modal_interaction.response.send_message(embed=embed)
        
        embed = discord.Embed(
            title="🔤 Word Chain Challenge",
            description=f"**Current word:** `{current_word.title()}`\n**Last letter:** `{last_letter.upper()}`\n\nFind a word that starts with **{last_letter.upper()}**!",
            color=0x9b59b6
        )
        embed.add_field(name="💰 Rewards", value="• 2 coins per letter\n• +5 bonus for 7+ letters", inline=False)
        embed.set_footer(text="Click the button below to enter your word!")
        
        class WordChainView(View):
            def __init__(self, current_word, last_letter, user_id):
                super().__init__(timeout=60)
                self.current_word = current_word
                self.last_letter = last_letter
                self.user_id = user_id
                
            @discord.ui.button(label="Enter Word", emoji="✏️", style=discord.ButtonStyle.primary)
            async def enter_word(self, button_interaction: discord.Interaction, button: Button):
                if button_interaction.user.id != self.user_id:
                    await button_interaction.response.send_message("This isn't your game!", ephemeral=True)
                    return
                
                modal = WordChainModal(self.current_word, self.last_letter, self.user_id)
                await button_interaction.response.send_modal(modal)
        
        view = WordChainView(current_word, last_letter, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="slots", description="🎰 Spin the slot machine and win big!")
    async def slots(self, interaction: discord.Interaction, bet: int = 20):
        if bet < 10:
            await interaction.response.send_message("Minimum bet is 10 coins!", ephemeral=True)
            return
        if bet > 200:
            await interaction.response.send_message("Maximum bet is 200 coins!", ephemeral=True)
            return
            
        # Check if user has enough coins
        user_data = db.get_user_data(interaction.user.id)
        if user_data.get('coins', 0) < bet:
            await interaction.response.send_message("You don't have enough coins!", ephemeral=True)
            return

        can_play, time_left = self.check_cooldown(interaction.user.id, "slots", 30)
        if not can_play:
            await interaction.response.send_message(
                f"🕐 You can play slots again in {int(time_left)} seconds!", 
                ephemeral=True
            )
            return

        # Slot symbols with different rarities
        symbols = {
            "🍒": {"weight": 30, "multiplier": 2},
            "🍋": {"weight": 25, "multiplier": 3},
            "🍊": {"weight": 20, "multiplier": 4},
            "🍇": {"weight": 15, "multiplier": 5},
            "🔔": {"weight": 8, "multiplier": 10},
            "💎": {"weight": 2, "multiplier": 50}
        }
        
        # Create weighted symbol list
        symbol_list = []
        for symbol, data in symbols.items():
            symbol_list.extend([symbol] * data["weight"])
        
        # Spin the slots
        results = [random.choice(symbol_list) for _ in range(3)]
        
        # Calculate winnings
        if len(set(results)) == 1:  # All three match
            multiplier = symbols[results[0]]["multiplier"]
            winnings = bet * multiplier
            win_type = "JACKPOT"
            color = 0xffd700
        elif len(set(results)) == 2:  # Two match
            matching_symbol = max(set(results), key=results.count)
            multiplier = symbols[matching_symbol]["multiplier"] // 2
            winnings = bet * max(1, multiplier)
            win_type = "WIN"
            color = 0x00ff00
        else:  # No match
            winnings = 0
            win_type = "LOSE"
            color = 0xff0000
        
        # Update coins
        if winnings > 0:
            db.add_coins(interaction.user.id, winnings - bet)  # Net gain
        else:
            db.remove_coins(interaction.user.id, bet)
        
        # Create result embed
        embed = discord.Embed(
            title="🎰 Slot Machine Results",
            description=f"{''.join(results)}\n\n**{win_type}!**",
            color=color
        )
        
        if winnings > 0:
            embed.add_field(name="💰 Winnings", value=f"{winnings} coins", inline=True)
            embed.add_field(name="📈 Net Gain", value=f"+{winnings - bet} coins", inline=True)
        else:
            embed.add_field(name="💸 Lost", value=f"{bet} coins", inline=True)
        
        embed.add_field(name="🎯 Bet", value=f"{bet} coins", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dailychallenge", description="🎯 Complete daily challenges for bonus rewards!")
    async def daily_challenge(self, interaction: discord.Interaction):
        user_data = db.get_user_data(interaction.user.id)
        last_challenge = user_data.get('last_daily_challenge', 0)
        current_time = datetime.now().timestamp()
        
        # Check if already completed today
        if current_time - last_challenge < 86400:  # 24 hours
            time_left = 86400 - (current_time - last_challenge)
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            await interaction.response.send_message(
                f"🕐 Daily challenge resets in {hours}h {minutes}m!", 
                ephemeral=True
            )
            return
        
        # Daily challenges
        challenges = [
            {"name": "Trivia Master", "description": "Answer 3 trivia questions correctly", "reward": 100, "type": "trivia"},
            {"name": "Lucky Gambler", "description": "Win any game 3 times", "reward": 150, "type": "gambling"},
            {"name": "Word Wizard", "description": "Complete 5 word chain challenges", "reward": 120, "type": "wordchain"},
            {"name": "Social Butterfly", "description": "Send 50 messages in the server", "reward": 80, "type": "messages"},
            {"name": "Slot Champion", "description": "Win at slots 2 times", "reward": 200, "type": "slots"}
        ]
        
        today_challenge = challenges[int(current_time // 86400) % len(challenges)]
        
        embed = discord.Embed(
            title="🎯 Daily Challenge",
            description=f"**{today_challenge['name']}**\n{today_challenge['description']}",
            color=0xe74c3c
        )
        embed.add_field(name="🏆 Reward", value=f"{today_challenge['reward']} coins", inline=True)
        embed.add_field(name="⏰ Time Left", value="24 hours", inline=True)
        embed.set_footer(text="Complete the challenge to claim your reward!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="tournament", description="🏆 Join community tournaments for massive rewards!")
    async def tournament(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏆 Tournament Hub",
            description="Community tournaments are coming soon!\n\nFeatures:\n• Weekly RPS tournaments\n• Trivia championships\n• Speed word challenges\n• Massive coin prizes",
            color=0xf39c12
        )
        embed.set_footer(text="Stay tuned for tournament announcements!")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MiniGames(bot))