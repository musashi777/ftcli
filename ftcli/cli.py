import typer
import rich
import asyncio
import subprocess
import questionary
import re
import json
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.progress_bar import ProgressBar
from typing import Dict, List, Optional

# Imports des modules du projet
from .client import FTClient
from .gemini_utils import extraire_sections_cv_ia, adapter_cv_ia, generer_rapport_matching_ia, generer_lettre_motivation_ia
from . import database
from .agent_api import get_structured_plan
from . import exporter
from .ui_components import create_main_menu

# --- Initialisation ---
console = Console()
app = typer.Typer(help="FTCli - Votre assistant de recherche d'emploi.", add_completion=False, no_args_is_help=False)
profil_app = typer.Typer(help="Gérer les profils de CV.")
suivi_app = typer.Typer(help="Suivre les candidatures.")
app.add_typer(profil_app, name="profils")
app.add_typer(suivi_app, name="suivi")

# --- Fonctions Helpers ---
def truncate_text(text: str, max_len: int = 40) -> str:
    if text and len(text) > max_len:
        return text[: max_len - 3].strip() + "..."
    return text

def get_rapport_summary(rapport: str) -> str:
    summary_lines = []
    in_suggestion = False
    for line in rapport.splitlines():
        if "Score de Compatibilité" in line:
            summary_lines.append(line)
        elif "Suggestion Stratégique" in line:
            in_suggestion = True
            summary_lines.append("\n" + line)
        elif in_suggestion and line.strip():
            summary_lines.append(line)
    return "\n".join(summary_lines)

def get_score_from_rapport(rapport: str) -> int:
    match = re.search(r"Score de Compatibilité\s*:\s*(\d+)\s*%", rapport)
    if match:
        return int(match.group(1))
    return 0

# --- Définitions complètes des commandes ---

@app.command(name="dashboard")
def show_dashboard():
    """Affiche un tableau de bord avec les statistiques et les actions prioritaires."""
    console.print(Panel("[bold cyan]📊 Tableau de Bord FTCli[/bold cyan]", expand=False, border_style="cyan"))
    all_offers = database.get_tracked_offers()
    stats_text = Text(f"Candidatures suivies : {len(all_offers)}\n", justify="left")
    stats_text.append(f"Entretiens prévus : {len([o for o in all_offers if o['statut'] == 'Entretien prévu'])}", style="bold green")
    actions_necessaires = [o for o in all_offers if o['statut'] == 'Sauvegardée'][:3]
    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column(); table.add_column(style="magenta")
    if actions_necessaires:
        for offre in actions_necessaires:
            table.add_row(f"[dim]ID {offre['id']}[/dim]", truncate_text(offre['offre_intitule']))
    else:
        table.add_row("✨", "Aucune action en attente.")
    console.print(Panel(stats_text, title="[bold]Statistiques[/bold]", border_style="blue"))
    console.print(Panel(table, title="[bold yellow]À Traiter en Priorité[/bold yellow]", border_style="yellow"))

@app.command()
def search(mots: str = typer.Option(..., "--mots"), departement: Optional[str] = typer.Option(None, "--departement"), max_results: int = typer.Option(15, "--max-results")) -> Optional[List[Dict]]:
    """Recherche des offres d'emploi et retourne les résultats."""
    console.print(f"[bold cyan]🔍 Recherche en cours pour '{mots}'...[/bold cyan]")
    try:
        offres = asyncio.run(FTClient().search_offres(mots=mots, departement=departement, max_results=max_results))
        if not offres:
            console.print("[yellow]⚠️ Aucune offre trouvée.[/yellow]"); return None
        
        table = Table(title=f"Résultats pour '{mots}'", box=rich.box.SIMPLE_HEAVY)
        table.add_column("ID Offre", style="cyan", no_wrap=True); table.add_column("Intitulé", style="white"); table.add_column("Lieu", style="yellow"); table.add_column("Type Contrat", style="bold")
        for offre in offres:
            type_contrat = offre.get("typeContrat", "N/A")
            style = "green" if type_contrat == "CDI" else "yellow" if type_contrat == "CDD" else "dim"
            table.add_row(offre.get("id", "N/A"), truncate_text(offre.get("intitule", "N/A")), truncate_text(offre.get("lieuTravail", {}).get("libelle", "N/A")), f"[{style}]{type_contrat}[/{style}]")
        console.print(table)
        return offres
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la recherche : {e}[/bold red]"); return None

@app.command()
def view(offre_id: str = typer.Argument(...)):
    """Affiche les détails d'une offre spécifique."""
    try:
        offre = asyncio.run(FTClient().get_offre(offre_id))
        if not offre:
            console.print(f"[bold red]❌ Offre {offre_id} non trouvée.[/bold red]"); return
        title=offre.get("intitule","N/A"); entreprise=offre.get("entreprise",{}).get("nom","N/A"); lieu=offre.get("lieuTravail",{}).get("libelle","N/A"); contrat=offre.get("typeContrat","N/A"); salaire=offre.get("salaire",{}).get("libelle","N/A"); desc=offre.get("description","N/A")
        md_content = f"### Entreprise: {entreprise}\n**Lieu**: {lieu}\n**Contrat**: {contrat} | **Salaire**: {salaire}\n\n{desc}"
        console.print(Panel(Markdown(md_content), title=f"[bold]{title}[/bold]", border_style="cyan", expand=True))
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la vue de l'offre : {e}[/bold red]")

@app.command("companies")
def find_companies(job: str = typer.Option(..., "--job"), location: str = typer.Option(..., "--location")):
    """Trouve les entreprises à fort potentiel d'embauche."""
    console.print(f"\n[bold cyan]🏢 Recherche des entreprises pour '{job}' à '{location}'...[/bold cyan]")
    try:
        companies = asyncio.run(FTClient().get_potential_companies(job_label=job, location_label=location))
        if not companies:
            console.print("[yellow]⚠️ Aucune entreprise trouvée.[/yellow]"); return
        table = Table(title="Entreprises à fort potentiel d'embauche", box=rich.box.MINIMAL_HEAVY_HEAD)
        table.add_column("Entreprise", style="green", no_wrap=True); table.add_column("Ville", style="cyan"); table.add_column("Potentiel", style="magenta"); table.add_column("SIRET", style="dim")
        for company in companies:
            table.add_row(company.get("company_name", "N/A"), company.get("city", "N/A"), f"{company.get('hiring_potential', 0):.2f}", company.get("siret", "N/A"))
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la recherche d'entreprises : {e}[/bold red]")

@profil_app.command("analyser")
def profil_analyser(cv_path: str = typer.Argument(...), nom: str = typer.Option(...)):
    """Analyse un CV PDF et sauvegarde le profil."""
    try:
        result = subprocess.run(["pdftotext", cv_path, "-"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            console.print(f"[bold red]❌ Erreur pdftotext : {result.stderr}[/bold red]"); return
        texte_cv = result.stdout.strip()
        if not texte_cv:
            console.print("[bold red]❌ Le CV est vide ou illisible.[/bold red]"); return
        with console.status("[bold green]Analyse du CV par l'IA...[/bold green]"):
            analyse_ia = extraire_sections_cv_ia(texte_cv)
        profil_id = database.save_cv_analysis(nom, texte_cv, analyse_ia)
        console.print(Panel(Markdown(analyse_ia), title=f"[bold]Analyse du CV '{nom}' (ID: {profil_id})[/bold]", border_style="cyan"))
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de l'analyse : {e}[/bold red]")

@profil_app.command("lister")
def profil_lister():
    """Liste tous les profils de CV sauvegardés."""
    profils = database.get_all_profiles()
    if not profils:
        console.print("[yellow]⚠️ Aucun profil de CV sauvegardé.[/yellow]"); return
    table = Table(title="Profils de CV Sauvegardés", box=rich.box.SIMPLE)
    table.add_column("ID", style="cyan"); table.add_column("Nom du Profil"); table.add_column("Date de Création")
    for profil in profils:
        table.add_row(str(profil["id"]), profil["nom"], profil["created_at"])
    console.print(table)

@suivi_app.command("save")
def suivi_save(offre_id: str = typer.Argument(...)):
    """Sauvegarde une offre dans le suivi des candidatures."""
    try:
        offre = asyncio.run(FTClient().get_offre(offre_id))
        if not offre:
            console.print(f"[bold red]❌ Offre {offre_id} non trouvée.[/bold red]"); return
        title = offre.get("intitule", "N/A"); entreprise = offre.get("entreprise", {}).get("nom", "N/A")
        database.save_tracked_offer(offre_id, title, entreprise, "Sauvegardée")
        console.print(f"[bold green]✅ Offre '{title}' sauvegardée ![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la sauvegarde : {e}[/bold red]")

@suivi_app.command("list")
def suivi_list():
    """Affiche la liste des candidatures suivies."""
    candidatures = database.get_tracked_offers()
    if not candidatures:
        console.print("[yellow]⚠️ Aucune candidature suivie.[/yellow]"); return
    table = Table(title="Suivi des Candidatures", box=rich.box.SIMPLE)
    table.add_column("ID Suivi", style="cyan"); table.add_column("Intitulé"); table.add_column("Entreprise"); table.add_column("Statut")
    for cand in candidatures:
        table.add_row(str(cand["id"]), truncate_text(cand["offre_intitule"]), truncate_text(cand["entreprise"]), cand["statut"])
    console.print(table)
    
@suivi_app.command("update")
def suivi_update(id_suivi: Optional[int] = typer.Argument(None), statut: Optional[str] = typer.Argument(None)):
    """Met à jour le statut d'une candidature."""
    candidatures = database.get_tracked_offers()
    if not candidatures:
        console.print("[yellow]⚠️ Aucune candidature suivie.[/yellow]"); return
    if id_suivi is None:
        choices = [f"ID {c['id']} - {truncate_text(c['offre_intitule'])} ({c['statut']})" for c in candidatures]
        selected = questionary.select("Choisir une candidature :", choices=choices).ask()
        if not selected: return
        id_suivi = int(selected.split(" - ")[0].replace("ID ", ""))
    if statut is None:
        statut = questionary.text("Nouveau statut :").ask()
        if not statut: return
    database.update_tracked_offer(id_suivi, statut)
    console.print(f"[bold green]✅ Statut mis à jour.[/bold green]"); suivi_list()
    
@suivi_app.command("notes")
def suivi_notes(id_suivi: int = typer.Argument(...)):
    """Affiche et permet de modifier les notes d'une candidature."""
    candidature = database.get_tracked_offer(id_suivi)
    if not candidature:
        console.print(f"[bold red]❌ Candidature {id_suivi} non trouvée.[/bold red]"); return
    console.print(f"[bold cyan]Notes pour ID {id_suivi} :[/bold cyan]")
    console.print(Markdown(candidature.get("notes", "Aucune note.")))
    if questionary.confirm("Modifier les notes ?").ask():
        new_notes = questionary.text("Nouvelles notes :", multiline=True).ask()
        if new_notes is not None:
            database.update_tracked_offer_notes(id_suivi, new_notes)
            console.print("[bold green]✅ Notes mises à jour ![/bold green]")

@app.command()
def adapter(profil: int = typer.Option(..., "--profil"), offre: str = typer.Option(..., "--offre")):
    """Adapte un CV pour une offre spécifique."""
    console.print(f"[bold cyan]📝 Adaptation du CV pour l'offre {offre}...[/bold cyan]")
    try:
        profil_data = database.get_profile(profil)
        if not profil_data: console.print(f"[bold red]❌ Profil {profil} non trouvé.[/bold red]"); return
        offre_data = asyncio.run(FTClient().get_offre(offre))
        if not offre_data: console.print(f"[bold red]❌ Offre {offre} non trouvée.[/bold red]"); return
        with console.status("[bold green]Envoi à l'IA pour adaptation du CV...[/bold green]"):
            cv_adapte = adapter_cv_ia(profil_data["texte"], offre_data)
        console.print(Panel(Markdown(cv_adapte), title="[bold]CV Adapté[/bold]", border_style="cyan", expand=True))
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de l'adaptation du CV : {e}[/bold red]")

@app.command("lettre")
def generer_lettre(profil: int = typer.Option(..., "--profil"), offre: str = typer.Option(..., "--offre")):
    """Génère une lettre de motivation adaptée à une offre via l'IA."""
    console.print(f"\n[bold cyan]📝 Génération de la lettre de motivation pour l'offre {offre}...[/bold cyan]")
    try:
        profil_data = database.get_profile(profil)
        if not profil_data: console.print(f"[bold red]❌ Profil {profil} non trouvé.[/bold red]"); return
        offre_data = asyncio.run(FTClient().get_offre(offre))
        if not offre_data: console.print(f"[bold red]❌ Offre {offre} non trouvée.[/bold red]"); return
        with console.status("[bold green]Envoi à l'IA pour la rédaction...[/bold green]"):
            lettre = generer_lettre_motivation_ia(profil_data["analyse"], offre_data)
        console.print(Panel(Markdown(lettre), title="[bold]Lettre de Motivation Suggérée[/bold]", border_style="cyan", expand=True))
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la génération de la lettre : {e}[/bold red]")

@app.command()
def match(profil: int = typer.Option(..., "--profil"), offre: str = typer.Option(..., "--offre")) -> Optional[Dict]:
    """Analyse la compatibilité (non-interactif, pour l'agent)."""
    console.print(f"[bold cyan]📊 Analyse de compatibilité pour l'offre {offre} avec le profil {profil}...[/bold cyan]")
    try:
        profil_data = database.get_profile(profil)
        if not profil_data:
            console.print(f"[bold red]❌ Profil {profil} non trouvé.[/bold red]"); raise typer.Exit(code=1)
        with console.status("[bold green]L'IA analyse le profil et l'offre...[/bold green]"):
            offre_data = asyncio.run(FTClient().get_offre(offre))
            rapport = generer_rapport_matching_ia(profil_data["analyse"], offre_data)
        
        console.print(Panel(Markdown(rapport), title="[bold]Rapport de Compatibilité[/bold]", border_style="cyan", expand=True))
        if rapport.strip().startswith("[ERREUR"):
             raise typer.Exit(code=1)
        return {"rapport": rapport, "profil_id": profil, "offre_id": offre}
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de l'analyse : {e}[/bold red]"); raise typer.Exit(code=1)

@app.command("analyse")
def analyse_interactive(profil: int = typer.Option(..., "--profil"), offre: str = typer.Option(..., "--offre")):
    """Analyse une offre et propose un menu d'actions."""
    console.print(f"[bold cyan]📊 Analyse de compatibilité pour l'offre {offre} avec le profil {profil}...[/bold cyan]")
    try:
        profil_data = database.get_profile(profil)
        if not profil_data: console.print(f"[bold red]❌ Profil {profil} non trouvé.[/bold red]"); return
        with console.status("[bold green]Récupération de l'offre et analyse IA...[/bold green]"):
            offre_data = asyncio.run(FTClient().get_offre(offre))
            if not offre_data: console.print(f"[bold red]❌ Offre {offre} non trouvée.[/bold red]"); return
            rapport = generer_rapport_matching_ia(profil_data["analyse"], offre_data)
        
        if rapport.strip().startswith("[ERREUR"):
             console.print("[bold red]L'analyse a échoué.[/bold red]"); return
        
        score = get_score_from_rapport(rapport)
        score_color = "green" if score > 70 else "yellow" if score > 50 else "red"
        
        console.rule("[bold yellow]Résumé de l'Analyse[/bold yellow]")
        console.print("\n[bold]Score de Compatibilité :[/bold]")
        console.print(ProgressBar(total=100, completed=score), f"[{score_color}]{score}%[/{score_color}]")
        
        summary = get_rapport_summary(rapport)
        console.print(Panel(summary, border_style="green", title="Suggestion Stratégique"))

        while True:
            action_choice = questionary.select("Que voulez-vous faire maintenant ?", choices=["📖 Voir le rapport détaillé", "📝 Adapter le CV", "✉️ Rédiger la lettre", "💾 Sauvegarder l'offre", "⬅️ Terminer"]).ask()
            if not action_choice or "Terminer" in action_choice: break
            elif "détaillé" in action_choice:
                console.print(Panel(Markdown(rapport), title="[bold]Rapport de Compatibilité Complet[/bold]", border_style="cyan", expand=True))
                questionary.press_any_key_to_continue().ask()
            elif "Adapter" in action_choice: adapter(profil=profil, offre=offre); break
            elif "Rédiger" in action_choice: generer_lettre(profil=profil, offre=offre); break
            elif "Sauvegarder" in action_choice: suivi_save(offre_id=offre); break
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de l'analyse interactive : {e}[/bold red]")

@app.command(name="synthese")
def analyse_synthetique(profil: int = typer.Option(..., "--profil"), offres: List[str] = typer.Option(..., "--offre")):
    """Analyse plusieurs offres et génère un tableau de synthèse comparatif."""
    console.print(f"\n[bold cyan]📊 Lancement de l'analyse de synthèse pour le profil {profil} sur {len(offres)} offres...[/bold cyan]")
    profil_data = database.get_profile(profil)
    if not profil_data:
        console.print(f"[bold red]❌ Profil {profil} non trouvé.[/bold red]"); raise typer.Exit()

    results = []
    with console.status("[bold green]Analyse des offres en cours...[/bold green]") as status:
        for i, offre_id in enumerate(offres):
            status.update(f"Analyse de l'offre {i+1}/{len(offres)} : {offre_id}")
            try:
                offre_data = asyncio.run(FTClient().get_offre(offre_id))
                rapport = generer_rapport_matching_ia(profil_data["analyse"], offre_data)
                score = get_score_from_rapport(rapport)
                results.append({"id": offre_id, "intitule": offre_data.get("intitule", "N/A"), "score": score})
            except Exception:
                results.append({"id": offre_id, "intitule": "Erreur d'analyse", "score": 0})
    
    results.sort(key=lambda x: x["score"], reverse=True)
    table = Table(title="[bold]Synthèse de Compatibilité[/bold]", box=rich.box.HEAVY_HEAD)
    table.add_column("Score", style="magenta", justify="right"); table.add_column("ID Offre", style="cyan"); table.add_column("Intitulé")
    for result in results:
        color = "green" if result['score'] > 70 else "yellow" if result['score'] > 50 else "red"
        table.add_row(f"[{color}]{result['score']}%[/{color}]", result["id"], truncate_text(result["intitule"]))
    console.print(table)

@app.command()
def agent(goal: str = typer.Argument(...), profil_id: Optional[int] = typer.Option(None, "--profil-id", "-p"), step_by_step: bool = typer.Option(False, "--step-by-step")):
    """L'agent IA interprète un objectif, crée un plan et l'exécute."""
    console.print(f"[bold cyan]🤖 AgentFT analyse votre objectif :[/bold cyan] [i]'{goal}'[/i]")
    with console.status("[bold green]Génération du plan d'action...[/bold green]"):
        result = get_structured_plan(goal, profil_id)
    if "error" in result:
        console.print(f"[bold red]{result['error']}[/bold red]"); raise typer.Exit(code=1)
    plan = result.get("plan", [])
    if not plan:
        console.print(f"[bold red]Erreur : L'agent n'a pas pu générer de plan.[/bold red]"); raise typer.Exit(code=1)

    console.print(Panel("[bold green]✅ Voici le plan d'action proposé :[/bold green]", expand=False, border_style="green"))
    for i, action in enumerate(plan, 1):
        command_name = action.get("name", "inconnu").replace("_", " ")
        args = action.get("arguments", {})
        if command_name == "suivi save":
             args_str = args.get("offre", "<ID MANQUANT>")
        else:
            args_str = " ".join([f"--{k.replace('_', '-')} \"{v}\"" if " " in str(v) else f"--{k.replace('_', '-')} {v}" for k, v in args.items()])
        console.print(f"[cyan]{i}.[/cyan] [yellow]ftcli {command_name} {args_str}[/yellow]")
    
    if not step_by_step and not questionary.confirm("Exécuter ce plan ?").ask():
        console.print("[yellow]Plan annulé.[/yellow]"); return

    console.print("\n" + "-" * 50); console.print("[bold cyan]🚀 Lancement de l'exécution du plan...[/bold cyan]")
    context = {"ID_OFFRE_LIST": []}

    for i, action in enumerate(plan, 1):
        if step_by_step:
            if not questionary.confirm(f"Étape {i}/{len(plan)}: Prêt à exécuter '{action.get('name')}' ?", default=True).ask():
                console.print("[yellow]Plan interrompu par l'utilisateur.[/yellow]"); break
        
        console.print(f"\n[bold]Étape {i}/{len(plan)} :[/bold] [yellow]{action.get('name')}[/yellow]")
        arguments = action.get("arguments", {}).copy()
        
        for key, value in list(arguments.items()):
            if isinstance(value, str) and "<ID_A_REMPLACER" in value:
                try:
                    index = int(value.split("_")[-1][:-1]) - 1 if "_" in value else 0
                    if index < len(context["ID_OFFRE_LIST"]):
                        arguments[key] = context["ID_OFFRE_LIST"][index]
                        console.print(f"[dim]Placeholder '{value}' remplacé par l'ID: {arguments[key]}[/dim]")
                    else:
                        console.print(f"[bold red]❌ Échec : Index du placeholder hors limites.[/bold red]"); break
                except (ValueError, IndexError):
                     console.print(f"[yellow]⚠️ Placeholder mal formé, utilisation du premier ID.[/yellow]")
                     if context["ID_OFFRE_LIST"]: arguments[key] = context["ID_OFFRE_LIST"][0]
        else:
            command_list = ["ftcli"]
            command_name = action.get("name").replace("_", " ")
            command_list.extend(command_name.split())
            if command_name == "suivi save":
                id_to_save = arguments.get("offre", "ID_MANQUANT")
                command_list.append(id_to_save)
            else:
                for key, value in arguments.items():
                    command_list.append(f"--{key.replace('_', '-')}")
                    command_list.append(str(value))
            try:
                result = subprocess.run(command_list, capture_output=True, text=True, check=False)
                output = result.stdout.strip()
                if output: console.print(output)
                if result.returncode != 0:
                    console.print(f"[bold red]❌ L'étape a échoué ! Erreur :[/bold red]\n{result.stderr.strip()}"); break
                if action.get("name") == "search":
                    potential_ids = re.findall(r"^\s*([0-9A-Z]{7,})\s", output, re.MULTILINE)
                    if potential_ids:
                        context["ID_OFFRE_LIST"] = potential_ids
                        console.print(f"➡️ Contexte mis à jour : ID_OFFRE_LIST = {context['ID_OFFRE_LIST']}")
            except Exception as e:
                console.print(f"[bold red]❌ Erreur critique : {e}[/bold red]"); break
            continue
        break
    console.print("\n" + "-" * 50); console.print("[bold green]🏁 Plan d'action terminé ![/bold green]")
    
# --- Menu et Point d'Entrée ---
@app.command(name="menu")
def interactive_menu_command():
    """Lance le menu principal interactif."""
    while True:
        choice = create_main_menu()
        if not choice or "Quitter" in choice:
            console.print("[yellow]Au revoir ! 👋[/yellow]"); break
        
        if "Rechercher des offres" in choice:
            mots = questionary.text("Mots-clés de recherche :").ask()
            if mots:
                dept = questionary.text("Département (optionnel) :").ask()
                offres_trouvees = search(mots=mots, departement=dept, max_results=15)
                if offres_trouvees:
                    while True:
                        action_choice = questionary.select("Que faire avec ces résultats ?", choices=["🧐 Voir les détails", "💾 Sauvegarder une offre", "📊 Analyser une offre", "⬅️ Retourner au menu"]).ask()
                        if not action_choice or "Retourner" in action_choice: break
                        offre_id_to_action = questionary.text("Quel ID d'offre ?").ask()
                        if not offre_id_to_action: continue
                        if "Voir" in action_choice: view(offre_id_to_action)
                        elif "Sauvegarder" in action_choice: suivi_save(offre_id_to_action)
                        elif "Analyser" in action_choice:
                            profils = database.get_all_profiles()
                            if not profils:
                                console.print("[bold red]Aucun profil trouvé.[/bold red]"); continue
                            profil_choice = questionary.select("Avec quel profil ?", choices=[f"ID {p['id']} - {p['nom']}" for p in profils]).ask()
                            if not profil_choice: continue
                            profil_id = int(profil_choice.split(" - ")[0].replace("ID ", ""))
                            analyse_interactive(profil=profil_id, offre=offre_id_to_action)
        
        elif "Trouver des entreprises" in choice:
            job = questionary.text("Nom du métier :").ask()
            if job:
                location = questionary.text("Lieu :").ask()
                if location: find_companies(job=job, location=location)
        
        elif "Tableau de bord" in choice:
            show_dashboard()
        
        elif "Gérer le suivi" in choice:
            suivi_list()
            
        elif "Gérer mes profils" in choice:
            profil_lister()
        
        elif "Lancer l'agent IA" in choice:
            goal = questionary.text("Votre objectif pour l'agent :").ask()
            if goal:
                profil_id_str = questionary.text("ID du profil (optionnel) :").ask()
                profil_id = int(profil_id_str) if profil_id_str and profil_id_str.isdigit() else None
                agent(goal=goal, profil_id=profil_id)
        
        questionary.press_any_key_to_continue("\nAppuyez sur une touche pour retourner au menu...").ask()

@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Point d'entrée principal de l'application."""
    database.init_db()
    if ctx.invoked_subcommand is None:
        run_interactive_menu()

if __name__ == "__main__":
    app()
