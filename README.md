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

Voici la structure détaillée du projet, enrichie avec des explications pour mieux comprendre le rôle de chaque fichier et dossier :

TEST-CLEAN 
│  
├── 📁 .venv  
│   → Environnement virtuel Python qui contient tous les packages et dépendances nécessaires au projet.  
│  
├── 📁 analyse  
│   → Scripts d’analyse intelligente (NLP, classification, résumé). C’est le cerveau du projet côté traitement du texte.  
│   ├── 📁 __pycache__  
│   │   → Cache Python généré automatiquement (peut être ignoré).  
│   ├── 📄 analyseur_semantique.py  
│   │   → Analyse le sens et les relations entre les mots pour enrichir la compréhension des textes.  
│   ├── 📄 classifier_theme.py  
│   │   → Classe les textes dans des thématiques précises (ex : marketing, IT, design).  
│   └── 📄 resumeur.py  
│       → Génère automatiquement des résumés synthétiques et clairs à partir des textes collectés.  
│  
├── 📁 debug  
│   → Contient des fichiers et logs utiles pour tester et corriger les erreurs du projet.  
│  
├── 📁 drivers  
│   → Drivers pour automatiser les navigateurs avec Selenium (Chrome, Edge).  
│   ├── 📁 chromedriver-win64  
│   ├── 📁 edgedriver_win64  
│   ├── ⚙️ chromedriver.exe  
│   ├── 📦 edgedriver_win64.zip  
│   └── ⚙️ msedgedriver.exe  
│       → Sans ces drivers, impossible de contrôler les navigateurs pour extraire les données.  
│  
├── 📁 fonts  
│   → Polices personnalisées utilisées dans les rapports PDF et les visualisations graphiques.  
│  
├── 📁 logos  
│   → Regroupe les logos des entreprises et plateformes scrappées, utilisés dans les rapports.  
│  
├── 📁 models  
│   → Modèles d’IA locaux utilisés pour les analyses avancées.  
│   └── 🧠 mistral-7b-instruct-v0.1.Q4_K_M.gguf  
│       → Un modèle NLP performant pour résumer, classer et analyser les textes.  
│  
├── 📁 scraping  
│   → Le moteur de collecte des données. Tous les scripts pour extraire, nettoyer et préparer les informations.  
│   ├── 📁 __pycache__  
│   ├── 📁 cleaned  
│   │   → Données déjà nettoyées après le scraping, prêtes à être analysées.  
│   ├── 📄 ai_analysis.py  
│   │   → Analyse assistée par IA du contenu collecté.  
│   ├── 📄 browser.py  
│   │   → Gère le navigateur Selenium (ouvrir, naviguer, fermer).  
│   ├── 📄 cleaner.py  
│   │   → Nettoie les données brutes en supprimant le bruit (balises HTML, caractères spéciaux, etc.).  
│   ├── 📄 crawler.py  
│   │   → Parcourt automatiquement les pages pour récupérer des liens et contenus.  
│   ├── 📄 extractor.py  
│   │   → Extrait des informations ciblées comme emails, téléphones, descriptions.  
│   ├── 📄 scraper_dynamic.py  
│   │   → Scraping des sites dynamiques (JavaScript, contenus générés en temps réel).  
│   ├── 📄 scraper_static.py  
│   │   → Scraping plus simple, basé uniquement sur le HTML statique.  
│   ├── 📄 section_extractor.py  
│   │   → Repère et extrait des sections précises (ex : "À propos", "Services").  
│   └── 📄 text_classifier.py  
│       → Classe automatiquement les textes scrappés par type ou catégorie.  
│  
├── 📁 screenshots  
│   → Captures d’écran des pages scrappées, utiles pour vérifier ou documenter les résultats.  
│  
├── 📁 utils  
│   → Boîte à outils du projet : tout ce qui facilite la manipulation des données et des rapports.  
│   ├── 📁 __pycache__  
│   ├── 📄 analyse_nlp.py  
│   │   → Fonctions de traitement NLP (analyse linguistique avancée).  
│   ├── 📄 analyse_tfidf.py  
│   │   → Calcule l’importance des mots dans les textes grâce à la méthode TF-IDF.  
│   ├── 📄 detection.py  
│   │   → Détecte des infos clés comme emails, numéros de téléphone, adresses.  
│   ├── 📄 io_handler.py  
│   │   → Gère la lecture et l’écriture des fichiers (JSON, CSV, etc.).  
│   ├── 📄 pdf_report.py  
│   │   → Génère automatiquement des rapports PDF professionnels.  
│   ├── 📄 rapport_final.py  
│   │   → Assemble toutes les analyses en un rapport final clair et structuré.  
│   └── 📄 synthese_nlp.py  
│       → Produit une synthèse globale des résultats NLP (résumés, mots-clés, tendances).  
│  
├── 📁 visualisations  
│   → Résultats visuels : graphiques et nuages de mots pour illustrer les analyses.  
│   ├── 🖼 global_bigrams_wc.png  
│   ├── 🖼 global_bigrams.png  
│   ├── 🖼 global_trigrams_wc.png  
│   └── 🖼 global_trigrams.png  
│       → Ces images aident à comprendre rapidement les thèmes dominants.  
│  
├── 📝 content_cleaner.log  
│   → Journal listant les étapes de nettoyage du contenu.  
├── 📄 dashboard.py  
│   → Interface utilisateur (Streamlit). La vitrine interactive du projet.  
├── 📄 envoi_mail.py  
│   → Automatise l’envoi des rapports PDF aux destinataires (équipe, clients).  
├── 📄 json_to_pdf.py  
│   → Convertit des données JSON en rapports PDF lisibles.  
├── 🗂 logo_mapping.json  
│   → Associe chaque entreprise à son logo pour enrichir les rapports visuellement.  
├── 📄 multi_scraper.py  
│   → Lance plusieurs scrapers en parallèle pour gagner du temps.  
├── 📄 nettoyage_base.py  
│   → Nettoie la base de données consolidée.  
├── 📄 nlp_tfidf_visualisation.py  
│   → Génère des visualisations des scores TF-IDF (importance des mots).  
├── 📝 pipeline.log  
│   → Journal d’exécution complet du pipeline.  
├── 📄 runall.py  
│   → Script chef d’orchestre qui lance tout le pipeline (scraping → analyse → rapport).  
├── 📝 scraper.log  
│   → Journal dédié uniquement au scraping.  
├── 📄 style.css  
│   → Feuille de style qui personnalise l’apparence du Dashboard.  
├── 📄 sites.csv  
│   → Liste des sites web à analyser (point de départ du scraping).  
│  
├── 📄 resultats_clean.json  
│   → Résultats après nettoyage.  
├── 📄 resultats_final.json  
│   → Résultats finaux consolidés et prêts pour les rapports.  
├── 📄 resultats.json  
│   → Résultats bruts directement issus du scraping.  
│  
├── 📄 rapport_entreprises.pdf  
│   → Rapport PDF focalisé sur les entreprises.  
├── 📄 rapport_final.pdf  
│   → Rapport PDF global (entreprises + freelances).  
├── 🖼 rapport_freelance_*.png  
│   → Graphiques dédiés aux freelances.  
└── 📄 rapport_sites.pdf  
    → Rapport PDF par site scrappé.  

---

## ✨ Fonctionnalités principales

Le projet offre une gamme complète de fonctionnalités pour automatiser la veille concurrentielle et produire des résultats exploitables :

### 1. **Scraping multi-site**
- **Description** : Collecte des données à partir de plusieurs sites web en parallèle, en combinant des approches dynamiques (JavaScript) et statiques (HTML brut).
- **Impact** : Réduit le temps de collecte des données et garantit une couverture maximale des sources.

### 2. **Nettoyage et structuration des données**
- **Description** : Supprime les éléments inutiles (URLs, images, etc.), détecte la langue des contenus et structure les données en catégories exploitables (services, technologies, clients).
- **Impact** : Prépare les données pour une analyse approfondie et garantit leur qualité.

### 3. **Analyse NLP avancée**
- **Description** : Applique des techniques de lemmatisation, tokenisation et TF-IDF pour extraire les mots-clés les plus pertinents. Génère également des statistiques globales sur les cooccurrences et les tendances.
- **Impact** : Identifie les termes et expressions clés pour mieux comprendre les tendances du marché.

### 4. **Visualisations interactives et statiques**
- **Description** : Génère des graphiques (histogrammes, nuages de mots, heatmaps) et des réseaux interactifs pour explorer les données.
- **Impact** : Facilite l'interprétation des résultats et leur présentation aux parties prenantes.

### 5. **Génération de rapports PDF**
- **Description** : Produit des rapports PDF professionnels avec des sections détaillées pour chaque entreprise, incluant des introductions générées automatiquement.
- **Impact** : Fournit un livrable clé pour les clients ou les décideurs.

### 6. **Dashboard interactif**
- **Description** : Interface utilisateur intuitive pour explorer les résultats, filtrer les données et télécharger les rapports.
- **Impact** : Rend les résultats accessibles et exploitables par tous les membres de l'équipe.

### 7. **Automatisation de l'envoi des rapports**
- **Description** : Envoie automatiquement les rapports par email aux parties prenantes, avec des pièces jointes et un contenu personnalisé.
- **Impact** : Réduit les tâches manuelles et garantit une communication régulière.

---

## 🛠️ Technologies utilisées

Le projet repose sur un ensemble de technologies modernes et performantes, soigneusement sélectionnées pour répondre aux besoins spécifiques de chaque étape du pipeline :

### 1. **Python**
- **Pourquoi ?** : Langage polyvalent et riche en bibliothèques pour le scraping, l'analyse NLP et la visualisation.
- **Impact** : Permet une intégration fluide de toutes les étapes du pipeline.

### 2. **Selenium & BeautifulSoup**
- **Pourquoi ?** : Selenium pour le scraping dynamique (JavaScript) et BeautifulSoup pour le scraping statique (HTML brut).
- **Impact** : Garantit une collecte de données robuste et flexible.

### 3. **Spacy**
- **Pourquoi ?** : Pour la tokenisation, la lemmatisation et la détection de langue.
- **Impact** : Fournit une base solide pour les analyses NLP.

### 4. **Scikit-learn**
- **Pourquoi ?** : Pour le calcul des scores TF-IDF et l'extraction des mots-clés.
- **Impact** : Identifie les termes les plus pertinents dans les données textuelles.

### 5. **Matplotlib, Seaborn & Plotly**
- **Pourquoi ?** : Pour créer des visualisations statiques et interactives.
- **Impact** : Facilite l'exploration et la présentation des résultats.

### 6. **FPDF**
- **Pourquoi ?** : Pour générer des rapports PDF professionnels.
- **Impact** : Produit des livrables clairs et bien structurés.

### 7. **Streamlit**
- **Pourquoi ?** : Pour développer le Dashboard interactif.
- **Impact** : Offre une interface utilisateur intuitive et moderne.

### 8. **Llama.cpp**
- **Pourquoi ?** : Pour utiliser un modèle NLP local (Mistral) pour les analyses avancées.
- **Impact** : Permet des analyses sémantiques précises sans dépendre d'une API externe.

---

## 📖 Manuel d'utilisation

### Prérequis :
1. **Python 3.8+** : Assurez-vous que Python est installé sur votre machine.
2. **Navigateurs et drivers** :
   - Installez **Google Chrome** ou **Microsoft Edge**.
   - Téléchargez les drivers correspondants (ex. `chromedriver.exe`).

### Installation des dépendances :
1. Clonez le projet :

   git clone https://github.com/IkramKhemiri/Veille-concurrentielle-automatis-e-avec-IA.git

2. Créez un environnement virtuel :

python -m venv .venv
source .venv/bin/activate  # Sur Windows : .venv\Scripts\activate

3. Installez les dépendances :

pip install -r requirements.txt

4. Téléchargez les modèles NLP nécessaires :

python -m spacy download fr_core_news_md
python -m spacy download en_core_web_md

5. Exécution du pipeline complet :
python runall.py

5. 1. Lancez le script principal :

python runall.py

5. 2. Accédez au Dashboard :

streamlit run dashboard.py

5. 3. Explorez les résultats et téléchargez les rapports.


