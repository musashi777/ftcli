import sqlite3
from datetime import datetime

def init_db():
    """Initialise la base de données SQLite."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cv_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_profil TEXT UNIQUE,
            texte_cv TEXT,
            analyse TEXT,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracked_offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offre_id TEXT UNIQUE,
            offre_intitule TEXT,
            entreprise TEXT,
            statut TEXT,
            notes TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_cv_analysis(nom_profil: str, texte_cv: str, analyse: str) -> int:
    """Sauvegarde l'analyse d'un CV dans la base de données."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO cv_analyses (nom_profil, texte_cv, analyse, created_at) VALUES (?, ?, ?, ?)",
        (nom_profil, texte_cv, analyse, created_at)
    )
    profil_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return profil_id

def get_profile_by_name(nom_profil: str) -> dict:
    """Récupère un profil par son nom."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cv_analyses WHERE nom_profil = ?", (nom_profil,))
    profile = cursor.fetchone()
    conn.close()
    if profile:
        return {"id": profile[0], "nom": profile[1], "texte": profile[2], "analyse": profile[3], "created_at": profile[4]}
    return None

def delete_profile(profil_id: int):
    """Supprime un profil de la base de données."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cv_analyses WHERE id = ?", (profil_id,))
    conn.commit()
    conn.close()

def get_all_profiles() -> list:
    """Récupère tous les profils sauvegardés."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom_profil, created_at FROM cv_analyses")
    profiles = [{"id": row[0], "nom": row[1], "created_at": row[2]} for row in cursor.fetchall()]
    conn.close()
    return profiles

def save_tracked_offer(offre_id: str, offre_intitule: str, entreprise: str, statut: str):
    """Sauvegarde une offre dans le suivi des candidatures."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO tracked_offers (offre_id, offre_intitule, entreprise, statut, created_at) VALUES (?, ?, ?, ?, ?)",
        (offre_id, offre_intitule, entreprise, statut, created_at)
    )
    conn.commit()
    conn.close()

def get_tracked_offers() -> list:
    """Récupère toutes les candidatures suivies."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, offre_id, offre_intitule, entreprise, statut, notes, created_at FROM tracked_offers")
    offers = [
        {"id": row[0], "offre_id": row[1], "offre_intitule": row[2], "entreprise": row[3], "statut": row[4], "notes": row[5], "created_at": row[6]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return offers

def update_tracked_offer(id_suivi: int, statut: str):
    """Met à jour le statut d'une candidature."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tracked_offers SET statut = ? WHERE id = ?", (statut, id_suivi))
    conn.commit()
    conn.close()

def update_tracked_offer_notes(id_suivi: int, notes: str):
    """Met à jour les notes d'une candidature."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tracked_offers SET notes = ? WHERE id = ?", (notes, id_suivi))
    conn.commit()
    conn.close()

def get_tracked_offer(id_suivi: int) -> dict:
    """Récupère une candidature par son ID."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, offre_id, offre_intitule, entreprise, statut, notes FROM tracked_offers WHERE id = ?", (id_suivi,))
    offer = cursor.fetchone()
    conn.close()
    if offer:
        return {"id": offer[0], "offre_id": offer[1], "offre_intitule": offer[2], "entreprise": offer[3], "statut": offer[4], "notes": offer[5]}
    return None

def get_profile(profil_id: int) -> dict:
    """Récupère un profil par son ID."""
    conn = sqlite3.connect("ftcli.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nom_profil, texte_cv, analyse FROM cv_analyses WHERE id = ?", (profil_id,))
    profile = cursor.fetchone()
    conn.close()
    if profile:
        return {"id": profile[0], "nom": profile[1], "texte": profile[2], "analyse": profile[3]}
    return None
