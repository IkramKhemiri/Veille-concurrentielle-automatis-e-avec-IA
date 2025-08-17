# scraping/crawler.py

"""
Rôle global :
Ce module est responsable de la collecte de données à partir de sites web, qu'ils soient statiques ou dynamiques, 
et de leur analyse sémantique. Il agit comme un orchestrateur, combinant les étapes de scraping et d'analyse pour produire 
un résultat structuré et exploitable.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module est une pièce maîtresse. 
Il automatise la détection du type de site (statique ou dynamique), extrait les données pertinentes et les analyse 
pour les structurer. Sans cette étape, il serait impossible de transformer les données brutes des sites web en informations 
organisées et prêtes à être utilisées dans des rapports ou des visualisations.

Comment il aide dans le pipeline :
- **Scraping** : Identifie le type de site et utilise la méthode appropriée pour extraire les données.
- **Analyse** : Passe les données extraites à l'analyseur sémantique pour les enrichir et les structurer.
- **Visualisation** : Prépare les données pour qu'elles puissent être utilisées dans des graphiques ou des tableaux.
- **Rapport** : Fournit des informations claires et organisées pour les intégrer dans des rapports professionnels.

Technologies utilisées :
- **Détection statique/dynamique** : Utilise une fonction pour déterminer si le site est statique ou dynamique.
- **Scraping statique et dynamique** : Intègre des modules spécialisés pour extraire les données en fonction du type de site.
- **Analyse sémantique** : Utilise un analyseur sémantique pour structurer et enrichir les données extraites.
- **Logging** : Permet de suivre les étapes du processus et de gérer les erreurs de manière transparente.
"""

import logging
from utils.detection import is_static_site
from scraping.scraper_static import scrape_static_site
from scraping.scraper_dynamic import scrape_dynamic_site
from analyse.analyseur_semantique import analyse_semantique

def crawl_site(url):
    """
    Rôle :
    Cette fonction est le point d'entrée principal pour scraper un site web et effectuer une analyse sémantique. 
    Elle détecte si le site est statique ou dynamique, utilise la méthode appropriée pour extraire les données, 
    puis les passe à l'analyseur sémantique pour les structurer.

    Fonctionnalité :
    - Détecte automatiquement si le site est statique ou dynamique.
    - Utilise un scraper adapté pour extraire les données du site.
    - Effectue une analyse sémantique sur les blocs de données extraits.
    - Retourne un dictionnaire structuré contenant les informations analysées.

    Importance :
    Cette fonction automatise l'ensemble du processus de collecte et d'analyse des données d'un site web. 
    Elle garantit que les données extraites sont prêtes à être utilisées dans les étapes suivantes du pipeline.

    Arguments :
    - `url` : L'URL du site web à scraper.

    Retour :
    Un dictionnaire structuré contenant les informations extraites et analysées.
    """
    try:
        # Détection du type de site (statique ou dynamique)
        is_static = is_static_site(url)
        logging.info(f"🔍 Détection du type de site : {'statique' if is_static else 'dynamique'}")

        # Scraping en fonction du type de site
        data = scrape_static_site(url) if is_static else scrape_dynamic_site(url)
        if not data:
            logging.warning(f"⚠️ Aucune donnée extraite de {url}")
            return {"name": url, "url": url, "summary": "Résumé non disponible."}

        # Analyse sémantique sur les blocs HTML extraits
        raw_blocks = data.get("raw_blocks", [])
        analyse = analyse_semantique(raw_blocks, url)

        # Retourne les données structurées
        return {"name": data.get("name", url), "url": url, **analyse}

    except Exception as e:
        # Gestion des erreurs et retour d'un résultat minimal
        logging.error(f"❌ Erreur dans crawl_site pour {url}: {str(e)}")
        return {"name": url, "url": url, "summary": "Résumé non disponible."}
