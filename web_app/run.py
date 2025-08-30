#!/usr/bin/env python3
"""
Simple startup script for Su-Chef Web Application
"""

from app import app

if __name__ == '__main__':
    print("🍳 Starting Su-Chef Web Application...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Su-Chef Web Application stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Make sure you have:")
        print("   - Installed all requirements: pip install -r requirements.txt")
        print("   - Set up your .env file with API keys")
        print("   - No other application using port 5000")
