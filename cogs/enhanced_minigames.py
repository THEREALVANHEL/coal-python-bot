import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput
import random
import asyncio
import time
from datetime import datetime, timedelta
import os, sys
import json

# Local import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database as db

class EnhancedMiniGames(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Anti-spam protection
        self.game_cooldowns = {}
        self.word_lists = self.load_word_lists()
        
    def load_word_lists(self):
        """Load word lists for word chain validation"""
        return {
            "common": [
                "apple", "banana", "computer", "discord", "elephant", "flower", "guitar", "house", 
                "internet", "jacket", "keyboard", "laptop", "music", "nature", "orange", "python",
                "queen", "rabbit", "science", "technology", "umbrella", "victory", "water", "xylophone",
                "yellow", "zebra", "amazing", "beautiful", "creative", "dynamic", "electric", "fantastic",
                "gigantic", "happiness", "incredible", "joyful", "knowledge", "learning", "magnificent",
                "notebook", "outstanding", "programming", "question", "rainbow", "sunshine", "telephone",
                "universe", "wonderful", "excellent", "yesterday", "zoology"
            ],
            "programming": [
                "algorithm", "boolean", "compiler", "database", "exception", "function", "github",
                "html", "integer", "javascript", "kernel", "library", "method", "nodejs", "object",
                "python", "query", "repository", "syntax", "typescript", "ubuntu", "variable",
                "website", "xml", "yaml", "zip"
            ],
            "science": [
                "atom", "biology", "chemistry", "dna", "evolution", "fossil", "galaxy", "hydrogen",
                "isotope", "jupiter", "kinetic", "laser", "molecule", "neutron", "oxygen", "planet",
                "quantum", "radiation", "sodium", "telescope", "uranium", "velocity", "wavelength",
                "xenon", "year", "zinc"
            ]
        }

    def check_cooldown(self, user_id: int, game_type: str, cooldown_seconds: int = 30) -> tuple:
        """Check if user is on cooldown for specific game"""
        current_time = time.time()
        cooldown_key = f"{user_id}_{game_type}"
        
        if cooldown_key in self.game_cooldowns:
            time_left = self.game_cooldowns[cooldown_key] - current_time
            if time_left > 0:
                return False, time_left
                
        self.game_cooldowns[cooldown_key] = current_time + cooldown_seconds
        return True, 0

    def validate_word(self, word: str, required_start_letter: str) -> bool:
        """Enhanced word validation using comprehensive word lists"""
        word = word.lower().strip()
        
        # Must start with correct letter
        if not word.startswith(required_start_letter.lower()):
            return False
        
        # Check against our word lists
        all_words = []
        for category in self.word_lists.values():
            all_words.extend(category)
        
        if word in all_words:
            return True
        
        # Common English words by length
        common_words = {
            3: ["cat", "dog", "car", "run", "sun", "fun", "bat", "hat", "rat", "mat", "sat", "fat", 
                "pen", "ten", "hen", "den", "men", "net", "bet", "get", "set", "wet", "let", "met", 
                "pet", "jet", "yet", "but", "cut", "gut", "hut", "jut", "nut", "put", "rut", "art",
                "eat", "ice", "age", "ace", "add", "aid", "air", "all", "and", "any", "are", "arm",
                "ask", "bad", "bag", "bar", "bed", "big", "bit", "box", "boy", "bus", "buy", "can",
                "day", "did", "end", "eye", "far", "few", "for", "got", "had", "has", "her", "him",
                "his", "how", "its", "job", "key", "law", "lay", "leg", "lot", "low", "man", "may",
                "new", "now", "old", "one", "our", "out", "own", "pay", "red", "say", "see", "she",
                "sit", "six", "son", "too", "top", "try", "two", "use", "war", "way", "who", "why",
                "win", "yes", "you"],
            4: ["able", "about", "even", "back", "also", "come", "down", "each", "find", "give", 
                "good", "hand", "have", "help", "here", "home", "into", "just", "keep", "know",
                "last", "left", "life", "like", "line", "live", "long", "look", "make", "many",
                "more", "most", "move", "much", "name", "need", "next", "only", "open", "over",
                "part", "play", "read", "real", "same", "seem", "show", "side", "some", "take",
                "tell", "that", "then", "they", "this", "time", "turn", "used", "very", "want",
                "week", "well", "went", "were", "what", "when", "with", "word", "work", "year"],
            5: ["about", "after", "again", "being", "below", "could", "every", "first", "found",
                "great", "group", "house", "large", "learn", "place", "plant", "point", "right",
                "small", "sound", "still", "study", "their", "there", "these", "thing", "think",
                "three", "under", "water", "where", "which", "while", "world", "would", "write"]
        }
        
        word_length = len(word)
        if word_length in common_words and word in common_words[word_length]:
            return True
        
        # For longer words (6+ characters), be more lenient as they're likely real words
        if word_length >= 6:
            # Basic checks for likely valid words
            vowels = set('aeiou')
            consonants = set('bcdfghjklmnpqrstvwxyz')
            
            # Must have at least one vowel
            if not any(c in vowels for c in word):
                return False
            
            # Must have at least one consonant
            if not any(c in consonants for c in word):
                return False
            
            # No more than 3 consecutive identical letters
            for i in range(len(word) - 2):
                if word[i] == word[i+1] == word[i+2]:
                    return False
            
            # Looks like a valid word
            return True
        
        return False

    def generate_ai_trivia_question(self, difficulty: str = "medium") -> dict:
        """Generate AI-powered trivia questions dynamically"""
        # Categories and their question templates
        categories = {
            "programming": {
                "easy": [
                    "What programming language is known for its simplicity and readability?",
                    "What does 'HTML' stand for?",
                    "Which symbol is used for comments in Python?",
                    "What is the file extension for Python files?",
                    "What does 'CSS' stand for?",
                    "Which company created JavaScript?",
                    "What does 'URL' stand for?",
                    "Which tag is used for line breaks in HTML?"
                ],
                "medium": [
                    "What is the time complexity of binary search?",
                    "Which design pattern ensures only one instance of a class exists?",
                    "What does 'API' stand for in programming?",
                    "Which data structure follows LIFO principle?",
                    "What does 'JSON' stand for?",
                    "Which HTTP method is used to retrieve data?",
                    "What is the default port for HTTP?",
                    "Which programming language was created by Guido van Rossum?"
                ],
                "hard": [
                    "What is the space complexity of merge sort?",
                    "Which algorithm is used for finding shortest path in unweighted graphs?",
                    "What is the difference between TCP and UDP?",
                    "Which sorting algorithm has best average case performance?",
                    "What is the time complexity of quicksort in worst case?",
                    "Which data structure is best for implementing a priority queue?",
                    "What does ACID stand for in database systems?",
                    "Which consensus algorithm is used in Bitcoin?"
                ]
            },
            "general": {
                "easy": [
                    "What is the largest planet in our solar system?",
                    "How many continents are there?",
                    "What is the capital of France?",
                    "Which animal is known as the king of the jungle?"
                ],
                "medium": [
                    "Who invented the telephone?",
                    "What is the speed of light in vacuum?",
                    "Which element has the symbol 'Au'?",
                    "In which year did World War II end?"
                ],
                "hard": [
                    "What is the smallest unit of matter?",
                    "Who developed the theory of relativity?",
                    "What is the Planck constant approximately?",
                    "Which mountain range separates Europe and Asia?"
                ]
            },
            "technology": {
                "easy": [
                    "What does 'WWW' stand for?",
                    "Which company created the iPhone?",
                    "What is the most popular search engine?",
                    "What does 'USB' stand for?"
                ],
                "medium": [
                    "Who founded Microsoft?",
                    "What is the latest version of HTTP?",
                    "Which programming language was created by Google?",
                    "What does 'IoT' stand for?"
                ],
                "hard": [
                    "What is the theoretical maximum speed of USB 3.0?",
                    "Which encryption algorithm is considered quantum-resistant?",
                    "What is the difference between machine learning and deep learning?",
                    "Which protocol is used for secure web communication?"
                ]
            }
        }
        
        # Select random category and question
        category = random.choice(list(categories.keys()))
        questions = categories[category][difficulty]
        question_text = random.choice(questions)
        
        # Generate realistic but random options based on category
        if category == "programming":
            if "Python" in question_text:
                options = ["Python", "Java", "C++", "JavaScript"]
                correct = 0
            elif "HTML" in question_text:
                options = ["HyperText Markup Language", "High Tech Modern Language", "Home Tool Markup Language", "Hyper Transfer Markup Language"]
                correct = 0
            elif "comments" in question_text:
                options = ["#", "//", "/*", "<!--"]
                correct = 0
            elif "file extension" in question_text:
                options = [".py", ".java", ".cpp", ".js"]
                correct = 0
            elif "binary search" in question_text:
                options = ["O(log n)", "O(n)", "O(n²)", "O(1)"]
                correct = 0
            elif "LIFO" in question_text:
                options = ["Stack", "Queue", "Array", "Tree"]
                correct = 0
            elif "API" in question_text:
                options = ["Application Programming Interface", "Automated Program Integration", "Advanced Programming Instructions", "Application Process Interface"]
                correct = 0
            elif "Singleton" in question_text or "one instance" in question_text:
                options = ["Singleton", "Factory", "Observer", "Strategy"]
                correct = 0
            elif "CSS" in question_text:
                options = ["Cascading Style Sheets", "Computer Style Sheets", "Creative Style Sheets", "Colorful Style Sheets"]
                correct = 0
            elif "JavaScript" in question_text and "company" in question_text:
                options = ["Netscape", "Microsoft", "Google", "Mozilla"]
                correct = 0
            elif "URL" in question_text:
                options = ["Uniform Resource Locator", "Universal Resource Locator", "Unique Resource Locator", "United Resource Locator"]
                correct = 0
            elif "line breaks" in question_text:
                options = ["<br>", "<break>", "<lb>", "<newline>"]
                correct = 0
            elif "JSON" in question_text:
                options = ["JavaScript Object Notation", "Java Standard Object Notation", "JavaScript Organized Notation", "Java Structured Object Notation"]
                correct = 0
            elif "HTTP method" in question_text and "retrieve" in question_text:
                options = ["GET", "POST", "PUT", "DELETE"]
                correct = 0
            elif "default port" in question_text and "HTTP" in question_text:
                options = ["80", "443", "8080", "3000"]
                correct = 0
            elif "Guido van Rossum" in question_text:
                options = ["Python", "Java", "Ruby", "JavaScript"]
                correct = 0
            elif "quicksort" in question_text and "worst case" in question_text:
                options = ["O(n²)", "O(n log n)", "O(n)", "O(log n)"]
                correct = 0
            elif "priority queue" in question_text:
                options = ["Heap", "Stack", "Queue", "Array"]
                correct = 0
            elif "ACID" in question_text:
                options = ["Atomicity Consistency Isolation Durability", "Advanced Computer Information Database", "Automatic Consistent Information Database", "Advanced Consistent Integrated Data"]
                correct = 0
            elif "Bitcoin" in question_text and "consensus" in question_text:
                options = ["Proof of Work", "Proof of Stake", "Delegated Proof of Stake", "Proof of Authority"]
                correct = 0
            else:
                options = ["Option A", "Option B", "Option C", "Option D"]
                correct = random.randint(0, 3)
        elif category == "general":
            if "largest planet" in question_text:
                options = ["Jupiter", "Saturn", "Earth", "Mars"]
                correct = 0
            elif "continents" in question_text:
                options = ["7", "6", "8", "5"]
                correct = 0
            elif "France" in question_text:
                options = ["Paris", "London", "Berlin", "Madrid"]
                correct = 0
            elif "king of jungle" in question_text:
                options = ["Lion", "Tiger", "Elephant", "Leopard"]
                correct = 0
            elif "telephone" in question_text:
                options = ["Alexander Graham Bell", "Thomas Edison", "Nikola Tesla", "Benjamin Franklin"]
                correct = 0
            elif "speed of light" in question_text:
                options = ["299,792,458 m/s", "300,000,000 m/s", "299,000,000 m/s", "301,000,000 m/s"]
                correct = 0
            elif "Au" in question_text:
                options = ["Gold", "Silver", "Aluminum", "Argon"]
                correct = 0
            else:
                options = ["Option A", "Option B", "Option C", "Option D"]
                correct = random.randint(0, 3)
        else:  # technology
            if "WWW" in question_text:
                options = ["World Wide Web", "World Wide Website", "Worldwide Web", "Web Wide World"]
                correct = 0
            elif "iPhone" in question_text:
                options = ["Apple", "Google", "Microsoft", "Samsung"]
                correct = 0
            elif "search engine" in question_text:
                options = ["Google", "Bing", "Yahoo", "DuckDuckGo"]
                correct = 0
            elif "USB" in question_text:
                options = ["Universal Serial Bus", "United Serial Bus", "Universal System Bus", "United System Bus"]
                correct = 0
            else:
                options = ["Option A", "Option B", "Option C", "Option D"]
                correct = random.randint(0, 3)
        
        # Shuffle options while keeping track of correct answer
        correct_answer = options[correct]
        random.shuffle(options)
        new_correct_index = options.index(correct_answer)
        
        # Calculate reward based on difficulty
        reward_map = {"easy": 10, "medium": 20, "hard": 35}
        
        return {
            "question": question_text,
            "options": options,
            "correct": new_correct_index,
            "difficulty": difficulty,
            "reward": reward_map[difficulty],
            "category": category
        }

    @app_commands.command(name="trivia", description="🧠 AI-powered trivia with dynamic questions!")
    async def trivia(self, interaction: discord.Interaction, difficulty: str = "medium"):
        # Check cooldown
        can_play, time_left = self.check_cooldown(interaction.user.id, "trivia", 60)
        if not can_play:
            await interaction.response.send_message(
                f"🕐 You can play trivia again in {int(time_left)} seconds!", 
                ephemeral=True
            )
            return

        # Validate difficulty
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "medium"

        question_data = self.generate_ai_trivia_question(difficulty)
        
        class SmartTriviaView(View):
            def __init__(self, question_data, user_id):
                super().__init__(timeout=45)
                self.question_data = question_data
                self.user_id = user_id
                self.answered = False
                
                # Add answer buttons with letters
                for i, option in enumerate(question_data["options"]):
                    button = Button(
                        label=f"{chr(65+i)}) {option[:50]}", 
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
                # Get the button that was clicked
                button = None
                for item in self.children:
                    if hasattr(item, 'custom_id') and item.custom_id == button_interaction.data.get('custom_id'):
                        button = item
                        break
                
                if not button:
                    await button_interaction.response.send_message("Error identifying button!", ephemeral=True)
                    return
                
                selected = int(button.custom_id)
                correct = selected == self.question_data["correct"]
                
                # Disable all buttons
                for item in self.children:
                    item.disabled = True
                    if int(item.custom_id) == self.question_data["correct"]:
                        item.style = discord.ButtonStyle.success
                    elif int(item.custom_id) == selected and not correct:
                        item.style = discord.ButtonStyle.danger
                
                if correct:
                    # Give coins based on difficulty
                    reward = self.question_data["reward"]
                    db.add_coins(self.user_id, reward)
                    
                    result_embed = discord.Embed(
                        title="🎉 Correct Answer!",
                        description=f"**Well done!** You earned **{reward} coins**!",
                        color=0x00ff00
                    )
                    result_embed.add_field(
                        name="💰 Difficulty Bonus",
                        value=f"**{self.question_data['difficulty'].title()}** question (+{reward} coins)",
                        inline=True
                    )
                    result_embed.add_field(
                        name="📚 Category",
                        value=f"{self.question_data['category'].title()}",
                        inline=True
                    )
                else:
                    correct_answer = self.question_data["options"][self.question_data["correct"]]
                    result_embed = discord.Embed(
                        title="❌ Wrong Answer",
                        description=f"The correct answer was: **{correct_answer}**\n\nBetter luck next time!",
                        color=0xff0000
                    )
                    result_embed.add_field(
                        name="📚 Category",
                        value=f"{self.question_data['category'].title()}",
                        inline=True
                    )
                    result_embed.add_field(
                        name="🎯 Difficulty",
                        value=f"{self.question_data['difficulty'].title()}",
                        inline=True
                    )
                
                await button_interaction.response.edit_message(view=self)
                await button_interaction.followup.send(embed=result_embed)

        embed = discord.Embed(
            title="🧠 Trivia Challenge",
            description=f"**Category:** {question_data['category'].title()}\n"
                       f"**Difficulty:** {question_data['difficulty'].title()}\n"
                       f"**Reward:** {question_data['reward']} coins\n\n"
                       f"**Question:** {question_data['question']}",
            color=0x9b59b6
        )
        embed.set_footer(text="Choose your answer below! ⏰ 45 seconds to answer")
        
        view = SmartTriviaView(question_data, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    def generate_word_chain_challenge(self) -> dict:
        """Generate a word chain challenge without revealing the answer"""
        # Start with a random word from our lists
        all_words = []
        for category in self.word_lists.values():
            all_words.extend(category)
        
        start_word = random.choice(all_words)
        last_letter = start_word[-1].lower()
        
        # Find valid words that start with the last letter (for validation)
        valid_words = [word for word in all_words if word.lower().startswith(last_letter)]
        
        return {
            "start_word": start_word,
            "last_letter": last_letter,
            "valid_words": valid_words
        }

    @app_commands.command(name="wordchain", description="🔤 Enhanced word chain - no hints, just skill!")
    async def wordchain(self, interaction: discord.Interaction):
        can_play, time_left = self.check_cooldown(interaction.user.id, "wordchain", 45)
        if not can_play:
            await interaction.response.send_message(
                f"🕐 You can play word chain again in {int(time_left)} seconds!", 
                ephemeral=True
            )
            return

        challenge = self.generate_word_chain_challenge()
        current_word = challenge["start_word"]
        last_letter = challenge["last_letter"]
        
        class SmartWordChainModal(Modal, title="Smart Word Chain Challenge"):
            def __init__(self, current_word, last_letter, valid_words, user_id):
                super().__init__()
                self.current_word = current_word
                self.last_letter = last_letter
                self.valid_words = valid_words
                self.user_id = user_id
                
            word_input = TextInput(
                label=f"Enter a word starting with '{last_letter.upper()}':",
                placeholder="Type your word here...",
                max_length=25,
                min_length=3
            )
            
            async def on_submit(self, modal_interaction: discord.Interaction):
                user_word = self.word_input.value.lower().strip()
                
                # Validate word starts with correct letter
                if not user_word.startswith(self.last_letter):
                    embed = discord.Embed(
                        title="❌ Invalid Starting Letter",
                        description=f"Your word must start with **'{self.last_letter.upper()}'**!\n"
                                   f"You entered: **'{user_word}'**",
                        color=0xff0000
                    )
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Check minimum length
                if len(user_word) < 3:
                    embed = discord.Embed(
                        title="❌ Too Short",
                        description="Word must be at least **3 letters** long!",
                        color=0xff0000
                    )
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Enhanced word validation
                is_valid_word = self.validate_word(user_word, self.last_letter)
                
                if not is_valid_word:
                    embed = discord.Embed(
                        title="❌ Invalid Word",
                        description=f"**'{user_word}'** doesn't appear to be a valid English word.\n"
                                   "Try a different word!",
                        color=0xff0000
                    )
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Calculate reward based on word length and difficulty
                base_reward = len(user_word) * 3
                length_bonus = 0
                
                if len(user_word) >= 7:
                    length_bonus = 10
                elif len(user_word) >= 5:
                    length_bonus = 5
                
                # Special bonus for creative/uncommon words
                creativity_bonus = 0
                if len(user_word) >= 8:
                    creativity_bonus = 5
                
                total_reward = base_reward + length_bonus + creativity_bonus
                
                # Award coins
                db.add_coins(self.user_id, total_reward)
                
                # Create success embed
                success_embed = discord.Embed(
                    title="✅ Excellent Word!",
                    description=f"**'{user_word.title()}'** is a great choice!",
                    color=0x00ff00
                )
                success_embed.add_field(
                    name="💰 Total Reward",
                    value=f"**{total_reward} coins**",
                    inline=True
                )
                success_embed.add_field(
                    name="📏 Word Length",
                    value=f"**{len(user_word)} letters**",
                    inline=True
                )
                
                bonus_text = []
                if length_bonus > 0:
                    bonus_text.append(f"Length bonus: +{length_bonus}")
                if creativity_bonus > 0:
                    bonus_text.append(f"Creativity bonus: +{creativity_bonus}")
                
                if bonus_text:
                    success_embed.add_field(
                        name="🎉 Bonuses",
                        value="\n".join(bonus_text),
                        inline=False
                    )
                
                success_embed.set_footer(text=f"Next word should start with '{user_word[-1].upper()}'")
                
                await modal_interaction.response.send_message(embed=success_embed)
        
        embed = discord.Embed(
            title="🔤 Word Chain Challenge",
            description=f"**Starting word:** `{current_word.title()}`\n"
                       f"**Your task:** Find a word that starts with **'{last_letter.upper()}'**\n\n"
                       f"💡 **Tips:**\n"
                       f"• Longer words = more coins\n"
                       f"• Creative words get bonus points\n"
                       f"• Minimum 3 letters required",
            color=0x9b59b6
        )
        embed.add_field(
            name="💰 Reward System",
            value="• 3 coins per letter\n• +5 bonus for 5+ letters\n• +10 bonus for 7+ letters\n• +5 creativity bonus for 8+ letters",
            inline=False
        )
        embed.set_footer(text="Click the button below to enter your word!")
        
        class SmartWordChainView(View):
            def __init__(self, current_word, last_letter, valid_words, user_id):
                super().__init__(timeout=90)
                self.current_word = current_word
                self.last_letter = last_letter
                self.valid_words = valid_words
                self.user_id = user_id
                
            @discord.ui.button(label="Enter Word", emoji="✏️", style=discord.ButtonStyle.primary)
            async def enter_word(self, button_interaction: discord.Interaction, button: Button):
                if button_interaction.user.id != self.user_id:
                    await button_interaction.response.send_message("This isn't your game!", ephemeral=True)
                    return
                
                modal = SmartWordChainModal(
                    self.current_word, 
                    self.last_letter, 
                    self.valid_words, 
                    self.user_id
                )
                await button_interaction.response.send_modal(modal)
        
        view = SmartWordChainView(current_word, last_letter, challenge["valid_words"], interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(EnhancedMiniGames(bot))