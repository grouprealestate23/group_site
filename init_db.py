# init_db.py
import os
from app import app, db

# Παίρνουμε το DATABASE_URL από το περιβάλλον
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("DATABASE_URL not set. Assuming local 'database.db'.")
else:
    # Σημαντική ρύθμιση για το Render PostgreSQL
    # Το Render δίνει URL που ξεκινά με 'postgres://' αλλά το SQLAlchemy θέλει 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Εφαρμόζουμε το URL στην εφαρμογή
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL


print("Connecting to database...")
with app.app_context():
    print("Creating database tables...")
    db.create_all() # <-- Αυτό "χτίζει" τους πίνακες με βάση τα Models (π.χ. class Conversation)
    print("Database tables created successfully.")