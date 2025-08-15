# utils/synthese_nlp.py
import json
from collections import Counter, defaultdict
from pathlib import Path

def charger_donnees(chemin):
    with open(chemin, encoding='utf-8') as f:
        return json.load(f)

def calculer_score(site):
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
    resultats = {
        "synthese_globale": resume,
        "sites": sites
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)

def main():
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

if __name__ == "__main__":
    main()
