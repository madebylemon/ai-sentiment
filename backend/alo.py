import numpy as np
import os
import tempfile
import uuid
from flask import Flask, request, jsonify, send_from_directory
import base64
from io import BytesIO
from PIL import Image
import google.generativeai as genai
from deepface import DeepFace
from werkzeug.utils import secure_filename
import speech_recognition as sr
from textblob import TextBlob
from transformers import pipeline
from gtts import gTTS
from flask_cors import CORS

# Allowed audio extensions and max duration (seconds)
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mpeg'}
MAX_DURATION = 30  # Optional stretch
UPLOAD_FOLDER = tempfile.gettempdir()

from flask import render_template
import pathlib
BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()
TEMPLATES_DIR = str(BASE_DIR / "templates")
STATIC_DIR = str(BASE_DIR / "static")
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
@app.route("/")
def index():
    return render_template("index.html")
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper: Check allowed file

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper: Get file duration (optional, for stretch goal)
def get_audio_duration(filepath):
    try:
        import wave
        import contextlib
        if filepath.lower().endswith('.wav'):
            with contextlib.closing(wave.open(filepath, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)
                return duration
        else:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(filepath)
            return len(audio) / 1000.0
    except Exception:
        return None

# Helper: Sentiment analysis using Hugging Face Transformers (fallback to TextBlob)
sentiment_pipeline = None
def analyze_sentiment(text):
    global sentiment_pipeline
    try:
        if sentiment_pipeline is None:
            sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        result = sentiment_pipeline(text)[0]
        label = result['label'].upper()
        score = round(result['score'], 2)
        return {'label': label, 'score': score}
    except Exception as e:
        # Fallback to TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        if polarity > 0.2:
            label = 'POSITIVE'
        elif polarity < -0.2:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'
        return {'label': label, 'score': round(abs(polarity), 2), 'fallback': True, 'error': str(e)}

# Helper: Generate response based on sentiment
def generate_response(sentiment_label):
    if sentiment_label == 'NEGATIVE':
        return "I'm here for you. It sounds like you're having a hard time. Can you tell me more?"
    elif sentiment_label == 'POSITIVE':
        return "That's wonderful to hear! Keep up the positive momentum."
    else:
        return "I'm listening. Tell me how you're feeling today."

# Helper: Convert text to speech and save as mp3
def text_to_speech(text, filename):
    tts = gTTS(text)
    tts.save(filename)


# Therapist chat endpoint: expects JSON { message: str, face_image: base64 str }
@app.route('/api/therapist', methods=['POST'])
def therapist():
    data = request.get_json()
    user_message = data.get('message', '')
    face_image_b64 = data.get('face_image', None)
    facial_emotion = None
    if face_image_b64:
        try:
            header, b64data = face_image_b64.split(',') if ',' in face_image_b64 else ('', face_image_b64)
            img_bytes = BytesIO(base64.b64decode(b64data))
            img = Image.open(img_bytes).convert('RGB')
            result = DeepFace.analyze(img_path = np.array(img), actions = ['emotion'], enforce_detection=False)
            if isinstance(result, list):
                result = result[0]
            dominant_emotion = result['dominant_emotion']
            emotion_score = result['emotion'][dominant_emotion]
            # Ensure emotion_score is a native Python float for JSON serialization
            emotion_score_py = float(emotion_score)
            facial_emotion = {'label': dominant_emotion.upper(), 'score': round(emotion_score_py, 2)}
        except Exception as e:
            facial_emotion = {'label': 'UNKNOWN', 'score': 0.0, 'error': str(e)}

    sentiment = analyze_sentiment(user_message)
    # Compose prompt for Gemini
    prompt = f"You are a compassionate therapist. The user says: '{user_message}'."
    if facial_emotion:
        prompt += f" The user's facial emotion appears to be {facial_emotion['label'].lower()} (score: {facial_emotion['score']})."
    prompt += " Respond empathetically and helpfully."

    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key:
        ai_response = "Gemini API key is not set. Please set the GEMINI_API_KEY environment variable."
    else:
        try:
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('models/gemini-2.0-flash')
            response = model.generate_content(prompt)
            ai_response = response.text
        except Exception as e:
            ai_response = f"Sorry, I couldn't generate a response right now. Error: {str(e)}"

    return jsonify({
        'response': ai_response,
        'facial_emotion': facial_emotion,
        'sentiment': sentiment
    })

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    # Serve the generated audio file
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)