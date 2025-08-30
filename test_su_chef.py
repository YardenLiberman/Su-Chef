#!/usr/bin/env python3
"""
Quick test to see if su_chef.py imports work now
"""

try:
    print("Testing imports...")
    from cooking_agent import CookingAgent
    print("✅ CookingAgent imported successfully")
    
    from recipe_generator import get_recipe_from_openai, process_recipe
    print("✅ Recipe generator imported successfully")
    
    from database import RecipeDatabase
    print("✅ Database imported successfully")
    
    print("✅ All imports successful - su_chef.py should work now!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    print(f"Error type: {type(e)}")
