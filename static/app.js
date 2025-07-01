document.getElementById('audioForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const form = e.target;
    const fileInput = document.getElementById('audioInput');
    const resultDiv = document.getElementById('result');
    const errorDiv = document.getElementById('error');
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    
    if (!fileInput.files.length) {
        errorDiv.textContent = 'Please select an audio file.';
        errorDiv.classList.remove('hidden');
        return;
    }
    const formData = new FormData();
    formData.append('audio', fileInput.files[0]);
    try {
        const response = await fetch('/api/therapist', {
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

        // Show extra details
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
    } catch (err) {
        errorDiv.textContent = 'Failed to connect to server.';
        errorDiv.classList.remove('hidden');
    }
});
