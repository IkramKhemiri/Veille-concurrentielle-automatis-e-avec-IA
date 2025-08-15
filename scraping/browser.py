# scraping/browser.py

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
    Crée un navigateur Chrome intelligent avec options anti-bot (Selenium + UDC),
    optimisé pour éviter les timeouts sur pages lourdes.
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
    try:
        driver.quit()
        logger.info("🧹 Navigateur fermé proprement.")
    except Exception:
        pass

def get_dynamic_html(url: str, driver=None, timeout: int = 30) -> Optional[str]:
    """
    🔍 Récupère le HTML complet d'un site dynamique avec gestion de timeout et fallback.
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
    🔍 Récupère le HTML brut d'un site web statique via requête HTTP simple.
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
