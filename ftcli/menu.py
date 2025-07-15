import questionary
import subprocess
from .ui_components import create_main_menu

def call_command(command: list):
    """Exécute une commande ftcli et attend que l'utilisateur continue."""
    try:
        subprocess.run(command, check=True)
    except Exception as e:
        print(f"Erreur lors de l'exécution de la commande : {e}")
    
    questionary.press_any_key_to_continue("\nAppuyez sur une touche pour retourner au menu...").ask()

def run_interactive_menu():
    """Boucle principale pour le menu interactif."""
    while True:
        choice = create_main_menu()
        
        if not choice or "Quitter" in choice:
            print("Au revoir ! 👋")
            break
        
        elif "Rechercher des offres" in choice:
            mots = questionary.text("Mots-clés de recherche :").ask()
            dept = questionary.text("Département (optionnel) :").ask()
            if mots:
                cmd = ["ftcli", "search", "--mots", mots]
                if dept:
                    cmd.extend(["--departement", dept])
                call_command(cmd)
        
        elif "Trouver des entreprises" in choice:
            job = questionary.text("Nom du métier :").ask()
            location = questionary.text("Lieu (ville, département) :").ask()
            if job and location:
                call_command(["ftcli", "companies", "--job", job, "--location", location])

        elif "Tableau de bord" in choice:
            call_command(["ftcli", "dashboard"])

        elif "Gérer le suivi" in choice:
            call_command(["ftcli", "suivi", "list"])
        
        elif "Gérer mes profils" in choice:
            call_command(["ftcli", "profils", "lister"])

        elif "Lancer l'agent IA" in choice:
            goal = questionary.text("Quel est votre objectif pour l'agent ?").ask()
            if goal:
                profil_id_str = questionary.text("ID du profil à utiliser (optionnel) :").ask()
                cmd = ["ftcli", "agent", goal]
                if profil_id_str and profil_id_str.isdigit():
                    cmd.extend(["--profil-id", profil_id_str])
                call_command(cmd)
