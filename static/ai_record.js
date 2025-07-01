// AI Avatar and Recording Logic
let mediaRecorder, audioChunks = [];
const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const recordingStatus = document.getElementById('recordingStatus');
const aiAvatar = document.getElementById('aiAvatar');

recordBtn.addEventListener('click', async function() {
    audioChunks = [];
    recordBtn.style.display = 'none';
    stopBtn.style.display = 'inline-block';
    recordingStatus.textContent = 'Recording...';
    aiAvatar.style.filter = 'brightness(1.2) drop-shadow(0 0 10px #8ba888)';
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            sendAudioBlob(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };
    } catch (err) {
        recordingStatus.textContent = 'Microphone access denied.';
        recordBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
        aiAvatar.style.filter = '';
    }
});

stopBtn.addEventListener('click', function() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        recordingStatus.textContent = 'Processing...';
        stopBtn.style.display = 'none';
        aiAvatar.style.filter = '';
    }
});

async function sendAudioBlob(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
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
            recordingStatus.textContent = '';
            recordBtn.style.display = 'inline-block';
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
        document.getElementById('extraDetails').innerHTML = details;
        resultDiv.classList.remove('hidden');
        // Animate avatar while speaking
        aiAvatar.style.filter = 'brightness(1.2) drop-shadow(0 0 10px #44624a)';
        audio.onplay = () => aiAvatar.style.filter = 'brightness(1.5) drop-shadow(0 0 20px #8ba888)';
        audio.onended = () => aiAvatar.style.filter = '';
        // Auto play response
        audio.play();
        recordingStatus.textContent = '';
        recordBtn.style.display = 'inline-block';
    } catch (err) {
        errorDiv.textContent = 'Failed to connect to server.';
        errorDiv.classList.remove('hidden');
        recordingStatus.textContent = '';
        recordBtn.style.display = 'inline-block';
    }
}

// ...existing code for file upload form...
