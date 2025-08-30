#!/usr/bin/env python3
"""
Test desktop app voice integration
"""

from core.services import CookingService

def test_desktop_voice():
    print("🧪 Testing Desktop App Voice Integration")
    print("=" * 50)
    
    # Create cooking service like desktop app does
    cooking_service = CookingService()
    
    # Test recipe data
    test_recipe = {
        "name": "Test Recipe",
        "ingredients": ["1 cup water", "1 tsp salt"],
        "instructions": ["Boil water", "Add salt", "Stir and serve"]
    }
    
    print("1. Starting cooking service...")
    success = cooking_service.start(test_recipe)
    
    if not success:
        print("❌ Failed to start cooking service")
        return
    
    print("2. Starting session...")
    if cooking_service.agent:
        session_started = cooking_service.agent.start_session()
        print(f"   Session started: {session_started}")
        
        if session_started:
            print("3. Testing voice commands...")
            
            # Test speaking
            print("   Testing speech...")
            cooking_service.agent.speak("Hello, this is a test")
            
            # Test commands
            print("   Testing 'next' command...")
            cooking_service.agent.send_command("next")
            
            print("   Testing 'repeat' command...")
            cooking_service.agent.send_command("repeat")
            
            print("   Testing 'ingredients' command...")
            cooking_service.agent.send_command("ingredients")
            
            print("4. Stopping session...")
            cooking_service.agent.stop_session()
            
            print("✅ Desktop voice test completed!")
        else:
            print("❌ Failed to start session")
    else:
        print("❌ No agent created")

if __name__ == "__main__":
    test_desktop_voice()
