# app.py (Optimized Version)
from flask import Flask, render_template, request, jsonify, redirect
import json
import os 
import google.generativeai as genai 
from flask_sqlalchemy import SQLAlchemy 
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
import re
from werkzeug.utils import secure_filename
import time
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app) 



LANGUAGES = {
    "Bulgarian": "bg",
    "Romanian": "ro",
    "Serbian": "sr",
    "English": "en",
    "Turkish": "tu",
    "German": "de",
    "Russian": "ru"
}

def translate_texts_with_gemini(texts_to_translate, target_language):
    """
    Παίρνει ένα λεξικό με κείμενα (π.χ. {'title': '...', 'description': '...'}),
    τα μεταφράζει στη γλώσσα-στόχο και επιστρέφει το μεταφρασμένο λεξικό.
    """
    if not GEMINI_API_KEY:
        print(f"Skipping translation to {target_language} as API key is not available.")
        # Επιστρέφουμε τα αρχικά κείμενα με μια ένδειξη για να ξέρουμε ότι δεν μεταφράστηκαν
        return {key: f"[UNTRANSLATED] {value}" for key, value in texts_to_translate.items()}

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Μετατρέπουμε το λεξικό σε μορφή JSON string για το prompt
        json_input = json.dumps(texts_to_translate, ensure_ascii=False, indent=2)

        prompt = f"""
        Translate the values of the following JSON object from Greek to {target_language}.
        Do NOT translate the keys.
        Do NOT alter the JSON structure.
        Provide ONLY the translated JSON object as your response, without any introductory text like 'Here is the translation'.

        Input JSON:
        {json_input}

        Translated JSON:
        """

        response = model.generate_content(prompt)
        
        # Προσπαθούμε να καθαρίσουμε την απάντηση από τυχόν περιττό κείμενο
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        translated_json = json.loads(cleaned_response)
        return translated_json

    except Exception as e:
        print(f"ERROR during translation to {target_language}: {e}")
        # Σε περίπτωση σφάλματος, επιστρέφουμε τα αρχικά κείμενα
        return {key: f"[TRANSLATION_FAILED] {value}" for key, value in texts_to_translate.items()}


# --- Μοντέλο Βάσης ---
class Conversation(db.Model):
    __tablename__ = 'conversations' 
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String, nullable=False)
    user_question = db.Column(db.String, nullable=False)
    bot_answer = db.Column(db.String, nullable=False)
    session_id = db.Column(db.String, nullable=True)

# --- Ρύθμιση του Gemini API ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("!!! WARNING: GEMINI_API_KEY environment variable not set. Chatbot will not work.")

# --- Ρυθμίσεις Email ---
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_RECEIVER = os.environ.get('MAIL_RECEIVER', MAIL_USERNAME) 

# ===============================================
# ==            ΒΕΛΤΙΣΤΟΠΟΙΗΣΗ ΤΑΧΥΤΗΤΑΣ         ==
# ===============================================

# --- Βοηθητική Συνάρτηση για τη φόρτωση των ακινήτων ---
def load_properties_from_json():
    """Διαβάζει το JSON αρχείο από τον δίσκο."""
    try:
        with open('static/js/data/properties.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"FATAL ERROR: Could not load properties.json. {e}")
        return []

# !! ΣΗΜΑΝΤΙΚΟ: Φορτώνουμε τα ακίνητα ΜΙΑ ΦΟΡΑ κατά την εκκίνηση του app !!
ALL_PROPERTIES = load_properties_from_json()
print(f"Loaded {len(ALL_PROPERTIES)} properties into memory.")

# ===============================================
# == Route για το Chatbot                     ==
# ===============================================

@app.route('/ask-chatbot', methods=['POST'])
def ask_chatbot():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    if not GEMINI_API_KEY:
        return jsonify({'reply': 'Συγγνώμη, ο βοηθός δεν είναι διαθέσιμος αυτή τη στιγμή.'})

    bot_reply = "Sorry, I am unable to respond right now." 

    try:
        # -- ΕΠΙΚΟΙΝΩΝΙΑ ΜΕ GEMINI --
        # ΧΡΗΣΗ ΤΗΣ GLOBAL ΜΕΤΑΒΛΗΤΗΣ (ΓΙΑ ΤΑΧΥΤΗΤΑ)
        properties_data = ALL_PROPERTIES 
        context = "Here is the available property data:\n"
        for prop in properties_data:
            price_str = f"€{prop['price']:,}".replace(',', '.') if prop.get('price', 0) > 0 else 'On request'
            context += f"- Property ID: {prop['id']}, Type: {prop['type']}, Location: {prop['location']}, Price: {price_str}\n"
        
        context += "\nCompany Contact Info:\n"
        context += "Phone: +30 694 619 3307\n"
        context += "Email: info@grouprealestate.gr\n"
        context += "Address: El. Venizelou 40, Nea Vrasna, 57021\n"

        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a helpful and professional real estate assistant for "Group Real Estate" and your answers must always be in Greek.
        Your role is to answer user questions based ONLY on the information provided below.
        Be friendly, concise, and act like a real estate expert.
        If the user asks for something not in the provided data, politely state that you don't have that information.
        Never mention that you are an AI.

        --- PROVIDED DATA ---
        {context}
        --- END OF DATA ---

        User Question: "{user_message}"
        """
        
        response = model.generate_content(prompt)
        bot_reply = response.text

    except Exception as e:
        print(f"Error communicating with Gemini API: {e}")

    # -- ΑΠΟΘΗΚΕΥΣΗ ΣΤΗ ΒΑΣΗ ΔΕΔΟΜΕΝΩΝ --
    try:
        new_convo = Conversation(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_question=user_message,
            bot_answer=bot_reply
        )
        db.session.add(new_convo)
        db.session.commit()

    except Exception as e:
        db.session.rollback() 
        print(f"Error logging to database: {e}")

    return jsonify({'reply': bot_reply})
    
# --- Βοηθητική Συνάρτηση για τη φόρτωση των ακινήτων (Την αφήνουμε, αλλά αλλάζουμε όνομα) ---
# (Το όνομά της άλλαξε σε load_properties_from_json παραπάνω)
    
@app.context_processor
def inject_locations():
    # ΧΡΗΣΗ ΤΗΣ GLOBAL ΜΕΤΑΒΛΗΤΗΣ (ΓΙΑ ΤΑΧΥΤΗΤΑ)
    properties = ALL_PROPERTIES
    location_counts = {}
    location_names = {}
    for prop in properties:
       if prop.get('lat') and prop.get('lon'):
            slug = prop.get('location_slug')
            name = prop.get('location')
            if slug and name:
                location_counts[slug] = location_counts.get(slug, 0) + 1
                if slug not in location_names:
                    location_names[slug] = name

    sorted_locations = sorted(location_names.items(), key=lambda item: item[1])

    return dict(
        location_counts=location_counts,
        sorted_locations=sorted_locations
    )

@app.template_filter('formatprice')
def format_price(value):
    try:
        price = int(value)
        return f'{price:,}'.replace(',', '.')
    except (ValueError, TypeError):
        return value
    
@app.route('/')
def home():
    # all_properties = load_properties() # <-- ΠΑΛΙΟΣ ΤΡΟΠΟΣ (ΑΡΓΟΣ)
    
    # ΧΡΗΣΗ ΤΗΣ GLOBAL ΜΕΤΑΒΛΗΤΗΣ (ΓΙΑ ΤΑΧΥΤΗΤΑ)
    # 1. Βρίσκουμε τα δεδομένα για το "The Twins"
    twins_project_data = next((p for p in ALL_PROPERTIES if p['id'] == 'the-twins'), None)

    # 2. Παίρνουμε 3 δείγματα ακινήτων
    excluded_ids = ['kerdylia-monokatoikia', 'the-twins', 'kerdylia-maisonette-m1', 'kerdylia-apartment-d1', 'kerdylia-isogio', 'kerdylia-orofos']
    sample_listings_pool = [p for p in ALL_PROPERTIES if p['id'] not in excluded_ids]
    sample_listings = sample_listings_pool[:3]

    return render_template('index.html', 
                           twins_project=twins_project_data, 
                           sample_listings=sample_listings)

@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/listings')
def listings_page():
    # all_properties = load_properties() # <-- ΠΑΛΙΟΣ ΤΡΟΠΟΣ (ΑΡΓΟΣ)
    
    # ΧΡΗΣΗ ΤΗΣ GLOBAL ΜΕΤΑΒΛΗΤΗΣ (ΓΙΑ ΤΑΧΥΤΗΤΑ)
    all_properties = ALL_PROPERTIES
    
    current_filters = {
        'type': request.args.get('type', 'all'),
        'location': request.args.get('location', 'all'),
        'sort': request.args.get('sort', '')
    }

    map_data = []
    for prop in all_properties:
       if prop.get('lat') and prop.get('lon'):
            map_data.append({
                'id': prop['id'],
                'lat': prop['lat'],
                'lon': prop['lon'],
                'title_key': prop['title_key'],
                'main_image': prop['main_image'],
                'price': prop.get('price', 0),
                'area': prop.get('area', 0),
                'bedrooms': prop.get('bedrooms', 0),
                'bathrooms': prop.get('bathrooms', 0)
            })

    # filtered_properties = all_properties[:] # <-- ΠΑΛΙΟΣ ΤΡΟΠΟΣ
    filtered_properties = ALL_PROPERTIES[:] # ΧΡΗΣΗ ΤΗΣ GLOBAL ΜΕΤΑΒΛΗΤΗΣ

    if current_filters['type'] != 'all':
        filtered_properties = [p for p in filtered_properties if p['type'] == current_filters['type']]
    if current_filters['location'] != 'all':
        filtered_properties = [p for p in filtered_properties if p['location_slug'] == current_filters['location']]
    
    if current_filters['sort'] == 'price_asc':
        filtered_properties.sort(key=lambda p: p.get('price', 0) if p.get('price', 0) > 0 else float('inf'))
    elif current_filters['sort'] == 'price_desc':
        filtered_properties.sort(key=lambda p: p.get('price', 0), reverse=True)

    return render_template('listings.html', 
                           properties=filtered_properties, 
                           current_filters=current_filters,
                           map_data=map_data)

@app.route('/property/<property_id>')
def property_single_page(property_id):
    # properties = load_properties() # <-- ΠΑΛΙΟΣ ΤΡΟΠΟΣ (ΑΡΓΟΣ)
    
    # ΧΡΗΣΗ ΤΗΣ GLOBAL ΜΕΤΑΒΛΗΤΗΣ (ΓΙΑ ΤΑΧΥΤΗΤΑ)
    selected_property = next((prop for prop in ALL_PROPERTIES if prop['id'] == property_id), None)
    
    if selected_property is None:
        return "Property not found", 404
    
    map_data = []
    if selected_property.get('lat') and selected_property.get('lon'):
        map_data.append({
            'id': selected_property['id'],
            'lat': selected_property['lat'],
            'lon': selected_property['lon'],
            'title_key': selected_property['title_key'],
            'price': selected_property.get('price', 0)
        })

    return render_template(
        'property-single.html', 
        prop=selected_property, 
        map_data=map_data)

@app.route('/project-kerdylia')
def project_kerdylia_page():
    # all_properties = load_properties() # <-- ΠΑΛΙΟΣ ΤΡΟΠΟΣ (ΑΡΓΟΣ)
    
    # ΧΡΗΣΗ ΤΗΣ GLOBAL ΜΕΤΑΒΛΗΤΗΣ (ΓΙΑ ΤΑΧΥΤΗΤΑ)
    project_properties = [
        prop for prop in ALL_PROPERTIES 
        if prop.get("project_id") == "kerdylia_riviera"
    ]
    return render_template('project-kerdylia.html', properties=project_properties)

@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        # ===============================================
        # ==            ΔΙΟΡΘΩΣΗ BUG EMAIL             ==
        # ===============================================
        
        # print(f"ΝΕΟ ΜΗΝΥΜΑ ΑΠΟ: {name} ({email})") # <-- ΠΑΛΙΟΣ ΚΩΔΙΚΑΣ (ΔΕΝ ΕΣΤΕΛΝΕ)
        # print(f"ΘΕΜΑ: {subject}")
        # print(f"ΜΗΝΥΜΑ: {message}")
        
        # ΝΕΟΣ ΚΩΔΙΚΑΣ ΠΟΥ ΣΤΕΛΝΕΙ EMAIL:
        email_subject = f"Νέο Μήνυμα από Φόρμα Επικοινωνίας: {subject}"
        email_body = f"""
        Έχετε λάβει ένα νέο μήνυμα από την κεντρική φόρμα επικοινωνίας του site.

        Στοιχεία Αποστολέα:
        Όνομα: {name}
        Email: {email}

        Θέμα: {subject}

        Μήνυμα:
        {message}
        """
        send_email_logic(email_subject, email_body)
        
        # (Προαιρετικά, μπορείς να προσθέσεις ένα μήνυμα επιτυχίας με flash)
        return render_template('contact.html') 

    return render_template('contact.html')

def send_email_logic(subject, body):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("!!! MAIL_USERNAME or MAIL_PASSWORD not set in environment variables. Email not sent.")
        return False

    em = EmailMessage()
    em['From'] = MAIL_USERNAME
    em['To'] = MAIL_RECEIVER
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.starttls(context=context)
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(em)
        print("Email sent successfully!")
        return True
    except Exception as e:
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(em)
            print("Email sent successfully via GMail fallback!")
            return True
        except Exception as e_gmail:
            print(f"Error sending email via Office365: {e}")
            print(f"Error sending email via GMail: {e_gmail}")
            return False

@app.route('/send_message', methods=['POST'])
def send_message():
    property_id = request.form['property_id']
    property_title = request.form['property_title']
    name = request.form['name']
    email = request.form['email']
    phone = request.form.get('phone_full', 'N/A')
    message = request.form['message']

    subject = f"Νέο Μήνυμα Ενδιαφέροντος για το Ακίνητο: {property_title}"
    body = f"""
    Έχετε λάβει ένα νέο μήνυμα ενδιαφέροντος.
    Στοιχεία Ακινήτου:
    ID: {property_id} - Τίτλος: {property_title}
    Στοιχεία Αποστολέα:
    Όνομα: {name} - Email: {email} - Τηλέφωνο: {phone}
    Μήνυμα:
    {message}
    """
    send_email_logic(subject, body)
    return redirect(f'/property/{property_id}')

@app.route('/propose_price', methods=['POST'])
def propose_price():
    property_id = request.form['property_id']
    property_title = request.form['property_title']
    proposed_price = request.form['proposed_price']
    name = request.form['name']
    email = request.form['email']
    phone = request.form.get('phone_full', 'N/A')

    subject = f"ΝΕΑ ΠΡΟΤΑΣΗ ΤΙΜΗΣ για το ακίνητο: {property_title}"
    body = f"""
    Έχετε λάβει μια νέα πρόταση τιμής.
    Στοιχεία Ακινήτου:
    ID: {property_id} - Τίτλος: {property_title}
    Προτεινόμενη Τιμή: €{proposed_price}
    Στοιχεία Ενδιαφερόμενου:
    Όνομα: {name} - Email: {email} - Τηλέφωνο: {phone}
    """
    send_email_logic(subject, body)
    return redirect(f'/property/{property_id}')

def get_existing_data():
    """Διαβάζει τα JSON αρχεία για να πάρει υπάρχουσες τοποθεσίες και features."""
    locations = set()
    features = {}
    try:
        # Παίρνουμε τις τοποθεσίες από το properties.json
        with open('static/js/data/properties.json', 'r', encoding='utf-8') as f:
            properties = json.load(f)
            for prop in properties:
                if 'location' in prop:
                    locations.add(prop['location'])
        
        # Παίρνουμε τα features από το el.json
        with open('static/js/data/i18n/el.json', 'r', encoding='utf-8') as f:
            translations = json.load(f)
            for key, value in translations.items():
                if key.startswith('feature_'):
                    features[key] = value # π.χ. {'feature_parking': 'Ιδιωτικό Πάρκινγκ'}
    except Exception as e:
        print(f"Could not load existing data: {e}")
        
    return sorted(list(locations)), features


@app.route('/admin/edit/<string:property_id>')
def edit_page(property_id):
    """
    Φορτώνει τη φόρμα επεξεργασίας, προσυμπληρωμένη με τα δεδομένα
    του ακινήτου με το συγκεκριμένο ID.
    """
    try:
        # Φορτώνουμε τα δεδομένα όπως και στο dashboard
        properties_path = 'static/js/data/properties.json'
        el_path = 'static/js/data/i18n/el.json'

        with open(properties_path, 'r', encoding='utf-8') as f:
            properties_list = json.load(f)
        
        with open(el_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)

        # Βρίσκουμε το συγκεκριμένο ακίνητο που θέλουμε να επεξεργαστούμε
        property_to_edit = next((p for p in properties_list if p.get('id') == property_id), None)

        if not property_to_edit:
            return "Property not found", 404

        # Προσθέτουμε τον τίτλο και την περιγραφή στο αντικείμενο
        property_to_edit['title'] = translations.get(property_to_edit.get('title_key', ''), '')
        property_to_edit['description'] = translations.get(property_to_edit.get('description_key', ''), '')
        
        # Παίρνουμε τις υπάρχουσες τοποθεσίες και features για τα dropdowns/checkboxes
        locations, features = get_existing_data()

        return render_template('edit.html', 
                               property=property_to_edit,
                               existing_locations=locations,
                               existing_features=features)

    except Exception as e:
        print(f"Error loading edit page for {property_id}: {e}")
        return str(e), 500


def add_new_feature_to_all_languages(feature_key, greek_label):
    """
    Προσθέτει ένα νέο χαρακτηριστικό σε όλα τα αρχεία μετάφρασης.
    """
    if not feature_key.startswith('feature_'):
        print(f"WARNING: New feature key '{feature_key}' does not start with 'feature_'. Adding it anyway.")

    # 1. Ενημέρωση του Ελληνικού αρχείου
    try:
        el_path = 'static/js/data/i18n/el.json'
        with open(el_path, 'r+', encoding='utf-8') as f:
            translations = json.load(f)
            if feature_key in translations:
                print(f"Feature key '{feature_key}' already exists. Skipping addition.")
                return # Αν υπάρχει ήδη, δεν κάνουμε τίποτα
            translations[feature_key] = greek_label
            f.seek(0); f.truncate()
            json.dump(translations, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"ERROR updating el.json with new feature: {e}")
        return # Αν αποτύχει εδώ, δεν συνεχίζουμε

    # 2. Μετάφραση και ενημέρωση των υπολοίπων γλωσσών
    for lang_name, lang_code in LANGUAGES.items():
        print(f"--- Translating new feature for {lang_name} ---")
        
        # Μεταφράζουμε μόνο την ετικέτα
        translated_label = translate_texts_with_gemini({"label": greek_label}, lang_name).get("label", f"[TRANSLATION_FAILED] {greek_label}")
        
        lang_path = f'static/js/data/i18n/{lang_code}.json'
        try:
            with open(lang_path, 'r+', encoding='utf-8') as f:
                translations = json.load(f)
                translations[feature_key] = translated_label
                f.seek(0); f.truncate()
                json.dump(translations, f, ensure_ascii=False, indent=4)
            print(f"Updated {lang_code}.json with new feature '{feature_key}'.")
        except Exception as e:
            print(f"ERROR updating {lang_code}.json with new feature: {e}")

@app.route('/api/update_property/<string:property_id>', methods=['POST'])
def update_property(property_id):
    """
    Ενημερώνει ένα υπάρχον ακίνητο, συμπεριλαμβανομένης της πλήρους διαχείρισης εικόνων
    (προσθήκη νέων, διαγραφή παλιών, αλλαγή σειράς και κύριας εικόνας).
    """
    try:
        data = request.form.to_dict()
        newly_uploaded_files = request.files.getlist('images')

        properties_path = 'static/js/data/properties.json'
        with open(properties_path, 'r+', encoding='utf-8') as f:
            properties_list = json.load(f)
            
            prop_index = next((i for i, p in enumerate(properties_list) if p.get('id') == property_id), -1)
            
            if prop_index == -1:
                return jsonify({'message': 'Property not found to update'}), 404

            prop_to_update = properties_list[prop_index]
            original_image_paths = prop_to_update.get('images', [])

            # --- 1. Διαχείριση Εικόνων ---
            final_image_paths = []
            
            # Παίρνουμε τη λίστα με τις υπάρχουσες εικόνες που ο χρήστης κράτησε (και τη νέα τους σειρά)
            kept_existing_images_str = request.form.get('existing_images', '')
            kept_existing_images = kept_existing_images_str.split(',') if kept_existing_images_str else []
            
            # Προσθέτουμε τις νέες εικόνες
            new_image_paths = []
            property_image_dir = os.path.join('static', 'assets', 'images', 'properties', property_id)
            os.makedirs(property_image_dir, exist_ok=True)
            
            for file in newly_uploaded_files:
                if file.filename:
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(property_image_dir, filename)
                    file.save(save_path)
                    web_path = save_path.replace(os.path.sep, '/').replace('static/', '')
                    new_image_paths.append(web_path)

            # Συνθέτουμε την τελική λίστα εικόνων με βάση τη σειρά που έστειλε το frontend
            final_ordered_paths_str = request.form.get('final_image_order', '')
            final_ordered_paths = final_ordered_paths_str.split(',') if final_ordered_paths_str else []

            # Διαγραφή των παλιών εικόνων που αφαιρέθηκαν
            images_to_delete = set(original_image_paths) - set(kept_existing_images)
            for img_path in images_to_delete:
                try:
                    full_path = os.path.join('static', img_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f"Deleted image: {full_path}")
                except Exception as e:
                    print(f"Error deleting image {img_path}: {e}")

            prop_to_update['images'] = final_ordered_paths
            
            # Ενημέρωση της κύριας εικόνας
            main_image_path = request.form.get('main_image')
            if main_image_path in final_ordered_paths:
                prop_to_update['main_image'] = main_image_path
            elif final_ordered_paths:
                prop_to_update['main_image'] = final_ordered_paths[0] # Fallback στην πρώτη
            else:
                prop_to_update['main_image'] = "assets/images/placeholder.webp"

            # --- 2. Ενημέρωση των υπόλοιπων πεδίων ---
            location = data['new_location'] if data.get('location') == 'add_new_location' else data.get('location')
            prop_to_update['location'] = location
            prop_to_update['location_slug'] = re.sub(r'[^a-z0-9]+', '-', location.lower()).strip('-')
            prop_to_update['type'] = data.get('type')
            prop_to_update['price'] = int(data.get('price', 0))
            prop_to_update['area'] = int(data.get('area', 0))
            prop_to_update['bedrooms'] = int(data.get('bedrooms', 0)) if data.get('type') != 'plot' else 0
            prop_to_update['bathrooms'] = int(data.get('bathrooms', 0)) if data.get('type') != 'plot' else 0
            prop_to_update['features_keys'] = request.form.getlist('features_keys')
            
            # --- 3. Αποθήκευση στο properties.json ---
            f.seek(0)
            f.truncate()
            json.dump(properties_list, f, ensure_ascii=False, indent=4)

        # --- 4. Ενημέρωση Μεταφράσεων ---
        greek_texts = {"title": data.get('title'), "description": data.get('description')}
        el_path = 'static/js/data/i18n/el.json'
        with open(el_path, 'r+', encoding='utf-8') as f:
            translations = json.load(f)
            translations[prop_to_update['title_key']] = greek_texts['title']
            translations[prop_to_update['description_key']] = greek_texts['description']
            f.seek(0); f.truncate()
            json.dump(translations, f, ensure_ascii=False, indent=4)

        for lang_name, lang_code in LANGUAGES.items():
            translated_texts = translate_texts_with_gemini(greek_texts, lang_name)
            lang_path = f'static/js/data/i18n/{lang_code}.json'
            try:
                with open(lang_path, 'r+', encoding='utf-8') as f:
                    translations = json.load(f)
                    translations[prop_to_update['title_key']] = translated_texts.get('title')
                    translations[prop_to_update['description_key']] = translated_texts.get('description')
                    f.seek(0); f.truncate()
                    json.dump(translations, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Could not update {lang_code}.json: {e}")

        return jsonify({'message': f'Το ακίνητο "{property_id}" ενημερώθηκε με επιτυχία!'}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Παρουσιάστηκε σφάλμα κατά την ενημέρωση: {e}'}), 500

@app.route('/admin/dashboard')
def dashboard():
    """Εμφανίζει τη λίστα όλων των ακινήτων για διαχείριση."""
    try:
        properties_path = 'static/js/data/properties.json'
        el_path = 'static/js/data/i18n/el.json'

        with open(properties_path, 'r', encoding='utf-8') as f:
            properties_data = json.load(f)
        
        with open(el_path, 'r', encoding='utf-8') as f:
            translations_data = json.load(f)

        # Συνδυάζουμε τα δεδομένα για να τα στείλουμε στο template
        # Θέλουμε τον πραγματικό τίτλο, όχι μόνο το κλειδί
        properties_for_template = []
        for prop in properties_data:
            display_prop = {
                "id": prop.get('id'),
                "main_image": prop.get('main_image'),
                "type": prop.get('type', 'N/A').capitalize(),
                "location": prop.get('location', 'N/A'),
                # Παίρνουμε τον τίτλο από το el.json. Αν δεν βρεθεί, δείχνουμε το key.
                "title": translations_data.get(prop.get('title_key'), prop.get('title_key', 'No Title'))
            }
            properties_for_template.append(display_prop)
        
        # Κάνουμε ταξινόμηση ανάποδα, ώστε τα πιο πρόσφατα να είναι πρώτα
        properties_for_template.reverse()

        return render_template('dashboard.html', properties=properties_for_template)
    
    except FileNotFoundError:
        # Αν κάποιο αρχείο λείπει, δείχνουμε μια άδεια σελίδα με μήνυμα
        return render_template('dashboard.html', properties=[], error="Data files not found.")
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        return render_template('dashboard.html', properties=[], error=str(e))


@app.route('/admin')
def admin_page():
    """Σερβίρει την admin σελίδα, περνώντας της τις λίστες για τα dropdowns/checkboxes."""
    locations, features = get_existing_data()
    return render_template('admin.html', existing_locations=locations, existing_features=features)

@app.route('/api/add_property', methods=['POST'])
def add_property():
    try:
        data = request.form.to_dict()
        uploaded_files = request.files.getlist('images')
        
        # --- 1. ID Ακινήτου & Έλεγχος Μοναδικότητας ---
        new_id = data.get('id')
        if not new_id:
            return jsonify({'message': 'Το πεδίο ID είναι υποχρεωτικό.'}), 400

        properties_path = 'static/js/data/properties.json'
        with open(properties_path, 'r', encoding='utf-8') as f:
            properties_list = json.load(f)
        
        existing_ids = {p['id'] for p in properties_list}
        if new_id in existing_ids:
            return jsonify({'message': f'Το ID "{new_id}" υπάρχει ήδη. Παρακαλώ επιλέξτε ένα μοναδικό ID.'}), 409

        # --- 2. Δυναμική Προσθήκη Νέου Χαρακτηριστικού (Feature) ---
        new_feature_key = data.get('new_feature_key')
        new_feature_label = data.get('new_feature_label')
        if new_feature_key and new_feature_label:
            add_new_feature_to_all_languages(new_feature_key, new_feature_label)

        # --- 3. Δημιουργία Αντικειμένου Ακινήτου ---
        new_property = {
            'id': new_id,
            'title_key': f"prop_title_{new_id}",
            'description_key': f"prop_desc_{new_id}"
        }
        
        location = data['new_location'] if data.get('location') == 'add_new_location' else data.get('location')
        
        new_property['location'] = location
        new_property['location_slug'] = re.sub(r'[^a-z0-9]+', '-', location.lower()).strip('-')
        new_property['status'] = "for_sale"
        new_property['type'] = data.get('type')
        new_property['price'] = int(data.get('price', 0))
        new_property['area'] = int(data.get('area', 0))
        new_property['bedrooms'] = int(data.get('bedrooms', 0)) if data.get('type') != 'plot' else 0
        new_property['bathrooms'] = int(data.get('bathrooms', 0)) if data.get('type') != 'plot' else 0
        new_property['lat'] = None
        new_property['lon'] = None
        
        selected_features = request.form.getlist('features_keys')
        if new_feature_key and new_feature_key not in selected_features:
            selected_features.append(new_feature_key)
        new_property['features_keys'] = selected_features

        # --- 4. Διαχείριση Εικόνων ---
        image_paths = []
        main_image_filename = data.get('main_image_filename')
        main_image_path = "assets/images/placeholder.webp"

        if uploaded_files and uploaded_files[0].filename:
            property_image_dir = os.path.join('static', 'assets', 'images', 'properties', new_id)
            os.makedirs(property_image_dir, exist_ok=True)
            
            for file in uploaded_files:
                filename = secure_filename(file.filename)
                save_path = os.path.join(property_image_dir, filename)
                file.save(save_path)
                web_path = save_path.replace(os.path.sep, '/').replace('static/', '')
                image_paths.append(web_path)
                
                if filename == main_image_filename:
                    main_image_path = web_path
        
        if not main_image_filename and image_paths:
            main_image_path = image_paths[0]

        new_property['images'] = image_paths
        new_property['main_image'] = main_image_path

        # --- 5. Αποθήκευση στα JSON αρχεία ---
        properties_list.append(new_property)
        with open(properties_path, 'w', encoding='utf-8') as f:
            json.dump(properties_list, f, ensure_ascii=False, indent=4)
        
        greek_texts = {"title": data.get('title'), "description": data.get('description')}
        el_path = 'static/js/data/i18n/el.json'
        with open(el_path, 'r+', encoding='utf-8') as f:
            translations = json.load(f)
            translations[new_property['title_key']] = greek_texts['title']
            translations[new_property['description_key']] = greek_texts['description']
            f.seek(0); f.truncate()
            json.dump(translations, f, ensure_ascii=False, indent=4)

        for lang_name, lang_code in LANGUAGES.items():
            translated_texts = translate_texts_with_gemini(greek_texts, lang_name)
            lang_path = f'static/js/data/i18n/{lang_code}.json'
            try:
                with open(lang_path, 'r+', encoding='utf-8') as f:
                    translations = json.load(f)
                    translations[new_property['title_key']] = translated_texts.get('title')
                    translations[new_property['description_key']] = translated_texts.get('description')
                    f.seek(0); f.truncate()
                    json.dump(translations, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Could not update {lang_code}.json: {e}")

        return jsonify({'message': 'Το ακίνητο και οι μεταφράσεις αποθηκεύτηκαν!', 'new_id': new_id}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Παρουσιάστηκε ένα γενικό σφάλμα: {e}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
