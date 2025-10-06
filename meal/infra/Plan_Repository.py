import json, os, random
from typing import Optional, List
from datetime import timedelta, date, datetime
from meal.domain.Plan import Plan
from meal.api.routes.recipes import load_recipes
from meal.infra.paths import PLAN_FILE

def _week_key(year: int, week_number: int) -> str:
    return f"{year}-W{week_number:02d}"

class PlanRepository:
    def get_week_plan(self, week_number: int, year: Optional[int] = None) -> Plan:
        if year is None:
            year = date.today().isocalendar().year
        if not os.path.exists(PLAN_FILE):
            with open(PLAN_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)
        try:
            with open(PLAN_FILE, "r", encoding="utf-8") as f:
                store = json.load(f) or {}
        except Exception:
            store = {}
        key = _week_key(year, week_number)
        if key not in store:
            store[key] = {d: {"breakfast": "-", "lunch": "-", "dinner": "-"}
                          for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]}
            with open(PLAN_FILE, "w", encoding="utf-8") as f:
                json.dump(store, f, indent=2, ensure_ascii=False)
        meals = store[key]
        monday = date.fromisocalendar(year, week_number, 1)
        days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        for i, day_name in enumerate(days):
            d = monday + timedelta(days=i)
            meals.setdefault(day_name, {"breakfast": "-", "lunch": "-", "dinner": "-"})
            meals[day_name].setdefault("breakfast", "-")
            meals[day_name].setdefault("lunch", "-")
            meals[day_name].setdefault("dinner", "-")
            meals[day_name]["date"] = d.strftime("%d.%m.%Y")
        plan = Plan(week_number, meals, year=year)
        plan.week = week_number
        plan.year = year
        return plan

    def save_week_plan(self, week_number: int, plan: Plan, year: Optional[int] = None) -> None:
        if year is None:
            year = getattr(plan, "year", date.today().isocalendar().year)
        try:
            with open(PLAN_FILE, "r", encoding="utf-8") as f:
                store = json.load(f) or {}
        except Exception:
            store = {}
        key = _week_key(year, week_number)
        clean_meals = {day: {k: v for k, v in meals.items() if k != "date"}
                       for day, meals in plan.meals.items()}
        store[key] = clean_meals
        with open(PLAN_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False)

    def reset_week(self, week_number: int, year: Optional[int] = None):
        """Reset non-cooked meals for future (or today) days only.

        Rules:
          - Do NOT modify meals whose date is in the past.
          - Do NOT modify slots already marked as cooked (dict with cooked=True).
          - Other slots are set back to '-'.

        """
        plan = self.get_week_plan(week_number, year)
        today = date.today()
        for day, meals in plan.meals.items():
            # Parse day date if present
            day_date = None
            try:
                day_date = datetime.strptime(meals.get("date",""), "%d.%m.%Y").date()
            except Exception:
                pass
            if day_date and day_date < today:
                # Skip past days entirely
                continue
            for slot in ("breakfast", "lunch", "dinner"):
                val = meals.get(slot)
                # Preserve cooked meals (dict with cooked True)
                if isinstance(val, dict) and val.get("cooked"):
                    continue
                meals[slot] = "-"
        self.save_week_plan(week_number, plan, year)

    def randomize_week(self, week_number: int, year: Optional[int] = None):
        """Fill meal plan with random recipes.

        Behavior:
          - Past days are never modified.
          - Cooked slots (dict with cooked=True) are never replaced.
          - If the entire week is in the future, non-cooked slots (including already assigned names) are re-randomized.
          - Otherwise, only empty placeholders ('-', '', None) are filled.
        """
        plan = self.get_week_plan(week_number, year)
        recipes = load_recipes()
        recipe_names = [r["name"] for r in recipes] if recipes else []
        today = date.today()
        day_dates = []
        for meals in plan.meals.values():
            try:
                day_dates.append(datetime.strptime(meals["date"], "%d.%m.%Y").date())
            except Exception:
                pass
        entire_week_in_future = bool(day_dates) and min(day_dates) > today
        fill_only_empty = not entire_week_in_future
        for day, meals in plan.meals.items():
            try:
                day_date = datetime.strptime(meals["date"], "%d.%m.%Y").date()
            except Exception:
                continue
            if day_date < today:
                continue
            for meal in ("breakfast", "lunch", "dinner"):
                current = meals.get(meal)
                # Always skip cooked entries
                if isinstance(current, dict) and current.get("cooked"):
                    continue
                if fill_only_empty and current not in (None, "", "-"):
                    continue
                meals[meal] = random.choice(recipe_names) if recipe_names else "-"
        self.save_week_plan(week_number, plan, year)

    def randomize_custom(self, week_number: int, year: Optional[int] = None, days: Optional[List[str]] = None, replace_existing: bool = False) -> int:
        """Randomize specific days.

        Args:
            week_number: ISO week number
            year: year
            days: list of day names (Monday..Sunday); if None -> all
            replace_existing: if True, replace any non-cooked slot (string) including already assigned recipes
                               if False, fill only placeholders ('-', '', None)
        Returns:
            int: number of slots modified (value actually changed)
        Rules:
          - Never modify past calendar days.
          - Never modify cooked slots (dict with cooked=True).
        """
        plan = self.get_week_plan(week_number, year)
        recipes = load_recipes()
        recipe_names = [r["name"] for r in recipes] if recipes else []
        today = date.today()
        valid_days = {"Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"}
        target_days = set(d for d in (days or valid_days) if d in valid_days)
        modified = 0
        for day_name, meals in plan.meals.items():
            if day_name not in target_days:
                continue
            try:
                day_date = datetime.strptime(meals.get("date",""), "%d.%m.%Y").date()
            except Exception:
                continue
            if day_date < today:
                continue  # skip past
            for slot in ("breakfast", "lunch", "dinner"):
                cur = meals.get(slot)
                if isinstance(cur, dict) and cur.get("cooked"):
                    continue
                if not replace_existing and cur not in (None, "", "-"):
                    continue
                new_val = random.choice(recipe_names) if recipe_names else "-"
                if new_val != cur:
                    meals[slot] = new_val
                    modified += 1
        self.save_week_plan(week_number, plan, year)
        return modified
