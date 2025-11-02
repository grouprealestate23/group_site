# init_db.py
import sqlite3

# Συνδέεται με τη βάση δεδομένων (αν δεν υπάρχει, τη δημιουργεί)
connection = sqlite3.connect('database.db')

# Δημιουργεί τον πίνακα για τις συνομιλίες
with open('schema.sql', encoding='utf-8') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()
