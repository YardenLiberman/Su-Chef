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
    
    # Add compatibility fields
    recipe_data['ingredients_json'] = json.dumps(recipe_data['ingredients'])
    recipe_data['steps'] = recipe_data['instructions']  # Alias for compatibility
    
    return recipe_data

if __name__ == "__main__":
    # This file is now used as a module only
    # Main functionality moved to su_chef.py
    print("This module should be imported, not run directly.")
    print("Run 'python su_chef.py' instead.")

  