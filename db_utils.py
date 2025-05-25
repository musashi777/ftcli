import sqlite3

def get_conn():
    return sqlite3.connect("database.db")

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS profils (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            competences TEXT,
            experiences TEXT,
            formations TEXT
        );
        """)
        conn.commit()

def insert_profil(nom, competences, experiences, formations):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO profils (nom, competences, experiences, formations) VALUES (?, ?, ?, ?)",
            (nom, competences, experiences, formations)
        )
        conn.commit()

def get_all_profils():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nom FROM profils")
        return cur.fetchall()

def get_profil_by_id(pid):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profils WHERE id=?", (pid,))
        return cur.fetchone()
