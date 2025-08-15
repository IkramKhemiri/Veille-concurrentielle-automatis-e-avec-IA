# scraping/cleaner.py
import re
import unicodedata
from bs4 import BeautifulSoup

GENERIC_PHRASES = [
    "en savoir plus", "learn more", "read more", "voir plus",
    "tous droits réservés", "accept cookies", "politique de confidentialité",
    "terms and conditions", "back to top", "lire la suite"
]

EXCLUDED_PATTERNS = [
    r"^https?://\S+$",
    r"^www\.\S+$",
    r"^\s*$",
    r"^\W{1,5}$",
]

SUBSTITUTIONS = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", "•": "-",
    "™": "(TM)", "®": "(R)", "©": "(C)", "€": "EUR", "→": "->",
}

def nettoyer_texte(texte: str) -> str:
    if not isinstance(texte, str):
        return ""
    for old, new in SUBSTITUTIONS.items():
        texte = texte.replace(old, new)
    # Keep accents for better NLP downstream; normalize
    texte = unicodedata.normalize('NFKC', texte)
    texte = re.sub(r'[\r\n\t]+', ' ', texte)
    texte = re.sub(r'\s+', ' ', texte).strip()
    return texte

def est_ligne_inutile(ligne: str) -> bool:
    if not ligne or not isinstance(ligne, str):
        return True
    t = ligne.strip().lower()
    if len(t) < 3:
        return True
    if any(phrase in t for phrase in GENERIC_PHRASES):
        return True
    for pattern in EXCLUDED_PATTERNS:
        if re.search(pattern, t):
            return True
    return False

def est_trop_repetitive(ligne: str) -> bool:
    words = ligne.split()
    if len(words) < 4:
        return False
    uniq = len(set(words)) / len(words)
    return uniq < 0.35

def nettoyer_bloc(txt: str) -> str:
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
        if k in seen:
            continue
        seen.add(k)
        out.append(l2)
    return "\n".join(out)

def clean_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav", "form", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return nettoyer_bloc(text)

def clean_extracted_data(texte: str, validate_urls=False) -> str:
    if not texte:
        return ""
    lines = [l for l in str(texte).splitlines()]
    cleaned = []
    seen = set()
    for l in lines:
        l2 = nettoyer_texte(l)
        if validate_urls and re.match(r"https?://", l2.lower()):
            continue
        if est_ligne_inutile(l2) or est_trop_repetitive(l2):
            continue
        k = l2.lower()
        if k in seen:
            continue
        seen.add(k)
        cleaned.append(l2)
    return "\n".join(cleaned)

def clean_text_blocks(text: str) -> str:
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
        if k in seen:
            continue
        seen.add(k)
        out.append(l2)
    return "\n".join(out)
