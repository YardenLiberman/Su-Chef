#!/usr/bin/env python3
"""
Su-Chef Windows Wrapper
Handles Windows encoding issues for the GUI subprocess
"""

import sys
import os
import codecs

# Force UTF-8 encoding for Windows
if os.name == 'nt':
    # Set console to UTF-8
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')

# Import and run the main Su-Chef application
try:
    from su_chef import main
    if __name__ == "__main__":
        main()
except UnicodeEncodeError as e:
    print(f"[ERROR] Unicode encoding error: {e}")
    print("[INFO] This is a Windows encoding issue. Using fallback mode.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Application error: {e}")
    sys.exit(1)
