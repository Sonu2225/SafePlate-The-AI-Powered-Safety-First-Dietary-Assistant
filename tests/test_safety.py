import unittest
import json
import sys
import os

# --- 1. SETUP PATHS ---
# Add the project root directory to Python's path so we can find Service B
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import the app directly
from service_b_data.app import app

class TestSafetyGate(unittest.TestCase):

    def setUp(self):
        # Create a test client for Service B
        # This runs the app virtually without needing a port/server running
        self.app = app.test_client()
        self.app.testing = True

    def test_peanut_exclusion(self):
        """CRITICAL: Test that requesting peanuts when allergic returns 0 results."""
        print("\n--- TEST: Attempting to fetch peanut recipes while allergic ---")
        
        payload = {
            "max_calories": 2000,
            "allergens": ["peanuts"],
            "query": "peanut butter" # Intentionally asking for the allergen
        }
        
        response = self.app.post('/filter_recipes', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        
        data = response.get_json()
        safe_recipes = data.get('safe_recipes', [])
        
        # ASSERTION: The list must be EMPTY or contain NO peanuts
        for recipe in safe_recipes:
            # Safely get ingredients (default to empty string if missing)
            ingredients = (recipe.get('ingredients') or "").lower()
            self.assertNotIn("peanut", ingredients, f"SAFETY FAIL: Found 'peanut' in {recipe['name']}")
            
        print(f"PASSED: Database returned {len(safe_recipes)} recipes (Should be 0 or strictly safe).")

    def test_calorie_limit(self):
        """Test that the calorie limit is strictly enforced."""
        limit = 300
        payload = {"max_calories": limit, "allergens": [], "query": ""}
        
        response = self.app.post('/filter_recipes', 
                                 data=json.dumps(payload), 
                                 content_type='application/json')
        
        data = response.get_json()
        safe_recipes = data.get('safe_recipes', [])
        
        # Check every returned recipe
        for recipe in safe_recipes:
            self.assertLessEqual(recipe['calories'], limit, f"FAIL: {recipe['name']} is over {limit} calories.")
            
        print(f"PASSED: Checked {len(safe_recipes)} recipes for calorie limit {limit}.")

if __name__ == '__main__':
    unittest.main()