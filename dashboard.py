#dashboard.py 
import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import base64
from datetime import datetime
import os
from streamlit_lottie import st_lottie
import requests
from io import BytesIO

# =========================
#   CONFIGURATION DE PAGE
# =========================
# Charger l'icône personnalisée
if os.path.exists("logos/logo-navitrends.png"):
    with open("logos/logo-navitrends.png", "rb") as f:
        logo_bytes = f.read()
        st.set_page_config(
            page_title="Analyse concurrentielle",
            page_icon=logo_bytes,
            layout="wide",
            initial_sidebar_state="expanded"
        )
else:
    st.set_page_config(
        page_title="Analyse concurrentielle",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# =========================
#   UTILITAIRES STYLES
# =========================
def local_css(file_name: str):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Fichier CSS introuvable: {file_name}")

def apply_theme_css(theme):
    """Injecte des overrides CSS selon le thème choisi."""
    bg = theme["bg"]
    surface = theme["surface"]
    surface_alt = theme["surface_alt"]
    text = theme["text"]
    subtext = theme["subtext"]
    primary = theme["primary"]
    secondary = theme["secondary"]
    tab_unselected = theme["tab_unselected"]

    css = f"""
    <style>
    html, body, [class*="css"] {{ color: {text} !important; }}
    h1, h2, h3, h4, h5, h6 {{ color: {text} !important; }}
    .subheader {{ color: {subtext} !important; }}

    [data-testid="stAppViewContainer"] {{
        background: {bg} !important;
    }}
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {surface} 0%, {surface_alt} 100%) !important;
        color: {text} !important;
        box-shadow: 2px 0 15px rgba(0,0,0,0.15);
    }}
    .header {{
        background: linear-gradient(135deg, {surface_alt} 0%, {surface} 100%) !important;
        border-left: 5px solid {primary} !important;
    }}
    .kpi-card, .file-card, .viz-explanation, .kpi-explanation {{
        background: {surface} !important;
        color: {text} !important;
        border: 1px solid rgba(255,255,255,0.08);
    }}
    .kpi-icon {{ color: {primary} !important; }}
    .file-card h4 {{ color: {primary} !important; }}
    .file-card a {{
        background: {primary} !important;
    }}
    .file-card a:hover {{
        background: {secondary} !important;
        transform: translateY(-2px);
    }}

    /* Onglets */
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        background: {tab_unselected} !important;
        color: {text} !important;
        border-radius: 10px !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, {primary} 0%, {secondary} 100%) !important;
        color: #fff !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.25);
    }}

    /* Liens */
    a, a:visited {{ color: {secondary}; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# =========================
#   LOTTIE (animations)
# =========================
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

lottie_analytics = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_uzkz3lqm.json")
lottie_docs      = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_5tkzkblw.json")
lottie_customize = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_tljjahxg.json")
lottie_theme     = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_ysa3qk4a.json")
lottie_export    = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_xlkxtmul.json")

# =========================
#   DONNÉES
# =========================
@st.cache_data
def load_data(file_name='resultats_final.json'):
    """Charge les données depuis un fichier JSON avec gestion robuste des formats"""
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Gestion des différents formats de fichiers
        if isinstance(data, dict):
            if 'results' in data:  # Format {results: [...]}
                rows = data['results']
            else:  # Format {id1: {...}, id2: {...}}
                rows = list(data.values())
        else:  # Format [...]
            rows = data
        
        # Conversion en DataFrame avec colonnes par défaut si nécessaires
        df = pd.DataFrame(rows)
        
        # Assure que les colonnes critiques existent
        expected_columns = {
            'name': None,
            'score': 0,
            'country': 'Inconnu',
            'keywords': []
        }
        
        for col, default in expected_columns.items():
            if col not in df.columns:
                df[col] = default
                
        return df
        
    except Exception as e:
        st.error(f"Erreur de chargement: {str(e)}")
        return pd.DataFrame()

def save_json(path: str, payload):
    try:
        # Si c'est un DataFrame, convertissez-le en format standard
        if isinstance(payload, pd.DataFrame):
            payload = {"results": payload.to_dict(orient='records')}
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Impossible d'écrire {path}: {e}")
        return False

def get_file_download_link(file_path, file_label):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(file_path)}">Télécharger {file_label}</a>'
        return href
    except Exception:
        return ""


# =========================
#   EXPORT COMPLET DU DASHBOARD
# =========================
def capture_full_dashboard(filtered_df):
    try:
        from fpdf import FPDF
        import tempfile
        import base64
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Entête avec logo
        if logo_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_logo:
                tmp_logo.write(logo_bytes)
                pdf.image(tmp_logo.name, x=10, y=8, w=30)
            os.unlink(tmp_logo.name)
        
        # Titre
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Rapport Complet d'Analyse Concurrentielle", ln=1)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
        pdf.ln(15)
        
        # Section Introduction
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Introduction", ln=1)
        pdf.set_font("Arial", "", 12)
        intro_text = """
        Ce rapport présente une analyse complète du paysage concurrentiel 
        avec visualisations des données clés et recommandations stratégiques.
        """
        pdf.multi_cell(0, 8, intro_text)
        pdf.ln(10)
        
        # Indicateurs Clés
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Indicateurs Clés", ln=1)
        pdf.set_font("Arial", "", 12)
        
        kpi_text = f"Entreprises analysées: {len(filtered_df)}\n"
        if "score" in filtered_df.columns:
            kpi_text += f"""
            - Score moyen: {filtered_df['score'].mean():.2f}
            - Score médian: {filtered_df['score'].median():.2f}
            - Écart-type: {filtered_df['score'].std():.2f}
            """
        if "country" in filtered_df.columns:
            kpi_text += f"\nPays représentés: {filtered_df['country'].nunique()}"
        
        pdf.multi_cell(0, 8, kpi_text)
        pdf.ln(10)
        
        # Ajouter toutes les visualisations
        if "score" in filtered_df.columns:
            # Histogramme des scores
            fig = px.histogram(filtered_df, x="score", title="Distribution des scores")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                fig.write_image(tmp.name)
                pdf.image(tmp.name, x=10, w=190)
                os.unlink(tmp.name)
            pdf.ln(10)
            
            # Graphique des scores par entreprise
            if "name" in filtered_df.columns:
                fig = px.bar(
                    filtered_df.sort_values("score", ascending=False).head(20),
                    x="name",
                    y="score",
                    title="Top 20 des entreprises"
                )
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    fig.write_image(tmp.name)
                    pdf.image(tmp.name, x=10, w=190)
                    os.unlink(tmp.name)
                pdf.ln(10)
        
        # Nuage de mots-clés
        if "keywords" in filtered_df.columns:
            all_kw = ' '.join(' '.join(kws) if isinstance(kws, list) else str(kws) 
                      for kws in filtered_df['keywords'].dropna())
            if all_kw.strip():
                wordcloud = WordCloud(width=800, height=400, background_color="white").generate(all_kw)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    wordcloud.to_file(tmp.name)
                    pdf.image(tmp.name, x=10, w=190)
                    os.unlink(tmp.name)
        
        output = BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
        output.write(pdf_bytes)
        output.seek(0)
        return output
        
    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF: {str(e)}")
        return None



# =========================
#   THÈMES
# =========================
PRESET_THEMES = {
    "Brillant": {
        "bg": "#ffffff", "surface": "#ffffff", "surface_alt": "#f3f6fb",
        "text": "#1f2a37", "subtext": "#6b7280",
        "primary": "#6a11cb", "secondary": "#2575fc",
        "tab_unselected": "#eef2f7",
        "font": "Montserrat"
    },
    "Smart": {
        "bg": "#0b1220", "surface": "#0f172a", "surface_alt": "#111827",
        "text": "#e5e7eb", "subtext": "#9ca3af",
        "primary": "#f59e0b", "secondary": "#f97316",
        "tab_unselected": "#1f2937",
        "font": "Inter"
    },
    "Océan": {
        "bg": "#0b132b", "surface": "#1c2541", "surface_alt": "#3a506b",
        "text": "#e6f1ff", "subtext": "#c7d2fe",
        "primary": "#2ec4b6", "secondary": "#5bc0eb",
        "tab_unselected": "#23395d",
        "font": "Poppins"
    },
    "Énergie": {
        "bg": "#1a1a1a", "surface": "#212121", "surface_alt": "#303030",
        "text": "#f5f5f5", "subtext": "#cfcfcf",
        "primary": "#ef4444", "secondary": "#f59e0b",
        "tab_unselected": "#2a2a2a",
        "font": "Montserrat"
    },
    "Émeraude": {
        "bg": "#f6fffb", "surface": "#ffffff", "surface_alt": "#ecfdf5",
        "text": "#064e3b", "subtext": "#10b981",
        "primary": "#10b981", "secondary": "#059669",
        "tab_unselected": "#e6f7f1",
        "font": "Inter"
    },
    "Sépia": {
        "bg": "#faf5ef", "surface": "#fdf8f2", "surface_alt": "#f5efe6",
        "text": "#3f2d20", "subtext": "#7b5e47",
        "primary": "#a97155", "secondary": "#d4a373",
        "tab_unselected": "#efe5da",
        "font": "Roboto"
    },
}

def theme_picker_ui():
    st.sidebar.title("🎨 Thèmes & style")
    if lottie_theme: st.sidebar.lottie(lottie_theme, height=80, key="theme_anim")

    preset_name = st.sidebar.selectbox("Choisir un thème", list(PRESET_THEMES.keys()), index=0)
    preset = PRESET_THEMES[preset_name].copy()

    st.sidebar.markdown("— ou —")
    use_custom = st.sidebar.checkbox("Personnaliser ce thème", False)

    if use_custom:
        c1, c2 = st.sidebar.columns(2)
        preset["primary"]   = c1.color_picker("Couleur primaire", preset["primary"])
        preset["secondary"] = c2.color_picker("Couleur secondaire", preset["secondary"])
        c3, c4 = st.sidebar.columns(2)
        preset["text"]      = c3.color_picker("Texte", preset["text"])
        preset["bg"]        = c4.color_picker("Fond global", preset["bg"])
        c5, c6 = st.sidebar.columns(2)
        preset["surface"]   = c5.color_picker("Surface", preset["surface"])
        preset["surface_alt"]=c6.color_picker("Surface alt", preset["surface_alt"])
        preset["tab_unselected"] = st.sidebar.color_picker("Onglet inactif", preset["tab_unselected"])
        preset["font"] = st.sidebar.selectbox("Police", ["Roboto","Montserrat","Inter","Poppins"], index= ["Roboto","Montserrat","Inter","Poppins"].index(preset["font"]))
    return preset

def inject_font_css(font_family: str, base_font_size: str):
    st.markdown(f"""
    <style>
      html, body, [class*="css"] {{
        font-family: {font_family}, sans-serif !important;
        font-size: {base_font_size};
      }}
    </style>
    """, unsafe_allow_html=True)

# =========================
#   RAPPORTS (PDF/MD)
# =========================
def build_report_md(df: pd.DataFrame, title: str, author: str, variant: str):
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    report = f"# {title}\n\n"
    report += f"**Auteur :** {author}\n\n"
    report += f"**Date :** {now}\n\n"
    report += f"**Type :** {variant}\n\n"
    report += f"**Nombre d'entreprises analysées :** {len(df)}\n\n"

    if 'score' in df.columns and pd.api.types.is_numeric_dtype(df['score']):
        report += "## 📊 Analyse des Scores\n"
        report += f"- Score moyen : {df['score'].mean():.2f}\n"
        report += f"- Score médian : {df['score'].median():.2f}\n"
        report += f"- Écart-type : {df['score'].std():.2f}\n"
        report += f"- Score minimum : {df['score'].min():.2f}\n"
        report += f"- Score maximum : {df['score'].max():.2f}\n\n"

        # Top 5 des entreprises
        top5 = df.sort_values('score', ascending=False).head(5)
        report += "### 🏆 Top 5 des entreprises\n"
        for i, (_, row) in enumerate(top5.iterrows(), 1):
            report += f"{i}. **{row.get('name', 'N/A')}** - Score: {row.get('score', 'N/A'):.1f}\n"
        report += "\n"

    if 'country' in df.columns:
        country_counts = df['country'].dropna().astype(str).value_counts()
        if len(country_counts) > 0:
            report += "## 🌍 Répartition géographique\n"
            report += f"- Nombre total de pays : {len(country_counts)}\n"
            report += "### Pays les plus représentés :\n"
            for country, count in country_counts.head(5).items():
                report += f"- {country}: {count} entreprises\n"
            report += "\n"

    if 'keywords' in df.columns:
        all_keywords = [kw for sublist in df['keywords'] for kw in (sublist if isinstance(sublist, list) else [sublist])]
        kw_counts = Counter(all_keywords)
        if len(kw_counts) > 0:
            report += "## 🔑 Mots-clés dominants\n"
            report += f"- Nombre de mots-clés uniques : {len(kw_counts)}\n"
            report += "### Top 10 des mots-clés :\n"
            for kw, count in kw_counts.most_common(10):
                report += f"- {kw} (apparaît {count} fois)\n"
            report += "\n"

    if variant == "Rapport final":
        report += "## 🚀 Recommandations stratégiques\n"
        report += "- **Prioriser** les acteurs avec un score ≥ 7\n"
        report += "- **Surveiller** les mots-clés émergents\n"
        report += "- **Explorer** les zones géographiques sous-représentées\n"
        report += "- **Analyser** les pratiques des leaders (top 5)\n"
        report += "- **Identifier** les opportunités dans les segments faiblement notés\n"

    return report

def build_pdf_from_text(title: str, body_text: str, filename: str) -> BytesIO | None:
    """
    Génère un PDF via FPDF en translittérant les caractères non supportés.
    Version corrigée pour le problème BytesIO.
    """
    try:
        from fpdf import FPDF
        import unicodedata
    except Exception:
        return None

    def normalize_text(text):
        """Convertit les caractères Unicode en leur équivalent ASCII le plus proche"""
        normalized = []
        for char in text:
            # Table de remplacement pour caractères spéciaux courants
            replacements = {
                '–': '-', '—': '-', '‘': "'", '’': "'", '“': '"', '”': '"',
                '…': '...', '•': '*', 'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                'à': 'a', 'â': 'a', 'ä': 'a', 'î': 'i', 'ï': 'i',
                'ô': 'o', 'ö': 'o', 'ù': 'u', 'û': 'u', 'ü': 'u',
                'ç': 'c', 'œ': 'oe', 'æ': 'ae', '€': 'EUR', '£': 'GBP'
            }
            if char in replacements:
                normalized.append(replacements[char])
            else:
                # Essayer de décomposer le caractère (é -> e + ´)
                decomposed = unicodedata.normalize('NFKD', char)
                # Garder seulement la partie base (supprime les accents)
                ascii_char = ''.join(c for c in decomposed if not unicodedata.combining(c))
                if ascii_char.isascii() and ascii_char.isprintable():
                    normalized.append(ascii_char)
                else:
                    normalized.append('?')  # Caractères inconnus
        return ''.join(normalized)

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Utiliser une police par défaut qui supporte les caractères de base
        pdf.set_font("Arial", size=12)

        # Titre (normalisé)
        pdf.set_font("Arial", "B", 16)
        pdf.multi_cell(0, 10, normalize_text(title))
        pdf.ln(4)

        # Corps du texte (normalisé ligne par ligne)
        pdf.set_font("Arial", size=12)
        for line in body_text.split("\n"):
            pdf.multi_cell(0, 8, normalize_text(line))

        # Version corrigée pour l'output
        mem = BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
        mem.write(pdf_bytes)
        mem.seek(0)
        return mem
        
    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF: {str(e)}")
        return None

# =========================
#   INTRODUCTION
# =========================
def show_introduction():
    """Affiche l'introduction avec le logo uniquement"""
    logo_html = ""
    if logo_bytes:
        logo_html = f'<img src="data:image/png;base64,{base64.b64encode(logo_bytes).decode()}" width="60">'
    
    st.markdown(f"""
    <div class="header">
        <div style="display:flex; align-items:center; gap:15px;">
            {logo_html}
            <div>
                <h1 style="margin-bottom:6px;">Analyse concurrentielle</h1>
                <p class="subheader">Outils stratégique pour l'équipe Navitrends</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### Objectifs stratégiques
    - Comparaison approfondie des acteurs du marché
    - Identification des tendances clés
    - Analyse des positionnements concurrentiels
    """)

# =========================
#   APPLICATION PRINCIPALE
# =========================
def main():
    # CSS de base
    local_css("style.css")

    # --- Sidebar : Thèmes & Style ---
    theme = theme_picker_ui()
    apply_theme_css(theme)

    st.sidebar.subheader("✏️ Typographie")
    inject_font_css(theme["font"], st.sidebar.select_slider("Taille du texte", ["14px","15px","16px","17px","18px"], value="16px"))

    # Charger le logo directement si disponible
    logo_bytes = None
    if os.path.exists("logos/logo-navitrends.png"):
        with open("logos/logo-navitrends.png", "rb") as f:
            logo_bytes = f.read()

    # --- Introduction ---
    show_introduction()

    # --- Fichiers sources ---
    st.sidebar.header("📂 Sources & fichiers")
    file_options = {
        "Résultats bruts": "resultats.json",
        "Résultats nettoyés": "resultats_clean.json",
        "Résultats finaux": "resultats_final.json"
    }
    selected_label = st.sidebar.selectbox("Fichier à analyser", options=list(file_options.keys()), index=2)
    selected_path = file_options[selected_label]

    for label, path in file_options.items():
        if os.path.exists(path):
            st.sidebar.markdown(get_file_download_link(path, label), unsafe_allow_html=True)

    # --- Chargement données ---
    df = load_data(selected_path)
    if df.empty:
        st.warning("Le fichier sélectionné ne contient aucune donnée valide.")
        return

    # --- Filtres rapides dans la page ---
    st.markdown("## 🔍 Filtre express")
    filt_col1, filt_col2, filt_col3, filt_col4 = st.columns([2,2,2,2])

    name_query = filt_col1.text_input("Rechercher par nom", value="", placeholder="Tapez une entreprise…")

    score_cats = {
        "Excellence (≥ 8)": lambda s: s >= 8,
        "Fort (6 – 8)":    lambda s: (s >= 6) & (s < 8),
        "Moyen (3 – 6)":   lambda s: (s >= 3) & (s < 6),
        "Faible (< 3)":    lambda s: s < 3
    }
    cat_selected = filt_col2.multiselect("Catégories de score", list(score_cats.keys()), default=[])

    country_selected = []
    if "country" in df.columns:
        countries = sorted([c for c in df["country"].dropna().astype(str).unique()])
        country_selected = filt_col3.multiselect("Pays", options=countries, default=[])

    sort_choice = filt_col4.selectbox("Tri", ["Nom (A→Z)", "Nom (Z→A)", "Score (↓)", "Score (↑)"], index=0)

    filtered_df = df.copy()
    if name_query.strip() and "name" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["name"].astype(str).str.contains(name_query.strip(), case=False, na=False)]

    if "score" in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df["score"]) and cat_selected:
        mask_global = False
        for cat in cat_selected:
            mask = score_cats[cat](filtered_df["score"])
            mask_global = mask if mask_global is False else (mask_global | mask)
        filtered_df = filtered_df[mask_global]

    if country_selected and "country" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["country"].astype(str).isin(country_selected)]

    if sort_choice == "Nom (A→Z)" and "name" in filtered_df.columns:
        filtered_df = filtered_df.sort_values("name", ascending=True, kind="stable")
    elif sort_choice == "Nom (Z→A)" and "name" in filtered_df.columns:
        filtered_df = filtered_df.sort_values("name", ascending=False, kind="stable")
    elif sort_choice == "Score (↓)" and "score" in filtered_df.columns:
        filtered_df = filtered_df.sort_values("score", ascending=False, kind="stable")
    elif sort_choice == "Score (↑)" and "score" in filtered_df.columns:
        filtered_df = filtered_df.sort_values("score", ascending=True, kind="stable")

    # --- KPIs ---
    st.markdown("## 📈 Indicateurs clés")
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-header"><span class="kpi-icon">🏢</span><span class="kpi-title">Entreprises</span></div>
            <div class="kpi-value">{len(filtered_df)}</div>
            <div class="kpi-desc">Total filtré</div>
        </div>
        """, unsafe_allow_html=True)

    primary_color = theme["primary"]
    secondary_color = theme["secondary"]

    if "score" in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df["score"]):
        with cols[1]:
            avg_score = float(filtered_df["score"].mean()) if len(filtered_df) else 0.0
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-header"><span class="kpi-icon">⭐</span><span class="kpi-title">Score moyen</span></div>
                <div class="kpi-value">{avg_score:.1f}</div>
                <div class="kpi-desc">/10</div>
            </div>
            """, unsafe_allow_html=True)

        with cols[2]:
            gauge_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_score,
                number={'suffix': " /10"},
                gauge={
                    "axis": {"range": [0, 10]},
                    "bar": {"color": primary_color},
                    "steps": [
                        {"range": [0, 3], "color": "#f8d7da"},
                        {"range": [3, 6], "color": "#fff3cd"},
                        {"range": [6, 8], "color": "#cfe2ff"},
                        {"range": [8,10], "color": "#d1e7dd"},
                    ]
                }
            ))
            gauge_fig.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10), transition_duration=400)
            st.plotly_chart(gauge_fig, use_container_width=True)

    if "country" in filtered_df.columns:
        with cols[3]:
            unique_countries = len(filtered_df["country"].dropna().unique())
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-header"><span class="kpi-icon">🌍</span><span class="kpi-title">Pays</span></div>
                <div class="kpi-value">{unique_countries}</div>
                <div class="kpi-desc">Représentés</div>
            </div>
            """, unsafe_allow_html=True)

    # --- VISUALISATIONS ---
    st.markdown("## 📊 Visualisations interactives")
    tab1, tab2, tab3 = st.tabs(["📊 Analyse stratégique", "📈 Comparaison", "💾 Données & export"])
    with tab1:
        # Vérifier d'abord si les données nécessaires existent
        if filtered_df.empty:
            st.warning("Aucune donnée à afficher après filtrage")
        else:
            # Histogramme des scores
            if "score" in filtered_df.columns:
                try:
                    st.markdown("### Distribution des scores")
                    fig = px.histogram(
                        filtered_df, 
                        x="score", 
                        nbins=20,
                        color_discrete_sequence=[primary_color],
                        labels={"score": "Score de compétitivité"}
                    )
                    fig.update_layout(
                        bargap=0.1, 
                        xaxis_title="Score (0-10)", 
                        yaxis_title="Nombre d'entreprises"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Erreur lors de la création de l'histogramme: {str(e)}")

            # Nuage de mots-clés
            if "keywords" in filtered_df.columns:
                try:
                    st.markdown("### Nuage de mots-clés stratégiques")
                    all_kw = ' '.join(' '.join(kws) if isinstance(kws, list) else str(kws) 
                            for kws in filtered_df['keywords'].dropna())
                    if all_kw.strip():
                        wordcloud = WordCloud(
                            width=1200, 
                            height=480,
                            background_color="white",
                            colormap='plasma',
                            max_words=200
                        ).generate(all_kw)
                        fig, ax = plt.subplots(figsize=(12, 4.5))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis('off')
                        st.pyplot(fig)
                    else:
                        st.info("Aucun mot-clé disponible après filtrage")
                except Exception as e:
                    st.error(f"Erreur lors de la création du nuage de mots-clés: {str(e)}")

            # Scores par entreprise
            if "name" in filtered_df.columns and "score" in filtered_df.columns:
                try:
                    st.markdown("### Scores par entreprise")
                    sc = px.scatter(
                        filtered_df.assign(_index=range(len(filtered_df))),
                        x="score",
                        y="_index",
                        text="name",
                        color_discrete_sequence=[secondary_color]
                    )
                    sc.update_traces(textposition="middle right")
                    sc.update_layout(
                        yaxis={"showticklabels": False},
                        height=560
                    )
                    st.plotly_chart(sc, use_container_width=True)
                except Exception as e:
                    st.error(f"Erreur lors de la création du graphique des scores: {str(e)}")
    # --- COMPARAISONS & CARTES ---

    with tab2:
        st.markdown("### Comparaison des entreprises")
        
        if 'name' not in filtered_df.columns:
            st.warning("La colonne 'name' est manquante dans les données")
        else:
            companies = filtered_df['name'].dropna().unique().tolist()
            
            if not companies:
                st.warning("Aucune entreprise disponible pour comparaison")
            else:
                selected_companies = st.multiselect(
                    "Sélectionnez jusqu'à 10 entreprises",
                    companies,
                    default=companies[:min(3, len(companies))],
                    max_selections=10
                )
                
                if selected_companies:
                    compare_df = filtered_df[filtered_df['name'].isin(selected_companies)]
                    
                    # Graphique de comparaison
                    if not compare_df.empty and 'score' in compare_df.columns:
                        fig = px.bar(
                            compare_df,
                            x='name',
                            y='score',
                            color='name',
                            title="Comparaison des scores"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Tableau comparatif
                    display_cols = ['score']
                    if 'country' in compare_df.columns:
                        display_cols.append('country')
                    if 'keywords' in compare_df.columns:
                        display_cols.append('keywords')
                    
                    if display_cols:
                        st.dataframe(
                            compare_df.set_index('name')[display_cols],
                            use_container_width=True
                        )

    with tab3:
        st.markdown("### Données filtrées (triables & exportables)")
        st.markdown('<div class="viz-explanation">Recherchez, filtrez, triez et exportez.</div>', unsafe_allow_html=True)

        display_cols = [c for c in ["name","score","country","keywords"] if c in filtered_df.columns] or list(filtered_df.columns)
        st.dataframe(filtered_df[display_cols], height=600, use_container_width=True)

        exp1, exp2 = st.columns(2)
        csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
        exp1.download_button("📥 Télécharger CSV (filtré)", data=csv_bytes, file_name=f"navitrends_filtre_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        json_payload = filtered_df.to_dict(orient="records")
        exp2.download_button("📥 Télécharger JSON (filtré)", data=json.dumps(json_payload, ensure_ascii=False, indent=2),
                             file_name=f"navitrends_filtre_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json")

    # --- EXPORTATION DU DASHBOARD ---
    st.markdown("## 🧾 Exportation des Résultats")
    
    tab_export, tab_reports = st.tabs(["📦 Export Complet", "📝 Rapports Analytiques"])
    
    with tab_export:
        st.markdown("""
        ### Export complet du dashboard
        Génère un document PDF contenant :
        - Les indicateurs clés actuels
        - Les principales visualisations
        - Un résumé des données filtrées
        """)
        
        if st.button("🖨️ Générer l'export complet", key="export_full"):
            with st.spinner("Génération du PDF en cours..."):
                export = capture_full_dashboard(filtered_df)
                if export:
                    st.download_button(
                        label="📥 Télécharger l'export complet",
                        data=export,
                        file_name=f"navitrends_export_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
    
    with tab_reports:
        st.markdown("""
        ### Rapports analytiques
        Téléchargez les rapports d'analyse complets :
        - **Rapport primaire** : Version initiale de l'analyse
        - **Rapport final** : Analyse complète avec recommandations
        """)

        col1, col2, col3 = st.columns(3)

        # Rapport primaire
        with col1:
            st.markdown("#### Rapport Primaire")
            st.markdown("Contient les premières observations et données brutes")
            if os.path.exists("rapport_sites.pdf"):
                with open("rapport_sites.pdf", "rb") as f:
                    st.download_button(
                        "📥 Télécharger le rapport primaire",
                        data=f,
                        file_name="rapport_primaire.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("Fichier rapport_site.pdf introuvable")
    # Rapport primaire
        with col2:
            st.markdown("#### Rapport Primaire")
            st.markdown("Contient les données nettoyées et prétraitées")
            if os.path.exists("rapport_entreprises.pdf"):
                with open("rapport_entreprises.pdf", "rb") as f:
                    st.download_button(
                        "📥 Télécharger le rapport nettoyé",
                        data=f,
                        file_name="rapport_entreprises.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("Fichier rapport_entreprises.pdf introuvable")

        # Rapport final
        with col3:
            st.markdown("#### Rapport Final")
            st.markdown("Version finale avec recommandations stratégiques")
            if os.path.exists("rapport_final.pdf"):
                with open("rapport_final.pdf", "rb") as f:
                    st.download_button(
                        "📥 Télécharger le rapport final",
                        data=f,
                        file_name="rapport_final.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("Fichier rapport_final.pdf introuvable")

if __name__ == "__main__":
    main()
