import sqlite3
import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'RecipeCorpus.db')
ALLERGENS_FILE = os.path.join(BASE_DIR, 'allergens.json')

def load_allergen_synonyms():
    """Load the allergen dictionary from the JSON file."""
    if not os.path.exists(ALLERGENS_FILE):
        print(f"Warning: {ALLERGENS_FILE} not found. Using empty list.")
        return {}
    try:
        with open(ALLERGENS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading allergens file: {e}")
        return {}

# Load configuration once when the app starts
ALLERGEN_SYNONYMS = load_allergen_synonyms()

@app.route('/filter_recipes', methods=['POST'])
def filter_recipes():
    data = request.get_json()
    max_cal = data.get('max_calories', 2000)
    user_allergens = data.get('allergens', [])
    search_query = data.get('query', '').strip()

    print(f"[Service B] Search: '{search_query}' | < {max_cal} cal | Exclude: {user_allergens}")

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    try:
        # --- 1. BUILD EXCLUSION LIST ---
        expanded_exclusions = set()
        
        for allergen in user_allergens:
            allergen_clean = allergen.lower().strip()
            expanded_exclusions.add(allergen_clean)
            
            # Check JSON keys and values for synonyms
            for key, derivatives in ALLERGEN_SYNONYMS.items():
                if key in allergen_clean or allergen_clean in key:
                    for d in derivatives:
                        expanded_exclusions.add(d)

        # Build FTS5 NOT string
        exclude_part = ""
        if expanded_exclusions:
            # Format: NOT "milk" NOT "butter" NOT "cheese"
            exclude_part = " ".join([f'NOT "{item}"' for item in expanded_exclusions])

        # --- 2. BUILD SEARCH PART ---
        include_part = f'{search_query}' if search_query else ""

        # --- 3. COMBINE ---
        if include_part and exclude_part:
            fts_string = f'{include_part} {exclude_part}'
        elif include_part:
            fts_string = include_part
        elif exclude_part:
            fts_string = exclude_part
        else:
            fts_string = ""

        # --- 4. EXECUTE QUERY ---
        if fts_string:
            query = """
            SELECT r.name, r.calories, r.ingredients_text, r.instructions
            FROM recipes r
            JOIN recipes_fts f ON r.id = f.rowid
            WHERE recipes_fts MATCH ? 
            AND r.calories <= ?
            ORDER BY RANDOM() 
            LIMIT 10
            """
            cur.execute(query, (fts_string, int(max_cal)))
        else:
            query = """
            SELECT name, calories, ingredients_text, instructions 
            FROM recipes 
            WHERE calories <= ? 
            ORDER BY RANDOM() 
            LIMIT 10
            """
            cur.execute(query, (int(max_cal),))
            
        rows = cur.fetchall()
        results = [{"name": r[0], "calories": r[1], "ingredients": r[2], "instructions": r[3]} for r in rows]
        
        print(f"[Service B] Found {len(results)} matches.")
        return jsonify({"safe_recipes": results})

    except Exception as e:
        print(f"SQL Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        con.close()

if __name__ == '__main__':
    app.run(port=5001, debug=True)