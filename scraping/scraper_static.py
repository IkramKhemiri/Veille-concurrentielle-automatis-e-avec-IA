# scraping/scraper_static.py

import logging
import requests
from scraping.extractor import extract_all
from scraping.cleaner import clean_extracted_data
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def get_static_html(url, timeout=10):
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
