#!/usr/bin/env python3
"""
Su-Chef Cooking Desktop Application
Voice-only cooking assistant that receives recipe data from web app
"""

import sys
import os
import json
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QTextEdit, QProgressBar,
                             QMessageBox, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap
try:
    import azure.cognitiveservices.speech as speechsdk
    print("Azure Speech SDK imported successfully")
except ImportError as e:
    print(f"Failed to import Azure Speech SDK: {e}")
    print("Please install: pip install azure-cognitiveservices-speech")
    speechsdk = None
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VoiceRecognitionThread(QThread):
    """Thread for continuous voice recognition"""
    voice_command = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, speech_key, speech_region):
        super().__init__()
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.is_listening = False
        self.speech_recognizer = None
        
    def run(self):
        """Start continuous voice recognition"""
        try:
            if not speechsdk:
                error_msg = "Azure Speech SDK not available. Please install: pip install azure-cognitiveservices-speech"
                print(f"❌ {error_msg}")
                self.error_occurred.emit(error_msg)
                return
                
            print(f"🎤 Starting voice recognition with key: {self.speech_key[:8]}... and region: {self.speech_region}")
            
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, 
                region=self.speech_region
            )
            speech_config.speech_recognition_language = "en-US"
            
            # Configure for better recognition - more sensitive settings
            speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "3000")
            speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "3000")
            speech_config.set_property(speechsdk.PropertyId.Speech_LogFilename, "speech_log.txt")
            
            print("🎤 Speech config created successfully")
            
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            print("🎤 Audio config created successfully")
            
            self.speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            print("🎤 Speech recognizer created successfully")
            
            # Connect events
            self.speech_recognizer.recognized.connect(self.on_recognized)
            self.speech_recognizer.recognizing.connect(self.on_recognizing)
            self.speech_recognizer.canceled.connect(self.on_canceled)
            print("🎤 Event handlers connected successfully")
            
            # Start continuous recognition
            print("🎤 Starting continuous recognition...")
            self.speech_recognizer.start_continuous_recognition()
            self.is_listening = True
            print("🎤 Continuous recognition started successfully")
            
            # Keep the thread alive while listening
            while self.is_listening:
                self.msleep(100)
                
        except Exception as e:
            print(f"❌ Voice recognition error in thread: {str(e)}")
            self.error_occurred.emit(f"Voice recognition error: {str(e)}")
    
    def on_recognized(self, event):
        """Handle recognized speech"""
        try:
            if event.result.text:
                print(f"🎤 Voice recognized: {event.result.text}")
                print(f"🎤 Confidence: {event.result.reason}")
                print(f"🎤 Result reason: {event.result.reason}")
                self.voice_command.emit(event.result.text.lower())
            else:
                print("🎤 No text recognized")
                
            # Debug: Print all event properties
            print(f"🎤 Event type: {type(event)}")
            print(f"🎤 Event result: {event.result}")
            if hasattr(event, 'result'):
                print(f"🎤 Result text: {event.result.text}")
                print(f"🎤 Result reason: {event.result.reason}")
                print(f"🎤 Result confidence: {getattr(event.result, 'confidence', 'N/A')}")
        except Exception as e:
            print(f"🎤 Error in on_recognized: {e}")
            self.error_occurred.emit(f"Recognition error: {str(e)}")
    
    def on_recognizing(self, event):
        """Handle speech being recognized (intermediate results)"""
        if event.result.text:
            print(f"🎤 Recognizing: {event.result.text}")
    
    def on_canceled(self, event):
        """Handle speech recognition cancellation"""
        print(f"🎤 Recognition canceled: {event.reason}")
        if event.reason == speechsdk.CancellationReason.ERROR:
            print(f"🎤 Error details: {event.error_details}")
            self.error_occurred.emit(f"Recognition canceled: {event.error_details}")
        elif event.reason == speechsdk.CancellationReason.END_OF_AUDIO:
            print("🎤 End of audio detected")
        elif event.reason == speechsdk.CancellationReason.END_OF_STREAM:
            print("🎤 End of stream detected")
    

    
    def stop_listening(self):
        """Stop voice recognition"""
        self.is_listening = False
        if self.speech_recognizer:
            try:
                self.speech_recognizer.stop_continuous_recognition()
                print("🎤 Voice recognition stopped")
            except Exception as e:
                print(f"❌ Error stopping recognition: {e}")
    
    def pause_listening(self):
        """Pause voice recognition temporarily"""
        if self.speech_recognizer and self.is_listening:
            try:
                # Don't actually stop - just mark as paused
                print("🎤 Voice recognition paused (soft pause)")
            except Exception as e:
                print(f"❌ Error pausing recognition: {e}")
    
    def resume_listening(self):
        """Resume voice recognition"""
        if self.speech_recognizer and self.is_listening:
            try:
                # Don't actually restart - just mark as resumed
                print("🎤 Voice recognition resumed (soft resume)")
            except Exception as e:
                print(f"❌ Error resuming recognition: {e}")

class TextToSpeechThread(QThread):
    """Thread for text-to-speech synthesis"""
    speech_finished = pyqtSignal()
    
    def __init__(self, speech_key, speech_region, text):
        super().__init__()
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.text = text
        
    def run(self):
        """Synthesize speech"""
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, 
                region=self.speech_region
            )
            speech_config.speech_synthesis_voice_name = "en-US-JennyMultilingualNeural"
            
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            result = speech_synthesizer.speak_text_async(self.text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                self.speech_finished.emit()
            else:
                print(f"Speech synthesis failed: {result.reason}")
                
        except Exception as e:
            print(f"Text-to-speech error: {str(e)}")
            self.speech_finished.emit()

class CookingAssistant(QMainWindow):
    """Main cooking assistant window"""
    
    def __init__(self, recipe_data=None, recipe_source=None):
        super().__init__()
        self.speech_key = os.getenv("SPEECH_KEY")
        self.speech_region = os.getenv("SPEECH_REGION", "westeurope")
        
        if not self.speech_key:
            QMessageBox.critical(self, "Error", "Missing SPEECH_KEY. Please check your .env file.")
            sys.exit(1)
        
        # State machine for cooking session
        self.cooking_state = "IDLE"  # IDLE -> INTRO -> WAIT_READY -> STEP_ACTIVE -> PAUSED -> DONE
        
        self.voice_thread = None
        self.tts_thread = None
        self.current_recipe = recipe_data
        self.recipe_source = recipe_source
        self.current_step = 0
        self.is_cooking = False
        self.cooking_timer = QTimer()
        self.cooking_timer.timeout.connect(self.update_cooking_timer)
        self.elapsed_time = 0
        
        # Voice command debouncing
        self.last_command_time = None
        self.last_command = None
        
        self.init_ui()
        
        # Handle recipe loading based on source
        if self.current_recipe:
            if self.recipe_source == 'deep_link':
                self.fetch_recipe_from_api()
            else:
                self.load_recipe()
        
        # Voice recognition will start when user clicks "Start Cooking"
    
    def fetch_recipe_from_api(self):
        """Fetch recipe data from the web app API"""
        try:
            recipe_id = self.current_recipe.get('id')
            if not recipe_id:
                self.log_command("❌ No recipe ID found in deep link")
                return
            
            self.log_command(f"🔗 Deep link received for recipe ID: {recipe_id}")
            # Don't speak automatically - let user control when to start
            
            # Import requests for HTTP calls
            import requests
            
            # Make API call to fetch recipe data
            api_url = f"http://localhost:5000/api/recipe/{recipe_id}/data"
            
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    recipe_data = response.json()
                    
                    # Update the current recipe with fetched data
                    self.current_recipe = recipe_data
                    
                    # Load the recipe into the UI
                    self.load_recipe()
                    
                    self.log_command(f"✅ Recipe loaded successfully: {recipe_data.get('name', 'Unknown')}")
                    # Don't speak automatically - let user control when to start
                    
                else:
                    error_msg = f"API error: {response.status_code}"
                    self.log_command(f"❌ {error_msg}")
                    # Don't speak errors automatically - let user control when to start
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Network error: {str(e)}"
                self.log_command(f"❌ {error_msg}")
                # Don't speak errors automatically - let user control when to start
                
        except Exception as e:
            self.log_command(f"❌ Error fetching recipe from API: {str(e)}")
            # Don't speak errors automatically - let user control when to start
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Su-Chef Voice Cooking Assistant")
        self.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Su-Chef Voice Cooking Assistant")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 20px;")
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("🎤 Listening for voice commands...")
        self.status_label.setFont(QFont("Arial", 16))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #27ae60; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # State Display
        self.state_label = QLabel("State: IDLE")
        self.state_label.setFont(QFont("Arial", 12))
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet("color: #7f8c8d; margin: 5px;")
        layout.addWidget(self.state_label)
        
        # Recipe Info
        self.recipe_info = QFrame()
        self.recipe_info.setFrameStyle(QFrame.Shape.StyledPanel)
        self.recipe_info.setStyleSheet("QFrame { background-color: #ecf0f1; border-radius: 10px; padding: 15px; }")
        recipe_info_layout = QVBoxLayout(self.recipe_info)
        
        self.recipe_name_label = QLabel("No Recipe Loaded")
        self.recipe_name_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.recipe_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        recipe_info_layout.addWidget(self.recipe_name_label)
        
        self.recipe_details_label = QLabel("")
        self.recipe_details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        recipe_info_layout.addWidget(self.recipe_details_label)
        
        layout.addWidget(self.recipe_info)
        
        # Cooking Controls
        controls_layout = QHBoxLayout()
        
        self.start_cooking_btn = QPushButton("Start Cooking")
        self.start_cooking_btn.setFont(QFont("Arial", 14))
        self.start_cooking_btn.clicked.connect(self.start_cooking)
        self.start_cooking_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        controls_layout.addWidget(self.start_cooking_btn)
        
        self.stop_cooking_btn = QPushButton("Stop Cooking")
        self.stop_cooking_btn.setFont(QFont("Arial", 14))
        self.stop_cooking_btn.clicked.connect(self.stop_cooking)
        self.stop_cooking_btn.setEnabled(False)
        self.stop_cooking_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        controls_layout.addWidget(self.stop_cooking_btn)
        
        # Debug Voice Button (temporary)
        self.debug_voice_btn = QPushButton("Debug Voice")
        self.debug_voice_btn.setFont(QFont("Arial", 12))
        self.debug_voice_btn.clicked.connect(self.debug_voice_recognition)
        self.debug_voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        controls_layout.addWidget(self.debug_voice_btn)
        
        # Ready Button (initially hidden)
        self.ready_btn = QPushButton("🚀 I'm Ready to Cook!")
        self.ready_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.ready_btn.clicked.connect(self.user_ready)
        self.ready_btn.setVisible(False)
        self.ready_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        controls_layout.addWidget(self.ready_btn)
        
        layout.addLayout(controls_layout)
        
        # Cooking Progress
        self.progress_group = QFrame()
        self.progress_group.setFrameStyle(QFrame.Shape.StyledPanel)
        self.progress_group.setStyleSheet("QFrame { background-color: #f8f9fa; border-radius: 10px; padding: 15px; }")
        self.progress_group.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_group)
        
        progress_title = QLabel("Cooking Progress")
        progress_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        progress_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(progress_title)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 8px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.step_label = QLabel("Step 0 of 0")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label.setFont(QFont("Arial", 12))
        progress_layout.addWidget(self.step_label)
        
        layout.addWidget(self.progress_group)
        
        # Current Step Display
        self.step_display = QFrame()
        self.step_display.setFrameStyle(QFrame.Shape.StyledPanel)
        self.step_display.setStyleSheet("QFrame { background-color: #e8f5e8; border-radius: 10px; padding: 20px; }")
        self.step_display.setVisible(False)
        step_layout = QVBoxLayout(self.step_display)
        
        step_title = QLabel("Current Step")
        step_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        step_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        step_layout.addWidget(step_title)
        
        self.current_step_text = QTextEdit()
        self.current_step_text.setReadOnly(True)
        self.current_step_text.setMaximumHeight(100)
        self.current_step_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #27ae60;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        step_layout.addWidget(self.current_step_text)
        
        # Step Navigation
        nav_layout = QHBoxLayout()
        
        self.next_step_btn = QPushButton("Next Step")
        self.next_step_btn.clicked.connect(self.next_step)
        self.next_step_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        nav_layout.addWidget(self.next_step_btn)
        
        step_layout.addLayout(nav_layout)
        layout.addWidget(self.step_display)
        
        # Cooking Timer
        self.timer_group = QFrame()
        self.timer_group.setFrameStyle(QFrame.Shape.StyledPanel)
        self.timer_group.setStyleSheet("QFrame { background-color: #fff3cd; border-radius: 10px; padding: 15px; }")
        self.timer_group.setVisible(False)
        timer_layout = QVBoxLayout(self.timer_group)
        
        timer_title = QLabel("Cooking Timer")
        timer_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        timer_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(timer_title)
        
        self.timer_display = QLabel("00:00")
        self.timer_display.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_display.setStyleSheet("color: #e67e22;")
        timer_layout.addWidget(self.timer_display)
        
        layout.addWidget(self.timer_group)
        
        # Voice command log
        self.command_log = QTextEdit()
        self.command_log.setReadOnly(True)
        self.command_log.setMaximumHeight(120)
        self.command_log.setPlaceholderText("Voice commands will appear here...")
        self.command_log.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Courier New';
            }
        """)
        layout.addWidget(QLabel("Voice Commands:"))
        layout.addWidget(self.command_log)
        

        
        # Voice commands help
        help_text = """
Voice Commands:
• "Start cooking" - Begin cooking process
• "Ready" - Start cooking after explanation
• "Next" - Go to next cooking step
• "Repeat" - Repeat current step
• "Help" - Ask cooking questions
        """
        help_label = QLabel(help_text)
        help_label.setFont(QFont("Arial", 10))
        help_label.setStyleSheet("color: #7f8c8d; background-color: #ecf0f1; padding: 10px; border-radius: 5px;")
        layout.addWidget(help_label)
        
    def debug_voice_recognition(self):
        """Debug voice recognition functionality"""
        try:
            if not self.voice_thread or not self.voice_thread.is_listening:
                self.speak("Voice recognition not active. Please start cooking first.")
                return
            
            self.speak("Testing voice recognition. Please say 'ready' clearly.")
            self.log_command("Debug: Testing voice recognition...")
            
            # Check current state
            self.log_command(f"Debug: Current cooking state: {self.cooking_state}")
            self.log_command(f"Debug: Voice thread status: {self.voice_thread.is_listening if self.voice_thread else 'None'}")
            
        except Exception as e:
            self.log_command(f"Debug error: {str(e)}")
            self.speak("Debug test failed. Check console for details.")
    
    def start_voice_recognition(self):
        """Start continuous voice recognition"""
        try:
            # Check if Azure Speech credentials are valid
            if not self.speech_key or not self.speech_region:
                error_msg = "Missing Azure Speech credentials. Check your .env file for SPEECH_KEY and SPEECH_REGION."
                self.log_command(f"❌ {error_msg}")
                self.status_label.setText("❌ Voice recognition failed - missing credentials")
                QMessageBox.critical(self, "Voice Recognition Error", error_msg)
                return
            
            self.log_command(f"🔑 Starting voice recognition with region: {self.speech_region}")
            
            # Create and start voice recognition thread
            self.voice_thread = VoiceRecognitionThread(self.speech_key, self.speech_region)
            self.voice_thread.voice_command.connect(self.handle_voice_command)
            self.voice_thread.error_occurred.connect(self.handle_voice_error)
            self.voice_thread.start()
            
            # Voice recognition started - no automatic test
            
        except Exception as e:
            error_msg = f"Failed to start voice recognition: {str(e)}"
            self.log_command(f"❌ {error_msg}")
            self.status_label.setText("❌ Voice recognition failed")
            QMessageBox.critical(self, "Voice Recognition Error", error_msg)
    

    def handle_voice_command(self, command):
        """Handle voice commands"""
        try:
            # Prevent duplicate commands within a short time
            current_time = datetime.now()
            if hasattr(self, 'last_command_time') and hasattr(self, 'last_command'):
                time_diff = (current_time - self.last_command_time).total_seconds()
                if time_diff < 1.0 and command.lower() == self.last_command.lower():
                    self.log_command(f"🎤 Ignoring duplicate command: {command}")
                    return
            
            self.last_command_time = current_time
            self.last_command = command
            
            self.log_command(f"🎤 Heard: {command}")
            self.log_command(f"🎤 Current state: {self.cooking_state}")
            
            # Convert to lowercase for better matching
            command_lower = command.lower()
            
            # Handle commands based on current state
            if self.cooking_state == "WAIT_READY":
                # Only allow "ready" commands in WAIT_READY state
                if any(phrase in command_lower for phrase in ["ready", "i'm ready", "let's start", "start", "יאללה", "אני מוכן", "אני מוכנה"]):
                    self.log_command(f"🎤 Processing 'ready' command in WAIT_READY state")
                    self.speak("Perfect! You're ready to cook!")
                    self.user_ready()
                else:
                    self.log_command(f"🎤 Ignored command in WAIT_READY state: {command}")
                    self.speak("Please say 'ready' when you want to start cooking.")
                    
            elif self.cooking_state == "STEP_ACTIVE":
                # Only respond to specific commands: next, repeat, help
                if any(phrase in command_lower for phrase in ["next", "next step", "continue", "go on"]):
                    self.next_step()
                elif any(phrase in command_lower for phrase in ["repeat", "repeat step", "say again", "what was that"]):
                    self.repeat_step()
                elif any(phrase in command_lower for phrase in ["help", "question", "ask"]):
                    self.speak("What cooking question do you have?")
                    # Wait for user's question and handle it
                else:
                    # Ignore other commands during cooking
                    self.log_command(f"🎤 Ignored command during cooking: {command}")
                    
            elif self.cooking_state == "IDLE":
                # Allow starting cooking from idle state
                if any(phrase in command_lower for phrase in ["start cooking", "begin cooking", "let's cook", "cook"]):
                    self.start_cooking()
                else:
                    self.speak("Say 'start cooking' to begin cooking.")
            
        except Exception as e:
            self.log_command(f"❌ Error handling voice command: {str(e)}")
            self.speak("Sorry, I had trouble processing that command. Please try again.")
            
    def handle_voice_error(self, error):
        """Handle voice recognition errors"""
        print(f"❌ Voice recognition error: {error}")
        self.log_command(f"❌ Voice error: {error}")
        self.status_label.setText("❌ Voice recognition error")
        # Don't speak errors - just log them
        
    def log_command(self, message):
        """Log voice commands and responses"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.command_log.append(f"[{timestamp}] {message}")
        except Exception as e:
            print(f"Log error: {e}")
        
    def speak(self, text):
        """Convert text to speech"""
        try:
            self.log_command(f"🗣️ Speaking: {text}")
            
            # Pause voice recognition while speaking to prevent echo
            if self.voice_thread and hasattr(self.voice_thread, 'pause_listening'):
                self.voice_thread.pause_listening()
            
            self.tts_thread = TextToSpeechThread(self.speech_key, self.speech_region, text)
            self.tts_thread.speech_finished.connect(self.on_speech_finished)
            self.tts_thread.start()
        except Exception as e:
            self.log_command(f"❌ Speech error: {str(e)}")
    
    def on_speech_finished(self):
        """Called when speech synthesis finishes"""
        # Resume voice recognition after a short delay to prevent echo
        if self.voice_thread and hasattr(self.voice_thread, 'resume_listening'):
            QTimer.singleShot(500, self.voice_thread.resume_listening)
        
    def load_recipe(self):
        """Load recipe data into the UI"""
        if not self.current_recipe:
            return
            
        self.recipe_name_label.setText(self.current_recipe.get('name', 'Unknown Recipe'))
        
        # Recipe details
        details = []
        if self.current_recipe.get('meal_type'):
            details.append(f"Meal: {self.current_recipe['meal_type']}")
        if self.current_recipe.get('cooking_time'):
            details.append(f"Time: {self.current_recipe['cooking_time']} min")
        if self.current_recipe.get('skill_level'):
            details.append(f"Skill: {self.current_recipe['skill_level']}")
            
        self.recipe_details_label.setText(" | ".join(details))
        
        # Enable start cooking button
        self.start_cooking_btn.setEnabled(True)
        
        self.log_command(f"✅ Recipe loaded: {self.current_recipe.get('name', 'Unknown')}")
        # Recipe loaded silently - no automatic speaking
        
    def start_cooking(self):
        """Start the cooking process"""
        if not self.current_recipe:
            self.speak("No recipe available. Please load a recipe first.")
            return
            
        self.log_command("🚀 Starting cooking session...")
        self.update_state("INTRO")
        
        # Start voice recognition now
        self.start_voice_recognition()
        
        # Single explanation message - no timers, no sequences
        self.speak("Hey! I'm your sous chef. I'll guide you through cooking this recipe. Say 'next' to go to the next step, 'repeat' to hear the current step again, or 'help' to ask me cooking questions. When you're ready to start cooking, say 'ready' or click the Ready button.")
        
        # Wait for user to be ready
        self.wait_for_user_ready()
        
        self.is_cooking = True
        self.current_step = 0
        self.start_cooking_btn.setEnabled(False)
        self.stop_cooking_btn.setEnabled(True)
        
        # Show progress elements
        self.progress_group.setVisible(True)
        self.step_display.setVisible(True)
        self.timer_group.setVisible(True)
        
        # Setup progress bar
        if self.current_recipe.get('steps'):
            self.progress_bar.setMaximum(len(self.current_recipe['steps']))
            self.progress_bar.setValue(1)
            self.step_label.setText(f"Step 1 of {len(self.current_recipe['steps'])}")
        else:
            self.progress_bar.setMaximum(1)
            self.progress_bar.setValue(1)
            self.step_label.setText("Step 1 of 1")
        
        # Start timer
        self.elapsed_time = 0
        self.cooking_timer.start(1000)  # Update every second
        
    def stop_cooking(self):
        """Stop the cooking process and close the app"""
        self.is_cooking = False
        self.update_state("IDLE")
        
        # Stop timer
        self.cooking_timer.stop()
        
        # Say completion message and close
        self.speak("Cooking session completed. Thank you for using Su-Chef!")
        self.log_command("⏹️ Cooking session completed - closing app")
        
        # Close the app after a short delay to let the message finish
        QTimer.singleShot(2000, self.close)
        
    def next_step(self):
        """Go to the next cooking step"""
        try:
            if not self.is_cooking or not self.current_recipe.get('steps') or self.cooking_state != "STEP_ACTIVE":
                return
                
            if self.current_step < len(self.current_recipe['steps']) - 1:
                self.current_step += 1
                self.show_current_step()
            else:
                self.speak("Congratulations! You've completed all the cooking steps!")
                self.log_command("🎉 Recipe completed!")
                self.stop_cooking()
        except Exception as e:
            self.log_command(f"❌ Error in next_step: {str(e)}")
            self.speak("Sorry, I encountered an error moving to the next step. Please try again.")
            
    def repeat_step(self):
        """Repeat the current cooking step"""
        if self.is_cooking and self.cooking_state == "STEP_ACTIVE":
            self.show_current_step()
            
    def show_current_step(self):
        """Display and speak the current cooking step"""
        try:
            if not self.current_recipe or not self.is_cooking or self.cooking_state != "STEP_ACTIVE":
                return
                
            if not self.current_recipe.get('steps'):
                return
                
            if self.current_step >= len(self.current_recipe['steps']):
                return
                
            step_number = self.current_step + 1
            step_text = self.current_recipe['steps'][self.current_step]
            
            # Update UI
            self.progress_bar.setValue(step_number)
            self.step_label.setText(f"Step {step_number} of {len(self.current_recipe['steps'])}")
            self.current_step_text.setText(step_text)
            
            # Speak step
            self.speak(f"Step {step_number}: {step_text}")
            self.log_command(f"📋 Step {step_number}: {step_text}")
            

        except Exception as e:
            self.log_command(f"❌ Error in show_current_step: {str(e)}")
            self.speak("Sorry, I encountered an error showing the current step. Please try again.")
        



    
    def wait_for_user_ready(self):
        """Wait for user to indicate they're ready to cook"""
        self.update_state("WAIT_READY")
        self.log_command("⏳ Waiting for user to be ready...")
        
    def begin_first_step(self):
        """Begin the first cooking step"""
        try:
            if not self.current_recipe or not self.current_recipe.get('steps'):
                self.current_step_text.setText("Ready to cook!")
                self.speak("Ready to cook!")
                return
                
            # Show and speak the first step
            self.show_current_step()
        except Exception as e:
            self.log_command(f"❌ Error in begin_first_step: {str(e)}")
            self.speak("Sorry, I encountered an error starting the first step. Please try again.")
        

    
    def handle_cooking_question(self, question):
        """Handle free-form cooking questions from the user"""
        try:
            question_lower = question.lower()
            
            # Common cooking questions and answers
            if any(word in question_lower for word in ["onion", "onions"]):
                if "done" in question_lower or "how done" in question_lower:
                    self.speak("Onions should be soft and translucent, with a slight golden color. They should be tender but not mushy.")
                elif "cut" in question_lower or "chop" in question_lower:
                    self.speak("For most recipes, dice onions into small, even pieces about half an inch square.")
                else:
                    self.speak("Onions add flavor and sweetness to dishes. They're usually cooked until soft and translucent.")
                    
            elif any(word in question_lower for word in ["garlic", "garlics"]):
                if "mince" in question_lower or "chop" in question_lower:
                    self.speak("Mince garlic very finely. You can use a garlic press or chop it with a knife until it's almost paste-like.")
                else:
                    self.speak("Garlic should be added after onions and cooked just until fragrant, about 30 seconds to avoid burning.")
                    
            elif any(word in question_lower for word in ["salt", "seasoning"]):
                self.speak("Season with salt throughout the cooking process, not just at the end. Start with a small amount and taste as you go.")
                
            elif any(word in question_lower for word in ["heat", "temperature", "hot"]):
                self.speak("Medium heat is usually best for most cooking. You want the food to cook evenly without burning.")
                
            elif any(word in question_lower for word in ["oil", "butter"]):
                self.speak("Use oil for high-heat cooking and butter for lower heat or finishing dishes. Olive oil is great for most cooking.")
                
            else:
                # Generic helpful response
                self.speak("That's a great cooking question! In general, take your time, taste as you go, and don't be afraid to adjust seasoning.")
                
        except Exception as e:
            self.speak("I'm sorry, I didn't catch that cooking question. Could you please repeat it?")
            self.log_command(f"❌ Error handling cooking question: {str(e)}")
        
    def update_cooking_timer(self):
        """Update the cooking timer display"""
        self.elapsed_time += 1
        minutes = self.elapsed_time // 60
        seconds = self.elapsed_time % 60
        self.timer_display.setText(f"{minutes:02d}:{seconds:02d}")
    
    def update_state(self, new_state):
        """Update cooking state and UI"""
        self.cooking_state = new_state
        self.state_label.setText(f"State: {new_state}")
        self.log_command(f"🔄 State changed to: {new_state}")
        
        # Update UI based on state
        if new_state == "WAIT_READY":
            self.ready_btn.setVisible(True)
            self.status_label.setText("⏳ Waiting for you to say you're ready...")
        elif new_state == "STEP_ACTIVE":
            self.ready_btn.setVisible(False)
            self.status_label.setText("👨‍🍳 Cooking in progress - Say 'next step' to continue")
        elif new_state == "PAUSED":
            self.status_label.setText("⏸️ Cooking paused - Say 'continue' to resume")
    
    def user_ready(self):
        """User clicked ready button or said ready"""
        try:
            if self.cooking_state == "WAIT_READY":
                self.log_command("✅ User is ready to cook!")
                self.update_state("STEP_ACTIVE")
                # Don't speak here - let begin_first_step handle the speech
                self.begin_first_step()
            else:
                self.log_command("⚠️ Ready button clicked but not in WAIT_READY state")
        except Exception as e:
            self.log_command(f"❌ Error in user_ready: {str(e)}")
            self.speak("Sorry, I encountered an error. Please try again.")
        
    def closeEvent(self, event):
        """Handle application closure"""
        try:
            if self.voice_thread:
                self.voice_thread.stop_listening()
                self.voice_thread.wait()
            if self.cooking_timer.isActive():
                self.cooking_timer.stop()
        except Exception as e:
            print(f"Close error: {e}")
        event.accept()

def handle_deep_link(deep_link):
    """Handle deep link protocol suchef://recipe/<id>"""
    try:
        if deep_link.startswith('suchef://recipe/'):
            recipe_id = deep_link.split('/')[-1]
            print(f"Deep link received for recipe ID: {recipe_id}")
            return {'id': recipe_id, 'source': 'deep_link'}
        return None
    except Exception as e:
        print(f"Error parsing deep link: {e}")
        return None

def main():
    """Main application entry point"""
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Check for deep link or recipe data
        recipe_data = None
        recipe_source = None
        
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            
            # Check if it's a deep link
            if arg.startswith('suchef://'):
                deep_link_data = handle_deep_link(arg)
                if deep_link_data:
                    recipe_data = deep_link_data
                    recipe_source = 'deep_link'
                    print(f"Deep link detected: {arg}")
            
            # If not a deep link, try to parse as JSON recipe data
            elif not recipe_source:
                try:
                    recipe_data = json.loads(arg)
                    recipe_source = 'command_line'
                except json.JSONDecodeError:
                    print("Invalid recipe data format")
        
        # Create and show main window
        window = CookingAssistant(recipe_data, recipe_source)
        window.show()
        
        # Start event loop
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application error: {e}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()
