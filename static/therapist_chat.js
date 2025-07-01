// Therapist Chat UI + Webcam
const webcam = document.getElementById('webcam');
const snapshot = document.getElementById('snapshot');
const webcamStatus = document.getElementById('webcamStatus');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chat-messages');
const aiAvatar = document.getElementById('aiAvatar');

// Start webcam on load
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcam.srcObject = stream;
        webcamStatus.textContent = 'Camera on';
    } catch (err) {
        webcamStatus.textContent = 'Camera access denied.';
    }
});

function captureSnapshot() {
    snapshot.getContext('2d').drawImage(webcam, 0, 0, snapshot.width, snapshot.height);
    return snapshot.toDataURL('image/png');
}

function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = sender === 'user' ? 'chat-msg user' : 'chat-msg ai';
    msgDiv.innerHTML = `<span>${text}</span>`;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show all AI responses, even if they are error messages
function showAIResponse(data) {
    if (data && typeof data.response === 'string') {
        appendMessage('ai', data.response);
    } else {
        appendMessage('ai', 'Sorry, there was an error or no response.');
    }
}

chatForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const userMsg = chatInput.value.trim();
    if (!userMsg) return;
    appendMessage('user', userMsg);
    chatInput.value = '';
    // Capture face snapshot
    const imgData = captureSnapshot();
    // Send to backend
    try {
        // Change avatar to speaking (open mouth)
        aiAvatar.src = '/static/ai_avatar_speaking.png';
        const response = await fetch('/api/therapy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMsg, face_image: imgData })
        });
        const data = await response.json();
        showAIResponse(data);
    } catch (err) {
        appendMessage('ai', 'Network error.');
    } finally {
        // After a short delay, revert avatar to idle (closed mouth)
        setTimeout(() => {
            aiAvatar.src = '/static/ai_avatar_idle.png';
        }, 1200);
    }
});
