import typer
import rich
import asyncio
import subprocess
import questionary
import re
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.progress_bar import ProgressBar
from typing import Dict, List, Optional
from .client import FTClient
from .gemini_utils import extraire_sections_cv_ia, adapter_cv_ia, generer_rapport_matching_ia, generer_lettre_motivation_ia
from . import database
from .agent_api import get_structured_plan
from . import exporter

# --- Initialisation ---
console = Console()
app = typer.Typer(help="FTCli - Votre assistant de recherche d'emploi en ligne de commande.")
profil_app = typer.Typer(help="Gérer les profils de CV analysés.")
suivi_app = typer.Typer(help="Suivre vos candidatures.")
app.add_typer(profil_app, name="profils")
app.add_typer(suivi_app, name="suivi")

# --- Fonctions Helpers ---
def truncate_text(text: str, max_len: int = 40) -> str:
    """Tronque le texte intelligemment pour l'affichage dans les tableaux."""
    if text and len(text) > max_len:
        return text[: max_len - 3].strip() + "..."
    return text

# --- Commandes Principales ---
@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Initialise la base de données et affiche le tableau de bord si aucune commande n'est passée."""
    database.init_db()
    if ctx.invoked_subcommand is None:
        show_dashboard()

@app.command(name="dashboard")
def show_dashboard():
    """Affiche un tableau de bord avec les statistiques et les actions prioritaires."""
    console.print(Panel("[bold cyan]📊 Tableau de Bord FTCli[/bold cyan]", expand=False, border_style="cyan"))
    all_offers = database.get_tracked_offers()
    stats_text = Text(f"Candidatures suivies : {len(all_offers)}\n", justify="left")
    stats_text.append(
        f"Entretiens prévus : {len([o for o in all_offers if o['statut'] == 'Entretien prévu'])}",
        style="bold green",
    )
    actions_necessaires = [o for o in all_offers if o['statut'] == 'Sauvegardée'][:3]
    actions_table = Table(box=None, show_header=False, padding=(0, 1))
    actions_table.add_column()
    actions_table.add_column(style="magenta")
    if actions_necessaires:
        for offre in actions_necessaires:
            actions_table.add_row(f"[dim]ID {offre['id']}[/dim]", truncate_text(offre['offre_intitule']))
    else:
        actions_table.add_row("✨", "Aucune action en attente, bravo !")
    console.print(Panel(stats_text, title="[bold]Statistiques[/bold]", border_style="blue"))
    console.print(Panel(actions_table, title="[bold yellow]⚠️ À Traiter en Priorité[/bold yellow]", border_style="yellow"))

@app.command()
def search(
    mots: str = typer.Option(None, "--mots", help="Mots-clés pour la recherche"),
    departement: str = typer.Option(None, "--departement", help="Numéro du département (ex: 75)"),
    commune: str = typer.Option(None, "--commune", help="Code INSEE de la commune"),
    max_results: int = typer.Option(15, "--max-results", help="Nombre maximum de résultats"),
    type_contrat: str = typer.Option(None, "--type-contrat", help="Code du type de contrat (CDI, CDD, MIS...)"),
    export: Optional[str] = typer.Option(None, "--export", help="Exporter les résultats (formats: txt, html)"),
):
    """Recherche des offres d'emploi via l'API France Travail."""
    search_terms = []
    if mots:
        search_terms.append(f"'{mots}'")
    if type_contrat:
        search_terms.append(f"Contrat: {type_contrat}")

    console.print(f"[bold cyan]🔍 Recherche en cours pour :[/bold cyan] [i]{' '.join(search_terms)}[/i]...")
    
    try:
        async def run_search():
            async with FTClient() as ft:
                offres = await ft.search_offres(
                    mots=mots, 
                    departement=departement, 
                    commune=commune, 
                    typeContrat=type_contrat
                )
            return offres[:max_results] if offres else []

        offres = asyncio.run(run_search())
        if not offres:
            console.print("[yellow]⚠️ Aucune offre trouvée.[/yellow]")
            return

        table = Table(title=f"Résultats de recherche pour {' '.join(search_terms)}", box=rich.box.SIMPLE)
        table.add_column("ID Offre", style="cyan")
        table.add_column("Intitulé")
        table.add_column("Lieu")
        table.add_column("Type Contrat")

        for offre in offres:
            table.add_row(
                offre.get("id", "N/A"),
                truncate_text(offre.get("intitule", "N/A")),
                truncate_text(offre.get("lieuTravail", {}).get("libelle", "N/A")),
                offre.get("typeContrat", "N/A"),
            )
        console.print(table)
        console.print("\nPour interagir : `ftcli view <ID_OFFRE>` ou `ftcli suivi save <ID_OFFRE>`")

        if export:
            if export not in ["txt", "html"]:
                console.print(f"[bold red]Format d'export '{export}' non valide. Choisissez 'txt' ou 'html'.[/bold red]")
                return
            
            safe_mots = "".join(c if c.isalnum() else "_" for c in mots) if mots else "recherche"
            filename = f"recherche_{safe_mots}.{export}"
            
            console.print(f"\n[green]📦 Exportation de {len(offres)} résultats vers [bold]{filename}[/bold]...[/green]")
            
            if export == "txt":
                exporter.export_to_txt(offres, filename)
            elif export == "html":
                exporter.export_to_html(offres, filename)
            
            console.print(f"[bold green]✅ Exportation terminée ![/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la recherche : {e}[/bold red]")

@app.command()
def view(offre_id: str = typer.Argument(..., help="ID de l'offre à consulter")):
    """Affiche les détails d'une offre spécifique."""
    try:
        async def get_offre_details():
            async with FTClient() as ft:
                return await ft.get_offre(offre_id)

        offre = asyncio.run(get_offre_details())
        if not offre:
            console.print(f"[bold red]❌ Offre {offre_id} non trouvée.[/bold red]")
            return

        title = offre.get("intitule", "Offre sans titre")
        entreprise = offre.get("entreprise", {}).get("nom", "N/A")
        lieu = offre.get("lieuTravail", {}).get("libelle", "N/A")
        contrat = offre.get("typeContrat", "N/A")
        salaire = offre.get("salaire", {}).get("libelle", "N/A")
        description = offre.get("description", "Aucune description disponible.")

        md_content = (
            f"\n\n### Entreprise: {entreprise}\n"
            f"**Lieu**: {lieu}\n"
            f"**Contrat**: {contrat} | **Salaire**: {salaire}\n\n"
            f"{description}"
        )
        console.print(Panel(Markdown(md_content), title=f"[bold]{title}[/bold]", border_style="cyan"))

        if questionary.confirm("Sauvegarder cette offre dans votre suivi ?").ask():
            database.save_tracked_offer(offre_id, title, entreprise, "Sauvegardée")
            console.print(f"[bold green]✅ Offre '{title}' sauvegardée ![/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la récupération de l'offre : {e}[/bold red]")

@app.command("companies")
def find_companies(
    job: str = typer.Option(..., "--job", help="Le nom du métier recherché (ex: 'boulanger')"),
    location: str = typer.Option(..., "--location", help="Le nom de la ville ou du département"),
):
    """Trouve les entreprises à fort potentiel d'embauche."""
    console.print(f"\n[bold cyan]🏢 Recherche des entreprises pour '{job}' à '{location}'...[/bold cyan]")
    
    try:
        async def run_fetch():
            async with FTClient() as ft:
                return await ft.get_potential_companies(job_label=job, location_label=location)
        
        companies = asyncio.run(run_fetch())
        if not companies:
            console.print("[yellow]⚠️ Aucune entreprise à fort potentiel trouvée pour ces critères.[/yellow]")
            return
            
        table = Table(title="Entreprises à fort potentiel d'embauche", box=rich.box.MINIMAL_HEAVY_HEAD)
        table.add_column("Entreprise", style="green", no_wrap=True)
        table.add_column("Ville", style="cyan")
        table.add_column("Potentiel", style="magenta")
        table.add_column("SIRET", style="dim")
        
        for company in companies:
            potential_str = f"{company.get('hiring_potential', 0):.2f}"
            table.add_row(
                company.get("company_name", "N/A"),
                company.get("city", "N/A"),
                potential_str,
                company.get("siret", "N/A")
            )
        console.print(table)

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la recherche d'entreprises : {e}[/bold red]")

@app.command()
def agent(
    goal: str = typer.Argument(..., help="Votre objectif. L'agent planifiera et exécutera les actions."),
    profil_id: int = typer.Option(None, "--profil-id", "-p", help="ID du profil à utiliser pour les analyses."),
):
    """L'agent IA interprète votre objectif, crée un plan et l'exécute après confirmation."""
    console.print(f"[bold cyan]🤖 AgentFT analyse votre objectif :[/bold cyan] [i]'{goal}'[/i]")

    with console.status("[bold green]Génération du plan d'action...[/bold green]", spinner="dots"):
        result = get_structured_plan(goal, profil_id)

    if "error" in result:
        console.print(f"[bold red]{result['error']}[/bold red]")
        raise typer.Exit(1)

    plan = result.get("plan", [])
    if not isinstance(plan, list) or not plan:
        console.print(f"[bold red]Erreur : L'agent n'a pas pu générer de plan valide.[/bold red]")
        raise typer.Exit(1)

    console.print(Panel("[bold green]✅ Voici le plan d'action proposé :[/bold green]", expand=False, border_style="green"))
    for i, action in enumerate(plan, 1):
        command_name = action.get("name", "inconnu").replace("_", " ")
        args_display_list = []
        for k, v in action.get("arguments", {}).items():
            args_display_list.append(f'--{k.replace("_", "-")} "{v}"' if isinstance(v, str) and " " in v else f'--{k.replace("_", "-")} {v}')
        args_display = " ".join(args_display_list)
        console.print(f"[cyan]{i}.[/cyan] [yellow]ftcli {command_name} {args_display}[/yellow]")


    if not questionary.confirm("Exécuter ce plan ?").ask():
        console.print("[yellow]Plan annulé.[/yellow]")
        return

    console.print("\n" + "-" * 50)
    console.print("[bold cyan]🚀 Lancement de l'exécution du plan...[/bold cyan]")

    context = {"ID_OFFRE_LIST": []}

    for i, action in enumerate(plan, 1):
        console.print(f"\n[bold]Étape {i}/{len(plan)} :[/bold] [yellow]{action.get('name')}[/yellow]")

        arguments = action.get("arguments", {}).copy()
        
        placeholder = arguments.get("offre", "")
        if "<ID_A_REMPLACER" in str(placeholder):
            index = 0
            if "_" in placeholder:
                try:
                    index_str = placeholder.split("_")[-1][:-1]
                    index = int(index_str) - 1
                except (ValueError, IndexError):
                    console.print(f"[yellow]⚠️ Placeholder '{placeholder}' mal formé, utilisation de la première offre par défaut.[/yellow]")
                    index = 0

            if index < len(context["ID_OFFRE_LIST"]):
                arguments["offre"] = context["ID_OFFRE_LIST"][index]
                console.print(f"[dim]Placeholder remplacé par l'ID: {arguments['offre']}[/dim]")
            else:
                console.print(f"[bold red]❌ Échec : Impossible de trouver l'offre à l'index {index+1}. Liste d'ID disponibles : {len(context['ID_OFFRE_LIST'])}[/bold red]")
                break
        
        command_name = action.get("name", "").replace("_", " ")
        command_list = ["ftcli", *command_name.split()]
        
        # CORRECTION : Logique spéciale pour la commande 'suivi save'
        if command_name == "suivi save":
            # On ignore les arguments de l'IA et on construit la commande correctement
            offre_id_to_save = arguments.get("offre")
            if not offre_id_to_save: # Fallback si la clé est différente
                for val in arguments.values():
                    if isinstance(val, str) and len(val) > 5: # Heuristique pour trouver un ID d'offre
                        offre_id_to_save = val
                        break
            
            if offre_id_to_save:
                command_list = ["ftcli", "suivi", "save", offre_id_to_save]
            else:
                console.print(f"[bold red]❌ L'agent n'a pas réussi à spécifier un ID d'offre pour 'suivi save'.[/bold red]")
                break
        else:
             for key, value in arguments.items():
                command_list.append(f"--{key.replace('_', '-')}")
                command_list.append(str(value))

        try:
            with console.status(f"[bold green]Exécution de `{' '.join(command_list)}`...[/bold green]", spinner="dots"):
                result = subprocess.run(command_list, capture_output=True, text=True, check=False)

            output = result.stdout
            console.print(output)

            if result.returncode != 0:
                console.print(f"[bold red]❌ L'étape a échoué ! Erreur :[/bold red]\n{result.stderr}")
                break

            if action.get("name") == "search":
                context["ID_OFFRE_LIST"] = []
                potential_ids = re.findall(r"^\s*([A-Z0-9]{7})\s", output, re.MULTILINE)
                if potential_ids:
                    context["ID_OFFRE_LIST"] = potential_ids
                    console.print(f"➡️ Contexte mis à jour : ID_OFFRE_LIST = {context['ID_OFFRE_LIST']}")
                else:
                    console.print("[yellow]⚠️ Aucun ID d'offre trouvé dans la sortie de recherche.[/yellow]")

        except Exception as e:
            console.print(f"[bold red]❌ Erreur critique : {e}[/bold red]")
            break

    console.print("\n" + "-" * 50)
    console.print("[bold green]🏁 Plan d'action terminé ![/bold green]")


@profil_app.command("analyser")
def profil_analyser(
    cv_path: str = typer.Argument(..., help="Chemin vers le fichier PDF du CV"),
    nom: str = typer.Option(..., "--nom", help="Nom du profil à sauvegarder"),
):
    """Analyse un CV PDF et sauvegarde le profil."""
    try:
        existing_profile = database.get_profile_by_name(nom)
        if existing_profile:
            console.print(f"[yellow]⚠️ Le profil '{nom}' existe déjà (ID: {existing_profile['id']}).[/yellow]")
            if questionary.confirm("Remplacer le profil existant ?").ask():
                database.delete_profile(existing_profile['id'])
            else:
                new_nom = questionary.text("Entrez un nouveau nom pour le profil :").ask()
                if not new_nom:
                    console.print("[yellow]Aucun nouveau nom fourni. Annulation.[/yellow]")
                    return
                nom = new_nom

        result = subprocess.run(["pdftotext", cv_path, "-"], capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"[bold red]❌ Erreur lors de l'extraction du texte : {result.stderr}[/bold red]")
            return
        texte_cv = result.stdout
        if not texte_cv.strip():
            console.print("[bold red]❌ Le CV est vide ou illisible.[/bold red]")
            return

        console.print("[bold cyan]📄 Analyse du CV en cours...[/bold cyan]")
        with console.status("[bold green]Envoi à l'IA Gemini...[/bold green]", spinner="dots"):
            analyse_ia = extraire_sections_cv_ia(texte_cv)

        profil_id = database.save_cv_analysis(nom, texte_cv, analyse_ia)
        console.print(Panel(Markdown(analyse_ia), title=f"[bold]Analyse du CV '{nom}' (ID: {profil_id})[/bold]", border_style="cyan"))
        console.print(f"[bold green]✅ Profil sauvegardé avec l'ID {profil_id}.[/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de l'analyse du CV : {e}[/bold red]")

@profil_app.command("lister")
def profil_lister():
    """Liste tous les profils de CV sauvegardés."""
    profils = database.get_all_profiles()
    if not profils:
        console.print("[yellow]⚠️ Aucun profil trouvé.[/yellow]")
        return

    table = Table(title="Profils de CV Sauvegardés", box=rich.box.SIMPLE)
    table.add_column("ID", style="cyan")
    table.add_column("Nom du Profil")
    table.add_column("Date")
    for profil in profils:
        table.add_row(str( profil["id"]), profil["nom"], profil["created_at"])
    console.print(table)

@suivi_app.command("save")
def suivi_save(offre_id: str = typer.Argument(..., help="ID de l'offre à sauvegarder")):
    """Sauvegarde une offre dans le suivi des candidatures."""
    try:
        async def get_offre_details():
            async with FTClient() as ft:
                return await ft.get_offre(offre_id)

        offre = asyncio.run(get_offre_details())
        if not offre:
            console.print(f"[bold red]❌ Offre {offre_id} non trouvée.[/bold red]")
            return

        title = offre.get("intitule", "Offre sans titre")
        entreprise = offre.get("entreprise", {}).get("nom", "N/A")
        database.save_tracked_offer(offre_id, title, entreprise, "Sauvegardée")
        console.print(f"[bold green]✅ Offre '{title}' sauvegardée ![/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la sauvegarde : {e}[/bold red]")

@suivi_app.command("list")
def suivi_list():
    """Liste toutes les candidatures suivies."""
    candidatures = database.get_tracked_offers()
    if not candidatures:
        console.print("[yellow]⚠️ Aucune candidature suivie.[/yellow]")
        return

    table = Table(title="Suivi des Candidatures", box=rich.box.SIMPLE)
    table.add_column("ID Suivi", style="cyan")
    table.add_column("Intitulé")
    table.add_column("Entreprise")
    table.add_column("Statut")
    for candidature in candidatures:
        table.add_row(
            str(candidature["id"]),
            truncate_text(candidature["offre_intitule"]),
            truncate_text(candidature["entreprise"]),
            candidature["statut"],
        )
    console.print(table)
    console.print("\nPour agir : `ftcli suivi update`, `ftcli suivi notes <ID_SUIVI>`")

@suivi_app.command("update")
def suivi_update(
    id_suivi: Optional[int] = typer.Argument(None, help="ID de la candidature à mettre à jour"),
    statut: Optional[str] = typer.Argument(None, help="Nouveau statut de la candidature"),
):
    """Met à jour le statut d'une candidature (interactif si aucun ID/statut fourni)."""
    candidatures = database.get_tracked_offers()
    if not candidatures:
        console.print("[yellow]⚠️ Aucune candidature suivie.[/yellow]")
        return

    if id_suivi is None:
        choices = [f"ID {c['id']} - {truncate_text(c['offre_intitule'])} ({c['statut']})" for c in candidatures]
        selected = questionary.select("Choisir une candidature :", choices=choices).ask()
        if not selected:
            console.print("[yellow]Aucune candidature sélectionnée.[/yellow]")
            return
        id_suivi = int(selected.split(" - ")[0].replace("ID ", ""))

    if statut is None:
        statut = questionary.text("Nouveau statut :", default="Entretien prévu").ask()
        if not statut:
            console.print("[yellow]Aucun statut fourni.[/yellow]")
            return

    try:
        database.update_tracked_offer(id_suivi, statut)
        console.print(f"[bold green]✅ Statut de la candidature {id_suivi} mis à jour.[/bold green]")
        suivi_list()

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la mise à jour : {e}[/bold red]")

@suivi_app.command("notes")
def suivi_notes(id_suivi: int = typer.Argument(..., help="ID de la candidature")):
    """Affiche et permet de modifier les notes d'une candidature."""
    try:
        candidature = database.get_tracked_offer(id_suivi)
        if not candidature:
            console.print(f"[bold red]❌ Candidature {id_suivi} non trouvée.[/bold red]")
            return

        console.print(f"[bold cyan]Notes actuelles pour ID {id_suivi} :[/bold cyan]")
        console.print(Markdown(candidature.get("notes", "Aucune note.")))

        if questionary.confirm("Modifier les notes ?").ask():
            new_notes = questionary.text("Nouvelles notes :", multiline=True).ask()
            if new_notes:
                database.update_tracked_offer_notes(id_suivi, new_notes)
                console.print("[bold green]✅ Notes mises à jour ![/bold green]")
                console.print(Markdown(new_notes))

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la gestion des notes : {e}[/bold red]")

@app.command()
def match(
    profil: int = typer.Option(..., "--profil", help="ID du profil de CV"),
    offre: str = typer.Option(..., "--offre", help="ID de l'offre"),
):
    """Analyse la compatibilité entre un profil de CV et une offre."""
    console.print(f"[bold cyan]📊 Analyse de compatibilité pour l'offre {offre} avec le profil {profil}...[/bold cyan]")
    try:
        profil_data = database.get_profile(profil)
        if not profil_data:
            console.print(f"[bold red]❌ Profil {profil} non trouvé.[/bold red]")
            raise typer.Exit(code=1)

        async def get_offre_details():
            async with FTClient() as ft:
                return await ft.get_offre(offre)

        offre_data = asyncio.run(get_offre_details())
        if not offre_data:
            console.print(f"[bold red]❌ Offre {offre} non trouvée.[/bold red]")
            raise typer.Exit(code=1)

        with console.status("[bold green]Envoi à l'IA Gemini pour générer le rapport...[/bold green]", spinner="dots"):
            rapport = generer_rapport_matching_ia(profil_data["analyse"], offre_data)
        
        console.print(Panel(Markdown(rapport), title="[bold]Rapport de Compatibilité[/bold]", border_style="cyan"))
        
        # CORRECTION : On vérifie si l'IA a retourné une erreur et on quitte le cas échéant
        if rapport.strip().startswith("[ERREUR Gemini]"):
             console.print("[bold red]L'agent ne peut pas continuer car l'analyse de compatibilité a échoué.[/bold red]")
             raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de l'analyse de compatibilité : {e}[/bold red]")
        raise typer.Exit(code=1)

@app.command()
def adapter(
    profil: int = typer.Option(..., "--profil", help="ID du profil de CV"),
    offre: str = typer.Option(..., "--offre", help="ID de l'offre"),
):
    """Adapte un CV pour une offre spécifique."""
    console.print(f"[bold cyan]📝 Adaptation du CV pour l'offre {offre} avec le profil {profil}...[/bold cyan]")
    try:
        profil_data = database.get_profile(profil)
        if not profil_data:
            console.print(f"[bold red]❌ Profil {profil} non trouvé.[/bold red]")
            return

        async def get_offre_details():
            async with FTClient() as ft:
                return await ft.get_offre(offre)

        offre_data = asyncio.run(get_offre_details())
        if not offre_data:
            console.print(f"[bold red]❌ Offre {offre} non trouvée.[/bold red]")
            return

        with console.status("[bold green]Envoi à l'IA Gemini pour adaptation du CV...[/bold green]", spinner="dots"):
            cv_adapte = adapter_cv_ia(profil_data["texte"], offre_data)
        console.print(Panel(Markdown(cv_adapte), title="[bold]CV Adapté[/bold]", border_style="cyan"))

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de l'adaptation du CV : {e}[/bold red]")

@app.command("lettre")
def generer_lettre(
    profil: int = typer.Option(..., "--profil", help="ID du profil de CV à utiliser."),
    offre: str = typer.Option(..., "--offre", help="ID de l'offre pour laquelle générer la lettre."),
):
    """Génère une lettre de motivation adaptée à une offre via l'IA."""
    console.print(f"\n[bold cyan]📝 Génération de la lettre de motivation pour l'offre {offre}...[/bold cyan]")
    try:
        profil_data = database.get_profile(profil)
        if not profil_data:
            console.print(f"[bold red]❌ Profil {profil} non trouvé.[/bold red]")
            return

        async def get_offre_details():
            async with FTClient() as ft:
                return await ft.get_offre(offre)

        offre_data = asyncio.run(get_offre_details())
        if not offre_data:
            console.print(f"[bold red]❌ Offre {offre} non trouvée.[/bold red]")
            return

        with console.status("[bold green]Envoi à l'IA Gemini pour la rédaction...[/bold green]", spinner="dots"):
            lettre = generer_lettre_motivation_ia(profil_data["analyse"], offre_data)
        
        console.print(Panel(Markdown(lettre), title="[bold]Lettre de Motivation Suggérée[/bold]", border_style="cyan", expand=True))

    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la génération de la lettre : {e}[/bold red]")

if __name__ == "__main__":
    app()
