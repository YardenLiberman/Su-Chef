import os
from dotenv import load_dotenv
from typing import Optional

from cooking_agent import CookingAgent
from recipe_generator import get_recipe_from_openai, process_recipe
from database import RecipeDatabase
import utils
import config

class SuChefManager:
    """Main manager class that coordinates all Su-Chef components."""
    
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
        utils.display_menu("Meal Type", config.MEAL_TYPE_DISPLAY)
        meal_type = utils.get_numbered_choice(
            "Choose meal type (1-4): ", 
            config.MEAL_TYPE_OPTIONS
        )
        if not meal_type:
            return None
        
        # Get cooking time
        cooking_time = utils.validate_positive_integer(
            "\nEnter maximum cooking time in minutes: ",
            config.MIN_COOKING_TIME
        )
        
        # Get skill level
        utils.display_menu("Skill Level", config.SKILL_LEVEL_DISPLAY)
        skill_level = utils.get_numbered_choice(
            "Choose skill level (1-3): ",
            config.SKILL_LEVEL_OPTIONS
        )
        if not skill_level:
            return None
        
        # Get dietary restrictions
        utils.display_menu("Dietary Restrictions", config.DIETARY_RESTRICTION_DISPLAY)
        dietary_choice = utils.get_numbered_choice(
            "Choose (1-6): ",
            {str(i): str(i) for i in range(1, 7)}
        )
        if not dietary_choice:
            return None
        
        dietary_restrictions = config.DIETARY_RESTRICTION_OPTIONS[dietary_choice]
        if dietary_choice == "3":  # Allergy - need specific input
            dietary_restrictions = input("Specify allergy: ").strip()
        
        # Get available ingredients
        ingredients_input = input("\nAvailable ingredients (comma-separated, or press Enter to skip): ").strip()
        available_ingredients = utils.parse_ingredients_input(ingredients_input)
        
        # Generate recipe
        prompt = utils.build_recipe_prompt(
            meal_type, str(cooking_time), skill_level, 
            dietary_restrictions, available_ingredients
        )
        
        print("\nGenerating recipe...")
        recipe_text = get_recipe_from_openai(prompt, self.openai_key)
        
        if recipe_text:
            print(f"\n{config.SEPARATOR_CHAR*50}")
            print("GENERATED RECIPE:")
            print(f"{config.SEPARATOR_CHAR*50}")
            print(recipe_text)
            
            if utils.get_user_confirmation("\nSave this recipe?"):
                recipe_data = process_recipe(recipe_text, meal_type, str(cooking_time), skill_level, dietary_restrictions)
                recipe_id = self.db.save_recipe(recipe_data, self.user_id)
                print(f"Recipe saved with ID: {recipe_id}")
                self.current_recipe_id = recipe_id
                return recipe_id
        else:
            print("Failed to generate recipe.")
        
        return None
    
    def search_recipes_workflow(self) -> Optional[int]:
        """Handle recipe search workflow."""
        print("\n--- Search Recipes ---")
        utils.display_menu("Search Options", config.SEARCH_MENU_OPTIONS)
        
        choice = utils.get_numbered_choice(
            "Choose option (1-3): ",
            {"1": "name", "2": "cooked", "3": "liked"}
        )
        if not choice:
            return None
        
        # Get search results
        if choice == "name":
            query = input("Enter recipe name to search: ").strip()
            if not query:
                print("Search query cannot be empty.")
                return None
            results = self.db.search_recipes(query=query, search_type='name')
        else:
            results = self.db.search_recipes(user_id=self.user_id, search_type=choice)
        
        if not results:
            print("No recipes found.")
            return None
        
        # Display results
        print("\nFound Recipes:")
        for i, recipe in enumerate(results, 1):
            print(f"{i}. {recipe[1]} ({recipe[3]} min, {recipe[4]})")
        
        # Get user selection
        if len(results) == 1:
            selected_recipe = results[0]
        else:
            choice_options = {str(i): i-1 for i in range(1, len(results)+1)}
            choice_idx = utils.get_numbered_choice(
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
        if not self.current_recipe_id:
            print("No recipe selected. Please generate or search for a recipe first.")
            return
        
        if not self.speech_key:
            print("Speech services not available. Voice guidance requires Azure Speech Services.")
            return
        
        # Get recipe data and prepare for voice guidance
        recipe_data = self.db.get_recipe_details(self.current_recipe_id)
        if not recipe_data:
            print("Recipe not found.")
            return
        
        if not utils.save_recipe_for_voice_guidance(recipe_data, config.DEFAULT_STEPS_FILENAME):
            print("Failed to prepare recipe for voice guidance.")
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
                    if utils.get_user_confirmation("\nMark this recipe as cooked?"):
                        liked = utils.get_user_confirmation("Did you like it?")
                        self.db.mark_recipe_cooked(self.user_id, self.current_recipe_id, liked)
                        print("Recipe marked as cooked!")
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
        
        utils.display_recipe_preview(recipe_data, config.DEFAULT_PREVIEW_INGREDIENTS)
        return True
    
    def view_recipe_details(self, recipe_id: int) -> None:
        """Display detailed recipe information."""
        recipe_data = self.db.get_recipe_details(recipe_id)
        if not recipe_data:
            print("Recipe not found.")
            return
        
        utils.display_recipe_details(recipe_data)
    
    def show_user_statistics(self) -> None:
        """Show user cooking statistics."""
        print(f"\n{config.SUBSECTION_CHAR*20} User Statistics {config.SUBSECTION_CHAR*20}")
        history = self.db.get_user_history(self.user_id)
        stats = utils.format_user_statistics(history)
        print(stats)
    
    def recipe_action_menu(self) -> None:
        """Menu for actions after selecting a recipe from database."""
        while True:
            utils.display_menu("What would you like to do with this recipe?", 
                             config.RECIPE_ACTION_OPTIONS, 40)
            
            choice = utils.get_numbered_choice(
                "\nChoose option (1-4): ",
                {"1": "guidance", "2": "details", "3": "change", "4": "back"}
            )
            
            if choice == "guidance":
                self.start_voice_guidance_workflow()
                break  # Return to main menu after guidance
            elif choice == "details":
                if self.current_recipe_id:
                    self.view_recipe_details(self.current_recipe_id)
                    input("\nPress Enter to continue...")
                continue  # Stay in action menu
            elif choice == "change":
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
            utils.display_menu("What would you like to do with this recipe?",
                             config.FILE_RECIPE_ACTION_OPTIONS, 40)
            
            choice = utils.get_numbered_choice(
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
            utils.display_menu(f"{config.APP_NAME} - {config.APP_SUBTITLE}", 
                             config.MAIN_MENU_OPTIONS, config.DEFAULT_MENU_WIDTH)
            
            choice = utils.get_numbered_choice(
                "\nChoose option (1-5): ",
                {"1": "create", "2": "saved", "3": "file", "4": "stats", "5": "exit"}
            )
            
            if choice == "create":
                # Generate new recipe
                recipe_id = self.generate_recipe_workflow()
                if recipe_id:
                    self.show_recipe_preview(recipe_id)
                    self.recipe_action_menu()
            
            elif choice == "saved":
                # Search and select saved recipe
                recipe_id = self.search_recipes_workflow()
                if recipe_id:
                    self.show_recipe_preview(recipe_id)
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
            
            elif choice == "stats":
                self.show_user_statistics()
            
            elif choice == "exit":
                break
            
            else:
                print("Invalid choice. Please try again.")
        
        self.db.close()
        print("Thank you for using Su-Chef!")

def main():
    """Main entry point."""
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