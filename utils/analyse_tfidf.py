# utils/analyse_tfidf.py

import json
import os
import spacy
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
from typing import List, Dict
import fr_core_news_sm
import en_core_web_sm

# 🔤 Chargement des modèles SpaCy
nlp_fr = fr_core_news_sm.load()
nlp_en = en_core_web_sm.load()

STOPWORDS = set([
    *spacy.lang.en.stop_words.STOP_WORDS,
    *spacy.lang.fr.stop_words.STOP_WORDS
])

PONCTUATION = set(string.punctuation)

def detect_langue(texte: str) -> str:
    """Détection simple de langue : anglais ou français (fallback en)"""
    fr_count = sum(1 for t in nlp_fr(texte) if not t.is_stop)
    en_count = sum(1 for t in nlp_en(texte) if not t.is_stop)
    return 'fr' if fr_count > en_count else 'en'

def preprocess_text(text: str) -> str:
    """Nettoyage et lemmatisation multilingue"""
    if not isinstance(text, str):
        return ""
    
    text = text.strip().lower()
    langue = detect_langue(text)
    doc = nlp_fr(text) if langue == 'fr' else nlp_en(text)
    
    tokens = [
        tok.lemma_ for tok in doc
        if tok.lemma_ not in STOPWORDS
        and tok.lemma_ not in PONCTUATION
        and not tok.is_digit
        and len(tok.lemma_) > 2
    ]
    
    return ' '.join(tokens)

def extraire_tfidf(docs: List[str], max_features: int = 20) -> Dict[str, float]:
    """Extraction des termes les plus pertinents avec TF-IDF"""
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=max_features,
        stop_words=None,
        token_pattern=r'\b\w{3,}\b',
        norm='l2'
    )
    tfidf_matrix = vectorizer.fit_transform(docs)
    mots = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1
    resultats = sorted(zip(mots, scores), key=lambda x: x[1], reverse=True)
    return resultats

def analyser_sites(data: List[Dict]) -> List[Dict]:
    resultats = []

    for site in data:
        nom = site.get("name", "inconnu")
        textes = []

        for champ in ["summary", "slogan", "services", "blog", "jobs"]:
            contenu = site.get(champ)
            if isinstance(contenu, list):
                for item in contenu:
                    if isinstance(item, dict):
                        textes.append(item.get("content", ""))
                    elif isinstance(item, str):
                        textes.append(item)
            elif isinstance(contenu, str):
                textes.append(contenu)
        
        textes_nettoyes = [preprocess_text(t) for t in textes if t]
        if not textes_nettoyes:
            continue
        
        score_mots = extraire_tfidf(textes_nettoyes)
        resultats.append({
            "name": nom,
            "top_keywords": score_mots
        })

    return resultats

def main():
    print("🔍 Lancement du traitement TF-IDF multilingue avec N-grams...")

    with open("resultats_clean.json", "r", encoding="utf-8") as f:
        donnees = json.load(f)

    resultats = analyser_sites(donnees)

    with open("resultats_tfidf.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)

    print("✅ TF-IDF multilingue terminé : resultats_tfidf.json")

if __name__ == "__main__":
    main()
