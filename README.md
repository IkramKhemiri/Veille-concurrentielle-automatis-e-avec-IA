# 📊 Projet Veille concurrentielle automatisée avec IA  — Dashboard & Analyse de données

Ce projet permet de **scraper, nettoyer, analyser et visualiser** des données d'entreprises et freelances, avec génération automatique de rapports PDF et graphiques.  
Il intègre du **NLP** (analyse sémantique, TF-IDF), de la **visualisation** et une **interface Dashboard**. C'est une solution intelligente qui **collecte, analyse et présente automatiquement** des données issues du web  
(sites de concurrents, plateformes de freelancing, annuaires professionnels…)  
afin d'aider les équipes commerciales à :
- Mieux comprendre le marché
- Surveiller la concurrence
- Détecter de nouvelles opportunités

---

## 📂 Structure du projet

TEST
│
├── 📁 .venv  
│   Environnement virtuel Python (packages et dépendances).
│
├── 📁 analyse  
│   ├── 📁 __pycache__ — Cache Python compilé.  
│   ├── 📄 analyseur_semantique.py — Analyse sémantique des textes.  
│   ├── 📄 classifier_theme.py — Classification thématique.  
│   └── 📄 resumeur.py — Génération de résumés automatiques.
│
├── 📁 debug  
│   Fichiers ou logs pour le débogage.
│
├── 📁 drivers  
│   ├── 📁 chromedriver-win64 — Driver Chrome pour Selenium.  
│   ├── 📁 edgedriver_win64 — Driver Edge pour Selenium.  
│   ├── ⚙️ chromedriver.exe — Exécutable du driver Chrome.  
│   ├── 📦 edgedriver_win64.zip — Archive driver Edge.  
│   └── ⚙️ msedgedriver.exe — Exécutable du driver Edge.
│
├── 📁 fonts  
│   Polices utilisées dans les rapports PDF et graphiques.
│
├── 📁 logos  
│   Logos des entreprises ou plateformes.
│
├── 📁 models  
│   └── 🧠 mistral-7b-instruct-v0.1.Q4_K_M.gguf — Modèle NLP local pour analyses.
│
├── 📁 scraping  
│   ├── 📁 __pycache__ — Cache Python compilé.  
│   ├── 📁 cleaned — Données nettoyées après scraping.  
│   ├── 📄 ai_analysis.py — Analyse IA des contenus extraits.  
│   ├── 📄 browser.py — Gestion du navigateur Selenium.  
│   ├── 📄 cleaner.py — Nettoyage des données brutes.  
│   ├── 📄 crawler.py — Parcours et collecte des données.  
│   ├── 📄 extractor.py — Extraction d’informations ciblées.  
│   ├── 📄 scraper_dynamic.py — Scraping dynamique (JavaScript).  
│   ├── 📄 scraper_static.py — Scraping statique (HTML simple).  
│   ├── 📄 section_extractor.py — Extraction de sections spécifiques.  
│   └── 📄 text_classifier.py — Classification de textes.
│
├── 📁 screenshots  
│   Captures d’écran des pages scrappées.
│
├── 📁 utils  
│   ├── 📁 __pycache__ — Cache Python compilé.  
│   ├── 📄 analyse_nlp.py — Traitement NLP.  
│   ├── 📄 analyse_tfidf.py — Analyse TF-IDF des mots clés.  
│   ├── 📄 detection.py — Détection d’informations (emails, numéros, etc.).  
│   ├── 📄 io_handler.py — Gestion lecture/écriture de fichiers.  
│   ├── 📄 pdf_report.py — Génération de rapports PDF.  
│   ├── 📄 rapport_final.py — Génération du rapport final consolidé.  
│   └── 📄 synthese_nlp.py — Synthèse des analyses NLP.
│
├── 📁 visualisations  
│   📊 Graphiques et nuages de mots générés.  
│   ├── 🖼 global_bigrams_wc.png — Nuage de mots (bigrams).  
│   ├── 🖼 global_bigrams.png — Graphique bigrams.  
│   ├── 🖼 global_trigrams_wc.png — Nuage de mots (trigrams).  
│   └── 🖼 global_trigrams.png — Graphique trigrams.
│
├── 📝 content_cleaner.log — Journal du nettoyage de contenu.  
├── 📄 dashboard.py — Interface Dashboard (Streamlit).  
├── 📄 envoi_mail.py — Envoi automatique des rapports par mail.  
├── 📄 json_to_pdf.py — Conversion JSON → PDF.  
├── 🗂 logo_mapping.json — Mapping entre noms et fichiers logos.  
├── 📄 multi_scraper.py — Lance plusieurs scrapers en parallèle.  
├── 📄 nettoyage_base.py — Script de nettoyage de la base de données.  
├── 📄 nlp_tfidf_visualisation.py — Visualisation des scores TF-IDF.  
├── 📝 pipeline.log — Journal d’exécution du pipeline.  
├── 📄 runall.py — Lance tout le pipeline complet.  
├── 📝 scraper.log — Journal du scraping.  
├── 📄 style.css — Feuille de style pour le Dashboard.  
├── 📄 sites.csv — Liste des sites à scraper.
│
├── 📄 resultats_clean.json — Résultats nettoyés.  
├── 📄 resultats_final.json — Résultats finaux après traitement.  
├── 📄 resultats.json — Résultats bruts.
│
├── 📄 rapport_entreprises.pdf — Rapport PDF entreprises.  
├── 📄 rapport_final.pdf — Rapport PDF final.  
├── 🖼 rapport_freelance_*.png — Graphiques des rapports freelances.  
└── 📄 rapport_sites.pdf — Rapport PDF par site.
