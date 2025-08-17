# scraping/section_extractor.py
"""
Rôle global :
Ce module est conçu pour extraire des sections spécifiques d'un site web (comme les services, le blog, etc.) en se basant sur des mots-clés. 
Il identifie les liens pertinents sur une page, visite ces liens, et extrait leur contenu textuel ainsi que leurs titres.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle essentiel en isolant les sections clés 
d'un site web. Ces sections contiennent souvent des informations importantes qui doivent être analysées ou visualisées. 
Sans cette étape, il serait difficile de cibler et d'extraire les parties pertinentes d'un site web.

Comment il aide dans le pipeline :
- **Scraping** : Identifie et extrait les sections pertinentes d'un site web.
- **Analyse** : Fournit des données textuelles organisées pour une analyse approfondie.
- **Visualisation** : Les sections extraites peuvent être utilisées pour créer des graphiques ou des tableaux spécifiques.
- **Rapport** : Les informations extraites sont prêtes à être intégrées dans des rapports professionnels.

Technologies utilisées :
- **Requests** : Pour envoyer des requêtes HTTP et récupérer le contenu HTML des pages liées.
- **BeautifulSoup** : Pour analyser et extraire les données textuelles des pages HTML.
- **Expressions régulières (regex)** : Pour nettoyer et normaliser le contenu textuel.
- **URL Parsing** : Pour gérer et nettoyer les URLs relatives ou absolues.
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

def clean_url(href, base_url):
    """
    Rôle :
    Nettoie et complète les URLs relatives pour les transformer en URLs absolues.

    Fonctionnalité :
    - Combine l'URL de base avec l'URL relative pour obtenir une URL absolue.
    - Supprime les fragments (#) et les paramètres de requête (?) pour simplifier l'URL.

    Importance :
    Cette fonction garantit que toutes les URLs extraites sont valides et prêtes à être utilisées pour des requêtes HTTP.

    Arguments :
    - `href` : L'URL relative ou absolue extraite d'une page.
    - `base_url` : L'URL de base du site web.

    Retour :
    Une URL absolue nettoyée.
    """
    url = urljoin(base_url, href)
    url = url.split("#")[0].split("?")[0]  # Supprime les fragments et les paramètres de requête
    return url.strip("/")

def is_valid_section_url(url, keywords):
    """
    Rôle :
    Vérifie si une URL est pertinente en fonction des mots-clés spécifiés.

    Fonctionnalité :
    - Analyse le chemin de l'URL pour détecter la présence de mots-clés.
    - Exclut les URLs associées à des réseaux sociaux, des emails, ou des pages génériques comme "privacy" ou "terms".

    Importance :
    Cette fonction filtre les URLs pour ne conserver que celles qui sont susceptibles de contenir des sections pertinentes.

    Arguments :
    - `url` : L'URL à vérifier.
    - `keywords` : Une liste de mots-clés à rechercher dans l'URL.

    Retour :
    `True` si l'URL est pertinente, sinon `False`.
    """
    parsed = urlparse(url.lower())
    if any(kw in parsed.path for kw in keywords):
        return not any(social in url for social in [
            "facebook", "linkedin", "instagram", "twitter", "mailto", "tel", "privacy", "terms"
        ])
    return False

def extract_title(soup):
    """
    Rôle :
    Extrait un titre pertinent de la page en analysant les balises HTML.

    Fonctionnalité :
    - Recherche les balises `<h1>` et `<h2>` pour trouver un titre.
    - Retourne le premier titre trouvé qui respecte une longueur raisonnable.

    Importance :
    Cette fonction permet d'identifier rapidement le sujet principal d'une page, ce qui est utile pour organiser les données extraites.

    Arguments :
    - `soup` : Un objet BeautifulSoup représentant le contenu HTML de la page.

    Retour :
    Une chaîne de caractères contenant le titre extrait, ou une chaîne vide si aucun titre pertinent n'est trouvé.
    """
    for tag in soup.find_all(['h1', 'h2']):
        txt = tag.get_text(strip=True)
        if 5 < len(txt) < 100:  # Vérifie que le titre a une longueur raisonnable
            return txt
    return ""

def extract_sections_with_content(base_url, soup, keywords, max_links=3):
    """
    Rôle :
    Extrait les sections pertinentes d'une page web en suivant les liens contenant des mots-clés.

    Fonctionnalité :
    - Parcourt tous les liens de la page pour identifier ceux qui contiennent des mots-clés pertinents.
    - Visite chaque lien pertinent, extrait le contenu textuel et le titre de la page liée.
    - Limite le nombre de sections extraites pour éviter une surcharge.

    Importance :
    Cette fonction permet de cibler et d'extraire les sections importantes d'un site web, comme les services ou les articles de blog, 
en se basant sur des mots-clés.

    Arguments :
    - `base_url` : L'URL de base du site web.
    - `soup` : Un objet BeautifulSoup représentant le contenu HTML de la page.
    - `keywords` : Une liste de mots-clés à rechercher dans les URLs.
    - `max_links` : Le nombre maximum de sections à extraire.

    Retour :
    Une liste de dictionnaires contenant les informations extraites pour chaque section (URL, titre, contenu).
    """
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

            if len(text) >= 100:  # Vérifie que le contenu est suffisamment long
                section_data = {
                    "url": full_url,
                    "title": extract_title(sub_soup),
                    "content": text[:2000]  # Limite le contenu à 2000 caractères
                }
                sections.append(section_data)
                visited.add(full_url)

            if len(sections) >= max_links:  # Arrête si le nombre maximum de sections est atteint
                break

        except Exception as e:
            print(f"⚠️ Erreur en visitant {full_url} : {e}")
            continue

    return sections
