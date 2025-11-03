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

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app) 

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
