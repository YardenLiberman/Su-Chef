#!/usr/bin/env python3
"""
Debug speech initialization
"""

import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

def debug_speech():
    print("🔍 Debugging Speech Initialization")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Check environment variables
    speech_key = os.getenv("SPEECH_KEY")
    speech_region = os.getenv("SPEECH_REGION")
    
    print(f"Speech Key: {speech_key[:10] if speech_key else 'None'}...")
    print(f"Speech Region: {speech_region}")
    
    if not speech_key:
        print("❌ No SPEECH_KEY found")
        return
        
    if not speech_region:
        print("❌ No SPEECH_REGION found")
        return
    
    # Try to create speech config
    try:
        print("Creating speech config...")
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, 
            region=speech_region
        )
        print("✅ Speech config created")
        
        # Try to create synthesizer
        print("Creating synthesizer...")
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        print("✅ Synthesizer created")
        
        # Try to create recognizer
        print("Creating recognizer...")
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        print("✅ Recognizer created")
        
        print("🎉 All speech services initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_speech()
