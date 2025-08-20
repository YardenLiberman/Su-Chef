#!/usr/bin/env python3
"""
Simple test server for Su-Chef
"""

from app import app

if __name__ == "__main__":
    print("=" * 60)
    print("Su-Chef Test Server Starting...")
    print("=" * 60)
    print("Server will be available at: http://127.0.0.1:5000")
    print("Open your browser and go to that URL")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")
