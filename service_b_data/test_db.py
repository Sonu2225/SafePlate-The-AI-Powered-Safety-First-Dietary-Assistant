import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'RecipeCorpus.db')

def run_query(description, query, params=()):
    print(f"\n--- {description} ---")
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        cur.execute(query, params)
        results = cur.fetchall()
        
        if not results:
            print("Query returned: No results found.")
        else:
            for row in results:
                print(f"Query returned: {row}")
        
    except Exception as e:
        print(f"QUERY FAILED: {e}")
    finally:
        if con:
            con.close()

def test_database():
    if not os.path.exists(DB_FILE):
        print(f"TEST FAILED: Database file not found at {DB_FILE}")
        return

    print(f"Found database at {DB_FILE}. Running tests...")

    # Test 1: Get all recipes 
    run_query(
        "Test 1: Basic connection (SELECT * FROM recipes)",
        "SELECT id, name, calories FROM recipes"
    )

    # Test 2: FTS5 Inclusion Test 
    run_query(
        "Test 2: FTS5 Inclusion (Find recipes with 'peanut')",
        "SELECT name, ingredients_text FROM recipes_fts WHERE recipes_fts MATCH ?",
        ("peanut",)
    )

    # "Select from recipes WHERE the ID is NOT IN the list of rows that match 'peanut'"
    run_query(
        "Test 3: SQL Exclusion (Find recipes WITHOUT 'peanut')",
        """
        SELECT name, ingredients_text
        FROM recipes
        WHERE id NOT IN (SELECT rowid FROM recipes_fts WHERE recipes_fts MATCH ?)
        """,
        ("peanut",)
    )

    # We combine the calorie check with the same SQL subquery logic.
    run_query(
        "Test 4: Combined Query (Find recipes < 400 cal AND WITHOUT 'milk')",
        """
        SELECT name, calories, ingredients_text
        FROM recipes
        WHERE calories < ? 
        AND id NOT IN (SELECT rowid FROM recipes_fts WHERE recipes_fts MATCH ?)
        """,
        (400, "milk")
    )

if __name__ == "__main__":
    test_database()