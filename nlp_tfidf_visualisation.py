#nlp_tfidf_visualisation.py
"""
Pipeline complet d'analyse d'entreprises :
- Nettoyage, tokenisation, lemmatisation (FR/EN)
- TF-IDF avec n-grams
- Extraction de mots-clés, cooccurrences, scoring simple
- Synthèse globale
- Visualisations complètes :
  * Histogrammes fréquences & TF-IDF (PNG)
  * WordClouds (PNG) + WordCloud animé (GIF)
  * Pie charts (PNG)
  * Heatmap de cooccurrences (PNG)
  * Réseau de mots interactif (PyVis HTML)
  * Histogrammes & TF-IDF interactifs (Plotly HTML)
- Sauvegardes : JSON final, CSV récap, PNG/GIF/HTML dans /visualisations
"""

import json
import string
import os
from pathlib import Path
from collections import Counter, defaultdict
from itertools import islice

import pandas as pd
import numpy as np

# Matplotlib / Seaborn
import matplotlib.pyplot as plt
import seaborn as sns

# Wordcloud & animations
from wordcloud import WordCloud
from PIL import Image, ImageDraw, ImageFont

# TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer

# Interactifs
try:
    import plotly.express as px
    import plotly.io as pio
    PLOTLY_OK = True
except Exception:
    PLOTLY_OK = False

try:
    from pyvis.network import Network
    PYVIS_OK = True
except Exception:
    PYVIS_OK = False

# NLP
import spacy

# ------------------------- Config -------------------------
INPUT_JSON = "resultats_clean.json"
OUTPUT_JSON = "resultats_final.json"
VISUAL_DIR = "visualisations"

TOP_N_KEYWORDS = 20
NGRAM_RANGE = (1, 3)
MAX_BARS = 20
TOP_FOR_COOCC = 30  # nombres de termes pris pour cooccurrences

os.makedirs(VISUAL_DIR, exist_ok=True)

# ------------------------- NLP Models -------------------------
def _load_spacy_model(name_md: str, name_sm: str):
    try:
        return spacy.load(name_md)
    except Exception:
        try:
            os.system(f"python -m spacy download {name_md}")
            return spacy.load(name_md)
        except Exception:
            # fallback vers sm
            try:
                return spacy.load(name_sm)
            except Exception:
                os.system(f"python -m spacy download {name_sm}")
                return spacy.load(name_sm)

nlp_fr = _load_spacy_model("fr_core_news_md", "fr_core_news_sm")
nlp_en = _load_spacy_model("en_core_web_md", "en_core_web_sm")

STOPWORDS = set(list(spacy.lang.en.stop_words.STOP_WORDS) +
                list(spacy.lang.fr.stop_words.STOP_WORDS))
PUNCTUATION = set(string.punctuation)

# ------------------------- Utilitaires -------------------------
def detect_lang(text: str) -> str:
    """Détection basique de langue FR/EN (comptage de non-stop)."""
    if not text or not isinstance(text, str):
        return "en"
    try:
        fr_count = sum(1 for t in nlp_fr(text) if not t.is_stop)
        en_count = sum(1 for t in nlp_en(text) if not t.is_stop)
        return 'fr' if fr_count >= en_count else 'en'
    except Exception:
        return "en"

def preprocess_text(text: str) -> str:
    """Nettoyage + lemmatisation (conserve >2 chars, pas digits/punct/stopwords)."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    lang = detect_lang(text)
    doc = nlp_fr(text) if lang == 'fr' else nlp_en(text)
    tokens = [
        tok.lemma_ for tok in doc
        if tok.lemma_ and tok.lemma_ not in STOPWORDS
        and tok.lemma_ not in PUNCTUATION
        and tok.is_alpha
        and len(tok.lemma_) > 2
    ]
    return " ".join(tokens)

def safe_savefig(path: str, tight: bool = True):
    Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    if tight:
        plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

def ensure_non_empty_counter(counter_obj: Counter) -> Counter:
    """Evite les erreurs en cas de Counter vide."""
    if counter_obj and sum(counter_obj.values()) > 0:
        return counter_obj
    return Counter({"aucun": 1})

# ------------------------- TF-IDF / N-grams -------------------------
def extract_tfidf(docs, top_n=TOP_N_KEYWORDS, ngram_range=NGRAM_RANGE):
    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range,
        stop_words=None,
        token_pattern=r'\b\w{3,}\b',
        norm='l2'
    )
    tfidf_matrix = vectorizer.fit_transform(docs)
    features = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.sum(axis=0).A1
    ranked = sorted(zip(features, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_n], ranked  # (top_n, all ranked)

def get_ngrams(tokens, n=2):
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

# ------------------------- Cooccurrences -------------------------
def cooccurrence_matrix(tokens_list, terms, window_size=2):
    """Matrix de cooccurrence pour 'terms' sur tous les documents de tokens_list."""
    idx = {t: i for i, t in enumerate(terms)}
    mat = np.zeros((len(terms), len(terms)), dtype=np.int32)
    termset = set(terms)
    for tokens in tokens_list:
        for i, tok in enumerate(tokens):
            if tok not in termset:
                continue
            start = max(0, i - window_size)
            end = min(len(tokens), i + window_size + 1)
            for j in range(start, end):
                if i == j:
                    continue
                t2 = tokens[j]
                if t2 in termset:
                    mat[idx[tok], idx[t2]] += 1
    return mat, idx

# ------------------------- Visualisations de base -------------------------
def plot_histogram(counter_obj: Counter, title, xlabel, ylabel, filename, horizontal=True, max_bars=MAX_BARS):
    counter_obj = ensure_non_empty_counter(counter_obj)
    items = counter_obj.most_common(max_bars)
    keys, values = zip(*items)
    plt.figure(figsize=(11, 7))
    if horizontal:
        y = np.arange(len(keys))
        plt.barh(y, values)
        plt.yticks(y, keys)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
    else:
        x = np.arange(len(keys))
        plt.bar(x, values)
        plt.xticks(x, keys, rotation=45, ha='right')
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
    plt.title(title)
    safe_savefig(filename)

def generate_wordcloud(freq_dict: Counter, title, filename):
    freq_dict = ensure_non_empty_counter(freq_dict)
    wc = WordCloud(width=1200, height=600, background_color="white")
    wc = wc.generate_from_frequencies(dict(freq_dict))
    plt.figure(figsize=(12, 6))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    plt.title(title)
    safe_savefig(filename)

def generate_pie_chart(counter_obj: Counter, title, filename, max_slices=12):
    counter_obj = ensure_non_empty_counter(counter_obj)
    items = counter_obj.most_common(max_slices)
    labels, sizes = zip(*items)
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title(title)
    safe_savefig(filename)

def generate_heatmap_coocc(mat, terms, title, filename):
    if mat.size == 0:
        # create empty placeholder
        plt.figure(figsize=(6, 4))
        plt.text(0.5, 0.5, "Pas assez de données", ha='center', va='center')
        safe_savefig(filename)
        return
    plt.figure(figsize=(12, 10))
    sns.heatmap(mat, xticklabels=terms, yticklabels=terms, cmap="Blues")
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    safe_savefig(filename)

def generate_ngram_charts(tokens_all, vis_prefix):
    bigrams = Counter()
    trigrams = Counter()
    for toks in tokens_all:
        bigrams.update(get_ngrams(toks, 2))
        trigrams.update(get_ngrams(toks, 3))

    plot_histogram(bigrams, "Top bigrammes", "Comptes", "Bigrammes",
                   os.path.join(VISUAL_DIR, f"{vis_prefix}_bigrams.png"), horizontal=True)
    plot_histogram(trigrams, "Top trigrammes", "Comptes", "Trigrammes",
                   os.path.join(VISUAL_DIR, f"{vis_prefix}_trigrams.png"), horizontal=True)

    # Wordclouds n-grams
    generate_wordcloud(bigrams, "WordCloud Bigrammes",
                       os.path.join(VISUAL_DIR, f"{vis_prefix}_bigrams_wc.png"))
    generate_wordcloud(trigrams, "WordCloud Trigrammes",
                       os.path.join(VISUAL_DIR, f"{vis_prefix}_trigrams_wc.png"))

# ------------------------- Animations -------------------------
def generate_animated_wordcloud(counter_obj: Counter, title, filename_gif, frames=12):
    """GIF simple: on filtre successivement les top-k pour créer une animation."""
    counter_obj = ensure_non_empty_counter(counter_obj)
    top_items = counter_obj.most_common(min(40, len(counter_obj)))
    if not top_items:
        return
    images = []
    for k in np.linspace(5, len(top_items), frames, dtype=int):
        subset = dict(top_items[:max(1, k)])
        wc = WordCloud(width=1000, height=500, background_color="white")
        wc = wc.generate_from_frequencies(subset)
        img = wc.to_image()
        draw = ImageDraw.Draw(img)
        try:
            # Titre overlay (sans police custom pour compat)
            draw.text((20, 20), f"{title} — top {k}", fill=(20, 20, 20))
        except Exception:
            pass
        images.append(img)
    images[0].save(
        filename_gif,
        save_all=True,
        append_images=images[1:],
        optimize=True,
        duration=600,
        loop=0
    )

# ------------------------- Interactifs -------------------------
def plotly_bar(counter_obj: Counter, title, filename_html, horizontal=True, max_bars=MAX_BARS):
    if not PLOTLY_OK:
        return
    counter_obj = ensure_non_empty_counter(counter_obj)
    items = counter_obj.most_common(max_bars)
    labels, values = zip(*items)
    df = pd.DataFrame({"label": labels, "value": values})
    if horizontal:
        fig = px.bar(df, x="value", y="label", orientation="h", title=title)
    else:
        fig = px.bar(df, x="label", y="value", title=title)
    pio.write_html(fig, file=filename_html, auto_open=False, include_plotlyjs="cdn")

def plotly_tfidf(all_ranked, title, filename_html, max_rows=100):
    if not PLOTLY_OK:
        return
    # all_ranked: liste [(term, score), ...]
    if not all_ranked:
        return
    top = list(islice(all_ranked, max_rows))
    df = pd.DataFrame(top, columns=["term", "score"])
    fig = px.bar(df, x="score", y="term", orientation="h", title=title)
    pio.write_html(fig, file=filename_html, auto_open=False, include_plotlyjs="cdn")

def generate_word_network(terms_scores: list, filename_html: str, max_nodes: int = 50):
    """Graphe interactif (PyVis) basé sur les cooccurrences entre top termes."""
    if not PYVIS_OK:
        return
    if not terms_scores:
        return

    # take top N terms only (by score)
    selected_terms = [t for t, _ in terms_scores[:max_nodes]]

    # Build cooccurrence on global token windows (we'll compute later in main)
    # Here we just create nodes; edges are added in main (need matrix)
    net = Network(height="750px", width="100%", bgcolor="#FFFFFF", font_color="#222222")
    net.barnes_hut()

    for t, s in terms_scores[:max_nodes]:
        net.add_node(t, label=t, title=f"score={round(s,3)}", value=float(s))

    # Edges will be added in main where we know coocc matrix
    # We'll save here and return net object to be enriched
    return net, selected_terms

def add_edges_to_pyvis(net, matrix, terms, threshold=1):
    """Ajoute des arêtes selon cooccurrences > threshold."""
    if not PYVIS_OK or net is None:
        return
    for i, ti in enumerate(terms):
        for j in range(i+1, len(terms)):
            w = int(matrix[i, j])
            if w >= threshold:
                net.add_edge(ti, terms[j], value=w, title=str(w))

# ------------------------- Analyse entreprises -------------------------
def analyse_entreprises(data):
    all_tokens = []
    all_lemmas = []
    all_keywords = []
    results = []

    tokens_per_doc = []  # pour coocc / n-grams

    for site in data:
        name = site.get("name", "Inconnu")
        content_fields = ["summary", "services", "blog", "clients", "jobs", "technologies", "slogan", "introduction"]
        full_text_parts = []
        for f in content_fields:
            v = site.get(f, "")
            if isinstance(v, list):
                for it in v:
                    if isinstance(it, dict):
                        full_text_parts.append(str(it.get("content", "")))
                    else:
                        full_text_parts.append(str(it))
            else:
                full_text_parts.append(str(v))
        full_text = " ".join(full_text_parts).replace("\n", " ").strip()

        preprocessed = preprocess_text(full_text)
        tokens = preprocessed.split()
        lemmes = tokens[:]  # déjà lemmatisés
        keywords = [w for w, c in Counter(lemmes).most_common(10)]

        # TF-IDF (protégé contre textes vides)
        tfidf_top = []
        tfidf_all = []
        if preprocessed.strip():
            try:
                tfidf_top, tfidf_all = extract_tfidf([preprocessed], top_n=TOP_N_KEYWORDS)
            except ValueError:
                print(f"⚠️ Pas assez de contenu pour TF-IDF pour {name}")
        else:
            print(f"⚠️ Aucun contenu utilisable pour {name}")

        # Résultat site
        site_result = {
            "name": name,
            "tokens": tokens,
            "lemmes": lemmes,
            "keywords": keywords,
            "tfidf": tfidf_top
        }
        results.append(site_result)

        # Globales
        all_tokens.extend(tokens)
        all_lemmas.extend(lemmes)
        all_keywords.extend(keywords)
        tokens_per_doc.append(tokens)

    return results, all_tokens, all_lemmas, all_keywords, tokens_per_doc

# ------------------------- Synthèse globale -------------------------
def synthese_globale(results, all_tokens, all_lemmas, all_keywords):
    freq_tokens = Counter(all_tokens)
    freq_lemmas = Counter(all_lemmas)
    freq_keywords = Counter(all_keywords)

    # Score simple par site (quantité d'infos)
    scores = []
    for r in results:
        s = 0
        if len(r.get("keywords", [])) >= 5:
            s += 3
        if len(r.get("tokens", [])) >= 30:
            s += 3
        if len(r.get("tfidf", [])) >= 10:
            s += 2
        s = min(10, s)
        r["score"] = s
        scores.append(s)

    synthese = {
        "nb_sites": len(results),
        "top_tokens": freq_tokens.most_common(20),
        "top_lemmes": freq_lemmas.most_common(20),
        "top_keywords": freq_keywords.most_common(20),
        "score_moyen": round(sum(scores) / len(scores), 2) if scores else 0
    }
    return synthese, freq_tokens, freq_lemmas, freq_keywords

# ------------------------- Visualisations globales -------------------------
def generate_visualisations(freq_tokens, freq_lemmas, freq_keywords, tokens_per_doc):
    # Histos (PNG)
    plot_histogram(freq_tokens, "Top Tokens (fréquences brutes)", "Fréquence", "Token",
                   os.path.join(VISUAL_DIR, "top_tokens.png"), horizontal=True)
    plot_histogram(freq_lemmas, "Top Lemmés (fréquences brutes)", "Fréquence", "Lemmes",
                   os.path.join(VISUAL_DIR, "top_lemmes.png"), horizontal=True)
    plot_histogram(freq_keywords, "Top Mots-clés (agrégés)", "Fréquence", "Mot-clé",
                   os.path.join(VISUAL_DIR, "top_keywords.png"), horizontal=True)

    # Wordclouds (PNG)
    generate_wordcloud(freq_tokens, "WordCloud Tokens", os.path.join(VISUAL_DIR, "wc_tokens.png"))
    generate_wordcloud(freq_lemmas, "WordCloud Lemmés", os.path.join(VISUAL_DIR, "wc_lemmes.png"))
    generate_wordcloud(freq_keywords, "WordCloud Mots-clés", os.path.join(VISUAL_DIR, "wc_keywords.png"))

    # Wordcloud animé (GIF)
    generate_animated_wordcloud(freq_tokens, "Tokens", os.path.join(VISUAL_DIR, "wc_tokens_animated.gif"))

    # Pie charts
    generate_pie_chart(freq_keywords, "Répartition (Top mots-clés)", os.path.join(VISUAL_DIR, "pie_keywords.png"))
    generate_pie_chart(freq_lemmas, "Répartition (Top lemmes)", os.path.join(VISUAL_DIR, "pie_lemmes.png"))

    # N-grams
    generate_ngram_charts(tokens_per_doc, "global")

    # Cooccurrences (sur top termes)
    top_terms = [t for t, _ in freq_lemmas.most_common(TOP_FOR_COOCC)]
    mat, idx = cooccurrence_matrix(tokens_per_doc, top_terms, window_size=2)
    # Heatmap
    generate_heatmap_coocc(mat, top_terms, "Heatmap Cooccurrences (top lemmes)", os.path.join(VISUAL_DIR, "heatmap_coocc.png"))

    # Réseau interactif PyVis + Plotly interactif
    all_ranked = list(freq_lemmas.items())
    all_ranked = sorted(all_ranked, key=lambda x: x[1], reverse=True)
        # Réseau interactif PyVis + Plotly interactif
    all_ranked = list(freq_lemmas.items())
    all_ranked = sorted(all_ranked, key=lambda x: x[1], reverse=True)
    if PYVIS_OK and all_ranked:
        try:
            net, selected_terms = generate_word_network(all_ranked, os.path.join(VISUAL_DIR, "network_keywords.html"))
            if net:
                # Ajouter des arêtes depuis matrix (réduction aux termes sélectionnés)
                sel_idx = [i for i, t in enumerate(top_terms) if t in selected_terms]
                if sel_idx:
                    # sous-matrice
                    sub_terms = [top_terms[i] for i in sel_idx]
                    sub_mat = mat[np.ix_(sel_idx, sel_idx)]
                    add_edges_to_pyvis(net, sub_mat, sub_terms, threshold=1)
                # Sauvegarde HTML
                try:
                    net.show(os.path.join(VISUAL_DIR, "network_keywords.html"))
                except Exception as e:
                    print(f"⚠️ Erreur PyVis show(): {e}")
        except Exception as e:
            print(f"⚠️ PyVis échoué: {e}")


    # Interactifs Plotly (si dispo)
    plotly_bar(freq_tokens, "Top Tokens (Interactif)", os.path.join(VISUAL_DIR, "top_tokens_interactif.html"))
    plotly_bar(freq_lemmas, "Top Lemmés (Interactif)", os.path.join(VISUAL_DIR, "top_lemmes_interactif.html"))
    plotly_bar(freq_keywords, "Top Mots-clés (Interactif)", os.path.join(VISUAL_DIR, "top_keywords_interactif.html"))

# ------------------------- Export tables -------------------------
def save_pandas_tables(results, synthese):
    # Table détaillée par site
    df = pd.DataFrame(results)
    df.to_csv(os.path.join(VISUAL_DIR, "tableau_sites.csv"), index=False, encoding="utf-8-sig")

    # Table des top tfidf par site (explosion pour lisibilité)
    rows = []
    for r in results:
        name = r.get("name", "Inconnu")
        for term, score in r.get("tfidf", []):
            rows.append({"site": name, "term": term, "tfidf_score": score})
    df_tfidf = pd.DataFrame(rows)
    if not df_tfidf.empty:
        df_tfidf.sort_values(by="tfidf_score", ascending=False, inplace=True)
        df_tfidf.to_csv(os.path.join(VISUAL_DIR, "tableau_tfidf.csv"), index=False, encoding="utf-8-sig")

    # Synthèse globale
    pd.DataFrame(synthese.items(), columns=["metrique", "valeur"]).to_csv(
        os.path.join(VISUAL_DIR, "synthese_globale.csv"), index=False, encoding="utf-8-sig"
    )

# ------------------------- Pipeline principal -------------------------
def main():
    if not Path(INPUT_JSON).exists():
        print(f"❌ Fichier introuvable : {INPUT_JSON}")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("🔍 Analyse entreprises en cours...")
    results, all_tokens, all_lemmas, all_keywords, tokens_per_doc = analyse_entreprises(data)

    print("📊 Génération synthèse globale...")
    synthese, freq_tokens, freq_lemmas, freq_keywords = synthese_globale(results, all_tokens, all_lemmas, all_keywords)

    print("🖼️ Création visualisations (PNG/GIF/HTML)...")
    generate_visualisations(freq_tokens, freq_lemmas, freq_keywords, tokens_per_doc)

    print("📋 Sauvegarde tableaux CSV...")
    save_pandas_tables(results, synthese)

    # Sauvegarde JSON final
    output_data = {
        "results": results,
        "synthese_globale": synthese
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Pipeline terminé.")
    print(f"📄 JSON final : {OUTPUT_JSON}")
    print(f"🖼️ Visualisations / tableaux : {VISUAL_DIR}")

if __name__ == "__main__":
    main()
