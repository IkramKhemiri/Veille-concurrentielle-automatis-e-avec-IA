"""
Rôle global :
Ce module est un outil avancé de nettoyage et d'enrichissement des données extraites des sites web. 
Il combine des techniques de traitement de texte basées sur des expressions régulières, des bibliothèques de parsing HTML, 
et un modèle d'IA local (Mistral via llama.cpp) pour produire des données nettoyées, classifiées et enrichies. 
Il génère également des introductions professionnelles et détecte automatiquement la langue des contenus.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle crucial en transformant 
les données brutes extraites en informations exploitables. Il garantit que les données sont propres, bien structurées, 
et prêtes pour les étapes d'analyse et de visualisation. Sans cette étape, les données seraient désorganisées et difficiles à exploiter.

Comment il aide dans le pipeline :
- **Scraping** : Nettoie et structure les données brutes extraites des sites web.
- **Analyse** : Classifie automatiquement les informations (services, technologies, clients, etc.) pour une analyse approfondie.
- **Visualisation** : Produit des données enrichies et prêtes à être utilisées dans des graphiques ou des rapports.
- **Rapport** : Génère des introductions professionnelles et des contenus reformulés pour améliorer la qualité des livrables.

Technologies utilisées :
- **BeautifulSoup** : Pour extraire et nettoyer le contenu HTML.
- **Regex** : Pour identifier et supprimer les motifs indésirables (URLs, images, etc.).
- **Llama.cpp** : Pour utiliser un modèle IA local (Mistral) pour la reformulation, la classification et la détection de langue.
- **JSON** : Pour lire et écrire les données structurées.
- **Logging** : Pour suivre les étapes du processus et gérer les erreurs.
"""

import os
import re
import json
import hashlib
import logging
import warnings
from collections import OrderedDict, defaultdict
from typing import Dict, Any, Union, List, Optional

from bs4 import BeautifulSoup
from bs4 import MarkupResemblesLocatorWarning
from llama_cpp import Llama

# ===================== CONFIGURATION =====================
"""
Rôle :
Configure les paramètres du module, tels que les chemins des fichiers, les seuils de nettoyage, et les paramètres du modèle IA.

Importance :
Centralise les configurations pour faciliter leur modification et garantir la cohérence du traitement.
"""
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
logging.basicConfig(filename="content_cleaner_pro.log", level=logging.INFO)

MODEL_PATH = r"C:\ENSI\2éme année\Stage ii2\essai\test\models\mistral-7b-instruct-v0.1.Q4_K_M.gguf"
INPUT_JSON = "resultats.json"
OUTPUT_JSON = "resultats_clean_pro.json"

MIN_CONTENT_LENGTH = 150  # Longueur minimale pour considérer un contenu comme pertinent
N_CTX = 4096
N_THREADS = max(2, (os.cpu_count() or 4) - 1)

try:
    import torch
    N_GPU_LAYERS = -1 if torch.cuda.is_available() else 0
except Exception:
    N_GPU_LAYERS = 0

# ===================== IA WRAPPER =====================
class LocalLlamaWrapper:
    """
    Rôle :
    Interface pour interagir avec le modèle IA local (Mistral via llama.cpp).

    Fonctionnalité :
    - Charge le modèle IA local.
    - Fournit une méthode pour générer des réponses à partir de prompts spécifiques.

    Importance :
    Cette classe encapsule la logique d'interaction avec le modèle IA, simplifiant son utilisation dans le reste du module.

    Arguments :
    - `model_path` : Chemin vers le fichier du modèle IA.
    """
    def __init__(self, model_path: str):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Fichier modèle introuvable: {model_path}")
        print("Chargement du modèle local (llama.cpp) ...")
        self.llm = Llama(
            model_path=model_path,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False
        )

    def generate(self, prompt: str, max_tokens: int = 300, temperature: float = 0.5) -> str:
        """
        Rôle :
        Génère une réponse à partir d'un prompt donné.

        Fonctionnalité :
        - Formate le prompt en fonction de la tâche (classification, détection de langue, reformulation).
        - Utilise le modèle IA pour produire une réponse.

        Importance :
        Permet d'utiliser le modèle IA pour des tâches variées, comme la classification ou la reformulation.

        Arguments :
        - `prompt` : Le texte d'entrée pour le modèle.
        - `max_tokens` : Nombre maximum de tokens dans la réponse.
        - `temperature` : Contrôle la créativité des réponses.

        Retour :
        Une chaîne de caractères contenant la réponse générée.
        """
        if "[CLASSIFY]" in prompt:
            instruct_prompt = (
                "<s>[INST] Tu es un assistant expert en analyse de contenu web. "
                "Classe les informations suivantes dans les catégories : "
                "technologies, services, clients, offres, blog. "
                "Réponds au format JSON strict. [/INST]\n"
                f"[INST] {prompt} [/INST]"
            )
        elif "[DETECT_LANG]" in prompt:
            instruct_prompt = (
                "<s>[INST] Identifie la langue principale de ce texte. "
                "Réponds uniquement avec le code langue (fr, en, es, etc.). [/INST]\n"
                f"[INST] {prompt} [/INST]"
            )
        else:
            instruct_prompt = (
                "<s>[INST] Tu es un rédacteur professionnel. "
                "Génère un texte fluide en conservant toutes les informations importantes. "
                "Sois concis mais complet. [/INST]\n"
                f"[INST] {prompt} [/INST]"
            )

        out = self.llm.create_completion(
            prompt=instruct_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            repeat_penalty=1.1
        )
        return out["choices"][0]["text"].strip()

# ===================== Content Cleaner PRO =====================
class ContentCleanerPro:
    """
    Rôle :
    Classe principale pour nettoyer, classer et enrichir les données extraites des sites web.

    Fonctionnalité :
    - Nettoie les contenus HTML et textuels.
    - Détecte automatiquement la langue des contenus.
    - Classifie les informations dans des catégories prédéfinies.
    - Génère des introductions professionnelles pour les entreprises.

    Importance :
    Cette classe centralise toutes les étapes de traitement des données, garantissant un pipeline cohérent et efficace.

    Arguments :
    - `llm_wrapper` : Une instance de `LocalLlamaWrapper` pour interagir avec le modèle IA.
    """
    def __init__(self, llm_wrapper: LocalLlamaWrapper):
        self.llm = llm_wrapper
        self.setup_patterns()

    def setup_patterns(self):
        """
        Rôle :
        Configure les motifs regex pour le nettoyage des contenus.

        Importance :
        Permet de détecter et de supprimer les éléments indésirables (URLs, images, etc.) dans les contenus.
        """
        self.URL_PATTERN = re.compile(
            r"(https?://\S+|www\.\S+|ftp://\S+|[a-zA-Z0-9-]+\.[a-z]{2,}(?:/\S*)?)",
            re.IGNORECASE
        )
        
        self.FORBIDDEN_PATTERNS = re.compile(
            r"\.(?:png|jpg|jpeg|webp|svg|gif|bmp|ico|tiff|avif)\b|"
            r"productimagetemplate\d+x\d+|@\d+x\.|"
            r"\b(?:undefined|null|false|true|nan|infinity)\b|"
            r"\b(?:\d{10,}|[\w.-]+@[\w-]+\.\w{2,10})\b|"
            r"<\s*\/?\w+\s*[^>]*>|"
            r"\b(?:google-analytics|gtag|ga\(|gtm\.js|fbq\(|facebook-pixel)\b",
            re.IGNORECASE
        )

    def detect_language(self, text: str) -> str:
        """
        Rôle :
        Détecte la langue principale d'un texte.

        Fonctionnalité :
        - Utilise le modèle IA pour identifier la langue.
        - Retourne un code langue (ex. "fr", "en").

        Importance :
        Permet d'adapter les traitements linguistiques en fonction de la langue détectée.

        Arguments :
        - `text` : Le texte à analyser.

        Retour :
        Un code langue (ex. "fr", "en").
        """
        if not text.strip():
            return "fr"  # Par défaut
        
        prompt = f"[DETECT_LANG] Texte à analyser:\n{text[:2000]}\nLangue:"
        try:
            lang = self.llm.generate(prompt, max_tokens=5, temperature=0.1)
            return lang.strip()[:2].lower()
        except Exception as e:
            logging.error(f"Erreur détection langue: {e}")
            return "fr"

    def advanced_clean_text(self, text: str) -> str:
        """
        Rôle :
        Nettoie et reformule un texte brut.

        Fonctionnalité :
        - Supprime les éléments indésirables (URLs, images, etc.).
        - Utilise le modèle IA pour reformuler le texte.

        Importance :
        Produit un texte propre et lisible, prêt pour l'analyse ou la visualisation.

        Arguments :
        - `text` : Le texte brut à nettoyer.

        Retour :
        Une chaîne de caractères contenant le texte nettoyé.
        """
        # Nettoyage de base
        soup = BeautifulSoup(text, 'lxml')
        clean_text = soup.get_text(' ', strip=True)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Suppression des URLs et motifs interdits
        clean_text = self.URL_PATTERN.sub('', clean_text)
        clean_text = self.FORBIDDEN_PATTERNS.sub('', clean_text)
        
        # Reformulation intelligente via IA
        if len(clean_text.split()) > 20:  # Seulement pour textes assez longs
            prompt = f"Reformule ce texte en gardant toutes les informations importantes:\n{clean_text[:3000]}"
            try:
                clean_text = self.llm.generate(prompt)
            except Exception as e:
                logging.error(f"Erreur reformulation: {e}")
        
        return clean_text.strip()

    def auto_classify_content(self, text: str) -> Dict[str, str]:
        """
        Rôle :
        Classe automatiquement un texte dans des catégories prédéfinies.

        Fonctionnalité :
        - Utilise le modèle IA pour analyser et classer les informations.

        Importance :
        Structure les données en catégories exploitables (services, technologies, etc.).

        Arguments :
        - `text` : Le texte à classer.

        Retour :
        Un dictionnaire contenant les catégories et leurs contenus.
        """
        if not text.strip():
            return {}
            
        prompt = f"[CLASSIFY] Analyse ce contenu et classe les informations:\n{text[:3000]}"
        try:
            classification = self.llm.generate(prompt)
            return json.loads(classification)
        except Exception as e:
            logging.error(f"Erreur classification: {e}")
            return {}

    def generate_enhanced_intro(self, site_data: Dict[str, Any]) -> str:
        """
        Rôle :
        Génère une introduction professionnelle pour une entreprise.

        Fonctionnalité :
        - Utilise les informations clés de l'entreprise pour créer une introduction.

        Importance :
        Améliore la qualité des rapports en fournissant des introductions bien rédigées.

        Arguments :
        - `site_data` : Un dictionnaire contenant les données de l'entreprise.

        Retour :
        Une chaîne de caractères contenant l'introduction générée.
        """
        lang = self.detect_language(self.extract_main_text(site_data))
        
        prompt = (
            f"Crée une introduction professionnelle (3-5 phrases) en {lang} pour cette entreprise "
            f"en intégrant ces informations clés:\n"
            f"Nom: {site_data.get('name', '')}\n"
            f"Services: {site_data.get('services', '')}\n"
            f"Technologies: {site_data.get('technologies', '')}\n"
            f"Points forts: {site_data.get('key_points', '')}"
        )
        
        return self.llm.generate(prompt, max_tokens=400)

    def extract_main_text(self, data: Union[dict, list, str]) -> str:
        """
        Rôle :
        Extrait tout le texte pertinent d'une structure de données.

        Fonctionnalité :
        - Parcourt récursivement les dictionnaires et listes pour extraire le texte.

        Importance :
        Garantit que tout le contenu textuel est pris en compte pour le nettoyage et l'analyse.

        Arguments :
        - `data` : Les données à analyser.

        Retour :
        Une chaîne de caractères contenant le texte extrait.
        """
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return ' '.join(
                self.extract_main_text(v) 
                for k, v in data.items() 
                if k not in ['url', 'success', 'logo']
            )
        if isinstance(data, list):
            return ' '.join(self.extract_main_text(item) for item in data)
        return ""

    def process_site(self, site: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Rôle :
        Traite un site complet pour nettoyer, classer et enrichir ses données.

        Fonctionnalité :
        - Nettoie le texte principal.
        - Classe les informations dans des catégories.
        - Génère une introduction professionnelle.

        Importance :
        Produit des données prêtes à être utilisées dans des rapports ou des visualisations.

        Arguments :
        - `site` : Un dictionnaire contenant les données brutes du site.

        Retour :
        Un dictionnaire contenant les données nettoyées et enrichies.
        """
        # Extraction et nettoyage du texte principal
        main_text = self.extract_main_text(site)
        cleaned_text = self.advanced_clean_text(main_text)
        
        if len(cleaned_text) < MIN_CONTENT_LENGTH:
            return None

        # Classification automatique
        classified = self.auto_classify_content(cleaned_text)
        
        # Construction du résultat final
        result = {
            'name': site.get('name', '').strip(),
            'url': site.get('url', '').strip(),
            'language': self.detect_language(cleaned_text),
            **classified,
            'full_content': cleaned_text,
            'introduction': self.generate_enhanced_intro({**site, **classified}),
            'success': True
        }
        
        return result

    def clean_json(self):
        """
        Rôle :
        Traite un fichier JSON contenant les données brutes des sites.

        Fonctionnalité :
        - Charge les données brutes.
        - Applique le nettoyage, la classification et l'enrichissement à chaque site.
        - Sauvegarde les résultats dans un nouveau fichier JSON.

        Importance :
        Automatise le traitement des données pour produire un fichier prêt à être utilisé dans les étapes suivantes.

        Retour :
        Aucun retour. Les résultats sont sauvegardés dans un fichier JSON.
        """
        try:
            with open(INPUT_JSON, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Erreur lecture fichier : {e}")
            print("Erreur: impossible de lire le JSON d'entrée.")
            return

        cleaned_sites = []
        for i, site in enumerate(data, 1):
            try:
                print(f"Traitement du site {i}/{len(data)}...")
                result = self.process_site(site)
                if result:
                    cleaned_sites.append(result)
            except Exception as e:
                logging.error(f"Erreur sur {site.get('name')}: {e}")

        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(cleaned_sites, f, ensure_ascii=False, indent=2)

        print(f"Nettoyage PRO terminé. Résultats sauvegardés dans {OUTPUT_JSON}")

# ===================== Main =====================
def main():
    """
    Rôle :
    Point d'entrée principal pour lancer le nettoyage des données.

    Fonctionnalité :
    - Vérifie l'existence du modèle IA.
    - Initialise le modèle et la classe de nettoyage.
    - Lance le traitement des données.

    Importance :
    Ordonne et exécute toutes les étapes nécessaires pour produire des données nettoyées et enrichies.

    Retour :
    Aucun retour. Les résultats sont affichés dans la console et sauvegardés dans un fichier JSON.
    """
    if not os.path.isfile(MODEL_PATH):
        print(f"Erreur: modèle introuvable à l'emplacement:\n{MODEL_PATH}")
        return

    print("Initialisation du modèle Mistral (GGUF) via llama.cpp ...")
    llm = LocalLlamaWrapper(MODEL_PATH)

    cleaner = ContentCleanerPro(llm)
    cleaner.clean_json()

if __name__ == "__main__":
    main()
