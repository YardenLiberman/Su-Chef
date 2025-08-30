#!/usr/bin/env python3
"""
Su-Chef Desktop App - Main Entry Point
Qt Quick (QML) + PySide6 Implementation
"""

import sys
import os
from PySide6.QtCore import QObject, Slot, Signal, QUrl, Property, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType

from core.services import RecipeService, DBService, CookingService


class Backend(QObject):
    """Backend service that bridges Python logic with QML UI"""
    
    # Signals to QML (UI updates)
    statusChanged = Signal(str)
    errorOccurred = Signal(str)
    heardText = Signal(str)
    stepChanged = Signal(int)
    recipeGenerated = Signal('QVariant')  # QVariant for complex data
    recipesLoaded = Signal('QVariant')
    cookingStarted = Signal()
    cookingStopped = Signal()
    recipeStepsChanged = Signal('QVariant')  # Send recipe steps to QML
    
    def __init__(self):
        super().__init__()
        
        # Initialize services
        self.recipe_service = RecipeService()
        self.db_service = DBService()
        self.cooking_service = CookingService()
        
        # Set up cooking service callbacks
        self.cooking_service.set_callbacks(
            on_heard=self.on_speech_heard,
            on_step_changed=self.on_step_changed,
            on_status=self.on_status_changed,
            on_error=self.on_error_occurred
        )
        
        # Current state
        self._current_user = ""
        self._current_recipe = None
        self._is_cooking = False
        self._is_listening = False
        
        # Voice recognition timer (same as mini app)
        self.listen_timer = QTimer()
        self.listen_timer.timeout.connect(self.check_voice_input)
        
    # Properties for QML binding
    @Property(str, notify=statusChanged)
    def currentUser(self):
        return self._current_user
    
    @Property(bool, notify=cookingStarted)
    def isCooking(self):
        return self._is_cooking
    
    @Property(bool, notify=statusChanged)
    def isListening(self):
        return self._is_listening
    
    # Slots (called from QML)
    @Slot(str, result=bool)
    def loginUser(self, username: str) -> bool:
        """Login user and initialize database"""
        try:
            if not username.strip():
                self.errorOccurred.emit("Username cannot be empty")
                return False
                
            user_id = self.db_service.add_user(username.strip())
            self._current_user = username.strip()
            self.statusChanged.emit(f"Welcome, {username}!")
            return True
            
        except Exception as e:
            self.errorOccurred.emit(f"Login failed: {str(e)}")
            return False
    
    @Slot(str, int, str, str, str)
    def generateRecipe(self, meal_type: str, time_limit: int, skill: str, diet: str, ingredients_text: str):
        """Generate a new recipe based on preferences - CLI logic"""
        try:
            # Check API key first (same as CLI)
            if not self.recipe_service.api_key:
                self.errorOccurred.emit("OpenAI API key not configured. Cannot generate recipes.")
                return
                
            self.statusChanged.emit("🔄 Generating recipe...")
            
            # Parse ingredients like CLI does
            available_ingredients = []
            if ingredients_text and ingredients_text.strip():
                available_ingredients = [ingredient.strip() for ingredient in ingredients_text.split(",") if ingredient.strip()]
            
            # Build prompt exactly like CLI
            dietary_restrictions = None if diet == "none" else diet
            
            prompt = f"""Please suggest a {meal_type} recipe that:
- Takes {time_limit} minutes or less to prepare
- Is suitable for a {skill} cook
"""
            
            if available_ingredients:
                prompt += f"- Uses some of these available ingredients: {', '.join(available_ingredients)}\n"
            
            if dietary_restrictions:
                prompt += f"\nMust be {dietary_restrictions}"
            
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
            
            print(f"DEBUG: Using CLI-style prompt for {meal_type}, {time_limit}min, {skill} level")
            
            # Use CLI's recipe generation method directly
            from core.recipe_generator import get_recipe_from_openai, process_recipe
            
            recipe_text = get_recipe_from_openai(prompt, self.recipe_service.api_key)
            
            if recipe_text:
                print("✅ Recipe text generated successfully")
                
                # Process recipe like CLI does
                recipe_data = process_recipe(
                    recipe_text,
                    meal_type,
                    str(time_limit),
                    skill,
                    dietary_restrictions
                )
                
                self._current_recipe = recipe_data
                instructions_count = len(recipe_data.get("instructions", []))
                print(f"✅ Recipe processed: {recipe_data.get('name', 'Unknown')} with {instructions_count} steps")
                
                self.recipeGenerated.emit(recipe_data)
                self.statusChanged.emit("✅ Recipe generated successfully!")
            else:
                self.errorOccurred.emit("❌ Failed to generate recipe. Check your OpenAI API key and internet connection.")
                
        except Exception as e:
            print(f"❌ Recipe generation error: {str(e)}")
            self.errorOccurred.emit(f"Recipe generation failed: {str(e)}")
    
    @Slot('QVariant')
    def startCooking(self, recipe_data):
        """Start voice-guided cooking session"""
        try:
            if not recipe_data:
                recipe_data = self._current_recipe
                
            if not recipe_data:
                self.errorOccurred.emit("No recipe selected")
                return
            
            self.statusChanged.emit("Starting cooking session...")
            
            # Convert QML object to Python dict if needed
            if hasattr(recipe_data, 'toVariant'):
                recipe_dict = recipe_data.toVariant()
            else:
                recipe_dict = dict(recipe_data) if recipe_data else {}
            
            # Use event-driven interface (NO BLOCKING)
            print(f"DEBUG: Starting cooking with recipe: {recipe_dict.get('name', 'Unknown')} - {len(recipe_dict.get('instructions', []))} steps")
            success = self.cooking_service.start(recipe_dict)
            
            if success:
                self._is_cooking = True
                self.cookingStarted.emit()
                self.statusChanged.emit("Voice guidance started - speak or type commands")
                
                # Send recipe steps to QML - CRITICAL FIX
                if self.cooking_service.agent and hasattr(self.cooking_service.agent, 'recipe_steps'):
                    steps = []
                    for i, step in enumerate(self.cooking_service.agent.recipe_steps):
                        if isinstance(step, dict):
                            steps.append(step['text'])
                        else:
                            steps.append(step)
                    print(f"DEBUG: Sending {len(steps)} steps to QML: {steps}")
                    self.recipeStepsChanged.emit(steps)
                    # Also emit step change to show current step
                    self.stepChanged.emit(0)  # Start at step 0
                
                # Start non-blocking session (replaces blocking run())
                if self.cooking_service.agent:
                    session_started = self.cooking_service.agent.start_session()
                    if session_started:
                        # Speak the first step
                        self.cooking_service.agent.speak_current_step()
                        # AUTO-START voice listening when cooking begins
                        self.startListening()
            else:
                self.errorOccurred.emit("Failed to start cooking session")
                
        except Exception as e:
            self.errorOccurred.emit(f"Failed to start cooking: {str(e)}")
    
    @Slot()
    def nextStep(self):
        """Go to next cooking step - map to CLI command"""
        if self._is_cooking and self.cooking_service.agent:
            self.cooking_service.agent.send_command("next")
            # Update GUI step indicator
            self.stepChanged.emit(self.cooking_service.agent.current_step)
    
    @Slot()
    def repeatStep(self):
        """Repeat current cooking step - map to CLI command"""
        if self._is_cooking and self.cooking_service.agent:
            self.cooking_service.agent.send_command("repeat")
    
    @Slot()
    def backStep(self):
        """Go to previous cooking step - map to CLI command"""
        if self._is_cooking and self.cooking_service.agent:
            self.cooking_service.agent.send_command("back")
            # Update GUI step indicator
            self.stepChanged.emit(self.cooking_service.agent.current_step)
    
    @Slot()
    def stopCooking(self):
        """Stop cooking session"""
        if self.cooking_service.agent:
            self.cooking_service.agent.stop_session()
        self._is_cooking = False
        self.cookingStopped.emit()
        self.statusChanged.emit("Cooking session ended")
    
    @Slot()
    def startListening(self):
        """Start voice recognition - same as mini app"""
        try:
            if self.cooking_service and self.cooking_service.agent and not self._is_listening:
                self._is_listening = True
                self.statusChanged.emit("🎤 Listening for voice commands...")
                # Start timer to check for voice input (improved timing)
                self.listen_timer.start(2000)  # Check every 2 seconds for better recognition
            else:
                self.statusChanged.emit("⚠️ Voice recognition not available - check API keys")
        except Exception as e:
            self.errorOccurred.emit(f"Voice recognition error: {str(e)}")
    
    @Slot()
    def stopListening(self):
        """Stop voice recognition - same as mini app"""
        try:
            if self._is_listening:
                self._is_listening = False
                self.listen_timer.stop()
                self.statusChanged.emit("🔇 Voice recognition stopped")
        except Exception as e:
            self.errorOccurred.emit(f"Voice stop error: {str(e)}")
    
    @Slot(str)
    def sendTextCommand(self, command: str):
        """Send text command (for manual input or testing)"""
        if self._is_cooking and self.cooking_service.agent:
            self.cooking_service.agent.send_command(command)
    
    @Slot()
    def testMicrophone(self):
        """Test microphone access - same as mini app"""
        try:
            if self.cooking_service and self.cooking_service.agent:
                self.statusChanged.emit("🎙️ Testing microphone - say 'Hello Su-Chef'")
                
                result = self.cooking_service.agent.recognizer.recognize_once_async().get()
                
                if result.reason.name == "RecognizedSpeech":
                    self.statusChanged.emit(f"✅ Microphone working! Heard: '{result.text}'")
                    self.heardText.emit(result.text)
                else:
                    self.statusChanged.emit("❌ No speech recognized - check microphone")
            else:
                self.statusChanged.emit("❌ No cooking agent available for microphone test")
        except Exception as e:
            self.errorOccurred.emit(f"❌ Microphone test failed: {str(e)}")
    
    def check_voice_input(self):
        """Check for voice input (called by timer) - improved sensitivity"""
        if not self._is_listening or not self.cooking_service or not self.cooking_service.agent:
            return
            
        try:
            # Improved voice recognition with better timeout settings
            recognizer = self.cooking_service.agent.recognizer
            
            # Set better recognition properties for continuous listening
            speech_config = recognizer.speech_config
            speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
            speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "2000")
            
            result = recognizer.recognize_once_async().get()
            
            if result.reason.name == "RecognizedSpeech":
                text = result.text.strip()
                self.heardText.emit(text)  # Send to QML
                self.statusChanged.emit(f"🎤 Heard: '{text}'")
                
                # Process the voice command using AI intent classification (same as CLI)
                if self.cooking_service.agent:
                    try:
                        # Use the same AI-powered intent classification as CLI
                        intent_data = self.cooking_service.agent.classify_intent(text)
                        intent = intent_data.get("intent", "UNKNOWN")
                        
                        print(f"DEBUG: Voice command '{text}' classified as '{intent}'")
                        
                        if intent == "NAVIGATION":
                            self.nextStep()
                        elif intent == "REPEAT":
                            self.repeatStep()
                        elif intent == "INGREDIENTS":
                            self.cooking_service.agent.send_command("ingredients")
                        elif intent == "STOP":
                            self.stopCooking()
                        elif intent in ["CLARIFICATION", "TIMING", "TECHNIQUE", "TROUBLESHOOTING", "QUESTION"]:
                            # Use AI to answer the question (same as CLI)
                            response = self.cooking_service.agent.get_ai_response(text)
                            if response:
                                self.statusChanged.emit(f"🤖 {response}")
                                # Also speak the response
                                self.cooking_service.agent.speak(response)
                        else:
                            # Fallback to simple keyword matching
                            command = text.lower()
                            if any(word in command for word in ["next", "continue", "move"]):
                                self.nextStep()
                            elif any(word in command for word in ["repeat", "again"]):
                                self.repeatStep()
                            elif any(word in command for word in ["back", "previous"]):
                                self.backStep()
                            elif "ingredient" in command:
                                self.cooking_service.agent.send_command("ingredients")
                            elif any(word in command for word in ["stop", "quit", "end"]):
                                self.stopCooking()
                            else:
                                self.statusChanged.emit(f"❓ Try: 'next', 'repeat', 'back', 'ingredients', or ask a cooking question")
                    except Exception as e:
                        print(f"DEBUG: Intent classification failed: {e}")
                        # Fallback to simple matching
                        command = text.lower()
                        if "next" in command:
                            self.nextStep()
                        elif "repeat" in command:
                            self.repeatStep()
                        else:
                            self.statusChanged.emit(f"❓ Try: 'next', 'repeat', 'back', 'ingredients'")
                    
        except Exception as e:
            # Ignore recognition errors (happens when no speech detected)
            pass
    
    @Slot('QVariant')
    def saveRecipe(self, recipe_data):
        """Save recipe to database"""
        try:
            if not self._current_user:
                self.errorOccurred.emit("Please login first")
                return
            
            # Convert QML object to Python dict if needed
            if hasattr(recipe_data, 'toVariant'):
                recipe_dict = recipe_data.toVariant()
            else:
                recipe_dict = dict(recipe_data) if recipe_data else {}
            
            recipe_id = self.db_service.save_recipe(recipe_dict)
            self.statusChanged.emit(f"Recipe saved with ID: {recipe_id}")
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to save recipe: {str(e)}")
    
    @Slot(str)
    def loadUserRecipes(self, recipe_type: str = "all"):
        """Load user's saved recipes"""
        try:
            if not self._current_user:
                self.recipesLoaded.emit([])
                return
            
            recipes = self.db_service.get_user_recipes(recipe_type)
            self.recipesLoaded.emit(recipes)
            
        except Exception as e:
            self.errorOccurred.emit(f"Failed to load recipes: {str(e)}")
            self.recipesLoaded.emit([])
    
    @Slot(int, result='QVariant')
    def getRecipeDetails(self, recipe_id: int):
        """Get detailed recipe information"""
        try:
            details = self.db_service.get_recipe_details(recipe_id)
            return details if details else {}
        except Exception as e:
            self.errorOccurred.emit(f"Failed to get recipe details: {str(e)}")
            return {}
    
    # Callback handlers (called from services)
    def on_speech_heard(self, text: str):
        """Handle speech recognition result"""
        self.heardText.emit(text)
    
    def on_step_changed(self, step_index: int):
        """Handle cooking step change"""
        self.stepChanged.emit(step_index)
    
    def on_status_changed(self, status: str):
        """Handle status update"""
        self.statusChanged.emit(status)
    
    def on_error_occurred(self, error: str):
        """Handle error"""
        self.errorOccurred.emit(error)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Su-Chef")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Su-Chef")
    
    # Create QML engine
    engine = QQmlApplicationEngine()
    
    # Create and register backend
    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)
    
    # Load main QML file
    qml_file = os.path.join(os.path.dirname(__file__), "ui", "Main.qml")
    engine.load(QUrl.fromLocalFile(qml_file))
    
    # Check if QML loaded successfully
    if not engine.rootObjects():
        print("Failed to load QML file")
        sys.exit(-1)
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
