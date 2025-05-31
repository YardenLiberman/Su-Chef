#!/usr/bin/env python3
"""
Su-Chef - Clean & Organized Cooking Assistant
Combines all functionality with better organization and structure.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Optional imports with graceful fallback
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import azure.cognitiveservices.speech as speechsdk
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

class RecipeDatabase:
    """Handles all database operations for recipes and user data."""
    
    def __init__(self, db_name="su_chef.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
    
    def create_tables(self):
        """Create all necessary database tables."""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Recipes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            cooking_time INTEGER,
            skill_level TEXT,
            dietary_restrictions TEXT,
            ingredients TEXT,
            steps TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # User recipe history
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_recipe_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            recipe_id INTEGER,
            cooked BOOLEAN DEFAULT FALSE,
            liked BOOLEAN DEFAULT FALSE,
            cooked_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id)
        )
        ''')
        
        self.conn.commit()
    
    def add_user(self, username: str) -> int:
        """Add user or return existing user ID."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            return cursor.fetchone()[0]
    
    def save_recipe(self, recipe_data: Dict[str, Any], user_id: int) -> int:
        """Save recipe and add to user history."""
        cursor = self.conn.cursor()
        
        cursor.execute('''
        INSERT INTO recipes (name, meal_type, cooking_time, skill_level, 
                           dietary_restrictions, ingredients, steps)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            recipe_data['name'],
            recipe_data.get('meal_type', ''),
            recipe_data.get('cooking_time', 0),
            recipe_data.get('skill_level', ''),
            recipe_data.get('dietary_restrictions', ''),
            json.dumps(recipe_data['ingredients']),
            json.dumps(recipe_data['steps'])
        ))
        
        recipe_id = cursor.lastrowid
        
        # Add to user history
        cursor.execute('''
        INSERT INTO user_recipe_history (user_id, recipe_id, cooked_date)
        VALUES (?, ?, ?)
        ''', (user_id, recipe_id, datetime.now()))
        
        self.conn.commit()
        return recipe_id
    
    def get_user_recipes(self, user_id: int, search_type: str = 'all') -> List[tuple]:
        """Get recipes for user with optional filtering."""
        cursor = self.conn.cursor()
        
        if search_type == 'all':
            cursor.execute('''
            SELECT r.recipe_id, r.name, r.cooking_time, r.skill_level, r.created_at
            FROM recipes r
            JOIN user_recipe_history urh ON r.recipe_id = urh.recipe_id
            WHERE urh.user_id = ?
            ORDER BY r.created_at DESC
            ''', (user_id,))
        elif search_type == 'cooked':
            cursor.execute('''
            SELECT r.recipe_id, r.name, r.cooking_time, r.skill_level, r.created_at
            FROM recipes r
            JOIN user_recipe_history urh ON r.recipe_id = urh.recipe_id
            WHERE urh.user_id = ? AND urh.cooked = TRUE
            ORDER BY urh.cooked_date DESC
            ''', (user_id,))
        elif search_type == 'liked':
            cursor.execute('''
            SELECT r.recipe_id, r.name, r.cooking_time, r.skill_level, r.created_at
            FROM recipes r
            JOIN user_recipe_history urh ON r.recipe_id = urh.recipe_id
            WHERE urh.user_id = ? AND urh.liked = TRUE
            ORDER BY urh.cooked_date DESC
            ''', (user_id,))
        
        return cursor.fetchall()
    
    def search_recipes_by_name(self, query: str) -> List[tuple]:
        """Search recipes by name."""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT recipe_id, name, cooking_time, skill_level, created_at
        FROM recipes
        WHERE name LIKE ?
        ORDER BY created_at DESC
        ''', (f'%{query}%',))
        return cursor.fetchall()
    
    def get_recipe_details(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get complete recipe details."""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT name, meal_type, cooking_time, skill_level, dietary_restrictions, 
               ingredients, steps
        FROM recipes WHERE recipe_id = ?
        ''', (recipe_id,))
        
        result = cursor.fetchone()
        if not result:
            return None
        
        return {
            'name': result[0],
            'meal_type': result[1],
            'cooking_time': result[2],
            'skill_level': result[3],
            'dietary_restrictions': result[4],
            'ingredients': json.loads(result[5]),
            'steps': json.loads(result[6])
        }
    
    def mark_recipe_cooked(self, user_id: int, recipe_id: int, liked: bool = False):
        """Mark recipe as cooked and optionally liked."""
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE user_recipe_history 
        SET cooked = TRUE, liked = ?, cooked_date = ?
        WHERE user_id = ? AND recipe_id = ?
        ''', (liked, datetime.now(), user_id, recipe_id))
        self.conn.commit()
    
    def get_user_statistics(self, user_id: int) -> Dict[str, int]:
        """Get user cooking statistics."""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN cooked = TRUE THEN 1 ELSE 0 END) as cooked,
            SUM(CASE WHEN liked = TRUE THEN 1 ELSE 0 END) as liked
        FROM user_recipe_history
        WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        return {
            'total': result[0],
            'cooked': result[1],
            'liked': result[2]
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()

class RecipeGenerator:
    """Handles AI recipe generation using OpenAI."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key) if OPENAI_AVAILABLE else None
    
    def generate_recipe(self, meal_type: str, cooking_time: int, skill_level: str, 
                       dietary_restrictions: str = None, available_ingredients: List[str] = None) -> Optional[str]:
        """Generate recipe using OpenAI."""
        if not self.client:
            return None
        
        prompt = self._build_prompt(meal_type, cooking_time, skill_level, 
                                  dietary_restrictions, available_ingredients)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating recipe: {e}")
            return None
    
    def _build_prompt(self, meal_type: str, cooking_time: int, skill_level: str,
                     dietary_restrictions: str = None, available_ingredients: List[str] = None) -> str:
        """Build recipe generation prompt."""
        prompt = f"""Create a {meal_type} recipe that:
- Takes {cooking_time} minutes or less to prepare
- Is suitable for a {skill_level} cook"""
        
        if available_ingredients:
            prompt += f"\n- Uses some of these ingredients: {', '.join(available_ingredients)}"
        
        if dietary_restrictions:
            prompt += f"\n- Must be {dietary_restrictions}"
        
        prompt += """

Format your response exactly like this:
Recipe Name: [name]
Cooking Time: [time in minutes]
Ingredients:
- [ingredient 1]
- [ingredient 2]
Instructions:
1. [step 1]
2. [step 2]
"""
        return prompt
    
    def parse_recipe(self, recipe_text: str, meal_type: str, cooking_time: int, 
                    skill_level: str, dietary_restrictions: str = None) -> Optional[Dict[str, Any]]:
        """Parse AI-generated recipe text into structured data."""
        lines = recipe_text.split('\n')
        name = ""
        ingredients = []
        steps = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("Recipe Name:"):
                name = line.replace("Recipe Name:", "").strip()
            elif line.startswith("Ingredients:"):
                current_section = "ingredients"
            elif line.startswith("Instructions:"):
                current_section = "steps"
            elif line.startswith("-") and current_section == "ingredients":
                ingredients.append(line[1:].strip())
            elif line[0].isdigit() and current_section == "steps":
                step = line.split(".", 1)
                if len(step) > 1:
                    steps.append(step[1].strip())
        
        if name and ingredients and steps:
            return {
                'name': name,
                'meal_type': meal_type,
                'cooking_time': cooking_time,
                'skill_level': skill_level,
                'dietary_restrictions': dietary_restrictions,
                'ingredients': ingredients,
                'steps': steps
            }
        return None

class VoiceAgent:
    """Handles voice recognition and synthesis for cooking guidance."""
    
    def __init__(self, speech_key: str, speech_region: str = "westeurope"):
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.current_recipe = None
        self.current_step = 0
        self.is_interrupted = False
        
        if SPEECH_AVAILABLE:
            self._setup_speech_services()
    
    def _setup_speech_services(self):
        """Initialize Azure Speech Services."""
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
        self.recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
    
    def load_recipe(self, recipe_data: Dict[str, Any]) -> bool:
        """Load recipe for voice guidance."""
        self.current_recipe = recipe_data
        self.current_step = 0
        self.is_interrupted = False
        return True
    
    def speak(self, text: str) -> bool:
        """Speak text using TTS."""
        if not SPEECH_AVAILABLE:
            print(f"🔊 {text}")
            return True
        
        try:
            result = self.synthesizer.speak_text_async(text).get()
            return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted
        except:
            print(f"🔊 {text}")
            return False
    
    def listen(self) -> Optional[str]:
        """Listen for user input."""
        if not SPEECH_AVAILABLE:
            print("❌ Voice recognition not available - voice guidance disabled")
            return None
        
        try:
            print("🎤 Listening...")
            result = self.recognizer.recognize_once_async().get()
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = result.text.strip()
                print(f"You said: {text}")
                return text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("🔇 No speech detected - please try speaking again")
                return None
            else:
                print("🔇 Speech recognition failed - please try again")
                return None
        except Exception as e:
            print(f"❌ Voice recognition error: {e}")
            return None
    
    def run_voice_guidance(self) -> bool:
        """Run complete voice guidance session."""
        if not self.current_recipe:
            print("No recipe loaded!")
            return False
        
        if not SPEECH_AVAILABLE:
            print("❌ Voice guidance requires Azure Speech Services!")
            return False
        
        recipe = self.current_recipe
        
        # Introduction
        self.speak(f"Welcome to voice cooking! Today we're making {recipe['name']}.")
        self.speak("I'll guide you through each step. You can say 'next' to continue, 'repeat' to hear again, 'ingredients' to hear the ingredients, or 'stop' to end.")
        
        # Read ingredients
        self.speak("Let's start with the ingredients you'll need:")
        for ingredient in recipe['ingredients']:
            self.speak(ingredient)
        
        self.speak("Say 'ready' when you have everything prepared.")
        retry_count = 0
        max_retries = 3
        while True:
            response = self.listen()
            if response is None:
                retry_count += 1
                if retry_count >= max_retries:
                    self.speak("Voice recognition is having issues. Ending voice guidance.")
                    self.is_interrupted = True
                    return False
                self.speak("I didn't hear you. Please try again.")
                continue
            
            if any(word in response.lower() for word in ['ready', 'start', 'begin']):
                break
            elif any(word in response.lower() for word in ['stop', 'quit', 'exit']):
                self.is_interrupted = True
                return False
        
        # Go through cooking steps
        for i, step in enumerate(recipe['steps'], 1):
            self.current_step = i
            self.speak(f"Step {i}: {step}")
            
            step_retry_count = 0
            max_step_retries = 5
            while True:
                response = self.listen()
                if response is None:
                    step_retry_count += 1
                    if step_retry_count >= max_step_retries:
                        self.speak("Voice recognition is having too many issues. Ending cooking session.")
                        self.is_interrupted = True
                        return False
                    self.speak("I didn't catch that. Please try again.")
                    continue
                
                response_lower = response.lower()
                
                if any(word in response_lower for word in ['next', 'continue', 'done']):
                    break
                elif any(word in response_lower for word in ['repeat', 'again']):
                    self.speak(f"Step {i}: {step}")
                elif 'ingredients' in response_lower:
                    self.speak("Here are the ingredients:")
                    for ingredient in recipe['ingredients']:
                        self.speak(ingredient)
                elif any(word in response_lower for word in ['stop', 'quit', 'exit']):
                    self.speak("Cooking stopped. Come back anytime!")
                    self.is_interrupted = True
                    return False
                else:
                    # Use AI to answer cooking questions
                    self._handle_cooking_question(response, step)
            
            # Ask if ready for next step (except for the last step)
            if i < len(recipe['steps']):
                self.speak("Are you ready for the next step?")
                ready_retry_count = 0
                while True:
                    response = self.listen()
                    if response is None:
                        ready_retry_count += 1
                        if ready_retry_count >= 3:
                            self.speak("Moving to next step.")
                            break
                        self.speak("I didn't hear you. Say 'yes' when ready for the next step.")
                        continue
                    
                    if any(word in response.lower() for word in ['yes', 'ready', 'next', 'continue']):
                        break
                    elif any(word in response.lower() for word in ['no', 'wait', 'hold']):
                        self.speak("Take your time. Say 'ready' when you want to continue.")
                    elif any(word in response.lower() for word in ['stop', 'quit', 'exit']):
                        self.speak("Cooking stopped. Come back anytime!")
                        self.is_interrupted = True
                        return False
                    else:
                        self.speak("Say 'yes' when you're ready for the next step, or 'no' if you need more time.")
        
        self.speak("Congratulations! You've finished cooking. Enjoy your meal!")
        
        # Final completion confirmation
        self.speak("Cooking session complete! Say 'finished' to end, or 'repeat last step' if you need to hear the final step again.")
        final_retry_count = 0
        while True:
            response = self.listen()
            if response is None:
                final_retry_count += 1
                if final_retry_count >= 3:
                    self.speak("Cooking session ended. Great job!")
                    break
                self.speak("Say 'finished' to complete the cooking session.")
                continue
            
            response_lower = response.lower()
            if any(word in response_lower for word in ['finished', 'done', 'complete', 'end']):
                self.speak("Excellent work! Hope you enjoy your meal!")
                break
            elif any(word in response_lower for word in ['repeat', 'last', 'final']):
                final_step = len(recipe['steps'])
                self.speak(f"Final step: {recipe['steps'][final_step-1]}")
            else:
                self.speak("Say 'finished' when you're done cooking.")
        
        return True
    
    def _handle_cooking_question(self, question: str, current_step: str):
        """Handle cooking-related questions using AI."""
        # Simple responses for common questions
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['how long', 'time']):
            self.speak("Follow the timing mentioned in the step. If unsure, start with less time and check.")
        elif any(word in question_lower for word in ['temperature', 'heat']):
            self.speak("Use medium heat unless specified otherwise in the recipe.")
        elif any(word in question_lower for word in ['ready', 'done', 'finished']):
            self.speak("When it looks and smells right according to the step description, it's usually ready.")
        else:
            self.speak("I'm here to guide you through the steps. Try following the current instruction and let me know when you're ready for the next step.")

class SuChef:
    """Main application class that coordinates all components."""
    
    def __init__(self):
        print("🍳 Starting Su-Chef...")
        load_dotenv()
        
        # Initialize components
        self.db = RecipeDatabase()
        self.user_id = None
        self.current_recipe_id = None
        
        # Check API keys and initialize optional components
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.speech_key = os.getenv("SPEECH_KEY")
        self.speech_region = os.getenv("SPEECH_REGION", "westeurope")
        
        self.recipe_generator = RecipeGenerator(self.openai_key) if self.openai_key else None
        self.voice_agent = VoiceAgent(self.speech_key, self.speech_region) if self.speech_key else None
        
        print(f"✅ Recipe generation: {'Available' if self.recipe_generator else 'Disabled'}")
        print(f"✅ Voice guidance: {'Available' if self.voice_agent else 'Disabled'}")
        
        self._setup_user()
    
    def _setup_user(self):
        """Setup user account."""
        username = input("Enter your username: ").strip()
        if not username:
            username = "Chef"
        
        self.user_id = self.db.add_user(username)
        print(f"Welcome, {username}! 👋")
    
    def main_menu(self):
        """Main application menu."""
        while True:
            print("\n" + "="*60)
            print("🍳 SU-CHEF - Your AI Cooking Assistant")
            print("="*60)
            print("1. Create new recipe")
            print("2. View saved recipes")
            print("3. Search recipes")
            print("4. Load recipe from file")
            print("5. Exit")
            
            choice = input("\nChoose option (1-5): ").strip()
            
            if choice == "1":
                self._create_recipe_workflow()
            elif choice == "2":
                self._view_recipes_workflow()
            elif choice == "3":
                self._search_recipes_workflow()
            elif choice == "4":
                self._load_file_workflow()
            elif choice == "5":
                print("Happy cooking! 👨‍🍳")
                break
            else:
                print("Please enter a valid option (1-5)")
    
    def _create_recipe_workflow(self):
        """Handle recipe creation workflow."""
        print("\n--- Create New Recipe ---")
        
        if self.recipe_generator:
            print("1. Generate with AI")
            print("2. Enter manually")
            choice = input("Choose (1-2): ").strip()
            
            if choice == "1":
                self._generate_ai_recipe()
                return
        
        self._create_manual_recipe()
    
    def _generate_ai_recipe(self):
        """Generate recipe using AI."""
        print("\n--- AI Recipe Generation ---")
        
        # Get parameters
        meal_types = {"1": "breakfast", "2": "lunch", "3": "dinner", "4": "snack"}
        print("Meal Type: 1) Breakfast 2) Lunch 3) Dinner 4) Snack")
        meal_choice = input("Choose (1-4): ").strip()
        meal_type = meal_types.get(meal_choice, "dinner")
        
        cooking_time = self._get_positive_integer("Cooking time (minutes): ", 30)
        
        skill_levels = {"1": "beginner", "2": "intermediate", "3": "advanced"}
        print("Skill Level: 1) Beginner 2) Intermediate 3) Advanced")
        skill_choice = input("Choose (1-3): ").strip()
        skill_level = skill_levels.get(skill_choice, "intermediate")
        
        dietary = input("Dietary restrictions (optional): ").strip() or None
        
        ingredients_input = input("Available ingredients (comma-separated, optional): ").strip()
        available_ingredients = [i.strip() for i in ingredients_input.split(",")] if ingredients_input else None
        
        print("\n🤖 Generating recipe...")
        recipe_text = self.recipe_generator.generate_recipe(
            meal_type, cooking_time, skill_level, dietary, available_ingredients
        )
        
        if recipe_text:
            print("\n" + "="*50)
            print("GENERATED RECIPE:")
            print(f"="*50)
            print(recipe_text)
            
            save = input("\nSave this recipe? (y/n): ").strip().lower()
            if save == 'y':
                recipe_data = self.recipe_generator.parse_recipe(
                    recipe_text, meal_type, cooking_time, skill_level, dietary
                )
                if recipe_data:
                    recipe_id = self.db.save_recipe(recipe_data, self.user_id)
                    print(f"✅ Recipe saved with ID: {recipe_id}")
                    self.current_recipe_id = recipe_id
                    self._recipe_action_menu()
        else:
            print("❌ Failed to generate recipe")
    
    def _create_manual_recipe(self):
        """Create recipe manually."""
        print("\n--- Manual Recipe Entry ---")
        
        name = input("Recipe name: ").strip()
        if not name:
            print("Recipe name is required!")
            return
        
        print("Enter ingredients (one per line, empty line to finish):")
        ingredients = []
        while True:
            ingredient = input("- ").strip()
            if not ingredient:
                break
            ingredients.append(ingredient)
        
        if not ingredients:
            print("At least one ingredient is required!")
            return
        
        print("Enter cooking steps (one per line, empty line to finish):")
        steps = []
        step_num = 1
        while True:
            step = input(f"{step_num}. ").strip()
            if not step:
                break
            steps.append(step)
            step_num += 1
        
        if not steps:
            print("At least one step is required!")
            return
        
        # Optional metadata
        meal_type = input("Meal type (optional): ").strip() or "main"
        cooking_time = self._get_positive_integer("Cooking time in minutes (optional): ", 0)
        skill_level = input("Skill level (optional): ").strip() or "intermediate"
        
        recipe_data = {
            'name': name,
            'meal_type': meal_type,
            'cooking_time': cooking_time,
            'skill_level': skill_level,
            'dietary_restrictions': None,
            'ingredients': ingredients,
            'steps': steps
        }
        
        recipe_id = self.db.save_recipe(recipe_data, self.user_id)
        print(f"✅ Recipe '{name}' saved with ID: {recipe_id}")
        self.current_recipe_id = recipe_id
        self._recipe_action_menu()
    
    def _view_recipes_workflow(self):
        """View user's saved recipes."""
        print("\n--- Your Recipes ---")
        print("1. All recipes")
        print("2. Cooked recipes")
        print("3. Liked recipes")
        
        choice = input("Choose (1-3): ").strip()
        search_types = {"1": "all", "2": "cooked", "3": "liked"}
        search_type = search_types.get(choice, "all")
        
        recipes = self.db.get_user_recipes(self.user_id, search_type)
        
        if not recipes:
            print("No recipes found!")
            return
        
        print(f"\nFound {len(recipes)} recipe(s):")
        for i, (recipe_id, name, cooking_time, skill_level, created_at) in enumerate(recipes, 1):
            print(f"{i}. {name} ({cooking_time}min, {skill_level}) - {created_at[:10]}")
        
        try:
            choice = int(input(f"\nSelect recipe (1-{len(recipes)}) or 0 to go back: "))
            if choice == 0:
                return
            if 1 <= choice <= len(recipes):
                self.current_recipe_id = recipes[choice-1][0]
                self._show_recipe_details()
                self._recipe_action_menu()
        except ValueError:
            print("Please enter a valid number")
    
    def _search_recipes_workflow(self):
        """Search recipes by name."""
        query = input("Enter recipe name to search: ").strip()
        if not query:
            return
        
        recipes = self.db.search_recipes_by_name(query)
        
        if not recipes:
            print("No recipes found!")
            return
        
        print(f"\nFound {len(recipes)} recipe(s):")
        for i, (recipe_id, name, cooking_time, skill_level, created_at) in enumerate(recipes, 1):
            print(f"{i}. {name} ({cooking_time}min, {skill_level}) - {created_at[:10]}")
        
        try:
            choice = int(input(f"\nSelect recipe (1-{len(recipes)}) or 0 to go back: "))
            if choice == 0:
                return
            if 1 <= choice <= len(recipes):
                self.current_recipe_id = recipes[choice-1][0]
                self._show_recipe_details()
                self._recipe_action_menu()
        except ValueError:
            print("Please enter a valid number")
    
    def _load_file_workflow(self):
        """Load recipe from JSON file."""
        filename = input("Enter filename (or press Enter for 'recipe.json'): ").strip()
        if not filename:
            filename = "recipe.json"
        
        try:
            with open(filename, 'r') as f:
                recipe_data = json.load(f)
            
            print(f"✅ Loaded recipe: {recipe_data.get('name', 'Unknown')}")
            
            if self.voice_agent:
                self.voice_agent.load_recipe(recipe_data)
                start = input("Start voice guidance now? (y/n): ").strip().lower()
                if start == 'y':
                    success = self.voice_agent.run_voice_guidance()
                    if success and not self.voice_agent.is_interrupted:
                        self._mark_recipe_completed()
        
        except FileNotFoundError:
            print(f"❌ File '{filename}' not found")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in file '{filename}'")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
    
    def _show_recipe_details(self):
        """Show detailed recipe information."""
        if not self.current_recipe_id:
            return
        
        recipe = self.db.get_recipe_details(self.current_recipe_id)
        if not recipe:
            print("Recipe not found!")
            return
        
        print(f"\n{'='*50}")
        print(f"🍳 {recipe['name']}")
        print(f"{'='*50}")
        print(f"Meal Type: {recipe['meal_type']}")
        print(f"Cooking Time: {recipe['cooking_time']} minutes")
        print(f"Skill Level: {recipe['skill_level']}")
        if recipe['dietary_restrictions']:
            print(f"Dietary: {recipe['dietary_restrictions']}")
        
        print("\n📋 INGREDIENTS:")
        for ingredient in recipe['ingredients']:
            print(f"  • {ingredient}")
        
        print("\n👨‍🍳 STEPS:")
        for i, step in enumerate(recipe['steps'], 1):
            print(f"  {i}. {step}")
    
    def _recipe_action_menu(self):
        """Menu for actions after selecting a recipe."""
        while True:
            print("\n" + "-"*40)
            print("What would you like to do?")
            print("-"*40)
            print("1. Start voice guidance")
            print("2. View recipe details")
            print("3. Back to main menu")
            print("4. Select different recipe")
            
            choice = input("Choose (1-4): ").strip()
            
            if choice == "1":
                self._start_voice_guidance()
                break
            elif choice == "2":
                self._show_recipe_details()
                input("\nPress Enter to continue...")
            elif choice == "3":
                break
            elif choice == "4":
                self._view_recipes_workflow()
                break
            else:
                print("Please enter a valid option (1-4)")
    
    def _start_voice_guidance(self):
        """Start voice guidance for current recipe."""
        if not self.voice_agent:
            print("❌ Voice guidance not available!")
            print("   Requires Azure Speech Services API key in .env file")
            print("   Set SPEECH_KEY and SPEECH_REGION variables")
            return
        
        if not SPEECH_AVAILABLE:
            print("❌ Voice guidance not available!")
            print("   Install required package: pip install azure-cognitiveservices-speech")
            return
        
        if not self.current_recipe_id:
            print("❌ No recipe selected!")
            return
        
        recipe = self.db.get_recipe_details(self.current_recipe_id)
        if not recipe:
            print("❌ Recipe not found!")
            return
        
        print("\n🎤 Starting voice guidance...")
        print("💡 Make sure your microphone is working and speak clearly")
        self.voice_agent.load_recipe(recipe)
        success = self.voice_agent.run_voice_guidance()
        
        if success and not self.voice_agent.is_interrupted:
            self._mark_recipe_completed()
    
    def _mark_recipe_completed(self):
        """Mark recipe as completed and get feedback."""
        cooked = input("\nMark this recipe as cooked? (y/n): ").strip().lower() == 'y'
        if cooked:
            liked = input("Did you like it? (y/n): ").strip().lower() == 'y'
            self.db.mark_recipe_cooked(self.user_id, self.current_recipe_id, liked)
            print("✅ Recipe marked as cooked!")
    
    def _get_positive_integer(self, prompt: str, default: int = 0) -> int:
        """Get positive integer input with default."""
        while True:
            try:
                value = input(prompt).strip()
                if not value:
                    return default
                value = int(value)
                if value >= 0:
                    return value
                else:
                    print("Please enter a positive number")
            except ValueError:
                print("Please enter a valid number")
    
    def cleanup(self):
        """Cleanup resources."""
        self.db.close()

def main():
    """Main entry point."""
    chef = None
    try:
        chef = SuChef()
        chef.main_menu()
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if chef:
            chef.cleanup()

if __name__ == "__main__":
    main() 