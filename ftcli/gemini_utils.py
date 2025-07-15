import os
import requests
import time
import json
from collections import deque
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-2.0-flash"

# --- Système de gestion de quota ---
REQUESTS_PER_MINUTE = 60
TIME_WINDOW = 60
request_timestamps = deque()

def wait_for_quota():
    """Fait une pause si nécessaire pour respecter le quota de l'API."""
    now = time.time()
    
    while request_timestamps and now - request_timestamps[0] > TIME_WINDOW:
        request_timestamps.popleft()
    
    if len(request_timestamps) >= REQUESTS_PER_MINUTE:
        time_to_wait = (request_timestamps[0] + TIME_WINDOW) - now
        if time_to_wait > 0:
            # Ce print peut être commenté si vous ne voulez pas voir les messages de pause
            # print(f"[bold yellow]⚠️ Limite de quota atteinte. Pause de {time_to_wait:.1f} secondes...[/bold yellow]")
            time.sleep(time_to_wait)
    
    request_timestamps.append(time.time())

def _call_gemini_api(prompt: str) -> str:
    """Fonction helper pour appeler l'API Gemini avec gestion d'erreurs et de quota."""
    if not API_KEY:
        return "[ERREUR] La clé API Gemini (GEMINI_API_KEY) n'est pas configurée."

    wait_for_quota()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    max_retries = 3
    delay = 5

    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=90)
            resp.raise_for_status()
            candidates = resp.json().get("candidates", [])
            if not candidates:
                return "[ERREUR Gemini] Réponse vide ou malformée de l'API."
            return candidates[0]["content"]["parts"][0]["text"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500 and attempt < max_retries - 1:
                # print(f"[AVERTISSEMENT] Erreur serveur Gemini ({e.response.status_code}). Nouvel essai...")
                time.sleep(delay)
                continue
            else:
                return f"[ERREUR Gemini] Problème de connexion : {e}\n{getattr(e.response, 'text', '')}"
        except Exception as e:
            return f"[ERREUR Gemini] Erreur inattendue : {e}"
    return "[ERREUR Gemini] Échec de l'appel API après plusieurs tentatives."

def extraire_sections_cv_ia(texte_cv: str) -> str:
    prompt = ("Lis attentivement ce texte de CV et extrais de façon structurée les sections suivantes au format Markdown :\n"
              "1. **Compétences**\n"
              "2. **Expériences professionnelles**\n"
              "3. **Formations**\n"
              "Voici le texte :\n\n" + texte_cv)
    return _call_gemini_api(prompt)

def adapter_cv_ia(texte_cv: str, description_offre: dict) -> str:
    prompt = f"""Adapte le CV suivant pour qu'il corresponde parfaitement à l'offre d'emploi. Mets en avant les compétences et expériences pertinentes.\n\n---CV---\n{texte_cv}\n\n---OFFRE---\n{json.dumps(description_offre, indent=2, ensure_ascii=False)}\n\n---CV ADAPTÉ---"""
    return _call_gemini_api(prompt)

def generer_rapport_matching_ia(analyse_cv: str, description_offre: dict) -> str:
    prompt = f"""En tant qu'expert en recrutement, analyse la compatibilité entre ce CV et cette offre. Fournis un rapport Markdown avec :
    1.  **📊 Score de Compatibilité** (en %).
    2.  **✅ Points Forts** (3-4 points clés du CV qui matchent l'offre).
    3.  **❌ Points Faibles** (2-3 compétences manquantes).
    4.  **🔑 Mots-clés à intégrer**.
    5.  **💬 Suggestion Stratégique**.\n\n---CV---\n{analyse_cv}\n\n---OFFRE---\n{json.dumps(description_offre, indent=2, ensure_ascii=False)}\n\n---RAPPORT---"""
    return _call_gemini_api(prompt)

def generer_lettre_motivation_ia(analyse_cv: str, description_offre: dict) -> str:
    prompt = f"""Rédige une lettre de motivation percutante et professionnelle basée sur ce CV et cette offre.\n\n---CV---\n{analyse_cv}\n\n---OFFRE---\n{json.dumps(description_offre, indent=2, ensure_ascii=False)}\n\n---LETTRE---"""
    return _call_gemini_api(prompt)
