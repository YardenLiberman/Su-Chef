from database import RecipeDatabase
import json
from datetime import datetime
from openai import OpenAI

def get_recipe_from_openai(prompt, api_key):
    """
    Send recipe prompt to OpenAI and get response
    """
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",  # Using an older, potentially cheaper model
            messages=[
                {"role": "system", "content": "You are a helpful cooking assistant that provides recipes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting recipe from OpenAI: {str(e)}")
        return None

def search_recipes(db, user_id=None):
    """Search recipes by name or user history"""
    print("\nSearch Options:")
    print("1. Search by recipe name")
    print("2. View cooked recipes")
    print("3. View liked recipes")
    print("4. Back to main menu")
    
    choice = input("Choose search option (1-4): ")
    
    if choice == "1":
        query = input("Enter recipe name to search: ")
        results = db.search_recipes(query=query, search_type='name')
    elif choice == "2":
        results = db.search_recipes(user_id=user_id, search_type='cooked')
    elif choice == "3":
        results = db.search_recipes(user_id=user_id, search_type='liked')
    else:
        return None
    
    if not results:
        print("No recipes found.")
        return None
    
    print("\nFound Recipes:")
    for i, recipe in enumerate(results, 1):
        print(f"{i}. {recipe[1]} (Steps: {recipe[-1]})")
    
    if len(results) > 1:
        recipe_choice = input("\nEnter recipe number to view details (or press Enter to go back): ")
        if recipe_choice.isdigit() and 1 <= int(recipe_choice) <= len(results):
            return results[int(recipe_choice)-1][0]  # Return recipe_id
    elif len(results) == 1:
        view_choice = input("\nView this recipe? (y/n): ")
        if view_choice.lower() == 'y':
            return results[0][0]  # Return recipe_id
    
    return None

def view_recipe(db, recipe_id, user_id):
    """View recipe details and steps"""
    recipe_data = db.get_recipe_details(recipe_id)
    if not recipe_data:
        print("Recipe not found.")
        return
    
    recipe = recipe_data['recipe']
    steps = recipe_data['steps']
    
    print(f"\nRecipe: {recipe[1]}")
    print(f"Meal Type: {recipe[2]}")
    print(f"Cooking Time: {recipe[3]} minutes")
    print(f"Skill Level: {recipe[4]}")
    print(f"Dietary Restrictions: {recipe[5]}")
    
    print("\nIngredients:")
    ingredients = json.loads(recipe[6])
    for ingredient in ingredients:
        print(f"- {ingredient}")
    
    print("\nSteps:")
    for step in steps:
        print(f"\n{step[0]}. {step[1]}")
        if step[2]:  # estimated_time
            print(f"   Estimated time: {step[2]} minutes")
        if step[3]:  # tips
            print(f"   Tips: {step[3]}")
    
    while True:
        print("\nOptions:")
        print("1. Mark as cooked")
        print("2. Mark as liked")
        print("3. Update step progress")
        print("4. Back to main menu")
        
        choice = input("Choose option (1-4): ")
        
        if choice == "1":
            db.mark_recipe_cooked(user_id, recipe_id, False)
            print("Recipe marked as cooked!")
        elif choice == "2":
            db.mark_recipe_cooked(user_id, recipe_id, True)
            print("Recipe marked as liked!")
        elif choice == "3":
            step_num = input("Enter completed step number: ")
            if step_num.isdigit():
                db.update_step_progress(user_id, recipe_id, int(step_num))
                print("Progress updated!")
        else:
            break

def main():
    # Initialize database
    db = RecipeDatabase()
    
    # Get user identification
    username = input("Please enter your username: ").strip()
    user_id = db.add_user(username)
    
    while True:
        print("\nMain Menu:")
        print("1. Generate new recipe")
        print("2. Search recipes")
        print("3. Exit")
        
        choice = input("Choose option (1-3): ")
        
        if choice == "1":
            # Get user input for recipe parameters
            meal_type = input("Enter meal type (breakfast/lunch/dinner/snack): ")
            cooking_time = input("Enter maximum cooking time in minutes: ")
            skill_level = input("Enter cooking skill level (beginner/intermediate/advanced): ")
            
            # Get dietary restrictions
            print("\nDietary restrictions options:")
            print("1. Vegetarian")
            print("2. Vegan") 
            print("3. Allergy (specify)")
            print("4. Kosher")
            print("5. Sugar-free")
            print("6. None")
            dietary_choice = input("Choose dietary restriction (enter number): ")
            
            dietary_restrictions = None
            if dietary_choice == "3":
                dietary_restrictions = input("Please specify food allergy: ")
            else:
                dietary_restrictions = {
                    "1": "vegetarian",
                    "2": "vegan", 
                    "4": "kosher",
                    "5": "sugar-free",
                    "6": None
                }.get(dietary_choice)
            
            # Make available ingredients optional
            ingredients_response = input("Do you want to specify available ingredients? (yes/no): ").lower()
            available_ingredients = []
            if ingredients_response == "yes":
                available_ingredients = input("Enter available ingredients (comma-separated): ").split(",")
                available_ingredients = [ingredient.strip() for ingredient in available_ingredients]
            
            # Build prompt for GPT
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
Recipe Name:
Cooking Time: 
Ingredients:
Instructions:
"""
            
            # Get API key securely
            api_key = input("Please enter your OpenAI API key: ").strip()
            if not api_key:
                print("Error: API key is required to generate recipes")
                continue
            
            # Get recipe from OpenAI
            recipe = get_recipe_from_openai(prompt, api_key)
            
            if recipe:
                # Process and save recipe
                recipe_data = process_recipe(recipe, meal_type, cooking_time, skill_level, dietary_restrictions)
                recipe_id = db.save_recipe(recipe_data, user_id)
                print(f"\nRecipe saved with ID: {recipe_id}")
                
                # View the recipe
                view_recipe(db, recipe_id, user_id)
            else:
                print("\nNo recipe was generated")
        
        elif choice == "2":
            recipe_id = search_recipes(db, user_id)
            if recipe_id:
                view_recipe(db, recipe_id, user_id)
        
        elif choice == "3":
            break
    
    db.close()

def process_recipe(recipe_text, meal_type, cooking_time, skill_level, dietary_restrictions):
    """Process the recipe text into structured data"""
    lines = recipe_text.split('\n')
    recipe_data = {
        'name': '',
        'meal_type': meal_type,
        'cooking_time': int(cooking_time),
        'skill_level': skill_level,
        'dietary_restrictions': dietary_restrictions,
        'ingredients': [],
        'instructions': []
    }
    
    current_section = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if ':' in line:
            section = line.split(':', 1)[0].lower().strip()
            content = line.split(':', 1)[1].strip()
            
            if 'recipe name' in section:
                recipe_data['name'] = content
            elif 'ingredients' in section:
                current_section = 'ingredients'
                if content:
                    recipe_data['ingredients'].append(content)
            elif 'instructions' in section:
                current_section = 'instructions'
                if content:
                    recipe_data['instructions'].append(content)
            continue
        
        if current_section == 'ingredients' and line:
            recipe_data['ingredients'].append(line.lstrip('- '))
        elif current_section == 'instructions' and line:
            if line[0].isdigit() or line.startswith('-') or line.startswith('•'):
                recipe_data['instructions'].append(line.lstrip('0123456789.- •'))
    
    return recipe_data

if __name__ == "__main__":
    main()

  