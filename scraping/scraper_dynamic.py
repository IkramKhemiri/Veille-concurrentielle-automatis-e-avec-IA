#scraping/scraper_dynamic.py

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
    for attempt in range(retries):
        try:
            driver.get(url)
            return True
        except WebDriverException as e:
            logging.warning(f"🌐 Tentative {attempt+1}/{retries} échouée pour {url} : {str(e)}")
            time.sleep(wait_sec)
    raise Exception(f"Impossible de charger {url} après {retries} tentatives")

def scroll_to_bottom(driver, pause_time=2, max_scrolls=6):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def update_url_param(url, param_name, param_value):
    parts = urlparse(url)
    query = parse_qs(parts.query)
    query[param_name] = [str(param_value)]
    new_query = urlencode(query, doseq=True)
    new_parts = parts._replace(query=new_query)
    return urlunparse(new_parts)

def try_url_parameter_pagination(driver, base_url, start_time):
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
