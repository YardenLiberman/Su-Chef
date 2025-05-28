# Su-Chef 🍳🤖

**Su-Chef** is an AI-powered cooking assistant that combines voice interaction with intelligent recipe management. It guides you through cooking with voice commands, generates new recipes, and tracks your culinary journey.

## Features ✨

### 🎤 Voice-Guided Cooking
- **Step-by-step voice guidance** through recipes
- **Natural language commands**: "next", "repeat", "ingredients", "help"
- **AI-powered question answering** for cooking tips and advice
- **Smart command detection** using OpenAI GPT

### 🍽️ Recipe Management
- **AI recipe generation** with customizable parameters
- **Recipe database** with SQLite storage
- **Search functionality** (by name, cooked recipes, liked recipes)
- **Progress tracking** and user statistics
- **Recipe preview** before cooking

### 🧠 Intelligent Features
- **Dietary restriction support** (vegetarian, vegan, allergies, etc.)
- **Skill level adaptation** (beginner, intermediate, advanced)
- **Ingredient-based recipe suggestions**
- **Cooking time optimization**

## Technologies Used 🛠️

- **Voice Recognition**: Azure Cognitive Services Speech SDK
- **Text-to-Speech**: Azure Speech Synthesis (Jenny Multilingual Neural Voice)
- **AI Processing**: OpenAI GPT-3.5-turbo
- **Database**: SQLite with custom recipe management
- **Language**: Python 3.7+

## Installation 📦

### Prerequisites
- Python 3.7 or higher
- Azure Speech Services subscription
- OpenAI API key

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/YardenLiberman/Su-Chef.git
   cd Su-Chef
   ```

2. **Install dependencies**
   ```bash
   pip install openai azure-cognitiveservices-speech python-dotenv
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   SPEECH_KEY=your_azure_speech_key_here
   SPEECH_REGION=your_azure_region_here
   ```

4. **Run the application**
   ```bash
   python su_chef_manager.py
   ```

## Usage Guide 📖

### Main Menu Options
1. **Create new recipe** - Generate AI-powered recipes
2. **Use saved recipe** - Browse and select from your recipe collection
3. **Load recipe from file** - Import external recipe files
4. **View user statistics** - See your cooking progress

### Voice Commands During Cooking
- **"Next"** - Move to the next step
- **"Repeat"** - Repeat the current step
- **"Ingredients"** - Hear the ingredients list
- **"Help"** or **"Tips"** - Get cooking advice
- **"Stop"** - End the cooking session
- **Ask any question** - Get AI-powered cooking assistance

### Recipe Generation Parameters
- **Meal Type**: Breakfast, Lunch, Dinner, Snack
- **Cooking Time**: Maximum time in minutes
- **Skill Level**: Beginner, Intermediate, Advanced
- **Dietary Restrictions**: Vegetarian, Vegan, Allergies, Kosher, Sugar-free
- **Available Ingredients**: Optional ingredient list

## File Structure 📁

```
Su-Chef/
├── su_chef_manager.py      # Main application manager
├── cooking_agent.py        # Voice guidance system
├── recipe_generator.py     # AI recipe generation
├── database.py            # Recipe database management
├── steps.json             # Recipe steps (auto-generated)
├── recipe.json            # Recipe data (auto-generated)
├── .env                   # Environment variables (not in repo)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## API Keys Setup 🔑

### Azure Speech Services
1. Create an Azure account
2. Create a Speech Services resource
3. Copy the key and region to your `.env` file

### OpenAI API
1. Create an OpenAI account
2. Generate an API key
3. Add it to your `.env` file

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is open source and available under the [MIT License](LICENSE).

## Support 💬

If you encounter any issues or have questions:
1. Check the troubleshooting section below
2. Open an issue on GitHub
3. Contact the development team

## Troubleshooting 🔧

### Common Issues
- **Voice not working**: Check microphone permissions and Azure Speech key
- **Recipe generation fails**: Verify OpenAI API key and internet connection
- **Database errors**: Ensure write permissions in the project directory

### Audio Issues
If you experience audio problems, the system will gracefully fall back to text-only mode while maintaining full functionality.

---

**Happy Cooking with Su-Chef! 👨‍🍳👩‍🍳** 