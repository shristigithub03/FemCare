from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import google.generativeai as genai
import json
from datetime import datetime
import os
import requests
import time
from flask_cors import CORS
import uuid

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

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Create user session
        session['user_id'] = str(uuid.uuid4())
        return redirect(url_for('onboarding'))
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Health Chatbot</title>
            <style>
                :root {
                    --primary: #ab0aab;
                    --secondary: #DB5968;
                    --light: #FCEAD9;
                    --accent1: #ed495d;
                    --accent2: #f96e83;
                    --dark: #2d645f;
                    --transparent: rgba(245, 53, 92, 0.723);
                }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: var(--light);
                    color: var(--dark);
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: var(--primary);
                    text-align: center;
                    margin-bottom: 30px;
                }
                .chat-container {
                    background-color: white;
                    border-radius: 15px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    padding: 20px;
                    margin-bottom: 20px;
                }
                #chatbox {
                    height: 400px;
                    overflow-y: auto;
                    padding: 15px;
                    margin-bottom: 15px;
                    border: 1px solid #eee;
                    border-radius: 10px;
                    background-color: #fafafa;
                }
                .user-message {
                    background-color: var(--transparent);
                    color: white;
                    padding: 10px 15px;
                    border-radius: 18px 18px 0 18px;
                    margin: 5px 0;
                    max-width: 80%;
                    float: right;
                    clear: both;
                }
                .bot-message {
                    background-color: var(--secondary);
                    color: white;
                    padding: 10px 15px;
                    border-radius: 18px 18px 18px 0;
                    margin: 5px 0;
                    max-width: 80%;
                    float: left;
                    clear: both;
                }
                .input-group {
                    display: flex;
                    gap: 10px;
                }
                #userInput {
                    flex: 1;
                    padding: 12px;
                    border: 2px solid var(--primary);
                    border-radius: 25px;
                    font-size: 16px;
                }
                button {
                    background-color: var(--primary);
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 12px 25px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: all 0.3s;
                }
                button:hover {
                    background-color: var(--accent1);
                    transform: translateY(-2px);
                }
                .welcome-box {
                    background: linear-gradient(135deg, var(--primary), var(--accent2));
                    color: white;
                    padding: 20px;
                    border-radius: 15px;
                    text-align: center;
                    margin-bottom: 30px;
                }
                .btn-start {
                    background-color: white;
                    color: var(--primary);
                    font-weight: bold;
                    padding: 12px 30px;
                    margin-top: 15px;
                }
            </style>
        </head>
        <body>
            <div class="welcome-box">
                <h1>Welcome to Health Assistant</h1>
                <p>Your personalized menstrual health companion</p>
                <form method="POST" action="/">
                    <button type="submit" class="btn-start">Get Started</button>
                </form>
            </div>
        </body>
        </html>
    ''')

@app.route("/onboarding", methods=['GET', 'POST'])
def onboarding():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        user_data = load_user_data()
        user_id = session['user_id']
        
        user_data[user_id] = {
            "name": request.form.get('name'),
            "age": int(request.form.get('age')),
            "cycle_phase": request.form.get('cycle_phase'),
            "cravings": request.form.get('cravings'),
            "dietary_specs": None,
            "cuisine": None,
            "allergies": None,
            "last_interaction": datetime.now().isoformat()
        }
        save_user_data(user_data)
        return redirect(url_for('chat_interface'))
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Personalization</title>
            <style>
                /* Reuse the same color variables from home */
                :root {
                    --primary: #ab0aab;
                    --secondary: #DB5968;
                    --light: #FCEAD9;
                    --accent1: #ed495d;
                    --accent2: #f96e83;
                    --dark: #2d645f;
                    --transparent: rgba(245, 53, 92, 0.723);
                }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: var(--light);
                    color: var(--dark);
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: var(--primary);
                    text-align: center;
                }
                .form-container {
                    background-color: white;
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }
                .form-group {
                    margin-bottom: 20px;
                }
                label {
                    display: block;
                    margin-bottom: 8px;
                    font-weight: 600;
                    color: var(--dark);
                }
                input, select {
                    width: 100%;
                    padding: 12px;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    font-size: 16px;
                    transition: border 0.3s;
                }
                input:focus, select:focus {
                    border-color: var(--primary);
                    outline: none;
                }
                button {
                    background-color: var(--primary);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 14px;
                    width: 100%;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                button:hover {
                    background-color: var(--accent1);
                }
            </style>
        </head>
        <body>
            <h1>Let's Personalize Your Experience</h1>
            <div class="form-container">
                <form method="POST" action="/onboarding">
                    <div class="form-group">
                        <label for="name">Your Name</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="age">Your Age</label>
                        <input type="number" id="age" name="age" min="10" max="100" required>
                    </div>
                    <div class="form-group">
                        <label for="cycle_phase">Current Cycle Phase</label>
                        <select id="cycle_phase" name="cycle_phase" required>
                            <option value="">Select phase</option>
                            <option value="menstrual">Menstrual</option>
                            <option value="follicular">Follicular</option>
                            <option value="ovulatory">Ovulatory</option>
                            <option value="luteal">Luteal</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="cravings">Current Cravings (if any)</label>
                        <input type="text" id="cravings" name="cravings" placeholder="e.g., chocolate, salty, spicy">
                    </div>
                    <button type="submit">Continue to Chat</button>
                </form>
            </div>
        </body>
        </html>
    ''')

@app.route("/chat", methods=['GET', 'POST'])
def chat_interface():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    user_id = session['user_id']
    user_data = load_user_data()
    
    if user_id not in user_data:
        return redirect(url_for('onboarding'))
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chat with Health Assistant</title>
            <style>
                :root {
                    --primary: #ab0aab;
                    --secondary: #DB5968;
                    --light: #FCEAD9;
                    --accent1: #ed495d;
                    --accent2: #f96e83;
                    --dark: #2d645f;
                    --transparent: rgba(245, 53, 92, 0.723);
                }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: var(--light);
                    color: var(--dark);
                    margin: 0;
                    padding: 0;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                }
                header {
                    background-color: var(--primary);
                    color: white;
                    padding: 15px 20px;
                    text-align: center;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .chat-container {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    max-width: 800px;
                    width: 100%;
                    margin: 0 auto;
                    padding: 20px;
                    box-sizing: border-box;
                }
                #chatbox {
                    flex: 1;
                    overflow-y: auto;
                    padding: 15px;
                    margin-bottom: 15px;
                    background-color: white;
                    border-radius: 15px;
                    box-shadow: inset 0 0 5px rgba(0,0,0,0.1);
                }
                .message {
                    margin-bottom: 15px;
                    max-width: 80%;
                    padding: 12px 18px;
                    border-radius: 20px;
                    line-height: 1.4;
                    position: relative;
                    animation: fadeIn 0.3s ease-out;
                }
                .user-message {
                    background-color: var(--transparent);
                    color: white;
                    margin-left: auto;
                    border-bottom-right-radius: 5px;
                }
                .bot-message {
                    background-color: var(--secondary);
                    color: white;
                    margin-right: auto;
                    border-bottom-left-radius: 5px;
                }
                .formatted-response {
                    background-color: white;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 10px 0;
                    color: var(--dark);
                    border-left: 4px solid var(--primary);
                }
                .input-area {
                    display: flex;
                    gap: 10px;
                    padding: 10px;
                    background-color: white;
                    border-radius: 30px;
                    box-shadow: 0 -2px 5px rgba(0,0,0,0.05);
                }
                #userInput {
                    flex: 1;
                    padding: 12px 20px;
                    border: 2px solid var(--primary);
                    border-radius: 30px;
                    font-size: 16px;
                    outline: none;
                }
                #sendButton {
                    background-color: var(--primary);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    cursor: pointer;
                    transition: all 0.3s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                #sendButton:hover {
                    background-color: var(--accent1);
                    transform: scale(1.05);
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .typing-indicator {
                    display: inline-block;
                    padding: 10px 15px;
                    background-color: #eee;
                    border-radius: 20px;
                    color: #666;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <header>
                <h1>Health Assistant</h1>
            </header>
            <div class="chat-container">
                <div id="chatbox">
                    <div class="bot-message">
                        Hello! I'm your health assistant. How can I help you today?
                    </div>
                </div>
                <div class="input-area">
                    <input type="text" id="userInput" placeholder="Type your message here..." autocomplete="off">
                    <button id="sendButton">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                    </button>
                </div>
            </div>

            <script>
                const chatbox = document.getElementById('chatbox');
                const userInput = document.getElementById('userInput');
                const sendButton = document.getElementById('sendButton');
                
                function formatResponse(text) {
                    // Format bullet points
                    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    text = text.replace(/\n/g, '<br>');
                    text = text.replace(/- (.*?)(<br>|$)/g, '• $1<br>');
                    return text;
                }
                
                function addMessage(sender, message, isFormatted = false) {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `${sender}-message message`;
                    
                    if (isFormatted) {
                        const formattedDiv = document.createElement('div');
                        formattedDiv.className = 'formatted-response';
                        formattedDiv.innerHTML = formatResponse(message);
                        messageDiv.appendChild(formattedDiv);
                    } else {
                        messageDiv.textContent = message;
                    }
                    
                    chatbox.appendChild(messageDiv);
                    chatbox.scrollTop = chatbox.scrollHeight;
                }
                
                function sendMessage() {
                    const message = userInput.value.trim();
                    if (!message) return;
                    
                    addMessage('user', message);
                    userInput.value = '';
                    
                    // Show typing indicator
                    const typingIndicator = document.createElement('div');
                    typingIndicator.className = 'bot-message message typing-indicator';
                    typingIndicator.textContent = 'Assistant is typing...';
                    chatbox.appendChild(typingIndicator);
                    chatbox.scrollTop = chatbox.scrollHeight;
                    
                    fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: '{{ session["user_id"] }}',
                            message: message
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Remove typing indicator
                        chatbox.removeChild(typingIndicator);
                        addMessage('bot', data.response, true);
                    })
                    .catch(error => {
                        chatbox.removeChild(typingIndicator);
                        addMessage('bot', "Sorry, I encountered an error. Please try again.");
                    });
                }
                
                sendButton.addEventListener('click', sendMessage);
                userInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') sendMessage();
                });
            </script>
        </body>
        </html>
    ''', user_id=user_id)

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
    app.run(host='0.0.0.0', port=5000, debug=True)