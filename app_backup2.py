from flask import Flask, render_template, request, jsonify
from openai import OpenAI  # Importing openai directly
import configparser

# Read configurations from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Check if the required OpenAI API key is present in the configuration
if 'OpenAI' not in config or 'api_key' not in config['OpenAI']:
    raise ValueError("OpenAI API key not found in config.ini")

# Initialize the OpenAI client
openai.api_key = config['OpenAI']['api_key']

app = Flask(__name__)
app.static_folder = 'static'

@app.route('/')
def home():
    # Render the chat.html template when the root URL is accessed
    return render_template('chat.html')

@app.route('/send', methods=['POST'])
def send_message():
    # Get the user's message from the request
    user_message = request.json.get('message', '')

    # Placeholder character info 
    character_info = {
        "name": "Unknown Character",
        "appearance": {
            "body_type": "Unknown",
            "complexion": "Unknown"
        },
        "bio": {
            "House_of_Ashes": "Unknown",
            "accident": "Unknown"
        },
        "traits": "Unknown"
    }

    # Update the prompt to include character details
    prompt = config['Prompt']['prompt'].format(
        name=character_info['name'],
        traits=character_info['traits'],
        appearance=character_info['appearance'],
        bio=character_info['bio'],
        conversation_summary=''
    )

    # Construct the conversation format for the OpenAI API
    conversation = [
        {"role": "system", "content": f"You are {character_info['name']}, and you are talking to {user_message}."},
        {"role": "user", "content": user_message}
    ]

    try:
        # Debug: print the conversation being sent to OpenAI API
        print("Sending conversation to OpenAI API:", conversation)

        # Call the OpenAI API to process the user's message and get a response
        response = openai.ChatCompletion.create(
            model=config['LanguageModel']['model'],
            messages=conversation
        )

        # Debug: print the response received from OpenAI API
        print("Received response from OpenAI API:", response)

        bot_response = response['choices'][0]['message']['content']
    except Exception as e:
        # Handle API errors
        print("Error:", str(e))  # Debug: print the error
        return jsonify(response="OpenAI API error: " + str(e))

    # Update the conversation summary with the latest interaction
    prompt = prompt.replace('{conversation_summary}', f'Player: {user_message}\nCharacter: {bot_response}\n')

    # Return the bot's response as JSON
    return jsonify(response=bot_response)

if __name__ == '__main__':
    app.run(debug=True)
