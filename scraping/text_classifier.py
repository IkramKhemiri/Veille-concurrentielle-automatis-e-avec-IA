"""
Rôle global :
Ce module est conçu pour classer des blocs de texte extraits d'un site web en fonction de thématiques prédéfinies 
(comme "services", "clients", "technologies", etc.). Il utilise des mots-clés spécifiques pour identifier la catégorie 
la plus probable d'un texte donné.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle clé en organisant les données textuelles 
en sections thématiques. Cela permet de structurer les informations brutes extraites, facilitant leur analyse et leur utilisation 
dans des visualisations ou des rapports. Sans cette étape, les données seraient désorganisées et difficiles à exploiter.

Comment il aide dans le pipeline :
- **Scraping** : Les blocs de texte extraits sont souvent non catégorisés. Ce module les organise en thèmes clairs.
- **Analyse** : Les données classées permettent une analyse plus ciblée et pertinente.
- **Visualisation** : Les sections thématiques peuvent être utilisées pour créer des graphiques ou des tableaux spécifiques.
- **Rapport** : Les informations organisées sont prêtes à être intégrées dans des rapports professionnels.

Technologies utilisées :
- **Expressions régulières (regex)** : Pour détecter la présence de mots-clés dans les blocs de texte.
- **Dictionnaire de mots-clés** : Une liste de mots-clés thématiques est utilisée pour classer les textes.
- **Collections (defaultdict)** : Pour organiser les blocs de texte classés par thème.
"""

import re
from collections import defaultdict

# Dictionnaire contenant les mots-clés associés à chaque thématique
THEMATIC_KEYWORDS = {
    "presentation": [
        "qui sommes-nous", "about us", "présentation", "qui est", "qui sommes", "notre histoire", "mission", "vision"
    ],
    "slogan": [
        "notre slogan", "slogan", "motto", "devise", "engagement", "accompagnement"
    ],
    "services": [
        "services", "nos services", "offre", "solutions", "prestations", "domaines d’intervention", "ce que nous faisons", "what we do"
    ],
    "clients": [
        "clients", "nos clients", "ils nous font confiance", "témoignages", "références", "portfolio"
    ],
    "technologies": [
        "technologies", "stack", "framework", "tools", "environnement technique", "langages"
    ],
    "blog": [
        "blog", "actualités", "news", "articles", "événements", "évènement", "publication"
    ],
    "contact": [
        "contact", "nous contacter", "get in touch", "email", "téléphone", "adresse"
    ],
    "jobs": [
        "carrière", "jobs", "recrutement", "nous rejoindre", "postuler", "emplois"
    ]
}

def classify_block(text):
    """
    Rôle :
    Classe un bloc de texte en fonction de sa thématique probable.

    Fonctionnalité :
    - Parcourt les mots-clés associés à chaque thématique.
    - Vérifie si un mot-clé est présent dans le texte.
    - Retourne la thématique correspondante si un mot-clé est trouvé.

    Importance :
    Cette fonction permet de catégoriser un texte brut en une thématique spécifique, facilitant ainsi son organisation 
    et son exploitation dans les étapes suivantes.

    Arguments :
    - `text` : Une chaîne de caractères représentant un bloc de texte.

    Retour :
    Une chaîne de caractères représentant la thématique (par exemple, "services", "clients") ou `None` si aucune thématique n'est trouvée.
    """
    if not text or len(text.strip()) < 20:  # Ignore les textes trop courts
        return None

    text_lower = text.lower()
    for theme, keywords in THEMATIC_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):  # Recherche un mot-clé dans le texte
                return theme
    return None

def classify_blocks(blocks):
    """
    Rôle :
    Classe une liste de blocs de texte en fonction de leurs thématiques probables.

    Fonctionnalité :
    - Parcourt chaque bloc de texte.
    - Utilise `classify_block` pour déterminer la thématique de chaque bloc.
    - Organise les blocs classés dans un dictionnaire par thématique.

    Importance :
    Cette fonction permet de traiter un ensemble de blocs de texte en une seule étape, en les organisant par thématique. 
    Cela facilite leur analyse et leur utilisation dans des visualisations ou des rapports.

    Arguments :
    - `blocks` : Une liste de chaînes de caractères représentant des blocs de texte.

    Retour :
    Un dictionnaire où les clés sont les thématiques et les valeurs sont des listes de blocs de texte appartenant à ces thématiques.
    """
    if not blocks or not isinstance(blocks, list):  # Vérifie que l'entrée est une liste valide
        return {}

    classified = defaultdict(list)
    for block in blocks:
        if not isinstance(block, str) or len(block.strip()) < 20:  # Ignore les blocs non pertinents
            continue
        theme = classify_block(block)
        if theme:
            classified[theme].append(block)  # Ajoute le bloc à la thématique correspondante
        else:
            classified["others"].append(block)  # Classe les blocs non identifiés dans "others"

    return dict(classified)
