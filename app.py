import os
import uuid
import io
import json
import time
import urllib.parse
from flask import Flask, request, jsonify, render_template, send_file, make_response
from dotenv import load_dotenv
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
from pydub import AudioSegment, exceptions as pydub_exceptions

# --- Configuration & Initialization ---
print("[INFO] Loading environment variables...")
load_dotenv()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
print(f"[INFO] Upload folder set at: {UPLOAD_FOLDER}")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in environment variables")
print("[INFO] Gemini API Key loaded successfully")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')

# --- Helper Functions ---
def get_gemini_response(text_prompt):
    """Get response from Gemini AI model"""
    print(f"[Gemini] Generating response for prompt: {text_prompt}")
    try:
        response = gemini_model.generate_content(text_prompt)
        print("[Gemini] Response generated successfully")
        return response.text
    except Exception as e:
        print(f"[ERROR] Gemini generation failed: {str(e)}")
        return f"Error: {str(e)}"

def generate_tts_audio_file(text_to_speak, output_file_path):
    """Generate TTS audio file using pyttsx3"""
    print(f"[TTS] Generating speech for text: {text_to_speak}")
    if not text_to_speak:
        return False

    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Adjust speech rate
        engine.save_to_file(text_to_speak, output_file_path)
        engine.runAndWait()
        print(f"[TTS] Audio saved at: {output_file_path}")

        if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
            return True
        return False
    except Exception as e:
        print(f"[TTS ERROR] {str(e)}")
        if os.path.exists(output_file_path):
            try: os.remove(output_file_path)
            except: pass
        return False

# --- Flask Routes ---
@app.route('/')
def index():
    print("[ROUTE] Index page requested")
    return render_template('index.html')

@app.route('/process-full-audio', methods=['POST'])
def process_full_audio_route():
    print("[ROUTE] /process-full-audio POST request received")
    if 'audio_blob' not in request.files:
        print("[ERROR] No audio_blob part found in request")
        return jsonify({"error": "No audio file part"}), 400

    audio_file = request.files['audio_blob']
    if not audio_file or audio_file.filename == '':
        print("[ERROR] No selected audio file")
        return jsonify({"error": "No selected file"}), 400

    unique_id = str(uuid.uuid4())
    input_ext = os.path.splitext(audio_file.filename)[1] or '.webm'
    input_filename = f"{unique_id}_input{input_ext}"
    wav_filename = f"{unique_id}_converted.wav"
    output_tts_filename = f"{unique_id}_response.wav"

    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
    wav_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
    output_tts_path = os.path.join(app.config['UPLOAD_FOLDER'], output_tts_filename)

    files_to_delete = [input_path, wav_path, output_tts_path]

    try:
        print("[STEP] Saving and converting uploaded audio...")
        audio_file.save(input_path)
        audio = AudioSegment.from_file(input_path).set_channels(1)
        audio.export(wav_path, format="wav")

        print("[STEP] Performing speech recognition...")
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            transcribed_text = recognizer.recognize_google(audio_data, language="en-US")
        print(f"[SPEECH] Transcribed Text: {transcribed_text}")

        print("[STEP] Getting Gemini response...")
        gemini_response = get_gemini_response(transcribed_text)
        if gemini_response.startswith("Error:"):
            raise RuntimeError(gemini_response)
        print(f"[GEMINI] Response: {gemini_response}")

        print("[STEP] Generating TTS response audio...")
        if not generate_tts_audio_file(gemini_response, output_tts_path):
            raise RuntimeError("TTS generation failed")

        print("[STEP] Preparing final audio response...")
        with open(output_tts_path, 'rb') as f:
            audio_bytes = f.read()

        response = make_response(send_file(
            io.BytesIO(audio_bytes),
            mimetype='audio/wav',
            download_name='response.wav'
        ))
        response.headers['X-Transcription'] = urllib.parse.quote(transcribed_text)
        response.headers['X-Gemini-Response'] = urllib.parse.quote(gemini_response)
        return response

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        print("[CLEANUP] Deleting temporary files...")
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"[CLEANUP] Deleted {file_path}")
                except Exception as e:
                    print(f"[CLEANUP ERROR] {file_path} not deleted: {str(e)}")

@app.route('/process-text', methods=['POST'])
def process_text_route():
    print("[ROUTE] /process-text POST request received")
    if not request.is_json:
        print("[ERROR] Request body not JSON")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    input_text = data.get('text', '')
    client_id = f"text-{uuid.uuid4()}"
    output_tts_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{client_id}_response.wav")

    try:
        print(f"[STEP] Getting Gemini response for text: {input_text}")
        gemini_response = get_gemini_response(input_text)
        if gemini_response.startswith("Error:"):
            raise RuntimeError(gemini_response)

        print("[STEP] Generating TTS audio for Gemini response...")
        if not generate_tts_audio_file(gemini_response, output_tts_path):
            raise RuntimeError("TTS generation failed")

        print("[STEP] Returning audio response...")
        with open(output_tts_path, 'rb') as f:
            audio_bytes = f.read()

        response = make_response(send_file(
            io.BytesIO(audio_bytes),
            mimetype='audio/wav',
            download_name='response.wav'
        ))
        response.headers['X-Gemini-Response'] = urllib.parse.quote(gemini_response)
        return response

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(output_tts_path):
            try:
                os.remove(output_tts_path)
                print(f"[CLEANUP] Deleted {output_tts_path}")
            except Exception as e:
                print(f"[CLEANUP ERROR] Could not delete {output_tts_path}: {str(e)}")

if __name__ == '__main__':
    print("[SERVER] Starting Flask app on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
