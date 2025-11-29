import sqlite3
import os
import pandas as pd

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'RecipeCorpus.db')

# --- THE CORRECT URL ---
# We use the raw link to the 13k-recipes.csv file on the 'main' branch
DATASET_URL = "https://raw.githubusercontent.com/josephrmartinez/recipe-dataset/main/13k-recipes.csv"

def create_database():
    # 1. Clean Slate
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed old database: {DB_FILE}")

    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    # 2. Create Tables
    print("Creating tables...")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        calories INTEGER,
        instructions TEXT,
        ingredients_text TEXT
    )
    """)

    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS recipes_fts 
    USING fts5(name, ingredients_text, content='recipes', content_rowid='id')
    """)

    cur.executescript("""
    CREATE TRIGGER IF NOT EXISTS recipes_ai AFTER INSERT ON recipes BEGIN
      INSERT INTO recipes_fts(rowid, name, ingredients_text) VALUES (new.id, new.name, new.ingredients_text);
    END;
    """)

    # 3. Load Data Directly from URL
    print(f"Downloading data from: {DATASET_URL}...")
    try:
        # Pandas can read directly from a URL!
        df = pd.read_csv(DATASET_URL)
        
        print(f"Download complete. Processing {len(df)} rows...")
        
        # Normalize columns to lowercase (Title -> title, Instructions -> instructions)
        df.columns = [c.lower().strip() for c in df.columns]
        
        recipes_to_insert = []
        
        for index, row in df.iterrows():
            try:
                # Map the specific columns from this dataset
                # The dataset uses: 'Title', 'Ingredients', 'Instructions'
                title = row.get('title', 'Unknown')
                ingredients = row.get('ingredients', '')
                instructions = row.get('instructions', '')
                
                # Skip invalid rows
                if pd.isna(title) or pd.isna(ingredients):
                    continue

                # Generate dummy calories (dataset doesn't have them)
                # Logic: longer ingredient list = more calories
                estimated_cal = int(len(str(ingredients)) * 1.5)
                if estimated_cal > 1200: estimated_cal = 1200
                if estimated_cal < 100: estimated_cal = 150

                recipes_to_insert.append((
                    str(title), 
                    estimated_cal, 
                    str(instructions), 
                    str(ingredients)
                ))
            except Exception as e:
                pass # Skip bad rows

        if recipes_to_insert:
            print(f"Inserting {len(recipes_to_insert)} recipes into SQLite...")
            cur.executemany("INSERT INTO recipes (name, calories, instructions, ingredients_text) VALUES (?, ?, ?, ?)", recipes_to_insert)
            con.commit()
            print(f"Success! Database populated with {len(recipes_to_insert)} recipes.")
        else:
            print("No recipes found. Check the column names.")

    except Exception as e:
        print(f"Error downloading/processing CSV: {e}")
    
    con.close()

if __name__ == "__main__":
    create_database()