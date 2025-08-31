# Su-Chef Web Application

A modern, responsive web interface for the Su-Chef AI Cooking Assistant, built with Flask and Bootstrap.

## Features

### 🍳 Recipe Management
- **AI-Powered Recipe Generation**: Create recipes using OpenAI's GPT models
- **Customizable Parameters**: Set meal type, cooking time, skill level, and dietary restrictions
- **Ingredient Management**: Specify available ingredients for personalized recipes
- **Recipe Storage**: Save and organize your favorite recipes

### 👨‍🍳 Interactive Cooking Experience
- **Step-by-Step Guidance**: Clear, numbered cooking instructions
- **Voice Commands**: Navigate recipes hands-free (placeholder for future implementation)
- **Cooking Timer**: Built-in timer for precise cooking
- **Progress Tracking**: Visual progress bar and step completion status
- **Ingredient Checklist**: Track gathered ingredients

### 📱 Modern Web Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Beautiful UI**: Modern Bootstrap-based interface with custom styling
- **User Authentication**: Secure login and registration system
- **Dashboard**: Overview of cooking statistics and recent recipes

### 🔍 Advanced Features
- **Recipe Filtering**: Filter by meal type, skill level, cooking status, and more
- **Search Functionality**: Find recipes by name
- **Recipe Status**: Mark recipes as cooked or liked
- **User Statistics**: Track your cooking progress and preferences

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
1. **Clone the repository** (if not already done):
   ```bash
   cd web_app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the `web_app` directory with:
   ```env
   OPENAI_API_KEY=YOUR_ACTUAL_API_KEY_HERE
   SPEECH_KEY=YOUR_ACTUAL_SPEECH_KEY_HERE
   SPEECH_REGION=westeurope
   SECRET_KEY=your_secret_key_here
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Access the web app**:
   Open your browser and go to `http://localhost:5000`

## Usage

### Getting Started
1. **Register/Login**: Create an account or log in to access the app
2. **Dashboard**: View your cooking statistics and recent recipes
3. **Create Recipe**: Generate new recipes using AI with your preferences
4. **Cook Recipe**: Follow step-by-step instructions with voice guidance
5. **Manage Recipes**: Save, organize, and track your cooking progress

### Recipe Creation Workflow
1. Choose meal type (breakfast, lunch, dinner, snack)
2. Set maximum cooking time
3. Select skill level (beginner, intermediate, advanced)
4. Specify dietary restrictions (optional)
5. List available ingredients (optional)
6. Generate recipe using AI
7. Review and save the recipe

### Cooking Interface
- **Step Navigation**: Use arrow keys or buttons to navigate between steps
- **Timer Control**: Start, pause, and reset cooking timer
- **Voice Commands**: Click the microphone button for voice recognition
- **Progress Tracking**: Monitor your cooking progress visually
- **Ingredient Checklist**: Check off ingredients as you gather them

## Technical Details

### Architecture
- **Backend**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite database with user authentication and recipe storage
- **Frontend**: Bootstrap 5 with custom CSS and JavaScript
- **AI Integration**: OpenAI GPT API for recipe generation
- **Voice Services**: Azure Speech Services integration (placeholder)

### Database Schema
- **Users**: User accounts and authentication
- **Recipes**: Recipe metadata and ingredients
- **Recipe Steps**: Individual cooking instructions
- **User History**: Cooking progress and preferences

### API Endpoints
- `POST /create_recipe`: Generate new recipes using AI
- `GET /recipe/<id>`: View recipe details
- `GET /recipe/<id>/cook`: Start cooking interface
- `POST /api/recipe/<id>/toggle_cooked`: Mark recipe as cooked
- `POST /api/recipe/<id>/toggle_liked`: Mark recipe as liked

## Customization

### Styling
- Modify `templates/base.html` for global style changes
- Custom CSS variables in the `<style>` section
- Bootstrap 5 classes for responsive design

### Functionality
- Add new recipe parameters in `app.py`
- Extend voice commands in `cook_recipe.html`
- Implement additional filtering options in `saved_recipes.html`

### Database
- Add new fields to database models in `app.py`
- Run database migrations for schema changes

## Future Enhancements

### Voice Integration
- **Real Voice Recognition**: Implement actual Azure Speech Services
- **Voice Commands**: Add more sophisticated voice control
- **Text-to-Speech**: Read recipe steps aloud

### Advanced Features
- **Recipe Sharing**: Share recipes with other users
- **Social Features**: Rate and comment on recipes
- **Meal Planning**: Plan weekly menus
- **Shopping Lists**: Generate ingredient shopping lists
- **Nutritional Information**: Add calorie and nutrition data

### Mobile App
- **Progressive Web App**: Make it installable on mobile devices
- **Offline Support**: Cache recipes for offline use
- **Push Notifications**: Remind users of cooking timers

## Troubleshooting

### Common Issues
1. **OpenAI API Errors**: Check your API key and quota
2. **Database Errors**: Ensure the database file is writable
3. **Template Errors**: Check for missing template files
4. **Port Conflicts**: Change the port in `app.py` if 5000 is busy

### Debug Mode
Run with debug enabled for detailed error messages:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Su-Chef AI Cooking Assistant system.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Open an issue in the repository

---

**Happy Cooking! 👨‍🍳✨**
