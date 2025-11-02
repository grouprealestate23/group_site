// static/js/modules/i18n.js

let translations = {};
const flagBaseUrl = '/static/assets/images/flags/'; // ΔΙΟΡΘΩΣΗ: Απόλυτη διαδρομή

const flagMap = {
    el: 'gr',
    en: 'gb',
    sr: 'rs',
    bg: 'bg',
    de: 'de',
    ro: 'ro'
};

async function setLanguage(lang) {
    try {
        // ΔΙΟΡΘΩΣΗ: Απόλυτη διαδρομή για το fetch
        const response = await fetch(`/static/js/data/i18n/${lang}.json`); 
        if (!response.ok) throw new Error(`Language file not found: ${lang}.json`);
        translations = await response.json();

        document.querySelectorAll('[data-lang-key]').forEach(elem => {
            const key = elem.getAttribute('data-lang-key');
            if (translations[key]) {
                let text = translations[key];
                // Αν υπάρχει property id, κάνε αντικατάσταση
                if (elem.dataset.propertyId) {
                    text = text.replace('%id%', elem.dataset.propertyId);
                }
                elem.textContent = text;
            }
        });
        
        document.querySelectorAll('[data-lang-placeholder]').forEach(elem => {
            const key = elem.getAttribute('data-lang-placeholder');
            if (translations[key]) elem.placeholder = translations[key];
        });

        document.documentElement.lang = lang;
        localStorage.setItem('preferredLanguage', lang);
        updateLanguageSwitcher(lang);

    } catch (error) {
        console.error('Failed to set language:', error);
    }
}

function updateLanguageSwitcher(lang) {
    const currentFlag = document.getElementById('current-flag');
    const currentLangText = document.getElementById('current-lang-text');
    const flagFileName = flagMap[lang] || 'gr';
    if (currentFlag) currentFlag.src = `${flagBaseUrl}${flagFileName}.svg`;
    if (currentLangText) currentLangText.textContent = lang.toUpperCase();
}

export async function initLanguageSwitcher() {
    const switcher = document.querySelector('.language-switcher');
    if (!switcher) return;

    switcher.addEventListener('click', (e) => {
        e.stopPropagation();
        switcher.classList.toggle('is-open');
    });

    document.querySelectorAll('.lang-dropdown a').forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const selectedLang = link.getAttribute('data-lang');
            await setLanguage(selectedLang);
            document.dispatchEvent(new CustomEvent('languageChange'));
            switcher.classList.remove('is-open');
        });
    });
    
    document.addEventListener('click', () => {
        if (switcher.classList.contains('is-open')) {
            switcher.classList.remove('is-open');
        }
    });

    const preferredLanguage = localStorage.getItem('preferredLanguage') || 'el';
    await setLanguage(preferredLanguage);
}

export function getCurrentTranslations() {
    return translations;
}