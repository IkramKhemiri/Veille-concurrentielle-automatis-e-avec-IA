"""
Rôle global :
Ce module est conçu pour produire une synthèse globale des résultats d'analyse NLP (Natural Language Processing) 
appliqués aux sites web. Il calcule des scores pour chaque site, analyse les langues détectées, identifie les mots-clés 
les plus fréquents, et génère un résumé global des données.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle clé en consolidant 
les résultats d'analyse NLP. Il fournit une vue d'ensemble des données, ce qui est essentiel pour évaluer la qualité 
et la pertinence des informations extraites. Cette synthèse permet également de prioriser les sites en fonction de leur score.

Comment il aide dans le pipeline :
- **Scraping** : Compile les données extraites pour les rendre exploitables.
- **Analyse** : Fournit des statistiques globales sur les langues, les mots-clés et les scores des sites.
- **Visualisation** : Génère des données synthétiques qui peuvent être utilisées pour des graphiques ou des tableaux.
- **Rapport** : Produit un résumé clair et structuré qui peut être intégré dans des rapports professionnels.

Technologies utilisées :
- **JSON** : Pour charger et sauvegarder les données structurées.
- **Collections (Counter)** : Pour compter les occurrences des langues et des mots-clés.
- **Pathlib** : Pour vérifier l'existence des fichiers.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

def charger_donnees(chemin):
    """
    Rôle :
    Charge les données JSON contenant les résultats d'analyse NLP.

    Fonctionnalité :
    - Lit un fichier JSON et retourne les données sous forme de liste ou de dictionnaire.

    Importance :
    Cette fonction est essentielle pour récupérer les données nécessaires à la synthèse globale.

    Arguments :
    - `chemin` : Le chemin du fichier JSON à charger.

    Retour :
    Les données JSON sous forme de liste ou de dictionnaire.
    """
    with open(chemin, encoding='utf-8') as f:
        return json.load(f)

def calculer_score(site):
    """
    Rôle :
    Calcule un score global pour un site en fonction de plusieurs critères.

    Fonctionnalité :
    - Attribue des points en fonction de la présence de mots-clés, de lemmes, d'un résumé, de la langue détectée, 
      et du nombre de tokens.
    - Limite le score maximum à 10.

    Importance :
    Cette fonction permet de quantifier la qualité et la richesse des données extraites pour chaque site.

    Arguments :
    - `site` : Un dictionnaire contenant les données d'un site.

    Retour :
    Un entier représentant le score du site (entre 0 et 10).
    """
    score = 0
    if len(site.get("keywords", [])) > 3:
        score += 3
    if len(site.get("lemmes", [])) > 5:
        score += 2
    if site.get("summary"):
        score += 2
    if site.get("lang") in ["fr", "en"]:
        score += 1
    if len(site.get("tokens", [])) > 20:
        score += 2
    return min(score, 10)

def synthese_globale(sites):
    """
    Rôle :
    Produit une synthèse globale des résultats d'analyse NLP pour tous les sites.

    Fonctionnalité :
    - Compte les langues détectées.
    - Identifie les mots-clés les plus fréquents.
    - Calcule les scores pour chaque site et génère des statistiques globales (moyenne, maximum, minimum).

    Importance :
    Cette fonction fournit une vue d'ensemble des données, permettant d'évaluer la qualité des résultats et de 
    prioriser les sites en fonction de leur pertinence.

    Arguments :
    - `sites` : Une liste de dictionnaires contenant les données des sites.

    Retour :
    Un dictionnaire contenant la synthèse globale (nombre de sites, langues détectées, top mots-clés, scores).
    """
    langues = Counter()
    mots_cles = Counter()
    scores = []

    for site in sites:
        lang = site.get("lang", "unk")
        langues[lang] += 1

        mots_cles.update(site.get("keywords", []))

        score = calculer_score(site)
        site["score"] = score
        scores.append(score)

    synthese = {
        "nombre_sites": len(sites),
        "langues_detectees": dict(langues),
        "top_keywords": [kw for kw, _ in mots_cles.most_common(15)],
        "score_moyen": round(sum(scores) / len(scores), 2) if scores else 0,
        "score_max": max(scores, default=0),
        "score_min": min(scores, default=0)
    }

    return synthese

def enregistrer_synthese(sites, resume, output_path):
    """
    Rôle :
    Sauvegarde la synthèse globale et les données des sites dans un fichier JSON.

    Fonctionnalité :
    - Combine la synthèse globale et les données des sites dans un seul fichier.
    - Écrit les résultats dans un fichier JSON avec une indentation pour une meilleure lisibilité.

    Importance :
    Cette fonction garantit que les résultats de la synthèse sont sauvegardés de manière fiable et réutilisable.

    Arguments :
    - `sites` : Une liste de dictionnaires contenant les données des sites.
    - `resume` : Un dictionnaire contenant la synthèse globale.
    - `output_path` : Le chemin du fichier JSON de sortie.

    Retour :
    Aucun retour. Les résultats sont sauvegardés dans le fichier spécifié.
    """
    resultats = {
        "synthese_globale": resume,
        "sites": sites
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)

def main():
    """
    Rôle :
    Point d'entrée principal pour générer la synthèse globale des résultats d'analyse NLP.

    Fonctionnalité :
    - Vérifie l'existence du fichier JSON contenant les résultats d'analyse.
    - Charge les données JSON.
    - Produit une synthèse globale des résultats.
    - Sauvegarde la synthèse et les données dans un nouveau fichier JSON.

    Importance :
    Cette fonction orchestre l'ensemble du processus de synthèse, garantissant que les résultats sont consolidés 
    et sauvegardés pour une utilisation ultérieure.

    Étapes :
    1. Vérifie si le fichier `resultats_analyse.json` existe.
    2. Charge les données JSON.
    3. Calcule la synthèse globale.
    4. Sauvegarde les résultats dans `synthese_resultats.json`.

    Arguments :
    Aucun argument direct. Les chemins des fichiers d'entrée et de sortie sont définis dans le code.

    Retour :
    Aucun retour. Les résultats sont affichés dans la console.
    """
    print("📊 Analyse NLP ➝ Synthèse globale & scoring ...")
    input_path = "resultats_analyse.json"
    output_path = "synthese_resultats.json"

    if not Path(input_path).exists():
        print("❌ Fichier resultats_analyse.json introuvable.")
        return

    data = charger_donnees(input_path)
    resume = synthese_globale(data)
    enregistrer_synthese(data, resume, output_path)

    print("✅ Résumé synthétique sauvegardé dans : synthese_resultats.json")
    print(f"\nRésumé rapide :\n- Sites : {resume['nombre_sites']}\n- Moyenne Score : {resume['score_moyen']}/10\n- Langues : {resume['langues_detectees']}")
    print(f"- Top Mots-clés : {', '.join(resume['top_keywords'][:10])}")

# Point d'entrée du script
if __name__ == "__main__":
    main()
