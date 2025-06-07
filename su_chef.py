#!/usr/bin/env python3
"""
Su-Chef - AI Cooking Assistant
Consolidated main application with recipe management and voice guidance.
"""

import os
import json
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any

from cooking_agent import CookingAgent
from recipe_generator import get_recipe_from_openai, process_recipe
from database import RecipeDatabase

# =============================================================================
# CONFIGURATION CONSTANTS (from config.py)
# =============================================================================

# Menu option mappings
MEAL_TYPE_OPTIONS = {
    "1": "breakfast",
    "2": "lunch", 
    "3": "dinner",
    "4": "snack"
}

SKILL_LEVEL_OPTIONS = {
    "1": "beginner",
    "2": "intermediate",
    "3": "advanced"
}

DIETARY_RESTRICTION_OPTIONS = {
    "1": "vegetarian",
    "2": "vegan",
    "3": "allergy",  # Special case - requires user input
    "4": "kosher",
    "5": "sugar-free",
    "6": None  # No restrictions
}

# Menu display texts
MEAL_TYPE_DISPLAY = [
    "Breakfast",
    "Lunch", 
    "Dinner",
    "Snack"
]

SKILL_LEVEL_DISPLAY = [
    "Beginner",
    "Intermediate",
    "Advanced"
]

DIETARY_RESTRICTION_DISPLAY = [
    "Vegetarian",
    "Vegan",
    "Allergy (specify)",
    "Kosher",
    "Sugar-free",
    "None"
]

# Main menu options
MAIN_MENU_OPTIONS = [
    "Create new recipe",
    "Use saved recipe", 
    "Load recipe from file",
    "Exit"
]

# Recipe action menu options
RECIPE_ACTION_OPTIONS = [
    "Start voice guidance",
    "View full recipe details",
    "Change to different recipe",
    "Back to main menu"
]

# File recipe action menu options
FILE_RECIPE_ACTION_OPTIONS = [
    "Start voice guidance",
    "Load different recipe file",
    "Back to main menu"
]

# Search menu options
SEARCH_MENU_OPTIONS = [
    "Search by name",
    "View cooked recipes",
    "View favorite recipes"
]

# Application constants
APP_NAME = "SU-CHEF"
APP_SUBTITLE = "Your AI Cooking Assistant"
DEFAULT_MENU_WIDTH = 60
DEFAULT_PREVIEW_INGREDIENTS = 3
DEFAULT_STEPS_FILENAME = "steps.json"

# Validation constants
MIN_COOKING_TIME = 1
MAX_MENU_ATTEMPTS = 3

# Display formatting
SEPARATOR_CHAR = "="
SUBSECTION_CHAR = "-"
PREVIEW_WIDTH = 50

# =============================================================================
# UTILITY FUNCTIONS (from utils.py)
# =============================================================================

def validate_positive_integer(prompt: str, min_value: int = 1) -> int:
    """Get and validate positive integer input from user."""
    while True:
        try:
            value = int(input(prompt).strip())
            if value >= min_value:
                return value
            else:
                print(f"Please enter a number >= {min_value}")
        except ValueError:
            print("Please enter a valid number")

def get_numbered_choice(prompt: str, options: Dict[str, str], max_attempts: int = 3) -> Optional[str]:
    """Get user choice from numbered options with validation."""
    attempts = 0
    while attempts < max_attempts:
        choice = input(prompt).strip()
        if choice in options:
            return options[choice]
        else:
            attempts += 1
            print(f"Please enter a valid number (1-{len(options)})")
            if attempts < max_attempts:
                print(f"Attempts remaining: {max_attempts - attempts}")
    return None

def display_menu(title: str, options: List[str], width: int = 60) -> None:
    """Display a formatted menu with title and options."""
    print("\n" + "="*width)
    print(title.center(width))
    print("="*width)
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")

def display_recipe_preview(recipe_data: Dict[str, Any], max_ingredients: int = 3) -> None:
    """Display a formatted recipe preview."""
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
    ingredients = json.loads(recipe[6])
    print(f"\n📋 Ingredients ({len(ingredients)} total):")
    for i, ingredient in enumerate(ingredients[:max_ingredients]):
        print(f"   • {ingredient}")
    if len(ingredients) > max_ingredients:
        print(f"   ... and {len(ingredients) - max_ingredients} more")
    
    # Show number of steps
    print(f"\n📝 Instructions: {len(steps)} steps")
    print(f"   1. {steps[0][1][:60]}{'...' if len(steps[0][1]) > 60 else ''}")
    if len(steps) > 1:
        print(f"   ... {len(steps) - 1} more steps")

def display_recipe_details(recipe_data: Dict[str, Any]) -> None:
    """Display complete recipe details."""
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
    ingredients = json.loads(recipe[6])
    for ingredient in ingredients:
        print(f"- {ingredient}")
    
    print("\nInstructions:")
    for step in steps:
        print(f"{step[0]}. {step[1]}")

def save_recipe_for_voice_guidance(recipe_data: Dict[str, Any], filename: str = 'steps.json') -> bool:
    """Save recipe in format suitable for voice guidance."""
    try:
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
        
        # Extract ingredients for voice agent
        ingredients = json.loads(recipe[6])
        steps_data['ingredients'] = ingredients
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(steps_data, f, indent=4)
        
        return True
    except Exception as e:
        print(f"Error saving recipe for voice guidance: {e}")
        return False

def get_user_confirmation(prompt: str, default: bool = False) -> bool:
    """Get yes/no confirmation from user."""
    suffix = " (Y/n): " if default else " (y/N): "
    while True:
        response = input(prompt + suffix).strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        elif response == '':
            return default
        else:
            print("Please enter 'y' for yes or 'n' for no")

def format_user_statistics(history: List[Any]) -> str:
    """Format user cooking statistics."""
    total_recipes = len(history)
    cooked_recipes = len([r for r in history if r[8]])  # r[8] is cooked column
    liked_recipes = len([r for r in history if r[9]])   # r[9] is liked column
    
    stats = f"Total recipes generated/saved: {total_recipes}\n"
    stats += f"Recipes cooked: {cooked_recipes}\n"
    stats += f"Recipes liked: {liked_recipes}\n"
    
    if total_recipes > 0:
        completion_rate = (cooked_recipes/total_recipes)*100
        stats += f"Cooking completion rate: {completion_rate:.1f}%\n"
        if cooked_recipes > 0:
            like_rate = (liked_recipes/cooked_recipes)*100
            stats += f"Like rate: {like_rate:.1f}%"
    
    return stats

def parse_ingredients_input(ingredients_input: str) -> List[str]:
    """Parse comma-separated ingredients input."""
    if not ingredients_input.strip():
        return []
    return [ingredient.strip() for ingredient in ingredients_input.split(",") if ingredient.strip()]

def build_recipe_prompt(meal_type: str, cooking_time: str, skill_level: str, 
                       dietary_restrictions: Optional[str] = None, 
                       available_ingredients: Optional[List[str]] = None) -> str:
    """Build a recipe generation prompt."""
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
    
    return prompt

class SuChef:
    """Main Su-Chef application class that coordinates all components."""
    
    def __init__(self):
        print("Initializing Su-Chef...")
        load_dotenv()
        
        # Initialize components
        self.db = RecipeDatabase()
        self.voice_agent = None
        self.user_id = None
        self.current_recipe_id = None
        self.temp_recipe_data = None
        
        # Check API keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.speech_key = os.getenv("SPEECH_KEY")
        
        print(f"OpenAI API available: {bool(self.openai_key)}")
        print(f"Speech services available: {bool(self.speech_key)}")
        print("Su-Chef initialized!")
    
    def initialize_voice_agent(self) -> bool:
        """Initialize the voice agent when needed."""
        if not self.voice_agent:
            try:
                self.voice_agent = CookingAgent()
                return True
            except Exception as e:
                print(f"Error initializing voice agent: {e}")
                return False
        return True
    
    def setup_user(self) -> bool:
        """Get user identification."""
        username = input("Please enter your username: ").strip()
        if not username:
            print("Username cannot be empty.")
            return False
        
        self.user_id = self.db.add_user(username)
        print(f"Welcome, {username}!")
        return True
    
    def generate_recipe_workflow(self) -> Optional[int]:
        """Handle the complete recipe generation workflow."""
        if not self.openai_key:
            print("OpenAI API key not found. Cannot generate recipes.")
            return None
        
        print("\n--- Generate New Recipe ---")
        
        # Get meal type
        display_menu("Meal Type", MEAL_TYPE_DISPLAY)
        meal_type = get_numbered_choice(
            "Choose meal type (1-4): ", 
            MEAL_TYPE_OPTIONS
        )
        if not meal_type:
            return None
        
        # Get cooking time
        cooking_time = validate_positive_integer(
            "\nEnter maximum cooking time in minutes: ",
            MIN_COOKING_TIME
        )
        
        # Get skill level
        display_menu("Skill Level", SKILL_LEVEL_DISPLAY)
        skill_level = get_numbered_choice(
            "Choose skill level (1-3): ",
            SKILL_LEVEL_OPTIONS
        )
        if not skill_level:
            return None
        
        # Get dietary restrictions
        display_menu("Dietary Restrictions", DIETARY_RESTRICTION_DISPLAY)
        dietary_choice = get_numbered_choice(
            "Choose (1-6): ",
            {str(i): str(i) for i in range(1, 7)}
        )
        if not dietary_choice:
            return None
        
        dietary_restrictions = DIETARY_RESTRICTION_OPTIONS[dietary_choice]
        if dietary_choice == "3":  # Allergy - need specific input
            dietary_restrictions = input("Specify allergy: ").strip()
        
        # Get available ingredients
        ingredients_input = input("\nAvailable ingredients (comma-separated, or press Enter to skip): ").strip()
        available_ingredients = parse_ingredients_input(ingredients_input)
        
        # Build base prompt for recipe generation
        base_prompt = build_recipe_prompt(
            meal_type, str(cooking_time), skill_level, 
            dietary_restrictions, available_ingredients
        )
        
        # Recipe generation loop - allow user to request different suggestions
        attempt_count = 0
        max_attempts = 10  # Reasonable limit to prevent infinite loops
        
        while attempt_count < max_attempts:
            attempt_count += 1
            
            # Modify prompt for subsequent attempts to get variety
            if attempt_count == 1:
                prompt = base_prompt
                print("\nGenerating recipe...")
            else:
                prompt = base_prompt + f"\n\nPlease provide a DIFFERENT recipe suggestion than previous attempts. Make it unique and creative while still meeting the requirements above."
                print(f"\nGenerating alternative recipe suggestion #{attempt_count}...")
            
            recipe_text = get_recipe_from_openai(prompt, self.openai_key)
            
            if recipe_text:
                print(f"\n{SEPARATOR_CHAR*50}")
                print("GENERATED RECIPE:")
                print(f"{SEPARATOR_CHAR*50}")
                print(recipe_text)
                
                # Ask user if they're satisfied with this recipe
                print(f"\n{SUBSECTION_CHAR*30}")
                print("Are you satisfied with this recipe?")
                display_menu("Recipe Options", [
                    "Yes, I like this recipe",
                    "No, generate a different recipe",
                    "Cancel and return to main menu"
                ], 40)
                
                choice = get_numbered_choice(
                    "Choose option (1-3): ",
                    {"1": "accept", "2": "different", "3": "cancel"}
                )
                
                if choice == "accept":
                    # Store recipe data temporarily for potential saving later
                    self.temp_recipe_data = {
                        'text': recipe_text,
                        'meal_type': meal_type,
                        'cooking_time': str(cooking_time),
                        'skill_level': skill_level,
                        'dietary_restrictions': dietary_restrictions
                    }
                    print(f"✅ Recipe accepted! Ready to proceed.")
                    return -1  # Special ID to indicate temporary recipe
                elif choice == "different":
                    if attempt_count >= max_attempts:
                        print(f"Maximum recipe generation attempts ({max_attempts}) reached.")
                        break
                    print("🔄 Generating a different recipe...")
                    continue  # Loop to generate another recipe
                elif choice == "cancel":
                    print("Recipe generation cancelled.")
                    return None
                else:
                    print("Invalid choice. Please try again.")
                    continue
            else:
                print("❌ Failed to generate recipe.")
                if attempt_count < max_attempts:
                    retry = get_user_confirmation("Would you like to try generating another recipe?")
                    if retry:
                        continue
                break
        
        if attempt_count >= max_attempts:
            print("Unable to generate a satisfactory recipe after multiple attempts.")
        
        return None
    
    def search_recipes_workflow(self) -> Optional[int]:
        """Handle recipe search workflow."""
        print("\n--- Use Saved Recipe ---")
        
        # First, ask user to choose between cooked and favorite recipes
        display_menu("Choose Recipe Type", ["Recipes you cooked", "Recipes you marked as favorite"])
        
        choice = get_numbered_choice(
            "Choose option (1-2): ",
            {"1": "cooked", "2": "liked"}
        )
        if not choice:
            return None
        
        # Get search results based on choice
        results = self.db.search_recipes(user_id=self.user_id, search_type=choice)
        
        if not results:
            recipe_type = "cooked" if choice == "cooked" else "favorite"
            print(f"No {recipe_type} recipes found.")
            return None
        
        # Display recipe names only
        print(f"\n{('Cooked' if choice == 'cooked' else 'Favorite')} Recipes:")
        for i, recipe in enumerate(results, 1):
            print(f"{i}. {recipe[1]}")
        
        # Get user selection
        if len(results) == 1:
            selected_recipe = results[0]
        else:
            choice_options = {str(i): i-1 for i in range(1, len(results)+1)}
            choice_idx = get_numbered_choice(
                f"\nSelect recipe (1-{len(results)}): ",
                choice_options
            )
            if choice_idx is None:
                return None
            selected_recipe = results[choice_idx]
        
        recipe_id = selected_recipe[0]
        self.current_recipe_id = recipe_id
        print(f"Selected: {selected_recipe[1]}")
        return recipe_id
    
    def start_voice_guidance_workflow(self) -> None:
        """Handle voice guidance workflow."""
        if not self.current_recipe_id and not self.temp_recipe_data:
            print("No recipe selected. Please generate or search for a recipe first.")
            return
        
        if not self.speech_key:
            print("Speech services not available. Voice guidance requires Azure Speech Services.")
            return
        
        # Handle temporary recipe (newly generated)
        if self.current_recipe_id == -1 and self.temp_recipe_data:
            # Process temporary recipe data for voice guidance
            recipe_data = process_recipe(
                self.temp_recipe_data['text'],
                self.temp_recipe_data['meal_type'],
                self.temp_recipe_data['cooking_time'],
                self.temp_recipe_data['skill_level'],
                self.temp_recipe_data['dietary_restrictions']
            )
            
            # Create a temporary recipe structure for voice guidance
            temp_recipe_structure = {
                'recipe': (None, recipe_data['name'], self.temp_recipe_data['meal_type'], 
                          int(self.temp_recipe_data['cooking_time']), self.temp_recipe_data['skill_level'],
                          self.temp_recipe_data['dietary_restrictions'], recipe_data['ingredients_json']),
                'steps': [(i+1, step) for i, step in enumerate(recipe_data['steps'])]
            }
            
            if not save_recipe_for_voice_guidance(temp_recipe_structure, DEFAULT_STEPS_FILENAME):
                print("Failed to prepare recipe for voice guidance.")
                return
        else:
            # Handle saved recipe
            recipe_data = self.db.get_recipe_details(self.current_recipe_id)
            if not recipe_data:
                print("Recipe not found.")
                return
            
            if not save_recipe_for_voice_guidance(recipe_data, DEFAULT_STEPS_FILENAME):
                print("Failed to prepare recipe for voice guidance.")
                return
        
        # Initialize voice agent if needed
        if not self.initialize_voice_agent():
            print("Failed to initialize voice agent.")
            return
        
        try:
            # Load the recipe and start guidance
            if self.voice_agent.load_recipe():
                self.voice_agent.run()
                
                # Recipe completion flow - check if completed successfully
                if hasattr(self.voice_agent, 'is_completed') and self.voice_agent.is_completed:
                    print("\n🎉 Recipe completed!")
                    
                    # Save recipe only if user marks it as cooked or favorite
                    if get_user_confirmation("Mark this recipe as cooked?"):
                        # Save recipe if it's temporary
                        if self.current_recipe_id == -1 and self.temp_recipe_data:
                            recipe_data = process_recipe(
                                self.temp_recipe_data['text'],
                                self.temp_recipe_data['meal_type'],
                                self.temp_recipe_data['cooking_time'],
                                self.temp_recipe_data['skill_level'],
                                self.temp_recipe_data['dietary_restrictions']
                            )
                            self.current_recipe_id = self.db.save_recipe(recipe_data, self.user_id)
                            self.temp_recipe_data = None
                        
                        self.db.mark_recipe_cooked(self.user_id, self.current_recipe_id, False)
                        print("✅ Recipe marked as cooked!")
                        
                        if get_user_confirmation("Mark this recipe as favorite?"):
                            self.db.mark_recipe_cooked(self.user_id, self.current_recipe_id, True)
                            print("⭐ Recipe marked as favorite!")
                elif self.voice_agent.is_interrupted:
                    print("\n⏹️ Cooking session ended early.")
            else:
                print("Failed to load recipe for voice guidance.")
        except Exception as e:
            print(f"Error during voice guidance: {e}")
    
    def show_recipe_preview(self, recipe_id: int) -> bool:
        """Show a quick preview of the recipe."""
        recipe_data = self.db.get_recipe_details(recipe_id)
        if not recipe_data:
            print("Recipe not found.")
            return False
        
        display_recipe_preview(recipe_data, DEFAULT_PREVIEW_INGREDIENTS)
        return True
    
    def view_recipe_details(self, recipe_id: int) -> None:
        """Display detailed recipe information."""
        recipe_data = self.db.get_recipe_details(recipe_id)
        if not recipe_data:
            print("Recipe not found.")
            return
        
        display_recipe_details(recipe_data)
    
    def show_user_statistics(self) -> None:
        """Show user cooking statistics."""
        print(f"\n{SUBSECTION_CHAR*20} User Statistics {SUBSECTION_CHAR*20}")
        history = self.db.get_user_history(self.user_id)
        stats = format_user_statistics(history)
        print(stats)
    
    def recipe_action_menu(self) -> None:
        """Menu for actions after selecting a recipe from database."""
        while True:
            # Show different options for temporary vs saved recipes
            if self.current_recipe_id == -1:
                display_menu("What would you like to do with this recipe?", 
                           ["Start voice guidance", "Back to main menu"], 40)
                choice = get_numbered_choice(
                    "\nChoose option (1-2): ",
                    {"1": "guidance", "2": "back"}
                )
            else:
                display_menu("What would you like to do with this recipe?", 
                           RECIPE_ACTION_OPTIONS, 40)
                choice = get_numbered_choice(
                    "\nChoose option (1-4): ",
                    {"1": "guidance", "2": "details", "3": "change", "4": "back"}
                )
            
            if choice == "guidance":
                self.start_voice_guidance_workflow()
                break  # Return to main menu after guidance
            elif choice == "details" and self.current_recipe_id != -1:
                if self.current_recipe_id:
                    self.view_recipe_details(self.current_recipe_id)
                    input("\nPress Enter to continue...")
                continue  # Stay in action menu
            elif choice == "change" and self.current_recipe_id != -1:
                # Go back to recipe selection
                recipe_id = self.search_recipes_workflow()
                if recipe_id:
                    self.show_recipe_preview(recipe_id)
                    continue  # Stay in this menu with new recipe
                else:
                    break  # No recipe selected, go back to main menu
            elif choice == "back":
                break  # Back to main menu
            else:
                print("Invalid choice. Please try again.")
    
    def file_recipe_action_menu(self) -> None:
        """Menu for actions after loading a recipe from file."""
        while True:
            display_menu("What would you like to do with this recipe?",
                             FILE_RECIPE_ACTION_OPTIONS, 40)
            
            choice = get_numbered_choice(
                "\nChoose option (1-3): ",
                {"1": "guidance", "2": "load", "3": "back"}
            )
            
            if choice == "guidance":
                if self.voice_agent:
                    self.voice_agent.run()
                break  # Return to main menu after guidance
            elif choice == "load":
                # Load different file
                if self.voice_agent.load_recipe():
                    print(f"Recipe '{self.voice_agent.recipe_name}' loaded from file.")
                    continue  # Stay in this menu with new recipe
                else:
                    print("Failed to load recipe from file.")
                    break
            elif choice == "back":
                break  # Back to main menu
            else:
                print("Invalid choice. Please try again.")
    
    def main_menu(self) -> None:
        """Main interactive menu."""
        if not self.setup_user():
            return
        
        while True:
            display_menu(f"{APP_NAME} - {APP_SUBTITLE}", 
                             MAIN_MENU_OPTIONS, DEFAULT_MENU_WIDTH)
            
            choice = get_numbered_choice(
                "\nChoose option (1-4): ",
                {"1": "create", "2": "saved", "3": "file", "4": "exit"}
            )
            
            if choice == "create":
                # Generate new recipe
                recipe_id = self.generate_recipe_workflow()
                if recipe_id == -1:  # Temporary recipe
                    self.current_recipe_id = -1
                    self.recipe_action_menu()
                elif recipe_id:
                    self.show_recipe_preview(recipe_id)
                    self.recipe_action_menu()
            
            elif choice == "saved":
                # Search and select saved recipe
                recipe_id = self.search_recipes_workflow()
                if recipe_id:
                    self.recipe_action_menu()
            
            elif choice == "file":
                # Load recipe from file
                if self.initialize_voice_agent():
                    if self.voice_agent.load_recipe():
                        print(f"Recipe '{self.voice_agent.recipe_name}' loaded from file.")
                        self.file_recipe_action_menu()
                    else:
                        print("Failed to load recipe from file.")
                else:
                    print("Failed to initialize voice agent.")
            
            elif choice == "exit":
                break
            
            else:
                print("Invalid choice. Please try again.")
        
        self.db.close()
        print("Thank you for using Su-Chef!")

def main():
    """Main entry point."""
    try:
        app = SuChef()
        app.main_menu()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 