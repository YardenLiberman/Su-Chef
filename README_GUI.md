# Su-Chef GUI Wrapper

A modern desktop GUI wrapper for the Su-Chef CLI application using Tkinter + ttkbootstrap.

## Features

- **🎨 Modern UI**: Clean, dark theme with ttkbootstrap
- **🔄 Process Management**: Spawns your existing CLI as subprocess
- **🎤 Voice Integration**: Full voice recognition support (no web limitations)
- **📊 Real-time Output**: Live display of CLI responses
- **🎛️ Manual Controls**: Buttons for common commands + manual input
- **⚡ Zero Backend Changes**: Uses your existing `su_chef.py` exactly as-is

## Installation

1. **Install GUI dependencies:**
   ```bash
   pip install -r requirements_gui.txt
   ```

2. **Ensure your CLI works:**
   ```bash
   python su_chef.py
   ```

3. **Run the GUI:**
   
   **Windows:**
   ```cmd
   run_gui.bat
   ```
   
   **Or manually:**
   ```cmd
   python su_chef_gui.py
   ```
   
   **Linux/Mac:**
   ```bash
   python su_chef_gui.py
   ```

## How It Works

The GUI wrapper:
1. Spawns `su_chef.py` as a child process
2. Pipes CLI stdout → GUI display
3. Sends user commands via CLI stdin
4. Maintains all your existing voice recognition logic

## GUI Layout

### Recipe Generation Form
- Username, meal type, cooking time, skill level
- Dietary restrictions, available ingredients
- Generate Recipe button

### Voice Controls
- Next Step, Repeat, Ingredients, Stop buttons
- Manual command input field
- Voice status indicator

### Output Display
- Real-time CLI output with syntax highlighting
- Clear output button
- Scrollable text area

## Usage

1. **Enter your username** (or use default "Chef")
2. **Fill recipe form** with your preferences
3. **Click "Generate Recipe"** - GUI automatically navigates CLI menus
4. **Click "Start Cooking"** when recipe is ready
5. **Use voice commands** or click buttons during cooking
6. **Manual commands** available via text input

## Voice Commands (Same as CLI)

- "next" - Move to next step
- "repeat" - Repeat current step  
- "ingredients" - List ingredients
- "stop" - End cooking session
- Ask any cooking question for AI help

## Architecture Benefits

- ✅ **CLI stays unchanged** - Zero risk to working code
- ✅ **Full voice support** - No browser audio limitations  
- ✅ **Process isolation** - GUI crash won't affect cooking
- ✅ **Easy debugging** - Can still run CLI standalone
- ✅ **Modern UI** - Professional desktop experience

## Troubleshooting

**GUI won't start:**
- Ensure `su_chef.py` is in the same directory
- Check `requirements_gui.txt` dependencies installed

**Windows Unicode errors:**
- Use `run_gui.bat` instead of direct Python command
- Or set: `set PYTHONIOENCODING=utf-8` before running
- GUI automatically handles Windows encoding issues

**Voice not working:**
- Same as CLI - check Azure Speech API keys
- Voice runs in CLI process, not GUI

**CLI output not showing:**
- Check if `su_chef.py` runs standalone
- Try "Restart CLI" button in GUI
- Enable "Debug Mode" to see detailed communication

**Recipe generation fails:**
- Check OpenAI API key in .env file
- Enable debug mode to see exact error
- Try "Restart CLI" button
