// Webcam and combined audio+image logic
let webcamStream = null;
const webcam = document.getElementById('webcam');
const openWebcamBtn = document.getElementById('openWebcamBtn');
const captureBtn = document.getElementById('captureBtn');
const webcamStatus = document.getElementById('webcamStatus');
const snapshot = document.getElementById('snapshot');

openWebcamBtn.addEventListener('click', async function() {
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcam.srcObject = webcamStream;
        webcam.style.display = 'inline-block';
        captureBtn.style.display = 'inline-block';
        openWebcamBtn.style.display = 'none';
        webcamStatus.textContent = 'Camera on';
    } catch (err) {
        webcamStatus.textContent = 'Camera access denied.';
    }
});

captureBtn.addEventListener('click', function() {
    if (!webcamStream) return;
    snapshot.getContext('2d').drawImage(webcam, 0, 0, snapshot.width, snapshot.height);
    snapshot.style.display = 'inline-block';
    webcam.style.display = 'none';
    captureBtn.style.display = 'none';
    openWebcamBtn.style.display = 'inline-block';
    webcamStatus.textContent = 'Photo captured';
});

// Modify sendAudioBlob to also send image if available
async function sendAudioBlob(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    // If a snapshot is visible, send it
    if (snapshot.style.display !== 'none') {
        snapshot.toBlob(function(blob) {
            formData.append('image', blob, 'snapshot.png');
            sendCombinedForm(formData);
        }, 'image/png');
    } else {
        sendCombinedForm(formData);
    }
}

async function sendCombinedForm(formData) {
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    try {
        const response = await fetch('/api/therapy', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (!response.ok) {
            errorDiv.textContent = data.error || 'An error occurred.';
            errorDiv.classList.remove('hidden');
            return;
        }
        document.getElementById('transcript').textContent = data.transcript;
        document.getElementById('sentiment').textContent = `${data.sentiment.label} (score: ${data.sentiment.score})`;
        document.getElementById('aiResponse').textContent = data.response;
        const audio = document.getElementById('audioResponse');
        audio.src = data.audio_response;
        let details = '';
        if (data.duration !== undefined) {
            details += `<p><strong>Audio Duration:</strong> ${data.duration.toFixed(2)} sec</p>`;
        }
        if (data.file_size_mb !== undefined) {
            details += `<p><strong>File Size:</strong> ${data.file_size_mb} MB</p>`;
        }
        if (data.filename) {
            details += `<p><strong>Filename:</strong> ${data.filename}</p>`;
        }
        if (data.facial_emotion) {
            details += `<p><strong>Facial Emotion:</strong> ${data.facial_emotion.label} (score: ${data.facial_emotion.score})</p>`;
        }
        document.getElementById('extraDetails').innerHTML = details;
        resultDiv.classList.remove('hidden');
        // Animate avatar while speaking
        aiAvatar.style.filter = 'brightness(1.2) drop-shadow(0 0 10px #44624a)';
        audio.onplay = () => aiAvatar.style.filter = 'brightness(1.5) drop-shadow(0 0 20px #8ba888)';
        audio.onended = () => aiAvatar.style.filter = '';
        audio.play();
    } catch (err) {
        errorDiv.textContent = 'Failed to connect to server.';
        errorDiv.classList.remove('hidden');
    }
}

// ...existing code for audio recording and file upload...
