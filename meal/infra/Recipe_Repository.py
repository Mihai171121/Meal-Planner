import json
from meal.domain.Recipe import Recipe
from meal.infra.paths import RECIPES_FILE

def reading_from_recipes():
    try:
        with open(RECIPES_FILE, 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)
        recipes = [Recipe.from_dict(entry) for entry in recipes_data]
        return recipes
    except Exception as e:
        print(f"Error reading recipes: {e}")