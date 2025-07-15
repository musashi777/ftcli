# 🚀 FTCli - Votre Assistant de Recherche d'Emploi IA (v1.0.0)

**FTCli** est un outil en ligne de commande puissant conçu pour rationaliser et optimiser votre recherche d'emploi. Il s'interface avec les API de **France Travail** et des **IA de pointe (Google Gemini, DeepSeek)** pour vous offrir un avantage compétitif, le tout depuis votre terminal.

Passez de la simple recherche d'offres à une stratégie de carrière proactive !

## ✨ Fonctionnalités Principales

* **Double Stratégie de Recherche :**
    * **Réactive :** Trouvez les offres d'emploi publiées avec des filtres avancés (`search`).
    * **Proactive :** Identifiez les entreprises à fort potentiel d'embauche qui ne recrutent pas encore ouvertement (`companies`).
* **Assistance par IA :**
    * **Analyse de CV :** Extrayez automatiquement les informations clés de votre CV PDF (`profils analyser`).
    * **Matching Intelligent :** Obtenez un rapport de compatibilité détaillé entre votre profil et une offre (`match`).
    * **Rédaction Automatisée :** Générez des CV adaptés (`adapter`) et des lettres de motivation percutantes (`lettre`) en quelques secondes.
* **Suivi de Candidatures (CRM) :**
    * Ne perdez plus jamais le fil de vos candidatures grâce à un tableau de suivi intégré pour gérer les statuts (`suivi list`), sauvegarder des offres (`suivi save`) et prendre des notes.
* **Agent Autonome :**
    * Donnez un objectif complexe en langage naturel (ex: "trouve 3 offres et analyse la meilleure") et laissez l'agent planifier et exécuter les actions pour vous (`agent`).
* **Interface Intuitive :**
    * Utilisez les commandes directement ou lancez un menu interactif simple d'utilisation avec `ftcli menu`.

## 🛠️ Installation

FTCli est conçu pour fonctionner sur des environnements Linux (Debian, Ubuntu...) et est particulièrement adapté pour **Termux** sur Android.

### Prérequis

1.  **Python** (version 3.10 ou supérieure).
2.  **Git** pour cloner le projet.
3.  **poppler-utils** pour permettre l'analyse des CV au format PDF.
    ```bash
    # Sur Debian/Ubuntu ou dans Termux
    pkg update && pkg upgrade
    pkg install git python poppler
    ```

### Étape 1 : Obtenir les Clés d'API

Pour utiliser FTCli, vous avez besoin de 3 types de clés d'API gratuites.

* **France Travail :**
    1.  Créez un compte sur [francetravail.io](https://francetravail.io).
    2.  Dans votre espace personnel, créez une nouvelle application.
    3.  Abonnez cette application aux **deux** API suivantes :
        * `Offres d'emploi v2`
        * `La Bonne Boite v2`
    4.  Copiez votre **Identifiant client** et votre **Clé secrète**.

* **Google Gemini (pour l'analyse IA) :**
    1.  Allez sur [Google AI Studio](https://aistudio.google.com/).
    2.  Connectez-vous avec votre compte Google et cliquez sur "Get API key".
    3.  Copiez votre clé API.

* **DeepSeek (pour l'agent) :**
    1.  Créez un compte sur le [Portail Développeur DeepSeek](https://platform.deepseek.com/).
    2.  Allez dans la section "API Keys" et créez une nouvelle clé.
    3.  Copiez votre clé API.

### Étape 2 : Installation de FTCli

1.  **Clonez le dépôt :**
    ```bash
    git clone [https://github.com/musashi777/ftcli](https://github.com/musashi777/ftcli)
    cd ftcli
    ```
2.  **Créez un environnement virtuel et activez-le :**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  **Installez les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Rendez la commande `ftcli` accessible :**
    ```bash
    pip install -e .
    ```

### Étape 3 : Configuration

1.  **Créez le fichier `.env`** à la racine de votre projet :
    ```bash
    cp .env.example .env
    ```
2.  **Ouvrez ce fichier `.env` et collez-y vos clés** :
    ```ini
    # Fichier: .env
    FT_CLIENT_ID="VOTRE_IDENTIFIANT_CLIENT_FRANCE_TRAVAIL"
    FT_CLIENT_SECRET="VOTRE_CLE_SECRETE_FRANCE_TRAVAIL"
    GEMINI_API_KEY="VOTRE_CLE_API_GEMINI"
    DEEPSEEK_API_KEY="VOTRE_CLE_API_DEEPSEEK"
    ```

L'installation est terminée ! Vous pouvez maintenant utiliser l'application.

## 📖 Guide des Commandes

#### Lancement
* `ftcli` : Affiche le tableau de bord.
* `ftcli menu` : Lance le menu interactif.
* `ftcli --help` : Affiche l'aide et toutes les commandes.

#### Recherche (Offres & Entreprises)
* `ftcli search --mots "..." --departement "..."` : Recherche des offres d'emploi.
* `ftcli companies --job "..." --location "..."` : Trouve les entreprises à fort potentiel d'embauche.
* `ftcli view <ID_OFFRE>` : Affiche les détails d'une offre.

#### Gestion des Profils & CV
* `ftcli profils analyser --nom "..." <chemin/vers/cv.pdf>` : Analyse un CV et le sauvegarde.
* `ftcli profils lister` : Liste tous les profils de CV sauvegardés.

#### Assistance IA
* `ftcli match --profil <ID> --offre <ID_OFFRE>` : Analyse la compatibilité entre votre profil et une offre et propose des actions.
* `ftcli adapter --profil <ID> --offre <ID_OFFRE>` : Génère une version de votre CV optimisée pour l'offre.
* `ftcli lettre --profil <ID> --offre <ID_OFFRE>` : Rédige une lettre de motivation personnalisée.

#### Suivi des Candidatures
* `ftcli suivi list` : Affiche toutes vos candidatures.
* `ftcli suivi save <ID_OFFRE>` : Ajoute une offre à votre suivi.
* `ftcli suivi update` : Modifie le statut d'une candidature.
* `ftcli suivi notes <ID_SUIVI>` : Ajoute ou modifie des notes pour une candidature.

#### Agent Autonome
* `ftcli agent "Votre objectif en français"` : Lance l'agent IA pour qu'il planifie et exécute plusieurs actions à la suite.
    * Exemple : `ftcli agent "cherche 3 offres de technicien à Lyon, sauvegarde la meilleure et rédige une lettre de motivation pour celle-ci en utilisant mon profil 1"`



## 💡 Exemples de Scénarios d'Utilisation

Voici comment vous pouvez utiliser `ftcli` dans des situations réelles pour optimiser votre recherche d'emploi.

---
### Scénario 1 : Recherche Simple et Consultation

* **Objectif :** Je veux rapidement voir les offres de "technicien informatique" dans les Bouches-du-Rhône et consulter les détails d'une offre qui m'intéresse.

* **Commandes :**

1.  **Lancer la recherche :**
    ```bash
    ftcli search --mots "technicien informatique" --departement 13
    ```

2.  **Consulter une offre précise** (après avoir noté son ID, par exemple `195FPVH`) :
    ```bash
    ftcli view 195FPVH
    ```

---
### Scénario 2 : Analyse de Compatibilité et Suivi

* **Objectif :** J'ai déjà analysé mon CV (profil ID 2). Je veux trouver une offre d'"aide-soignant", vérifier si mon profil correspond, et la sauvegarder si c'est le cas.

* **Commandes :**

1.  **Lancer la recherche :**
    ```bash
    ftcli search --mots "aide-soignant" --departement 13
    ```

2.  **Analyser la compatibilité** avec une offre (par exemple `192VXBS`) :
    ```bash
    ftcli match --profil 2 --offre 192VXBS
    ```

3.  **Sauvegarder l'offre** pour ne pas l'oublier :
    ```bash
    ftcli suivi save 192VXBS
    ```

---
### Scénario 3 : Workflow d'Application Complet avec l'IA

* **Objectif :** Je veux postuler à une offre de "développeur" et je veux que l'IA m'aide à préparer un CV et une lettre de motivation parfaits.

* **Commandes :**

1.  **Trouver l'offre parfaite** et noter son ID (ex: `195DFCP`) :
    ```bash
    ftcli search --mots "Développeur Symfony" --type-contrat CDI
    ```

2.  **Analyser la compatibilité** pour comprendre les attentes du recruteur :
    ```bash
    ftcli match --profil 1 --offre 195DFCP
    ```

3.  **Générer une version optimisée de votre CV** :
    ```bash
    ftcli adapter --profil 1 --offre 195DFCP
    ```

4.  **Générer une lettre de motivation** sur mesure :
    ```bash
    ftcli lettre --profil 1 --offre 195DFCP
    ```

---
### Scénario 4 : Automatisation Totale avec l'Agent

* **Objectif :** Je suis pressé. Je veux que l'assistant fasse tout le travail du Scénario 3 pour moi.

* **Commande :**

1.  **Donner une mission complexe à l'agent :**
    ```bash
    ftcli agent "Trouve la meilleure offre pour 'technicien de maintenance' à Marseille, analyse la compatibilité avec mon profil 1, puis prépare un CV adapté et une lettre de motivation."
    ```
