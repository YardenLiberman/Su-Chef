#!/usr/bin/env python3
"""
Su-Chef Web Application
Flask backend for the interactive cooking assistant
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, Dict, List, Any

# Load environment variables
load_dotenv()

# Add parent directory to path to import Su-Chef backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Su-Chef backend components
from cooking_agent import CookingAgent
from recipe_generator import get_recipe_from_openai, process_recipe
from database import RecipeDatabase as SuChefDatabase

# Import configuration
from config import SECRET_KEY, DATABASE_URI, DEBUG, HOST, PORT

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Su-Chef backend components (will be created per request to avoid threading issues)
suchef_db = None

# Global voice agent (initialized when needed)
voice_agent = None

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cooking preferences
    skill_level = db.Column(db.String(20), default='beginner')
    dietary_restrictions = db.Column(db.String(200))
    preferred_cooking_time = db.Column(db.Integer, default=30)
    favorite_cuisine = db.Column(db.String(50))
    
    # Relationships
    recipes = db.relationship('UserRecipe', backref='user', lazy=True)
    cooking_sessions = db.relationship('CookingSession', backref='user', lazy=True)

class UserRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_name = db.Column(db.String(200), nullable=False)
    recipe_data = db.Column(db.Text, nullable=False)  # JSON string
    is_cooked = db.Column(db.Boolean, default=False)
    is_liked = db.Column(db.Boolean, default=False)
    cooked_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CookingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('user_recipe.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    current_step = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import the exact CLI functions that work
def parse_ingredients_input(ingredients_input: str) -> List[str]:
    """Parse comma-separated ingredients input."""
    if not ingredients_input:
        return []
    return [ingredient.strip() for ingredient in ingredients_input.split(',') if ingredient.strip()]

def build_recipe_prompt(meal_type: str, cooking_time: str, skill_level: str, 
                       dietary_restrictions: Optional[str], available_ingredients: List[str]) -> str:
    """Build recipe generation prompt - EXACT copy from CLI"""
    
    # Base prompt structure
    prompt = f"""Generate a detailed {meal_type} recipe with the following specifications:

REQUIREMENTS:
- Meal Type: {meal_type}
- Maximum Cooking Time: {cooking_time} minutes
- Skill Level: {skill_level}
- Dietary Restrictions: {dietary_restrictions or 'None'}
"""
    
    # Add available ingredients if provided
    if available_ingredients:
        ingredients_str = ', '.join(available_ingredients)
        prompt += f"- Available Ingredients: {ingredients_str}\n"
        prompt += "- Please prioritize using the available ingredients listed above\n"
    
    prompt += """
RESPONSE FORMAT:
Please provide a complete recipe in the following format:

Recipe Name: [Creative and descriptive name]

Ingredients:
- [ingredient 1 with quantity]
- [ingredient 2 with quantity]
- [etc.]

Instructions:
1. [step 1]
2. [step 2]
"""
    
    return prompt

# Use the EXACT same logic as the working CLI
def generate_ai_recipe(meal_type, cooking_time, skill_level, dietary_restrictions, available_ingredients=None):
    """Generate recipe using EXACT CLI logic"""
    
    # Get OpenAI API key from environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return generate_fallback_recipe(meal_type, cooking_time, skill_level, dietary_restrictions)
    
    try:
        # Parse ingredients exactly like CLI
        if available_ingredients and isinstance(available_ingredients, str):
            available_ingredients = parse_ingredients_input(available_ingredients)
        elif not available_ingredients:
            available_ingredients = []
        
        # Build prompt using EXACT CLI function
        base_prompt = build_recipe_prompt(
            meal_type, str(cooking_time), skill_level, 
            dietary_restrictions, available_ingredients
        )
        
        print(f"🤖 Generating {meal_type} recipe with OpenAI...")
        print(f"Parameters: {cooking_time}min, {skill_level}, {dietary_restrictions or 'no restrictions'}")
        
        # Use EXACT CLI recipe generation with timeout protection
        print("🔄 Calling OpenAI API...")
        recipe_text = get_recipe_from_openai(base_prompt, openai_key)
        print(f"📝 OpenAI response length: {len(recipe_text) if recipe_text else 0} characters")
        
        if recipe_text:
            print("✅ Recipe generated successfully!")
            
            # Try to process using CLI processor
            try:
                print("🔄 Processing recipe with CLI processor...")
                processed_recipe = process_recipe(recipe_text, meal_type, str(cooking_time), skill_level, dietary_restrictions)
                processed_recipe['raw_text'] = recipe_text  # Keep original for debugging
                print("✅ Recipe processing completed successfully!")
                return processed_recipe
            except Exception as process_error:
                print(f"⚠️ Processing failed: {process_error}")
                import traceback
                traceback.print_exc()
                # Return raw recipe if processing fails
                return {
                    "name": f"AI Generated {meal_type.title()} Recipe",
                    "meal_type": meal_type,
                    "cooking_time": cooking_time,
                    "skill_level": skill_level,
                    "dietary_restrictions": dietary_restrictions,
                    "ingredients": ["See recipe text below for ingredients"],
                    "steps": [recipe_text],
                    "raw_text": recipe_text,
                    "ai_generated": True
                }
        else:
            print("❌ Recipe generation failed - no response from OpenAI")
            return generate_fallback_recipe(meal_type, cooking_time, skill_level, dietary_restrictions)
            
    except Exception as e:
        print(f"❌ Recipe generation error: {e}")
        return generate_fallback_recipe(meal_type, cooking_time, skill_level, dietary_restrictions)

def generate_fallback_recipe(meal_type, cooking_time, skill_level, dietary_restrictions):
    """Fallback recipe when AI is not available"""
    print(f"🔄 Generating fallback recipe for {meal_type}")
    
    # Simple recipes based on meal type
    recipes = {
        "breakfast": {
            "name": "Simple Scrambled Eggs",
            "ingredients": ["2 eggs", "2 tbsp butter", "Salt and pepper", "Optional: cheese"],
            "steps": [
                "Crack eggs into a bowl and whisk",
                "Heat butter in a non-stick pan over medium heat", 
                "Pour eggs into pan and gently stir",
                "Cook for 2-3 minutes until set",
                "Season with salt and pepper, serve hot"
            ]
        },
        "lunch": {
            "name": "Quick Sandwich",
            "ingredients": ["2 slices bread", "Filling of choice", "Butter or mayo"],
            "steps": [
                "Toast bread if desired",
                "Spread butter or mayo on one side",
                "Add your favorite filling", 
                "Close sandwich and cut if desired",
                "Serve immediately"
            ]
        },
        "dinner": {
            "name": "Simple Pasta",
            "ingredients": ["200g pasta", "2 tbsp olive oil", "2 cloves garlic", "Salt", "Parmesan cheese"],
            "steps": [
                "Boil water in a large pot with salt",
                "Cook pasta according to package directions",
                "Heat olive oil and sauté minced garlic",
                "Drain pasta and toss with garlic oil", 
                "Serve with grated Parmesan cheese"
            ]
        }
    }
    
    recipe_template = recipes.get(meal_type.lower(), recipes["lunch"])
    
    return {
        "name": recipe_template["name"],
        "meal_type": meal_type,
        "cooking_time": cooking_time,
        "skill_level": skill_level,
        "dietary_restrictions": dietary_restrictions or "None",
        "ingredients": recipe_template["ingredients"],
        "steps": recipe_template["steps"],
        "fallback": True,
        "ai_generated": False,
        "note": "This is a fallback recipe. Configure OPENAI_API_KEY for AI-generated recipes."
    }

# Routes
@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(username=data['username']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            login_user(user)
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'error': 'Username already exists'})
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': 'Email already registered'})
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            skill_level=data.get('skill_level', 'beginner'),
            dietary_restrictions=data.get('dietary_restrictions', ''),
            preferred_cooking_time=data.get('preferred_cooking_time', 30),
            favorite_cuisine=data.get('favorite_cuisine', '')
        )
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return jsonify({'success': True, 'redirect': url_for('dashboard')})
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Main user dashboard"""
    return render_template('dashboard.html')

@app.route('/api/generate_recipe', methods=['POST'])
@login_required
def generate_recipe():
    """Generate recipe using EXACT CLI backend logic"""
    data = request.get_json()
    
    print(f"\n🍳 Recipe generation request from {current_user.username}")
    print(f"Parameters: {data}")
    
    try:
        # Generate recipe using EXACT CLI logic
        recipe_data = generate_ai_recipe(
            meal_type=data.get('meal_type', 'dinner'),
            cooking_time=data.get('cooking_time', 30),
            skill_level=data.get('skill_level', 'beginner'),
            dietary_restrictions=data.get('dietary_restrictions'),
            available_ingredients=data.get('available_ingredients')
        )
        
        print(f"✅ Recipe generated: {recipe_data.get('name', 'Unknown')}")
        
        # Save to Su-Chef database if it's a real recipe
        database_saved = False
        if not recipe_data.get('fallback'):
            try:
                # Create new database instance for this request
                temp_db = SuChefDatabase()
                
                # Add user to Su-Chef database
                suchef_user_id = temp_db.add_user(current_user.username)
                
                # Save recipe to Su-Chef database
                recipe_id = temp_db.save_recipe(recipe_data, suchef_user_id)
                recipe_data['suchef_recipe_id'] = recipe_id
                database_saved = True
                
                # Close the database connection
                temp_db.close()
                print(f"✅ Recipe saved to Su-Chef database with ID: {recipe_id}")
                
            except Exception as e:
                print(f"⚠️ Failed to save to Su-Chef database: {e}")
        
        return jsonify({
            'success': True,
            'recipe': recipe_data,
            'ai_powered': not recipe_data.get('fallback', False),
            'database_saved': database_saved,
            'debug_info': {
                'has_openai_key': bool(os.getenv("OPENAI_API_KEY")),
                'has_speech_key': bool(os.getenv("SPEECH_KEY")),
                'is_fallback': recipe_data.get('fallback', False)
            }
        })
    except Exception as e:
        print(f"❌ Recipe generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': str(e),
            'debug_info': {
                'has_openai_key': bool(os.getenv("OPENAI_API_KEY")),
                'has_speech_key': bool(os.getenv("SPEECH_KEY"))
            }
        })

# Voice guidance API endpoints
@app.route('/api/voice/initialize', methods=['POST'])
@login_required
def initialize_voice_agent():
    """Initialize voice agent for cooking guidance"""
    global voice_agent
    
    try:
        if not voice_agent:
            # Initialize without microphone test to prevent blocking
            voice_agent = CookingAgent(test_microphone=False)
        
        return jsonify({
            'success': True,
            'message': 'Voice agent initialized',
            'voice_available': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'voice_available': False
        })

@app.route('/api/voice/speak', methods=['POST'])
@login_required
def voice_speak():
    """Text-to-speech endpoint"""
    global voice_agent
    data = request.get_json()
    
    try:
        if not voice_agent:
            voice_agent = CookingAgent(test_microphone=False)
        
        text = data.get('text', '')
        success = voice_agent.speak(text)
        
        return jsonify({
            'success': success,
            'message': 'Speech completed' if success else 'Speech failed'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/voice/listen', methods=['GET'])
@login_required
def voice_listen():
    """Speech-to-text endpoint"""
    global voice_agent
    
    try:
        print("🎤 Voice listen endpoint called")
        
        if not voice_agent:
            print("🤖 Initializing new voice agent...")
            voice_agent = CookingAgent(test_microphone=False)
            print("✅ Voice agent initialized")
            
            # Verify the voice agent is properly configured
            if hasattr(voice_agent, 'speech_key') and voice_agent.speech_key:
                print("✅ Azure Speech Key configured")
            else:
                print("❌ Azure Speech Key missing!")
                
            if hasattr(voice_agent, 'recognizer') and voice_agent.recognizer:
                print("✅ Speech recognizer initialized")
            else:
                print("❌ Speech recognizer not initialized!")
        
        print("🎤 Starting speech recognition...")
        print("🎤 Please speak now... (listening for 10 seconds)")
        
        # Give more time and better error handling
        recognized_text = voice_agent.listen()
        
        if recognized_text:
            print(f"✅ Speech recognized: '{recognized_text}'")
        else:
            print("❌ No speech recognized or recognition failed")
        
        print(f"🎤 Final recognition result: '{recognized_text}'")
        
        return jsonify({
            'success': bool(recognized_text),
            'text': recognized_text or '',
            'message': 'Speech recognized' if recognized_text else 'No speech detected'
        })
    except Exception as e:
        print(f"❌ Voice listen error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/voice/guidance', methods=['POST'])
@login_required
def start_voice_guidance():
    """Start voice-guided cooking session"""
    global voice_agent
    data = request.get_json()
    
    try:
        if not voice_agent:
            voice_agent = CookingAgent(test_microphone=False)
        
        # Load recipe data into voice agent
        recipe_data = data.get('recipe')
        if recipe_data:
            # Convert web format to Su-Chef format
            steps_data = {
                'recipe_name': recipe_data['name'],
                'steps': [
                    {'step_number': i+1, 'text': step}
                    for i, step in enumerate(recipe_data['steps'])
                ]
            }
            
            # Save temporary recipe file for voice agent in web_app directory
            steps_file_path = os.path.join(os.path.dirname(__file__), 'steps.json')
            with open(steps_file_path, 'w') as f:
                json.dump(steps_data, f, indent=2)
            
            # Load recipe into voice agent
            if voice_agent.load_recipe(steps_file_path):
                # Start the cooking session immediately
                voice_agent.speak(f"Starting cooking session for {recipe_data['name']}. Say 'next' to begin with the first step.")
                return jsonify({
                    'success': True,
                    'message': 'Voice guidance started! Say "next" to begin cooking.',
                    'recipe_loaded': True,
                    'recipe_name': recipe_data['name'],
                    'total_steps': len(recipe_data['steps']),
                    'instructions': 'Voice guidance is now active. Use voice commands: "next", "repeat", "ingredients", "help"'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to load recipe file for voice guidance'
                })
        
        return jsonify({
            'success': False,
            'error': 'No recipe data provided for voice guidance'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/voice/interact', methods=['POST'])
@login_required
def voice_interact():
    """Handle voice interaction during cooking"""
    global voice_agent
    data = request.get_json()
    
    try:
        if not voice_agent:
            return jsonify({'success': False, 'error': 'Voice agent not initialized'})
        
        command = data.get('command', '').lower().strip()
        
        if command == 'next':
            # Move to next step
            if hasattr(voice_agent, 'current_step') and hasattr(voice_agent, 'recipe_steps') and voice_agent.recipe_steps:
                if voice_agent.current_step < len(voice_agent.recipe_steps) - 1:
                    voice_agent.current_step += 1
                    step_number = voice_agent.current_step + 1
                    total_steps = len(voice_agent.recipe_steps)
                    step_text = f"Step {step_number} of {total_steps}: {voice_agent.recipe_steps[voice_agent.current_step]}"
                    
                    # Speak with step information
                    voice_agent.speak(step_text)
                    
                    # Also print to console for debugging
                    print(f"🍳 Speaking: {step_text}")
                    
                    return jsonify({
                        'success': True,
                        'message': step_text,
                        'step_number': step_number,
                        'total_steps': total_steps,
                        'is_last_step': voice_agent.current_step >= len(voice_agent.recipe_steps) - 1
                    })
                else:
                    completion_msg = f"Congratulations! You have completed all {len(voice_agent.recipe_steps)} steps of the recipe. Enjoy your meal!"
                    voice_agent.speak(completion_msg)
                    print(f"🎉 Recipe completed: {completion_msg}")
                    return jsonify({
                        'success': True,
                        'message': completion_msg,
                        'completed': True,
                        'total_steps': len(voice_agent.recipe_steps)
                    })
            else:
                error_msg = "No recipe loaded. Please start a cooking session first."
                voice_agent.speak(error_msg)
                return jsonify({'success': False, 'error': 'No recipe loaded'})
                
        elif command == 'repeat':
            # Repeat current step
            if hasattr(voice_agent, 'current_step') and hasattr(voice_agent, 'recipe_steps') and voice_agent.recipe_steps:
                step_number = voice_agent.current_step + 1
                total_steps = len(voice_agent.recipe_steps)
                step_text = f"Repeating step {step_number} of {total_steps}: {voice_agent.recipe_steps[voice_agent.current_step]}"
                voice_agent.speak(step_text)
                print(f"🔄 Repeating: {step_text}")
                return jsonify({
                    'success': True, 
                    'message': step_text,
                    'step_number': step_number,
                    'total_steps': total_steps
                })
            else:
                error_msg = "No recipe loaded. Please start a cooking session first."
                voice_agent.speak(error_msg)
                return jsonify({'success': False, 'error': 'No recipe loaded'})
                
        elif command == 'ingredients':
            # List ingredients
            voice_agent.speak("Let me list the ingredients for you.")
            return jsonify({'success': True, 'message': 'Listing ingredients'})
            
        elif command == 'help':
            # Provide help
            help_msg = "Available commands: Say 'next' for next step, 'repeat' to repeat current step, 'ingredients' to list ingredients."
            voice_agent.speak(help_msg)
            return jsonify({'success': True, 'message': help_msg})
            
        else:
            # Listen for voice input
            recognized_text = voice_agent.listen()
            if recognized_text:
                return jsonify({
                    'success': True,
                    'recognized_text': recognized_text,
                    'message': f'You said: {recognized_text}'
                })
            else:
                return jsonify({'success': False, 'error': 'No speech recognized'})
                
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test_voice', methods=['GET'])
def test_voice():
    """Simple voice test endpoint"""
    try:
        print("🎤 Direct voice test called")
        agent = CookingAgent(test_microphone=False)
        print("🎤 Agent created, testing speech recognition...")
        
        result = agent.listen()
        print(f"🎤 Direct test result: '{result}'")
        
        return jsonify({
            'success': bool(result),
            'text': result or '',
            'message': f'Direct test: {result}' if result else 'No speech detected in direct test'
        })
    except Exception as e:
        print(f"❌ Direct voice test error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test_backend', methods=['GET'])
def test_backend():
    """Test if Su-Chef backend components are working"""
    results = {}
    
    # Test OpenAI availability
    openai_key = os.getenv("OPENAI_API_KEY")
    results['openai_available'] = bool(openai_key)
    
    # Test Speech services availability  
    speech_key = os.getenv("SPEECH_KEY")
    results['speech_available'] = bool(speech_key)
    
    # Test database
    try:
        temp_db = SuChefDatabase()
        temp_db.close()
        results['database_available'] = True
    except Exception as e:
        results['database_available'] = False
        results['database_error'] = str(e)
    
    # Test recipe generator
    try:
        if openai_key:
            # Just test the import, don't actually call OpenAI
            results['recipe_generator_available'] = True
        else:
            results['recipe_generator_available'] = False
            results['recipe_generator_error'] = "No OpenAI API key"
    except Exception as e:
        results['recipe_generator_available'] = False
        results['recipe_generator_error'] = str(e)
    
    # Test voice agent
    try:
        if speech_key:
            results['voice_agent_available'] = True
        else:
            results['voice_agent_available'] = False
            results['voice_agent_error'] = "No Speech API key"
    except Exception as e:
        results['voice_agent_available'] = False
        results['voice_agent_error'] = str(e)
    
    return jsonify({
        'success': True,
        'backend_status': results
    })

@app.route('/api/get_saved_recipes', methods=['GET'])
@login_required
def get_saved_recipes():
    """Get user's saved recipes"""
    try:
        # Get recipes from Flask database
        user_recipes = UserRecipe.query.filter_by(user_id=current_user.id).all()
        
        recipes = []
        for user_recipe in user_recipes:
            recipe_data = json.loads(user_recipe.recipe_data)
            recipes.append({
                'id': user_recipe.id,
                'name': user_recipe.recipe_name,
                'is_cooked': user_recipe.is_cooked,
                'is_liked': user_recipe.is_liked,
                'created_at': user_recipe.created_at.isoformat(),
                'recipe_data': recipe_data
            })
        
        # Also try to get recipes from Su-Chef database
        try:
            temp_db = SuChefDatabase()
            suchef_user_id = temp_db.add_user(current_user.username)  # This will get existing user
            suchef_recipes = temp_db.get_user_history(suchef_user_id)
            
            # Add Su-Chef recipes to the list with full details
            for recipe in suchef_recipes:
                recipe_id = recipe[0]
                # Get full recipe details including steps and ingredients
                recipe_details = temp_db.get_recipe_details(recipe_id)
                
                if recipe_details:
                    recipes.append({
                        'id': f"suchef_{recipe_id}",
                        'name': recipe[1],
                        'is_cooked': bool(recipe[7]),
                        'is_liked': bool(recipe[8]),
                        'created_at': recipe[9].isoformat() if recipe[9] else None,
                        'source': 'suchef',
                        'recipe_data': {
                            'name': recipe[1],
                            'meal_type': recipe[2],
                            'cooking_time': recipe[3],
                            'skill_level': recipe[4],
                            'dietary_restrictions': recipe[5],
                            'ingredients': recipe_details.get('ingredients', []),
                            'steps': recipe_details.get('steps', [])
                        }
                    })
                else:
                    # Fallback if details not found
                    recipes.append({
                        'id': f"suchef_{recipe_id}",
                        'name': recipe[1],
                        'is_cooked': bool(recipe[7]),
                        'is_liked': bool(recipe[8]),
                        'created_at': recipe[9].isoformat() if recipe[9] else None,
                        'source': 'suchef',
                        'recipe_data': {
                            'name': recipe[1],
                            'meal_type': recipe[2],
                            'cooking_time': recipe[3],
                            'skill_level': recipe[4],
                            'dietary_restrictions': recipe[5],
                            'ingredients': [],
                            'steps': ["Recipe details not available"]
                        }
                    })
            
            # Close database connection
            temp_db.close()
        except Exception as e:
            print(f"Could not load Su-Chef recipes: {e}")
        
        return jsonify({
            'success': True,
            'recipes': recipes
        })
    except Exception as e:
        print(f"Error getting saved recipes: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_recipe', methods=['POST'])
@login_required
def save_recipe():
    """Save recipe to user's collection"""
    data = request.get_json()
    
    user_recipe = UserRecipe(
        user_id=current_user.id,
        recipe_name=data['recipe_name'],
        recipe_data=json.dumps(data['recipe_data']),
        is_cooked=data.get('is_cooked', False),
        is_liked=data.get('is_liked', False)
    )
    
    db.session.add(user_recipe)
    db.session.commit()
    
    return jsonify({'success': True, 'recipe_id': user_recipe.id})

@app.route('/api/user_recipes')
@login_required
def get_user_recipes():
    """Get user's saved recipes"""
    recipes = UserRecipe.query.filter_by(user_id=current_user.id).all()
    
    recipe_list = []
    for recipe in recipes:
        recipe_list.append({
            'id': recipe.id,
            'name': recipe.recipe_name,
            'is_cooked': recipe.is_cooked,
            'is_liked': recipe.is_liked,
            'cooked_date': recipe.cooked_date.isoformat() if recipe.cooked_date else None,
            'created_at': recipe.created_at.isoformat() if recipe.created_at else None
        })
    
    return jsonify({'success': True, 'recipes': recipe_list})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("Starting Su-Chef Web Application...")
    print(f"Server will be available at: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=DEBUG, host=HOST, port=PORT)
