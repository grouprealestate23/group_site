// static/js/accessibility.js

const a11yToggleButton = document.getElementById('a11y-toggle-button');
const a11yPanel = document.querySelector('.a11y-panel');
const darkModeToggle = document.getElementById('dark-mode-toggle');

// Συνάρτηση για εφαρμογή του dark mode
function setDarkMode(isDark) {
    if (isDark) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
    } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
    }
}

// Έλεγχος κατά τη φόρτωση της σελίδας για το αποθηκευμένο theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    setDarkMode(true);
}

// Event listener για το άνοιγμα/κλείσιμο του panel
if (a11yToggleButton && a11yPanel) {
    a11yToggleButton.addEventListener('click', () => {
        document.querySelectorAll('.widget-panel.open').forEach(panel => {
            if (panel !== a11yPanel) panel.classList.remove('open');
        });
        a11yPanel.classList.toggle('open');
    });
}

// Event listener για το κουμπί του Dark Mode
if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
        const isCurrentlyDark = document.body.classList.contains('dark-mode');
        setDarkMode(!isCurrentlyDark);
    });
}

// Βοηθητική λογική για να κλείνει το a11y panel όταν ανοίγει το chat
const chatbotToggleButton = document.getElementById('chatbot-toggle-button');
if (chatbotToggleButton && a11yPanel) {
    chatbotToggleButton.addEventListener('click', () => {
        a11yPanel.classList.remove('open');
    });
}