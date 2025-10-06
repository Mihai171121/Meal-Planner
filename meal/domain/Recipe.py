#TODO Recipe (nume, porții, ingrediente, pași, tag-uri)
import os, json
from meal.domain.Ingredient import Ingredient
from meal.domain.RecipeCooked import RecipeCooked
from typing import List, Dict, Optional

class Recipe:
    def __init__(self, name: str = "", servings: int = 0, ingredients: Optional[List[Ingredient]] = None,
                 steps: Optional[List[str]] = None, tags: Optional[List[str]] = None,
                 calories_per_serving: int = 0, macros: Optional[Dict[str, int]] = None, image: str = ""):
        self.name = name
        self.servings = servings
        self.ingredients = ingredients[:] if ingredients else []
        self.steps = steps[:] if steps else []
        self.tags = tags[:] if tags else []
        self.calories_per_serving = calories_per_serving
        m = macros or {}
        # Normalize key synonyms
        if 'carbohydrates' in m and 'carbs' not in m:
            m['carbs'] = m.get('carbohydrates')
        self.macros = {
            'protein': m.get('protein', 0),
            'carbs': m.get('carbs', 0),
            'fats': m.get('fats', m.get('fat', 0))
        }
        self.image = image

    def __str__(self) -> str:
        macros_str = f"Protein: {self.macros.get('protein',0)}g, Carbs: {self.macros.get('carbs',0)}g, Fats: {self.macros.get('fats',0)}g"
        return f"{self.name} - {self.servings} servings - Tags: {', '.join(self.tags)} - Calories/serving: {self.calories_per_serving} - Macros: {macros_str}"

    __repr__ = __str__

    def get_protein(self): return self.macros.get("protein", 0)
    def get_carbs(self): return self.macros.get("carbs", 0)
    def get_fats(self): return self.macros.get("fats", 0)

    @staticmethod
    def from_dict(data):
        d = dict(data)
        d['ingredients'] = [Ingredient.from_dict(ing) for ing in d.get('ingredients', [])]
        return Recipe(**d)

    def to_dict(self):
        return {
            "name": self.name,
            "servings": self.servings,
            "ingredients": [ing.to_dict() for ing in self.ingredients],
            "steps": self.steps,
            "tags": self.tags,
            "calories_per_serving": self.calories_per_serving,
            "macros": {
                "protein": self.macros.get("protein", 0),
                "carbs": self.macros.get("carbs", 0),
                "fats": self.macros.get("fats", 0),
            },
            "image": self.image,
        }

    @classmethod
    def read_from_json(cls, file_name: str):
        recipes: List[Recipe] = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, '..', 'data', file_name + '.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                recipes_data = json.load(f)
                for recipe_data in recipes_data:
                    recipes.append(cls.from_dict(recipe_data))
        except Exception as e:
            print(f"Error reading recipes: {e}")
        return recipes

    def check_ingredients(self, available_ingredients: List[Ingredient]):
        for ingredient in self.ingredients:
            required_qty = ingredient.default_quantity
            total_available = sum(avail_ing.default_quantity for avail_ing in available_ingredients if avail_ing.name == ingredient.name)
            if total_available < required_qty:
                return False
        return True

    def cook(self, available_ingredients: List[Ingredient]):
        if not self.check_ingredients(available_ingredients):
            return None
        for ingredient in self.ingredients:
            needed = ingredient.default_quantity
            same_name = [ing for ing in available_ingredients if ing.name == ingredient.name]
            # naive FIFO (no expiry ordering currently tracked consistently)
            for ing_obj in same_name:
                if needed <= 0:
                    break
                take = min(ing_obj.default_quantity, needed)
                ing_obj.set_quantity(-take)
                needed -= take
                if ing_obj.default_quantity <= 0:
                    try:
                        available_ingredients.remove(ing_obj)
                    except ValueError:
                        pass
        return RecipeCooked(self.name, self.servings, kallories=self.calories_per_serving, tags=self.tags)
