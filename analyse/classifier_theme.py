# analyse/classifier_theme.py

import re

THEMES = {
    "services": ["service", "nos services", "solutions", "prestations"],
    "clients": ["nos clients", "ils nous font confiance", "testimonials", "portfolio"],
    "technologies": ["technologie", "stack", "tools", "framework"],
    "jobs": ["recrutement", "emplois", "job", "carrière"],
    "blog": ["blog", "actualités", "articles"],
    "emails": [],
    "phones": []
}

def classer_par_theme(texte):
    sections = {k: [] for k in THEMES}

    # Normalisation
    lignes = texte.splitlines()
    for ligne in lignes:
        l = ligne.lower().strip()
        if not l or len(l) < 15:
            continue
        for theme, mots_cles in THEMES.items():
            if any(mc in l for mc in mots_cles):
                sections[theme].append(ligne.strip())

    # Extraction des emails
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", texte)
    sections["emails"] = list(set(emails))

    # Extraction des téléphones
    phones = re.findall(r"(?:\+\d{1,3})?[ \-.]?\(?\d{2,4}\)?[ \-.]?\d{3,4}[ \-.]?\d{3,4}", texte)
    sections["phones"] = list(set(phones))

    return sections
