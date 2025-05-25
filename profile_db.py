import sqlite3
import json

DB_FILE = "ftcli_profile.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY,
        nom TEXT,
        email TEXT,
        donnees_json TEXT
    )''')
    conn.commit()
    conn.close()

def save_profile(nom, email, donnees):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    donnees_json = json.dumps(donnees, ensure_ascii=False)
    c.execute("DELETE FROM user_profile") # Un seul profil
    c.execute("INSERT INTO user_profile (nom, email, donnees_json) VALUES (?, ?, ?)", (nom, email, donnees_json))
    conn.commit()
    conn.close()

def load_profile():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT nom, email, donnees_json FROM user_profile LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        nom, email, donnees_json = row
        donnees = json.loads(donnees_json)
        return {"nom": nom, "email": email, **donnees}
    return None
