"""
Rôle global :
Ce module gère les opérations d'entrée/sortie (I/O) pour le projet de scraping. Il inclut le chargement des sites à scraper, 
la sauvegarde et le chargement des données JSON, la génération de hachages pour les contenus HTML, et la sauvegarde des captures d'écran.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle essentiel en assurant la gestion 
fiable des données. Il garantit que les données extraites sont correctement sauvegardées et accessibles pour les étapes suivantes. 
De plus, il permet de capturer des preuves visuelles (captures d'écran) et de vérifier l'intégrité des données grâce aux hachages.

Comment il aide dans le pipeline :
- **Scraping** : Charge les sites à scraper et sauvegarde les résultats extraits.
- **Analyse** : Fournit des données structurées en JSON pour une analyse approfondie.
- **Visualisation** : Les données JSON peuvent être utilisées pour générer des graphiques ou des tableaux.
- **Rapport** : Les captures d'écran et les données sauvegardées enrichissent les rapports finaux.

Technologies utilisées :
- **CSV** : Pour charger les listes de sites à scraper.
- **JSON** : Pour sauvegarder et charger les données structurées.
- **Hashlib** : Pour générer des hachages SHA-256 des contenus HTML.
- **OS** : Pour gérer les chemins de fichiers et créer des répertoires.
"""

import os
import csv
import json
import hashlib

def load_sites(path):
    """
    Rôle :
    Charge une liste de sites à scraper à partir d'un fichier CSV.

    Fonctionnalité :
    - Lit un fichier CSV contenant les informations des sites (par exemple, URL, nom).
    - Retourne une liste de dictionnaires représentant chaque site.

    Importance :
    Cette fonction est essentielle pour initialiser le processus de scraping en fournissant une liste structurée des sites à traiter.

    Arguments :
    - `path` : Le chemin du fichier CSV contenant les sites.

    Retour :
    Une liste de dictionnaires représentant les sites à scraper.
    """
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_json(data, path):
    """
    Rôle :
    Sauvegarde des données structurées dans un fichier JSON.

    Fonctionnalité :
    - Écrit les données dans un fichier JSON avec une indentation pour une meilleure lisibilité.
    - Assure la compatibilité avec les caractères non-ASCII.

    Importance :
    Cette fonction garantit que les données extraites ou analysées sont sauvegardées de manière fiable et réutilisable.

    Arguments :
    - `data` : Les données à sauvegarder (généralement un dictionnaire ou une liste).
    - `path` : Le chemin du fichier JSON de sortie.

    Retour :
    Aucun retour. Les données sont sauvegardées dans le fichier spécifié.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(path):
    """
    Rôle :
    Charge des données à partir d'un fichier JSON.

    Fonctionnalité :
    - Lit un fichier JSON et retourne les données sous forme de dictionnaire ou de liste.

    Importance :
    Cette fonction permet de récupérer des données sauvegardées pour les étapes suivantes du pipeline, comme l'analyse ou la visualisation.

    Arguments :
    - `path` : Le chemin du fichier JSON à charger.

    Retour :
    Les données chargées sous forme de dictionnaire ou de liste.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def hash_html(html):
    """
    Rôle :
    Génère un hachage unique pour un contenu HTML.

    Fonctionnalité :
    - Utilise l'algorithme SHA-256 pour créer un hachage du contenu HTML.
    - Retourne une chaîne de caractères représentant le hachage.

    Importance :
    Cette fonction permet de vérifier l'intégrité des contenus HTML et d'éviter les doublons dans les données extraites.

    Arguments :
    - `html` : Une chaîne de caractères contenant le contenu HTML.

    Retour :
    Une chaîne de caractères représentant le hachage SHA-256 du contenu HTML.
    """
    return hashlib.sha256(html.encode('utf-8')).hexdigest()

def save_screenshot(driver, name):
    """
    Rôle :
    Sauvegarde une capture d'écran d'une page web.

    Fonctionnalité :
    - Crée un répertoire "screenshots" s'il n'existe pas.
    - Sauvegarde une capture d'écran avec un nom basé sur le paramètre `name`.

    Importance :
    Cette fonction est utile pour capturer des preuves visuelles des pages scrappées, ce qui peut être utile pour le débogage ou les rapports.

    Arguments :
    - `driver` : L'instance Selenium WebDriver utilisée pour naviguer sur la page.
    - `name` : Le nom de la capture d'écran (généralement basé sur l'URL ou le titre de la page).

    Retour :
    Le chemin du fichier de la capture d'écran sauvegardée.
    """
    path = f"screenshots/{name.replace(' ', '_')}.png"
    os.makedirs("screenshots", exist_ok=True)
    driver.save_screenshot(path)
    return path
