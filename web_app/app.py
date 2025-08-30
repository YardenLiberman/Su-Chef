#!/usr/bin/env python3
"""
Su-Chef Web Application
Flask-based web interface for the AI Cooking Assistant
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
import openai
import azure.cognitiveservices.speech as speechsdk
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'su-chef-secret-key-2024')
socketio = SocketIO(app, cors_allowed_origins="*")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///su_chef_web.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key and openai.api_key.startswith('sk-proj-'):
    openai.api_base = "https://api.openai.com/v1"

# Azure Speech configuration
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION", "westeurope")

# Jinja filters
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipes = db.relationship('Recipe', backref='user', lazy=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)
    cooking_time = db.Column(db.Integer, nullable=False)
    skill_level = db.Column(db.String(50), nullable=False)
    dietary_restrictions = db.Column(db.String(200))
    ingredients = db.Column(db.Text, nullable=False)  # JSON string
    steps = db.relationship('RecipeStep', backref='recipe', lazy=True, order_by='RecipeStep.step_number')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cooked = db.Column(db.Boolean, default=False)
    liked = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """Convert recipe to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'meal_type': self.meal_type,
            'cooking_time': self.cooking_time,
            'skill_level': self.skill_level,
            'dietary_restrictions': self.dietary_restrictions,
            'ingredients': json.loads(self.ingredients) if self.ingredients else [],
            'steps': [step.to_dict() for step in self.steps],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id,
            'cooked': self.cooked,
            'liked': self.liked
        }

class RecipeStep(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    step_number = db.Column(db.Integer, nullable=False)
    step_text = db.Column(db.Text, nullable=False)
    estimated_time = db.Column(db.Integer)
    tips = db.Column(db.Text)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    
    def to_dict(self):
        """Convert recipe step to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'step_number': self.step_number,
            'step_text': self.step_text,
            'estimated_time': self.estimated_time,
            'tips': self.tips,
            'recipe_id': self.recipe_id
        }

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    # Show all recipes (reverted to working version)
    recent_recipes = Recipe.query.filter_by(user_id=session['user_id']).order_by(Recipe.created_at.desc()).limit(5).all()
    
    # Convert recipes to dictionaries for template rendering
    recent_recipes_dict = [recipe.to_dict() for recipe in recent_recipes]
    
    # Get user statistics
    total_recipes = Recipe.query.filter_by(user_id=session['user_id']).count()
    cooked_recipes = Recipe.query.filter_by(user_id=session['user_id'], cooked=True).count()
    liked_recipes = Recipe.query.filter_by(user_id=session['user_id'], liked=True).count()
    
    return render_template('dashboard.html', 
                         user=user, 
                         recent_recipes=recent_recipes_dict,
                         total_recipes=total_recipes,
                         cooked_recipes=cooked_recipes,
                         liked_recipes=liked_recipes)

@app.route('/create_recipe', methods=['GET', 'POST'])
def create_recipe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.get_json()
        
        try:
            # Generate recipe using OpenAI
            recipe_text = generate_recipe_from_openai(data)
            if recipe_text:
                # Parse and save recipe
                recipe_data = parse_recipe_text(recipe_text)
                recipe = Recipe(
                    name=recipe_data['name'],
                    meal_type=data['meal_type'],
                    cooking_time=data['cooking_time'],
                    skill_level=data['skill_level'],
                    dietary_restrictions=data.get('dietary_restrictions'),
                    ingredients=json.dumps(recipe_data['ingredients']),
                    user_id=session['user_id']
                )
                
                db.session.add(recipe)
                db.session.flush()  # Get the recipe ID
                
                # Add steps
                for i, step_text in enumerate(recipe_data['steps'], 1):
                    step = RecipeStep(
                        recipe_id=recipe.id,
                        step_number=i,
                        step_text=step_text
                    )
                    db.session.add(step)
                
                db.session.commit()
                
                return jsonify({'success': True, 'recipe_id': recipe.id})
            else:
                return jsonify({'success': False, 'error': 'Failed to generate recipe'})
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    return render_template('create_recipe.html')

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != session['user_id']:
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    # Convert recipe to dictionary for template rendering
    recipe_dict = recipe.to_dict()
    
    return render_template('view_recipe.html', recipe=recipe_dict)

@app.route('/recipe/<int:recipe_id>/cook')
def cook_recipe(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != session['user_id']:
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    # Convert recipe to dictionary for template rendering
    recipe_dict = recipe.to_dict()
    
    return render_template('cook_recipe.html', recipe=recipe_dict)

@app.route('/saved_recipes')
def saved_recipes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get filter parameter
    filter_type = request.args.get('filter', 'all')
    
    # Base query for all recipes
    base_query = Recipe.query.filter_by(user_id=session['user_id'])
    
    # Apply filters
    if filter_type == 'liked':
        recipes = base_query.filter_by(liked=True).order_by(Recipe.created_at.desc()).all()
    elif filter_type == 'cooked':
        recipes = base_query.filter_by(cooked=True).order_by(Recipe.created_at.desc()).all()
    else:
        # Show all recipes
        recipes = base_query.order_by(Recipe.created_at.desc()).all()
    
    # Convert recipes to dictionaries for template rendering
    recipes_dict = [recipe.to_dict() for recipe in recipes]
    
    return render_template('saved_recipes.html', recipes=recipes_dict, current_filter=filter_type)

@app.route('/api/recipe/<int:recipe_id>/toggle_cooked', methods=['POST'])
def toggle_cooked(recipe_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    recipe.cooked = not recipe.cooked
    db.session.commit()
    
    return jsonify({'success': True, 'cooked': recipe.cooked})

@app.route('/api/recipe/<int:recipe_id>/toggle_liked', methods=['POST'])
def toggle_liked(recipe_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    recipe.liked = not recipe.liked
    db.session.commit()
    
    return jsonify({'success': True, 'liked': recipe.liked})

@app.route('/api/recipe/<int:recipe_id>/delete', methods=['DELETE'])
def delete_recipe(recipe_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.user_id != session['user_id']:
        return jsonify({'success': False, 'error': 'Access denied'})
    
    try:
        # Delete recipe steps first (due to foreign key constraint)
        RecipeStep.query.filter_by(recipe_id=recipe_id).delete()
        # Delete the recipe
        db.session.delete(recipe)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Recipe deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error deleting recipe: {str(e)}'})

@app.route('/api/recipe/<int:recipe_id>/data')
def get_recipe_data(recipe_id):
    """Get recipe data for desktop app via deep link"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        
        # Convert to dictionary for JSON serialization
        recipe_dict = recipe.to_dict()
        
        return jsonify(recipe_dict)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error fetching recipe: {str(e)}'}), 500

@app.route('/launch_desktop/<int:recipe_id>')
def launch_desktop(recipe_id):
    """Launch desktop app with recipe ID"""
    try:
        import subprocess
        import sys
        from pathlib import Path
        
        # Get the project root directory (parent of web_app)
        project_root = Path(__file__).parent.parent.absolute()
        launcher_path = project_root / "launch_suchef.py"
        
        if launcher_path.exists():
            # Launch the desktop app
            cmd = [sys.executable, str(launcher_path), str(recipe_id)]
            subprocess.Popen(cmd)
            
            return f"""
            <html>
            <head><title>Desktop App Launched</title></head>
            <body>
                <h2>✅ Desktop App Launched!</h2>
                <p>Recipe ID: {recipe_id}</p>
                <p>The Su-Chef desktop app should now be opening with your recipe.</p>
                <p><a href="javascript:window.close()">Close this window</a></p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <head><title>Error</title></head>
            <body>
                <h2>❌ Launcher not found</h2>
                <p>Could not find: {launcher_path}</p>
                <p>Please run manually: <code>python launch_suchef.py {recipe_id}</code></p>
                <p><a href="javascript:window.close()">Close this window</a></p>
            </body>
            </html>
            """
            
    except Exception as e:
        return f"""
        <html>
        <head><title>Error</title></head>
        <body>
            <h2>❌ Error launching desktop app</h2>
            <p>Error: {str(e)}</p>
            <p>Please run manually: <code>python launch_suchef.py {recipe_id}</code></p>
            <p><a href="javascript:window.close()">Close this window</a></p>
        </body>
        </html>
        """

@app.route('/api/voice/speak', methods=['POST'])
def speak_text():
    """Convert text to speech using Azure Speech Services"""
    try:
        # For now, just return success without trying to use Azure Speech Services
        # This will prevent the 500 error and let the browser handle TTS
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Return success - the browser will handle the actual speech synthesis
        return jsonify({
            'success': True, 
            'text': text,
            'message': 'Text ready for browser speech synthesis'
        })
            
    except Exception as e:
        print(f"❌ Error in speak_text endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/voice/cooking_question', methods=['POST'])
def ask_cooking_question():
    """Ask OpenAI a cooking question"""
    try:
        # Debug logging
        print(f"🔍 Cooking question endpoint called")
        print(f"🔍 OpenAI API key exists: {bool(openai.api_key)}")
        print(f"🔍 OpenAI API key length: {len(openai.api_key) if openai.api_key else 0}")
        
        if not openai.api_key:
            print(f"❌ OpenAI API key missing")
            return jsonify({'success': False, 'error': 'OpenAI not configured'}), 400
        
        data = request.get_json()
        question = data.get('question', '')
        recipe_context = data.get('recipe_context', '')
        
        print(f"🔍 Question received: {question}")
        print(f"🔍 Recipe context: {recipe_context}")
        
        if not question:
            print(f"❌ No question provided")
            return jsonify({'success': False, 'error': 'No question provided'}), 400
        
        # Create a context-aware prompt
        system_prompt = """You are a professional chef and cooking instructor. Answer cooking questions clearly, concisely, and helpfully in 2-3 sentences maximum. 
        If a recipe context is provided, focus your answer on the CURRENT STEP that the user is asking about. 
        Always provide practical, actionable advice specific to the current cooking stage. Keep answers brief and to the point."""
        
        user_prompt = f"Recipe context: {recipe_context}\n\nQuestion: {question}\n\nPlease focus your answer on the current step and provide specific guidance for where the user is in their cooking process."
        
        print(f"🔍 Calling OpenAI API...")
        
        # Call OpenAI using the new API format
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,  # Reduced from 300 to make answers shorter
            temperature=0.7
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"✅ OpenAI response received: {answer[:100]}...")
        
        response_data = {
            'success': True,
            'answer': answer,
            'question': question
        }
        print(f"🔍 Sending response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error in cooking question endpoint: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'data': 'Connected to Su-Chef backend'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_user_room')
def handle_join_user_room(data):
    """Join user to their personal room for notifications"""
    user_id = data.get('user_id')
    if user_id:
        join_room(f"user_{user_id}")
        emit('room_joined', {'room': f"user_{user_id}"})

@socketio.on('generate_recipe_ws')
def handle_generate_recipe_ws(data):
    """Handle recipe generation via WebSocket"""
    try:
        # Generate recipe using OpenAI
        recipe_text = generate_recipe_from_openai(data)
        if recipe_text:
            # Parse and save recipe
            recipe_data = parse_recipe_text(recipe_text)
            recipe = Recipe(
                name=recipe_data['name'],
                meal_type=data['meal_type'],
                cooking_time=data['cooking_time'],
                skill_level=data['skill_level'],
                dietary_restrictions=data.get('dietary_restrictions'),
                ingredients=json.dumps(recipe_data['ingredients']),
                user_id=data['user_id']
            )
            
            db.session.add(recipe)
            db.session.flush()  # Get the recipe ID
            
            # Add steps
            for i, step_text in enumerate(recipe_data['steps'], 1):
                step = RecipeStep(
                    recipe_id=recipe.id,
                    step_number=i,
                    step_text=step_text
                )
                db.session.add(step)
            
            db.session.commit()
            
            # Emit success to user's room with full recipe data
            emit('recipe_generated', {
                'success': True, 
                'recipe_id': recipe.id,
                'recipe_name': recipe.name,
                'meal_type': recipe.meal_type,
                'cooking_time': recipe.cooking_time,
                'skill_level': recipe.skill_level,
                'dietary_restrictions': recipe.dietary_restrictions,
                'ingredients': recipe_data['ingredients'],
                'steps': recipe_data['steps'],
                'message': 'Recipe generated successfully!'
            }, room=f"user_{data['user_id']}")
        else:
            emit('recipe_generated', {
                'success': False, 
                'error': 'Failed to generate recipe from OpenAI'
            }, room=f"user_{data['user_id']}")
            
    except Exception as e:
        emit('recipe_generated', {
            'success': False, 
            'error': str(e)
        }, room=f"user_{data['user_id']}")

@socketio.on('cooking_progress')
def handle_cooking_progress(data):
    """Handle cooking progress updates"""
    user_id = data.get('user_id')
    recipe_id = data.get('recipe_id')
    current_step = data.get('current_step')
    total_steps = data.get('total_steps')
    
    if user_id:
        emit('progress_update', {
            'recipe_id': recipe_id,
            'current_step': current_step,
            'total_steps': total_steps,
            'progress': (current_step / total_steps) * 100
        }, room=f"user_{user_id}")

# Helper functions
def generate_recipe_from_openai(data):
    """Generate recipe using OpenAI API"""
    if not openai.api_key:
        return None
    
    prompt = f"""Please suggest a {data['meal_type']} recipe that:
- Takes {data['cooking_time']} minutes or less to prepare
- Is suitable for a {data['skill_level']} cook
"""
    
    if data.get('available_ingredients'):
        prompt += f"- Uses some of these available ingredients: {', '.join(data['available_ingredients'])}\n"
    
    if data.get('dietary_restrictions'):
        prompt += f"\nMust be {data['dietary_restrictions']}"
    
    prompt += """

Please provide the recipe in this format:
Recipe Name: [name]
Cooking Time: [time in minutes]
Ingredients:
- [ingredient 1]
- [ingredient 2]
Instructions:
1. [step 1]
2. [step 2]
"""
    
    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def parse_recipe_text(recipe_text):
    """Parse recipe text into structured data"""
    lines = recipe_text.strip().split('\n')
    recipe_data = {
        'name': '',
        'ingredients': [],
        'steps': []
    }
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('Recipe Name:'):
            recipe_data['name'] = line.replace('Recipe Name:', '').strip()
        elif line.startswith('Ingredients:'):
            current_section = 'ingredients'
        elif line.startswith('Instructions:'):
            current_section = 'steps'
        elif line.startswith('-') and current_section == 'ingredients':
            ingredient = line.replace('-', '').strip()
            if ingredient:
                recipe_data['ingredients'].append(ingredient)
        elif line[0].isdigit() and line[1] == '.' and current_section == 'steps':
            step = line.split('.', 1)[1].strip()
            if step:
                recipe_data['steps'].append(step)
    
    return recipe_data

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)

