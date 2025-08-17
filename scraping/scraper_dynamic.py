"""
Rôle global :
Ce module est conçu pour scraper des sites web dynamiques, c'est-à-dire des sites dont le contenu est généré ou modifié par JavaScript. 
Il utilise Selenium pour simuler un navigateur, interagir avec les pages, et extraire les données pertinentes. 
Il gère également des scénarios complexes comme la pagination, le défilement infini et les interactions avec des boutons.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module est essentiel pour traiter les sites dynamiques 
qui ne peuvent pas être scrappés avec des requêtes HTTP simples. Ces sites représentent une grande partie du web moderne, 
et ce module permet de contourner les limitations techniques pour accéder aux données nécessaires.

Comment il aide dans le pipeline :
- **Scraping** : Il extrait le contenu HTML complet des sites dynamiques, y compris les données générées par JavaScript.
- **Analyse** : Les données extraites sont nettoyées et organisées pour être analysées dans les étapes suivantes.
- **Visualisation** : Les informations collectées peuvent être utilisées pour créer des graphiques ou des tableaux.
- **Rapport** : Les données structurées sont prêtes à être intégrées dans des rapports professionnels.

Technologies utilisées :
- **Selenium** : Pour simuler un navigateur et interagir avec les sites dynamiques.
- **BeautifulSoup** : Pour analyser et extraire les données textuelles des pages HTML.
- **Expressions régulières (regex)** : Pour détecter et extraire des motifs spécifiques comme les emails et les numéros de téléphone.
- **Logging** : Pour suivre les étapes du processus et gérer les erreurs de manière transparente.
"""

import time
import logging
import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from selenium.common.exceptions import (
    WebDriverException, NoSuchElementException, ElementClickInterceptedException
)
from selenium.webdriver.common.by import By

from scraping.browser import get_driver
from scraping.extractor import extract_all
from scraping.cleaner import clean_extracted_data
from analyse.analyseur_semantique import analyse_semantique_site
from utils.detection import detect_heavy_js
from scraping.scraper_static import scrape_static_site

MAX_DYNAMIC_SECONDS = 120  # Limite max en secondes pour le scraping dynamique

def open_with_retry(driver, url, retries=3, wait_sec=4):
    """
    Rôle :
    Tente de charger une URL dans le navigateur avec plusieurs essais en cas d'échec.

    Fonctionnalité :
    - Charge l'URL dans le navigateur.
    - Réessaie jusqu'à un nombre maximum de tentatives en cas d'erreur.

    Importance :
    Cette fonction garantit une meilleure résilience face aux erreurs réseau ou aux problèmes temporaires du site.

    Arguments :
    - `driver` : Instance du navigateur Selenium.
    - `url` : L'URL à charger.
    - `retries` : Nombre maximum de tentatives.
    - `wait_sec` : Temps d'attente entre les tentatives.

    Retour :
    `True` si le chargement réussit, sinon une exception est levée.
    """
    for attempt in range(retries):
        try:
            driver.get(url)
            return True
        except WebDriverException as e:
            logging.warning(f"🌐 Tentative {attempt+1}/{retries} échouée pour {url} : {str(e)}")
            time.sleep(wait_sec)
    raise Exception(f"Impossible de charger {url} après {retries} tentatives")

def scroll_to_bottom(driver, pause_time=2, max_scrolls=6):
    """
    Rôle :
    Simule un défilement vers le bas de la page pour charger dynamiquement le contenu.

    Fonctionnalité :
    - Défile progressivement jusqu'à la fin de la page.
    - Arrête le défilement si la hauteur de la page ne change plus.

    Importance :
    Cette fonction est essentielle pour charger les contenus dynamiques qui apparaissent uniquement après un défilement.

    Arguments :
    - `driver` : Instance du navigateur Selenium.
    - `pause_time` : Temps d'attente entre chaque défilement.
    - `max_scrolls` : Nombre maximum de défilements.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def update_url_param(url, param_name, param_value):
    """
    Rôle :
    Modifie un paramètre dans l'URL pour gérer la pagination via des paramètres.

    Fonctionnalité :
    - Analyse l'URL et met à jour le paramètre spécifié.
    - Reconstruit l'URL avec le nouveau paramètre.

    Importance :
    Cette fonction est utile pour gérer la pagination basée sur des paramètres dans l'URL.

    Arguments :
    - `url` : L'URL à modifier.
    - `param_name` : Nom du paramètre à mettre à jour.
    - `param_value` : Nouvelle valeur du paramètre.

    Retour :
    Une URL mise à jour.
    """
    parts = urlparse(url)
    query = parse_qs(parts.query)
    query[param_name] = [str(param_value)]
    new_query = urlencode(query, doseq=True)
    new_parts = parts._replace(query=new_query)
    return urlunparse(new_parts)

def try_url_parameter_pagination(driver, base_url, start_time):
    """
    Rôle :
    Gère la pagination en modifiant les paramètres de l'URL.

    Fonctionnalité :
    - Parcourt les pages en incrémentant les paramètres de l'URL.
    - Extrait les données de chaque page.

    Importance :
    Cette méthode est utile pour scraper des sites qui utilisent des paramètres d'URL pour la pagination.

    Arguments :
    - `driver` : Instance du navigateur Selenium.
    - `base_url` : URL de base pour la pagination.
    - `start_time` : Heure de début pour limiter la durée du scraping.

    Retour :
    Une liste de données extraites des pages paginées.
    """
    logging.info("🔁 Tentative pagination via paramètres URL")
    seen_pages = set()
    contents = []
    page_num = 2
    param_names = ["page", "p", "start", "offset"]
    seen_hashes = set()

    while page_num <= 50:
        if time.time() - start_time > MAX_DYNAMIC_SECONDS:
            logging.warning("⏱️ Temps limite atteint, arrêt pagination paramètres")
            break
        stop = True
        for param in param_names:
            if time.time() - start_time > MAX_DYNAMIC_SECONDS:
                break
            paginated_url = update_url_param(base_url, param, page_num)
            if paginated_url in seen_pages:
                continue
            seen_pages.add(paginated_url)
            try:
                driver.get(paginated_url)
                time.sleep(2)
                scroll_to_bottom(driver)
                html = driver.page_source
                if not html or len(html) < 100:
                    continue
                html_clean = clean_extracted_data(html)
                data = extract_all(html_clean, paginated_url)
                if not data or str(data) in seen_hashes:
                    continue
                seen_hashes.add(str(data))
                contents.append(data)
                stop = False
            except Exception as e:
                logging.warning(f"⚠️ Erreur pagination {paginated_url} : {e}")
        if stop:
            break
        page_num += 1
    return contents

def click_next_pages(driver, start_time):
    """
    Rôle :
    Gère la pagination en cliquant sur les boutons "Suivant" ou "Next".

    Fonctionnalité :
    - Clique sur le bouton de pagination pour charger la page suivante.
    - Extrait les données de chaque page.

    Importance :
    Cette méthode est nécessaire pour les sites qui utilisent des boutons pour la pagination au lieu de paramètres d'URL.

    Arguments :
    - `driver` : Instance du navigateur Selenium.
    - `start_time` : Heure de début pour limiter la durée du scraping.

    Retour :
    Une liste de données extraites des pages paginées.
    """
    pages = []
    seen_hashes = set()
    while True:
        if time.time() - start_time > MAX_DYNAMIC_SECONDS:
            logging.warning("⏱️ Temps limite atteint, arrêt pagination clics")
            break
        try:
            scroll_to_bottom(driver)
            html = driver.page_source
            if not html or len(html) < 100:
                break
            html_clean = clean_extracted_data(html)
            data = extract_all(html_clean, driver.current_url)
            data_hash = str(data)
            if not data or data_hash in seen_hashes:
                break
            pages.append(data)
            seen_hashes.add(data_hash)

            next_button = driver.find_element(By.XPATH, "//a[contains(., 'Next') or contains(., 'Suivant')]")
            driver.execute_script("arguments[0].scrollIntoView();", next_button)
            time.sleep(1)
            next_button.click()
            time.sleep(3)
        except (NoSuchElementException, ElementClickInterceptedException):
            break
        except Exception as e:
            logging.warning(f"⚠️ Erreur clic pagination : {e}")
            break
    return pages

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

def save_debug_files(url, html, driver):
    """
    Rôle :
    Sauvegarde les fichiers de débogage pour analyser les problèmes éventuels.

    Fonctionnalité :
    - Enregistre le HTML brut et la capture d'écran de la page.

    Importance :
    Cette fonction aide à diagnostiquer les erreurs en fournissant des preuves tangibles de l'état de la page au moment du scraping.

    Arguments :
    - `url` : L'URL de la page.
    - `html` : Le contenu HTML de la page.
    - `driver` : Instance du navigateur Selenium.
    """
    try:
        os.makedirs("debug", exist_ok=True)
        domain = urlparse(url).netloc.replace(".", "_")
        html_path = f"debug/{domain}.html"
        screenshot_path = f"debug/{domain}.png"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html or "")
        if driver:
            driver.save_screenshot(screenshot_path)

        logging.info(f"📝 HTML et screenshot sauvegardés dans debug/ pour {url}")
    except Exception as e:
        logging.warning(f"⚠️ Erreur sauvegarde debug : {e}")

def scrape_dynamic_site(url: str) -> dict:
    """
    Rôle :
    Point d'entrée principal pour le scraping des sites dynamiques.

    Fonctionnalité :
    - Gère le processus complet de scraping dynamique pour une URL donnée.

    Importance :
    Cette fonction orchestre l'ensemble du processus de scraping dynamique, y compris la gestion des erreurs et le fallback vers le scraping statique si nécessaire.

    Arguments :
    - `url` : L'URL du site à scraper.

    Retour :
    Un dictionnaire contenant le résultat du scraping, avec succès ou échec.
    """
    logging.info(f"🔄 Scraping dynamique : {url}")
    start_time = time.time()

    timeout = 90 if detect_heavy_js(url) else 60
    driver = get_driver(timeout=timeout)
    if not driver:
        return {"success": False, "url": url, "error": "WebDriver non disponible"}

    all_blocks = []

    try:
        open_with_retry(driver, url)

        scroll_to_bottom(driver)
        if time.time() - start_time > MAX_DYNAMIC_SECONDS:
            raise TimeoutError("Temps limite scraping dynamique atteint")

        html = driver.page_source
        if not html or len(html) < 100:
            raise ValueError("HTML vide ou trop court")

        html_clean = clean_extracted_data(html)
        first_block = extract_all(html_clean, url)
        all_blocks.append(first_block)

        all_blocks.extend(click_next_pages(driver, start_time))
        all_blocks.extend(try_url_parameter_pagination(driver, url, start_time))

        merged = merge_results(all_blocks)
        merged["raw_text"] = clean_extracted_data(html_clean)
        merged = analyse_semantique_site(merged, url=url)

        if not any(v for k, v in merged.items() if k not in ["emails", "phones", "slogan", "location"]):
            logging.warning(f"⚠️ Contenu vide pour {url}, fallback static...")
            static_result = scrape_static_site(url)
            if static_result.get("success"):
                return analyse_semantique_site(static_result, url=url)
            else:
                raise ValueError("Contenu vide ou non informatif")

        return {"success": True, "url": url, "data": merged}

    except Exception as e:
        logging.error(f"❌ Échec scraping {url}: {e}")
        save_debug_files(url, driver.page_source if driver else "", driver)
        logging.info(f"📥 Fallback vers scrape_static_site pour {url}")
        static_result = scrape_static_site(url)
        if static_result.get("success"):
            return analyse_semantique_site(static_result, url=url)
        return {"success": False, "url": url, "error": str(e)}

    finally:
        try:
            driver.quit()
        except:
            pass
        logging.info("✅ WebDriver fermé proprement")
