from typing import List, Dict

def export_to_txt(data: List[Dict], filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        for i, offre in enumerate(data, 1):
            lieu = offre.get("lieuTravail", {}).get("libelle", "?")
            contrat = offre.get("typeContratLibelle", "?")
            date = offre.get("dateCreation", "")[:10]
            entreprise = offre.get("entreprise", {}).get("nom") or offre.get("entreprise", {}).get("description", "?")
            url = offre.get("origineOffre", {}).get("urlOrigine", "-")
            salaire = offre.get("salaire", {}).get("libelle") or "Non précisé"
            rome = f"{offre.get('romeCode','')} - {offre.get('romeLibelle','')}"
            appel = offre.get("appellationlibelle", "")
            desc = offre.get("description", "").replace("\n", " ").strip()
            desc_short = desc[:200] + ("..." if len(desc) > 200 else "")
            f.write(f"""{i}. {offre.get("intitule", "?")}
Lieu : {lieu}
Type de contrat : {contrat}
Date publication : {date}
Entreprise : {entreprise}
Salaire : {salaire}
ROME : {rome} | {appel}
Description : {desc_short}
Lien : {url}
{'-'*70}
""")

def export_to_html(data: List[Dict], filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><title>Offres d'emploi</title></head><body>")
        f.write("<h1>Offres d'emploi exportées</h1>")
        for i, offre in enumerate(data, 1):
            lieu = offre.get("lieuTravail", {}).get("libelle", "?")
            contrat = offre.get("typeContratLibelle", "?")
            date = offre.get("dateCreation", "")[:10]
            entreprise = offre.get("entreprise", {}).get("nom") or offre.get("entreprise", {}).get("description", "?")
            url = offre.get("origineOffre", {}).get("urlOrigine", "-")
            salaire = offre.get("salaire", {}).get("libelle") or "Non précisé"
            rome = f"{offre.get('romeCode','')} - {offre.get('romeLibelle','')}"
            appel = offre.get("appellationlibelle", "")
            desc = offre.get("description", "").replace("\n", " ").strip()
            desc_short = desc[:400] + ("..." if len(desc) > 400 else "")
            f.write(f"""
<h2>{i}. {offre.get("intitule", "?")}</h2>
<ul>
<li><b>Lieu :</b> {lieu}</li>
<li><b>Type de contrat :</b> {contrat}</li>
<li><b>Date publication :</b> {date}</li>
<li><b>Entreprise :</b> {entreprise}</li>
<li><b>Salaire :</b> {salaire}</li>
<li><b>ROME :</b> {rome} | {appel}</li>
<li><b>Description :</b> {desc_short}</li>
<li><b>Lien :</b> <a href="{url}">{url}</a></li>
</ul>
<hr>
""")
        f.write("</body></html>")
