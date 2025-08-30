#!/usr/bin/env python3
"""
Advanced Learning System for Su-Chef
Demonstrates: Persistent Learning, Skill Progression, Predictive Intelligence
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sqlite3
from dataclasses import dataclass, asdict
import openai

@dataclass
class UserProfile:
    """Comprehensive user profile with learning data."""
    user_id: str
    skill_level: str = "beginner"  # beginner/intermediate/advanced
    cooking_pace: str = "normal"   # slow/normal/fast
    preferred_cuisines: List[str] = None
    dietary_restrictions: List[str] = None
    
    # Learning metrics
    total_recipes_completed: int = 0
    total_cooking_time: float = 0.0
    average_questions_per_recipe: float = 0.0
    confusion_rate: float = 0.0
    
    # Skill progression
    technique_mastery: Dict[str, float] = None  # technique -> confidence score
    ingredient_familiarity: Dict[str, int] = None  # ingredient -> usage count
    timing_accuracy: float = 0.0
    
    # Behavioral patterns
    question_patterns: Dict[str, int] = None
    common_mistakes: List[str] = None
    learning_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferred_cuisines is None:
            self.preferred_cuisines = []
        if self.dietary_restrictions is None:
            self.dietary_restrictions = []
        if self.technique_mastery is None:
            self.technique_mastery = {}
        if self.ingredient_familiarity is None:
            self.ingredient_familiarity = {}
        if self.question_patterns is None:
            self.question_patterns = {}
        if self.common_mistakes is None:
            self.common_mistakes = []
        if self.learning_preferences is None:
            self.learning_preferences = {
                "prefers_detailed_explanations": False,
                "needs_timing_reminders": False,
                "struggles_with_techniques": [],
                "learns_best_with": "visual"  # visual/audio/text
            }

class AdvancedLearningSystem:
    """Advanced learning system with persistence and intelligence."""
    
    def __init__(self, db_path: str = "user_learning.db"):
        self.db_path = db_path
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self._init_database()
    
    def _init_database(self):
        """Initialize persistent learning database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User profiles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            profile_data TEXT,  -- JSON serialized UserProfile
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Cooking sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooking_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            recipe_name TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            questions_asked INTEGER,
            confusion_events INTEGER,
            completion_status TEXT,  -- completed/abandoned/interrupted
            session_data TEXT,  -- JSON with detailed session info
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
        )
        ''')
        
        # Learning events table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            session_id TEXT,
            event_type TEXT,  -- question/mistake/success/confusion
            event_data TEXT,  -- JSON with event details
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    # ========================================================================
    # IMPROVEMENT 1: PERSISTENT USER PROFILES
    # ========================================================================
    
    def load_user_profile(self, user_id: str) -> UserProfile:
        """Load persistent user profile."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT profile_data FROM user_profiles WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            profile_dict = json.loads(result[0])
            return UserProfile(**profile_dict)
        else:
            # Create new profile
            return UserProfile(user_id=user_id)
    
    def save_user_profile(self, profile: UserProfile):
        """Save user profile persistently."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        profile_json = json.dumps(asdict(profile))
        cursor.execute('''
        INSERT OR REPLACE INTO user_profiles (user_id, profile_data, last_updated)
        VALUES (?, ?, ?)
        ''', (profile.user_id, profile_json, datetime.now()))
        
        conn.commit()
        conn.close()
    
    # ========================================================================
    # IMPROVEMENT 2: SKILL PROGRESSION TRACKING
    # ========================================================================
    
    def analyze_skill_progression(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's cooking skill progression over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent sessions
        cursor.execute('''
        SELECT session_data, start_time FROM cooking_sessions 
        WHERE user_id = ? AND start_time > datetime('now', '-30 days')
        ORDER BY start_time
        ''', (user_id,))
        
        sessions = cursor.fetchall()
        conn.close()
        
        if not sessions:
            return {"progression": "insufficient_data"}
        
        # Analyze progression patterns
        progression_data = {
            "sessions_analyzed": len(sessions),
            "skill_improvements": [],
            "areas_needing_work": [],
            "confidence_trends": {},
            "recommendation": ""
        }
        
        # Track question complexity over time
        question_complexity = []
        for session_data, timestamp in sessions:
            session = json.loads(session_data)
            complexity_score = self._calculate_question_complexity(session.get("questions", []))
            question_complexity.append((timestamp, complexity_score))
        
        # Detect skill improvement
        if len(question_complexity) >= 3:
            recent_complexity = sum(score for _, score in question_complexity[-3:]) / 3
            early_complexity = sum(score for _, score in question_complexity[:3]) / 3
            
            if recent_complexity > early_complexity:
                progression_data["skill_improvements"].append("Asking more sophisticated questions")
            elif recent_complexity < early_complexity * 0.8:
                progression_data["skill_improvements"].append("Becoming more independent")
        
        return progression_data
    
    def _calculate_question_complexity(self, questions: List[Dict]) -> float:
        """Calculate complexity score of questions asked."""
        if not questions:
            return 0.0
        
        complexity_weights = {
            "NAVIGATION": 0.1,      # Simple commands
            "REPEAT": 0.2,          # Basic repetition
            "INGREDIENTS": 0.3,     # List requests
            "TIMING": 0.6,          # Time management
            "TECHNIQUE": 0.8,       # Cooking methods
            "SUBSTITUTION": 0.9,    # Creative problem solving
            "TROUBLESHOOTING": 1.0  # Complex problem solving
        }
        
        total_complexity = sum(complexity_weights.get(q.get("intent", ""), 0.5) for q in questions)
        return total_complexity / len(questions)
    
    # ========================================================================
    # IMPROVEMENT 3: PREDICTIVE INTELLIGENCE
    # ========================================================================
    
    def predict_user_needs(self, user_profile: UserProfile, current_recipe: Dict, current_step: int) -> List[str]:
        """Predict what user might need help with."""
        predictions = []
        
        # Based on historical confusion patterns
        if "timing" in user_profile.common_mistakes:
            if any(word in current_recipe["steps"][current_step].lower() for word in ["minutes", "until", "cook"]):
                predictions.append("timing_reminder")
        
        # Based on technique mastery
        current_step_text = current_recipe["steps"][current_step].lower()
        for technique, confidence in user_profile.technique_mastery.items():
            if technique in current_step_text and confidence < 0.6:
                predictions.append(f"technique_help_{technique}")
        
        # Based on ingredient familiarity
        for ingredient in current_recipe.get("ingredients", []):
            ingredient_name = ingredient.split()[0].lower()  # Get base ingredient
            if user_profile.ingredient_familiarity.get(ingredient_name, 0) < 2:
                predictions.append(f"ingredient_guidance_{ingredient_name}")
        
        return predictions
    
    def generate_proactive_suggestions(self, predictions: List[str], user_profile: UserProfile) -> List[str]:
        """Generate proactive suggestions based on predictions."""
        suggestions = []
        
        for prediction in predictions:
            if prediction == "timing_reminder":
                suggestions.append("⏰ Pro tip: Set a timer for this step to avoid overcooking!")
            elif prediction.startswith("technique_help_"):
                technique = prediction.replace("technique_help_", "")
                suggestions.append(f"🔧 Need help with {technique}? I can break it down step by step.")
            elif prediction.startswith("ingredient_guidance_"):
                ingredient = prediction.replace("ingredient_guidance_", "")
                suggestions.append(f"🥕 First time using {ingredient}? Here's what to look for...")
        
        return suggestions
    
    # ========================================================================
    # IMPROVEMENT 4: INTELLIGENT PATTERN RECOGNITION
    # ========================================================================
    
    def analyze_learning_patterns(self, user_id: str) -> Dict[str, Any]:
        """Use AI to analyze complex learning patterns."""
        if not self.openai_key:
            return {"error": "OpenAI key not available"}
        
        # Get user's learning history
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT event_data FROM learning_events 
        WHERE user_id = ? AND timestamp > datetime('now', '-30 days')
        ORDER BY timestamp
        ''', (user_id,))
        
        events = [json.loads(row[0]) for row in cursor.fetchall()]
        conn.close()
        
        if not events:
            return {"patterns": "insufficient_data"}
        
        try:
            client = openai.OpenAI(api_key=self.openai_key)
            
            # Prepare learning data for AI analysis
            learning_data = {
                "total_events": len(events),
                "question_types": [e.get("intent") for e in events if e.get("intent")],
                "confusion_triggers": [e.get("trigger") for e in events if e.get("type") == "confusion"],
                "success_patterns": [e.get("context") for e in events if e.get("type") == "success"]
            }
            
            analysis_prompt = f"""
Analyze this cooking learning data and identify patterns:

Learning Data: {json.dumps(learning_data, indent=2)}

Identify:
1. Learning strengths (what user does well)
2. Learning gaps (areas needing improvement)
3. Optimal learning strategies for this user
4. Personalized recommendations

Respond in JSON format:
{{
    "strengths": ["strength1", "strength2"],
    "gaps": ["gap1", "gap2"],
    "learning_style": "visual/auditory/kinesthetic",
    "recommendations": ["rec1", "rec2"],
    "confidence_level": "beginner/intermediate/advanced"
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert learning analyst specializing in cooking education. Analyze learning patterns and provide insights."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}
    
    # ========================================================================
    # IMPROVEMENT 5: ADAPTIVE DIFFICULTY
    # ========================================================================
    
    def adjust_guidance_level(self, user_profile: UserProfile, recipe_complexity: str) -> Dict[str, Any]:
        """Adjust guidance level based on user skill and recipe complexity."""
        
        # Calculate user competence score
        competence_factors = {
            "skill_level": {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.9},
            "completion_rate": min(user_profile.total_recipes_completed / 10, 1.0),
            "confusion_rate": 1.0 - min(user_profile.confusion_rate, 1.0),
            "technique_mastery": sum(user_profile.technique_mastery.values()) / max(len(user_profile.technique_mastery), 1)
        }
        
        competence_score = sum(competence_factors.values()) / len(competence_factors)
        
        # Recipe complexity mapping
        complexity_scores = {"easy": 0.3, "medium": 0.6, "hard": 0.9}
        recipe_score = complexity_scores.get(recipe_complexity, 0.6)
        
        # Determine guidance level
        guidance_ratio = recipe_score / max(competence_score, 0.1)
        
        if guidance_ratio > 1.5:
            guidance_level = "high"
            features = ["detailed_explanations", "proactive_tips", "frequent_check_ins"]
        elif guidance_ratio > 1.0:
            guidance_level = "medium"
            features = ["standard_explanations", "occasional_tips"]
        else:
            guidance_level = "low"
            features = ["minimal_guidance", "on_demand_help"]
        
        return {
            "guidance_level": guidance_level,
            "features": features,
            "competence_score": competence_score,
            "recipe_complexity": recipe_score,
            "explanation": f"User competence: {competence_score:.2f}, Recipe complexity: {recipe_score:.2f}"
        }
    
    # ========================================================================
    # IMPROVEMENT 6: CROSS-RECIPE LEARNING
    # ========================================================================
    
    def extract_transferable_knowledge(self, completed_recipes: List[Dict]) -> Dict[str, Any]:
        """Extract knowledge that transfers across recipes."""
        
        transferable_knowledge = {
            "mastered_techniques": [],
            "familiar_ingredients": [],
            "timing_patterns": {},
            "common_substitutions": {},
            "preferred_methods": []
        }
        
        # Analyze techniques across recipes
        technique_frequency = {}
        for recipe in completed_recipes:
            for step in recipe.get("steps", []):
                techniques = self._extract_techniques_from_step(step)
                for technique in techniques:
                    technique_frequency[technique] = technique_frequency.get(technique, 0) + 1
        
        # Mark frequently used techniques as mastered
        for technique, frequency in technique_frequency.items():
            if frequency >= 3:  # Used in 3+ recipes
                transferable_knowledge["mastered_techniques"].append(technique)
        
        return transferable_knowledge
    
    def _extract_techniques_from_step(self, step_text: str) -> List[str]:
        """Extract cooking techniques from step text."""
        techniques = []
        technique_keywords = {
            "sauté": ["sauté", "sautéing", "sauteed"],
            "chop": ["chop", "chopping", "chopped", "dice", "dicing"],
            "boil": ["boil", "boiling", "boiled"],
            "fry": ["fry", "frying", "fried"],
            "bake": ["bake", "baking", "baked"],
            "grill": ["grill", "grilling", "grilled"],
            "steam": ["steam", "steaming", "steamed"],
            "roast": ["roast", "roasting", "roasted"]
        }
        
        step_lower = step_text.lower()
        for technique, keywords in technique_keywords.items():
            if any(keyword in step_lower for keyword in keywords):
                techniques.append(technique)
        
        return techniques

# ========================================================================
# INTEGRATION EXAMPLE
# ========================================================================

def integrate_with_cooking_agent():
    """Example of how to integrate advanced learning with cooking agent."""
    
    learning_system = AdvancedLearningSystem()
    
    # Load user profile
    user_profile = learning_system.load_user_profile("user123")
    
    # Analyze skill progression
    progression = learning_system.analyze_skill_progression("user123")
    print(f"Skill progression: {progression}")
    
    # Predict user needs for current recipe
    current_recipe = {
        "name": "Pasta Carbonara",
        "steps": ["Heat pan", "Cook pasta", "Mix eggs and cheese", "Combine carefully"],
        "ingredients": ["pasta", "eggs", "cheese", "bacon"]
    }
    
    predictions = learning_system.predict_user_needs(user_profile, current_recipe, 2)
    suggestions = learning_system.generate_proactive_suggestions(predictions, user_profile)
    
    print(f"Proactive suggestions: {suggestions}")
    
    # Adjust guidance level
    guidance = learning_system.adjust_guidance_level(user_profile, "medium")
    print(f"Guidance level: {guidance}")

if __name__ == "__main__":
    integrate_with_cooking_agent() 