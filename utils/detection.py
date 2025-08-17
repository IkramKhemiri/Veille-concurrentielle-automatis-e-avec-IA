"""
Rôle global :
Ce module est conçu pour détecter des caractéristiques spécifiques des sites web, comme leur nature statique ou dynamique, 
la présence de mesures anti-bot, ou encore des sections contenant des nouveautés ou des offres. Il fournit également des outils 
pour analyser les sites et détecter les signaux indiquant une forte utilisation de JavaScript.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle essentiel en identifiant les 
caractéristiques des sites web avant leur traitement. Cela permet d'adapter les stratégies de scraping et d'analyse en fonction 
des spécificités de chaque site. Par exemple, détecter un site lourd en JavaScript permet de choisir une approche dynamique 
(Selenium), tandis qu'un site statique peut être traité plus rapidement avec des requêtes HTTP simples.

Comment il aide dans le pipeline :
- **Scraping** : Identifie si un site est statique ou dynamique, et détecte les mesures anti-bot pour ajuster les outils de scraping.
- **Analyse** : Extrait des sections pertinentes comme les nouveautés ou les offres pour enrichir les données.
- **Visualisation** : Fournit des informations sur les sections importantes qui peuvent être utilisées dans des graphiques ou des tableaux.
- **Rapport** : Aide à structurer les données en identifiant les éléments clés d'un site web.

Technologies utilisées :
- **Requests** : Pour envoyer des requêtes HTTP et récupérer le contenu HTML des sites web.
- **BeautifulSoup** : Pour analyser et extraire les données textuelles des pages HTML.
- **Expressions régulières (regex)** : Pour détecter des motifs spécifiques dans les URLs ou le contenu HTML.
- **Logging** : Pour suivre les étapes du processus et signaler les erreurs ou les caractéristiques détectées.
"""

import requests
from bs4 import BeautifulSoup
import logging
import re

# Définitions des mots-clés pour différentes détections
DEFAULT_KEYWORDS = [
    "contact", "about", "service", "solution", "propos", "accueil", "home",
    "produit", "offre", "actualités", "blog", "portfolio", "témoignage", "tarif"
]

NOVELTY_KEYWORDS = [
    "nouveaut", "new", "news", "recent", "update", "mise à jour", "promotion",
    "promo", "soldes", "réduction", "actualité", "publication", "release", "événement"
]

OFFRE_KEYWORDS = [
    "offre", "nos offres", "solution", "nos solutions", "services", "nos services",
    "formule", "abonnement", "devis", "tarifs", "pricing", "pack", "forfait"
]

ANTIBOT_KEYWORDS = [
    "cloudflare", "captcha", "verify you are human", "attention required", "protection"
]

SCRIPT_HEAVY_SIGNALS = [
    "data-reactroot", "window.__NEXT_DATA__", "webpack", "react-refresh", "next-data", "nuxt", "vue"
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"

HEAVY_JS_DOMAINS = [
    "upwork.com", "malt.fr", "fiverr.com", "freelancer.com",
    "toptal.com", "peopleperhour.com", "guru.com", "producthunt.com"
]

def fetch_html(url, timeout=10):
    """
    Rôle :
    Récupère le contenu HTML d'une URL via une requête HTTP.

    Fonctionnalité :
    - Envoie une requête GET à l'URL spécifiée.
    - Retourne la réponse HTTP ou `None` en cas d'erreur.

    Importance :
    Cette fonction est essentielle pour obtenir le contenu HTML brut d'un site web, 
    qui sera ensuite analysé pour détecter ses caractéristiques.

    Arguments :
    - `url` : L'URL du site à scraper.
    - `timeout` : Temps maximum (en secondes) pour la requête.

    Retour :
    Un objet `Response` contenant le contenu HTML ou `None` en cas d'échec.
    """
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        return r
    except requests.RequestException as e:
        logging.warning(f"⚠️ Échec requête GET {url}: {e}")
        return None

def is_static_site(url, keywords=DEFAULT_KEYWORDS):
    """
    Rôle :
    Détermine si un site est statique en recherchant des mots-clés spécifiques dans son contenu HTML.

    Fonctionnalité :
    - Récupère le contenu HTML du site.
    - Analyse le texte brut pour détecter la présence de mots-clés prédéfinis.

    Importance :
    Cette fonction permet de distinguer les sites statiques (faciles à scraper) des sites dynamiques, 
    ce qui aide à choisir la méthode de scraping appropriée.

    Arguments :
    - `url` : L'URL du site à analyser.
    - `keywords` : Une liste de mots-clés à rechercher dans le contenu HTML.

    Retour :
    `True` si le site est statique, sinon `False`.
    """
    resp = fetch_html(url, timeout=8)
    if not resp or resp.status_code != 200:
        return False
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    return any(kw in text for kw in keywords)

def contains_antibot_measures(html: str) -> bool:
    """
    Rôle :
    Détecte la présence de mesures anti-bot dans le contenu HTML.

    Fonctionnalité :
    - Recherche des mots-clés spécifiques aux systèmes anti-bot (ex. CAPTCHA, Cloudflare).

    Importance :
    Cette fonction permet d'identifier les sites qui nécessitent des solutions avancées pour contourner les protections anti-bot.

    Arguments :
    - `html` : Une chaîne de caractères contenant le contenu HTML.

    Retour :
    `True` si des mesures anti-bot sont détectées, sinon `False`.
    """
    text = (html or "").lower()
    return any(word in text for word in ANTIBOT_KEYWORDS)

def detect_novelty_sections(html: str) -> bool:
    """
    Rôle :
    Détecte la présence de sections contenant des nouveautés dans le contenu HTML.

    Fonctionnalité :
    - Recherche des mots-clés associés aux nouveautés (ex. "news", "nouveautés").

    Importance :
    Cette fonction identifie les sections pertinentes pour extraire des informations récentes ou mises à jour.

    Arguments :
    - `html` : Une chaîne de caractères contenant le contenu HTML.

    Retour :
    `True` si des sections de nouveautés sont détectées, sinon `False`.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    return any(nk in text for nk in NOVELTY_KEYWORDS)

def extract_novelty_snippets(html: str, limit: int = 6) -> list:
    """
    Rôle :
    Extrait des extraits textuels contenant des nouveautés à partir du contenu HTML.

    Fonctionnalité :
    - Parcourt les balises HTML pertinentes (ex. `<h1>`, `<p>`) pour trouver des textes contenant des mots-clés de nouveautés.
    - Limite le nombre d'extraits retournés.

    Importance :
    Cette fonction permet de cibler et d'extraire les informations récentes ou mises à jour d'un site web.

    Arguments :
    - `html` : Une chaîne de caractères contenant le contenu HTML.
    - `limit` : Nombre maximum d'extraits à retourner.

    Retour :
    Une liste de chaînes de caractères contenant les extraits textuels.
    """
    snippets = []
    soup = BeautifulSoup(html or "", "html.parser")
    tags = soup.find_all(["h1", "h2", "h3", "p", "li", "section", "div"])
    for tag in tags:
        text = tag.get_text(" ", strip=True)
        if not text or len(text) < 20:
            continue
        if any(nk in text.lower() for nk in NOVELTY_KEYWORDS):
            snippets.append(text)
        if len(snippets) >= limit:
            break
    return snippets

def detect_offres(text: str, limit: int = 10) -> list:
    """
    Rôle :
    Détecte les lignes contenant des offres dans un texte brut.

    Fonctionnalité :
    - Parcourt chaque ligne du texte.
    - Recherche des mots-clés associés aux offres (ex. "services", "tarifs").

    Importance :
    Cette fonction identifie les sections pertinentes pour extraire des informations sur les offres ou services proposés.

    Arguments :
    - `text` : Une chaîne de caractères contenant le texte brut.
    - `limit` : Nombre maximum de lignes à retourner.

    Retour :
    Une liste de chaînes de caractères contenant les lignes pertinentes.
    """
    lines = [l.strip() for l in str(text).splitlines() if l.strip()]
    out = []
    for l in lines:
        if any(k in l.lower() for k in OFFRE_KEYWORDS):
            out.append(l)
        if len(out) >= limit:
            break
    return out

def detect_nouveautes(text: str, limit: int = 10) -> list:
    """
    Rôle :
    Détecte les lignes contenant des nouveautés dans un texte brut.

    Fonctionnalité :
    - Parcourt chaque ligne du texte.
    - Recherche des mots-clés associés aux nouveautés (ex. "nouveautés", "actualités").

    Importance :
    Cette fonction identifie les sections pertinentes pour extraire des informations récentes ou mises à jour.

    Arguments :
    - `text` : Une chaîne de caractères contenant le texte brut.
    - `limit` : Nombre maximum de lignes à retourner.

    Retour :
    Une liste de chaînes de caractères contenant les lignes pertinentes.
    """
    lines = [l.strip() for l in str(text).splitlines() if l.strip()]
    out = []
    for l in lines:
        if any(k in l.lower() for k in NOVELTY_KEYWORDS):
            out.append(l)
        if len(out) >= limit:
            break
    return out

# wrappers used by extractor
def detect_offre_keywords(text: str, limit: int = 10):
    return detect_offres(text, limit)

def detect_nouveaute_keywords(text: str, limit: int = 10):
    return detect_nouveautes(text, limit)

def is_site_empty(html: str, min_length: int = 300) -> bool:
    """
    Rôle :
    Détermine si un site est vide ou contient peu de contenu utile.

    Fonctionnalité :
    - Vérifie la longueur du contenu HTML.
    - Analyse le texte visible pour détecter s'il est en dessous d'un seuil minimal.

    Importance :
    Cette fonction aide à identifier les sites qui n'ont pas de contenu significatif, 
    ce qui peut influencer les étapes suivantes du pipeline.

    Arguments :
    - `html` : Une chaîne de caractères contenant le contenu HTML.
    - `min_length` : Longueur minimale du contenu texte pour qu'un site ne soit pas considéré comme vide.

    Retour :
    `True` si le site est considéré comme vide, sinon `False`.
    """
    if not html or len(html) < min_length:
        return True
    soup = BeautifulSoup(html, "html.parser")
    return len(soup.get_text(" ", strip=True)) < min_length

def analyze_site_features(url: str) -> dict:
    """
    Rôle :
    Analyse les caractéristiques d'un site web donné.

    Fonctionnalité :
    - Récupère le contenu HTML du site.
    - Évalue diverses propriétés : statique/dynamique, présence de mesures anti-bot, sections de nouveautés, etc.

    Importance :
    Cette fonction fournit une vue d'ensemble des caractéristiques d'un site, 
    essentielle pour adapter les stratégies de scraping et d'analyse.

    Arguments :
    - `url` : L'URL du site à analyser.

    Retour :
    Un dictionnaire contenant les caractéristiques détectées du site.
    """
    r = fetch_html(url)
    res = {"url": url, "is_static": False, "has_antibot": False, "has_novelty": False, "novelty_snippets": [], "is_empty": True, "status_code": None}
    if not r:
        return res
    res["status_code"] = r.status_code
    if r.status_code != 200:
        return res
    html = r.text
    res["has_antibot"] = contains_antibot_measures(html)
    res["has_novelty"] = detect_novelty_sections(html)
    res["novelty_snippets"] = extract_novelty_snippets(html)
    res["is_empty"] = is_site_empty(html)
    res["is_static"] = is_static_site(url)
    return res

def detect_heavy_js(url: str, timeout: int = 6) -> bool:
    """
    Rôle :
    Détecte si un site utilise fortement JavaScript ou est une application monopage (SPA).

    Fonctionnalité :
    - Vérifie si le domaine appartient à une liste connue de sites lourds en JavaScript.
    - Recherche des indicateurs spécifiques de SPA dans le contenu HTML.
    - Analyse la quantité de texte visible par rapport au nombre de balises `<script>`.

    Importance :
    Cette fonction aide à identifier les sites nécessitant une approche de scraping dynamique (ex. Selenium).

    Arguments :
    - `url` : L'URL du site à analyser.
    - `timeout` : Temps maximum (en secondes) pour la requête.

    Retour :
    `True` si le site est lourd en JavaScript, sinon `False`.
    """
    try:
        domain = re.sub(r"^https?://", "", url).split("/")[0].lower()
        if any(d in domain for d in HEAVY_JS_DOMAINS):
            logging.info(f"⚠️ {domain} detected as heavy-JS (whitelist).")
            return True

        r = fetch_html(url, timeout=timeout)
        if not r or r.status_code != 200:
            return False
        html = r.text.lower()
        if any(sig in html for sig in SCRIPT_HEAVY_SIGNALS):
            logging.info(f"⚠️ {domain} contains SPA markers.")
            return True

        soup = BeautifulSoup(html, "html.parser")
        text_len = len(soup.get_text(" ", strip=True))
        scripts = soup.find_all("script")
        external_scripts = [s for s in scripts if s.get("src")]
        if text_len < 300 and (len(scripts) > 10 or len(external_scripts) > 4):
            logging.info(f"⚠️ {domain} low text ({text_len}) + many scripts -> heavy.")
            return True
        if len(scripts) > 25:
            logging.info(f"⚠️ {domain} many script tags -> heavy.")
            return True

    except Exception as e:
        logging.warning(f"detect_heavy_js error for {url}: {e}")
    return False
