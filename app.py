from flask import Flask, request, jsonify, send_from_directory
import openai
import os
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
from google.cloud import storage
import json

app = Flask(__name__, static_folder="static")

# n8n Webhook URL (Replace this with your actual webhook URL)
N8N_WEBHOOK_URL = "https://supermallen.app.n8n.cloud/webhook/77cc4dc2-ad54-41b3-b3df-1dff0f800d48"

# Load Google Cloud credentials from Railway environment variable
GCS_KEY_JSON = os.getenv("GCS_KEY")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET")

print("GCS_KEY_JSON is", "set" if GCS_KEY_JSON else "NOT set")
gcs_credentials = service_account.Credentials.from_service_account_info(json.loads(GCS_KEY_JSON))
storage_client = storage.Client(credentials=gcs_credentials)
bucket = storage_client.bucket(GCS_BUCKET_NAME)

@app.route('/')
def home():
    return send_from_directory("static", "index.html")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form.get("message", "")
    input_type = request.form.get("voice", "false").lower() == "true"

    if not user_input and 'files' not in request.files:
        return jsonify({"error": "No input provided"}), 400

    try:
        # Prepare payload for n8n webhook
        data = {
            "message": user_input,
            "type": "voice" if input_type else "text"
        }

        files = request.files.getlist("files")
        file_payload = [("files", (f.filename, f.stream, f.content_type)) for f in files]

        response = requests.post(N8N_WEBHOOK_URL, data=data, files=file_payload)

        if response.status_code != 200:
            return jsonify({"error": "Failed to get response from n8n"}), 500

        response_data = response.json()
        marcus_reply = response_data.get("response", "")
        audio_url = response_data.get("audio_url", None)

        return jsonify({"response": marcus_reply, "audio_url": audio_url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
