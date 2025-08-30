#!/usr/bin/env python3
"""
Services layer for Su-Chef desktop app
Provides clean interface between QML UI and core modules
"""

import os
import json
from typing import Dict, List, Any, Optional, Callable
from dotenv import load_dotenv

from .recipe_generator import get_recipe_from_openai, process_recipe
from .database import RecipeDatabase
from .cooking_agent import CookingAgent


class RecipeService:
    """Service for recipe generation and management"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    def generate(self, preferences: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a recipe based on user preferences"""
        if not self.api_key:
            return {"error": "OpenAI API key not configured"}
            
        # Build prompt from preferences
        prompt = self._build_prompt(preferences)
        
        # Get recipe from OpenAI
        recipe_text = get_recipe_from_openai(prompt, self.api_key)
        if not recipe_text:
            return {"error": "Failed to generate recipe"}
            
        # Process into structured data
        try:
            recipe_data = process_recipe(
                recipe_text,
                preferences.get("meal_type", "dinner"),
                str(preferences.get("time_limit", 30)),
                preferences.get("skill", "beginner"),
                preferences.get("diet", None)
            )
            
            return {
                "success": True,
                "recipe": recipe_data,
                "raw_text": recipe_text
            }
        except Exception as e:
            return {"error": f"Failed to process recipe: {str(e)}"}
    
    def _build_prompt(self, prefs: Dict[str, Any]) -> str:
        """Build recipe generation prompt"""
        meal_type = prefs.get("meal_type", "dinner")
        time_limit = prefs.get("time_limit", 30)
        skill = prefs.get("skill", "beginner")
        diet = prefs.get("diet", None)
        available = prefs.get("available", [])
        
        prompt = f"""Please suggest a {meal_type} recipe that:
- Takes {time_limit} minutes or less to prepare
- Is suitable for a {skill} cook
"""
        
        if available:
            prompt += f"- Uses some of these available ingredients: {', '.join(available)}\n"
        
        if diet:
            prompt += f"\nMust be {diet}"
        
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
        
        return prompt


class DBService:
    """Service for database operations"""
    
    def __init__(self, db_name: str = "su_chef.db"):
        self.db = RecipeDatabase(db_name)
        self.current_user_id = None
    
    def add_user(self, username: str) -> int:
        """Add or get user"""
        self.current_user_id = self.db.add_user(username)
        return self.current_user_id
    
    def save_recipe(self, recipe_data: Dict[str, Any]) -> int:
        """Save recipe to database"""
        if not self.current_user_id:
            raise ValueError("No user logged in")
        return self.db.save_recipe(recipe_data, self.current_user_id)
    
    def get_user_recipes(self, search_type: str = "all") -> List[Any]:
        """Get user's recipes"""
        if not self.current_user_id:
            return []
        
        if search_type == "cooked":
            return self.db.search_recipes(user_id=self.current_user_id, search_type="cooked")
        elif search_type == "liked":
            return self.db.search_recipes(user_id=self.current_user_id, search_type="liked")
        else:
            return self.db.get_user_history(self.current_user_id)
    
    def get_recipe_details(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed recipe information"""
        return self.db.get_recipe_details(recipe_id)
    
    def mark_recipe_cooked(self, recipe_id: int, liked: bool = False):
        """Mark recipe as cooked/liked"""
        if self.current_user_id:
            self.db.mark_recipe_cooked(self.current_user_id, recipe_id, liked)


class CookingService:
    """Service for voice-guided cooking"""
    
    def __init__(self):
        # Load environment variables from parent directory if not found locally
        load_dotenv()
        if not os.getenv("SPEECH_KEY"):
            # Try loading from parent directory
            parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            if os.path.exists(parent_env):
                load_dotenv(parent_env)
        
        self.agent = None
        self.callbacks = {}
        self.current_recipe = None
        self.is_active = False
        
    def set_callbacks(self, **callbacks):
        """Set callback functions for UI updates"""
        self.callbacks = callbacks
        
    def start(self, recipe_data: Dict[str, Any]) -> bool:
        """Start cooking session with recipe - event-driven version"""
        try:
            # Initialize cooking agent with event-driven interface
            if not self.agent:
                self.agent = CookingAgent(test_microphone=False)  # Skip mic test for GUI
                if not hasattr(self.agent, 'speech_key') or not self.agent.speech_key:
                    self._emit_error("Speech services not configured")
                    return False
                
                # Set up callbacks for UI updates
                self.agent.set_ui_callbacks(
                    on_step_change=self._on_step_change,
                    on_status_change=self._on_status_change,
                    on_speech_heard=self._on_speech_heard,
                    on_error=self._on_error
                )
            
            # Prepare recipe for voice guidance
            self._prepare_recipe_for_voice(recipe_data)
            
            # Load recipe data into agent
            if self.agent.load_recipe("steps.json"):
                self.current_recipe = recipe_data
                self.is_active = True
                self._emit_status("Cooking session prepared")
                return True
            else:
                self._emit_error("Failed to load recipe")
                return False
                
        except Exception as e:
            self._emit_error(f"Failed to start cooking: {str(e)}")
            return False
    
    def next(self):
        """Go to next step"""
        if self.agent and self.is_active:
            self.agent.next_step()
    
    def repeat(self):
        """Repeat current step"""
        if self.agent and self.is_active:
            self.agent.repeat_step()
    
    def back(self):
        """Go to previous step"""
        if self.agent and self.is_active:
            self.agent.previous_step()
    
    def stop(self):
        """Stop cooking session"""
        if self.agent:
            self.agent.stop()
        self.is_active = False
        self._emit_status("Cooking session stopped")
    
    def _prepare_recipe_for_voice(self, recipe_data: Dict[str, Any]):
        """Prepare recipe data for voice guidance"""
        steps_data = {
            'recipe_name': recipe_data.get('name', 'Recipe'),
            'ingredients': recipe_data.get('ingredients', []),
            'steps': [
                {'step_number': i+1, 'text': step}
                for i, step in enumerate(recipe_data.get('instructions', []))
            ]
        }
        
        # Save to steps.json for voice agent
        with open('steps.json', 'w') as f:
            json.dump(steps_data, f, indent=4)
    
    def _on_step_change(self, step_index: int):
        """Handle step change"""
        self._emit_callback('on_step_changed', step_index)
    
    def _on_status_change(self, status: str):
        """Handle status change"""
        self._emit_callback('on_status', status)
    
    def _on_speech_heard(self, text: str):
        """Handle speech recognition"""
        self._emit_callback('on_heard', text)
    
    def _on_error(self, error: str):
        """Handle error"""
        self._emit_callback('on_error', error)
    
    def _emit_callback(self, callback_name: str, *args):
        """Emit callback if registered"""
        if callback_name in self.callbacks:
            self.callbacks[callback_name](*args)
    
    def _emit_status(self, status: str):
        """Emit status update"""
        self._emit_callback('on_status', status)
    
    def _emit_error(self, error: str):
        """Emit error"""
        self._emit_callback('on_error', error)
