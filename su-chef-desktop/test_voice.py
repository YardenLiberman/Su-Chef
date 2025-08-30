#!/usr/bin/env python3
"""
Test script to check if voice services are available
"""

import os
from dotenv import load_dotenv

def test_voice_setup():
    print("🔍 Checking Su-Chef Voice Setup...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check OpenAI API
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("✅ OpenAI API Key: Found")
        print(f"   Key starts with: {openai_key[:10]}...")
    else:
        print("❌ OpenAI API Key: Missing")
        print("   Recipe generation will not work")
    
    # Check Azure Speech Services
    speech_key = os.getenv("SPEECH_KEY")
    speech_region = os.getenv("SPEECH_REGION")
    
    if speech_key and speech_region:
        print("✅ Azure Speech Services: Configured")
        print(f"   Speech Key starts with: {speech_key[:10]}...")
        print(f"   Region: {speech_region}")
    else:
        print("❌ Azure Speech Services: Missing")
        print("   Voice input/output will not work")
        if not speech_key:
            print("   Missing: SPEECH_KEY")
        if not speech_region:
            print("   Missing: SPEECH_REGION")
    
    print("\n" + "=" * 50)
    
    if not openai_key and not speech_key:
        print("🚨 CRITICAL: No API keys configured!")
        print("\nTo fix this:")
        print("1. Copy env_template.txt to .env")
        print("2. Add your actual API keys to .env")
        print("3. Restart the application")
        return False
    elif not speech_key:
        print("⚠️  Voice features disabled - no Speech API key")
        return False
    elif not openai_key:
        print("⚠️  Recipe generation disabled - no OpenAI API key") 
        return False
    else:
        print("🎉 All services configured!")
        return True

if __name__ == "__main__":
    test_voice_setup()
