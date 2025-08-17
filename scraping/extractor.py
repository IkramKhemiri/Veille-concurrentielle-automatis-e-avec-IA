"""
Rôle global :
Ce module est conçu pour extraire et organiser les données textuelles pertinentes à partir du contenu HTML d'une page web. 
Il identifie les sections importantes (services, clients, technologies, etc.), extrait les emails et numéros de téléphone, 
et nettoie les données pour les rendre exploitables.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle essentiel en transformant 
le contenu brut d'une page web en données structurées et prêtes à être analysées. Les pages web contiennent souvent beaucoup 
de bruit (liens inutiles, phrases génériques, etc.), et ce module permet de filtrer ces éléments pour ne conserver que les informations pertinentes.

Comment il aide dans le pipeline :
- **Scraping** : Il traite le contenu HTML brut extrait d'une page web.
- **Analyse** : Il organise les données en sections thématiques pour faciliter leur analyse.
- **Visualisation** : Les données structurées peuvent être utilisées pour créer des graphiques ou des tableaux.
- **Rapport** : Les informations extraites sont prêtes à être intégrées dans des rapports professionnels.

Technologies utilisées :
- **BeautifulSoup** : Pour analyser et extraire le contenu HTML.
- **Expressions régulières (regex)** : Pour détecter et extraire des motifs spécifiques comme les emails et les numéros de téléphone.
- **Heuristiques** : Pour classer les blocs de texte en catégories pertinentes.
- **Nettoyage de texte** : Utilise des fonctions de nettoyage pour éliminer le bruit et normaliser les données.
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scraping.cleaner import clean_text_blocks, nettoyer_texte
from scraping.text_classifier import classify_block
from utils.detection import detect_offre_keywords, detect_nouveaute_keywords

# Expressions régulières pour détecter les emails et numéros de téléphone
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{1,4}\)?[\s\-\.]?)?\d{3,5}[\s\-\.]?\d{3,5}\b")

# Liste de snippets interdits (liens ou phrases inutiles)
FORBIDDEN_SNIPPETS = [
    "cookie", "terms", "privacy", "login", "sign in", "sign up", "subscribe",
    "linkedin", "facebook", "twitter", "instagram", "©", "all rights reserved"
]

def _unique_list(seq):
    """
    Rôle :
    Supprime les doublons d'une liste tout en conservant l'ordre des éléments.

    Fonctionnalité :
    - Parcourt les éléments de la liste.
    - Élimine les doublons en utilisant un ensemble pour suivre les éléments déjà vus.

    Importance :
    Cette fonction garantit que les données extraites ne contiennent pas de répétitions inutiles, 
    ce qui est essentiel pour produire des résultats propres et cohérents.

    Arguments :
    - `seq` : Une liste d'éléments.

    Retour :
    Une liste sans doublons.
    """
    seen = set()
    out = []
    for x in seq:
        k = (x or "").strip()
        if not k:
            continue
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out

def extract_all(html: str, base_url: str) -> dict:
    """
    Rôle :
    Extrait et organise les données textuelles pertinentes à partir du contenu HTML d'une page web.

    Fonctionnalité :
    - Analyse le contenu HTML pour extraire les titres, descriptions, blocs de texte, liens et images.
    - Nettoie et classe les blocs de texte en sections thématiques (services, clients, technologies, etc.).
    - Extrait les emails et numéros de téléphone à l'aide d'expressions régulières.
    - Détecte les offres et nouveautés à l'aide de mots-clés spécifiques.

    Importance :
    Cette fonction est essentielle pour transformer le contenu brut d'une page web en données structurées et exploitables. 
    Elle garantit que les informations importantes sont extraites et organisées de manière cohérente.

    Arguments :
    - `html` : Une chaîne de caractères contenant le contenu HTML de la page.
    - `base_url` : L'URL de base pour associer les liens extraits.

    Retour :
    Un dictionnaire contenant les sections thématiques, les emails, les numéros de téléphone et d'autres informations pertinentes.
    """
    soup = BeautifulSoup(html or "", "html.parser")

    # Extraction du titre et de la description meta
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    metas = {}
    for m in soup.find_all("meta"):
        key = (m.get("name") or m.get("property") or "").lower()
        if m.get("content") and key:
            metas[key] = m.get("content").strip()
    description = metas.get("description") or metas.get("og:description") or ""

    # Collecte des blocs de texte brut à partir de plusieurs balises HTML
    raw_blocks = []
    seen = set()
    tags_to_scan = ["h1", "h2", "h3", "h4", "p", "li", "article", "section", "div", "span", "td", "blockquote"]
    for tag_name in tags_to_scan:
        for node in soup.find_all(tag_name):
            text = node.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            raw_blocks.append(text)

    # Extraction des textes alternatifs des images
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        if alt and len(alt.split()) >= 2:
            k = alt.lower()
            if k not in seen:
                seen.add(k)
                raw_blocks.append(alt)

    # Extraction des textes des liens
    for a in soup.find_all("a"):
        tx = a.get_text(" ", strip=True)
        if tx and len(tx.split()) >= 2:
            k = tx.lower()
            if k not in seen:
                seen.add(k)
                raw_blocks.append(tx)

    # Nettoyage des blocs de texte
    merged_text = "\n".join(raw_blocks)
    cleaned_text = clean_text_blocks(merged_text)
    cleaned_blocks = [b.strip() for b in cleaned_text.splitlines() if b.strip()]

    # Initialisation des sections thématiques
    sections = {
        "slogan": [], "summary": [], "services": [], "clients": [], "blog": [],
        "jobs": [], "technologies": [], "emails": [], "phones": [], "offres": [], "nouveautes": []
    }

    # Classification des blocs de texte
    for block in cleaned_blocks:
        cat = classify_block(block)
        if cat in sections:
            sections[cat].append(block)
        else:
            low = block.lower()
            if len(block.split()) <= 8 and not sections["slogan"]:
                sections["slogan"].append(block)
            elif any(k in low for k in ["service", "solution", "produit", "what we do", "nos services"]):
                sections["services"].append(block)
            elif any(k in low for k in ["client", "nos clients", "référence", "portfolio", "they trust"]):
                sections["clients"].append(block)
            elif any(k in low for k in ["blog", "article", "news", "actualité"]):
                sections["blog"].append(block)
            elif any(k in low for k in ["job", "career", "recrut", "poste", "emploi"]):
                sections["jobs"].append(block)
            elif any(k in low for k in ["python", "java", "javascript", "react", "node", "django", "flask", "aws", "azure"]):
                sections["technologies"].append(block)
            else:
                if len(block.split()) > 8:
                    sections["services"].append(block)

    # Extraction des emails et numéros de téléphone
    emails = EMAIL_RE.findall((html or "") + "\n" + merged_text)
    phones = PHONE_RE.findall((html or "") + "\n" + merged_text)
    emails = _unique_list([e.lower() for e in emails])
    phones = _unique_list([re.sub(r"[^\d\+]", "", p) for p in phones])

    sections["emails"] = emails
    sections["phones"] = phones

    # Détection des offres et nouveautés
    offres = detect_offre_keywords(merged_text)
    nouveautes = detect_nouveaute_keywords(merged_text)
    if offres:
        sections["offres"].extend(offres)
    if nouveautes:
        sections["nouveautes"].extend(nouveautes)

    # Conversion des sections en format structuré
    def to_items(lst):
        return [{"url": base_url, "content": x} for x in _unique_list(lst)]

    result = {
        "title": title,
        "meta_description": description,
        "raw_text": merged_text or (html or ""),
        "slogan": sections["slogan"][0] if sections["slogan"] else "",
        "summary": sections["summary"][0] if sections["summary"] else description or "",
        "services": to_items(sections["services"]),
        "clients": to_items(sections["clients"]),
        "technologies": to_items(sections["technologies"]),
        "blog": to_items(sections["blog"]),
        "jobs": to_items(sections["jobs"]),
        "emails": sections["emails"],
        "phones": sections["phones"],
        "offres": to_items(sections["offres"]),
        "nouveautes": to_items(sections["nouveautes"]),
        "location": ""
    }
    return result
