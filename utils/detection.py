# utils/detection.py
import requests
from bs4 import BeautifulSoup
import logging
import re

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
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        return r
    except requests.RequestException as e:
        logging.warning(f"⚠️ Échec requête GET {url}: {e}")
        return None

def is_static_site(url, keywords=DEFAULT_KEYWORDS):
    resp = fetch_html(url, timeout=8)
    if not resp or resp.status_code != 200:
        return False
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    return any(kw in text for kw in keywords)

def contains_antibot_measures(html: str) -> bool:
    text = (html or "").lower()
    return any(word in text for word in ANTIBOT_KEYWORDS)

def detect_novelty_sections(html: str) -> bool:
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    return any(nk in text for nk in NOVELTY_KEYWORDS)

def extract_novelty_snippets(html: str, limit: int = 6) -> list:
    snippets = []
    soup = BeautifulSoup(html or "", "html.parser")
    tags = soup.find_all(["h1","h2","h3","p","li","section","div"])
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
    lines =[l.strip() for l in str(text).splitlines() if l.strip()]
    out=[]
    for l in lines:
        if any(k in l.lower() for k in OFFRE_KEYWORDS):
            out.append(l)
        if len(out)>=limit:
            break
    return out

def detect_nouveautes(text: str, limit: int = 10) -> list:
    lines =[l.strip() for l in str(text).splitlines() if l.strip()]
    out=[]
    for l in lines:
        if any(k in l.lower() for k in NOVELTY_KEYWORDS):
            out.append(l)
        if len(out)>=limit:
            break
    return out

# wrappers used by extractor
def detect_offre_keywords(text: str, limit: int = 10):
    return detect_offres(text, limit)

def detect_nouveaute_keywords(text: str, limit: int = 10):
    return detect_nouveautes(text, limit)

def is_site_empty(html: str, min_length: int = 300) -> bool:
    if not html or len(html) < min_length:
        return True
    soup = BeautifulSoup(html, "html.parser")
    return len(soup.get_text(" ", strip=True)) < min_length

def analyze_site_features(url: str) -> dict:
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
    Heuristic detection of JS-heavy / SPA sites:
    - domain whitelist check
    - presence of SPA markers (next/nuxt/react)
    - low visible text with many <script> tags
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
        # SPA indicators
        if any(sig in html for sig in SCRIPT_HEAVY_SIGNALS):
            logging.info(f"⚠️ {domain} contains SPA markers.")
            return True

        soup = BeautifulSoup(html, "html.parser")
        text_len = len(soup.get_text(" ", strip=True))
        scripts = soup.find_all("script")
        external_scripts = [s for s in scripts if s.get("src")]
        # heuristic rules
        if text_len < 300 and (len(scripts) > 10 or len(external_scripts) > 4):
            logging.info(f"⚠️ {domain} low text ({text_len}) + many scripts -> heavy.")
            return True
        if len(scripts) > 25:
            logging.info(f"⚠️ {domain} many script tags -> heavy.")
            return True

    except Exception as e:
        logging.warning(f"detect_heavy_js error for {url}: {e}")
    return False
