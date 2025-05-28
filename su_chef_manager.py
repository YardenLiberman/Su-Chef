import os
from dotenv import load_dotenv
from cooking_agent import CookingAgent
from recipe_generator import get_recipe_from_openai, process_recipe
from database import RecipeDatabase

class SuChefManager:
    def __init__(self):
        print("Initializing Su-Chef Manager...")
        load_dotenv()
        
        # Initialize components
        self.db = RecipeDatabase()
        self.voice_agent = None
        self.user_id = None
        self.current_recipe_id = None
        
        # Check API keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.speech_key = os.getenv("SPEECH_KEY")
        
        print(f"OpenAI API available: {bool(self.openai_key)}")
        print(f"Speech services available: {bool(self.speech_key)}")
        
        print("Su-Chef Manager initialized!")
    
    def initialize_voice_agent(self):
        """Initialize the voice agent when needed."""
        if not self.voice_agent:
            try:
                self.voice_agent = CookingAgent()
                return True
            except Exception as e:
                print(f"Error initializing voice agent: {e}")
                return False
        return True
    
    def setup_user(self):
        """Get user identification."""
        username = input("Please enter your username: ").strip()
        self.user_id = self.db.add_user(username)
        print(f"Welcome, {username}!")
        return self.user_id
    
    def generate_recipe_workflow(self):
        """Handle the complete recipe generation workflow."""
        if not self.openai_key:
            print("OpenAI API key not found. Cannot generate recipes.")
            return None
        
        print("\n--- Generate New Recipe ---")
        
        # Get meal type with numbered options
        print("\nMeal Type:")
        print("1. Breakfast")
        print("2. Lunch") 
        print("3. Dinner")
        print("4. Snack")
        while True:
            meal_choice = input("Choose meal type (1-4): ").strip()
            meal_map = {"1": "breakfast", "2": "lunch", "3": "dinner", "4": "snack"}
            if meal_choice in meal_map:
                meal_type = meal_map[meal_choice]
                break
            else:
                print("Please enter a valid number (1-4)")
        
        # Validate cooking time input
        while True:
            cooking_time_input = input("\nEnter maximum cooking time in minutes: ").strip()
            if cooking_time_input.isdigit() and int(cooking_time_input) > 0:
                cooking_time = cooking_time_input
                break
            else:
                print("Please enter a valid number of minutes (e.g., 30)")
        
        # Get skill level with numbered options
        print("\nSkill Level:")
        print("1. Beginner")
        print("2. Intermediate")
        print("3. Advanced")
        while True:
            skill_choice = input("Choose skill level (1-3): ").strip()
            skill_map = {"1": "beginner", "2": "intermediate", "3": "advanced"}
            if skill_choice in skill_map:
                skill_level = skill_map[skill_choice]
                break
            else:
                print("Please enter a valid number (1-3)")
        
        # Dietary restrictions
        print("\nDietary restrictions:")
        print("1. Vegetarian  2. Vegan  3. Allergy  4. Kosher  5. Sugar-free  6. None")
        while True:
            dietary_choice = input("Choose (1-6): ").strip()
            if dietary_choice in ["1", "2", "3", "4", "5", "6"]:
                break
            else:
                print("Please enter a valid number (1-6)")
        
        dietary_restrictions = None
        if dietary_choice == "3":
            dietary_restrictions = input("Specify allergy: ").strip()
        else:
            dietary_map = {"1": "vegetarian", "2": "vegan", "4": "kosher", "5": "sugar-free"}
            dietary_restrictions = dietary_map.get(dietary_choice)
        
        # Available ingredients
        ingredients_input = input("\nAvailable ingredients (comma-separated, or press Enter to skip): ").strip()
        available_ingredients = [i.strip() for i in ingredients_input.split(",")] if ingredients_input else []
        
        # Build prompt
        prompt = f"""Please suggest a {meal_type} recipe that:
- Takes {cooking_time} minutes or less to prepare
- Is suitable for a {skill_level} cook
"""
        
        if available_ingredients:
            prompt += f"- Uses some of these available ingredients: {', '.join(available_ingredients)}\n"
        
        if dietary_restrictions:
            prompt += f"\nMust be {dietary_restrictions}"
        
        prompt += """

Please provide the recipe in this format:
Recipe Name: [name]
Cooking Time: [time in minutes]
Ingredients:
- [ingredient 1]
- [ingredient 2]
Instructions:
1. [step 1]
2. [step 2]
"""
        
        print("\nGenerating recipe...")
        recipe_text = get_recipe_from_openai(prompt, self.openai_key)
        
        if recipe_text:
            print("\n" + "="*50)
            print("GENERATED RECIPE:")
            print("="*50)
            print(recipe_text)
            
            save_choice = input("\nSave this recipe? (y/n): ").strip().lower()
            if save_choice == 'y':
                recipe_data = process_recipe(recipe_text, meal_type, cooking_time, skill_level, dietary_restrictions)
                recipe_id = self.db.save_recipe(recipe_data, self.user_id)
                print(f"Recipe saved with ID: {recipe_id}")
                self.current_recipe_id = recipe_id
                return recipe_id
        else:
            print("Failed to generate recipe.")
        
        return None
    
    def search_recipes_workflow(self):
        """Handle recipe search workflow."""
        print("\n--- Search Recipes ---")
        print("1. Search by name")
        print("2. View cooked recipes")
        print("3. View liked recipes")
        
        choice = input("Choose option (1-3): ").strip()
        
        results = []
        if choice == "1":
            query = input("Enter recipe name to search: ").strip()
            results = self.db.search_recipes(query=query, search_type='name')
        elif choice == "2":
            results = self.db.search_recipes(user_id=self.user_id, search_type='cooked')
        elif choice == "3":
            results = self.db.search_recipes(user_id=self.user_id, search_type='liked')
        
        if not results:
            print("No recipes found.")
            return None
        
        print("\nFound Recipes:")
        for i, recipe in enumerate(results, 1):
            print(f"{i}. {recipe[1]} ({recipe[3]} min, {recipe[4]})")
        
        if len(results) == 1:
            recipe_choice = "1"
        else:
            recipe_choice = input(f"\nSelect recipe (1-{len(results)}): ").strip()
        
        if recipe_choice.isdigit() and 1 <= int(recipe_choice) <= len(results):
            selected_recipe = results[int(recipe_choice)-1]
            recipe_id = selected_recipe[0]
            self.current_recipe_id = recipe_id
            print(f"Selected: {selected_recipe[1]}")
            return recipe_id
        
        return None
    
    def prepare_recipe_for_voice_guidance(self, recipe_id):
        """Prepare a recipe from database for voice guidance."""
        if not recipe_id:
            return False
        
        # Get recipe details from database
        recipe_data = self.db.get_recipe_details(recipe_id)
        if not recipe_data:
            print("Recipe not found in database.")
            return False
        
        recipe = recipe_data['recipe']
        steps = recipe_data['steps']
        
        # Create steps.json file for the voice agent
        steps_data = {
            'recipe_name': recipe[1],
            'steps': [
                {'step_number': step[0], 'text': step[1]}
                for step in steps
            ]
        }
        
        # Save to steps.json for voice agent
        import json
        with open('steps.json', 'w') as f:
            json.dump(steps_data, f, indent=4)
        
        print(f"Recipe '{recipe[1]}' prepared for voice guidance.")
        return True
    
    def start_voice_guidance_workflow(self):
        """Handle voice guidance workflow."""
        if not self.current_recipe_id:
            print("No recipe selected. Please generate or search for a recipe first.")
            return
        
        if not self.speech_key:
            print("Speech services not available. Voice guidance requires Azure Speech Services.")
            return
        
        # Prepare recipe for voice guidance
        if not self.prepare_recipe_for_voice_guidance(self.current_recipe_id):
            return
        
        # Initialize voice agent if needed
        if not self.initialize_voice_agent():
            print("Failed to initialize voice agent.")
            return
        
        print("\nStarting voice guidance...")
        try:
            # Load the recipe and start guidance
            if self.voice_agent.load_recipe():
                self.voice_agent.run()
                
                # Mark as cooked when completed
                if not self.voice_agent.is_interrupted:
                    mark_cooked = input("\nMark this recipe as cooked? (y/n): ").strip().lower()
                    if mark_cooked == 'y':
                        liked = input("Did you like it? (y/n): ").strip().lower() == 'y'
                        self.db.mark_recipe_cooked(self.user_id, self.current_recipe_id, liked)
                        print("Recipe marked as cooked!")
            else:
                print("Failed to load recipe for voice guidance.")
        except Exception as e:
            print(f"Error during voice guidance: {e}")
    
    def view_recipe_details(self, recipe_id):
        """Display detailed recipe information."""
        recipe_data = self.db.get_recipe_details(recipe_id)
        if not recipe_data:
            print("Recipe not found.")
            return
        
        recipe = recipe_data['recipe']
        steps = recipe_data['steps']
        
        print(f"\n{'='*50}")
        print(f"RECIPE: {recipe[1]}")
        print(f"{'='*50}")
        print(f"Meal Type: {recipe[2]}")
        print(f"Cooking Time: {recipe[3]} minutes")
        print(f"Skill Level: {recipe[4]}")
        print(f"Dietary Restrictions: {recipe[5] or 'None'}")
        
        print("\nIngredients:")
        import json
        ingredients = json.loads(recipe[6])
        for ingredient in ingredients:
            print(f"- {ingredient}")
        
        print("\nInstructions:")
        for step in steps:
            print(f"{step[0]}. {step[1]}")
    
    def main_menu(self):
        """Main interactive menu."""
        if not self.setup_user():
            return
        
        while True:
            print("\n" + "="*60)
            print("SU-CHEF MANAGER - Your AI Cooking Assistant")
            print("="*60)
            print("1. Create new recipe")
            print("2. Use saved recipe")
            print("3. Load recipe from file")
            print("4. View user statistics")
            print("5. Exit")
            
            choice = input("\nChoose option (1-5): ").strip()
            
            if choice == "1":
                # Generate new recipe
                recipe_id = self.generate_recipe_workflow()
                if recipe_id:
                    self.show_recipe_preview(recipe_id)
                    self.recipe_action_menu()
            
            elif choice == "2":
                # Search and select saved recipe
                recipe_id = self.search_recipes_workflow()
                if recipe_id:
                    self.show_recipe_preview(recipe_id)
                    self.recipe_action_menu()
            
            elif choice == "3":
                # Load recipe from file
                if self.initialize_voice_agent():
                    if self.voice_agent.load_recipe():
                        print(f"Recipe '{self.voice_agent.recipe_name}' loaded from file.")
                        self.file_recipe_action_menu()
                    else:
                        print("Failed to load recipe from file.")
                else:
                    print("Failed to initialize voice agent.")
            
            elif choice == "4":
                self.show_user_statistics()
            
            elif choice == "5":
                break
            
            else:
                print("Invalid choice. Please try again.")
        
        self.db.close()
        print("Thank you for using Su-Chef!")
    
    def show_recipe_preview(self, recipe_id):
        """Show a quick preview of the recipe before action menu."""
        recipe_data = self.db.get_recipe_details(recipe_id)
        if not recipe_data:
            return False
        
        recipe = recipe_data['recipe']
        steps = recipe_data['steps']
        
        print(f"\n{'='*50}")
        print(f"RECIPE PREVIEW: {recipe[1]}")
        print(f"{'='*50}")
        print(f"⏱️  Cooking Time: {recipe[3]} minutes")
        print(f"👨‍🍳 Skill Level: {recipe[4]}")
        print(f"🥗 Meal Type: {recipe[2]}")
        if recipe[5]:
            print(f"🚫 Dietary: {recipe[5]}")
        
        # Show first few ingredients
        import json
        ingredients = json.loads(recipe[6])
        print(f"\n📋 Ingredients ({len(ingredients)} total):")
        for i, ingredient in enumerate(ingredients[:3]):
            print(f"   • {ingredient}")
        if len(ingredients) > 3:
            print(f"   ... and {len(ingredients) - 3} more")
        
        # Show number of steps
        print(f"\n📝 Instructions: {len(steps)} steps")
        print(f"   1. {steps[0][1][:60]}{'...' if len(steps[0][1]) > 60 else ''}")
        if len(steps) > 1:
            print(f"   ... {len(steps) - 1} more steps")
        
        return True

    def recipe_action_menu(self):
        """Menu for actions after selecting a recipe from database."""
        while True:
            print("\n" + "-"*40)
            print("What would you like to do with this recipe?")
            print("-"*40)
            print("1. Start voice guidance")
            print("2. View full recipe details")
            print("3. Change to different recipe")
            print("4. Back to main menu")
            
            choice = input("\nChoose option (1-4): ").strip()
            
            if choice == "1":
                self.start_voice_guidance_workflow()
                break  # Return to main menu after guidance
            elif choice == "2":
                if self.current_recipe_id:
                    self.view_recipe_details(self.current_recipe_id)
                    input("\nPress Enter to continue...")
                continue  # Stay in action menu
            elif choice == "3":
                # Go back to recipe selection
                recipe_id = self.search_recipes_workflow()
                if recipe_id:
                    self.show_recipe_preview(recipe_id)
                    continue  # Stay in this menu with new recipe
                else:
                    break  # No recipe selected, go back to main menu
            elif choice == "4":
                break  # Back to main menu
            else:
                print("Invalid choice. Please try again.")
    
    def file_recipe_action_menu(self):
        """Menu for actions after loading a recipe from file."""
        while True:
            print("\n" + "-"*40)
            print("What would you like to do with this recipe?")
            print("-"*40)
            print("1. Start voice guidance")
            print("2. Load different recipe file")
            print("3. Back to main menu")
            
            choice = input("\nChoose option (1-3): ").strip()
            
            if choice == "1":
                if self.voice_agent:
                    self.voice_agent.run()
                break  # Return to main menu after guidance
            elif choice == "2":
                # Load different file
                if self.voice_agent.load_recipe():
                    print(f"Recipe '{self.voice_agent.recipe_name}' loaded from file.")
                    continue  # Stay in this menu with new recipe
                else:
                    print("Failed to load recipe from file.")
                    break
            elif choice == "3":
                break  # Back to main menu
            else:
                print("Invalid choice. Please try again.")
    
    def show_user_statistics(self):
        """Show user cooking statistics."""
        print(f"\n--- User Statistics ---")
        
        # Get user history
        history = self.db.get_user_history(self.user_id)
        total_recipes = len(history)
        cooked_recipes = len([r for r in history if r[8]])  # r[8] is cooked column
        liked_recipes = len([r for r in history if r[9]])   # r[9] is liked column
        
        print(f"Total recipes generated/saved: {total_recipes}")
        print(f"Recipes cooked: {cooked_recipes}")
        print(f"Recipes liked: {liked_recipes}")
        
        if total_recipes > 0:
            print(f"Cooking completion rate: {(cooked_recipes/total_recipes)*100:.1f}%")
            if cooked_recipes > 0:
                print(f"Like rate: {(liked_recipes/cooked_recipes)*100:.1f}%")

def main():
    print("Starting Su-Chef Manager...")
    try:
        manager = SuChefManager()
        manager.main_menu()
    except Exception as e:
        print(f"Error starting Su-Chef Manager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 