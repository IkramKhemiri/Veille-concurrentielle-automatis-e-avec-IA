"""
Rôle global :
Ce module est conçu pour nettoyer et filtrer les données textuelles extraites de sites web. Il supprime les éléments inutiles, 
les répétitions et les caractères spéciaux, tout en conservant les informations pertinentes. Il peut également traiter le contenu HTML brut 
pour en extraire uniquement le texte exploitable.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle crucial en garantissant que les données textuelles 
sont propres, cohérentes et prêtes à être analysées. Les données extraites des sites web contiennent souvent du bruit (scripts, styles, phrases génériques, etc.), 
et ce module permet de les transformer en contenu exploitable. Sans cette étape, les données seraient difficiles à analyser ou à visualiser.

Comment il aide dans le pipeline :
- **Scraping** : Nettoie les données brutes extraites pour éliminer le bruit et les éléments inutiles.
- **Analyse** : Prépare les données textuelles pour qu'elles soient prêtes à être analysées ou classifiées.
- **Visualisation** : Fournit des données textuelles claires et concises pour les intégrer dans des graphiques ou des tableaux.
- **Rapport** : Garantit que les informations textuelles dans les rapports sont propres et professionnelles.

Technologies utilisées :
- **BeautifulSoup** : Pour analyser et nettoyer le contenu HTML.
- **Expressions régulières (regex)** : Pour détecter et supprimer les motifs indésirables dans le texte.
- **Unicode** : Pour normaliser les caractères spéciaux et garantir une compatibilité maximale.
"""

import re
import unicodedata
from bs4 import BeautifulSoup

# Liste de phrases génériques à exclure du texte
GENERIC_PHRASES = [
    "en savoir plus", "learn more", "read more", "voir plus",
    "tous droits réservés", "accept cookies", "politique de confidentialité",
    "terms and conditions", "back to top", "lire la suite"
]

# Motifs à exclure du texte (URLs, lignes vides, etc.)
EXCLUDED_PATTERNS = [
    r"^https?://\S+$",  # URLs
    r"^www\.\S+$",      # URLs commençant par www
    r"^\s*$",           # Lignes vides
    r"^\W{1,5}$",       # Lignes contenant uniquement des caractères spéciaux
]

# Substitutions pour normaliser les caractères spéciaux
SUBSTITUTIONS = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", "•": "-",
    "™": "(TM)", "®": "(R)", "©": "(C)", "€": "EUR", "→": "->",
}

def nettoyer_texte(texte: str) -> str:
    """
    Rôle :
    Nettoie une chaîne de texte en supprimant les caractères spéciaux, en normalisant les espaces et en appliquant des substitutions.

    Fonctionnalité :
    - Remplace les caractères spéciaux par des équivalents standards.
    - Normalise le texte en supprimant les espaces inutiles et les retours à la ligne.
    - Préserve les accents pour une meilleure compatibilité avec les outils NLP.

    Importance :
    Cette fonction garantit que le texte est propre et normalisé, ce qui est essentiel pour les étapes d'analyse ou de visualisation.

    Arguments :
    - `texte` : Une chaîne de caractères à nettoyer.

    Retour :
    Une chaîne de caractères nettoyée.
    """
    if not isinstance(texte, str):
        return ""
    for old, new in SUBSTITUTIONS.items():
        texte = texte.replace(old, new)
    texte = unicodedata.normalize('NFKC', texte)  # Normalisation Unicode
    texte = re.sub(r'[\r\n\t]+', ' ', texte)  # Supprime les retours à la ligne et tabulations
    texte = re.sub(r'\s+', ' ', texte).strip()  # Supprime les espaces multiples
    return texte

def est_ligne_inutile(ligne: str) -> bool:
    """
    Rôle :
    Détermine si une ligne de texte est inutile ou non.

    Fonctionnalité :
    - Vérifie si la ligne est vide, trop courte ou contient des phrases génériques.
    - Utilise des motifs pour exclure les URLs ou les lignes non pertinentes.

    Importance :
    Cette fonction permet de filtrer les lignes inutiles avant de les inclure dans les données finales.

    Arguments :
    - `ligne` : Une chaîne de caractères représentant une ligne de texte.

    Retour :
    `True` si la ligne est inutile, sinon `False`.
    """
    if not ligne or not isinstance(ligne, str):
        return True
    t = ligne.strip().lower()
    if len(t) < 3:  # Trop courte
        return True
    if any(phrase in t for phrase in GENERIC_PHRASES):  # Contient une phrase générique
        return True
    for pattern in EXCLUDED_PATTERNS:  # Correspond à un motif exclu
        if re.search(pattern, t):
            return True
    return False

def est_trop_repetitive(ligne: str) -> bool:
    """
    Rôle :
    Vérifie si une ligne de texte est trop répétitive.

    Fonctionnalité :
    - Calcule le ratio de mots uniques par rapport au nombre total de mots.
    - Considère une ligne comme répétitive si ce ratio est trop faible.

    Importance :
    Cette fonction permet d'éliminer les lignes qui contiennent des répétitions excessives, souvent inutiles.

    Arguments :
    - `ligne` : Une chaîne de caractères représentant une ligne de texte.

    Retour :
    `True` si la ligne est trop répétitive, sinon `False`.
    """
    words = ligne.split()
    if len(words) < 4:  # Trop courte pour être répétitive
        return False
    uniq = len(set(words)) / len(words)  # Ratio mots uniques / total
    return uniq < 0.35

def nettoyer_bloc(txt: str) -> str:
    """
    Rôle :
    Nettoie un bloc de texte en supprimant les lignes inutiles ou répétitives.

    Fonctionnalité :
    - Divise le texte en lignes et applique des filtres pour exclure les lignes non pertinentes.
    - Supprime les doublons et retourne un texte nettoyé.

    Importance :
    Cette fonction garantit que les blocs de texte sont propres et prêts à être utilisés dans les étapes suivantes.

    Arguments :
    - `txt` : Une chaîne de caractères représentant un bloc de texte.

    Retour :
    Une chaîne de caractères nettoyée.
    """
    if not txt:
        return ""
    lines = [l.strip() for l in str(txt).splitlines()]
    out = []
    seen = set()
    for l in lines:
        l2 = nettoyer_texte(l)
        if est_ligne_inutile(l2) or est_trop_repetitive(l2):
            continue
        k = l2.lower()
        if k in seen:  # Évite les doublons
            continue
        seen.add(k)
        out.append(l2)
    return "\n".join(out)

def clean_html(html: str) -> str:
    """
    Rôle :
    Nettoie le contenu HTML brut pour en extraire uniquement le texte pertinent.

    Fonctionnalité :
    - Supprime les balises inutiles (scripts, styles, etc.).
    - Extrait le texte brut et applique un nettoyage supplémentaire.

    Importance :
    Cette fonction est essentielle pour transformer le contenu HTML en texte exploitable.

    Arguments :
    - `html` : Une chaîne de caractères contenant le contenu HTML.

    Retour :
    Une chaîne de caractères contenant le texte nettoyé.
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav", "form", "aside"]):
        tag.decompose()  # Supprime les balises inutiles
    text = soup.get_text(separator="\n")
    return nettoyer_bloc(text)

def clean_extracted_data(texte: str, validate_urls=False) -> str:
    """
    Rôle :
    Nettoie les données textuelles extraites en supprimant les lignes inutiles, répétitives ou invalides.

    Fonctionnalité :
    - Applique un nettoyage ligne par ligne.
    - Valide ou exclut les URLs si nécessaire.
    - Supprime les doublons.

    Importance :
    Cette fonction garantit que les données extraites sont prêtes pour l'analyse ou la visualisation.

    Arguments :
    - `texte` : Une chaîne de caractères contenant les données extraites.
    - `validate_urls` : Si `True`, exclut les URLs des données nettoyées.

    Retour :
    Une chaîne de caractères nettoyée.
    """
    if not texte:
        return ""
    lines = [l for l in str(texte).splitlines()]
    cleaned = []
    seen = set()
    for l in lines:
        l2 = nettoyer_texte(l)
        if validate_urls and re.match(r"https?://", l2.lower()):  # Exclut les URLs si demandé
            continue
        if est_ligne_inutile(l2) or est_trop_repetitive(l2):
            continue
        k = l2.lower()
        if k in seen:  # Évite les doublons
            continue
        seen.add(k)
        cleaned.append(l2)
    return "\n".join(cleaned)

def clean_text_blocks(text: str) -> str:
    """
    Rôle :
    Nettoie des blocs de texte en supprimant les lignes inutiles et les doublons.

    Fonctionnalité :
    - Divise le texte en lignes.
    - Applique un nettoyage ligne par ligne.
    - Supprime les doublons.

    Importance :
    Cette fonction est utile pour traiter des blocs de texte volumineux et garantir leur qualité.

    Arguments :
    - `text` : Une chaîne de caractères représentant un bloc de texte.

    Retour :
    Une chaîne de caractères nettoyée.
    """
    if not text:
        return ""
    lines = [l.strip() for l in str(text).splitlines()]
    out = []
    seen = set()
    for l in lines:
        l2 = nettoyer_texte(l)
        if est_ligne_inutile(l2):
            continue
        k = l2.lower()
        if k in seen:  # Évite les doublons
            continue
        seen.add(k)
        out.append(l2)
    return "\n".join(out)
