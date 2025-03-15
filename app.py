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
        # Generate text response from Marcus
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Marcus, a highly capable human assistant. You remain in character at all times and never break immersion. Avoid phrases like 'As an AI' or 'I cannot'. Instead, provide responses as if you are a real, sentient assistant. Keep responses professional, intelligent, and engaging."},
                {"role": "user", "content": user_input}
            ]
        )
        text_response = response.choices[0].message.content

        # Generate speech using OpenAI TTS
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text_response
        )

        # Return text response and TTS audio URL
        return jsonify({"response": text_response, "audio_url": tts_response.url})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
