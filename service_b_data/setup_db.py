import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'RecipeCorpus.db')

def create_database():
    # Delete old database file if it exists, for a clean setup
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed old database: {DB_FILE}")

    # Connect to (or create) the database file
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    print("Creating 'recipes' table and 'recipes_fts' virtual table...")
    
    # --- Create the main recipe table ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        calories INTEGER,
        instructions TEXT,
        ingredients_text TEXT -- A plain-text field for searching
    )
    """)

    # --- Create the FTS5 Virtual Table for fast, robust search ---
    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS recipes_fts 
    USING fts5(
        name,
        ingredients_text,
        content='recipes', 
        content_rowid='id'
    )
    """)

    # --- Trigger to keep FTS table in sync with the recipes table ---
    cur.executescript("""
    CREATE TRIGGER IF NOT EXISTS recipes_ai AFTER INSERT ON recipes BEGIN
      INSERT INTO recipes_fts(rowid, name, ingredients_text) 
      VALUES (new.id, new.name, new.ingredients_text);
    END;
    CREATE TRIGGER IF NOT EXISTS recipes_ad AFTER DELETE ON recipes BEGIN
      INSERT INTO recipes_fts(recipes_fts, rowid, name, ingredients_text) 
      VALUES ('delete', old.id, old.name, old.ingredients_text);
    END;
    CREATE TRIGGER IF NOT EXISTS recipes_au AFTER UPDATE ON recipes BEGIN
      INSERT INTO recipes_fts(recipes_fts, rowid, name, ingredients_text) 
      VALUES ('delete', old.id, old.name, old.ingredients_text);
      INSERT INTO recipes_fts(rowid, name, ingredients_text) 
      VALUES (new.id, new.name, new.ingredients_text);
    END;
    """)
    
    print("Tables and triggers created successfully.")

    # --- Insert Sample Data ---
    print("Inserting 3 sample recipes for testing...")
    sample_recipes = [
        (1, 
         "Classic Peanut Butter Sandwich", 350, 
         "1. Spread peanut butter on one slice of bread. 2. Enjoy.", 
         "bread, peanut butter, jelly"),
        (2, 
         "Simple Garden Salad", 150, 
         "1. Chop lettuce and tomatoes. 2. Toss in a bowl. 3. Add dressing.", 
         "lettuce, tomato, olive oil, vinegar"),
        (3, 
         "Cheesy Scrambled Eggs", 420, 
         "1. Whisk eggs, milk, and cheese. 2. Scramble in a hot pan.", 
         "eggs, milk, cheddar cheese, butter, salt")
    ]

    cur.executemany("INSERT INTO recipes VALUES(?, ?, ?, ?, ?)", sample_recipes)
    
    con.commit()
    con.close()
    
    print(f"Database setup complete. File created at: {DB_FILE}")

if __name__ == "__main__":
    create_database()