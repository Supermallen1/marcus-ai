from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import base64
import time

app = Flask(__name__, static_folder="static")
TEMP_AUDIO_FOLDER = os.path.join("static", "audio")
os.makedirs(TEMP_AUDIO_FOLDER, exist_ok=True)

# === Webhook URLs ===
N8N_CHAT_WEBHOOK_URL = "https://supermallen.app.n8n.cloud/webhook/8822c292-c476-49a6-8353-fcc45d67dea9"
N8N_VOICE_WEBHOOK_URL = "https://supermallen.app.n8n.cloud/webhook/a713fdd6-6923-4a6b-a906-0e381c1681ef"

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
        webhook_url = N8N_VOICE_WEBHOOK_URL if input_type else N8N_CHAT_WEBHOOK_URL
        print("🧠 Webhook selected:", webhook_url)

        data = {
            "message": user_input,
            "type": "voice" if input_type else "text"
        }
        print("📦 Payload to n8n:", data)

        files = request.files.getlist("files")
        file_payload = [("files", (f.filename, f.stream, f.content_type)) for f in files]

        response = requests.post(webhook_url, data=data, files=file_payload)
        print("✅ n8n Response status:", response.status_code)

        response_data = response.json()
        print("📝 n8n Response data:", response_data)

        audio_data_b64 = response_data.get("audio_data")

        audio_url = None
        if audio_data_b64:
            audio_bytes = base64.b64decode(audio_data_b64)
            audio_filename = f"marcus_reply_{int(time.time())}.mp3"
            audio_path = os.path.join(TEMP_AUDIO_FOLDER, audio_filename)
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            audio_url = f"/static/audio/{audio_filename}"
            print("🔊 Saved audio file:", audio_url)

        return jsonify({"response": marcus_reply, "audio_url": audio_url})

    except Exception as e:
        print("🔥 Exception occurred:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))

