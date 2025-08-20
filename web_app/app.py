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
from datetime import datetime

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

# Simple recipe generation functions
def generate_demo_recipe(meal_type, cooking_time, skill_level, dietary_restrictions, available_ingredients=None):
    """Generate a demo recipe for testing purposes"""
    
    import random
    
    # Breakfast recipes
    breakfast_recipes = [
        {
            "name": "Quick Breakfast Burrito",
            "ingredients": [
                "2 large eggs",
                "1/4 cup shredded cheese", 
                "1 small tortilla",
                "1/4 cup black beans",
                "Salsa to taste"
            ],
            "steps": [
                "Scramble eggs in a pan over medium heat",
                "Warm tortilla in a dry pan for 30 seconds",
                "Add eggs to tortilla and top with cheese",
                "Add beans and salsa, then roll up tightly",
                "Serve immediately and enjoy!"
            ]
        },
        {
            "name": "Overnight Oats with Berries",
            "ingredients": [
                "1/2 cup rolled oats",
                "1/2 cup milk or almond milk",
                "1 tbsp honey",
                "1/4 cup mixed berries",
                "1 tbsp chopped nuts"
            ],
            "steps": [
                "Mix oats, milk, and honey in a jar",
                "Refrigerate overnight (or at least 4 hours)",
                "Top with fresh berries and chopped nuts",
                "Stir gently and enjoy cold or warm"
            ]
        },
        {
            "name": "Greek Yogurt Parfait",
            "ingredients": [
                "1 cup Greek yogurt",
                "2 tbsp granola",
                "1/4 cup fresh fruit",
                "1 tbsp honey",
                "1 tbsp chopped almonds"
            ],
            "steps": [
                "Layer half the yogurt in a glass",
                "Add granola and fruit",
                "Top with remaining yogurt",
                "Drizzle with honey and sprinkle almonds"
            ]
        }
    ]
    
    # Lunch recipes
    lunch_recipes = [
        {
            "name": "Mediterranean Salad",
            "ingredients": [
                "Mixed greens (2 cups)",
                "Cherry tomatoes (1/2 cup)",
                "Cucumber (1/2 cup, diced)",
                "Red onion (1/4 cup, thinly sliced)",
                "Feta cheese (1/4 cup, crumbled)",
                "Olive oil (2 tbsp)",
                "Lemon juice (1 tbsp)"
            ],
            "steps": [
                "Wash and chop all vegetables",
                "Combine greens, tomatoes, cucumber, and onion in a large bowl",
                "Sprinkle feta cheese on top",
                "Dress with olive oil and lemon juice",
                "Toss gently and serve immediately"
            ]
        },
        {
            "name": "Quinoa Buddha Bowl",
            "ingredients": [
                "1/2 cup quinoa, cooked",
                "1/2 cup chickpeas",
                "1 cup roasted vegetables",
                "2 tbsp tahini dressing",
                "Fresh herbs for garnish"
            ],
            "steps": [
                "Cook quinoa according to package directions",
                "Arrange quinoa in a bowl",
                "Add chickpeas and roasted vegetables",
                "Drizzle with tahini dressing",
                "Garnish with fresh herbs"
            ]
        },
        {
            "name": "Caprese Sandwich",
            "ingredients": [
                "2 slices whole grain bread",
                "Fresh mozzarella (2 oz)",
                "2-3 tomato slices",
                "Fresh basil leaves",
                "Balsamic glaze",
                "Olive oil"
            ],
            "steps": [
                "Toast bread lightly",
                "Layer mozzarella, tomatoes, and basil",
                "Drizzle with balsamic glaze and olive oil",
                "Close sandwich and cut diagonally"
            ]
        }
    ]
    
    # Dinner recipes
    dinner_recipes = [
        {
            "name": "Simple Pasta Dish",
            "ingredients": [
                "8 oz pasta of your choice",
                "2 tbsp olive oil",
                "2 cloves garlic, minced",
                "Salt and pepper to taste",
                "1/4 cup Parmesan cheese, grated"
            ],
            "steps": [
                "Bring a large pot of salted water to boil",
                "Cook pasta according to package directions",
                "Heat olive oil in a pan over medium heat",
                "Sauté minced garlic until fragrant (30 seconds)",
                "Toss cooked pasta with oil and garlic mixture",
                "Season with salt and pepper, top with cheese"
            ]
        },
        {
            "name": "Sheet Pan Chicken and Vegetables",
            "ingredients": [
                "2 chicken breasts",
                "2 cups mixed vegetables",
                "2 tbsp olive oil",
                "Herbs and spices",
                "Salt and pepper"
            ],
            "steps": [
                "Preheat oven to 400°F (200°C)",
                "Season chicken and vegetables with oil and spices",
                "Arrange on a sheet pan",
                "Bake for 25-30 minutes until chicken is cooked",
                "Let rest for 5 minutes before serving"
            ]
        },
        {
            "name": "Stir-Fry with Rice",
            "ingredients": [
                "1 cup cooked rice",
                "2 cups mixed vegetables",
                "2 tbsp soy sauce",
                "1 tbsp sesame oil",
                "2 cloves garlic, minced"
            ],
            "steps": [
                "Heat sesame oil in a wok or large pan",
                "Stir-fry vegetables until crisp-tender",
                "Add garlic and cook for 30 seconds",
                "Add rice and soy sauce",
                "Toss everything together and serve hot"
            ]
        }
    ]
    
    # Select recipe based on meal type
    if "breakfast" in meal_type.lower():
        recipe_data = random.choice(breakfast_recipes)
    elif "lunch" in meal_type.lower():
        recipe_data = random.choice(lunch_recipes)
    else:
        recipe_data = random.choice(dinner_recipes)
    
    # Create the recipe object
    recipe = {
        "name": recipe_data["name"],
        "meal_type": meal_type,
        "cooking_time": cooking_time,
        "skill_level": skill_level,
        "ingredients": recipe_data["ingredients"],
        "steps": recipe_data["steps"]
    }
    
    # Add dietary restrictions note if specified
    if dietary_restrictions:
        recipe["dietary_note"] = f"Adapted for {dietary_restrictions} diet"
    
    # Add available ingredients note if specified
    if available_ingredients:
        recipe["ingredients_note"] = f"Using available ingredients: {', '.join(available_ingredients)}"
    
    return recipe

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
    """Generate recipe based on user preferences"""
    data = request.get_json()
    
    try:
        # Generate demo recipe
        recipe_data = generate_demo_recipe(
            meal_type=data['meal_type'],
            cooking_time=data['cooking_time'],
            skill_level=data['skill_level'],
            dietary_restrictions=data.get('dietary_restrictions'),
            available_ingredients=data.get('available_ingredients')
        )
        
        return jsonify({
            'success': True,
            'recipe': recipe_data
        })
    except Exception as e:
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
