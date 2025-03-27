from flask import Flask, request, jsonify, send_from_directory
import openai
import os
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
from google.cloud import storage
import json
import base64
import time
from io import BytesIO

app = Flask(__name__, static_folder="static")

# 🔗 Replace these with your actual n8n webhook URLs
N8N_CHAT_WEBHOOK_URL = "https://supermallen.app.n8n.cloud/webhook/8822c292-c476-49a6-8353-fcc45d67dea9"
N8N_VOICE_WEBHOOK_URL = "https://supermallen.app.n8n.cloud/webhook/a713fdd6-6923-4a6b-a906-0e381c1681ef"

# Load Google Cloud credentials
GCS_KEY_JSON = os.getenv("GCS_KEY_JSON")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET")
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
        # 🔁 Use different n8n webhook URL depending on input type
        webhook_url = N8N_VOICE_WEBHOOK_URL if input_type else N8N_CHAT_WEBHOOK_URL

        # Prepare payload for n8n
        data = {
            "message": user_input,
            "type": "voice" if input_type else "text"
        }

        # Attach any uploaded files
        files = request.files.getlist("files")
        file_payload = [("files", (f.filename, f.stream, f.content_type)) for f in files]

        # Send to n8n
        response = requests.post(webhook_url, data=data, files=file_payload)
        response_data = response.json()

        # Parse response from Marcus
        marcus_reply = response_data.get("response", "")
        audio_url = response_data.get("audio_url", None)
        audio_data_b64 = response_data.get("audio_data")

        # 🔊 If audio is returned, upload it to GCS and generate public URL
        if audio_data_b64:
            audio_bytes = base64.b64decode(audio_data_b64)
            audio_filename = f"marcus_reply_{int(time.time())}.mp3"

            blob = bucket.blob(audio_filename)
            blob.upload_from_file(BytesIO(audio_bytes), content_type="audio/mpeg")
            blob.make_public()

            audio_url = blob.public_url

        return jsonify({
            "response": marcus_reply,
            "audio_url": audio_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
