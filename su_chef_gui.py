#!/usr/bin/env python3
"""
Su-Chef GUI Wrapper
Modern Tkinter + ttkbootstrap GUI that wraps the existing su_chef.py CLI
Maintains all CLI functionality while providing a user-friendly interface.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import subprocess
import threading
import queue
import os
import sys
import time
import json
from typing import Optional, Dict, Any
import re

class SuChefGUI:
    def __init__(self):
        # Create main window with modern theme
        self.root = ttk_bs.Window(themename="superhero")  # Dark modern theme
        self.root.title("Su-Chef - AI Cooking Assistant")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Process management
        self.cli_process: Optional[subprocess.Popen] = None
        self.output_queue = queue.Queue()
        self.is_running = False
        self.current_state = "idle"  # idle, generating, cooking, voice_active
        
        # GUI state
        self.recipe_data = {}
        self.cooking_steps = []
        self.current_step = 0
        self.debug_mode = False
        
        # Create GUI
        self.create_widgets()
        self.setup_layout()
        
        # Start CLI process
        self.start_cli_process()
        
        # Start output monitoring
        self.monitor_output()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main container with padding
        self.main_frame = ttk_bs.Frame(self.root, padding=10)
        
        # Header
        self.header_frame = ttk_bs.Frame(self.main_frame)
        self.title_label = ttk_bs.Label(
            self.header_frame, 
            text="🍳 Su-Chef - AI Cooking Assistant", 
            font=("Arial", 16, "bold"),
            bootstyle="primary"
        )
        self.status_label = ttk_bs.Label(
            self.header_frame, 
            text="Ready to cook!", 
            font=("Arial", 10),
            bootstyle="secondary"
        )
        
        # Recipe Generation Form
        self.form_frame = ttk_bs.LabelFrame(self.main_frame, text="Generate Recipe", padding=10)
        
        # Form fields in grid
        self.username_label = ttk_bs.Label(self.form_frame, text="Username:")
        self.username_entry = ttk_bs.Entry(self.form_frame, width=20)
        self.username_entry.insert(0, "Chef")  # Default username
        
        self.meal_label = ttk_bs.Label(self.form_frame, text="Meal Type:")
        self.meal_combo = ttk_bs.Combobox(
            self.form_frame, 
            values=["breakfast", "lunch", "dinner", "snack"],
            state="readonly",
            width=18
        )
        self.meal_combo.set("dinner")
        
        self.time_label = ttk_bs.Label(self.form_frame, text="Cooking Time (min):")
        self.time_spinbox = ttk_bs.Spinbox(
            self.form_frame, 
            from_=5, to=180, 
            width=20,
            value=30
        )
        
        self.skill_label = ttk_bs.Label(self.form_frame, text="Skill Level:")
        self.skill_combo = ttk_bs.Combobox(
            self.form_frame,
            values=["beginner", "intermediate", "advanced"],
            state="readonly",
            width=18
        )
        self.skill_combo.set("intermediate")
        
        self.diet_label = ttk_bs.Label(self.form_frame, text="Dietary Restrictions:")
        self.diet_combo = ttk_bs.Combobox(
            self.form_frame,
            values=["none", "vegetarian", "vegan", "kosher", "sugar-free"],
            state="readonly",
            width=18
        )
        self.diet_combo.set("none")
        
        self.ingredients_label = ttk_bs.Label(self.form_frame, text="Available Ingredients:")
        self.ingredients_entry = ttk_bs.Entry(self.form_frame, width=50)
        self.ingredients_entry.insert(0, "chicken, rice, vegetables")  # Example
        
        # Buttons
        self.button_frame = ttk_bs.Frame(self.form_frame)
        self.generate_btn = ttk_bs.Button(
            self.button_frame,
            text="🎲 Generate Recipe",
            command=self.generate_recipe,
            bootstyle="success",
            width=15
        )
        self.start_cooking_btn = ttk_bs.Button(
            self.button_frame,
            text="🍳 Start Cooking",
            command=self.start_cooking,
            bootstyle="primary",
            width=15,
            state="disabled"
        )
        
        # Voice Controls
        self.voice_frame = ttk_bs.LabelFrame(self.main_frame, text="Voice Controls", padding=10)
        self.voice_status_label = ttk_bs.Label(
            self.voice_frame, 
            text="🎤 Voice: Ready", 
            font=("Arial", 10, "bold"),
            bootstyle="info"
        )
        
        self.voice_button_frame = ttk_bs.Frame(self.voice_frame)
        self.next_btn = ttk_bs.Button(
            self.voice_button_frame,
            text="➡️ Next Step",
            command=lambda: self.send_command("next"),
            bootstyle="info",
            width=12,
            state="disabled"
        )
        self.repeat_btn = ttk_bs.Button(
            self.voice_button_frame,
            text="🔄 Repeat",
            command=lambda: self.send_command("repeat"),
            bootstyle="warning",
            width=12,
            state="disabled"
        )
        self.ingredients_btn = ttk_bs.Button(
            self.voice_button_frame,
            text="📋 Ingredients",
            command=lambda: self.send_command("ingredients"),
            bootstyle="secondary",
            width=12,
            state="disabled"
        )
        self.stop_btn = ttk_bs.Button(
            self.voice_button_frame,
            text="⏹️ Stop",
            command=lambda: self.send_command("stop"),
            bootstyle="danger",
            width=12,
            state="disabled"
        )
        
        # Manual command input
        self.command_frame = ttk_bs.Frame(self.voice_frame)
        self.command_label = ttk_bs.Label(self.command_frame, text="Manual Command:")
        self.command_entry = ttk_bs.Entry(self.command_frame, width=30)
        self.command_entry.bind("<Return>", self.send_manual_command)
        self.send_cmd_btn = ttk_bs.Button(
            self.command_frame,
            text="Send",
            command=self.send_manual_command,
            bootstyle="outline-primary",
            width=8
        )
        
        # Output Display
        self.output_frame = ttk_bs.LabelFrame(self.main_frame, text="Su-Chef Output", padding=10)
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame,
            height=15,
            width=80,
            font=("Consolas", 10),
            bg="#2b3e50",  # Dark background
            fg="#ecf0f1",  # Light text
            insertbackground="#ecf0f1"  # Light cursor
        )
        self.output_text.config(state="disabled")
        
        # Output control buttons
        self.output_controls = ttk_bs.Frame(self.output_frame)
        self.clear_btn = ttk_bs.Button(
            self.output_controls,
            text="Clear Output",
            command=self.clear_output,
            bootstyle="outline-secondary",
            width=12
        )
        self.debug_btn = ttk_bs.Button(
            self.output_controls,
            text="Debug Mode",
            command=self.toggle_debug,
            bootstyle="outline-info",
            width=12
        )
        self.restart_btn = ttk_bs.Button(
            self.output_controls,
            text="Restart CLI",
            command=self.restart_cli,
            bootstyle="outline-warning",
            width=12
        )
        
    def setup_layout(self):
        """Arrange widgets in the window"""
        
        # Main frame
        self.main_frame.pack(fill="both", expand=True)
        
        # Header
        self.header_frame.pack(fill="x", pady=(0, 10))
        self.title_label.pack()
        self.status_label.pack()
        
        # Recipe form
        self.form_frame.pack(fill="x", pady=(0, 10))
        
        # Form grid layout
        self.username_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=2)
        self.username_entry.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=2)
        
        self.meal_label.grid(row=0, column=2, sticky="w", padx=(0, 5), pady=2)
        self.meal_combo.grid(row=0, column=3, sticky="w", pady=2)
        
        self.time_label.grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        self.time_spinbox.grid(row=1, column=1, sticky="w", padx=(0, 20), pady=2)
        
        self.skill_label.grid(row=1, column=2, sticky="w", padx=(0, 5), pady=2)
        self.skill_combo.grid(row=1, column=3, sticky="w", pady=2)
        
        self.diet_label.grid(row=2, column=0, sticky="w", padx=(0, 5), pady=2)
        self.diet_combo.grid(row=2, column=1, sticky="w", padx=(0, 20), pady=2)
        
        self.ingredients_label.grid(row=3, column=0, sticky="w", padx=(0, 5), pady=2)
        self.ingredients_entry.grid(row=3, column=1, columnspan=3, sticky="ew", pady=2)
        
        # Configure column weights for responsive design
        self.form_frame.columnconfigure(1, weight=1)
        self.form_frame.columnconfigure(3, weight=1)
        
        # Buttons
        self.button_frame.grid(row=4, column=0, columnspan=4, pady=(10, 0))
        self.generate_btn.pack(side="left", padx=(0, 10))
        self.start_cooking_btn.pack(side="left")
        
        # Voice controls
        self.voice_frame.pack(fill="x", pady=(0, 10))
        self.voice_status_label.pack(pady=(0, 5))
        
        self.voice_button_frame.pack(pady=(0, 5))
        self.next_btn.pack(side="left", padx=2)
        self.repeat_btn.pack(side="left", padx=2)
        self.ingredients_btn.pack(side="left", padx=2)
        self.stop_btn.pack(side="left", padx=2)
        
        self.command_frame.pack(fill="x")
        self.command_label.pack(side="left", padx=(0, 5))
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.send_cmd_btn.pack(side="right")
        
        # Output
        self.output_frame.pack(fill="both", expand=True)
        self.output_text.pack(fill="both", expand=True, pady=(0, 5))
        self.output_controls.pack(fill="x")
        self.clear_btn.pack(side="left", padx=(0, 5))
        self.debug_btn.pack(side="left", padx=(0, 5))
        self.restart_btn.pack(side="left")
        
    def start_cli_process(self):
        """Start the su_chef.py CLI process"""
        try:
            # Check if su_chef.py exists
            if not os.path.exists("su_chef.py"):
                self.append_output("❌ Error: su_chef.py not found in current directory")
                return
            
            # Start the CLI process with Windows-specific settings
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'  # Force UTF-8 encoding
            env['PYTHONUNBUFFERED'] = '1'  # Force unbuffered output
            
            # Use Windows wrapper if on Windows, otherwise use regular CLI
            cli_script = "su_chef_windows.py" if os.name == 'nt' else "su_chef.py"
            
            # Check if the CLI script exists
            if not os.path.exists(cli_script):
                cli_script = "su_chef.py"  # Fallback to regular CLI
            
            self.cli_process = subprocess.Popen(
                [sys.executable, "-u", cli_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace problematic characters
                bufsize=0,  # Unbuffered
                universal_newlines=True,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.is_running = True
            self.append_output("✅ Su-Chef CLI started successfully")
            self.update_status("CLI Ready - Enter username to begin")
            
            # Start thread to read output
            self.output_thread = threading.Thread(target=self.read_cli_output, daemon=True)
            self.output_thread.start()
            
        except Exception as e:
            self.append_output(f"❌ Failed to start CLI: {e}")
            messagebox.showerror("Error", f"Failed to start Su-Chef CLI: {e}")
    
    def read_cli_output(self):
        """Read output from CLI process in separate thread"""
        while self.is_running and self.cli_process and self.cli_process.poll() is None:
            try:
                line = self.cli_process.stdout.readline()
                if line:
                    self.output_queue.put(("output", line.rstrip()))
                else:
                    time.sleep(0.1)
            except Exception as e:
                self.output_queue.put(("error", f"Output read error: {e}"))
                break
    
    def monitor_output(self):
        """Monitor output queue and update GUI"""
        try:
            while True:
                msg_type, content = self.output_queue.get_nowait()
                
                if msg_type == "output":
                    self.append_output(content)
                    self.parse_cli_output(content)
                elif msg_type == "error":
                    self.append_output(f"❌ {content}")
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.monitor_output)
    
    def parse_cli_output(self, output: str):
        """Parse CLI output to update GUI state"""
        output_lower = output.lower()
        
        # Update status based on CLI output
        if "welcome" in output_lower and "chef" in output_lower:
            self.update_status("User logged in - Ready to generate recipes")
        elif "generating recipe" in output_lower or "please suggest a" in output_lower:
            self.current_state = "generating"
            self.update_status("🔄 Generating recipe with OpenAI...")
            self.generate_btn.config(state="disabled")
        elif "generated recipe:" in output_lower or "recipe name:" in output_lower:
            self.current_state = "recipe_ready"
            self.update_status("✅ Recipe generated! Review and click 'Start Cooking'")
            self.generate_btn.config(state="normal")
            self.start_cooking_btn.config(state="normal")
        elif "recipe accepted" in output_lower or "ready to proceed" in output_lower:
            self.current_state = "recipe_ready"
            self.update_status("✅ Recipe ready - Click 'Start Cooking' to begin")
            self.generate_btn.config(state="normal")
            self.start_cooking_btn.config(state="normal")
        elif "starting cooking guide" in output_lower or "hi! i'm su-chef" in output_lower:
            self.current_state = "cooking"
            self.update_status("🍳 Cooking session active - Voice commands enabled")
            self.enable_voice_controls()
        elif "recipe completed" in output_lower or "all done" in output_lower or "great job cooking" in output_lower:
            self.current_state = "completed"
            self.update_status("🎉 Recipe completed! Great job!")
            self.disable_voice_controls()
        elif "failed to generate recipe" in output_lower or "openai api" in output_lower:
            self.current_state = "error"
            self.update_status("❌ Recipe generation failed - Check API key")
            self.generate_btn.config(state="normal")
        elif "voice recognition" in output_lower:
            if "working" in output_lower:
                self.voice_status_label.config(text="🎤 Voice: Active", bootstyle="success")
            elif "failed" in output_lower:
                self.voice_status_label.config(text="🎤 Voice: Error", bootstyle="danger")
        elif "listening" in output_lower:
            self.voice_status_label.config(text="🎤 Voice: Listening...", bootstyle="info")
        elif "you said:" in output_lower or "you typed:" in output_lower:
            self.voice_status_label.config(text="🎤 Voice: Processing...", bootstyle="warning")
        elif "step " in output_lower and ":" in output_lower:
            # Cooking step detected
            if self.current_state != "cooking":
                self.current_state = "cooking"
                self.enable_voice_controls()
    
    def append_output(self, text: str):
        """Append text to output display"""
        self.output_text.config(state="normal")
        self.output_text.insert("end", f"{text}\n")
        self.output_text.see("end")
        self.output_text.config(state="disabled")
    
    def update_status(self, status: str):
        """Update status label"""
        self.status_label.config(text=status)
    
    def send_command(self, command: str):
        """Send command to CLI process"""
        if not self.cli_process or not self.is_running:
            self.append_output(f"❌ Cannot send command - CLI process not running")
            return
            
        # Check if process is still alive
        if self.cli_process.poll() is not None:
            self.append_output(f"❌ CLI process has terminated - restarting...")
            self.restart_cli()
            return
            
        try:
            # Encode command properly for Windows
            command_line = f"{command}\n"
            self.cli_process.stdin.write(command_line)
            self.cli_process.stdin.flush()
            
            if self.debug_mode:
                self.append_output(f"🔧 DEBUG: Sent command: '{command}'")
            else:
                self.append_output(f">>> {command}")
                
        except BrokenPipeError:
            self.append_output(f"❌ CLI process pipe broken - restarting...")
            self.restart_cli()
        except OSError as e:
            if e.errno == 22:  # Invalid argument on Windows
                self.append_output(f"❌ Windows pipe error - restarting CLI...")
                self.restart_cli()
            else:
                self.append_output(f"❌ OS error sending command '{command}': {e}")
        except Exception as e:
            self.append_output(f"❌ Failed to send command '{command}': {e}")
            if "invalid argument" in str(e).lower():
                self.append_output("💡 This looks like a Windows encoding issue - restarting CLI...")
                self.restart_cli()
    
    def send_manual_command(self, event=None):
        """Send manual command from entry field"""
        command = self.command_entry.get().strip()
        if command:
            self.send_command(command)
            self.command_entry.delete(0, "end")
    
    def generate_recipe(self):
        """Start recipe generation workflow"""
        if not self.cli_process or not self.is_running:
            messagebox.showerror("Error", "CLI process not running")
            return
        
        self.append_output("🔄 Starting recipe generation...")
        self.generate_btn.config(state="disabled")
        
        # Create a sequence of commands to send
        commands = []
        
        # Username
        username = self.username_entry.get().strip() or "Chef"
        commands.append(username)
        
        # Main menu choice (1 = Create new recipe)
        commands.append("1")
        
        # Meal type
        meal_type = self.meal_combo.get()
        meal_choices = {"breakfast": "1", "lunch": "2", "dinner": "3", "snack": "4"}
        commands.append(meal_choices.get(meal_type, "3"))
        
        # Cooking time
        commands.append(self.time_spinbox.get())
        
        # Skill level
        skill = self.skill_combo.get()
        skill_choices = {"beginner": "1", "intermediate": "2", "advanced": "3"}
        commands.append(skill_choices.get(skill, "2"))
        
        # Dietary restrictions
        diet = self.diet_combo.get()
        diet_choices = {
            "none": "6", "vegetarian": "1", "vegan": "2", 
            "kosher": "4", "sugar-free": "5"
        }
        commands.append(diet_choices.get(diet, "6"))
        
        # Handle allergy case (if diet is allergy, need to specify)
        if diet == "allergy":
            commands.append("3")  # Allergy option
            commands.append("nuts")  # Default allergy
        
        # Available ingredients
        ingredients = self.ingredients_entry.get().strip()
        commands.append(ingredients if ingredients else "")
        
        # Accept the first generated recipe (after generation completes)
        commands.append("1")  # Accept recipe
        
        # Send commands with delays
        self.send_command_sequence(commands, 0)
    
    def send_command_sequence(self, commands, index):
        """Send commands in sequence with appropriate delays"""
        if index >= len(commands) or not self.is_running:
            return
        
        command = commands[index]
        self.send_command(command)
        
        # Different delays based on command type
        if index == 0:  # Username
            delay = 1000
        elif index == len(commands) - 1:  # Accept recipe - wait longer for generation
            delay = 8000  # 8 seconds for recipe generation
        elif command in ["1", "2", "3", "4", "5", "6"]:  # Menu choices
            delay = 500
        else:  # Text inputs
            delay = 1000
        
        # Schedule next command
        self.root.after(delay, lambda: self.send_command_sequence(commands, index + 1))
    
    def start_cooking(self):
        """Start cooking session"""
        if self.current_state == "recipe_ready":
            self.send_command("1")  # Start voice guidance
            self.enable_voice_controls()
    
    def enable_voice_controls(self):
        """Enable voice control buttons"""
        self.next_btn.config(state="normal")
        self.repeat_btn.config(state="normal")
        self.ingredients_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        self.start_cooking_btn.config(state="disabled")
    
    def disable_voice_controls(self):
        """Disable voice control buttons"""
        self.next_btn.config(state="disabled")
        self.repeat_btn.config(state="disabled")
        self.ingredients_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.start_cooking_btn.config(state="normal")
    
    def clear_output(self):
        """Clear the output display"""
        self.output_text.config(state="normal")
        self.output_text.delete(1.0, "end")
        self.output_text.config(state="disabled")
    
    def toggle_debug(self):
        """Toggle debug mode for more verbose output"""
        self.debug_mode = not self.debug_mode
        if self.debug_mode:
            self.debug_btn.config(text="Debug: ON", bootstyle="info")
            self.append_output("🐛 Debug mode enabled - showing all CLI communication")
        else:
            self.debug_btn.config(text="Debug Mode", bootstyle="outline-info")
            self.append_output("🐛 Debug mode disabled")
    
    def restart_cli(self):
        """Restart the CLI process"""
        self.append_output("🔄 Restarting CLI process...")
        
        # Stop current process
        if self.cli_process:
            try:
                self.cli_process.terminate()
                self.cli_process.wait(timeout=3)
            except:
                self.cli_process.kill()
        
        self.is_running = False
        time.sleep(1)  # Brief pause
        
        # Reset state
        self.current_state = "idle"
        self.disable_voice_controls()
        self.generate_btn.config(state="normal")
        
        # Start new process
        self.start_cli_process()
    
    def on_closing(self):
        """Handle window close event"""
        if self.cli_process:
            try:
                self.cli_process.terminate()
                self.cli_process.wait(timeout=3)
            except:
                self.cli_process.kill()
        
        self.is_running = False
        self.root.destroy()

def main():
    """Main entry point"""
    # Check dependencies
    try:
        import ttkbootstrap
    except ImportError:
        print("❌ ttkbootstrap not installed. Install with: pip install ttkbootstrap")
        return
    
    # Check if su_chef.py exists
    if not os.path.exists("su_chef.py"):
        print("❌ su_chef.py not found in current directory")
        print("   Please run this GUI from the same directory as su_chef.py")
        return
    
    # Create and run GUI
    app = SuChefGUI()
    app.root.mainloop()

if __name__ == "__main__":
    main()
