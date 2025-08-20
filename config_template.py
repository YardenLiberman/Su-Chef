# Su-Chef Configuration Template
# Copy this file to config.py and fill in your actual API keys

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables")

# Azure Speech Services Configuration
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION", "westeurope")
VOICE_NAME = os.getenv("VOICE_NAME", "en-US-JennyMultilingualNeural")
LANGUAGE = os.getenv("LANGUAGE", "en-US")

if not SPEECH_KEY:
    print("Warning: SPEECH_KEY not found in environment variables")

# Application Configuration
MAX_RECIPE_ATTEMPTS = int(os.getenv("MAX_RECIPE_ATTEMPTS", "10"))
DEFAULT_COOKING_TIME = int(os.getenv("DEFAULT_COOKING_TIME", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database Configuration
DATABASE_NAME = os.getenv("DATABASE_NAME", "su_chef.db")
RECIPES_DIRECTORY = os.getenv("RECIPES_DIRECTORY", "recipes")

# Voice Configuration
SPEECH_SYNTHESIS_OUTPUT_FORMAT = "Raw16Khz16BitMonoPcm"
INITIAL_SILENCE_TIMEOUT_MS = "8000"
END_SILENCE_TIMEOUT_MS = "2000"
SEGMENTATION_SILENCE_TIMEOUT_MS = "2000"
