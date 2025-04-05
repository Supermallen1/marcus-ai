from flask import Flask, request, jsonify, send_from_directory, Response
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
    print("\n🔥 /chat endpoint hit")

    user_input = request.form.get("message", "")
    is_voice = request.form.get("voice", "false").lower() == "true"
    session_id = request.form.get("sessionId") or f"marcus-{int(time.time())}"

    if not user_input and 'files' not in request.files:
        return jsonify({"error": "No input provided"}), 400

    try:
        # Construct form data
        form_data = {
            "message": user_input,
            "sessionId": session_id,
            "input_type": "voice" if is_voice else "text"
        }

        files = request.files.getlist("files")
        file_payload = [("files", (f.filename, f.stream, f.content_type)) for f in files]

        print("📤 Sending to Marcus via webhook:", N8N_MARCUS_WEBHOOK_URL)
        response = requests.post(N8N_MARCUS_WEBHOOK_URL, data=form_data, files=file_payload)
        print("✅ n8n Response Status:", response.status_code)

        content_type = response.headers.get("Content-Type", "")
        print("📦 Response Content-Type:", content_type)

        if "audio" in content_type:
            # Directly return the MP3 audio stream to the frontend
            return Response(
                response.content,
                status=200,
                mimetype="audio/mp3",
                headers={
                    "Content-Disposition": "inline; filename=marcus.mp3"
                }
            )

        # Fallback: assume it's JSON
        response_data = response.json()
        print("📝 Text response from Marcus:", response_data)
        return jsonify(response_data)

    except Exception as e:
        print("🔥 Error:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
