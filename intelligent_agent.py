#!/usr/bin/env python3
"""
Intelligent Cooking Agent - Enhanced version with advanced AI capabilities
Demonstrates: Intent Recognition, Context Management, Learning, Proactive Intelligence
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
import openai
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

class IntelligentCookingAgent:
    """Advanced cooking agent with enhanced AI capabilities."""
    
    def __init__(self):
        load_dotenv()
        
        # API Configuration
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.speech_key = os.getenv("SPEECH_KEY")
        self.speech_region = os.getenv("SPEECH_REGION", "westeurope")
        
        # Cooking State
        self.current_step = 0
        self.recipe_steps = []
        self.recipe_ingredients = []
        self.recipe_name = ""
        self.is_interrupted = False
        
        # ENHANCED: User Model & Learning
        self.user_model = {
            "cooking_pace": "normal",  # slow/normal/fast
            "question_patterns": {},   # track common question types
            "skill_progression": [],   # track improvement over time
            "preferences": {},         # learned preferences
            "session_history": []      # conversation memory
        }
        
        # ENHANCED: Context Management
        self.cooking_context = {
            "session_start": datetime.now(),
            "step_timings": [],        # how long each step takes
            "questions_asked": [],     # conversation history
            "confusion_indicators": 0,  # track when user seems confused
            "proactive_suggestions": []  # suggestions made
        }
        
        # Initialize services
        self._init_speech_services()
        
    def _init_speech_services(self):
        """Initialize Azure Speech Services."""
        if not self.speech_key:
            print("❌ Azure Speech key missing")
            return
            
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.speech_region
        )
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyMultilingualNeural"
        
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
        self.recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)
    
    # ========================================================================
    # ENHANCEMENT 1: INTELLIGENT INTENT RECOGNITION
    # ========================================================================
    
    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """Advanced intent classification using OpenAI."""
        try:
            client = openai.OpenAI(api_key=self.openai_key)
            
            # Enhanced prompt for intent classification
            classification_prompt = f"""
Analyze this cooking assistant user input and classify the intent:

User Input: "{user_input}"
Current Cooking Context:
- Recipe: {self.recipe_name}
- Current Step: {self.current_step + 1}/{len(self.recipe_steps)}
- Step Text: {self.recipe_steps[self.current_step] if self.current_step < len(self.recipe_steps) else "Complete"}

Classify into ONE of these intents and provide confidence:
1. NAVIGATION (next, back, skip, go to step X)
2. CLARIFICATION (what, how, why, explain)
3. TIMING (how long, when ready, is it done)
4. SUBSTITUTION (replace ingredient, alternative)
5. TECHNIQUE (how to chop, what temperature, cooking method)
6. TROUBLESHOOTING (help, stuck, not working, burned)
7. REPEAT (say again, repeat step)
8. INGREDIENTS (list ingredients, what do I need)
9. STOP (quit, end, stop cooking)
10. GENERAL_QUESTION (other cooking questions)

Respond in JSON format:
{{
    "intent": "INTENT_NAME",
    "confidence": 0.95,
    "entities": ["extracted", "key", "words"],
    "urgency": "low/medium/high",
    "requires_immediate_action": true/false
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert intent classifier for cooking assistants. Always respond with valid JSON."},
                    {"role": "user", "content": classification_prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            intent_data = json.loads(response.choices[0].message.content)
            
            # Log for learning
            self.cooking_context["questions_asked"].append({
                "timestamp": datetime.now().isoformat(),
                "input": user_input,
                "intent": intent_data,
                "step": self.current_step
            })
            
            return intent_data
            
        except Exception as e:
            print(f"❌ Intent classification error: {e}")
            # Fallback to simple classification
            return self._simple_intent_fallback(user_input)
    
    def _simple_intent_fallback(self, user_input: str) -> Dict[str, Any]:
        """Fallback intent classification."""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['next', 'continue', 'proceed']):
            return {"intent": "NAVIGATION", "confidence": 0.8, "entities": ["next"]}
        elif any(word in user_lower for word in ['repeat', 'again']):
            return {"intent": "REPEAT", "confidence": 0.8, "entities": ["repeat"]}
        elif any(word in user_lower for word in ['stop', 'quit', 'end']):
            return {"intent": "STOP", "confidence": 0.8, "entities": ["stop"]}
        else:
            return {"intent": "GENERAL_QUESTION", "confidence": 0.5, "entities": []}
    
    # ========================================================================
    # ENHANCEMENT 2: ADVANCED CONTEXT MANAGEMENT
    # ========================================================================
    
    def build_rich_context(self, user_input: str, intent_data: Dict) -> Dict[str, Any]:
        """Build comprehensive context for AI responses."""
        
        # Calculate cooking progress
        progress_percent = (self.current_step / len(self.recipe_steps)) * 100 if self.recipe_steps else 0
        
        # Analyze user patterns
        recent_questions = self.cooking_context["questions_asked"][-3:]
        question_types = [q["intent"]["intent"] for q in recent_questions]
        
        # Detect confusion patterns
        confusion_indicators = self._detect_confusion_patterns(recent_questions)
        
        # Build rich context
        rich_context = {
            "recipe_info": {
                "name": self.recipe_name,
                "total_steps": len(self.recipe_steps),
                "current_step": self.current_step + 1,
                "current_instruction": self.recipe_steps[self.current_step] if self.current_step < len(self.recipe_steps) else "Complete",
                "progress_percent": round(progress_percent, 1),
                "ingredients": self.recipe_ingredients
            },
            "user_context": {
                "cooking_pace": self.user_model["cooking_pace"],
                "recent_question_types": question_types,
                "confusion_level": confusion_indicators,
                "session_duration": str(datetime.now() - self.cooking_context["session_start"]),
                "questions_this_session": len(self.cooking_context["questions_asked"])
            },
            "current_interaction": {
                "user_input": user_input,
                "classified_intent": intent_data,
                "urgency": intent_data.get("urgency", "low"),
                "requires_action": intent_data.get("requires_immediate_action", False)
            },
            "cooking_intelligence": {
                "next_steps_preview": self.recipe_steps[self.current_step+1:self.current_step+3] if self.current_step+1 < len(self.recipe_steps) else [],
                "estimated_remaining_time": self._estimate_remaining_time(),
                "potential_issues": self._predict_potential_issues(),
                "proactive_tips": self._generate_proactive_tips()
            }
        }
        
        return rich_context
    
    def _detect_confusion_patterns(self, recent_questions: List[Dict]) -> str:
        """Detect if user seems confused based on question patterns."""
        if len(recent_questions) < 2:
            return "none"
        
        # Check for repeated clarification requests
        clarification_count = sum(1 for q in recent_questions if q["intent"]["intent"] == "CLARIFICATION")
        repeat_count = sum(1 for q in recent_questions if q["intent"]["intent"] == "REPEAT")
        
        if clarification_count >= 2 or repeat_count >= 2:
            return "high"
        elif clarification_count >= 1 or repeat_count >= 1:
            return "medium"
        else:
            return "low"
    
    def _estimate_remaining_time(self) -> str:
        """Estimate remaining cooking time."""
        remaining_steps = len(self.recipe_steps) - self.current_step
        avg_time_per_step = 3  # minutes - could be learned from user data
        estimated_minutes = remaining_steps * avg_time_per_step
        return f"{estimated_minutes} minutes"
    
    def _predict_potential_issues(self) -> List[str]:
        """Predict potential cooking issues based on current step."""
        if self.current_step >= len(self.recipe_steps):
            return []
        
        current_instruction = self.recipe_steps[self.current_step].lower()
        issues = []
        
        if "heat" in current_instruction or "temperature" in current_instruction:
            issues.append("temperature_control")
        if "time" in current_instruction or "minutes" in current_instruction:
            issues.append("timing_critical")
        if "mix" in current_instruction or "stir" in current_instruction:
            issues.append("technique_sensitive")
        
        return issues
    
    def _generate_proactive_tips(self) -> List[str]:
        """Generate proactive cooking tips."""
        if self.current_step >= len(self.recipe_steps):
            return []
        
        current_instruction = self.recipe_steps[self.current_step].lower()
        tips = []
        
        if "oil" in current_instruction and self.current_step == 0:
            tips.append("Make sure your pan is properly heated before adding oil")
        if "onion" in current_instruction:
            tips.append("Cut onions just before cooking to prevent them from getting soggy")
        
        return tips
    
    # ========================================================================
    # ENHANCEMENT 3: LEARNING CAPABILITIES
    # ========================================================================
    
    def learn_from_interaction(self, user_input: str, ai_response: str, user_feedback: Optional[str] = None):
        """Learn from user interactions to improve future responses."""
        
        # Track question patterns
        intent = self.classify_intent(user_input)["intent"]
        if intent in self.user_model["question_patterns"]:
            self.user_model["question_patterns"][intent] += 1
        else:
            self.user_model["question_patterns"][intent] = 1
        
        # Learn cooking pace
        if intent == "NAVIGATION" and user_input.lower() in ["next", "continue"]:
            step_duration = self._calculate_step_duration()
            self.cooking_context["step_timings"].append(step_duration)
            self._update_cooking_pace()
        
        # Store interaction for future learning
        interaction_record = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response,
            "user_feedback": user_feedback,
            "step": self.current_step,
            "intent": intent
        }
        
        self.user_model["session_history"].append(interaction_record)
        
        # Limit history size
        if len(self.user_model["session_history"]) > 50:
            self.user_model["session_history"] = self.user_model["session_history"][-50:]
    
    def _calculate_step_duration(self) -> float:
        """Calculate how long user spent on current step."""
        if not self.cooking_context["step_timings"]:
            return 180.0  # Default 3 minutes
        
        # Simple calculation - in real implementation, track step start times
        return 180.0  # Placeholder
    
    def _update_cooking_pace(self):
        """Update user's cooking pace based on step timings."""
        if len(self.cooking_context["step_timings"]) < 3:
            return
        
        avg_time = sum(self.cooking_context["step_timings"]) / len(self.cooking_context["step_timings"])
        
        if avg_time < 120:  # Less than 2 minutes per step
            self.user_model["cooking_pace"] = "fast"
        elif avg_time > 300:  # More than 5 minutes per step
            self.user_model["cooking_pace"] = "slow"
        else:
            self.user_model["cooking_pace"] = "normal"
    
    # ========================================================================
    # ENHANCED AI RESPONSE GENERATION
    # ========================================================================
    
    def get_intelligent_response(self, user_input: str) -> Optional[str]:
        """Generate intelligent, context-aware responses."""
        
        # Step 1: Classify intent
        intent_data = self.classify_intent(user_input)
        
        # Step 2: Handle direct actions
        if intent_data["intent"] == "NAVIGATION":
            return self._handle_navigation(intent_data)
        elif intent_data["intent"] == "REPEAT":
            return self._handle_repeat()
        elif intent_data["intent"] == "STOP":
            self.is_interrupted = True
            return "Ending cooking session. Great job!"
        
        # Step 3: Build rich context for complex queries
        rich_context = self.build_rich_context(user_input, intent_data)
        
        # Step 4: Generate intelligent response
        try:
            client = openai.OpenAI(api_key=self.openai_key)
            
            enhanced_prompt = f"""
You are an intelligent cooking assistant with deep context awareness. 

RICH CONTEXT:
{json.dumps(rich_context, indent=2)}

RESPONSE GUIDELINES:
- Use the rich context to provide highly relevant, personalized advice
- Consider the user's cooking pace ({rich_context['user_context']['cooking_pace']})
- Address their confusion level ({rich_context['user_context']['confusion_level']})
- Be proactive if you detect potential issues
- Reference specific steps, ingredients, and timing when relevant
- Keep responses under 60 words but make them intelligent and helpful

USER QUESTION: "{user_input}"

Provide an intelligent, context-aware response:
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert cooking assistant with advanced context awareness and learning capabilities."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.7,
                max_tokens=80
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Learn from this interaction
            self.learn_from_interaction(user_input, ai_response)
            
            return ai_response
            
        except Exception as e:
            print(f"❌ AI Response Error: {e}")
            return "I'm having trouble processing that. Could you rephrase your question?"
    
    def _handle_navigation(self, intent_data: Dict) -> Optional[str]:
        """Handle navigation commands intelligently."""
        if "next" in intent_data.get("entities", []):
            self.current_step += 1
            
            # Proactive intelligence
            if self.current_step < len(self.recipe_steps):
                next_step = self.recipe_steps[self.current_step]
                
                # Check if next step needs preparation
                if "preheat" in next_step.lower():
                    return "Moving to next step. Pro tip: Start preheating now as it takes time!"
                elif "chop" in next_step.lower() or "cut" in next_step.lower():
                    return "Next step involves cutting. Make sure your knife is sharp for safety!"
            
            return None  # Let main loop handle step announcement
        
        return "I didn't understand that navigation command."
    
    def _handle_repeat(self) -> str:
        """Handle repeat requests intelligently."""
        if self.current_step < len(self.recipe_steps):
            step_text = f"Step {self.current_step + 1}: {self.recipe_steps[self.current_step]}"
            
            # Add helpful context based on user's confusion level
            confusion = self.cooking_context.get("confusion_indicators", 0)
            if confusion > 2:
                return f"{step_text}\n\nTake your time with this step. Would you like me to break it down further?"
            else:
                return step_text
        
        return "We've completed all steps!"
    
    # ========================================================================
    # BASIC FUNCTIONALITY (simplified from original)
    # ========================================================================
    
    def speak(self, text: str) -> bool:
        """Text-to-speech."""
        if not self.speech_key:
            print(f"🔊 {text}")
            return True
        
        try:
            result = self.synthesizer.speak_text_async(text).get()
            return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted
        except:
            print(f"🔊 {text}")
            return False
    
    def listen(self) -> Optional[str]:
        """Speech-to-text with fallback."""
        if not self.speech_key:
            return input("Type your response: ").strip()
        
        try:
            result = self.recognizer.recognize_once_async().get()
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text.strip()
        except:
            pass
        
        # Fallback to text
        return input("Voice not detected. Type your response: ").strip()
    
    def load_recipe(self, filename: str = "steps.json") -> bool:
        """Load recipe from JSON file."""
        try:
            with open(filename, 'r') as f:
                recipe_data = json.load(f)
                self.recipe_name = recipe_data.get("recipe_name", "Unknown Recipe")
                self.recipe_steps = [step["text"] for step in recipe_data.get("steps", [])]
                self.recipe_ingredients = recipe_data.get("ingredients", [])
                return True
        except:
            print("❌ Could not load recipe file")
            return False
    
    def run(self):
        """Main intelligent cooking loop."""
        if not self.load_recipe():
            return
        
        print(f"\n🧠 Starting INTELLIGENT cooking guide for: {self.recipe_name}")
        self.speak(f"Hi! I'm your intelligent cooking assistant. I'll learn from our interaction and provide personalized guidance for {self.recipe_name}.")
        
        while not self.is_interrupted and self.current_step < len(self.recipe_steps):
            # Announce current step
            step_text = f"Step {self.current_step + 1}: {self.recipe_steps[self.current_step]}"
            print(f"\n{step_text}")
            self.speak(step_text)
            
            # Add proactive suggestions
            tips = self._generate_proactive_tips()
            if tips:
                tip = tips[0]  # Show first tip
                print(f"💡 Tip: {tip}")
                self.speak(f"Tip: {tip}")
            
            print("Say 'next' when ready, or ask any question...")
            
            # Get user input
            user_input = self.listen()
            if not user_input:
                continue
            
            # Process with intelligent response
            response = self.get_intelligent_response(user_input)
            if response:
                print(f"\n🧠 Assistant: {response}")
                self.speak(response)
        
        if not self.is_interrupted:
            print("\n🎉 Recipe completed!")
            self.speak("Congratulations! You've completed the recipe. I've learned from our session to help you better next time!")
            
            # Show learning summary
            self._show_learning_summary()
    
    def _show_learning_summary(self):
        """Show what the agent learned during the session."""
        print(f"\n📊 Learning Summary:")
        print(f"• Your cooking pace: {self.user_model['cooking_pace']}")
        print(f"• Questions asked: {len(self.cooking_context['questions_asked'])}")
        print(f"• Most common question type: {max(self.user_model['question_patterns'], key=self.user_model['question_patterns'].get) if self.user_model['question_patterns'] else 'None'}")

if __name__ == "__main__":
    agent = IntelligentCookingAgent()
    agent.run() 