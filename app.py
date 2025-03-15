from flask import Flask, request, jsonify, send_from_directory
import openai
import os

app = Flask(__name__, static_folder="static")

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def home():
    return send_from_directory("static", "index.html")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message", "")

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are Marcus, a human assistant. Stay in character and never say 'As an AI...'"},
                      {"role": "user", "content": user_input}]
        )

        # Ensure correct response extraction
        response_message = response.choices[0].message.content if hasattr(response.choices[0], "message") else "Error processing response"

        return jsonify({"response": response_message})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
