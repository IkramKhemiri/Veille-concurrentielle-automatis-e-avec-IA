# scraping/crawler.py

import logging
from utils.detection import is_static_site
from scraping.scraper_static import scrape_static_site
from scraping.scraper_dynamic import scrape_dynamic_site
from analyse.analyseur_semantique import analyse_semantique

def crawl_site(url):
    """
    Scrape un site (statique ou dynamique) et effectue une analyse sémantique.
    Retourne un dictionnaire structuré.
    """
    try:
        is_static = is_static_site(url)
        logging.info(f"🔍 Détection du type de site : {'statique' if is_static else 'dynamique'}")
        data = scrape_static_site(url) if is_static else scrape_dynamic_site(url)
        if not data:
            logging.warning(f"⚠️ Aucune donnée extraite de {url}")
            return {"name": url, "url": url, "summary": "Résumé non disponible."}

        # Analyse sémantique sur blocs HTML (si présents)
        raw_blocks = data.get("raw_blocks", [])
        analyse = analyse_semantique(raw_blocks, url)

        return {"name": data.get("name", url), "url": url, **analyse}

    except Exception as e:
        logging.error(f"❌ Erreur dans crawl_site pour {url}: {str(e)}")
        return {"name": url, "url": url, "summary": "Résumé non disponible."}
