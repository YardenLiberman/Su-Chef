#!/usr/bin/env python3
"""
Su-Chef CLI - Command Line Interface for AI Cooking Assistant
Generate recipes directly from the command line without interactive menus.
"""

import argparse
import os
import json
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any

from cooking_agent import CookingAgent
from recipe_generator import get_recipe_from_openai, process_recipe
from database import RecipeDatabase

def setup_environment():
    """Load environment variables and check API keys."""
    load_dotenv()
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("   Please set your OpenAI API key in .env file or environment.")
        return False
    
    return True

def generate_recipe_cli(meal_type: str, cooking_time: int, skill_level: str, 
                       dietary_restrictions: Optional[str] = None, 
                       ingredients: Optional[str] = None,
                       save: bool = False, output_file: Optional[str] = None) -> Optional[Dict]:
    """Generate a recipe using CLI parameters."""
    
    if not setup_environment():
        return None
    
    # Prepare recipe parameters
    recipe_params = {
        "meal_type": meal_type,
        "cooking_time": cooking_time,
        "skill_level": skill_level,
        "dietary_restrictions": dietary_restrictions or "none",
        "available_ingredients": ingredients or ""
    }
    
    print(f"🍳 Generating {meal_type} recipe...")
    print(f"   ⏱️  Cooking time: {cooking_time} minutes")
    print(f"   👨‍🍳 Skill level: {skill_level}")
    if dietary_restrictions:
        print(f"   🚫 Dietary: {dietary_restrictions}")
    if ingredients:
        print(f"   🥘 Using ingredients: {ingredients}")
    
    try:
        # Generate recipe using OpenAI
        raw_recipe = get_recipe_from_openai(recipe_params)
        if not raw_recipe:
            print("❌ Failed to generate recipe from OpenAI")
            return None
        
        # Process the recipe
        recipe = process_recipe(raw_recipe)
        if not recipe:
            print("❌ Failed to process recipe")
            return None
        
        # Display the recipe
        display_recipe(recipe)
        
        # Save to database if requested
        if save:
            db = RecipeDatabase()
            recipe_id = db.save_recipe(recipe)
            if recipe_id:
                print(f"✅ Recipe saved to database with ID: {recipe_id}")
            else:
                print("❌ Failed to save recipe to database")
            db.close()
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(recipe, f, indent=2, ensure_ascii=False)
                print(f"✅ Recipe saved to file: {output_file}")
            except Exception as e:
                print(f"❌ Failed to save to file: {e}")
        
        return recipe
        
    except Exception as e:
        print(f"❌ Error generating recipe: {e}")
        return None

def display_recipe(recipe: Dict[str, Any]) -> None:
    """Display a formatted recipe."""
    print(f"\n{'='*60}")
    print(f"🍽️  RECIPE: {recipe.get('name', 'Unknown Recipe')}")
    print(f"{'='*60}")
    
    # Recipe info
    print(f"🍽️  Meal Type: {recipe.get('meal_type', 'N/A')}")
    print(f"⏱️  Cooking Time: {recipe.get('cooking_time', 'N/A')} minutes")
    print(f"👨‍🍳 Skill Level: {recipe.get('skill_level', 'N/A')}")
    print(f"🚫 Dietary: {recipe.get('dietary_restrictions', 'None')}")
    
    # Ingredients
    ingredients = recipe.get('ingredients', [])
    if ingredients:
        print(f"\n📋 Ingredients ({len(ingredients)}):")
        for ingredient in ingredients:
            print(f"   • {ingredient}")
    
    # Instructions
    steps = recipe.get('steps', [])
    if steps:
        print(f"\n📝 Instructions ({len(steps)} steps):")
        for i, step in enumerate(steps, 1):
            print(f"   {i}. {step}")
    
    print(f"\n{'='*60}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Su-Chef CLI - Generate AI cooking recipes from command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick dinner recipe
  python su_chef_cli.py dinner --time 30 --skill intermediate

  # Vegetarian breakfast with specific ingredients
  python su_chef_cli.py breakfast --time 15 --skill beginner --diet vegetarian --ingredients "eggs, bread, cheese"

  # Save recipe to database and file
  python su_chef_cli.py lunch --time 45 --skill advanced --save --output my_recipe.json

Available meal types: breakfast, lunch, dinner, snack
Available skill levels: beginner, intermediate, advanced
        """
    )
    
    # Required arguments
    parser.add_argument('meal_type', 
                       choices=['breakfast', 'lunch', 'dinner', 'snack'],
                       help='Type of meal to generate')
    
    # Optional arguments
    parser.add_argument('--time', '-t', type=int, default=30,
                       help='Cooking time in minutes (default: 30)')
    
    parser.add_argument('--skill', '-s', 
                       choices=['beginner', 'intermediate', 'advanced'],
                       default='intermediate',
                       help='Cooking skill level (default: intermediate)')
    
    parser.add_argument('--diet', '-d', type=str,
                       help='Dietary restrictions (e.g., vegetarian, vegan, gluten-free)')
    
    parser.add_argument('--ingredients', '-i', type=str,
                       help='Available ingredients (comma-separated)')
    
    parser.add_argument('--save', action='store_true',
                       help='Save recipe to database')
    
    parser.add_argument('--output', '-o', type=str,
                       help='Save recipe to JSON file')
    
    args = parser.parse_args()
    
    # Generate the recipe
    recipe = generate_recipe_cli(
        meal_type=args.meal_type,
        cooking_time=args.time,
        skill_level=args.skill,
        dietary_restrictions=args.diet,
        ingredients=args.ingredients,
        save=args.save,
        output_file=args.output
    )
    
    if not recipe:
        print("❌ Failed to generate recipe")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
