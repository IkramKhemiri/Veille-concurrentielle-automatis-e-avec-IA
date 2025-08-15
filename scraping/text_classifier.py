# scraping/text_classifier.py

import re
from collections import defaultdict

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
    Classe un bloc de texte selon sa thématique probable.
    """
    if not text or len(text.strip()) < 20:
        return None

    text_lower = text.lower()
    for theme, keywords in THEMATIC_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                return theme
    return None

def classify_blocks(blocks):
    """
    Classe une liste de blocs de texte par thème.
    """
    if not blocks or not isinstance(blocks, list):
        return {}

    classified = defaultdict(list)
    for block in blocks:
        if not isinstance(block, str) or len(block.strip()) < 20:
            continue
        theme = classify_block(block)
        if theme:
            classified[theme].append(block)
        else:
            classified["others"].append(block)

    return dict(classified)
