#nettoyage_base.py
"""
ULTIMATE CONTENT CLEANER PRO (100% OFFLINE)
Version améliorée avec :
- Nettoyage intelligent combinant regex + IA
- Classification automatique des informations
- Génération d'introductions complètes
- Détection de langue
- Reformulation avancée
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

# ===================== CONFIG =====================
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)
logging.basicConfig(filename="content_cleaner_pro.log", level=logging.INFO)

MODEL_PATH = r"C:\ENSI\2éme année\Stage ii2\essai\test\models\mistral-7b-instruct-v0.1.Q4_K_M.gguf"
INPUT_JSON = "resultats.json"
OUTPUT_JSON = "resultats_clean_pro.json"

MIN_CONTENT_LENGTH = 150  # Augmenté pour contenus plus riches
N_CTX = 4096
N_THREADS = max(2, (os.cpu_count() or 4) - 1)

try:
    import torch
    N_GPU_LAYERS = -1 if torch.cuda.is_available() else 0
except Exception:
    N_GPU_LAYERS = 0

# ===================== IA WRAPPER =====================
class LocalLlamaWrapper:
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
        """Génération avec différents formats de prompt selon la tâche"""
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
    def __init__(self, llm_wrapper: LocalLlamaWrapper):
        self.llm = llm_wrapper
        self.setup_patterns()

    def setup_patterns(self):
        """Configurations des motifs pour le nettoyage"""
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
        """Détection de langue via le modèle"""
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
        """Nettoyage combinant regex et IA"""
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
        """Classification automatique du contenu"""
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
        """Génération d'une introduction complète"""
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
        """Extraction récursive de tout le texte"""
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
        """Traitement complet d'un site"""
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
        """Traitement du fichier JSON complet"""
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
    if not os.path.isfile(MODEL_PATH):
        print(f"Erreur: modèle introuvable à l'emplacement:\n{MODEL_PATH}")
        return

    print("Initialisation du modèle Mistral (GGUF) via llama.cpp ...")
    llm = LocalLlamaWrapper(MODEL_PATH)

    cleaner = ContentCleanerPro(llm)
    cleaner.clean_json()

if __name__ == "__main__":
    main()