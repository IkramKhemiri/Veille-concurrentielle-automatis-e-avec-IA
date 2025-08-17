"""
Rôle global :
Ce module est conçu pour effectuer un scraping multi-site en parallèle, en utilisant les capacités de multiprocessing. 
Il combine des approches dynamiques et statiques pour extraire les données des sites web, puis applique une analyse sémantique 
pour enrichir les résultats. Enfin, il génère un rapport PDF et sauvegarde les données dans un fichier JSON.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module est essentiel car il automatise le traitement 
de plusieurs sites en parallèle, réduisant ainsi le temps nécessaire pour collecter et analyser les données. Il garantit également 
une gestion robuste des erreurs et des fallback (retours en arrière) pour maximiser le taux de succès.

Comment il aide dans le pipeline :
- **Scraping** : Extrait les données des sites web en utilisant des approches dynamiques (JavaScript) et statiques (HTML brut).
- **Analyse** : Enrichit les données extraites avec une analyse sémantique pour structurer les informations.
- **Visualisation** : Génère un rapport PDF contenant les résultats du scraping.
- **Rapport** : Sauvegarde les données dans un fichier JSON pour une utilisation ultérieure.

Technologies utilisées :
- **Multiprocessing** : Pour exécuter le scraping en parallèle sur plusieurs sites.
- **Logging** : Pour suivre les étapes du processus et gérer les erreurs.
- **JSON** : Pour sauvegarder les résultats structurés.
- **FPDF** : Pour générer un rapport PDF.
- **Selenium** et **BeautifulSoup** : Pour le scraping dynamique et statique.
"""

import time
import logging
from multiprocessing import Pool, cpu_count
from scraping.scraper_dynamic import scrape_dynamic_site
from scraping.scraper_static import scrape_static_site
from utils.io_handler import load_sites, save_json
from utils.pdf_report import generate_pdf
from analyse.analyseur_semantique import analyse_semantique_site as analyser_semantiquement

SITE_TIMEOUT = 150  # secondes max par site

# Configuration du logger pour suivre les étapes du processus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('scraper.log', encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def process_result(raw_result, site_meta):
    """
    Rôle :
    Traite les résultats bruts du scraping pour les enrichir avec des métadonnées et une analyse sémantique.

    Fonctionnalité :
    - Fusionne les données brutes avec les métadonnées du site.
    - Applique une analyse sémantique pour structurer et enrichir les résultats.
    - Gère les retours en arrière (fallback) en cas d'échec du scraping dynamique.

    Importance :
    Cette fonction garantit que les résultats sont complets, enrichis et prêts pour les étapes suivantes du pipeline.

    Arguments :
    - `raw_result` : Les données brutes extraites du site.
    - `site_meta` : Les métadonnées du site (nom, URL).

    Retour :
    Un dictionnaire contenant les résultats enrichis.
    """
    if not isinstance(raw_result, dict):
        raw_result = {"success": False, "error": "invalid result"}

    if "data" in raw_result and isinstance(raw_result["data"], dict):
        merged = {**raw_result, **raw_result["data"]}
        merged.pop("data", None)
        raw_result = merged

    raw_result["name"] = site_meta.get("name", raw_result.get("name", ""))
    raw_result["url"] = site_meta.get("url", raw_result.get("url", ""))

    if not raw_result.get("success"):
        logger.info(f"ℹ️ Fallback static for {raw_result.get('url')}")
        static = scrape_static_site(raw_result.get("url"))
        if static and static.get("success"):
            raw_result = static
            if "data" in raw_result and isinstance(raw_result["data"], dict):
                merged = {**raw_result, **raw_result["data"]}
                merged.pop("data", None)
                raw_result = merged

    data_input = raw_result if raw_result.get("success") else raw_result.get("data", raw_result)

    try:
        sem = analyser_semantiquement(data_input, url=raw_result.get("url", site_meta.get("url", "")))
    except Exception as e:
        logger.warning(f"⚠️ analyse_semantique failed for {raw_result.get('url')}: {e}")
        sem = data_input

    return {
        "name": sem.get("name", site_meta.get("name", "")),
        "url": sem.get("url", site_meta.get("url", "")),
        "success": True if raw_result.get("success") or sem else False,
        **sem
    }

def scrape_site_worker(site: dict) -> dict:
    """
    Rôle :
    Effectue le scraping d'un site en utilisant une approche dynamique, avec fallback statique en cas d'échec.

    Fonctionnalité :
    - Tente d'extraire les données dynamiquement.
    - Passe à une approche statique si le scraping dynamique échoue.
    - Retourne les résultats enrichis avec les métadonnées du site.

    Importance :
    Cette fonction garantit que chaque site est traité de manière robuste, même en cas d'échec partiel.

    Arguments :
    - `site` : Un dictionnaire contenant les informations du site (nom, URL).

    Retour :
    Un dictionnaire contenant les résultats du scraping.
    """
    name = site.get("name", "Nom inconnu")
    url = site.get("url", "")
    logger.info(f"🔍 Scraping: {name} ({url})")
    try:
        raw = scrape_dynamic_site(url)
        return process_result(raw, site)
    except Exception as e:
        logger.error(f"❌ Erreur lors du scraping de {name}: {e}")
        try:
            static = scrape_static_site(url)
            return process_result(static, site)
        except Exception as e2:
            logger.error(f"❌ Static fallback failed for {name}: {e2}")
            return {"name": name, "url": url, "success": False, "error": str(e2)}

def main():
    """
    Rôle :
    Point d'entrée principal pour lancer le scraping multi-site.

    Fonctionnalité :
    - Charge la liste des sites à scraper.
    - Exécute le scraping en parallèle en utilisant plusieurs processus.
    - Sauvegarde les résultats dans un fichier JSON et génère un rapport PDF.

    Importance :
    Cette fonction orchestre l'ensemble du processus de scraping, garantissant une exécution efficace et une gestion robuste des erreurs.

    Étapes :
    1. Charge les sites depuis un fichier CSV.
    2. Configure le multiprocessing pour traiter les sites en parallèle.
    3. Sauvegarde les résultats et génère un rapport PDF.

    Retour :
    Aucun retour. Les résultats sont sauvegardés et affichés dans la console.
    """
    logger.info("🚀 Lancement du scraping multi-site...")
    try:
        sites = load_sites("sites.csv")
    except Exception as e:
        logger.error(f"❌ Erreur chargement sites.csv : {e}")
        return

    if not sites:
        logger.warning("⚠️ Aucun site trouvé.")
        return

    logger.info(f"📥 {len(sites)} sites à traiter")
    n_processes = max(cpu_count() - 1, 1)
    logger.info(f"⚙️ Utilisation de {n_processes} processus")

    start = time.time()
    results = []

    with Pool(processes=n_processes) as pool:
        async_results = [pool.apply_async(scrape_site_worker, (site,)) for site in sites]
        for i, async_res in enumerate(async_results, start=1):
            try:
                result = async_res.get(timeout=SITE_TIMEOUT)
                results.append(result)
            except Exception as e:
                logger.error(f"⏱️ Timeout ou erreur pour site {sites[i-1].get('url')}: {e}")
                results.append({"name": sites[i-1].get("name", ""), "url": sites[i-1].get("url", ""), "success": False, "error": "Timeout ou erreur"})

    duration = time.time() - start
    logger.info(f"⏱️ Temps total : {duration:.2f}s")

    save_json(results, "resultats.json")
    logger.info("✅ Données sauvegardées dans resultats.json")

    if generate_pdf(results, "rapport_sites.pdf"):
        logger.info("📄 Rapport PDF généré avec succès")
    else:
        logger.error("❌ Échec de génération du PDF")

    logger.info("🏁 Traitement terminé.")

if __name__ == "__main__":
    main()
