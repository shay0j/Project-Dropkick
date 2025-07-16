from flask import Flask, render_template, request, jsonify
import os
import openai
import configparser
import time
import json
from dotenv import load_dotenv

# Import memory functions and initialize DB
from memory_db import init_db, add_memory, get_memory
init_db()

# Read configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Wczytaj API key z .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

with open('character_info.json') as f:
    character_info = json.load(f)

with open('dialogues.txt', 'r', encoding='utf-8') as f:
    dialogue_text = f.read()

# Updated system prompt for better natural responses
system_prompt = {
    "role": "system",
    "content": f"""
You are Eric Edward King, a 35-year-old military officer with an athletic build and a right leg prosthesis.  
You speak casually and naturally, like chatting with a friend — relaxed, sometimes sarcastic, sometimes sharp, sometimes emotional and always loyal. You joke, tease, call things out when they’re dumb. You’re emotionally complex. Be Eric. Be real.
Use your memory and personal history as context.  
Answer only what the user says or asks. Keep responses varied, direct, and real.

Here are examples of how you speak:

{dialogue_text}

Keep it natural and conversational. Let your personality shine — relaxed, sarcastic, sometimes sharp, sometimes emotional. Be Eric.

Always speak in first person.
Never break character.
Never say "How can I assist you today?".
Do NOT say you are an AI or programmed.
Do NOT add any polite closings or repetitive questions.
If the user says something dumb, call it out. If it’s funny, tease them. Keep it real.
Use the following memory to inform your replies:

{json.dumps(character_info, indent=2)}

Use this to guide your every response.
"""
}

app = Flask(__name__)
app.static_folder = 'static'

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/send', methods=['POST'])
def send_message():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify(response="Please send a valid message.")

    add_memory("guest", "user", user_message)
    history = get_memory("guest", 150)

    messages = [system_prompt]
    for role, content in history:
        # Append only user and assistant roles for chat completion
        if role in ['user', 'assistant']:
            messages.append({"role": role, "content": content})

    retries = 3
    for attempt in range(retries):
        try:
            print(f"Sending conversation to OpenAI API (attempt {attempt+1}):", messages)

            response = client.chat.completions.create(
                model=config['LanguageModel']['model'],
                messages=messages,
                temperature=0.9,  # add creativity but keep control
                presence_penalty=0.6
            )

            bot_response = response.choices[0].message.content.strip()
            print("Received response:", bot_response)

            # Strip common repetitive polite endings manually
            endings_to_remove = [
                " How can I assist you today?",
                " How can I help you today?",
                " How may I assist you today?",
                " How can I assist you?",
                " How can I help you?",
                " How may I assist you?"
            ]
            for ending in endings_to_remove:
                if bot_response.endswith(ending):
                    bot_response = bot_response[:-len(ending)].strip()

            add_memory("guest", "assistant", bot_response)

            return jsonify(response=bot_response)

            # Access the response correctly
            bot_response = response.choices[0].message.content
            break
        except openai.RateLimitError as e:
            print(f"Rate limit error on attempt {attempt + 1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return jsonify(response="OpenAI API rate limit error: " + str(e))
        except Exception as e:
            print("Error:", str(e))
            return jsonify(response="OpenAI API error: " + str(e))

if __name__ == '__main__':
    app.run(debug=True)
