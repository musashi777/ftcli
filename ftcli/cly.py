#!/usr/bin/env python3
import argparse
import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
import google.generativeai as genai

# Charger les variables d'environnement
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def extraire_texte_cv(chemin_cv):
    """Extrait le texte d'un fichier PDF."""
    doc = fitz.open(chemin_cv)
    texte = ""
    for page in doc:
        texte += page.get_text()
    return texte

def analyser_cv(texte_cv):
    """Analyse le CV pour extraire les compétences, expériences et formations."""
    prompt = f"""
Analyse le CV suivant et extrait les informations suivantes :
- Compétences
- Expériences professionnelles
- Formations

CV :
{texte_cv}
"""
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

def adapter_cv(texte_cv, description_offre):
    """Adapte le CV en fonction de l'offre d'emploi."""
    prompt = f"""
À partir du CV suivant :
{texte_cv}

Et de la description de l'offre d'emploi suivante :
{description_offre}

Génère un CV adapté mettant en avant les compétences et expériences pertinentes pour cette offre.
"""
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

def main():
    parser = argparse.ArgumentParser(description="Analyse et adaptation de CV")
    parser.add_argument("--cv", help="Chemin vers le fichier CV en PDF")
    parser.add_argument("--offre", help="Description de l'offre d'emploi")
    args = parser.parse_args()

    if args.cv:
        texte_cv = extraire_texte_cv(args.cv)
        informations_cv = analyser_cv(texte_cv)
        print("Informations extraites du CV :")
        print(informations_cv)

        if args.offre:
            cv_adapte = adapter_cv(texte_cv, args.offre)
            print("CV adapté à l'offre :")
            print(cv_adapte)
    else:
        print("Veuillez fournir le chemin vers le fichier CV en utilisant l'option --cv.")

if __name__ == "__main__":
    main()
