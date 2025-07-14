import os
import requests
import json
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

def get_structured_plan(user_goal: str, profil_id: int = None) -> Dict[str, List[Dict]]:
    """
    Génère un plan d'action structuré (liste d'objets JSON) pour un objectif complexe.
    Args:
        user_goal (str): L'objectif de l'utilisateur, par exemple "Trouver 5 offres et analyser leur compatibilité".
        profil_id (int, optional): L'ID du profil de CV à utiliser pour les actions comme 'match' ou 'adapter'.
    Returns:
        Dict[str, List[Dict]]: Un dictionnaire avec une clé 'plan' contenant une liste d'actions.
    """
    if not DEEPSEEK_API_KEY:
        return {"error": "Clé API DeepSeek non configurée dans votre fichier .env."}

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}

    
    # NOUVEAU PROMPT (beaucoup plus précis)
    system_prompt = (
        'Tu es "AgentFT", un agent IA expert qui planifie des actions pour un outil en ligne de commande `ftcli`.\n'
        'Ta seule et unique réponse doit être un objet JSON contenant une clé "plan", qui est un tableau d\'actions à exécuter dans l\'ordre.\n'
        'Chaque action est un objet avec un "name" et un dictionnaire "arguments".\n\n'
        'RÈGLE D\'OR POUR LES LIEUX : Pour les grandes villes françaises (Marseille, Lyon, Paris...), utilise TOUJOURS `--departement`.\n'
        'RÈGLE D\'OR POUR LES ARGUMENTS : Dans le JSON, les noms d\'arguments doivent utiliser des underscores (snake_case), comme dans les fonctions Python.\n'
        'IMPORTANT: Si une action dépend du résultat d\'une recherche, utilise un placeholder indexé comme `<ID_A_REMPLACER_1>` pour la première offre, `<ID_A_REMPLACER_2>` pour la seconde, etc.\n\n'
        'Voici les fonctions que tu peux utiliser et leurs arguments exacts:\n'
        ' - `search(mots: str, departement: str = None, max_results: int = 5)`\n'
        ' - `view(offre: str)`\n'
        ' - `match(offre: str, profil: int)`\n'
        ' - `adapter(offre: str, profil: int)`\n'
        ' - `suivi save(offre: str)`\n\n'
        'Exemple de sortie attendue pour une demande complexe:\n'
        '{\n'
        '  "plan": [\n'
        '    {\n'
        '      "name": "search",\n'
        '      "arguments": {"mots": "administrateur réseau", "departement": "13", "max_results": 3}\n'
        '    },\n'
        '    {\n'
        '      "name": "match",\n'
        '      "arguments": {"offre": "<ID_A_REMPLACER_1>", "profil": 2}\n'
        '    }\n'
        '  ]\n'
        '}'
    )
    

    # Ajouter l'ID du profil au prompt si fourni
    user_prompt = user_goal
    if profil_id is not None:
        user_prompt += f" Utilise l'ID de profil {profil_id} pour les actions nécessitant un profil."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    data = {
        "model": "deepseek-coder",
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 2048,  # Augmenté pour gérer des plans complexes
        "response_format": {"type": "json_object"}
    }

    max_retries = 3
    delay = 5  # secondes
    for attempt in range(max_retries):
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data), timeout=30)
            response.raise_for_status()
            response_text = response.json()["choices"][0]["message"]["content"]

            # Validation robuste de la réponse
            plan_data = json.loads(response_text)
            if not isinstance(plan_data, dict) or "plan" not in plan_data or not isinstance(plan_data["plan"], list):
                return {"error": f"Structure JSON incorrecte. Reçu : {response_text}"}

            # Vérifier que les actions utilisent des paramètres valides
            for action in plan_data["plan"]:
                if not isinstance(action, dict) or "name" not in action or "arguments" not in action:
                    return {"error": f"Action mal formée : {action}"}
                if action["name"] == "search" and "limit" in action.get("arguments", {}):
                    return {"error": "L'option '--limit' est incorrecte. Utilise '--max-results'."}
                if action["name"] in ["match", "adapter"] and not isinstance(action["arguments"].get("profil"), int):
                    return {"error": f"ID de profil invalide pour {action['name']}. Un entier est requis."}

            return {"plan": plan_data["plan"]}

        except (requests.exceptions.RequestException, IndexError, KeyError, json.JSONDecodeError) as e:
            error_details = response.text if 'response' in locals() else 'Pas de réponse du serveur.'
            if attempt < max_retries - 1:
                time.sleep(delay)
                continue
            return {"error": f"Échec de l'appel API DeepSeek après {max_retries} tentatives. Détail : {e}. Réponse : {error_details}"}

    return {"error": "Échec de l'appel API DeepSeek après plusieurs tentatives."}
