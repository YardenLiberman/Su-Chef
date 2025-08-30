#!/usr/bin/env python3
"""
Simple launcher for Su-Chef desktop app
This can be called from the web app to launch the desktop app
"""
import sys
import subprocess
import os
from pathlib import Path

def launch_desktop_app(recipe_id):
    """Launch the desktop app with a specific recipe ID"""
    try:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent.absolute()
        desktop_app_path = script_dir / "cooking_desktop_app.py"
        
        if not desktop_app_path.exists():
            print(f"❌ Error: {desktop_app_path} not found!")
            return False
        
        # Launch the desktop app with the recipe ID
        cmd = [sys.executable, str(desktop_app_path), f"suchef://recipe/{recipe_id}"]
        
        print(f"🚀 Launching Su-Chef Desktop App for recipe {recipe_id}...")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🐍 Python executable: {sys.executable}")
        print(f"📱 Desktop app path: {desktop_app_path}")
        print(f"🔗 Command: {' '.join(cmd)}")
        
        # Use subprocess.run with capture_output to see any errors
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Desktop app launched successfully!")
            return True
        else:
            print(f"❌ Desktop app failed to start (exit code: {result.returncode})")
            print(f"📤 stdout: {result.stdout}")
            print(f"📥 stderr: {result.stderr}")
            return False
        
    except subprocess.TimeoutExpired:
        print("⏰ Desktop app launch timed out - it might be running in background")
        return True
    except Exception as e:
        print(f"❌ Error launching desktop app: {e}")
        return False

def main():
    if len(sys.argv) > 1:
        recipe_id = sys.argv[1]
        success = launch_desktop_app(recipe_id)
        if not success:
            print("\n💡 Troubleshooting tips:")
            print("1. Check if you have all required packages: pip install -r desktop_requirements.txt")
            print("2. Check if you have a .env file with SPEECH_KEY and SPEECH_REGION")
            print("3. Try running the desktop app directly: python cooking_desktop_app.py")
            print("4. Check the console for any error messages")
    else:
        print("Usage: python launch_suchef.py <recipe_id>")
        print("Example: python launch_suchef.py 6")

if __name__ == "__main__":
    main()
