"""
Rôle global :
Ce module est un classificateur thématique qui analyse un texte brut pour identifier et organiser les informations 
en fonction de thèmes prédéfinis (services, clients, technologies, etc.). Il extrait également des informations spécifiques 
comme les adresses email et les numéros de téléphone.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle crucial en structurant les données textuelles. 
Il permet de catégoriser les informations brutes en sections thématiques claires, facilitant leur exploitation dans les étapes suivantes. 
Sans cette étape, les données seraient désorganisées et difficiles à utiliser.

Comment il aide dans le pipeline :
- **Scraping** : Les données textuelles extraites sont souvent non structurées.
- **Analyse** : Ce module organise ces données en thèmes, rendant leur traitement plus efficace.
- **Visualisation** : Les sections thématiques permettent de créer des graphiques ou des tableaux spécifiques à chaque catégorie.
- **Rapport** : Les informations organisées sont prêtes à être intégrées dans des rapports professionnels.

Technologies utilisées :
- **Expressions régulières (regex)** : Utilisées pour extraire des informations spécifiques comme les emails et les numéros de téléphone.
- **Thèmes prédéfinis** : Une liste de mots-clés pour chaque thème permet de classer les lignes de texte en fonction de leur contenu.
"""

import re

# Dictionnaire contenant les thèmes et leurs mots-clés associés
THEMES = {
    "services": ["service", "nos services", "solutions", "prestations"],
    "clients": ["nos clients", "ils nous font confiance", "testimonials", "portfolio"],
    "technologies": ["technologie", "stack", "tools", "framework"],
    "jobs": ["recrutement", "emplois", "job", "carrière"],
    "blog": ["blog", "actualités", "articles"],
    "emails": [],  # Les emails seront extraits dynamiquement
    "phones": []   # Les numéros de téléphone seront extraits dynamiquement
}

# Fonction principale pour classer un texte brut par thèmes
def classer_par_theme(texte):
    """
    Rôle :
    Cette fonction analyse un texte brut pour identifier et organiser les informations en fonction de thèmes prédéfinis. 
    Elle extrait également des emails et des numéros de téléphone.

    Fonctionnalité :
    - Parcourt chaque ligne du texte pour détecter des mots-clés associés à des thèmes spécifiques.
    - Organise les lignes correspondantes dans des sections thématiques.
    - Utilise des expressions régulières pour extraire les emails et les numéros de téléphone.

    Importance :
    Cette fonction est essentielle pour structurer les données textuelles brutes, ce qui facilite leur exploitation 
    dans les étapes suivantes du pipeline.

    Arguments :
    - `texte` : Une chaîne de caractères contenant le texte brut à analyser.

    Retour :
    Un dictionnaire contenant les sections thématiques et les informations extraites (emails, téléphones).
    """
    # Initialisation des sections thématiques
    sections = {k: [] for k in THEMES}

    # Normalisation et traitement ligne par ligne
    lignes = texte.splitlines()
    for ligne in lignes:
        l = ligne.lower().strip()  # Convertir en minuscule et supprimer les espaces inutiles
        if not l or len(l) < 15:  # Ignorer les lignes vides ou trop courtes
            continue
        # Vérification des mots-clés pour chaque thème
        for theme, mots_cles in THEMES.items():
            if any(mc in l for mc in mots_cles):  # Si un mot-clé est trouvé dans la ligne
                sections[theme].append(ligne.strip())  # Ajouter la ligne à la section correspondante

    # Extraction des emails à l'aide d'expressions régulières
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", texte)
    sections["emails"] = list(set(emails))  # Supprimer les doublons

    # Extraction des numéros de téléphone à l'aide d'expressions régulières
    phones = re.findall(r"(?:\+\d{1,3})?[ \-.]?\(?\d{2,4}\)?[ \-.]?\d{3,4}[ \-.]?\d{3,4}", texte)
    sections["phones"] = list(set(phones))  # Supprimer les doublons

    # Retourner les sections thématiques
    return sections
