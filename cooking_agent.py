import json
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import openai
from typing import Optional, Dict, List, Any

class CookingAgent:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Azure Speech Service configuration
        self.speech_key = os.getenv("SPEECH_KEY")
        self.speech_region = os.getenv("SPEECH_REGION", "westeurope")
        self.voice_name = os.getenv("VOICE_NAME", "en-US-JennyMultilingualNeural")
        self.language = os.getenv("LANGUAGE", "en-US")
        
        # Check if required keys are present
        if not self.speech_key:
            print("Error: SPEECH_KEY not found in environment variables!")
            return
        
        # OpenAI configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Error: OPENAI_API_KEY not found in environment variables!")
            return
            
        if self.api_key and self.api_key.startswith('sk-proj-'):
            openai.api_base = "https://api.openai.com/v1"
        openai.api_key = self.api_key
        
        # State management
        self.current_step = 0
        self.recipe_steps = []
        self.recipe_ingredients = []
        self.recipe_name = ""
        self.original_recipe_data = {}  # Store complete original JSON
        self.is_interrupted = False
        self.is_completed = False  # Track if recipe was completed successfully
        
        # ENHANCED LEARNING: Add comprehensive user model tracking
        self.user_model = {
            "cooking_pace": "normal",  # slow/normal/fast
            "question_patterns": {},   # track question types
            "confusion_count": 0,      # track confusion indicators
            "session_questions": [],   # current session questions
            "preferences": {},         # learned preferences
            "skill_indicators": {      # track skill level indicators
                "technique_questions": 0,
                "timing_questions": 0,
                "troubleshooting_questions": 0,
                "equipment_questions": 0
            },
            "interaction_patterns": {  # track interaction patterns
                "quick_navigation": 0,
                "detailed_questions": 0,
                "repeat_requests": 0
            },
            "step_timing": [],         # track time spent on each step
            "common_confusions": []    # track what confuses the user
        }
        
        # LEARNING: Session tracking
        self.session_start_time = None
        
        # Initialize speech services
        self._init_speech_services()
        
    def _init_speech_services(self):
        """Initialize Azure speech services."""
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.speech_region
        )
        self.speech_config.speech_synthesis_voice_name = self.voice_name
        self.speech_config.speech_recognition_language = self.language
        
        # Configure faster speech
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
        )
        
        # Improve speech recognition sensitivity
        self.speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "8000")
        self.speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "2000")
        self.speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "2000")
        
        # Use default microphone with better configuration
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
        self.recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=audio_config)
        
        # Test microphone access
        self.test_microphone()
        

    def test_microphone(self):
        """Test microphone access and speech services."""
        try:
            # Simple, clean instruction
            print("Say 'Hello Su-Chef' clearly. Listening for 10 seconds...")
            
            # Configure for longer listening time
            result = self.recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"✅ Voice recognition working! Heard: '{result.text}'")
                return True
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("⚠️ No speech recognized. Voice features will use text fallback.")
                return False
                    
            elif result.reason == speechsdk.ResultReason.Canceled:
                print("❌ Voice recognition failed. Using text fallback.")
                return False
                
        except Exception as e:
            print("❌ Voice recognition error. Using text fallback.")
            return False
        
        return False
        
    def speak(self, text: str) -> bool:
        """Speak text with faster rate."""
        if not text:
            return True
            
        ssml_text = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{self.voice_name}">
                <prosody rate="+30.00%">
                    {text}
                </prosody>
            </voice>
        </speak>"""
        
        try:
            result = self.synthesizer.speak_ssml_async(ssml_text).get()
            return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted
        except:
            return False
            
    def listen(self) -> Optional[str]:
        """Listen for user input with improved error handling."""
        try:
            result = self.recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = result.text.strip()
                print(f"You said: {text}")
                return text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"Speech recognition canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {cancellation_details.error_details}")
                    print("Check your microphone and Azure Speech key.")
                return None
                
        except Exception as e:
            print(f"Speech recognition error: {str(e)}")
            print("Falling back to text input...")
            # Fallback to text input if voice fails
            try:
                text_input = input("Type your command: ").strip()
                if text_input:
                    print(f"You typed: {text_input}")
                    return text_input
            except KeyboardInterrupt:
                return None
        
        return None

    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """Classify user intent using OpenAI for better understanding."""
        try:
            client = openai.OpenAI()
            
            prompt = f"""
Classify this cooking assistant user input:
Input: "{user_input}"
Context: Step {self.current_step + 1} of {len(self.recipe_steps)} - {self.recipe_name}

Classify as ONE intent:
- NAVIGATION: "next", "continue", "move on", "skip" (explicit commands to advance)
- CLARIFICATION: "what", "how", "why", "explain", "tell me about", "current step" (questions about current step)
- TIMING: "how long", "when ready", "is it done", "time"
- SUBSTITUTION: "replace ingredient", "alternative", "substitute"
- TECHNIQUE: "how to cook", "temperature", "method", "technique"
- TROUBLESHOOTING: "help", "stuck", "problem", "wrong", "issue"
- REPEAT: "say again", "repeat", "one more time"
- INGREDIENTS: "list ingredients", "what ingredients", "ingredients"
- STOP: "quit", "end", "stop", "exit"
- QUESTION: other cooking questions

IMPORTANT: Questions ABOUT the current step should be CLARIFICATION, not NAVIGATION.
Only classify as NAVIGATION if explicitly asking to move forward.

Respond with just the intent name.
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20
            )
            
            intent = response.choices[0].message.content.strip().upper()
            return {"intent": intent, "confidence": 0.9}
            
        except Exception as e:
            print(f"Intent classification failed: {e}")
            # Fallback to simple matching
            user_lower = user_input.lower()
            if any(word in user_lower for word in ['next', 'continue']):
                return {"intent": "NAVIGATION", "confidence": 0.7}
            elif any(word in user_lower for word in ['repeat', 'again']):
                return {"intent": "REPEAT", "confidence": 0.7}
            else:
                return {"intent": "QUESTION", "confidence": 0.5}

    def get_ai_response(self, question: str) -> Optional[str]:
        """Enhanced AI response with intent classification."""
        
        # Step 1: Classify intent intelligently
        intent_data = self.classify_intent(question)
        intent = intent_data["intent"]
        
        # Step 2: Handle intents intelligently
        if intent == "NAVIGATION":
            # Check if we're at the final step
            if self.current_step >= len(self.recipe_steps) - 1:
                # Complete the recipe and exit the cooking loop
                self.is_completed = True
                self.is_interrupted = True
                return "Perfect! Recipe completed! Great job cooking!"
            else:
                # Move to next step
                self.current_step += 1
                # Add proactive intelligence
                if self.current_step < len(self.recipe_steps):
                    next_step = self.recipe_steps[self.current_step].lower()
                    if "heat" in next_step or "temperature" in next_step:
                        return "Moving to next step. This involves temperature control - be careful!"
                return None
            
        elif intent == "REPEAT":
            if self.current_step < len(self.recipe_steps):
                step_text = f"Step {self.current_step + 1}: {self.recipe_steps[self.current_step]}"
                print(f"\n{step_text}")
                self.speak(step_text)
                print("Say 'next' when ready, or ask a question...")
            return None
            
        elif intent == "STOP":
            self.speak("Ending the recipe guide.")
            self.is_interrupted = True
            return None
            
        elif intent == "INGREDIENTS":
            self.speak_ingredients()
            return None
        
        # Step 3: Enhanced context for complex questions
        try:
            client = openai.OpenAI()
            
            # Build comprehensive rich context
            rich_context = self.build_rich_context(question, intent)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an intelligent cooking assistant with context awareness. Provide smart, practical cooking advice."},
                    {"role": "user", "content": rich_context}
                ],
                temperature=0.7,
                max_tokens=60
            )
            
            base_response = response.choices[0].message.content.strip()
            
            # LEARNING: Personalize response based on user model
            personalized_response = self.get_personalized_response(base_response, intent)
            
            # LEARNING: Learn from this interaction
            self.learn_from_interaction(question, intent, personalized_response)
            
            # Add instruction for continuing after questions
            if intent not in ["NAVIGATION", "REPEAT", "STOP", "INGREDIENTS"]:
                personalized_response += " Say 'Next' to continue cooking, or ask another question if you're still unsure."
            
            return personalized_response
            
        except Exception as e:
            print(f"❌ AI Error: {str(e)}")
            return "I'm having trouble with that question. Could you try rephrasing it?"
            
    def load_recipe(self, filename: str = None) -> bool:
        """Load recipe steps from JSON file. Handles multiple formats."""
        # Try to load from steps.json first (friend's format), then recipe.json
        files_to_try = ["steps.json", "recipe.json"] if filename is None else [filename]
        
        for file_path in files_to_try:
            try:
                with open(file_path, 'r') as f:
                    recipe_data = json.load(f)
                    self.original_recipe_data = recipe_data.copy()  # Store original data
                    
                    # Handle steps.json format (from friend's code)
                    if "steps" in recipe_data and isinstance(recipe_data["steps"], list):
                        if len(recipe_data["steps"]) > 0 and "text" in recipe_data["steps"][0]:
                            # Friend's format: [{"step_number": 1, "text": "..."}, ...]
                            self.recipe_steps = [step["text"] for step in recipe_data["steps"]]
                            self.recipe_name = recipe_data.get("recipe_name", "Unknown Recipe")
                            # Try to load ingredients from companion recipe.json file
                            self._load_ingredients_from_companion_file()
                            print(f"Loaded recipe: {self.recipe_name}")
                            return True
                        else:
                            # Original format: {"steps": ["step1", "step2", ...]}
                            self.recipe_steps = recipe_data["steps"]
                            self.recipe_name = recipe_data.get("name", "Unknown Recipe")
                            self.recipe_ingredients = recipe_data.get("ingredients", [])
                            return True
                    
                    # Handle recipe.json format (instructions field)
                    elif "instructions" in recipe_data:
                        self.recipe_steps = recipe_data["instructions"]
                        self.recipe_name = recipe_data.get("name", "Unknown Recipe")
                        self.recipe_ingredients = recipe_data.get("ingredients", [])
                        return True
                        
            except FileNotFoundError:
                continue
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON format in {file_path}")
                continue
        
        print("Error: No valid recipe file found. Please check steps.json or recipe.json files.")
        return False
            
    def _load_ingredients_from_companion_file(self):
        """Try to load ingredients from recipe.json when using steps.json."""
        try:
            with open("recipe.json", 'r') as f:
                recipe_data = json.load(f)
                self.recipe_ingredients = recipe_data.get("ingredients", [])
        except (FileNotFoundError, json.JSONDecodeError):
            # If no companion file, ingredients will remain empty
            self.recipe_ingredients = []
            

    
    def speak_ingredients(self):
        """Speak the recipe ingredients list."""
        if not self.recipe_ingredients:
            self.speak("I don't have the ingredients list available for this recipe.")
            return
        
        print(f"\nIngredients for {self.recipe_name}:")
        ingredients_text = f"Here are the ingredients for {self.recipe_name}: "
        
        for i, ingredient in enumerate(self.recipe_ingredients):
            print(f"  • {ingredient}")
            if i == 0:
                ingredients_text += ingredient
            else:
                ingredients_text += f", {ingredient}"
        
        self.speak(ingredients_text)
        print("\nSay 'next' to continue with the recipe, or ask another question.")
                
    def run(self):
        """Simple interaction loop for voice-guided cooking."""
        if not self.load_recipe():
            return
        
        # LEARNING: Initialize session tracking
        from datetime import datetime
        self.session_start_time = datetime.now()
            
        print(f"\n🍳 Starting cooking guide for: {self.recipe_name}")
        self.speak(f"Hi! I'm Su-Chef, your cooking assistant for {self.recipe_name}. Say 'next' to continue, 'repeat' to hear again, 'ingredients' for the ingredient list, or ask any cooking question.")
        
        # Speak the first step
        step_spoken = False
        just_repeated = False
        
        while not self.is_interrupted and self.current_step < len(self.recipe_steps):
            # Speak current step only if not already spoken
            if not step_spoken:
                step_text = f"Step {self.current_step + 1}: {self.recipe_steps[self.current_step]}"
                print(f"\n{step_text}")
                self.speak(step_text)
                print("Say 'next' when ready, or ask a question...")
                step_spoken = True
            
            # Get user input (voice or text fallback)
            user_input = self.listen()
            
            if not user_input:
                # Simple fallback to text
                print("Voice not detected. Type your command:")
                try:
                    user_input = input("> ").strip() or "next"
                except KeyboardInterrupt:
                    break
            
            if user_input:
                # Check if this is a repeat command
                intent_data = self.classify_intent(user_input)
                intent = intent_data["intent"]
                
                # Process the input
                response = self.get_ai_response(user_input)
                if response:
                    print(f"\nAssistant: {response}")
                    self.speak(response)
                    # Don't repeat step automatically - wait for explicit "next"
                elif intent == "REPEAT":
                    # Step was just repeated, don't speak it again
                    just_repeated = True
                else:
                    # If response is None and not repeat, it means navigation happened
                    step_spoken = False  # Need to speak the new step
                    just_repeated = False
        
        if not self.is_interrupted:
            print("\n🎉 Recipe completed!")
            self.speak("All done! Great job cooking!")
    
    def _show_learning_summary(self):
        """Enhanced learning summary with comprehensive insights."""
        print(f"\n🧠 Enhanced Learning Summary:")
        
        # Basic metrics
        print(f"• Your cooking pace: {self.user_model['cooking_pace']}")
        print(f"• Total questions asked: {len(self.user_model['session_questions'])}")
        
        # Skill level analysis
        total_skill_questions = sum(self.user_model["skill_indicators"].values())
        skill_level = "beginner" if total_skill_questions > 8 else "intermediate" if total_skill_questions > 3 else "experienced"
        print(f"• Estimated skill level: {skill_level}")
        
        # Question patterns
        if self.user_model["question_patterns"]:
            most_common = max(self.user_model["question_patterns"], key=self.user_model["question_patterns"].get)
            print(f"• Most common question type: {most_common}")
        
        # Interaction patterns
        if self.user_model["interaction_patterns"]["detailed_questions"] > 5:
            print("• You ask detailed questions - shows good attention to detail!")
        if self.user_model["interaction_patterns"]["quick_navigation"] > 8:
            print("• You navigate quickly through steps - confident cooking!")
        if self.user_model["interaction_patterns"]["repeat_requests"] > 2:
            print("• You requested several repeats - I'll speak more clearly next time")
        
        # Confusion analysis
        confusion_level = "High" if self.user_model['confusion_count'] > 3 else "Medium" if self.user_model['confusion_count'] > 1 else "Low"
        print(f"• Confusion level: {confusion_level}")
        
        if self.user_model["common_confusions"]:
            print(f"• Common confusion areas: {len(self.user_model['common_confusions'])} steps needed clarification")
        
        # Skill insights
        if self.user_model["skill_indicators"]["technique_questions"] > 3:
            print("• You're learning cooking techniques - great for skill building!")
        if self.user_model["skill_indicators"]["timing_questions"] > 2:
            print("• You're focused on timing - shows precision cooking!")
        if self.user_model["skill_indicators"]["equipment_questions"] > 2:
            print("• You asked about equipment - building your kitchen knowledge!")
        
        print("\n🎯 I'll use these insights to provide better guidance next time!")
        print("🚀 Keep cooking and learning - you're doing great!")

    def learn_from_interaction(self, user_input: str, intent: str, ai_response: str):
        """Enhanced learning from user interactions to improve future responses."""
        
        # Track question patterns
        if intent in self.user_model["question_patterns"]:
            self.user_model["question_patterns"][intent] += 1
        else:
            self.user_model["question_patterns"][intent] = 1
        
        # Enhanced confusion tracking
        if intent in ["CLARIFICATION", "REPEAT", "TROUBLESHOOTING"]:
            self.user_model["confusion_count"] += 1
            # Track what specifically confuses the user
            if intent == "CLARIFICATION":
                self.user_model["common_confusions"].append({
                    "step": self.current_step,
                    "question": user_input,
                    "step_text": self.recipe_steps[self.current_step] if self.current_step < len(self.recipe_steps) else ""
                })
        
        # Enhanced skill level tracking
        if intent == "TECHNIQUE":
            self.user_model["skill_indicators"]["technique_questions"] += 1
        elif intent == "TIMING":
            self.user_model["skill_indicators"]["timing_questions"] += 1
        elif intent == "TROUBLESHOOTING":
            self.user_model["skill_indicators"]["troubleshooting_questions"] += 1
        elif intent == "EQUIPMENT":
            self.user_model["skill_indicators"]["equipment_questions"] += 1
        
        # Enhanced interaction pattern tracking
        if intent == "NAVIGATION":
            self.user_model["interaction_patterns"]["quick_navigation"] += 1
            self._update_cooking_pace()
        elif intent == "REPEAT":
            self.user_model["interaction_patterns"]["repeat_requests"] += 1
        elif intent in ["CLARIFICATION", "TECHNIQUE", "TIMING", "TROUBLESHOOTING"]:
            self.user_model["interaction_patterns"]["detailed_questions"] += 1
        
        # Store enhanced session questions for analysis
        self.user_model["session_questions"].append({
            "input": user_input,
            "intent": intent,
            "step": self.current_step,
            "response": ai_response,
            "timestamp": len(self.user_model["session_questions"])  # Simple timestamp
        })
    
    def _update_cooking_pace(self):
        """Enhanced cooking pace analysis based on multiple indicators."""
        navigation_count = self.user_model["question_patterns"].get("NAVIGATION", 0)
        total_questions = sum(self.user_model["question_patterns"].values())
        
        if total_questions > 3:  # Need some data
            navigation_ratio = navigation_count / total_questions
            detailed_questions = self.user_model["interaction_patterns"]["detailed_questions"]
            repeat_requests = self.user_model["interaction_patterns"]["repeat_requests"]
            
            # Multi-factor pace analysis
            if navigation_ratio > 0.6 and detailed_questions < 3:  # Mostly navigation, few questions
                self.user_model["cooking_pace"] = "fast"
            elif navigation_ratio < 0.4 or detailed_questions > 5 or repeat_requests > 2:  # Lots of questions/repeats
                self.user_model["cooking_pace"] = "slow"
            else:
                self.user_model["cooking_pace"] = "normal"
    
    def get_personalized_response(self, base_response: str, intent: str) -> str:
        """Enhanced personalization based on comprehensive user model."""
        
        # Analyze user skill level
        total_skill_questions = sum(self.user_model["skill_indicators"].values())
        skill_level = "beginner" if total_skill_questions > 8 else "intermediate" if total_skill_questions > 3 else "experienced"
        
        # Adjust for cooking pace and skill level
        if self.user_model["cooking_pace"] == "slow":
            if skill_level == "beginner":
                return f"{base_response} Take your time - you're learning great!"
            else:
                return f"{base_response} No rush, careful cooking is good cooking."
        elif self.user_model["cooking_pace"] == "fast":
            if intent == "NAVIGATION":
                return f"{base_response} Great pace! You're cooking confidently."
            else:
                return f"{base_response} You're moving fast - double-check this step."
        
        # Adjust for confusion patterns
        if self.user_model["confusion_count"] > 3:
            if intent in ["TECHNIQUE", "CLARIFICATION"]:
                return f"{base_response} I'll explain more clearly next time."
            else:
                return f"{base_response} Let me know if anything is unclear."
        
        # Adjust for repeat patterns
        if self.user_model["interaction_patterns"]["repeat_requests"] > 2:
            return f"{base_response} I'll speak more clearly."
        
        # Skill-based adjustments
        if skill_level == "beginner" and intent in ["TECHNIQUE", "EQUIPMENT"]:
            return f"{base_response} Don't worry, everyone learns these basics!"
        elif skill_level == "experienced" and intent == "TECHNIQUE":
            return f"{base_response} You probably know this, but just to confirm."
        
        return base_response

    def build_rich_context(self, question: str, intent: str) -> str:
        """Build comprehensive context for enhanced AI responses."""
        
        # Calculate progress
        progress_percent = (self.current_step / len(self.recipe_steps)) * 100 if self.recipe_steps else 0
        
        # Analyze recent questions and patterns
        recent_intents = [q["intent"] for q in self.user_model["session_questions"][-3:]]
        
        # Predict next steps
        next_steps = []
        if self.current_step + 1 < len(self.recipe_steps):
            next_steps = self.recipe_steps[self.current_step+1:self.current_step+3]
        
        # Analyze user skill level
        total_skill_questions = sum(self.user_model["skill_indicators"].values())
        skill_level = "beginner" if total_skill_questions > 8 else "intermediate" if total_skill_questions > 3 else "experienced"
        
        # Identify confusion patterns
        confusion_areas = []
        if self.user_model["common_confusions"]:
            confusion_areas = [conf["step"] for conf in self.user_model["common_confusions"][-2:]]
        
        # Build enhanced rich context
        rich_context = f"""
ENHANCED COOKING INTELLIGENCE CONTEXT:

RECIPE STATUS:
- Recipe: {self.recipe_name}
- Progress: {self.current_step + 1}/{len(self.recipe_steps)} ({progress_percent:.1f}% complete)
- Current Step: {self.recipe_steps[self.current_step] if self.current_step < len(self.recipe_steps) else "Complete"}
- Next Steps Preview: {'; '.join(next_steps[:2]) if next_steps else "Recipe complete"}

ENHANCED USER PROFILE:
- Cooking Pace: {self.user_model["cooking_pace"]}
- Estimated Skill Level: {skill_level}
- Confusion Level: {"High" if self.user_model["confusion_count"] > 3 else "Medium" if self.user_model["confusion_count"] > 1 else "Low"}
- Recent Question Types: {', '.join(recent_intents) if recent_intents else "None"}
- Total Questions This Session: {len(self.user_model["session_questions"])}

INTERACTION PATTERNS:
- Quick Navigation: {self.user_model["interaction_patterns"]["quick_navigation"]}
- Detailed Questions: {self.user_model["interaction_patterns"]["detailed_questions"]}
- Repeat Requests: {self.user_model["interaction_patterns"]["repeat_requests"]}

SKILL INDICATORS:
- Technique Questions: {self.user_model["skill_indicators"]["technique_questions"]}
- Timing Questions: {self.user_model["skill_indicators"]["timing_questions"]}
- Equipment Questions: {self.user_model["skill_indicators"]["equipment_questions"]}
- Troubleshooting Questions: {self.user_model["skill_indicators"]["troubleshooting_questions"]}

CURRENT INTERACTION:
- User Intent: {intent}
- Question: "{question}"
- Available Ingredients: {', '.join(self.recipe_ingredients) if self.recipe_ingredients else "Not specified"}
- Previous Confusion Steps: {confusion_areas if confusion_areas else "None"}

INTELLIGENT RESPONSE REQUIREMENTS:
- Provide context-aware, personalized advice based on skill level
- Consider user's cooking pace, confusion patterns, and interaction style
- Reference specific steps, ingredients, timing, and techniques
- Anticipate potential issues based on next steps and user patterns
- Be proactive, encouraging, and adaptive to user's learning style
- Keep response practical and under 50 words
- Match response complexity to user's skill level

Generate enhanced intelligent cooking assistance:
"""
        return rich_context

if __name__ == "__main__":
    # This file is now used as a module only
    # Main functionality moved to su_chef.py
    print("This module should be imported, not run directly.")
    print("Run 'python su_chef.py' instead.") 