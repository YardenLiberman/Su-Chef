import json
import os
from typing import Dict, List, Optional, Any

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