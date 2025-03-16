from flask import Flask, request, jsonify, send_from_directory
import openai
import os
import requests

app = Flask(__name__, static_folder="static")

# n8n Webhook URL (Replace this with your actual webhook URL)
N8N_WEBHOOK_URL = "https://supermallen.app.n8n.cloud/webhook/77cc4dc2-ad54-41b3-b3df-1dff0f800d48"

@app.route('/')
def home():
    return send_from_directory("static", "index.html")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message", "")
    input_type = request.json.get("type", "text")  # "text" or "voice"

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Send request to n8n webhook
        response = requests.post(N8N_WEBHOOK_URL, json={
            "message": user_input,
            "type": input_type  # This helps n8n determine the response format
        })

        if response.status_code != 200:
            return jsonify({"error": "Failed to get response from n8n"}), 500
        
        response_data = response.json()
        marcus_reply = response_data.get("response", "")
        audio_url = response_data.get("audio_url", None)  # If n8n generates audio

        return jsonify({"response": marcus_reply, "audio_url": audio_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
