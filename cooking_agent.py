import json
import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import openai
from typing import Optional, Dict, List, Any

class CookingAgent:
    def __init__(self):
        print("Initializing CookingAgent...")
        # Load environment variables
        load_dotenv()
        print("Environment variables loaded")
        
        # Azure Speech Service configuration
        self.speech_key = os.getenv("SPEECH_KEY")
        self.speech_region = os.getenv("SPEECH_REGION", "westeurope")
        self.voice_name = os.getenv("VOICE_NAME", "en-US-JennyMultilingualNeural")
        self.language = os.getenv("LANGUAGE", "en-US")
        
        print(f"Speech key found: {bool(self.speech_key)}")
        print(f"Speech region: {self.speech_region}")
        
        # Check if required keys are present
        if not self.speech_key:
            print("Error: SPEECH_KEY not found in environment variables!")
            print("Please check your .env file.")
            return
        
        # OpenAI configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        print(f"OpenAI key found: {bool(self.api_key)}")
        if not self.api_key:
            print("Error: OPENAI_API_KEY not found in environment variables!")
            print("Please add your OpenAI API key to the .env file.")
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
        self.context = {
            "needs_help": False,
            "last_question": None,
            "current_focus": None,
            "conversation_history": [],
            "user_preferences": {},
            "cooking_start_time": None
        }
        
        print("Initializing speech services...")
        # Initialize speech services
        self._init_speech_services()
        print("CookingAgent initialization complete!")
        
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
        
    def check_microphone_settings(self):
        """Provide guidance for checking microphone settings on Windows."""
        print("\n🔧 Microphone Setup Guide:")
        print("1. Right-click the speaker icon in your system tray")
        print("2. Select 'Open Sound settings'")
        print("3. Under 'Input', make sure the correct microphone is selected")
        print("4. Click 'Device properties' and ensure the volume is at 70-100%")
        print("5. Click 'Additional device properties' → 'Levels' tab")
        print("6. Set microphone level to 70-80 and boost to +10dB if available")
        print("7. In 'Advanced' tab, try different sample rates (44.1kHz or 48kHz)")
        print("\n💡 Quick test: Try speaking into your microphone while watching the")
        print("   input level bar in Windows Sound settings - it should move when you speak.")
        
    def test_microphone(self):
        """Test microphone access and speech services."""
        print("Testing microphone and speech services...")
        print("🎤 Make sure your microphone is connected and not muted")
        print("🔊 Speak clearly and at normal volume")
        
        try:
            # Give user more time and clearer instructions
            print("\n📢 Please say 'Hello Su-Chef' clearly now...")
            print("(You have 10 seconds to speak)")
            
            # Configure for longer listening time
            result = self.recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                print(f"✅ Microphone test successful! Heard: '{result.text}'")
                print("🎉 Voice recognition is working properly!")
                return True
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("⚠️ Microphone detected but no clear speech recognized.")
                print("\n🔧 Troubleshooting tips:")
                print("   • Speak louder and more clearly")
                print("   • Move closer to your microphone")
                print("   • Check if your microphone is muted")
                print("   • Try using a headset microphone")
                print("   • Make sure no other apps are using the microphone")
                
                # Show microphone settings guide
                self.check_microphone_settings()
                
                # Offer a second chance
                print("\n🔄 Let's try one more time...")
                print("Say 'Testing one two three' clearly:")
                
                result2 = self.recognizer.recognize_once_async().get()
                if result2.reason == speechsdk.ResultReason.RecognizedSpeech:
                    print(f"✅ Second test successful! Heard: '{result2.text}'")
                    return True
                else:
                    print("❌ Second test also failed. Voice features will use text fallback.")
                    return False
                    
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"❌ Microphone test failed: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {cancellation_details.error_details}")
                    print("\n🔧 Possible solutions:")
                    print("   • Check your Azure Speech Service key")
                    print("   • Verify your internet connection")
                    print("   • Try restarting the application")
                return False
                
        except Exception as e:
            print(f"❌ Microphone test error: {str(e)}")
            print("Voice features may not work properly. The system will fall back to text input.")
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
        print("Speak now...")
        try:
            result = self.recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = result.text.strip()
                print(f"You said: {text}")
                return text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                print("No speech could be recognized. Please try again.")
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

    def analyze_question(self, question: str) -> Dict[str, Any]:
        """Analyze the user's question to determine context and type."""
        question = question.lower()
        
        # Common question patterns
        patterns = {
            "how_to": ["how do i", "how to", "what's the best way"],
            "timing": ["how long", "when is", "until"],
            "temperature": ["temperature", "hot", "heat", "warm"],
            "substitute": ["instead of", "substitute", "replace"],
            "help": ["help", "stuck", "not sure"],
            "tips": ["tip", "advice", "suggest"],
            "check": ["ready", "done", "finished", "check"]
        }
        
        # Determine question type
        q_type = "general"
        for t, keywords in patterns.items():
            if any(k in question for k in keywords):
                q_type = t
                break
                
        return {
            "type": q_type,
            "needs_demo": any(w in question for w in ["show", "demonstrate", "example"]),
            "is_urgent": any(w in question for w in ["help", "quick", "emergency", "burning"]),
            "step_specific": any(str(i) for i in range(1, len(self.recipe_steps) + 1) if str(i) in question)
        }
        
    def get_ai_response(self, question: str) -> Optional[str]:
        """Get dynamic AI response based on question analysis."""
        print(f"🔍 DEBUG: Processing input: '{question}'")
        
        # First, let AI determine if this is a session command
        try:
            client = openai.OpenAI()
            command_check_messages = [
                {
                    "role": "system", 
                    "content": "You are analyzing user input to determine if it's a session command or cooking question. Respond with ONLY 'COMMAND' if the user wants to stop/quit/end the session, 'NEXT' if they want to proceed to next step, 'REPEAT' if they want to repeat current step, 'INGREDIENTS' if they want to hear the ingredients list, or 'QUESTION' if it's a cooking-related question."
                },
                {"role": "user", "content": f"User said: '{question}'"}
            ]
            
            command_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=command_check_messages,
                temperature=0.1,
                max_tokens=10
            )
            
            ai_decision = command_response.choices[0].message.content.strip().upper()
            print(f"🤖 DEBUG: AI classified as: '{ai_decision}'")
            
            # Handle AI's decision
            if ai_decision == "COMMAND":
                print("🛑 DEBUG: Stopping session")
                self.speak("Ending the recipe guide.")
                self.is_interrupted = True
                return None
            elif ai_decision == "NEXT":
                print(f"➡️ DEBUG: Moving to next step (current: {self.current_step})")
                self.current_step += 1
                print(f"➡️ DEBUG: Now at step: {self.current_step}")
                return None
            elif ai_decision == "REPEAT":
                print("🔄 DEBUG: Repeating current step")
                self.speak_current_step(repeat_step=True)
                return None
            elif ai_decision == "INGREDIENTS":
                print("📝 DEBUG: Speaking ingredients")
                self.speak_ingredients()
                return None
                
        except Exception as e:
            print(f"❌ AI Command Check Error: {str(e)}")
            # Fall through to regular question handling if AI check fails
        
        # If it's a question, proceed with context-rich AI response
        analysis = self.analyze_question(question)
        current_step = self.recipe_steps[self.current_step]
        
        # Update conversation history
        self.context["last_question"] = question
        self.context["conversation_history"].append({
            "step": self.current_step + 1,
            "question": question,
            "type": analysis['type']
        })
        
        # Keep only last 5 questions for context
        if len(self.context["conversation_history"]) > 5:
            self.context["conversation_history"] = self.context["conversation_history"][-5:]
        
        # Build comprehensive context with complete recipe data
        recent_questions = "\n".join([f"Q: {q['question']} (Step {q['step']})" 
                                    for q in self.context["conversation_history"][-3:]])
        
        # Create clean, structured context for AI (Option 1 approach)
        progress_percentage = int((self.current_step / len(self.recipe_steps)) * 100)
        
        # Previous step info
        previous_step_text = ""
        if self.current_step > 0:
            previous_step_text = f"PREVIOUS STEP (COMPLETED):\nStep {self.current_step}: {self.recipe_steps[self.current_step - 1]}\n"
        else:
            previous_step_text = "PREVIOUS STEP: None (this is the first step)\n"
        
        # Next step info
        next_step_text = ""
        if self.current_step < len(self.recipe_steps) - 1:
            next_step_text = f"\nNEXT STEP (UPCOMING):\nStep {self.current_step + 2}: {self.recipe_steps[self.current_step + 1]}"
            # Add one more step if available
            if self.current_step < len(self.recipe_steps) - 2:
                next_step_text += f"\nStep {self.current_step + 3}: {self.recipe_steps[self.current_step + 2]}"
        else:
            next_step_text = "\nNEXT STEP: None (this is the final step)"
        
        # Ingredients list
        ingredients_text = ""
        if self.recipe_ingredients:
            ingredients_text = "\nINGREDIENTS AVAILABLE:\n" + "\n".join([f"• {ingredient}" for ingredient in self.recipe_ingredients])
        else:
            ingredients_text = "\nINGREDIENTS: Not available in recipe data"
        
        # Recent conversation
        conversation_text = ""
        if recent_questions:
            conversation_text = f"\nRECENT CONVERSATION:\n{recent_questions}"
        else:
            conversation_text = "\nRECENT CONVERSATION: No previous questions in this session"
        
        context_info = f"""RECIPE: {self.recipe_name} (Step {self.current_step + 1} of {len(self.recipe_steps)})
PROGRESS: {progress_percentage}% complete

{previous_step_text}
CURRENT STEP (NOW):
Step {self.current_step + 1}: {current_step}
{next_step_text}
{ingredients_text}
{conversation_text}

USER QUESTION: "{question}"
QUESTION TYPE: {analysis['type']}
URGENCY: {'🚨 SAFETY CONCERN' if analysis['is_urgent'] else 'Normal'}

INSTRUCTIONS FOR AI:
- Answer based on the clear step information above
- Reference specific step numbers when helpful
- Use the ingredients list for substitution questions
- Consider their progress for timing questions
- Be specific and practical"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": """You are Su-Chef, an expert cooking assistant with complete access to the user's recipe data and cooking progress. You have the full recipe JSON, current step, ingredients, and conversation history.

RESPONSE GUIDELINES:
- Keep responses under 60 words but be specific and helpful
- Use the complete recipe data to provide accurate, contextual answers
- Reference specific steps by number when relevant (e.g., "In step 3, you'll need...")
- Consider what ingredients they have available for substitution questions
- For timing questions, factor in their current progress and remaining steps
- If they ask about techniques, be specific to their current ingredient/step
- Cross-reference previous and upcoming steps for better guidance
- If they seem confused, offer to repeat or clarify the current step
- Always be encouraging and supportive

SMART CONTEXT USAGE:
- Know exactly where they are in the recipe progression
- Understand what they've already completed
- Anticipate what's coming next
- Reference specific ingredients from their list
- Remember their previous questions in this session
- Provide step-specific timing and technique advice"""
                },
                {"role": "user", "content": context_info}
            ]
            
            print(f"🔍 DEBUG: Sending context to AI (first 500 chars):")
            print(f"{context_info[:500]}...")
            print(f"🔍 DEBUG: Current step: {self.current_step + 1}, Total steps: {len(self.recipe_steps)}")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=80
            )
            
            ai_response = response.choices[0].message.content
            print(f"🤖 DEBUG: AI response: {ai_response}")
            
            return ai_response
        except Exception as e:
            print(f"❌ AI Error: {str(e)}")
            return None
            
    def process_command(self, command: str) -> str:
        """Process navigation and help commands."""
        if not command:
            return "CONTINUE"
            
        command = command.lower()
        
        # Navigation commands
        if any(word in command for word in ["next", "continue", "go ahead"]):
            self.current_step += 1
            return "NEXT"
        elif any(word in command for word in ["stop", "quit", "exit", "end"]):
            self.speak("Ending the recipe guide.")
            self.is_interrupted = True
            return "STOP"
        elif any(word in command for word in ["repeat", "again"]):
            self.speak_current_step(repeat_step=True)
            return "CONTINUE"
        
        # Help commands
        if any(word in command for word in ["tip", "help", "advice"]):
            tips = self.get_ai_response(f"What are the key tips for: {self.recipe_steps[self.current_step]}")
            if tips:
                print("\nTips:", tips)
                self.speak(tips)
                print("\nSay 'next' when ready, or ask another question.")
            return "CONTINUE"
            
        # If it's not a recognized command, treat it as a question
        return "QUESTION"
            
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
                        print(f"Loaded recipe: {self.recipe_name}")
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
            
    def speak_current_step(self, repeat_step=True):
        """Speak the current recipe step."""
        if 0 <= self.current_step < len(self.recipe_steps):
            if repeat_step:
                step_text = f"Step {self.current_step + 1}: {self.recipe_steps[self.current_step]}"
                print(f"\n{step_text}")
                self.speak(step_text)
            print("\nSay 'help' or 'tips' if you need guidance.")
    
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
        """Main interaction loop with improved voice handling."""
        if not self.load_recipe():
            return
            
        print(f"\nStarting cooking assistant for: {self.recipe_name}")
        self.speak(f"Hi, I'm Su-Chef, your cooking assistant! I'll guide you step by step through {self.recipe_name}. You can say 'next' to move to the next step, 'repeat' to hear something again, 'ingredients' to hear the ingredients list, 'help' if you need tips, or 'stop' to end our session. Or ask me any question.")
        
        while not self.is_interrupted and self.current_step < len(self.recipe_steps):
            self.speak_current_step(repeat_step=True)
            
            retry_count = 0
            max_retries = 3
            step_at_start = self.current_step  # Track the step we started with
            
            while not self.is_interrupted and retry_count < max_retries and self.current_step == step_at_start:
                print("\nListening for your command or question...")
                print("(If voice isn't working, the system will prompt for text input)")
                
                user_input = self.listen()
                
                if not user_input:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"No input detected. Retry {retry_count}/{max_retries}")
                        print("Try speaking louder or closer to the microphone...")
                    else:
                        print("Voice detection failed. Continuing with text input only.")
                        print("Type 'next' to continue, 'stop' to quit, or ask a question:")
                        try:
                            user_input = input("> ").strip()
                            if not user_input:
                                user_input = "next"  # Default action
                        except KeyboardInterrupt:
                            self.is_interrupted = True
                            break
                    
                if user_input:
                    # Reset retry count on successful input
                    retry_count = 0
                    
                    # Let AI handle all input - commands and questions
                    response = self.get_ai_response(user_input)
                    if response:
                        print("\nAssistant:", response)
                        self.speak(response)
                    
                    # The loop will automatically break if current_step changed (next command)
                    # or if we've reached the end or been interrupted
                        
        if not self.is_interrupted:
            print("\nRecipe completed!")
            self.speak("All done! Great job!")

def main():
    print("Starting Su-Chef Cooking Agent...")
    try:
        agent = CookingAgent()
        print("Agent initialized successfully!")
        agent.run()
    except Exception as e:
        print(f"Error starting agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 