#!/usr/bin/env python3
"""
Test script to debug GUI-CLI interaction
Run this to see exactly what the CLI expects and outputs
"""

import subprocess
import sys
import time

def test_cli_interaction():
    """Test the CLI interaction manually"""
    print("🧪 Testing Su-Chef CLI interaction...")
    
    # Check if su_chef.py exists
    import os
    if not os.path.exists("su_chef.py"):
        print("❌ su_chef.py not found in current directory")
        return
    
    try:
        # Start CLI process
        process = subprocess.Popen(
            [sys.executable, "su_chef.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("✅ CLI process started")
        
        # Test commands sequence
        commands = [
            "TestUser",  # Username
            "1",         # Create new recipe
            "3",         # Dinner
            "30",        # 30 minutes
            "2",         # Intermediate
            "6",         # No dietary restrictions
            "chicken, rice, vegetables",  # Ingredients
            "1"          # Accept recipe
        ]
        
        print("\n📝 Sending commands:")
        for i, cmd in enumerate(commands):
            print(f"  {i+1}. Sending: '{cmd}'")
            process.stdin.write(f"{cmd}\n")
            process.stdin.flush()
            
            # Read some output
            time.sleep(1)
            
            # Try to read available output (non-blocking)
            import select
            if select.select([process.stdout], [], [], 0)[0]:
                try:
                    output = process.stdout.read(1024)
                    if output:
                        print(f"     Output: {output[:100]}...")
                except:
                    pass
        
        print("\n⏳ Waiting for final output...")
        time.sleep(5)
        
        # Try to read final output
        try:
            final_output = process.stdout.read(2048)
            if final_output:
                print(f"📄 Final output:\n{final_output}")
        except:
            pass
        
        # Cleanup
        process.terminate()
        print("✅ Test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_cli_interaction()
