import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def extraire_sections_cv_ia(texte_cv):
    """
    Envoie le texte d'un CV à Gemini pour extraire les sections clés :
    Compétences, Expériences professionnelles, Formations.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    prompt = (
        "Lis attentivement ce texte de CV et extrais de façon structurée les sections suivantes (en Markdown) :\n"
        "1. **Compétences** : liste des compétences techniques et comportementales\n"
        "2. **Expériences professionnelles** : entreprises, fonctions, dates, missions principales\n"
        "3. **Formations** : diplômes, écoles, dates\n"
        "Ne génère rien d’autre que ce plan, avec des sous-titres et listes à puces si nécessaire. "
        "Sois exhaustif. Voici le texte à analyser :\n\n" + texte_cv
    )
    data = {"contents": [ {"parts": [ {"text": prompt} ] } ]}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"[ERREUR Gemini] {e}\n{getattr(resp, 'text', '')}"
