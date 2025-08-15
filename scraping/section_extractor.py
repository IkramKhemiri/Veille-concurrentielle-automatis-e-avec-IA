# scraping/section_extractor.py
# Ce module extrait des sections spécifiques d'un site web (services, blog, etc.) selon des mots-clés.

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

def clean_url(href, base_url):
    """
    Nettoie et complète les URLs relatives.
    """
    url = urljoin(base_url, href)
    url = url.split("#")[0].split("?")[0]  # Remove fragments and query params
    return url.strip("/")

def is_valid_section_url(url, keywords):
    """
    Vérifie si l'URL contient l'un des mots-clés recherchés.
    """
    parsed = urlparse(url.lower())
    if any(kw in parsed.path for kw in keywords):
        return not any(social in url for social in [
            "facebook", "linkedin", "instagram", "twitter", "mailto", "tel", "privacy", "terms"
        ])
    return False

def extract_title(soup):
    """
    Essaie d'extraire un titre pertinent de la page.
    """
    for tag in soup.find_all(['h1', 'h2']):
        txt = tag.get_text(strip=True)
        if 5 < len(txt) < 100:
            return txt
    return ""

def extract_sections_with_content(base_url, soup, keywords, max_links=3):
    sections = []
    visited = set()

    headers = {"User-Agent": "Mozilla/5.0"}
    links = soup.find_all("a", href=True)

    for link in links:
        href = link.get("href")
        if not href or href.startswith("javascript:") or href.startswith("#"):
            continue

        full_url = clean_url(href, base_url)
        if full_url in visited or not is_valid_section_url(full_url, keywords):
            continue

        try:
            response = requests.get(full_url, timeout=6, headers=headers)
            response.raise_for_status()
            sub_soup = BeautifulSoup(response.text, "html.parser")
            text = sub_soup.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)

            if len(text) >= 100:
                section_data = {
                    "url": full_url,
                    "title": extract_title(sub_soup),
                    "content": text[:2000]  # Limite le résumé
                }
                sections.append(section_data)
                visited.add(full_url)

            if len(sections) >= max_links:
                break

        except Exception as e:
            print(f"⚠️] Erreur en visitant {full_url} : {e}")
            continue

    return sections