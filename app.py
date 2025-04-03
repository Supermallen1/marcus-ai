from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import json
import base64
import time
from io import BytesIO
from google.oauth2 import service_account
from google.cloud import storage

app = Flask(__name__, static_folder="static")

# === Webhook URL to Marcus (Production) ===
N8N_MARCUS_WEBHOOK_URL = "https://supermallen.app.n8n.cloud/webhook/8248cbab-abaa-4490-aa7d-6ff07a87be62"

# === Google Cloud Storage Setup ===
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
    print("\n🔥 Chat endpoint was hit")

    user_input = request.form.get("message", "")
    input_type = request.form.get("voice", "false").lower() == "true"

    if not user_input and 'files' not in request.files:
        print("❌ No input provided")
        return jsonify({"error": "No input provided"}), 400

    try:
        # Prepare request to Marcus via n8n webhook
        print("🧠 Using Marcus webhook:", N8N_MARCUS_WEBHOOK_URL)

        data = {
            "message": user_input,
            "sessionId": "marcus-session-001",  # Optional: replace with dynamic ID if needed
            "input_type": "voice" if input_type else "text"
        }

        files = request.files.getlist("files")
        file_payload = [("files", (f.filename, f.stream, f.content_type)) for f in files]

        response = requests.post(N8N_MARCUS_WEBHOOK_URL, data=data, files=file_payload)
        print("✅ n8n Response status:", response.status_code)

        content_type = response.headers.get("Content-Type", "")
        if "audio" in content_type:
            audio_bytes = response.content
            audio_filename = f"marcus_reply_{int(time.time())}.mp3"

            # Upload to GCS
            blob = bucket.blob(audio_filename)
            blob.upload_from_file(BytesIO(audio_bytes), content_type="audio/mpeg")
            blob.make_public()
            audio_url = blob.public_url
            print("🔊 Audio uploaded to GCS:", audio_url)

            return jsonify({"audio_url": audio_url})

        # Fallback: handle non-audio response
        response_data = response.json()
        print("📝 Fallback response from Marcus:", response_data)
        return jsonify(response_data)

    except Exception as e:
        print("🔥 Exception occurred:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
