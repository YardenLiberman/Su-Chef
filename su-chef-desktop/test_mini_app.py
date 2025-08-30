#!/usr/bin/env python3
"""
Mini Desktop App to Test Voice Integration
Simple Qt app with buttons to test voice commands
"""

import sys
import threading
from PySide6.QtCore import QObject, Slot, Signal, QTimer
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt

from core.services import RecipeService, CookingService
from core.cooking_agent_cli import CookingAgent as CLICookingAgent

class MiniVoiceTest(QWidget):
    def __init__(self):
        super().__init__()
        self.cooking_service = None
        self.recipe_service = RecipeService()
        self.is_listening = False
        self.listen_timer = QTimer()
        self.listen_timer.timeout.connect(self.check_voice_input)
        self.voice_thread = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("🎤 Su-Chef Voice Test")
        self.setGeometry(100, 100, 600, 500)
        self.setStyleSheet("""
            QWidget { 
                background-color: #1a1a1a; 
                color: white; 
                font-family: Arial;
            }
            QPushButton { 
                background-color: #333; 
                border: 2px solid #555; 
                border-radius: 8px; 
                padding: 10px; 
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #444; 
                border-color: #00ff99;
            }
            QPushButton:pressed { 
                background-color: #555; 
            }
            QPushButton:disabled {
                background-color: #222;
                color: #666;
                border-color: #333;
            }
            QLabel { 
                font-size: 16px; 
                padding: 10px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                border: 2px solid #555;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Courier New';
            }
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🎤 Su-Chef Voice Integration Test")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ff99; padding: 20px;")
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("Ready to test voice integration")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")
        layout.addWidget(self.status_label)
        
        # Recipe info
        self.recipe_info = QLabel("No recipe loaded")
        self.recipe_info.setAlignment(Qt.AlignCenter)
        self.recipe_info.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.recipe_info)
        
        # Step info
        self.step_info = QLabel("Step: -")
        self.step_info.setAlignment(Qt.AlignCenter)
        self.step_info.setStyleSheet("color: #00ff99; font-size: 18px; font-weight: bold;")
        layout.addWidget(self.step_info)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🎲 Generate Recipe")
        self.generate_btn.clicked.connect(self.generate_recipe)
        button_layout.addWidget(self.generate_btn)
        
        self.start_btn = QPushButton("▶️ Start Cooking")
        self.start_btn.clicked.connect(self.start_cooking)
        self.start_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        
        layout.addLayout(button_layout)
        
        # Voice command buttons
        voice_layout = QHBoxLayout()
        
        self.next_btn = QPushButton("⏭️ Next")
        self.next_btn.clicked.connect(self.next_step)
        self.next_btn.setEnabled(False)
        voice_layout.addWidget(self.next_btn)
        
        self.repeat_btn = QPushButton("🔁 Repeat")
        self.repeat_btn.clicked.connect(self.repeat_step)
        self.repeat_btn.setEnabled(False)
        voice_layout.addWidget(self.repeat_btn)
        
        self.back_btn = QPushButton("⏮️ Back")
        self.back_btn.clicked.connect(self.back_step)
        self.back_btn.setEnabled(False)
        voice_layout.addWidget(self.back_btn)
        
        self.ingredients_btn = QPushButton("📋 Ingredients")
        self.ingredients_btn.clicked.connect(self.ingredients)
        self.ingredients_btn.setEnabled(False)
        voice_layout.addWidget(self.ingredients_btn)
        
        layout.addLayout(voice_layout)
        
        # Stop button
        self.stop_btn = QPushButton("🛑 Stop Cooking")
        self.stop_btn.clicked.connect(self.stop_cooking)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # Voice recognition test
        voice_test_layout = QHBoxLayout()
        
        self.listen_btn = QPushButton("🎤 Listen Once")
        self.listen_btn.clicked.connect(self.listen_once)
        self.listen_btn.setEnabled(False)
        self.listen_btn.setStyleSheet("""
            QPushButton { 
                background-color: #ff6b35; 
                border: 2px solid #ff8c42; 
            }
            QPushButton:hover { 
                background-color: #ff8c42; 
                border-color: #ffaa00;
            }
        """)
        voice_test_layout.addWidget(self.listen_btn)
        
        self.test_mic_btn = QPushButton("🎙️ Test Microphone")
        self.test_mic_btn.clicked.connect(self.test_microphone)
        voice_test_layout.addWidget(self.test_mic_btn)
        
        layout.addLayout(voice_test_layout)
        
        # Voice recognition status
        self.voice_status = QLabel("Voice recognition: Not active")
        self.voice_status.setAlignment(Qt.AlignCenter)
        self.voice_status.setStyleSheet("color: #888; font-size: 12px; padding: 5px;")
        layout.addWidget(self.voice_status)
        
        # Log area
        log_label = QLabel("📝 Voice Output Log:")
        log_label.setStyleSheet("color: #00ff99; font-weight: bold; margin-top: 20px;")
        layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        self.setLayout(layout)
        
    def log(self, message):
        """Add message to log area"""
        self.log_area.append(f"🔊 {message}")
        
    def generate_recipe(self):
        """Generate a test recipe"""
        self.status_label.setText("Generating recipe...")
        self.generate_btn.setEnabled(False)
        
        # Generate recipe
        result = self.recipe_service.generate({
            'meal_type': 'dinner',
            'time_limit': 20,
            'skill': 'beginner',
            'diet': None,
            'available': []
        })
        
        if result and result.get('success'):
            self.current_recipe = result['recipe']
            self.recipe_info.setText(f"Recipe: {self.current_recipe['name']} ({len(self.current_recipe['instructions'])} steps)")
            self.status_label.setText("Recipe generated! Click 'Start Cooking' to test voice.")
            self.start_btn.setEnabled(True)
            self.log(f"Generated recipe: {self.current_recipe['name']}")
        else:
            self.status_label.setText("❌ Recipe generation failed")
            self.generate_btn.setEnabled(True)
            
    def start_cooking(self):
        """Start cooking session"""
        self.status_label.setText("Starting cooking session...")
        
        # Create cooking service
        self.cooking_service = CookingService()
        success = self.cooking_service.start(self.current_recipe)
        
        if success and self.cooking_service.agent:
            # Start voice session
            session_started = self.cooking_service.agent.start_session()
            
            if session_started:
                self.status_label.setText("🎤 Voice cooking session active!")
                self.update_step_display()
                
                # Enable voice buttons
                self.next_btn.setEnabled(True)
                self.repeat_btn.setEnabled(True)
                self.back_btn.setEnabled(True)
                self.ingredients_btn.setEnabled(True)
                self.stop_btn.setEnabled(True)
                
                # Enable voice recognition test
                self.test_mic_btn.setEnabled(True)
                
                # Disable start buttons
                self.start_btn.setEnabled(False)
                self.generate_btn.setEnabled(False)
                
                # Speak first step
                self.cooking_service.agent.speak_current_step()
                self.log("Started cooking session - spoke first step")
            else:
                self.status_label.setText("❌ Failed to start voice session")
        else:
            self.status_label.setText("❌ Failed to start cooking service")
            
    def update_step_display(self):
        """Update step display"""
        if self.cooking_service and self.cooking_service.agent:
            current = self.cooking_service.agent.current_step + 1
            total = len(self.cooking_service.agent.recipe_steps)
            self.step_info.setText(f"Step: {current}/{total}")
            
    def next_step(self):
        """Next step command"""
        if self.cooking_service and self.cooking_service.agent:
            self.cooking_service.agent.send_command("next")
            self.update_step_display()
            self.log("Command: Next step")
            
    def repeat_step(self):
        """Repeat step command"""
        if self.cooking_service and self.cooking_service.agent:
            self.cooking_service.agent.send_command("repeat")
            self.log("Command: Repeat step")
            
    def back_step(self):
        """Back step command"""
        if self.cooking_service and self.cooking_service.agent:
            self.cooking_service.agent.send_command("back")
            self.update_step_display()
            self.log("Command: Back step")
            
    def ingredients(self):
        """Ingredients command"""
        if self.cooking_service and self.cooking_service.agent:
            self.cooking_service.agent.send_command("ingredients")
            self.log("Command: List ingredients")
            
    def stop_cooking(self):
        """Stop cooking session"""
        if self.cooking_service and self.cooking_service.agent:
            self.cooking_service.agent.send_command("stop")
            
        self.status_label.setText("Cooking session stopped")
        self.step_info.setText("Step: -")
        
        # Disable voice buttons
        self.next_btn.setEnabled(False)
        self.repeat_btn.setEnabled(False)
        self.back_btn.setEnabled(False)
        self.ingredients_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        # Enable start buttons
        self.generate_btn.setEnabled(True)
        
        self.log("Stopped cooking session")
        
    def test_microphone(self):
        """Test microphone access - CLI style"""
        self.log("Testing microphone...")
        self.voice_status.setText("🎙️ Testing microphone - say something...")
        
        if self.cooking_service and self.cooking_service.agent:
            # Test microphone using the CLI-style listen method
            try:
                self.log("Say something clearly (like 'next' or 'repeat')...")
                text = self.cooking_service.agent.listen()
                
                if text:
                    self.log(f"✅ Microphone working! Heard: '{text}'")
                    self.voice_status.setText(f"✅ Microphone OK - Heard: '{text}'")
                    self.listen_btn.setEnabled(True)
                    
                    # Process the command immediately like CLI
                    self.process_voice_command(text)
                else:
                    self.log("❌ No speech recognized")
                    self.voice_status.setText("❌ No speech recognized - check microphone")
            except Exception as e:
                self.log(f"❌ Microphone test failed: {e}")
                self.voice_status.setText("❌ Microphone test failed")
        else:
            self.log("❌ No cooking agent available for microphone test")
            
    def process_voice_command(self, text):
        """Process voice command using CLI-style AI classification"""
        try:
            intent_data = self.cooking_service.agent.classify_intent(text)
            intent = intent_data.get("intent", "UNKNOWN")
            
            self.log(f"🧠 Intent: {intent}")
            
            if intent == "NAVIGATION":
                self.next_step()
            elif intent == "REPEAT":
                self.repeat_step()
            elif intent == "INGREDIENTS":
                self.ingredients()
            elif intent == "STOP":
                self.stop_cooking()
            elif intent in ["CLARIFICATION", "TIMING", "TECHNIQUE", "TROUBLESHOOTING", "QUESTION"]:
                # Use AI to answer the question like CLI
                response = self.cooking_service.agent.get_ai_response(text)
                if response:
                    self.log(f"🤖 {response}")
                    self.cooking_service.agent.speak(response)
            else:
                # Fallback to simple keyword matching
                command = text.lower()
                if "next" in command:
                    self.next_step()
                elif "repeat" in command or "again" in command:
                    self.repeat_step()
                elif "back" in command or "previous" in command:
                    self.back_step()
                elif "ingredient" in command:
                    self.ingredients()
                elif "stop" in command or "quit" in command:
                    self.stop_cooking()
                else:
                    self.log(f"❓ Unknown command: '{text}' - try 'next', 'repeat', 'back', 'ingredients'")
        except Exception as e:
            self.log(f"❌ Intent classification failed: {e}")
            # Fallback to simple commands
            command = text.lower()
            if "next" in command:
                self.next_step()
            elif "repeat" in command or "again" in command:
                self.repeat_step()
            elif "back" in command or "previous" in command:
                self.back_step()
            elif "ingredient" in command:
                self.ingredients()
            elif "stop" in command or "quit" in command:
                self.stop_cooking()
            else:
                self.log(f"❓ Unknown command: '{text}' - try 'next', 'repeat', 'back', 'ingredients'")
            
    def listen_once(self):
        """Listen for one voice command - CLI style"""
        if self.cooking_service and self.cooking_service.agent:
            self.log("🎤 Listening... speak now!")
            self.voice_status.setText("🎤 Listening for command...")
            
            try:
                text = self.cooking_service.agent.listen()
                if text:
                    self.log(f"🎤 Heard: '{text}'")
                    self.process_voice_command(text)
                else:
                    self.log("❌ No speech recognized")
                    self.voice_status.setText("❌ No speech - try again")
            except Exception as e:
                self.log(f"❌ Voice recognition failed: {e}")
                self.voice_status.setText("❌ Voice recognition failed")
        else:
            self.log("❌ No cooking agent available")
            
    def toggle_listening(self):
        """Toggle voice recognition on/off"""
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
            
    def start_listening(self):
        """Start continuous voice recognition"""
        if self.cooking_service and self.cooking_service.agent:
            self.is_listening = True
            self.listen_btn.setText("🔇 Stop Listening")
            self.listen_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #00ff99; 
                    border: 2px solid #00cc77; 
                    color: black;
                }
                QPushButton:hover { 
                    background-color: #00cc77; 
                    border-color: #009955;
                }
            """)
            self.voice_status.setText("🎤 Listening for voice commands...")
            self.log("Started voice recognition - try saying 'next', 'repeat', 'back', 'ingredients'")
            
            # Start background thread for voice recognition
            self.voice_thread = threading.Thread(target=self.voice_recognition_loop, daemon=True)
            self.voice_thread.start()
            
    def stop_listening(self):
        """Stop voice recognition"""
        self.is_listening = False
        self.listen_btn.setText("🎤 Start Listening")
        self.listen_btn.setStyleSheet("""
            QPushButton { 
                background-color: #ff6b35; 
                border: 2px solid #ff8c42; 
            }
            QPushButton:hover { 
                background-color: #ff8c42; 
                border-color: #ffaa00;
            }
        """)
        self.voice_status.setText("🔇 Voice recognition stopped")
        self.log("Stopped voice recognition")
        
    def check_voice_input(self):
        """Check for voice input (called by timer)"""
        if not self.is_listening or not self.cooking_service or not self.cooking_service.agent:
            return
            
        try:
            # Use the CLI-style listen method that works properly
            text = self.cooking_service.agent.listen()
            
            if text:
                self.log(f"🎤 Heard: '{text}'")
                
                # Use AI intent classification like CLI
                try:
                    intent_data = self.cooking_service.agent.classify_intent(text)
                    intent = intent_data.get("intent", "UNKNOWN")
                    
                    self.log(f"🧠 Intent: {intent}")
                    
                    if intent == "NAVIGATION":
                        self.next_step()
                    elif intent == "REPEAT":
                        self.repeat_step()
                    elif intent == "INGREDIENTS":
                        self.ingredients()
                    elif intent == "STOP":
                        self.stop_cooking()
                    elif intent in ["CLARIFICATION", "TIMING", "TECHNIQUE", "TROUBLESHOOTING", "QUESTION"]:
                        # Use AI to answer the question like CLI
                        response = self.cooking_service.agent.get_ai_response(text)
                        if response:
                            self.log(f"🤖 {response}")
                            self.cooking_service.agent.speak(response)
                    else:
                        # Fallback to simple keyword matching
                        command = text.lower()
                        if "next" in command:
                            self.next_step()
                        elif "repeat" in command or "again" in command:
                            self.repeat_step()
                        elif "back" in command or "previous" in command:
                            self.back_step()
                        elif "ingredient" in command:
                            self.ingredients()
                        elif "stop" in command or "quit" in command:
                            self.stop_cooking()
                        else:
                            self.log(f"❓ Unknown command: '{text}' - try 'next', 'repeat', 'back', 'ingredients'")
                except Exception as e:
                    self.log(f"❌ Intent classification failed: {e}")
                    # Fallback to simple commands
                    command = text.lower()
                    if "next" in command:
                        self.next_step()
                    elif "repeat" in command or "again" in command:
                        self.repeat_step()
                    elif "back" in command or "previous" in command:
                        self.back_step()
                    elif "ingredient" in command:
                        self.ingredients()
                    elif "stop" in command or "quit" in command:
                        self.stop_cooking()
                    else:
                        self.log(f"❓ Unknown command: '{text}' - try 'next', 'repeat', 'back', 'ingredients'")
                    
        except Exception as e:
            # Ignore recognition errors (happens when no speech detected)
            pass
            
    def voice_recognition_loop(self):
        """Background thread for continuous voice recognition"""
        while self.is_listening:
            if self.cooking_service and self.cooking_service.agent:
                try:
                    text = self.cooking_service.agent.listen()
                    if text and self.is_listening:  # Check if still listening
                        # Process in main thread
                        self.check_voice_input()
                except Exception as e:
                    if self.is_listening:  # Only log if we're still supposed to be listening
                        self.log(f"Voice recognition error: {e}")
                    break

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Su-Chef Voice Test")
    
    window = MiniVoiceTest()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
