#!/usr/bin/env python3
"""
Test recipe steps loading directly
"""

from core.services import RecipeService, CookingService

def test_recipe_steps():
    print("🧪 Testing Recipe Steps Loading")
    print("=" * 50)
    
    # 1. Generate recipe
    recipe_service = RecipeService()
    result = recipe_service.generate({
        'meal_type': 'dinner',
        'time_limit': 20,
        'skill': 'beginner',
        'diet': None,
        'available': []
    })
    
    if not result or not result.get('success'):
        print("❌ Recipe generation failed")
        return
    
    recipe = result['recipe']
    print(f"✅ Generated recipe: {recipe['name']}")
    print(f"   Instructions: {len(recipe['instructions'])}")
    for i, step in enumerate(recipe['instructions']):
        print(f"   {i+1}. {step}")
    
    # 2. Start cooking service
    cooking_service = CookingService()
    success = cooking_service.start(recipe)
    
    if success and cooking_service.agent:
        print(f"\n✅ Cooking service started")
        print(f"   Recipe steps loaded: {len(cooking_service.agent.recipe_steps)}")
        
        # Show what the agent actually loaded
        for i, step in enumerate(cooking_service.agent.recipe_steps):
            if isinstance(step, dict):
                print(f"   Agent step {i+1}: {step['text']}")
            else:
                print(f"   Agent step {i+1}: {step}")
        
        # Test session start
        session_started = cooking_service.agent.start_session()
        print(f"   Session started: {session_started}")
        
        if session_started:
            print(f"   Current step: {cooking_service.agent.current_step}")
            print(f"   Recipe name: {cooking_service.agent.recipe_name}")
            
            # Test speaking current step
            cooking_service.agent.speak_current_step()
            
    else:
        print("❌ Failed to start cooking service")

if __name__ == "__main__":
    test_recipe_steps()
