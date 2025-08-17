"""
Rôle global :
Ce module est conçu pour analyser les textes extraits de sites web en utilisant la méthode TF-IDF (Term Frequency-Inverse Document Frequency). 
Il identifie les termes les plus pertinents dans les textes en fonction de leur importance relative, tout en prenant en charge plusieurs langues 
(anglais et français). Il utilise également des techniques de nettoyage et de lemmatisation pour améliorer la qualité des résultats.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle clé en extrayant les mots-clés les plus significatifs 
des textes. Ces mots-clés permettent de mieux comprendre le contenu des sites web et de générer des visualisations comme des nuages de mots ou des 
analyses thématiques. Sans cette étape, il serait difficile d'identifier les termes importants dans des textes volumineux.

Comment il aide dans le pipeline :
- **Scraping** : Les textes extraits sont souvent bruts et non analysés. Ce module les nettoie et en extrait les termes pertinents.
- **Analyse** : Fournit une liste de mots-clés classés par importance pour une analyse approfondie.
- **Visualisation** : Les mots-clés extraits peuvent être utilisés pour créer des graphiques ou des nuages de mots.
- **Rapport** : Les mots-clés enrichissent les rapports en mettant en avant les termes les plus significatifs.

Technologies utilisées :
- **SpaCy** : Pour la détection de langue, le nettoyage, et la lemmatisation des textes.
- **Scikit-learn (TfidfVectorizer)** : Pour calculer les scores TF-IDF des termes.
- **JSON** : Pour lire et écrire les données enrichies dans des fichiers JSON.
- **Collections** : Pour organiser et traiter les données textuelles.
"""

import json
import os
import spacy
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
from typing import List, Dict
import fr_core_news_sm
import en_core_web_sm

# 🔤 Chargement des modèles SpaCy pour le français et l'anglais
nlp_fr = fr_core_news_sm.load()
nlp_en = en_core_web_sm.load()

# Liste des mots vides (stopwords) et des ponctuations
STOPWORDS = set([
    *spacy.lang.en.stop_words.STOP_WORDS,
    *spacy.lang.fr.stop_words.STOP_WORDS
])
PONCTUATION = set(string.punctuation)

def detect_langue(texte: str) -> str:
    """
    Rôle :
    Détecte la langue dominante d'un texte (anglais ou français).

    Fonctionnalité :
    - Compte les mots non vides (non stopwords) dans le texte pour chaque langue.
    - Retourne "fr" si le texte contient plus de mots français, sinon "en".

    Importance :
    Cette fonction garantit que le texte est analysé avec le modèle linguistique approprié, 
    ce qui améliore la précision des résultats.

    Arguments :
    - `texte` : Une chaîne de caractères représentant le texte à analyser.

    Retour :
    Une chaîne de caractères représentant la langue détectée ("fr" ou "en").
    """
    fr_count = sum(1 for t in nlp_fr(texte) if not t.is_stop)
    en_count = sum(1 for t in nlp_en(texte) if not t.is_stop)
    return 'fr' if fr_count > en_count else 'en'

def preprocess_text(text: str) -> str:
    """
    Rôle :
    Nettoie et lemmatise un texte en fonction de sa langue.

    Fonctionnalité :
    - Détecte la langue du texte.
    - Supprime les mots vides, les ponctuations, et les chiffres.
    - Lemmatisation des mots pour obtenir leur forme de base.

    Importance :
    Cette fonction prépare les textes pour l'analyse TF-IDF en éliminant le bruit et en normalisant les termes.

    Arguments :
    - `text` : Une chaîne de caractères représentant le texte à nettoyer.

    Retour :
    Une chaîne de caractères contenant le texte nettoyé et lemmatisé.
    """
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
    """
    Rôle :
    Extrait les termes les plus pertinents d'une liste de documents en utilisant TF-IDF.

    Fonctionnalité :
    - Calcule les scores TF-IDF pour chaque terme dans les documents.
    - Retourne les termes les plus importants avec leurs scores.

    Importance :
    Cette fonction identifie les mots-clés les plus significatifs dans un ensemble de textes, 
    facilitant leur analyse et leur visualisation.

    Arguments :
    - `docs` : Une liste de chaînes de caractères représentant les documents à analyser.
    - `max_features` : Le nombre maximum de termes à extraire.

    Retour :
    Une liste de tuples contenant les termes et leurs scores TF-IDF.
    """
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),  # Analyse des unigrammes, bigrammes et trigrammes
        max_features=max_features,
        stop_words=None,
        token_pattern=r'\b\w{3,}\b',  # Exclut les mots de moins de 3 caractères
        norm='l2'
    )
    tfidf_matrix = vectorizer.fit_transform(docs)
    mots = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1
    resultats = sorted(zip(mots, scores), key=lambda x: x[1], reverse=True)
    return resultats

def analyser_sites(data: List[Dict]) -> List[Dict]:
    """
    Rôle :
    Analyse les textes extraits de plusieurs sites web pour identifier les mots-clés les plus pertinents.

    Fonctionnalité :
    - Combine les textes des sections importantes de chaque site.
    - Nettoie et lemmatise les textes.
    - Applique l'analyse TF-IDF pour extraire les mots-clés.

    Importance :
    Cette fonction permet de résumer les contenus des sites web en identifiant les termes les plus significatifs.

    Arguments :
    - `data` : Une liste de dictionnaires contenant les données des sites web.

    Retour :
    Une liste de dictionnaires contenant les noms des sites et leurs mots-clés principaux.
    """
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
                        textes.append(contenu)
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
    """
    Rôle :
    Point d'entrée principal pour exécuter l'analyse TF-IDF sur un fichier JSON contenant les données des sites web.

    Fonctionnalité :
    - Charge les données d'un fichier JSON.
    - Applique l'analyse TF-IDF à chaque site.
    - Sauvegarde les résultats dans un nouveau fichier JSON.

    Importance :
    Cette fonction automatise le processus d'analyse TF-IDF, permettant de traiter facilement un grand nombre de sites web.

    Arguments :
    Aucun argument direct. Les fichiers d'entrée et de sortie sont définis dans le code.

    Retour :
    Aucun retour. Les résultats sont sauvegardés dans un fichier JSON.
    """
    print("🔍 Lancement du traitement TF-IDF multilingue avec N-grams...")

    with open("resultats_clean.json", "r", encoding="utf-8") as f:
        donnees = json.load(f)

    resultats = analyser_sites(donnees)

    with open("resultats_tfidf.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)

    print("✅ TF-IDF multilingue terminé : resultats_tfidf.json")

if __name__ == "__main__":
    main()
