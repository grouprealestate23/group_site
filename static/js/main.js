// static/js/main.js

import { initLanguageSwitcher, getCurrentTranslations } from './modules/i18n.js';

// --- ΟΡΙΣΜΟΣ ΣΥΝΑΡΤΗΣΕΩΝ ---

function initMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', () => {
            mainNav.classList.toggle('is-open');
            menuToggle.classList.toggle('is-active');
        });
    }
}

function setActiveNavLink() {
    const navLinks = document.querySelectorAll('.main-nav a, .footer-column a'); // Προσθέτουμε και τα links του footer
    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
        link.classList.remove('active');
        // Εξασφαλίζουμε ότι το link έχει href πριν προσπαθήσουμε να το διαβάσουμε
        if (link.getAttribute('href')) {
            const linkPath = new URL(link.href).pathname;
            
            // Κανόνας για να γίνεται active το 'Ακίνητα' όταν είμαστε σε ένα συγκεκριμένο ακίνητο
            if (link.getAttribute('href') === '/listings' && currentPath.startsWith('/property')) {
                 link.classList.add('active');
            } else if (linkPath === currentPath) {
                // Γενικός κανόνας για όλες τις άλλες σελίδες
                link.classList.add('active');
            }
        }
    });
}


function initHeroSlider() {
    const slider = document.querySelector('.showcase-background-slider');
    if (!slider) return;

    const mediaItems = slider.querySelectorAll('.showcase-media-item');
    if (mediaItems.length <= 1) return;

    let currentIndex = 0;

    function showNext() {
        const currentItem = mediaItems[currentIndex];
        
        // Σταματάμε το βίντεο αν είναι βίντεο
        if (currentItem.tagName === 'VIDEO') {
            currentItem.pause();
            currentItem.currentTime = 0;
        }

        currentItem.classList.remove('is-active');
        
        currentIndex = (currentIndex + 1) % mediaItems.length;
        
        const nextItem = mediaItems[currentIndex];
        nextItem.classList.add('is-active');

        // Ξεκινάμε το βίντεο αν είναι βίντεο
        if (nextItem.tagName === 'VIDEO') {
            nextItem.play().catch(e => console.error("Autoplay prevented:", e));
        }
    }

    // Για τα βίντεο, προχωράμε στο επόμενο όταν τελειώσουν
    mediaItems.forEach(item => {
        if (item.tagName === 'VIDEO') {
            item.addEventListener('ended', showNext);
        }
    });
    
    // Για τις εικόνες, αλλάζουμε κάθε 5 δευτερόλεπτα
    setInterval(() => {
        if (mediaItems[currentIndex].tagName === 'IMG') {
            showNext();
        }
    }, 5000); // 5 δευτερόλεπτα για κάθε εικόνα

    // Ξεκινάμε το πρώτο media item
     if (mediaItems[0].tagName === 'VIDEO') {
        mediaItems[0].play().catch(e => console.error("Initial autoplay prevented:", e));
    }
}


function initListingsCarousels() {
    const allCards = document.querySelectorAll('.property-card');
    if (allCards.length === 0) return;

    allCards.forEach(card => {
        const imageContainer = card.querySelector('.property-card-image');
        const imageEl = card.querySelector('.property-card-main-image');
        const prevBtn = card.querySelector('.prev-button');
        const nextBtn = card.querySelector('.next-button');

        if (!imageContainer || !imageEl || !prevBtn) return;

        try {
            const imagePaths = JSON.parse(imageContainer.dataset.images);
            if (imagePaths.length <= 1) return;

            let currentIndex = 0;
            const getStaticUrl = (path) => `/static/${path}`;

            const updateImage = () => {
                imageEl.src = getStaticUrl(imagePaths[currentIndex]);
            };

            prevBtn.addEventListener('click', (e) => {
                e.preventDefault(); 
                e.stopPropagation();
                currentIndex = (currentIndex - 1 + imagePaths.length) % imagePaths.length;
                updateImage();
            });

            nextBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                currentIndex = (currentIndex + 1) % imagePaths.length;
                updateImage();
            });

        } catch(e) {
            console.error("Failed to init card carousel for card:", card, e);
        }
    });
}

function initFaqAccordion() {
    const allQuestions = document.querySelectorAll('.faq-question');
    if (allQuestions.length === 0) return;

    allQuestions.forEach(question => {
        question.addEventListener('click', () => {
            const item = question.parentElement;
            const answer = item.querySelector('.faq-answer');
            const isActive = question.classList.contains('active');

            allQuestions.forEach(q => {
                if (q !== question) {
                    q.classList.remove('active');
                    q.nextElementSibling.style.maxHeight = null;
                }
            });

            if (!isActive) {
                question.classList.add('active');
                answer.style.maxHeight = answer.scrollHeight + 'px';
            } else {
                 question.classList.remove('active');
                 answer.style.maxHeight = null;
            }
        });
    });
}

function startCounter(element) {
    const target = parseInt(element.getAttribute('data-target'));
    if (isNaN(target)) return;

    let current = 0;
    const duration = 2000; 
    const stepTime = 20;
    const totalSteps = duration / stepTime;
    const increment = target / totalSteps;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            clearInterval(timer);
            element.innerText = target + '+';
        } else {
            element.innerText = Math.ceil(current) + '+';
        }
    }, stepTime);
}

function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                if (entry.target.classList.contains('animate-on-scroll')) {
                    entry.target.classList.add('is-visible');
                }
                
                if (entry.target.classList.contains('stat-number')) {
                    startCounter(entry.target);
                }
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll, .stat-number').forEach(element => {
        observer.observe(element);
    });
}


function initPropertyCarousel() {
    const carouselContainer = document.querySelector('.carousel-container');
    if (!carouselContainer) return;
    
    try {
        const imagePaths = JSON.parse(carouselContainer.dataset.images);
        if (imagePaths.length === 0) return;

        const mainImage = carouselContainer.querySelector('.carousel-main-image');
        const prevButton = carouselContainer.querySelector('.prev-button');
        const nextButton = carouselContainer.querySelector('.next-button');
        const thumbnailsContainer = carouselContainer.querySelector('.carousel-thumbnails');
        let currentIndex = 0;
        const getStaticUrl = (path) => `/static/${path}`;

        function updateCarousel(newIndex, isInitial = false) {
            currentIndex = (newIndex + imagePaths.length) % imagePaths.length;
            
            if (!isInitial) {
                 mainImage.style.opacity = '0';
            }

            setTimeout(() => {
                mainImage.src = getStaticUrl(imagePaths[currentIndex]);
                mainImage.style.opacity = '1';
                mainImage.classList.add('loaded');
            }, isInitial ? 0 : 200);

            const allThumbs = thumbnailsContainer.querySelectorAll('.thumbnail-image');
            allThumbs.forEach((thumb, index) => {
                thumb.classList.toggle('active', index === currentIndex);
                if (index === currentIndex) {
                    thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
                }
            });
        }
        
        thumbnailsContainer.innerHTML = '';
        imagePaths.forEach((path, index) => {
            const thumb = document.createElement('img');
            thumb.src = getStaticUrl(path);
            thumb.classList.add('thumbnail-image');
            thumb.alt = `Thumbnail ${index + 1}`;
            thumb.addEventListener('click', () => updateCarousel(index));
            thumbnailsContainer.appendChild(thumb);
        });

        if (prevButton) prevButton.addEventListener('click', () => updateCarousel(currentIndex - 1));
        if (nextButton) nextButton.addEventListener('click', () => updateCarousel(currentIndex + 1));
        
        updateCarousel(0, true);

    } catch (e) {
        console.error("Failed to initialize property carousel:", e);
    }
}


function initListingsMap() {
    const mapElement = document.getElementById('listings-map');
    
       if (!mapElement || typeof L === 'undefined' || typeof mapProperties === 'undefined' || mapProperties.length === 0) {
        if (mapElement) {
             mapElement.closest('.listings-map-section').style.display = 'none';
        }
        return; 
    }

    const officeCoords = [40.708090, 23.699340];
    const map = L.map('listings-map').setView(officeCoords, 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    const markers = [];
    const translations = getCurrentTranslations();

    if (mapProperties.length > 0) {
        mapProperties.forEach(prop => {
            if (prop.lat && prop.lon) {
                const priceText = prop.price > 0 ? `€${(prop.price / 1000).toFixed(0)}K` : '...';
                const pricePinIcon = L.divIcon({ className: 'price-pin', html: priceText });
                const marker = L.marker([prop.lat, prop.lon], { icon: pricePinIcon });

                const popupContent = `
                    <div style="width:200px; font-family: 'Plus Jakarta Sans', sans-serif;">
                        <a href="/property/${prop.id}" style="text-decoration:none; color:inherit;">
                            <img src="/static/${prop.main_image}" alt="" style="width:100%; height:120px; object-fit:cover; border-radius:8px;">
                            <h5 style="margin:8px 0 5px; font-size:14px; font-weight:600;" data-lang-key="${prop.title_key}">${translations[prop.title_key] || prop.title_key}</h5>
                        </a>
                        <p style="margin:0; font-size:16px; font-weight:700; color:#e12828;">
                            ${prop.price > 0 ? '€' + prop.price.toLocaleString('de-DE') : `<span data-lang-key="price_on_request">${translations['price_on_request']}</span>`}
                        </p>
                        <div class="popup-stats" style="display:flex; gap:10px; margin-top:8px; font-size:12px; color:#555;">
                            <span><i class="bi bi-aspect-ratio"></i> ${prop.area} m²</span>
                            <span><i class="bi bi-door-open"></i> ${prop.bedrooms}</span>
                            <span><i class="bi bi-badge-wc"></i> ${prop.bathrooms}</span>
                        </div>
                    </div>
                `;
                marker.bindPopup(popupContent);
                markers.push(marker);
            } 
        });
    }

    const officeIcon = L.divIcon({ className: 'office-pin', html: '<i class="bi bi-building"></i>'});
    const officeMarker = L.marker(officeCoords, { icon: officeIcon }).addTo(map);
    const officePopupContent = `
        <div style="font-family: 'Plus Jakarta Sans', sans-serif;">
            <h5 style="margin:0 0 5px; font-weight:600;" data-lang-key="office_popup_title">${translations['office_popup_title'] || 'Our Office'}</h5>
            <p style="margin:0;">El. Venizelou 40, Nea Vrasna</p>
        </div>
    `;
    officeMarker.bindPopup(officePopupContent);
    markers.push(officeMarker);

    if (markers.length > 0) {
        const featureGroup = L.featureGroup(markers).addTo(map);
        map.fitBounds(featureGroup.getBounds().pad(0.2));
    }
}
function initLightbox() {
    const carouselContainer = document.querySelector('.carousel-container');
    const lightboxOverlay = document.getElementById('lightbox-overlay');
    if (!carouselContainer || !lightboxOverlay) return;

    const openBtn = carouselContainer.querySelector('.fullscreen-button');
    const mainCarouselImage = carouselContainer.querySelector('.carousel-main-image');
    
    const closeBtn = lightboxOverlay.querySelector('.lightbox-close');
    const lightboxImage = document.getElementById('lightbox-image');
    const nextBtn = lightboxOverlay.querySelector('.lightbox-next');
    const prevBtn = lightboxOverlay.querySelector('.lightbox-prev');
    const lightboxThumbnailsContainer = lightboxOverlay.querySelector('.lightbox-thumbnails');
    
    try {
        const imagePaths = JSON.parse(carouselContainer.dataset.images);
        if (imagePaths.length <= 1) {
            openBtn.style.display = 'none'; // Κρύβουμε το κουμπί αν υπάρχει μόνο 1 εικόνα
            return;
        }

        let currentIndex = 0;
        const getStaticUrl = (path) => `/static/${path}`;

        function showImageAtIndex(index) {
            currentIndex = (index + imagePaths.length) % imagePaths.length;
            lightboxImage.src = getStaticUrl(imagePaths[currentIndex]);

            const allThumbs = lightboxThumbnailsContainer.querySelectorAll('.lightbox-thumb-img');
            allThumbs.forEach((thumb, idx) => {
                thumb.classList.toggle('active', idx === currentIndex);
            });
        }

        function openLightbox() {
            const currentCarouselSrc = mainCarouselImage.src;
            const currentCarouselPath = new URL(currentCarouselSrc).pathname;
            const startIndex = imagePaths.findIndex(path => getStaticUrl(path) === currentCarouselPath);
            
            showImageAtIndex(startIndex >= 0 ? startIndex : 0);
            lightboxOverlay.classList.add('active');
        }

        function closeLightbox() {
            lightboxOverlay.classList.remove('active');
        }

        openBtn.addEventListener('click', openLightbox);
        closeBtn.addEventListener('click', closeLightbox);
        lightboxOverlay.addEventListener('click', (e) => {
            if (e.target === lightboxOverlay) closeLightbox();
        });
        nextBtn.addEventListener('click', () => showImageAtIndex(currentIndex + 1));
        prevBtn.addEventListener('click', () => showImageAtIndex(currentIndex - 1));

        document.addEventListener('keydown', (e) => {
            if (lightboxOverlay.classList.contains('active')) {
                if (e.key === 'Escape') closeLightbox();
                if (e.key === 'ArrowRight') nextBtn.click();
                if (e.key === 'ArrowLeft') prevBtn.click();
            }
        });

        lightboxThumbnailsContainer.innerHTML = ''; // Καθαρίζουμε για να μην διπλοεγγραφούν
        imagePaths.forEach((path, index) => {
            const thumb = document.createElement('img');
            thumb.src = getStaticUrl(path);
            thumb.classList.add('lightbox-thumb-img');
            thumb.addEventListener('click', () => showImageAtIndex(index));
            lightboxThumbnailsContainer.appendChild(thumb);
        });

    } catch(e) { console.error("Lightbox init failed", e); }
}


// --- ΚΕΝΤΡΙΚΟΣ ΕΓΚΕΦΑΛΟΣ ---
document.addEventListener('DOMContentLoaded', async () => {
    await initLanguageSwitcher(); // Πρέπει να τρέξει πρώτα για να έχουμε τις μεταφράσεις
    
    initMobileMenu();
    setActiveNavLink();
    initScrollAnimations();
    initHeroSlider();
    initFaqAccordion();
    initListingsCarousels(); // Τρέχει σε όλες τις σελίδες που έχουν property-card

    // Ειδικές συναρτήσεις ανά σελίδα
    if (document.querySelector('.property-single-section')) {
        initPropertyCarousel();
        initLightbox();
    }
    
    if (document.getElementById('listings-map')) {
        initListingsMap();
    }
});