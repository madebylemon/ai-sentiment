# Sentiment Therapy App

A modern AI therapist web app where users can chat with an AI therapist via text (with webcam emotion analysis) or upload audio. The AI generates empathetic, sentiment-tailored responses using Google Gemini, considering both user text and facial emotion. The experience is seamless, interactive, and visually engaging, with a calming color palette and a modern chat UI.

## Features
- **Chat with AI Therapist:** Messenger-style chat UI, therapist avatar, and webcam emotion analysis.
- **Audio Upload:** Upload audio files for transcription, sentiment analysis, and AI response.
- **Emotion & Sentiment Analysis:** Uses DeepFace for facial emotion and TextBlob for sentiment.
- **LLM Integration:** Uses Google Gemini (Generative AI) for intelligent, empathetic responses.
- **Modern UI:** Calming color palette, responsive layout, and easy navigation.

## Setup

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd sentiment_project
```

### 2. Install dependencies
```sh
pip install -r requirements.txt
```

### 3. Set your Gemini API key
```sh
export GEMINI_API_KEY="your-gemini-api-key"
```

### 4. Run the app
```sh
python3 alo.py
```

Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Project Structure
```
sentiment_project/
├── alo.py                  # Flask backend (main entry)
├── templates/
│   ├── home.html           # Home/intro page
│   └── index.html          # Therapist chat page
├── static/
│   ├── style.css           # Main styles
│   ├── therapist_chat.js   # Chat & webcam logic
│   ├── app.js              # Audio upload logic
│   ├── ai_avatar_idle.png  # Therapist avatar (idle)
│   └── ai_avatar_speaking.png # Therapist avatar (speaking)
└── README.md
```

## Requirements
- Python 3.8+
- Flask
- flask-cors
- deepface
- pillow
- numpy
- textblob
- gtts
- speechrecognition
- google-generativeai
- pydub

## Notes
- Set your `GEMINI_API_KEY` as an environment variable before running.
- For webcam emotion analysis, allow camera access in your browser.
- Audio uploads are limited to 10MB and 30 seconds.

## License
MIT
