#!/usr/bin/env python3
"""
Simple startup script for Su-Chef Web Application
"""

import sys
import os

def main():
    print("=" * 50)
    print("Su-Chef Web Application Startup")
    print("=" * 50)
    
    try:
        print("1. Testing imports...")
        from app import app
        print("   ✓ Flask app imported successfully")
        
        print("2. Testing database models...")
        with app.app_context():
            from app import db
            print("   ✓ Database context created")
            
            # Test database creation
            db.create_all()
            print("   ✓ Database tables created")
        
        print("3. Starting Flask server...")
        print(f"   Server will be available at: http://127.0.0.1:5000")
        print("   Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the app
        app.run(debug=False, host='127.0.0.1', port=5000)
        
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        print("   Please check that all required packages are installed:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Startup failed! Check the error messages above.")
        input("Press Enter to exit...")
        sys.exit(1)
