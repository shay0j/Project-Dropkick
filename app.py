from flask import Flask, render_template, request, jsonify
import os
import openai
import configparser
import time
import json

# Read configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Check if the required OpenAI API key is present in the configuration
if 'openai' not in config or 'api_key' not in config['openai']:
    raise ValueError("OpenAI API key not found in config.ini")

# Get the API key from the config file
api_key = config['openai']['api_key']

# Set the environment variable
os.environ['OPENAI_API_KEY'] = api_key

# Initialize the OpenAI client
client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Load character information from the JSON file
with open('character_info.json') as f:
    character_info = json.load(f)

app = Flask(__name__)
app.static_folder = 'static'



@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/send', methods=['POST'])
def send_message():
    user_message = request.json.get('message', '')

#Character info loaded from JSON file
    prompt = config['Prompt']['prompt'].format(
        name=character_info['name'],
        traits=character_info['traits'],
        appearance=f"Body Type: {character_info['appearance']['body_type']}, Complexion: {character_info['appearance']['complexion']}",
        bio=f"Biography:{character_info['bio']['biography']}, House of Ashes: {character_info['bio']['House_of_Ashes']}, Accident: {character_info['bio']['accident']}",
        conversation_summary=''
    )

    conversation = [
        {"role": "system", "content": f"Your name is {character_info['name']}, your personality is {character_info['traits']}, you look like {character_info['appearance']}, your life story is {character_info['bio']}, your relationships with some of the people you know can be described as {character_info['relationships']}. You always speak in the first person and never break the character. You act accordingly,and you are talking to {user_message}."},
        {"role": "user", "content": user_message}
    ]


    retries = 3
    for attempt in range(retries):
        try:
            print("Sending conversation to OpenAI API:", conversation)

            response = client.chat.completions.create(
                model=config['LanguageModel']['model'],
                messages=conversation
            )

            print("Received response from OpenAI API:", response)

            # Access the response correctly
            bot_response = response.choices[0].message.content
            break
        except openai.error.RateLimitError as e:
            print(f"Rate limit error on attempt {attempt + 1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return jsonify(response="OpenAI API rate limit error: " + str(e))
        except Exception as e:
            print("Error:", str(e))
            return jsonify(response="OpenAI API error: " + str(e))

    prompt = prompt.replace('{conversation_summary}', f'Player: {user_message}\nCharacter: {bot_response}\n')

    return jsonify(response=bot_response)

if __name__ == '__main__':
    app.run(debug=True)
