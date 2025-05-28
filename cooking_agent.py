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
        self.is_interrupted = False
        self.context = {
            "needs_help": False,
            "last_question": None,
            "current_focus": None
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
        
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
        self.recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
        
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
        """Listen for user input."""
        print("Speak now...")
        try:
            result = self.recognizer.recognize_once_async().get()
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = result.text.strip()
                print(f"You said: {text}")
                return text
        except:
            pass
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
            
            # Handle AI's decision
            if ai_decision == "COMMAND":
                self.speak("Ending the recipe guide.")
                self.is_interrupted = True
                return None
            elif ai_decision == "NEXT":
                self.current_step += 1
                return None
            elif ai_decision == "REPEAT":
                self.speak_current_step(repeat_step=True)
                return None
            elif ai_decision == "INGREDIENTS":
                self.speak_ingredients()
                return None
                
        except Exception as e:
            print(f"AI Command Check Error: {str(e)}")
            # Fall through to regular question handling if AI check fails
        
        # If it's a question, proceed with normal AI response
        analysis = self.analyze_question(question)
        current_step = self.recipe_steps[self.current_step]
        
        # Build context-aware prompt
        prompt = f"""Question about: '{current_step}'
        User asks: {question}
        Question type: {analysis['type']}
        {'URGENT: Please provide immediate safety guidance.' if analysis['is_urgent'] else ''}
        {'Focus on visual/physical cues to check progress.' if analysis['type'] == 'check' else ''}
        {'Provide specific step-by-step guidance.' if analysis['type'] == 'how_to' else ''}
        """
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are a helpful cooking expert. Keep responses under 40 words. Focus on practical, specific advice."
                },
                {"role": "user", "content": prompt}
            ]
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=60
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI Error: {str(e)}")
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
        """Main interaction loop."""
        if not self.load_recipe():
            return
            
        print(f"\nStarting cooking assistant for: {self.recipe_name}")
        self.speak(f"Hi, I'm Su-Chef, your cooking assistant! I'll guide you step by step through {self.recipe_name}. You can say 'next' to move to the next step, 'repeat' to hear something again, 'ingredients' to hear the ingredients list, 'help' if you need tips, or 'stop' to end our session. Or ask me any question.")
        
        while not self.is_interrupted and self.current_step < len(self.recipe_steps):
            self.speak_current_step(repeat_step=True)
            
            while not self.is_interrupted:
                print("\nListening for your command or question...")
                user_input = self.listen()
                
                if not user_input:
                    continue
                    
                # Let AI handle all input - commands and questions
                response = self.get_ai_response(user_input)
                if response:
                    print("\nAssistant:", response)
                    self.speak(response)
                
                # Check if we should move to next step (AI might have incremented current_step)
                if self.current_step >= len(self.recipe_steps):
                    break
                    
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