import typer
import rich
from client import FTClient
from exporter import export_to_txt, export_to_html
from gemini_utils import extraire_sections_cv_ia

app = typer.Typer()

@app.command()
def search(
    mots: str = typer.Option(..., help="Mots-clés"),
    arrondissement: str = typer.Option(None, help="Arrondissement (ex: 13, 6...)"),
    max_results: int = typer.Option(10, help="Nombre d'offres max"),
    export_format: str = typer.Option(None, help="Format d'export : txt, html"),
    export_filename: str = typer.Option("offres", help="Nom du fichier export (sans extension)")
):
    # Codes INSEE Marseille
    arr_marseille = {
        "1": "13201", "2": "13202", "3": "13203", "4": "13204",
        "5": "13205", "6": "13206", "7": "13207", "8": "13208",
        "9": "13209", "10": "13210", "11": "13211", "12": "13212",
        "13": "13213", "14": "13214", "15": "13215", "16": "13216"
    }
    commune_code = arr_marseille.get(arrondissement) if arrondissement else None

    import asyncio
    async def runner():
        async with FTClient() as ft:
            offres = await ft.search_offres(
                mots=mots,
                communes=[commune_code] if commune_code else None,
            )
        offres = offres[:max_results]
        rich.print(f"[bold green]Offres trouvées : {len(offres)}")
        for i, offre in enumerate(offres, 1):
            titre = offre.get("intitule", "?")
            lieu = offre.get("lieuTravail", {}).get("libelle", "?")
            contrat = offre.get("typeContratLibelle", "?")
            print(f"{i}. {titre} | {lieu} | {contrat}")

        if offres:
            choix = input("Numéro d’offre pour voir les détails ou 0 pour quitter: ")
            if choix.isdigit() and int(choix) > 0 and int(choix) <= len(offres):
                idx = int(choix) - 1
                offre = offres[idx]
                print("\n[DESCRIPTION DE L'OFFRE]")
                print(offre.get("description", "Pas de description"))
                print("\nRésumé IA des prérequis :")
                print(extraire_sections_cv_ia(offre.get("description", "")))
            else:
                return

        if export_format:
            filename = f"{export_filename}.{export_format}"
            if export_format == "txt":
                export_to_txt(offres, filename)
            elif export_format == "html":
                export_to_html(offres, filename)
            print(f"Fichier exporté : {filename}")

    asyncio.run(runner())

@app.command("analyse-cv")
def analyse_cv(
    cv_path: str = typer.Option(..., help="Chemin du fichier PDF CV"),
    out: str = typer.Option("terminal", help="Sortie : terminal, txt, md, ou chemin fichier")
):
    import subprocess
    txt_path = cv_path.replace(".pdf", ".txt")
    try:
        subprocess.run(["pdftotext", cv_path, txt_path], check=True)
        with open(txt_path, "r", encoding="utf-8") as f:
            texte_cv = f.read()
    except Exception as e:
        typer.echo(f"[ERREUR] Impossible d'extraire le texte : {e}")
        raise typer.Exit(code=1)
    typer.echo("[INFO] Envoi du texte extrait à Gemini pour analyse IA…")
    result = extraire_sections_cv_ia(texte_cv)
    if out == "terminal":
        typer.echo(result)
    else:
        if out in ("txt", "md"):
            output_file = txt_path.replace(".txt", f"_analyse.{out}")
        else:
            output_file = out
        with open(output_file, "w", encoding="utf-8") as fout:
            fout.write(result)
        typer.echo(f"[OK] Résultat écrit dans : {output_file}")

if __name__ == "__main__":
    app()
