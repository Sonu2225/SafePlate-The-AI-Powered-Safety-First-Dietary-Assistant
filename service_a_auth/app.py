import sqlite3
import os
import bcrypt
import random
import string
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
CORS(app)

DB_FILE = os.path.join(os.path.dirname(__file__), 'SecureUserProfile.db')

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

def get_db():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({"error": "Missing fields"}), 400
        
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password.encode(), salt)
    
    try:
        con = get_db()
        con.execute("INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)", 
                   (username, email, pw_hash, salt))
        con.execute("INSERT INTO preferences VALUES (?, ?, ?, ?, ?)", (username, "", 2000, "Any", 60))
        con.commit()
        con.close()
        return jsonify({"message": "Account created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    con = get_db()
    user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    con.close()
    
    if user and bcrypt.checkpw(password.encode(), user['password_hash']):
        return jsonify({"message": "Login successful", "username": username}), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    con = get_db()
    user = con.execute("SELECT username FROM users WHERE email=?", (email,)).fetchone()
    
    if not user:
        con.close()
        return jsonify({"error": "Email not found"}), 404
    
    code = ''.join(random.choices(string.digits, k=6))
    
    con.execute("UPDATE users SET reset_token=? WHERE email=?", (code, email))
    con.commit()
    con.close()
    
    try:
        msg = Message(
            subject="Password Reset Request", 
            sender=app.config['MAIL_USERNAME'], 
            recipients=[email]
        )
        msg.body = f"Your password reset code is: {code}\n\nThis code expires in 15 minutes."
        
        mail.send(msg)
        return jsonify({"message": "Reset code sent to email."})
        
    except Exception as e:
        print(f"Mail Error: {e}")
        return jsonify({"error": "Failed to send email. Check server logs."}), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email', '').strip()
    code = data.get('code', '').strip()
    new_password = data.get('new_password')
    
    con = get_db()
    user = con.execute("SELECT reset_token, salt FROM users WHERE email=?", (email,)).fetchone()
    
    if not user or str(user['reset_token']) != str(code):
        con.close()
        return jsonify({"error": "Invalid reset code"}), 401
        
    new_hash = bcrypt.hashpw(new_password.encode(), user['salt'])
    con.execute("UPDATE users SET password_hash=?, reset_token=NULL WHERE email=?", (new_hash, email))
    con.commit()
    con.close()
    
    return jsonify({"message": "Password reset successful"})

@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    con = get_db()
    if request.method == 'GET':
        row = con.execute("SELECT * FROM preferences WHERE username=?", (username,)).fetchone()
        con.close()
        if row: return jsonify(dict(row))
        return jsonify({"error": "User not found"}), 404
        
    if request.method == 'POST':
        data = request.get_json()
        con.execute("""
            UPDATE preferences 
            SET allergens=?, calorie_limit=?, cuisine_pref=?, cooking_time=? 
            WHERE username=?
        """, (data['allergens'], data['calorie_limit'], data['cuisine_pref'], data['cooking_time'], username))
        con.commit()
        con.close()
        return jsonify({"message": "Profile updated successfully"})

if __name__ == '__main__':
    app.run(port=5000, debug=True)