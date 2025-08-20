#!/usr/bin/env python3
"""
Test script to verify Su-Chef setup and basic functionality.
Run this to check if everything is configured correctly.
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import python-dotenv: {e}")
        print("   Run: pip install python-dotenv")
        return False
    
    try:
        import openai
        print("✅ openai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import openai: {e}")
        print("   Run: pip install openai")
        return False
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        print("✅ azure-cognitiveservices-speech imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import azure-cognitiveservices-speech: {e}")
        print("   Run: pip install azure-cognitiveservices-speech")
        return False
    
    return True

def test_local_modules():
    """Test if local project modules can be imported."""
    print("\n🔍 Testing local modules...")
    
    try:
        from database import RecipeDatabase
        print("✅ RecipeDatabase imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import RecipeDatabase: {e}")
        return False
    
    try:
        from recipe_generator import get_recipe_from_openai
        print("✅ recipe_generator imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import recipe_generator: {e}")
        return False
    
    try:
        from cooking_agent import CookingAgent
        print("✅ CookingAgent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import CookingAgent: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variable setup."""
    print("\n🔍 Testing environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    speech_key = os.getenv("SPEECH_KEY")
    
    if openai_key:
        print("✅ OPENAI_API_KEY found")
    else:
        print("⚠️  OPENAI_API_KEY not found")
        print("   Create a .env file with your OpenAI API key")
    
    if speech_key:
        print("✅ SPEECH_KEY found")
    else:
        print("⚠️  SPEECH_KEY not found")
        print("   Create a .env file with your Azure Speech key")
    
    return bool(openai_key and speech_key)

def test_database():
    """Test database initialization."""
    print("\n🔍 Testing database...")
    
    try:
        from database import RecipeDatabase
        db = RecipeDatabase()
        print("✅ Database initialized successfully")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Su-Chef Setup Test")
    print("=" * 40)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test local modules
    if not test_local_modules():
        all_tests_passed = False
    
    # Test environment
    if not test_environment():
        all_tests_passed = False
    
    # Test database
    if not test_database():
        all_tests_passed = False
    
    print("\n" + "=" * 40)
    if all_tests_passed:
        print("🎉 All tests passed! Su-Chef is ready to use.")
        print("\nNext steps:")
        print("1. Set up your API keys in a .env file")
        print("2. Run: python su_chef.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Create a .env file with your API keys")
        print("3. Check file permissions and database access")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
