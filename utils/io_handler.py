# utils/io_handler.py
# This module handles file I/O operations for the scraper, including loading sites, saving JSON data
import os
import csv
import json
import hashlib

def load_sites(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def hash_html(html):
    return hashlib.sha256(html.encode('utf-8')).hexdigest()

def save_screenshot(driver, name):
    path = f"screenshots/{name.replace(' ', '_')}.png"
    os.makedirs("screenshots", exist_ok=True)
    driver.save_screenshot(path)
    return path