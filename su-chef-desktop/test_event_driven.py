#!/usr/bin/env python3
"""
Simple test for event-driven cooking agent
Tests the new non-blocking architecture
"""

import sys
import time
import json
from core.cooking_agent import CookingAgent, CookingState

def create_test_recipe():
    """Create a simple test recipe"""
    test_recipe = {
        "recipe_name": "Test Recipe",
        "ingredients": ["1 cup water", "1 tsp salt"],
        "steps": [
            {"step_number": 1, "text": "Boil water in a pot"},
            {"step_number": 2, "text": "Add salt to the water"},
            {"step_number": 3, "text": "Stir and serve"}
        ]
    }
    
    with open('steps.json', 'w') as f:
        json.dump(test_recipe, f, indent=2)
    
    print("✅ Created test recipe: steps.json")

def test_event_driven_agent():
    """Test the event-driven cooking agent"""
    print("🧪 Testing Event-Driven Cooking Agent")
    print("=" * 50)
    
    # Create test recipe
    create_test_recipe()
    
    # Initialize agent
    print("1. Initializing agent...")
    agent = CookingAgent(test_microphone=False)  # Skip mic test
    
    if not hasattr(agent, 'speech_key') or not agent.speech_key:
        print("⚠️  No speech key - will test without voice")
    
    # Set up callbacks to see what happens
    def on_status(status):
        print(f"📢 Status: {status}")
    
    def on_step_change(step_idx):
        print(f"📍 Step changed to: {step_idx + 1}")
    
    def on_speech_heard(text):
        print(f"🎤 Heard: {text}")
    
    def on_error(error):
        print(f"❌ Error: {error}")
    
    agent.set_ui_callbacks(
        on_status_change=on_status,
        on_step_change=on_step_change,
        on_speech_heard=on_speech_heard,
        on_error=on_error
    )
    
    # Test state transitions
    print(f"2. Initial state: {agent.state}")
    
    # Start session (non-blocking)
    print("3. Starting session...")
    success = agent.start_session()
    
    if not success:
        print("❌ Failed to start session")
        return
    
    print(f"4. State after start: {agent.state}")
    
    # Test commands
    test_commands = ["next", "repeat", "ingredients", "next", "stop"]
    
    for i, cmd in enumerate(test_commands):
        print(f"\n5.{i+1} Testing command: '{cmd}'")
        agent.send_command(cmd)
        time.sleep(1)  # Give time for processing
        print(f"     Current state: {agent.state}")
        
        if agent.state == CookingState.STOPPED:
            break
    
    # Clean shutdown
    print("\n6. Stopping session...")
    agent.stop_session()
    print(f"7. Final state: {agent.state}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    try:
        test_event_driven_agent()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
