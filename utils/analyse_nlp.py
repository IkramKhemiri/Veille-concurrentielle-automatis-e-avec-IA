# utils/analyse_nlp.py

import spacy
import json
import langdetect
from collections import Counter
from typing import List, Dict

# Charger les modèles pour plusieurs langues
MODELS = {
    "fr": spacy.load("fr_core_news_md"),
    "en": spacy.load("en_core_web_md"),
    # "es": spacy.load("es_core_news_md"),  # Décommente si besoin
}

def detect_lang(text: str) -> str:
    try:
        return langdetect.detect(text)
    except:
        return "en"  # langue par défaut

def analyser_texte(text: str, lang: str = None) -> Dict:
    if not text or not isinstance(text, str):
        return {"mots_cles": []}
    
    lang = lang or detect_lang(text)
    nlp = MODELS.get(lang, MODELS["en"])
    doc = nlp(text)

    tokens = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    lemmes = [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop]
    mots_cles = [word for word, freq in Counter(lemmes).most_common(10)]

    return {
        "langue": lang,
        "mots_cles": mots_cles,
        "lemmes": lemmes,
        "tokens": tokens
    }

def analyser_site(site: Dict) -> Dict:
    contenu = " ".join(str(site.get(k, "")) for k in ["summary", "services", "blog", "clients", "jobs", "technologies"])
    contenu = contenu.strip().replace("\n", " ")
    result = analyser_texte(contenu)
    site["analyse_nlp"] = result
    return site

def enrichir_json_multilingue(fichier_in: str = "resultats_clean.json", fichier_out: str = "resultats_analyse.json"):
    with open(fichier_in, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = [analyser_site(site) for site in data]

    with open(fichier_out, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"✅ NLP multilingue terminé : {fichier_out}")

# ➕ Fonction main pour exécution directe
if __name__ == "__main__":
    print("🔍 Lancement du traitement NLP multilingue...")
    enrichir_json_multilingue()
