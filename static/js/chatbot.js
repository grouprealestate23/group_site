// static/js/chatbot.js
import { getCurrentTranslations } from './modules/i18n.js'; // Εισάγουμε τη συνάρτηση για τις μεταφράσεις

const toggleButton = document.getElementById('chatbot-toggle-button');
const chatWindow = document.querySelector('.chat-window');
const chatForm = document.getElementById('chatbot-form');
const chatInput = document.getElementById('chatbot-input');
const chatBody = document.querySelector('.chat-body');

toggleButton.addEventListener('click', () => {
    // Κλείνει οποιοδήποτε άλλο ανοιχτό widget panel
    document.querySelectorAll('.widget-panel.open').forEach(panel => {
        if (panel !== chatWindow) panel.classList.remove('open');
    });
    chatWindow.classList.toggle('open');

    // --- ΝΕΑ ΛΟΓΙΚΗ: Εμφάνιση μηνύματος καλωσορίσματος ---
    // Αν το chat ανοίγει και δεν έχει κανένα μήνυμα, πρόσθεσε το welcome message
    if (chatWindow.classList.contains('open') && chatBody.children.length === 0) {
        const translations = getCurrentTranslations();
        const welcomeMessage = translations['chatbot_welcome_message'] || "Hello! How can I help you today?";
        addMessage(welcomeMessage, 'bot');
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    chatInput.value = '';
    
    addMessage('...', 'bot', true); // "Thinking" indicator

    try {
        const response = await fetch('/ask-chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();
        updateLastBotMessage(data.reply);

    } catch (error) {
        console.error('Chatbot error:', error);
        updateLastBotMessage('Sorry, something went wrong.');
    }
});

function addMessage(text, type, isThinking = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message', type);
    if(isThinking) messageDiv.classList.add('thinking');
    messageDiv.innerHTML = text; // Χρησιμοποιούμε innerHTML για να δουλεύουν τυχόν HTML tags
    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight; // Auto-scroll to bottom
}

function updateLastBotMessage(text) {
    const thinkingMessage = chatBody.querySelector('.thinking');
    if (thinkingMessage) {
        thinkingMessage.innerHTML = text; // Χρησιμοποιούμε innerHTML
        thinkingMessage.classList.remove('thinking');
    }
}