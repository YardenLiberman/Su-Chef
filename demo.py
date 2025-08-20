#!/usr/bin/env python3
"""
Su-Chef Demo - Shows basic functionality without requiring API keys
Perfect for testing the interface and understanding how the app works
"""

import json
import os
from typing import Dict, List, Any

def display_menu(title: str, options: List[str], width: int = 60) -> None:
    """Display a formatted menu with title and options."""
    print("\n" + "="*width)
    print(title.center(width))
    print("="*width)
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")

def get_numbered_choice(prompt: str, options: Dict[str, str], max_attempts: int = 3):
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

def show_demo_recipe():
    """Show a demo recipe to demonstrate the interface."""
    demo_recipe = {
        "name": "Demo Pasta Carbonara",
        "meal_type": "Dinner",
        "cooking_time": 25,
        "skill_level": "Intermediate",
        "dietary_restrictions": "None",
        "ingredients": [
            "400g spaghetti",
            "200g pancetta or guanciale",
            "4 large eggs",
            "100g Pecorino Romano cheese",
            "100g Parmigiano Reggiano",
            "Black pepper",
            "Salt"
        ],
        "steps": [
            "Bring a large pot of salted water to boil",
            "Cook spaghetti according to package directions",
            "Meanwhile, cook pancetta in a large skillet until crispy",
            "In a bowl, whisk eggs and grated cheeses",
            "Drain pasta, reserving 1 cup of pasta water",
            "Add hot pasta to skillet with pancetta",
            "Remove from heat and quickly stir in egg mixture",
            "Add pasta water as needed for creamy consistency",
            "Season with black pepper and serve immediately"
        ]
    }
    
    print(f"\n{'='*60}")
    print(f"DEMO RECIPE: {demo_recipe['name']}")
    print(f"{'='*60}")
    print(f"🍽️  Meal Type: {demo_recipe['meal_type']}")
    print(f"⏱️  Cooking Time: {demo_recipe['cooking_time']} minutes")
    print(f"👨‍🍳 Skill Level: {demo_recipe['skill_level']}")
    print(f"🚫 Dietary: {demo_recipe['dietary_restrictions']}")
    
    print(f"\n📋 Ingredients ({len(demo_recipe['ingredients'])}):")
    for ingredient in demo_recipe['ingredients']:
        print(f"   • {ingredient}")
    
    print(f"\n📝 Instructions ({len(demo_recipe['steps'])} steps):")
    for i, step in enumerate(demo_recipe['steps'], 1):
        print(f"   {i}. {step}")
    
    print(f"\n{'='*60}")
    print("This is a demo recipe to show the interface.")
    print("In the full version, you'd get AI-generated recipes!")
    print(f"{'='*60}")

def show_voice_demo():
    """Show what voice features would look like."""
    print(f"\n{'='*60}")
    print("VOICE GUIDANCE DEMO")
    print(f"{'='*60}")
    print("🎤 In the full version, you would hear:")
    print("   • Step-by-step cooking instructions")
    print("   • Voice commands like 'next', 'repeat', 'ingredients'")
    print("   • AI-powered cooking tips and answers")
    print("   • Natural language interaction")
    print("\n🔊 Voice Output:")
    print("   'Welcome to Su-Chef! I'll guide you through making Pasta Carbonara.'")
    print("   'Step 1: Bring a large pot of salted water to boil.'")
    print("   'Say 'next' when ready for the next step, or ask me anything!'")
    print(f"{'='*60}")

def show_ai_features():
    """Show what AI features would look like."""
    print(f"\n{'='*60}")
    print("AI FEATURES DEMO")
    print(f"{'='*60}")
    print("🤖 Recipe Generation:")
    print("   • AI creates recipes based on your preferences")
    print("   • Customizable cooking time, skill level, diet")
    print("   • Uses available ingredients")
    print("\n🧠 Smart Assistance:")
    print("   • Ask cooking questions during preparation")
    print("   • Get substitution suggestions")
    print("   • Troubleshooting help")
    print("   • Technique explanations")
    print(f"{'='*60}")

def main():
    """Main demo function."""
    print("🍳 Su-Chef Demo - AI Cooking Assistant")
    print("This demo shows the interface without requiring API keys")
    
    while True:
        print("\n" + "🍳"*20)
        display_menu("Su-Chef Demo Menu", [
            "View Demo Recipe",
            "See Voice Features", 
            "Explore AI Capabilities",
            "Exit Demo"
        ])
        print("🍳"*20)
        
        print("\n" + "="*60)
        print("Available Options:")
        print("1. View Demo Recipe - See a sample recipe with ingredients and steps")
        print("2. See Voice Features - Learn about voice-guided cooking")
        print("3. Explore AI Capabilities - Discover AI recipe generation features")
        print("4. Exit Demo - Close the demo and return to terminal")
        print("="*60)
        
        choice = get_numbered_choice(
            "\nChoose option (1-4): ",
            {"1": "recipe", "2": "voice", "3": "ai", "4": "exit"}
        )
        
        if choice == "recipe":
            show_demo_recipe()
        elif choice == "voice":
            show_voice_demo()
        elif choice == "ai":
            show_ai_features()
        elif choice == "exit":
            print("\n👋 Thanks for trying the Su-Chef demo!")
            print("To use the full version:")
            print("1. Set up your API keys (see SETUP.md)")
            print("2. Run: python su_chef.py")
            break
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
