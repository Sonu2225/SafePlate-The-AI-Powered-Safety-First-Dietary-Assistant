import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'SecureUserProfile.db')

def create_secure_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()

    # 1. Users Table (Added Email and Token columns)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        password_hash BLOB NOT NULL, 
        salt BLOB NOT NULL,
        reset_token TEXT
    )
    """)

    # 2. Preferences Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS preferences (
        username TEXT PRIMARY KEY,
        allergens TEXT,
        calorie_limit INTEGER DEFAULT 2000,
        cuisine_pref TEXT DEFAULT 'Any',
        cooking_time INTEGER DEFAULT 60,
        FOREIGN KEY(username) REFERENCES users(username)
    )
    """)

    con.commit()
    con.close()
    print(f"User DB (with Email support) created at: {DB_FILE}")

if __name__ == "__main__":
    create_secure_db()