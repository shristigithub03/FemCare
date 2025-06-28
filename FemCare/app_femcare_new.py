from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import json
from datetime import datetime
import os
import requests
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# API Configuration
api_key = "AIzaSyCLnI_Tl1zS3nRcfBWsyBhxiJvu3x9dOLw"
mistral_api_key = "J2hdJ9IT34rK8P0t6SnJQkLfpCUTA9vy"
genai.configure(api_key=api_key)

# Database Setup
USER_DATA_FILE = "user_data.json"

PROMPT_TEMPLATES = {
    "general_health": "You are a menstrual health assistant. Provide a clear, factual, and educational response to the following question about menstrual health: {user_input}. Ensure the response is appropriate for all audiences.",
    "nutrition": "You are a nutritionist specializing in menstrual health. Based on the user's current cycle phase ({cycle_phase}) and cravings ({cravings}), provide specific dietary recommendations. Answer: {user_input}",
    "child_friendly": "You are a friendly menstrual health assistant. Answer: '{user_input}' in a simple, age-appropriate way. Use comforting language and keep it brief.",
    "exercise": "You are a fitness coach specializing in menstrual health. Based on cycle phase ({cycle_phase}), recommend exercises. Answer: '{user_input}'",
    "cravings_alternatives": "Suggest healthy alternatives for cravings ({cravings}) in the {cycle_phase} phase. Answer: '{user_input}'",
    "meal_planner": "Create a daily meal plan considering cycle phase ({cycle_phase}), cravings ({cravings}), dietary specs ({dietary_specs}), cuisine ({cuisine}), and allergies ({allergies}). Format: Breakfast: [meal] Lunch: [meal] Dinner: [meal]",
    "fertility": "You are a fertility specialist. Answer: '{user_input}' about fertility clearly without jargon.",
    "puberty": "Help understand puberty and periods. Answer: '{user_input}' simply and empathetically."
}

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

def ask_mistral(prompt):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {mistral_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

def ask_gpt(prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "FALLBACK_TO_MISTRAL"
    except Exception:
        return "FALLBACK_TO_MISTRAL"
    finally:
        time.sleep(1)

def determine_intent(user_input, age, cravings):
    user_input = user_input.lower()
    if age < 18:
        return "child_friendly"
    elif "alternative" in user_input and cravings:
        return "cravings_alternatives"
    elif any(word in user_input for word in ["nutrition", "diet", "food", "eat"]):
        return "nutrition"
    elif any(word in user_input for word in ["exercise", "workout", "fitness"]):
        return "exercise"
    elif any(word in user_input for word in ["pregnant", "fertility", "ovulation"]):
        return "fertility"
    elif any(word in user_input for word in ["puberty", "teen", "young"]):
        return "puberty"
    else:
        return "general_health"

def handle_question(user_input, user_data, user_id):
    age = user_data[user_id]["age"]
    cravings = user_data[user_id]["cravings"]
    cycle_phase = user_data[user_id]["cycle_phase"]
    intent = determine_intent(user_input, age, cravings)

    if intent == "nutrition":
        prompt = PROMPT_TEMPLATES["nutrition"].format(
            cycle_phase=cycle_phase, cravings=cravings, user_input=user_input)
    elif intent == "child_friendly":
        prompt = PROMPT_TEMPLATES["child_friendly"].format(user_input=user_input)
    elif intent == "exercise":
        prompt = PROMPT_TEMPLATES["exercise"].format(
            cycle_phase=cycle_phase, user_input=user_input)
    elif intent == "cravings_alternatives":
        prompt = PROMPT_TEMPLATES["cravings_alternatives"].format(
            cravings=cravings, cycle_phase=cycle_phase, user_input=user_input)
    elif intent == "fertility":
        prompt = PROMPT_TEMPLATES["fertility"].format(user_input=user_input)
    elif intent == "puberty":
        prompt = PROMPT_TEMPLATES["puberty"].format(user_input=user_input)
    else:
        prompt = PROMPT_TEMPLATES["general_health"].format(user_input=user_input)

    response = ask_gpt(prompt)
    return response if response != "FALLBACK_TO_MISTRAL" else ask_mistral(prompt)

@app.route("/")
def home():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Health Chatbot</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
                #chatbox { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
                #userInput { width: 75%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                button { width: 20%; padding: 8px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
                .user { color: #0066cc; margin: 5px 0; }
                .bot { color: #009933; margin: 5px 0; }
            </style>
        </head>
        <body>
            <h1>Health Assistant</h1>
            <div id="chatbox"></div>
            <div>
                <input type="text" id="userInput" placeholder="Ask about health...">
                <button onclick="sendMessage()">Send</button>
            </div>
            <script>
                function sendMessage() {
                    const input = document.getElementById('userInput');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    const chatbox = document.getElementById('chatbox');
                    chatbox.innerHTML += `<div class="user">You: ${message}</div>`;
                    
                    fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: "web_user", message: message })
                    })
                    .then(response => response.json())
                    .then(data => {
                        chatbox.innerHTML += `<div class="bot">Bot: ${data.response}</div>`;
                        chatbox.scrollTop = chatbox.scrollHeight;
                        input.value = '';
                    });
                }
                document.getElementById('userInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') sendMessage();
                });
            </script>
        </body>
        </html>
    ''')

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    user_data = load_user_data()
    user_data[user_id] = {
        "name": data.get('name', 'User'),
        "age": int(data.get('age', 25)),
        "cycle_phase": data.get('cycle_phase', 'follicular'),
        "cravings": data.get('cravings', 'none'),
        "last_interaction": datetime.now().isoformat()
    }
    save_user_data(user_data)
    return jsonify({'status': 'success', 'user_id': user_id})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id', 'web_user')
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {
            "name": "Web User",
            "age": 25,
            "cycle_phase": "follicular",
            "cravings": "none",
            "last_interaction": datetime.now().isoformat()
        }
        save_user_data(user_data)
    
    response = handle_question(message, user_data, user_id)
    return jsonify({'response': response})

@app.route('/api/quiz', methods=['GET'])
def quiz():
    return jsonify({
        "questions": [
            {
                "question": "Average menstrual cycle length?",
                "options": ["21 days", "28 days", "35 days"],
                "answer": 1
            },
            {
                "question": "Phase after ovulation?",
                "options": ["Follicular", "Luteal", "Menstrual"],
                "answer": 1
            }
        ]
    })

@app.route('/api/meal_plan', methods=['POST'])
def meal_planner():
    data = request.json
    user_id = data.get('user_id', 'web_user')
    
    user_data = load_user_data()
    if user_id not in user_data:
        return jsonify({'error': 'User not found'}), 404
    
    prompt = PROMPT_TEMPLATES["meal_planner"].format(
        cycle_phase=user_data[user_id]["cycle_phase"],
        cravings=user_data[user_id]["cravings"],
        dietary_specs=data.get('dietary_specs', 'none'),
        cuisine=data.get('cuisine', 'any'),
        allergies=data.get('allergies', 'none')
    )
    
    plan = ask_gpt(prompt)
    return jsonify({'meal_plan': plan})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # This will work in all cases