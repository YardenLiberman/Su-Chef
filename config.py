"""Configuration constants and mappings for Su-Chef application."""

# Menu option mappings
MEAL_TYPE_OPTIONS = {
    "1": "breakfast",
    "2": "lunch", 
    "3": "dinner",
    "4": "snack"
}

SKILL_LEVEL_OPTIONS = {
    "1": "beginner",
    "2": "intermediate",
    "3": "advanced"
}

DIETARY_RESTRICTION_OPTIONS = {
    "1": "vegetarian",
    "2": "vegan",
    "3": "allergy",  # Special case - requires user input
    "4": "kosher",
    "5": "sugar-free",
    "6": None  # No restrictions
}

# Menu display texts
MEAL_TYPE_DISPLAY = [
    "Breakfast",
    "Lunch", 
    "Dinner",
    "Snack"
]

SKILL_LEVEL_DISPLAY = [
    "Beginner",
    "Intermediate",
    "Advanced"
]

DIETARY_RESTRICTION_DISPLAY = [
    "Vegetarian",
    "Vegan",
    "Allergy (specify)",
    "Kosher",
    "Sugar-free",
    "None"
]

# Main menu options
MAIN_MENU_OPTIONS = [
    "Create new recipe",
    "Use saved recipe", 
    "Load recipe from file",
    "View user statistics",
    "Exit"
]

# Recipe action menu options
RECIPE_ACTION_OPTIONS = [
    "Start voice guidance",
    "View full recipe details",
    "Change to different recipe",
    "Back to main menu"
]

# File recipe action menu options
FILE_RECIPE_ACTION_OPTIONS = [
    "Start voice guidance",
    "Load different recipe file",
    "Back to main menu"
]

# Search menu options
SEARCH_MENU_OPTIONS = [
    "Search by name",
    "View cooked recipes",
    "View liked recipes"
]

# Application constants
APP_NAME = "SU-CHEF MANAGER"
APP_SUBTITLE = "Your AI Cooking Assistant"
DEFAULT_MENU_WIDTH = 60
DEFAULT_PREVIEW_INGREDIENTS = 3
DEFAULT_STEPS_FILENAME = "steps.json"

# Validation constants
MIN_COOKING_TIME = 1
MAX_MENU_ATTEMPTS = 3

# Display formatting
SEPARATOR_CHAR = "="
SUBSECTION_CHAR = "-"
PREVIEW_WIDTH = 50 