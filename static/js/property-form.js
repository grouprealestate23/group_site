// static/js/property-form.js

document.addEventListener('DOMContentLoaded', () => {
    const mainPhoneInputField = document.querySelector("#phone-input");
    if (mainPhoneInputField) {
        window.intlTelInput(mainPhoneInputField, { initialCountry: "gr", utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js" });
    }

    const proposePriceBtn = document.getElementById('propose-price-btn');
    const priceModal = document.getElementById('price-proposal-modal');
    const contactModal = document.getElementById('proposal-contact-modal');
    const priceElement = document.querySelector('.property-sidebar .price');

    // Αν δεν υπάρχει κουμπί ή modals, σταμάτα
    if (!proposePriceBtn || !priceModal || !contactModal || !priceElement) return;

    // ΔΙΟΡΘΩΣΗ: Διαβάζουμε την τιμή από το κείμενο του element, όχι από dataset
    const priceText = priceElement.innerText.trim();
    // Καθαρίζουμε το κείμενο από το '€' και τις τελείες, και το μετατρέπουμε σε αριθμό
    const basePrice = parseFloat(priceText.replace(/€/g, '').replace(/\./g, ''));
    
    // Αν η τιμή δεν είναι αριθμός (π.χ. "Κατόπιν Επικοινωνίας"), κρύβουμε το κουμπί
    if (isNaN(basePrice) || basePrice === 0) {
        proposePriceBtn.style.display = 'none';
        return;
    }

    const proposalInput = priceModal.querySelector('#proposal-price-input');
    const errorMessage = priceModal.querySelector('#price-proposal-error');
    const continueBtn = priceModal.querySelector('#submit-proposal-btn');
    const originalPriceDisplay = priceModal.querySelector('#modal-original-price');

    const contactForm = contactModal.querySelector('#proposal-contact-form');
    const hiddenPriceInput = contactModal.querySelector('#hidden-proposed-price');
    const proposalPhoneInput = contactModal.querySelector("#proposal-phone-input");
    
    if(!proposalPhoneInput) return; // Guard clause
    const proposalIntlTel = window.intlTelInput(proposalPhoneInput, { initialCountry: "gr", utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js" });

    proposePriceBtn.addEventListener('click', () => {
        originalPriceDisplay.textContent = `€${basePrice.toLocaleString('de-DE')}`;
        priceModal.classList.add('active');
    });

    priceModal.querySelector('.modal-close').addEventListener('click', () => priceModal.classList.remove('active'));
    contactModal.querySelector('.modal-close').addEventListener('click', () => contactModal.classList.remove('active'));

    continueBtn.addEventListener('click', () => {
        const proposedPrice = parseFloat(proposalInput.value);
        const minPrice = basePrice * 0.85;

        if (isNaN(proposedPrice) || proposedPrice < minPrice) {
            errorMessage.textContent = `Η προσφορά πρέπει να είναι τουλάχιστον €${Math.ceil(minPrice).toLocaleString('de-DE')}.`;
            return;
        }

        errorMessage.textContent = '';
        hiddenPriceInput.value = proposedPrice;
        priceModal.classList.remove('active');
        contactModal.classList.add('active');
    });

    contactForm.addEventListener('submit', (e) => {
        // Παίρνουμε τον πλήρη αριθμό και τον βάζουμε σε ένα νέο hidden input
        // για να είμαστε σίγουροι ότι στέλνεται σωστά.
        const fullNumber = proposalIntlTel.getNumber();
        
        let hiddenFullPhoneInput = contactForm.querySelector('input[name="phone_full"]');
        if (!hiddenFullPhoneInput) {
             hiddenFullPhoneInput = document.createElement('input');
             hiddenFullPhoneInput.type = 'hidden';
             hiddenFullPhoneInput.name = 'phone_full';
             contactForm.appendChild(hiddenFullPhoneInput);
        }
        hiddenFullPhoneInput.value = fullNumber;
    });
});