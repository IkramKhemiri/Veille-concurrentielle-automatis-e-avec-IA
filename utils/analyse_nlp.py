"""
Rôle global :
Ce module est conçu pour effectuer une analyse linguistique avancée (NLP) sur des textes extraits de sites web. 
Il détecte la langue, extrait les mots-clés, les lemmes et les tokens, et enrichit les données avec des informations 
linguistiques utiles. Il prend en charge plusieurs langues grâce à des modèles Spacy.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle clé en ajoutant une couche 
d'analyse linguistique aux données textuelles. Cela permet d'extraire des informations pertinentes et de mieux comprendre 
le contenu des sites web. Sans cette étape, les données textuelles resteraient brutes et moins exploitables.

Comment il aide dans le pipeline :
- **Scraping** : Les données textuelles extraites sont souvent volumineuses et non analysées. Ce module les structure et les enrichit.
- **Analyse** : Fournit des informations linguistiques comme les mots-clés et les lemmes pour une analyse approfondie.
- **Visualisation** : Les mots-clés extraits peuvent être utilisés pour créer des nuages de mots ou des graphiques.
- **Rapport** : Les données enrichies permettent de générer des rapports plus détaillés et informatifs.

Technologies utilisées :
- **Spacy** : Pour effectuer l'analyse linguistique (lemmatisation, extraction de tokens, etc.).
- **Langdetect** : Pour détecter automatiquement la langue du texte.
- **Collections (Counter)** : Pour compter les occurrences des mots et extraire les mots-clés les plus fréquents.
- **JSON** : Pour lire et écrire les données enrichies dans des fichiers JSON.
"""

import spacy
import json
import langdetect
from collections import Counter
from typing import List, Dict

# Charger les modèles pour plusieurs langues
MODELS = {
    "fr": spacy.load("fr_core_news_md"),  # Modèle pour le français
    "en": spacy.load("en_core_web_md"),  # Modèle pour l'anglais
    # "es": spacy.load("es_core_news_md"),  # Décommentez pour ajouter le support de l'espagnol
}

def detect_lang(text: str) -> str:
    """
    Rôle :
    Détecte automatiquement la langue d'un texte.

    Fonctionnalité :
    - Utilise la bibliothèque `langdetect` pour identifier la langue dominante dans le texte.
    - Retourne "en" (anglais) par défaut en cas d'erreur.

    Importance :
    Cette fonction garantit que le texte est analysé avec le modèle linguistique approprié, 
    ce qui améliore la précision de l'analyse NLP.

    Arguments :
    - `text` : Une chaîne de caractères représentant le texte à analyser.

    Retour :
    Une chaîne de caractères représentant le code de la langue détectée (par exemple, "fr", "en").
    """
    try:
        return langdetect.detect(text)
    except:
        return "en"  # Langue par défaut en cas d'erreur

def analyser_texte(text: str, lang: str = None) -> Dict:
    """
    Rôle :
    Analyse un texte pour extraire des informations linguistiques comme les mots-clés, les lemmes et les tokens.

    Fonctionnalité :
    - Détecte la langue du texte si elle n'est pas spécifiée.
    - Utilise un modèle Spacy pour analyser le texte.
    - Extrait les tokens (mots), les lemmes (formes de base des mots) et les mots-clés les plus fréquents.

    Importance :
    Cette fonction enrichit les données textuelles avec des informations linguistiques utiles, 
    facilitant leur exploitation dans les étapes suivantes.

    Arguments :
    - `text` : Une chaîne de caractères représentant le texte à analyser.
    - `lang` : La langue du texte (facultatif). Si non spécifiée, elle est détectée automatiquement.

    Retour :
    Un dictionnaire contenant la langue détectée, les mots-clés, les lemmes et les tokens.
    """
    if not text or not isinstance(text, str):
        return {"mots_cles": []}

    lang = lang or detect_lang(text)
    nlp = MODELS.get(lang, MODELS["en"])  # Utilise le modèle correspondant à la langue détectée
    doc = nlp(text)

    tokens = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    lemmes = [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop]
    mots_cles = [word for word, freq in Counter(lemmes).most_common(10)]  # Top 10 des mots-clés

    return {
        "langue": lang,
        "mots_cles": mots_cles,
        "lemmes": lemmes,
        "tokens": tokens
    }

def analyser_site(site: Dict) -> Dict:
    """
    Rôle :
    Analyse linguistiquement le contenu textuel d'un site web.

    Fonctionnalité :
    - Combine les sections textuelles importantes du site (résumé, services, blog, etc.).
    - Effectue une analyse NLP sur le contenu combiné.
    - Ajoute les résultats de l'analyse au dictionnaire du site.

    Importance :
    Cette fonction enrichit les données d'un site avec des informations linguistiques, 
    rendant les données plus exploitables pour des analyses ou des visualisations.

    Arguments :
    - `site` : Un dictionnaire contenant les données d'un site web.

    Retour :
    Le dictionnaire du site enrichi avec les résultats de l'analyse NLP.
    """
    contenu = " ".join(str(site.get(k, "")) for k in ["summary", "services", "blog", "clients", "jobs", "technologies"])
    contenu = contenu.strip().replace("\n", " ")
    result = analyser_texte(contenu)
    site["analyse_nlp"] = result
    return site

def enrichir_json_multilingue(fichier_in: str = "resultats_clean.json", fichier_out: str = "resultats_analyse.json"):
    """
    Rôle :
    Enrichit un fichier JSON contenant des données de sites web avec des analyses linguistiques multilingues.

    Fonctionnalité :
    - Charge les données d'un fichier JSON.
    - Applique l'analyse NLP à chaque site.
    - Sauvegarde les données enrichies dans un nouveau fichier JSON.

    Importance :
    Cette fonction automatise l'enrichissement des données textuelles avec des informations linguistiques, 
    facilitant leur exploitation dans des rapports ou des visualisations.

    Arguments :
    - `fichier_in` : Le chemin du fichier JSON d'entrée contenant les données brutes.
    - `fichier_out` : Le chemin du fichier JSON de sortie contenant les données enrichies.

    Retour :
    Aucun retour. Les résultats sont sauvegardés dans le fichier de sortie.
    """
    with open(fichier_in, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = [analyser_site(site) for site in data]

    with open(fichier_out, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"✅ NLP multilingue terminé : {fichier_out}")

# ➕ Fonction main pour exécution directe
if __name__ == "__main__":
    """
    Rôle :
    Point d'entrée principal pour exécuter l'analyse NLP multilingue sur un fichier JSON.

    Fonctionnalité :
    - Lance la fonction `enrichir_json_multilingue` pour traiter les données d'entrée.
    - Affiche un message de confirmation une fois le traitement terminé.

    Importance :
    Permet d'exécuter le script directement depuis la ligne de commande pour enrichir les données JSON avec des analyses NLP.
    """
    print("🔍 Lancement du traitement NLP multilingue...")
    enrichir_json_multilingue()
