import unittest
from fastapi.testclient import TestClient
from meal.api.api_run import app
from meal.infra.Plan_Repository import PlanRepository
from datetime import date

class TestShoppingListAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_api_shopping_list_basic(self):
        # Pregătește planul pentru săptămâna ISO curentă (dinamic)
        iso = date.today().isocalendar()
        week = iso.week
        repo = PlanRepository()
        plan = repo.get_week_plan(week)

        # Reset plan meals for deterministic test context
        for day, meals in plan.meals.items():
            meals['breakfast'] = '-'
            meals['lunch'] = '-'
            meals['dinner'] = '-'

        days = list(plan.meals.keys())
        if len(days) >= 5:
            plan.meals[days[0]]['lunch'] = 'Chicken Curry'
            plan.meals[days[1]]['breakfast'] = 'Vegetable Stir Fry'
            plan.meals[days[2]]['dinner'] = 'Chicken Curry'
            plan.meals[days[3]]['dinner'] = 'Spaghetti Bolognese'
            plan.meals[days[4]]['lunch'] = 'Chicken Curry'
        else:
            first = days[0]
            plan.meals[first]['breakfast'] = 'Vegetable Stir Fry'
            plan.meals[first]['lunch'] = 'Chicken Curry'
            plan.meals[first]['dinner'] = 'Chicken Curry'

        repo.save_week_plan(week, plan)

        resp = self.client.get('/api/shopping-list')  # fără param -> week curent
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('week', data)
        self.assertEqual(data['week'], week)
        self.assertIn('items', data)
        self.assertIn('count', data)
        items = data['items']
        if items:
            for it in items:
                for key in ('name','unit','required','have','missing'):
                    self.assertIn(key, it)
        # Bell pepper trebuie să apară ca lipsă
        bell = [i for i in items if i['name'].lower() == 'bell pepper']
        self.assertTrue(bell, 'Bell pepper should be missing (not in pantry).')
        # Spaghetti nu trebuie să apară (avem 500, cerință 400)
        spaghetti = [i for i in items if i['name'].lower() == 'spaghetti']
        self.assertFalse(spaghetti, 'Spaghetti should not be missing (pantry has enough).')
        # Chicken breast trebuie să fie missing cu 1000 (1500 necesar - 500 existent)
        # (Potential future assertion for Chicken breast deficit could be added here)

# Removed direct unittest.main() call to allow pytest discovery
