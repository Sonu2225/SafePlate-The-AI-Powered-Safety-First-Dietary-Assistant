import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
import json
import time

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
# Enable CORS for everything
CORS(app, resources={r"/*": {"origins": "*"}})

SERVICE_B_URL = "http://127.0.0.1:5001/filter_recipes"

# Global variables to hold models
fast_model = None
smart_model = None

def configure_models():
    global fast_model, smart_model
    try:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("CRITICAL: GOOGLE_API_KEY not found in environment!")
            return False
            
        genai.configure(api_key=api_key)
        
        # Initialize models
        fast_model = genai.GenerativeModel('gemini-2.5-flash')
        smart_model = genai.GenerativeModel('gemini-2.5-pro')
        print("Gemini Models Initialized")
        return True
    except Exception as e:
        print(f" Model Init Error: {e}")
        return False

# Initialize on startup
models_ready = configure_models()

def get_smart_keywords(user_msg):
    if not fast_model: return user_msg
    try:
        # IMPROVED PROMPT: Translates concepts like "High Protein" into searchable ingredients
        prompt = f"""
        TASK: Convert the user's request into a list of specific search ingredients.
        REQUEST: "{user_msg}"
        OUTPUT: Space-separated keywords only. No commas.
        
        EXAMPLES:
        - "High Protein" -> chicken beef pork fish tofu beans eggs
        - "Vegetarian" -> vegetable tofu beans rice pasta
        - "Italian" -> pasta tomato basil cheese
        """
        response = fast_model.generate_content(prompt)
        return response.text.strip().replace(",", "")
    except:
        return user_msg

@app.route('/generate', methods=['POST'])
def generate_response():
    data = request.get_json()
    user_msg = data.get('message', '')
    history = data.get('history', [])
    profile = data.get('profile', {})
    
    print(f"[Service C] Processing: '{user_msg}'")

    def generate():
        # 1. CRITICAL HEARTBEAT
        yield json.dumps({"text": ""}) + "\n"

        # 2. CHECK SETUP
        if not models_ready or not smart_model:
            yield json.dumps({"text": " System Error: AI models not configured. Check API Key."}) + "\n"
            return

        # 3. LOGIC
        raw_keywords = get_smart_keywords(user_msg)
        search_query = " OR ".join([f'"{t}"' for t in raw_keywords.split()]) if raw_keywords else ""
        
        max_cal = profile.get('calorie_limit', 2000)
        allergens = profile.get('allergens', [])

        safe_recipes = []
        try:
            b_payload = {"max_calories": max_cal, "allergens": allergens, "query": search_query}
            response = requests.post(SERVICE_B_URL, json=b_payload, timeout=10)
            safe_recipes = response.json().get('safe_recipes', [])
            
            # Fallback
            if not safe_recipes:
                b_payload["query"] = "" 
                response = requests.post(SERVICE_B_URL, json=b_payload, timeout=10)
                safe_recipes = response.json().get('safe_recipes', [])
        except Exception as e:
            print(f"Service B Warning: {e}")

        recipe_context = "SYSTEM NOTE: Database returned 0 safe recipes."
        if safe_recipes:
            recipe_context = "AVAILABLE RECIPES:\n"
            for r in safe_recipes:
                recipe_context += f"- {r['name']} ({r['calories']} cal) | Ing: {r['ingredients']} | Instr: {r['instructions']}\n"

        # 4. STREAMING GENERATION
        chat = smart_model.start_chat(history=history)
        
        # IMPROVED PROMPT: Explicit substitution rules
        system_instruction = f"""
        ROLE: Expert Culinary Consultant (Safety Focused).
        USER PROFILE: Max Calories: {max_cal} | Allergens: {allergens}
        CONTEXT: {recipe_context}
        
        INSTRUCTIONS:
        1. Select the BEST recipe matching "{user_msg}".
        2. SUBSTITUTION: If ingredients conflict with allergies, substitute them.
           - If Gluten-Free & Soy Sauce found -> Replace with "Tamari".
           - If Dairy-Free & Butter found -> Replace with "Olive Oil".
           - If Peanut-Free & Peanut Butter found -> Replace with "Sunflower Butter".
        3. FORMATTING: Use Markdown headers (##) and bullets (*).
        
        REQUIRED FORMAT:
        ## [Recipe Name] ([Calories] cal)
        > *[Description]*
        ### Ingredients
        * [List with Substitutions Applied]
        ### Instructions
        1. [Steps]
        ---
        **Safety Check:** [State any substitutions made]
        """
        
        full_prompt = f"{system_instruction}\nUSER MESSAGE: {user_msg}"

        try:
            response = chat.send_message(full_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield json.dumps({"text": chunk.text}) + "\n"
        except Exception as e:
            yield json.dumps({"text": f"\n **AI Error:** {str(e)}"}) + "\n"

    # 5. CREATE RESPONSE WITH EXPLICIT CORS HEADERS
    response = Response(stream_with_context(generate()), mimetype='application/x-ndjson')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run(port=5002, debug=True, threaded=True)