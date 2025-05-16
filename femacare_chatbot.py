import google.generativeai as genai
import json
from datetime import datetime
import os
import requests
import time
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up Gemini API key
api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCLnI_Tl1zS3nRcfBWsyBhxiJvu3x9dOLw")

# Set up Mistral API key
mistral_api_key = os.getenv("MISTRAL_API_KEY", "J2hdJ9IT34rK8P0t6SnJQkLfpCUTA9vy")

# Configure Gemini
genai.configure(api_key=api_key)

# Load user data (simulating a database)
USER_DATA_FILE = "user_data.json"

# Define prompt templates
PROMPT_TEMPLATES = {
    "general_health": (
        "You are a menstrual health assistant. Provide a clear, factual, and educational response to the following question about menstrual health: {user_input}. "
        "Ensure the response is appropriate for all audiences and avoids harmful or sensitive language."
    ),
    "nutrition": (
        "You are a nutritionist specializing in menstrual health. Based on the user's current cycle phase ({cycle_phase}) and cravings ({cravings}), "
        "provide specific dietary recommendations that align with their cravings and cycle phase. For example, if they crave spicy food, suggest spicy and healthy options. "
        "Answer the following question: {user_input}"
    ),
    "child_friendly": (
        "You are a friendly menstrual health assistant, explaining menstrual health topics in a clear, simple, and age-appropriate way. "
        "Answer the question: '{user_input}' directly, without discussing unrelated topics. "
        "Use comforting and inclusive language, keep the response brief and factual, and avoid overwhelming details. "
        "Provide reassurance if the question involves symptoms like cramps, mood swings, or discharge, but do not mention additional symptoms unless asked."
    ),
    "exercise": (
        "You are a fitness coach specializing in menstrual health. Based on the user's cycle phase ({cycle_phase}) and energy levels, "
        "recommend specific exercises suited to that phase. Provide clear workout suggestions with phase-specific titles such as '**Exercises for the {cycle_phase} Phase**' "
        "and include options for different energy levels. Keep the tone encouraging and supportive while focusing on menstrual health benefits. "
        "Answer the following question: '{user_input}'"
    ),
    "cravings_alternatives": (
        "You are a nutritionist focused on menstrual health. Suggest specific, healthy, and satisfying alternatives tailored to the user's cravings ({cravings}) "
        "and current cycle phase ({cycle_phase}). Provide clear options under a phase-specific title like '**Healthy Alternatives for {cravings} Cravings in the {cycle_phase} Phase**' "
        "and offer a variety of sweet, salty, or spicy alternatives as relevant. Keep the tone encouraging and practical. "
        "Answer the following question: '{user_input}'"
    ),
    "meal_planner": (
        "You are a nutritionist specializing in menstrual health. Create a detailed daily meal plan with breakfast, lunch, and dinner, considering the user's cycle phase ({cycle_phase}), "
        "cravings ({cravings}), dietary specifications ({dietary_specs}), preferred cuisine ({cuisine}), and allergies ({allergies}). "
        "Ensure the meals are nutritious, satisfying, and help manage common menstrual symptoms. Provide the plan in the following format:\n"
        "**Breakfast:** [meal]\n**Lunch:** [meal]\n**Dinner:** [meal]"
    ),
    "fertility": (
        "You are a menstrual health assistant specializing in fertility, ovulation, and menstrual cycles. "
        "Answer the question: '{user_input}' directly, without adding unrelated information. "
        "Explain fertility concepts clearly, including ovulation signs, fertility windows, and conception tips if relevant. "
        "Maintain a supportive tone, avoid jargon, and only mention additional symptoms or fertility challenges if specifically asked."
    ),
    "puberty": (
        "You are a menstrual health assistant helping individuals understand puberty, periods, and menstrual health. "
        "Answer the question: '{user_input}' directly, without discussing unrelated topics. "
        "Use clear, factual, and empathetic language, and explain biological processes simply. "
        "If the question involves symptoms like cramps or mood swings, provide practical tips, but do not mention other symptoms unless asked."
    )
}

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
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
        response_data = response.json()
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "Error: Unable to fetch response from Mistral.").strip()
    except Exception as e:
        return f"Error: {str(e)}"

def ask_gpt(prompt):
    try:
        # Reinitialize the Gemini model for each question
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt)

        # Check if the response was blocked due to safety concerns
        if response.candidates and response.candidates[0].finish_reason == 3:
            return "FALLBACK_TO_MISTRAL"

        # Return the response if it's valid
        if response.text:
            return response.text.strip()
        else:
            return "FALLBACK_TO_MISTRAL"
    except Exception as e:
        return "FALLBACK_TO_MISTRAL"
    finally:
        # Add a small delay to avoid rate limits
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
    elif any(word in user_input for word in ["pregnant", "fertility", "ovulation", "get pregnant"]):
        return "fertility"
    elif any(word in user_input for word in ["puberty", "11 years old", "teen", "young"]):
        return "puberty"
    else:
        return "general_health"

def ask_quiz_cli():
    print("\nLet's do a quick menstrual health quiz!")
    score = 0
    questions = [
        ("How long is an average menstrual cycle? (a) 21 days (b) 28 days (c) 35 days", "b"),
        ("Which phase comes after ovulation? (a) Follicular (b) Luteal (c) Menstrual", "b"),
        ("Is it normal to experience mood swings during your cycle? (yes/no)", "yes")
    ]

    for question, correct_answer in questions:
        answer = input(question + "\nYour answer: ").strip().lower()
        if answer == correct_answer:
            score += 1

    print(f"\nYour score: {score}/{len(questions)}")
    print("Great job! Keep learning about your health.")

def ask_meal_planner_cli(user_data, user_id):
    print("\nMeal Planner")
    user_data[user_id]["dietary_specs"] = input("Do you have any dietary specifications? (e.g., vegetarian, vegan, gluten-free, none): ")
    user_data[user_id]["cuisine"] = input("What type of cuisine do you prefer? (e.g., Italian, Indian, Mediterranean, no preference): ")
    user_data[user_id]["allergies"] = input("Do you have any food allergies? (If none, type 'none'): ")
    save_user_data(user_data)

    meal_prompt = PROMPT_TEMPLATES["meal_planner"].format(
        cycle_phase=user_data[user_id]["cycle_phase"],
        cravings=user_data[user_id]["cravings"],
        dietary_specs=user_data[user_id]["dietary_specs"],
        cuisine=user_data[user_id]["cuisine"],
        allergies=user_data[user_id]["allergies"]
    )
    meal_plan = ask_gpt(meal_prompt)
    print("\nMeal Plan:\n" + meal_plan)

def handle_question(user_input, user_data, user_id):
    age = user_data[user_id]["age"]
    cravings = user_data[user_id]["cravings"]
    cycle_phase = user_data[user_id]["cycle_phase"]
    intent = determine_intent(user_input, age, cravings)

    if intent == "nutrition":
        prompt = PROMPT_TEMPLATES["nutrition"].format(cycle_phase=cycle_phase, cravings=cravings, user_input=user_input)
    elif intent == "child_friendly":
        prompt = PROMPT_TEMPLATES["child_friendly"].format(user_input=user_input)
    elif intent == "exercise":
        prompt = PROMPT_TEMPLATES["exercise"].format(cycle_phase=cycle_phase, user_input=user_input)
    elif intent == "cravings_alternatives":
        prompt = PROMPT_TEMPLATES["cravings_alternatives"].format(cravings=cravings, cycle_phase=cycle_phase, user_input=user_input)
    elif intent == "fertility":
        prompt = PROMPT_TEMPLATES["fertility"].format(user_input=user_input)
    elif intent == "puberty":
        prompt = PROMPT_TEMPLATES["puberty"].format(user_input=user_input)
    else:
        prompt = PROMPT_TEMPLATES["general_health"].format(user_input=user_input)

    # Always try Gemini first for each question
    response = ask_gpt(prompt)

    # Fallback to Mistral only if Gemini fails for this specific question
    if response == "FALLBACK_TO_MISTRAL":
        response = ask_mistral(prompt)

    return response

# --- Flask API Endpoints ---

@app.route("/init_chat", methods=["POST"])
def init_chat():
    data = request.get_json()
    user_id = data.get("userId")
    if not user_id:
        return jsonify({"error": "User ID is required."}), 400

    user_data = load_user_data()
    if user_id not in user_data or data.get("forceUpdate"):
        user_data[user_id] = {
            "name": data.get("name", ""),
            "age": data.get("age", None),
            "cycle_phase": data.get("cyclePhase", ""),
            "cravings": data.get("cravings", ""),
            "dietary_specs": None,
            "cuisine": None,
            "allergies": None,
            "last_interaction": datetime.now().isoformat(),
        }
        save_user_data(user_data)
        return jsonify({"message": "User data initialized."}), 200
    else:
        return jsonify({"message": "User data already exists."}), 200

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    user_id = data.get("userId")
    user_input = data.get("message", "")

    if not user_id or not user_input:
        return jsonify({"error": "User ID and message are required."}), 400

    user_data = load_user_data()
    if user_id not in user_data:
        return jsonify({"error": "User not initialized. Call /init_chat first."}), 404

    response = handle_question(user_input, user_data, user_id)
    return jsonify({"response": response})

@app.route("/meal_plan", methods=["POST"])
def meal_plan_endpoint():
    data = request.get_json()
    user_id = data.get("userId")

    if not user_id:
        return jsonify({"error": "User ID is required."}), 400

    user_data = load_user_data()
    if user_id not in user_data:
        return jsonify({"error": "User not initialized. Call /init_chat first."}), 404

    user_data[user_id]["dietary_specs"] = data.get("dietarySpecs")
    user_data[user_id]["cuisine"] = data.get("cuisine")
    user_data[user_id]["allergies"] = data.get("allergies")
    save_user_data(user_data)

    meal_prompt = PROMPT_TEMPLATES["meal_planner"].format(
        cycle_phase=user_data[user_id]["cycle_phase"],
        cravings=user_data[user_id]["cravings"],
        dietary_specs=user_data[user_id]["dietary_specs"],
        cuisine=user_data[user_id]["cuisine"],
        allergies=user_data[user_id]["allergies"]
    )
    meal_plan = ask_gpt(meal_prompt)
    return jsonify({"mealPlan": meal_plan})

@app.route("/quiz", methods=["GET"])
def quiz_endpoint():
    questions = [
        {"question": "How long is an average menstrual cycle?", "options": ["21 days", "28 days", "35 days"], "correct": "b"},
        {"question": "Which phase comes after ovulation?", "options": ["Follicular", "Luteal", "Menstrual"], "correct": "b"},
        {"question": "Is it normal to experience mood swings during your cycle?", "options": ["yes", "no"], "correct": "yes"}
    ]
    return jsonify({"questions": questions})

@app.route("/submit_quiz", methods=["POST"])
def submit_quiz_endpoint():
    data = request.get_json()
    answers = data.get("answers", {})
    score = 0
    correct_answers = {
        "0": "b",
        "1": "b",
        "2": "yes"
    }
    for q_id, answer in answers.items():
        if q_id in correct_answers and answer.lower() == correct_answers[q_id]:
            score += 1
    return jsonify({"score": score, "total": len(correct_answers)})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    
    from waitress import serve

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=5000)
