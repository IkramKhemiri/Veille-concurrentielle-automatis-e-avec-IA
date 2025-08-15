# analyse/resumeur.py

import logging
from transformers import MT5ForConditionalGeneration, MT5Tokenizer
import torch

# Chargement global du modèle
_model = None
_tokenizer = None


def _load_mt5():
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        logging.info("📦 Chargement du modèle mT5 pour génération...")
        _tokenizer = MT5Tokenizer.from_pretrained("google/mt5-small")
        _model = MT5ForConditionalGeneration.from_pretrained("google/mt5-small")


def _generate_mt5_prompt(prompt, blocs_textuels, min_length=30, max_length=100):
    try:
        _load_mt5()
        texte = "\n".join([str(x).strip() for x in blocs_textuels if x]).strip()

        if not texte or len(texte.split()) < 10:
            return "Texte insuffisant."

        full_prompt = f"{prompt} : {texte}"
        inputs = _tokenizer(full_prompt, return_tensors="pt", max_length=512, truncation=True)
        output = _model.generate(
            inputs["input_ids"],
            max_length=max_length,
            min_length=min_length,
            num_beams=4,
            early_stopping=True
        )
        return _tokenizer.decode(output[0], skip_special_tokens=True)
    except Exception as e:
        logging.warning(f"⚠️ Erreur génération mT5 : {e}")
        return "Génération non disponible."


def generer_introduction_mt5(blocs_textuels):
    return _generate_mt5_prompt(
        "Présente l'entreprise de façon professionnelle et concise",
        blocs_textuels,
        min_length=40,
        max_length=100
    )


def generer_resume_final_mt5(blocs_textuels):
    return _generate_mt5_prompt(
        "Fais une conclusion globale sur cette entreprise à partir des informations données",
        blocs_textuels,
        min_length=40,
        max_length=100
    )
