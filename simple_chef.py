#!/usr/bin/env python3
"""
Simple Su-Chef - A simplified cooking assistant
All functionality in one file for easy understanding and maintenance.
"""

import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Try to import optional dependencies
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available - recipe generation disabled")

try:
    import azure.cognitiveservices.speech as speechsdk
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("Azure Speech not available - voice features disabled")

class SimpleSuChef:
    def __init__(self):
        print("🍳 Starting Simple Su-Chef...")
        load_dotenv()
        
        # Setup database
        self.setup_database()
        
        # Get user
        self.username = input("Enter your name: ").strip() or "Chef"
        print(f"Welcome, {self.username}! 👋")
        
        # Check what features are available
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.speech_key = os.getenv("SPEECH_KEY")
        
        print(f"✅ Recipe generation: {'Yes' if self.openai_key and OPENAI_AVAILABLE else 'No'}")
        print(f"✅ Voice guidance: {'Yes' if self.speech_key and SPEECH_AVAILABLE else 'No'}")
    
    def setup_database(self):
        """Create simple database for recipes."""
        self.conn = sqlite3.connect("simple_recipes.db")
        cursor = self.conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            steps TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        self.conn.commit()
    
    def main_menu(self):
        """Simple main menu."""
        while True:
            print("\n" + "="*40)
            print("🍳 SIMPLE SU-CHEF")
            print("="*40)
            print("1. Create new recipe")
            print("2. View saved recipes")
            print("3. Cook with voice guidance")
            print("4. Exit")
            
            choice = input("\nChoose (1-4): ").strip()
            
            if choice == "1":
                self.create_recipe()
            elif choice == "2":
                self.view_recipes()
            elif choice == "3":
                self.voice_cooking()
            elif choice == "4":
                print("Happy cooking! 👨‍🍳")
                break
            else:
                print("Please enter 1, 2, 3, or 4")
    
    def create_recipe(self):
        """Create a new recipe - either manually or with AI."""
        print("\n--- Create Recipe ---")
        
        if self.openai_key and OPENAI_AVAILABLE:
            print("1. Generate with AI")
            print("2. Enter manually")
            choice = input("Choose (1-2): ").strip()
            
            if choice == "1":
                self.generate_ai_recipe()
                return
        
        # Manual recipe entry
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
        
        # Save recipe
        self.save_recipe(name, ingredients, steps)
        print(f"✅ Recipe '{name}' saved!")
    
    def generate_ai_recipe(self):
        """Generate recipe using AI."""
        if not (self.openai_key and OPENAI_AVAILABLE):
            print("AI recipe generation not available!")
            return
        
        # Simple inputs
        meal_type = input("What type of meal? (breakfast/lunch/dinner/snack): ").strip() or "dinner"
        time_limit = input("Max cooking time in minutes (default 30): ").strip() or "30"
        dietary = input("Any dietary restrictions? (optional): ").strip()
        
        # Build prompt
        prompt = f"Create a simple {meal_type} recipe that takes {time_limit} minutes or less."
        if dietary:
            prompt += f" Must be {dietary}."
        
        prompt += """

Format your response exactly like this:
RECIPE NAME: [name]
INGREDIENTS:
- [ingredient 1]
- [ingredient 2]
STEPS:
1. [step 1]
2. [step 2]
"""
        
        print("🤖 Generating recipe...")
        try:
            client = openai.OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            recipe_text = response.choices[0].message.content.strip()
            print("\n" + "="*50)
            print(recipe_text)
            print("="*50)
            
            save = input("\nSave this recipe? (y/n): ").strip().lower()
            if save == 'y':
                self.parse_and_save_ai_recipe(recipe_text)
        
        except Exception as e:
            print(f"❌ Error generating recipe: {e}")
    
    def parse_and_save_ai_recipe(self, recipe_text):
        """Parse AI-generated recipe and save it."""
        lines = recipe_text.split('\n')
        name = ""
        ingredients = []
        steps = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("RECIPE NAME:"):
                name = line.replace("RECIPE NAME:", "").strip()
            elif line.startswith("INGREDIENTS:"):
                current_section = "ingredients"
            elif line.startswith("STEPS:"):
                current_section = "steps"
            elif line.startswith("-") and current_section == "ingredients":
                ingredients.append(line[1:].strip())
            elif line[0].isdigit() and current_section == "steps":
                # Remove step number
                step = line.split(".", 1)
                if len(step) > 1:
                    steps.append(step[1].strip())
        
        if name and ingredients and steps:
            self.save_recipe(name, ingredients, steps)
            print(f"✅ Recipe '{name}' saved!")
        else:
            print("❌ Could not parse recipe properly")
    
    def save_recipe(self, name, ingredients, steps):
        """Save recipe to database."""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO recipes (name, ingredients, steps)
        VALUES (?, ?, ?)
        ''', (name, json.dumps(ingredients), json.dumps(steps)))
        self.conn.commit()
    
    def view_recipes(self):
        """View all saved recipes."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM recipes ORDER BY created_at DESC")
        recipes = cursor.fetchall()
        
        if not recipes:
            print("\n📝 No recipes saved yet!")
            return
        
        print("\n--- Your Recipes ---")
        for i, (recipe_id, name, created_at) in enumerate(recipes, 1):
            print(f"{i}. {name} (saved {created_at[:10]})")
        
        try:
            choice = int(input(f"\nView recipe (1-{len(recipes)}) or 0 to go back: "))
            if choice == 0:
                return
            if 1 <= choice <= len(recipes):
                self.show_recipe_details(recipes[choice-1][0])
        except ValueError:
            print("Please enter a valid number")
    
    def show_recipe_details(self, recipe_id):
        """Show full recipe details."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, ingredients, steps FROM recipes WHERE id = ?", (recipe_id,))
        result = cursor.fetchone()
        
        if not result:
            print("Recipe not found!")
            return
        
        name, ingredients_json, steps_json = result
        ingredients = json.loads(ingredients_json)
        steps = json.loads(steps_json)
        
        print(f"\n{'='*50}")
        print(f"🍳 {name}")
        print(f"{'='*50}")
        
        print("\n📋 INGREDIENTS:")
        for ingredient in ingredients:
            print(f"  • {ingredient}")
        
        print("\n👨‍🍳 STEPS:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
        
        print("\nOptions:")
        print("1. Use for voice cooking")
        print("2. Back to recipes")
        
        choice = input("Choose (1-2): ").strip()
        if choice == "1":
            self.prepare_voice_cooking(name, ingredients, steps)
    
    def voice_cooking(self):
        """Start voice-guided cooking."""
        if not (self.speech_key and SPEECH_AVAILABLE):
            print("❌ Voice guidance not available!")
            print("Need Azure Speech Services API key")
            return
        
        # Check if we have a recipe ready
        if os.path.exists("current_recipe.json"):
            with open("current_recipe.json", "r") as f:
                recipe = json.load(f)
            print(f"🍳 Ready to cook: {recipe['name']}")
            self.start_voice_guidance(recipe)
        else:
            print("❌ No recipe prepared for cooking!")
            print("First select a recipe from 'View saved recipes'")
    
    def prepare_voice_cooking(self, name, ingredients, steps):
        """Prepare recipe for voice cooking."""
        recipe = {
            "name": name,
            "ingredients": ingredients,
            "steps": steps
        }
        
        with open("current_recipe.json", "w") as f:
            json.dump(recipe, f, indent=2)
        
        print(f"✅ Recipe '{name}' prepared for voice cooking!")
        
        if self.speech_key and SPEECH_AVAILABLE:
            start_now = input("Start voice cooking now? (y/n): ").strip().lower()
            if start_now == 'y':
                self.start_voice_guidance(recipe)
    
    def start_voice_guidance(self, recipe):
        """Simple voice guidance through recipe."""
        if not (self.speech_key and SPEECH_AVAILABLE):
            print("❌ Voice guidance not available!")
            return
        
        try:
            # Setup speech
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=os.getenv("SPEECH_REGION", "westeurope")
            )
            speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
            
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
            
            def speak(text):
                print(f"🔊 {text}")
                synthesizer.speak_text_async(text).get()
            
            def listen():
                print("🎤 Listening...")
                result = recognizer.recognize_once_async().get()
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    return result.text.strip().lower()
                return ""
            
            # Start cooking
            speak(f"Let's cook {recipe['name']}! Say 'ready' when you're ready to start.")
            
            while True:
                response = listen()
                if "ready" in response:
                    break
                elif "stop" in response or "quit" in response:
                    speak("Cooking cancelled. Goodbye!")
                    return
            
            # Read ingredients
            speak("Here are the ingredients you'll need:")
            for ingredient in recipe['ingredients']:
                speak(ingredient)
            
            speak("Say 'continue' when you have everything ready.")
            while True:
                response = listen()
                if "continue" in response or "ready" in response:
                    break
                elif "stop" in response:
                    return
            
            # Go through steps
            for i, step in enumerate(recipe['steps'], 1):
                speak(f"Step {i}: {step}")
                speak("Say 'next' when done, or 'repeat' to hear again.")
                
                while True:
                    response = listen()
                    if "next" in response:
                        break
                    elif "repeat" in response:
                        speak(f"Step {i}: {step}")
                    elif "stop" in response:
                        speak("Cooking stopped. Come back anytime!")
                        return
            
            speak("Congratulations! You've finished cooking. Enjoy your meal!")
            
        except Exception as e:
            print(f"❌ Voice guidance error: {e}")
    
    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    """Main entry point."""
    try:
        chef = SimpleSuChef()
        chef.main_menu()
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 