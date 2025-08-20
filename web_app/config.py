# Su-Chef Web Application Configuration
import os

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-12345')

# Database Configuration
DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///su_chef_web.db')

# Application Configuration
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '127.0.0.1')  # Changed from 0.0.0.0 to 127.0.0.1 for security
PORT = int(os.getenv('PORT', '5000'))
