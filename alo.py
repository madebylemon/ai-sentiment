
from werkzeug.datastructures import FileStorage
from deepface import DeepFace
from PIL import Image
import numpy as np
import os
import tempfile
import uuid
import base64
from io import BytesIO
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import speech_recognition as sr
from textblob import TextBlob
from gtts import gTTS
from flask_cors import CORS


# =============================
# Configurations
# =============================
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mpeg'}
MAX_DURATION = 30  # seconds
MAX_FILE_SIZE_MB = 10
UPLOAD_FOLDER = tempfile.gettempdir()

# =============================
# Utility Functions
# =============================

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper: Check allowed file

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper: Get file duration (optional, for stretch goal)
def get_audio_duration(filepath):
    """Return duration of audio file in seconds."""
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
    except Exception as e:
        print(f"[ERROR] Failed to get audio duration: {e}")
        return None

# Helper: Sentiment analysis using TextBlob
def analyze_sentiment(text):
    """Analyze sentiment and return label, score, and polarity."""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        label = 'POSITIVE'
    elif polarity < -0.2:
        label = 'NEGATIVE'
    else:
        label = 'NEUTRAL'
    return {'label': label, 'score': round(abs(polarity), 2), 'polarity': polarity}

# Helper: Generate response based on sentiment
def generate_response(sentiment_label):
    """Generate a response based on sentiment label."""
    if sentiment_label == 'NEGATIVE':
        return "I'm here for you. It sounds like you're having a hard time. Can you tell me more?"
    elif sentiment_label == 'POSITIVE':
        return "That's wonderful to hear! Keep up the positive momentum."
    else:
        return "I'm listening. Tell me how you're feeling today."

# Helper: Convert text to speech and save as mp3
def text_to_speech(text, filename):
    """Convert text to speech and save as mp3."""
    tts = gTTS(text)
    tts.save(filename)

@app.route('/api/therapy', methods=['POST'])
def therapy():
    """
    POST /api/therapy
    Accepts: multipart/form-data with 'audio' file
    Returns: JSON with transcript, sentiment, AI response, audio_response (mp3), and details
    """
    transcript = None
    sentiment = None
    ai_response = None
    audio_response = None
    duration = None
    file_size_mb = None
    filename = None
    temp_audio_path = None
    facial_emotion = None

    # --- Handle audio upload (multipart/form-data) ---
    if 'audio' in request.files and request.files['audio'].filename != '':
        file = request.files['audio']
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: wav, mp3, mpeg.'}), 400
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        if file_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            return jsonify({'error': f'File too large. Max size is {MAX_FILE_SIZE_MB} MB.'}), 400
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        temp_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.{ext}")
        file.save(temp_audio_path)
        duration = get_audio_duration(temp_audio_path)
        if duration and duration > MAX_DURATION:
            os.remove(temp_audio_path)
            return jsonify({'error': f'Audio too long. Max duration is {MAX_DURATION} seconds.', 'duration': duration}), 400
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(temp_audio_path) as source:
                audio = recognizer.record(source)
            transcript = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            os.remove(temp_audio_path)
            return jsonify({'error': 'Could not understand audio.'}), 400
        except Exception as e:
            os.remove(temp_audio_path)
            return jsonify({'error': f'Transcription failed: {str(e)}'}), 500
        sentiment = analyze_sentiment(transcript)
        ai_response = generate_response(sentiment['label'])
        response_audio_filename = f"{uuid.uuid4()}.mp3"
        response_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], response_audio_filename)
        try:
            text_to_speech(ai_response, response_audio_path)
            audio_response = f"/download/{response_audio_filename}"
        except Exception as e:
            return jsonify({'error': f'TTS failed: {str(e)}'}), 500
        file_size_mb = round(file_length / (1024*1024), 2)
        if temp_audio_path:
            os.remove(temp_audio_path)

    # --- Handle chat (JSON) ---
    elif request.is_json:
        data = request.get_json()
        user_message = data.get('message', '')
        face_image_b64 = data.get('face_image', None)
        # Facial emotion from image (optional)
        if face_image_b64:
            try:
                header, b64data = face_image_b64.split(',') if ',' in face_image_b64 else ('', face_image_b64)
                img_bytes = BytesIO(base64.b64decode(b64data))
                img = Image.open(img_bytes).convert('RGB')
                img_np = np.array(img)
                result = DeepFace.analyze(img_path=img_np, actions=['emotion'], enforce_detection=False)
                if isinstance(result, list):
                    result = result[0]
                dominant_emotion = result['dominant_emotion']
                emotion_score = float(result['emotion'][dominant_emotion])
                facial_emotion = {'label': dominant_emotion.upper(), 'score': round(emotion_score, 2)}
            except Exception as e:
                facial_emotion = {'label': 'UNKNOWN', 'score': 0.0, 'error': str(e)}
        sentiment = analyze_sentiment(user_message)
        # --- Gemini LLM integration ---
        ai_response = None
        try:
            import google.generativeai as genai
            gemini_api_key = os.environ.get('GEMINI_API_KEY')
            if not gemini_api_key:
                ai_response = "Gemini API key is not set. Please set the GEMINI_API_KEY environment variable."
            else:
                genai.configure(api_key=gemini_api_key)
                prompt = f"You are a compassionate therapist. The user says: '{user_message}'."
                if facial_emotion:
                    prompt += f" The user's facial emotion appears to be {facial_emotion['label'].lower()} (score: {facial_emotion['score']})."
                prompt += " Respond empathetically and helpfully."
                model = genai.GenerativeModel('models/gemini-2.0-flash')
                response = model.generate_content(prompt)
                ai_response = response.text
        except Exception as e:
            ai_response = f"Sorry, I couldn't generate a response right now. Error: {str(e)}"
        # fallback if LLM fails
        if not ai_response:
            ai_response = generate_response(sentiment['label'])

    # --- Handle image upload (optional, multipart/form-data) ---
    elif 'image' in request.files and request.files['image'].filename != '':
        image_file = request.files['image']
        try:
            img = Image.open(image_file.stream).convert('RGB')
            img_np = np.array(img)
            result = DeepFace.analyze(img_path=img_np, actions=['emotion'], enforce_detection=False)
            if isinstance(result, list):
                result = result[0]
            dominant_emotion = result['dominant_emotion']
            emotion_score = float(result['emotion'][dominant_emotion])
            facial_emotion = {'label': dominant_emotion.upper(), 'score': round(emotion_score, 2)}
        except Exception as e:
            facial_emotion = {'label': 'UNKNOWN', 'score': 0.0, 'error': str(e)}

    return jsonify({
        'transcript': transcript,
        'sentiment': sentiment,
        'response': ai_response,
        'audio_response': audio_response,
        'duration': duration,
        'file_size_mb': file_size_mb,
        'filename': filename,
        'facial_emotion': facial_emotion
    })

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    """Serve the generated audio file."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Therapist/chat page
@app.route('/therapist')
def therapist():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)