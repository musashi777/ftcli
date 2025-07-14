import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Utilisation d'un modèle plus récent et performant
GEMINI_MODEL = "gemini-1.5-flash"

def _call_gemini_api(prompt: str) -> str:
    """Fonction helper pour appeler l'API Gemini avec gestion d'erreurs et logique de retry."""
    if not API_KEY:
        return "[ERREUR] La clé API Gemini (GEMINI_API_KEY) n'est pas configurée."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    max_retries = 3
    delay = 5 # secondes

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
                print(f"[AVERTISSEMENT] Erreur serveur Gemini ({e.response.status_code}). Nouvel essai dans {delay} secondes...")
                time.sleep(delay)
                continue
            else:
                return f"[ERREUR Gemini] Problème de connexion : {e}\n{getattr(e.response, 'text', '')}"
        except Exception as e:
            error_details = getattr(resp, "text", "Aucun détail de réponse disponible.")
            return f"[ERREUR Gemini] Erreur inattendue : {e}\n{error_details}"

    return "[ERREUR Gemini] Échec de l'appel API après plusieurs tentatives."

def extraire_sections_cv_ia(texte_cv: str) -> str:
    """Envoie le texte d'un CV à Gemini pour extraire les sections clés."""
    prompt = (
        "Lis attentivement ce texte de CV et extrais de façon structurée les sections suivantes au format Markdown :\n"
        "1. **Compétences** : Liste des compétences techniques et comportementales.\n"
        "2. **Expériences professionnelles** : Pour chaque poste, inclure l'entreprise, la fonction, les dates et les missions principales.\n"
        "3. **Formations** : Liste des diplômes, écoles et dates.\n"
        "Ne génère rien d’autre que ce plan. Sois exhaustif. Voici le texte à analyser :\n\n" + texte_cv
    )
    return _call_gemini_api(prompt)

def adapter_cv_ia(texte_cv_analyse: str, description_offre: str) -> str:
    """Adapte un CV (analyse structurée) en fonction d'une offre d'emploi."""
    prompt = f"""
Voici une analyse structurée d'un CV :
--- CV ANALYSÉ ---
{texte_cv_analyse}
--- FIN CV ANALYSÉ ---

Voici la description d'une offre d'emploi :
--- OFFRE D'EMPLOI ---
{description_offre}
--- FIN OFFRE D'EMPLOI ---

Ta mission est de générer un nouveau document texte optimisé pour cette offre. Mets en avant les compétences et expériences du CV qui correspondent le mieux aux exigences de l'offre.
Organise le résultat comme un CV classique (résumé, compétences, expériences, formation). Le ton doit être professionnel et percutant.
"""
    return _call_gemini_api(prompt)

def generer_rapport_matching_ia(analyse_cv: str, description_offre: str) -> str:
    """Génère un rapport de compatibilité entre un CV et une offre d'emploi."""
    prompt = f"""
En tant qu'expert en recrutement, analyse la compatibilité entre le profil de CV suivant et la description de l'offre d'emploi.

--- PROFIL DU CANDIDAT (CV) ---
{analyse_cv}
--- FIN PROFIL ---

--- DESCRIPTION DE L'OFFRE D'EMPLOI ---
{description_offre}
--- FIN OFFRE ---

Génère un rapport de compatibilité concis au format Markdown. Le rapport doit inclure IMPÉRATIVEMENT les sections suivantes :
1.  **📊 Score de Compatibilité** : Donne un pourcentage estimé de compatibilité et une phrase de résumé.
2.  **✅ Points Forts** : Liste les 3 à 5 compétences ou expériences les plus importantes du candidat qui correspondent parfaitement à l'offre.
3.  **❌ Points Faibles** : Liste les 2 ou 3 compétences clés requises par l'offre qui ne semblent pas présentes dans le CV.
4.  **🔑 Mots-clés à intégrer** : Suggère une liste de mots-clés de l'offre que le candidat devrait intégrer dans son CV pour passer les filtres ATS.
5.  **💬 Suggestion Stratégique** : Une courte phrase donnant un conseil au candidat pour cette postulation spécifique.
"""
    return _call_gemini_api(prompt)

def generer_lettre_motivation_ia(analyse_cv: str, description_offre: str) -> str:
    """Génère une lettre de motivation personnalisée."""
    prompt = f"""
Tu es un expert en recrutement. Rédige une lettre de motivation percutante et professionnelle en te basant sur les informations suivantes.

CONTEXTE : Le candidat suivant postule à l'offre d'emploi ci-dessous.

--- PROFIL DU CANDIDAT (CV) ---
{analyse_cv}
--- FIN PROFIL ---

--- DESCRIPTION DE L'OFFRE D'EMPLOI ---
{description_offre}
--- FIN OFFRE ---

INSTRUCTIONS :
1. Adresse la lettre de manière formelle (ex: "Madame, Monsieur,").
2. Structure la lettre en 3-4 paragraphes clairs :
   - Paragraphe 1 : Introduction, mention du poste visé et de l'entreprise.
   - Paragraphe 2 : Mettre en avant 2 ou 3 compétences/expériences CLÉS du candidat qui correspondent PARFAITEMENT aux exigences de l'offre. Utilise des exemples concrets du CV.
   - Paragraphe 3 : Montrer l'enthousiasme pour l'entreprise et le poste, et comment le candidat peut apporter de la valeur.
3. Termine par une formule de politesse classique et une proposition de rencontre.
4. Le ton doit être confiant et professionnel. La lettre ne doit PAS être une simple répétition du CV.
"""
    return _call_gemini_api(prompt)
