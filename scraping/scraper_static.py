"""
Rôle global :
Ce module est conçu pour scraper des sites web statiques, c'est-à-dire des sites dont le contenu est directement accessible via des requêtes HTTP. 
Il extrait les données pertinentes à partir du HTML brut et gère également la pagination pour collecter des informations sur plusieurs pages.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module est essentiel pour traiter les sites statiques, 
qui représentent une part importante du web. Il permet de collecter rapidement et efficacement des données exploitables sans nécessiter 
de rendu JavaScript.

Comment il aide dans le pipeline :
- **Scraping** : Il extrait le contenu HTML brut des sites statiques.
- **Analyse** : Les données extraites sont nettoyées et organisées pour être analysées dans les étapes suivantes.
- **Visualisation** : Les informations collectées peuvent être utilisées pour créer des graphiques ou des tableaux.
- **Rapport** : Les données structurées sont prêtes à être intégrées dans des rapports professionnels.

Technologies utilisées :
- **Requests** : Pour envoyer des requêtes HTTP et récupérer le contenu HTML des pages.
- **BeautifulSoup** : Pour analyser et extraire les données textuelles des pages HTML.
- **Expressions régulières (regex)** : Pour détecter et extraire des motifs spécifiques comme les emails et les numéros de téléphone.
- **Logging** : Pour suivre les étapes du processus et gérer les erreurs de manière transparente.
"""

import logging
import requests
from scraping.extractor import extract_all
from scraping.cleaner import clean_extracted_data
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def get_static_html(url, timeout=10):
    """
    Rôle :
    Récupère le contenu HTML brut d'un site web statique via une requête HTTP.

    Fonctionnalité :
    - Envoie une requête HTTP GET à l'URL spécifiée.
    - Retourne le contenu HTML si la requête est réussie.
    - Gère les erreurs et les statuts HTTP non 200.

    Importance :
    Cette fonction est idéale pour scraper des sites statiques qui ne nécessitent pas de rendu JavaScript. 
    Elle est rapide et consomme moins de ressources qu'un navigateur automatisé.

    Arguments :
    - `url` : L'URL du site à scraper.
    - `timeout` : Temps maximum (en secondes) pour la requête.

    Retour :
    Une chaîne de caractères contenant le HTML brut ou une chaîne vide en cas d'erreur.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.text
        else:
            logging.warning(f"⚠️ Erreur HTTP {response.status_code} pour {url}")
            return ""
    except Exception as e:
        logging.warning(f"⚠️ Erreur get_static_html : {e}")
        return ""

def is_empty(data):
    """
    Rôle :
    Vérifie si les données extraites sont vides ou non pertinentes.

    Fonctionnalité :
    - Parcourt les sections clés des données extraites (services, clients, blog, etc.).
    - Retourne `True` si toutes les sections sont vides ou non significatives.

    Importance :
    Cette fonction permet de détecter rapidement si le scraping a échoué ou si les données extraites sont inutilisables.

    Arguments :
    - `data` : Un dictionnaire contenant les données extraites.

    Retour :
    `True` si les données sont vides, sinon `False`.
    """
    if not data or not isinstance(data, dict):
        return True
    for key in ["services", "clients", "blog", "jobs", "summary"]:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return False
        elif isinstance(val, list) and any(str(x).strip() for x in val):
            return False
    return True

def merge_results(results):
    """
    Rôle :
    Fusionne les résultats extraits de plusieurs pages en un seul ensemble de données.

    Fonctionnalité :
    - Combine les données extraites en unifiant les listes et en conservant les valeurs uniques.

    Importance :
    Cette fonction est cruciale pour obtenir un ensemble de données complet et non dupliqué à partir de plusieurs pages.

    Arguments :
    - `results` : Liste des blocs de résultats extraits.

    Retour :
    Un dictionnaire contenant les données fusionnées.
    """
    merged = {}
    for block in results:
        for key, val in block.items():
            if isinstance(val, list):
                merged.setdefault(key, []).extend(val)
            elif isinstance(val, str):
                if not merged.get(key):
                    merged[key] = val
    return merged

def update_url_param(url, param_name, param_value):
    parts = urlparse(url)
    query = parse_qs(parts.query)
    query[param_name] = [str(param_value)]
    new_query = urlencode(query, doseq=True)
    new_parts = parts._replace(query=new_query)
    return urlunparse(new_parts)

def try_paginate(url):
    """
    Rôle :
    Gère la pagination pour collecter des données sur plusieurs pages d'un site statique.

    Fonctionnalité :
    - Modifie les paramètres de l'URL pour accéder aux pages suivantes.
    - Extrait les données de chaque page et les fusionne.

    Importance :
    Cette méthode est essentielle pour scraper des sites statiques avec plusieurs pages de contenu.

    Arguments :
    - `url` : L'URL de base pour la pagination.

    Retour :
    Un dictionnaire contenant les données fusionnées de toutes les pages.
    """
    logging.info("🔁 Pagination intelligente activée...")
    results = []
    seen_urls = set()
    seen_contents = set()
    
    param_names = ["page", "p", "start", "offset"]
    current_page = 1
    stop = False

    while not stop:
        stop = True
        for param in param_names:
            paginated_url = update_url_param(url, param, current_page)
            if paginated_url in seen_urls:
                continue

            logging.info(f"📄 Scraping page {current_page} via param `{param}` : {paginated_url}")
            try:
                html = get_static_html(paginated_url)
                if not html or len(html) < 100:
                    continue

                html_clean = clean_extracted_data(html)
                data = extract_all(html_clean, paginated_url)

                content_signature = str(data)
                if is_empty(data) or content_signature in seen_contents:
                    continue

                seen_contents.add(content_signature)
                seen_urls.add(paginated_url)
                results.append(data)
                stop = False

            except Exception as e:
                logging.warning(f"⚠️ Erreur pagination sur {paginated_url}: {str(e)}")

        current_page += 1
        if current_page > 50:
            logging.warning("⚠️ Arrêt forcé à 50 pages pour éviter boucle infinie")
            break

    return merge_results(results)

def scrape_static_site(url: str) -> dict:
    """
    Rôle :
    Point d'entrée principal pour le scraping des sites statiques.

    Fonctionnalité :
    - Récupère le contenu HTML brut d'une page.
    - Extrait les données pertinentes et gère la pagination si nécessaire.
    - Nettoie et structure les données extraites.

    Importance :
    Cette fonction orchestre l'ensemble du processus de scraping statique, garantissant que les données collectées sont exploitables.

    Arguments :
    - `url` : L'URL du site à scraper.

    Retour :
    Un dictionnaire contenant les données extraites ou un message d'erreur en cas d'échec.
    """
    logging.info(f"🌐 Scraping statique pour : {url}")

    try:
        html = get_static_html(url)
        if not html or len(html) < 100:
            raise ValueError("❌ HTML trop court ou vide")

        html_clean = clean_extracted_data(html)
        first_data = extract_all(html_clean, base_url=url)

        paginated_results = try_paginate(url)
        all_results = merge_results([first_data, paginated_results])

        for key in ["summary", "slogan", "location"]:
            if key in all_results and isinstance(all_results[key], str):
                all_results[key] = clean_extracted_data(all_results[key])

        if is_empty(all_results):
            raise ValueError("❌ Contenu vide ou sans valeur après extraction")

        return {
            "success": True,
            "url": url,
            "data": all_results
        }

    except Exception as e:
        logging.error(f"⛔ Erreur finale sur {url}: {e}")
        return {
            "success": False,
            "url": url,
            "error": str(e)
        }
