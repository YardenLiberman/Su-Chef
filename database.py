import sqlite3
from datetime import datetime
import json
import os
import shutil

class RecipeDatabase:
    def __init__(self, db_name="recipe_history.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.recipes_dir = "recipes"
        self._ensure_recipe_directory()
    
    def _ensure_recipe_directory(self):
        """Ensure the recipes directory exists"""
        if not os.path.exists(self.recipes_dir):
            os.makedirs(self.recipes_dir)
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create recipes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            cooking_time INTEGER,
            skill_level TEXT,
            dietary_restrictions TEXT,
            ingredients TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, created_at)
        )
        ''')
        
        # Create steps table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS steps (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            step_number INTEGER NOT NULL,
            step_text TEXT NOT NULL,
            estimated_time INTEGER,
            tips TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id),
            UNIQUE(recipe_id, step_number)
        )
        ''')
        
        # Create user_recipe_history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_recipe_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            recipe_id INTEGER,
            cooked BOOLEAN DEFAULT FALSE,
            liked BOOLEAN DEFAULT FALSE,
            cooked_date TIMESTAMP,
            last_step_completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id)
        )
        ''')
        
        # Create user_preferences table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            meal_type TEXT,
            cooking_time_preference INTEGER,
            skill_level TEXT,
            dietary_restrictions TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        self.conn.commit()
    
    def add_user(self, username):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # User already exists, return their ID
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            return cursor.fetchone()[0]
    
    def save_recipe(self, recipe_data, user_id):
        cursor = self.conn.cursor()
        
        # Save recipe
        cursor.execute('''
        INSERT INTO recipes (name, meal_type, cooking_time, skill_level, 
                           dietary_restrictions, ingredients)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            recipe_data['name'],
            recipe_data['meal_type'],
            recipe_data['cooking_time'],
            recipe_data['skill_level'],
            recipe_data['dietary_restrictions'],
            json.dumps(recipe_data['ingredients'])
        ))
        
        recipe_id = cursor.lastrowid
        
        # Save steps
        for step_num, step_text in enumerate(recipe_data['instructions'], 1):
            cursor.execute('''
            INSERT INTO steps (recipe_id, step_number, step_text)
            VALUES (?, ?, ?)
            ''', (recipe_id, step_num, step_text))
        
        # Add to user's history
        cursor.execute('''
        INSERT INTO user_recipe_history (user_id, recipe_id, cooked_date)
        VALUES (?, ?, ?)
        ''', (user_id, recipe_id, datetime.now()))
        
        self.conn.commit()
        
        # Create recipe directory and save files
        self._save_recipe_files(recipe_id, recipe_data)
        
        return recipe_id
    
    def _save_recipe_files(self, recipe_id, recipe_data):
        """Save recipe data to organized files"""
        recipe_dir = os.path.join(self.recipes_dir, str(recipe_id))
        if not os.path.exists(recipe_dir):
            os.makedirs(recipe_dir)
        
        # Save complete recipe
        with open(os.path.join(recipe_dir, 'recipe.json'), 'w') as f:
            json.dump(recipe_data, f, indent=4)
        
        # Save steps only (TTS optimized)
        steps_data = {
            'recipe_name': recipe_data['name'],
            'steps': [
                {'step_number': i+1, 'text': step}
                for i, step in enumerate(recipe_data['instructions'])
            ]
        }
        with open(os.path.join(recipe_dir, 'steps.json'), 'w') as f:
            json.dump(steps_data, f, indent=4)
        
        # Save metadata
        metadata = {
            'name': recipe_data['name'],
            'meal_type': recipe_data['meal_type'],
            'cooking_time': recipe_data['cooking_time'],
            'skill_level': recipe_data['skill_level'],
            'dietary_restrictions': recipe_data['dietary_restrictions'],
            'total_steps': len(recipe_data['instructions'])
        }
        with open(os.path.join(recipe_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=4)


    
    def search_recipes(self, query=None, user_id=None, search_type='name'):
        """
        Search recipes by name or user history
        search_type can be: 'name', 'cooked', 'liked'
        """
        cursor = self.conn.cursor()
        
        if search_type == 'name':
            cursor.execute('''
            SELECT r.*, COUNT(s.step_id) as total_steps
            FROM recipes r
            LEFT JOIN steps s ON r.recipe_id = s.recipe_id
            WHERE r.name LIKE ?
            GROUP BY r.recipe_id
            ORDER BY r.created_at DESC
            ''', (f'%{query}%',))
            
        elif search_type in ['cooked', 'liked']:
            filter_condition = 'cooked = TRUE' if search_type == 'cooked' else 'liked = TRUE'
            cursor.execute(f'''
            SELECT r.*, COUNT(s.step_id) as total_steps
            FROM recipes r
            JOIN user_recipe_history urh ON r.recipe_id = urh.recipe_id
            LEFT JOIN steps s ON r.recipe_id = s.recipe_id
            WHERE urh.user_id = ? AND {filter_condition}
            GROUP BY r.recipe_id
            ORDER BY urh.cooked_date DESC
            ''', (user_id,))
        
        return cursor.fetchall()
    
    def get_recipe_details(self, recipe_id):
        """Get complete recipe details including steps"""
        cursor = self.conn.cursor()
        
        # Get basic recipe info
        cursor.execute('''
        SELECT r.*, COUNT(s.step_id) as total_steps
        FROM recipes r
        LEFT JOIN steps s ON r.recipe_id = s.recipe_id
        WHERE r.recipe_id = ?
        GROUP BY r.recipe_id
        ''', (recipe_id,))
        recipe = cursor.fetchone()
        
        if not recipe:
            return None
        
        # Get steps
        cursor.execute('''
        SELECT step_number, step_text, estimated_time, tips
        FROM steps
        WHERE recipe_id = ?
        ORDER BY step_number
        ''', (recipe_id,))
        steps = cursor.fetchall()
        
        return {
            'recipe': recipe,
            'steps': steps
        }
    
    def mark_recipe_cooked(self, user_id, recipe_id, liked=False):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE user_recipe_history 
        SET cooked = TRUE, liked = ?, cooked_date = ?
        WHERE user_id = ? AND recipe_id = ?
        ''', (liked, datetime.now(), user_id, recipe_id))
        self.conn.commit()
    
    def get_user_history(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT r.*, urh.cooked, urh.liked, urh.cooked_date
        FROM recipes r
        JOIN user_recipe_history urh ON r.recipe_id = urh.recipe_id
        WHERE urh.user_id = ?
        ORDER BY urh.cooked_date DESC
        ''', (user_id,))
        return cursor.fetchall()
    

    
    def close(self):
        self.conn.close() 