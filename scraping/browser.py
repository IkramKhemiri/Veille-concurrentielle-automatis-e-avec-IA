"""
Rôle global :
Ce module est conçu pour gérer la navigation web automatisée et la récupération de contenu HTML, qu'il s'agisse de sites statiques ou dynamiques. 
Il utilise Selenium avec undetected-chromedriver (UDC) pour contourner les mécanismes anti-bot et garantir une navigation fluide.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module est essentiel pour extraire les données brutes des sites web. 
Certains sites utilisent des technologies dynamiques comme JavaScript, rendant leur contenu inaccessible via des requêtes HTTP simples. 
Ce module permet de contourner ces limitations en simulant un navigateur réel, tout en optimisant les performances et en gérant les timeouts.

Comment il aide dans le pipeline :
- **Scraping** : Il récupère le contenu HTML, qu'il soit statique ou généré dynamiquement, pour alimenter les étapes suivantes.
- **Analyse** : Les données brutes extraites sont ensuite analysées et structurées.
- **Visualisation** : Les informations extraites peuvent être utilisées pour créer des graphiques ou des tableaux.
- **Rapport** : Les données collectées servent de base pour générer des rapports professionnels.

Technologies utilisées :
- **Selenium avec undetected-chromedriver (UDC)** : Pour simuler un navigateur et contourner les mécanismes anti-bot.
- **Requests** : Pour récupérer le contenu HTML des sites statiques via des requêtes HTTP simples.
- **Logging** : Pour suivre les étapes et gérer les erreurs de manière transparente.
"""

import os
import time
import random
import logging
from typing import Optional
from pathlib import Path

import requests
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

# ✅ Chemin absolu vers chromedriver.exe (adapter si nécessaire)
CHROMEDRIVER_PATH = str(Path("C:/ENSI/2éme année/Stage ii2/essai/test/drivers/chromedriver.exe"))

def get_driver(headless: bool = True, timeout: int = 30) -> uc.Chrome:
    """
    Rôle :
    Crée et configure un navigateur Chrome automatisé avec des options anti-bot pour récupérer le contenu des sites web.

    Fonctionnalité :
    - Configure le navigateur en mode "headless" (invisible) ou avec interface graphique.
    - Ajoute des options pour contourner les mécanismes de détection des bots.
    - Définit un User-Agent réaliste pour simuler un utilisateur humain.
    - Gère les timeouts pour éviter les blocages sur des pages lourdes.

    Importance :
    Cette fonction est essentielle pour interagir avec des sites web dynamiques qui nécessitent un rendu JavaScript. 
    Elle garantit une navigation fluide et évite les blocages liés aux mécanismes anti-bot.

    Arguments :
    - `headless` : Si `True`, le navigateur fonctionne en arrière-plan sans interface graphique.
    - `timeout` : Temps maximum (en secondes) pour charger une page.

    Retour :
    Une instance de navigateur Chrome configurée.
    """
    try:
        logger.info("🚀 Initialisation du navigateur intelligent (UDC)...")

        options = uc.ChromeOptions()

        # Mode affichage ou invisible
        if headless:
            options.headless = True
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--start-maximized")

        # 📌 Stratégie de chargement "eager" : attend uniquement le HTML initial, pas tous les scripts/images
        options.page_load_strategy = "eager"

        # 🔒 Options anti-bot
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--incognito")
        options.add_argument("--lang=en-US,en;q=0.9")
        options.add_argument("--log-level=3")

        # 🎭 User-Agent réaliste
        user_agent = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0 Safari/537.36",
        ])
        options.add_argument(f"user-agent={user_agent}")

        # ✅ Création du driver
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            driver_executable_path=CHROMEDRIVER_PATH,
            version_main=None
        )

        driver.set_page_load_timeout(timeout)
        logger.info("✅ Navigateur prêt avec chromedriver : " + CHROMEDRIVER_PATH)
        return driver

    except WebDriverException as e:
        logger.error(f"❌ Erreur lors de la création du navigateur : {e}")
        raise RuntimeError("Échec de l'initialisation du navigateur intelligent.")

def close_driver(driver):
    """
    Rôle :
    Ferme proprement une instance de navigateur Chrome.

    Fonctionnalité :
    - Quitte le navigateur et libère les ressources.

    Importance :
    Cette fonction garantit que les ressources système utilisées par le navigateur sont libérées après utilisation, 
    évitant ainsi les fuites de mémoire.

    Arguments :
    - `driver` : L'instance de navigateur à fermer.
    """
    try:
        driver.quit()
        logger.info("🧹 Navigateur fermé proprement.")
    except Exception:
        pass

def get_dynamic_html(url: str, driver=None, timeout: int = 30) -> Optional[str]:
    """
    Rôle :
    Récupère le contenu HTML complet d'un site web dynamique en utilisant un navigateur automatisé.

    Fonctionnalité :
    - Charge l'URL dans un navigateur Chrome automatisé.
    - Exécute le JavaScript pour récupérer le contenu complet de la page.
    - Gère les timeouts et retourne le HTML partiel si nécessaire.

    Importance :
    Cette fonction est essentielle pour scraper des sites dynamiques qui utilisent JavaScript pour générer leur contenu. 
    Elle garantit que toutes les données visibles à l'utilisateur sont accessibles.

    Arguments :
    - `url` : L'URL du site à scraper.
    - `driver` : Une instance de navigateur Chrome (facultatif).
    - `timeout` : Temps maximum (en secondes) pour charger la page.

    Retour :
    Une chaîne de caractères contenant le HTML complet ou `None` en cas d'erreur.
    """
    try:
        if not driver:
            driver = get_driver(headless=True, timeout=timeout)

        try:
            driver.get(url)
        except TimeoutException:
            logger.warning(f"⚠️ Timeout atteint pour {url}, récupération du HTML partiel...")
        finally:
            html = driver.execute_script("return document.documentElement.outerHTML")
            return html

    except Exception as e:
        logger.error(f"❌ Erreur récupération HTML dynamique : {str(e)}")
        return None

def get_static_html(url: str, timeout: int = 10) -> Optional[str]:
    """
    Rôle :
    Récupère le contenu HTML brut d'un site web statique via une requête HTTP simple.

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
    Une chaîne de caractères contenant le HTML brut ou `None` en cas d'erreur.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=timeout, headers=headers)

        if response.status_code == 200:
            html = response.text
            logger.debug(f"📄 HTML statique récupéré (début):\n{html[:300]}...")
            return html
        else:
            logger.warning(f"⚠️ Statut HTTP {response.status_code} pour {url}")
    except Exception as e:
        logger.warning(f"⚠️ Erreur récupération HTML statique : {str(e)}")
    return None
