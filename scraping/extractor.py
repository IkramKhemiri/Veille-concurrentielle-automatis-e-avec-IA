# scraping/extractor.py
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from scraping.cleaner import clean_text_blocks, nettoyer_texte
from scraping.text_classifier import classify_block
from utils.detection import detect_offre_keywords, detect_nouveaute_keywords

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{1,4}\)?[\s\-\.]?)?\d{3,5}[\s\-\.]?\d{3,5}\b")

FORBIDDEN_SNIPPETS = [
    "cookie", "terms", "privacy", "login", "sign in", "sign up", "subscribe",
    "linkedin", "facebook", "twitter", "instagram", "©", "all rights reserved"
]

def _unique_list(seq):
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
    Extraction permissive : capture titres/meta/alt/liens/paragraphes + raw_text.
    Retourne sections listées et raw_text brut.
    """
    soup = BeautifulSoup(html or "", "html.parser")

    # Title & meta description
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    metas = {}
    for m in soup.find_all("meta"):
        key = (m.get("name") or m.get("property") or "").lower()
        if m.get("content") and key:
            metas[key] = m.get("content").strip()
    description = metas.get("description") or metas.get("og:description") or ""

    # Collect raw blocks from many tags (permissive)
    raw_blocks = []
    seen = set()
    tags_to_scan = ["h1","h2","h3","h4","p","li","article","section","div","span","td","blockquote"]
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

    # image alt texts
    for img in soup.find_all("img"):
        alt = (img.get("alt") or "").strip()
        if alt and len(alt.split()) >= 2:
            k = alt.lower()
            if k not in seen:
                seen.add(k)
                raw_blocks.append(alt)

    # link texts (useful)
    for a in soup.find_all("a"):
        tx = a.get_text(" ", strip=True)
        if tx and len(tx.split()) >= 2:
            k = tx.lower()
            if k not in seen:
                seen.add(k)
                raw_blocks.append(tx)

    merged_text = "\n".join(raw_blocks)
    cleaned_text = clean_text_blocks(merged_text)
    cleaned_blocks = [b.strip() for b in cleaned_text.splitlines() if b.strip()]

    # Initialize sections
    sections = {
        "slogan": [], "summary": [], "services": [], "clients": [], "blog": [],
        "jobs": [], "technologies": [], "emails": [], "phones": [], "offres": [], "nouveautes": []
    }

    # Classify using existing classifier, otherwise heuristics
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
            elif any(k in low for k in ["python","java","javascript","react","node","django","flask","aws","azure"]):
                sections["technologies"].append(block)
            else:
                # if long, treat as potential service/presentation
                if len(block.split()) > 8:
                    sections["services"].append(block)

    # Emails & phones from both merged_text and raw HTML (more recall)
    emails = EMAIL_RE.findall((html or "") + "\n" + merged_text)
    phones = PHONE_RE.findall((html or "") + "\n" + merged_text)
    emails = _unique_list([e.lower() for e in emails])
    # normalize phones
    phones = _unique_list([re.sub(r"[^\d\+]", "", p) for p in phones])

    sections["emails"] = emails
    sections["phones"] = phones

    # Offres / nouveautes detections via utils
    offres = detect_offre_keywords(merged_text)
    nouveautes = detect_nouveaute_keywords(merged_text)
    if offres:
        sections["offres"].extend(offres)
    if nouveautes:
        sections["nouveautes"].extend(nouveautes)

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
