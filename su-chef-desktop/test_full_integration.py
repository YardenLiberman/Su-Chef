#!/usr/bin/env python3
"""
Test full integration: Recipe generation + Voice cooking
"""

from core.services import RecipeService, CookingService

def test_full_integration():
    print("🧪 Testing Full Integration: Recipe Generation + Voice")
    print("=" * 60)
    
    # 1. Generate a recipe
    print("1. Generating recipe...")
    recipe_service = RecipeService()
    result = recipe_service.generate({
        'meal_type': 'dinner',
        'time_limit': 30,
        'skill': 'beginner',
        'diet': None,
        'available': []
    })
    
    if not result or not result.get('success'):
        print("❌ Recipe generation failed")
        return
    
    recipe = result['recipe']
    print(f"✅ Generated recipe: {recipe['name']}")
    print(f"   Steps: {len(recipe['instructions'])}")
    
    # 2. Start cooking service
    print("\n2. Starting cooking service...")
    cooking_service = CookingService()
    success = cooking_service.start(recipe)
    
    if not success:
        print("❌ Failed to start cooking service")
        return
    
    print("✅ Cooking service started")
    
    # 3. Start voice session
    print("\n3. Starting voice session...")
    if cooking_service.agent:
        session_started = cooking_service.agent.start_session()
        print(f"✅ Voice session started: {session_started}")
        
        if session_started:
            print(f"   Recipe loaded: {cooking_service.agent.recipe_name}")
            print(f"   Total steps: {len(cooking_service.agent.recipe_steps)}")
            
            # 4. Test voice commands
            print("\n4. Testing voice commands...")
            
            print("   🔊 Speaking first step...")
            cooking_service.agent.speak_current_step()
            
            print("   ⏭️ Testing 'next' command...")
            cooking_service.agent.send_command("next")
            
            print("   🔁 Testing 'repeat' command...")
            cooking_service.agent.send_command("repeat")
            
            print("   📋 Testing 'ingredients' command...")
            cooking_service.agent.send_command("ingredients")
            
            print("   🛑 Testing 'stop' command...")
            cooking_service.agent.send_command("stop")
            
            print("\n✅ Full integration test completed!")
            print("🎉 If you heard voice output, the integration is working!")
        else:
            print("❌ Failed to start voice session")
    else:
        print("❌ No cooking agent created")

if __name__ == "__main__":
    test_full_integration()
