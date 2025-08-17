"""
Rôle global :
Ce module utilise un modèle de traitement du langage naturel (NLP), mT5, pour générer automatiquement des introductions et des résumés 
à partir de blocs textuels. Il est conçu pour reformuler et synthétiser des informations de manière concise et professionnelle.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle clé en transformant des données textuelles 
brutes en résumés clairs et exploitables. Ces résumés permettent de présenter les informations de manière concise et professionnelle, 
ce qui est essentiel pour les rapports ou les visualisations. Sans cette étape, les données textuelles pourraient être trop longues ou désorganisées 
pour être directement utilisées.

Comment il aide dans le pipeline :
- **Scraping** : Les données textuelles extraites sont souvent volumineuses et non synthétisées.
- **Analyse** : Ce module reformule et résume ces données pour les rendre plus compréhensibles.
- **Visualisation** : Les introductions et résumés générés peuvent être utilisés comme descriptions dans des graphiques ou tableaux.
- **Rapport** : Les résumés permettent de présenter les informations de manière concise et professionnelle dans les rapports finaux.

Technologies utilisées :
- **Transformers (mT5)** : Un modèle NLP multilingue de Google, utilisé pour la génération de texte.
- **PyTorch** : Utilisé pour charger et exécuter le modèle mT5.
- **Logging** : Pour suivre les erreurs et les étapes de chargement du modèle.
"""

import logging
from transformers import MT5ForConditionalGeneration, MT5Tokenizer
import torch

# Chargement global du modèle
_model = None
_tokenizer = None

# Fonction pour charger le modèle mT5
def _load_mt5():
    """
    Rôle :
    Cette fonction charge le modèle mT5 et son tokenizer en mémoire. Elle s'assure que le modèle est chargé une seule fois 
    pour éviter des rechargements inutiles.

    Fonctionnalité :
    - Charge le tokenizer mT5 pour préparer les données textuelles.
    - Charge le modèle mT5 pour la génération de texte.

    Importance :
    Le chargement du modèle est une étape essentielle pour permettre la génération de résumés et d'introductions. 
    En le chargeant globalement, on optimise les performances en évitant des rechargements répétitifs.
    """
    global _model, _tokenizer
    if _model is None or _tokenizer is None:
        logging.info("📦 Chargement du modèle mT5 pour génération...")
        _tokenizer = MT5Tokenizer.from_pretrained("google/mt5-small")
        _model = MT5ForConditionalGeneration.from_pretrained("google/mt5-small")

# Fonction générique pour générer du texte avec mT5
def _generate_mt5_prompt(prompt, blocs_textuels, min_length=30, max_length=100):
    """
    Rôle :
    Cette fonction génère un texte basé sur un prompt donné et des blocs textuels en entrée. Elle utilise le modèle mT5 
    pour produire une sortie cohérente et concise.

    Fonctionnalité :
    - Combine les blocs textuels en une seule chaîne.
    - Prépare les données pour le modèle mT5 en utilisant le tokenizer.
    - Génère un texte en respectant les contraintes de longueur minimale et maximale.
    - Gère les erreurs éventuelles lors de la génération.

    Importance :
    Cette fonction est le moteur principal de la génération de texte. Elle permet de produire des introductions et des résumés 
de manière flexible et réutilisable.

    Arguments :
    - `prompt` : Une instruction qui guide la génération (par exemple, "Présente l'entreprise...").
    - `blocs_textuels` : Une liste de textes à utiliser comme base pour la génération.
    - `min_length` : Longueur minimale du texte généré.
    - `max_length` : Longueur maximale du texte généré.

    Retour :
    Une chaîne de caractères contenant le texte généré ou un message d'erreur si la génération échoue.
    """
    try:
        _load_mt5()  # Charger le modèle si ce n'est pas déjà fait
        texte = "\n".join([str(x).strip() for x in blocs_textuels if x]).strip()

        if not texte or len(texte.split()) < 10:  # Vérifier si le texte est suffisant pour la génération
            return "Texte insuffisant."

        # Préparer le prompt complet
        full_prompt = f"{prompt} : {texte}"
        inputs = _tokenizer(full_prompt, return_tensors="pt", max_length=512, truncation=True)
        output = _model.generate(
            inputs["input_ids"],
            max_length=max_length,
            min_length=min_length,
            num_beams=4,  # Utilisation de beam search pour améliorer la qualité
            early_stopping=True
        )
        return _tokenizer.decode(output[0], skip_special_tokens=True)  # Décoder la sortie en texte lisible
    except Exception as e:
        logging.warning(f"⚠️ Erreur génération mT5 : {e}")
        return "Génération non disponible."

# Fonction pour générer une introduction
def generer_introduction_mt5(blocs_textuels):
    """
    Rôle :
    Génère une introduction professionnelle et concise à partir des blocs textuels fournis.

    Fonctionnalité :
    - Utilise un prompt spécifique pour guider la génération ("Présente l'entreprise...").
    - Produit un texte d'introduction clair et structuré.

    Importance :
    Une introduction bien rédigée est essentielle pour présenter une entreprise de manière professionnelle, 
    que ce soit dans un rapport ou une visualisation.

    Arguments :
    - `blocs_textuels` : Une liste de textes à utiliser comme base pour la génération.

    Retour :
    Une chaîne de caractères contenant l'introduction générée.
    """
    return _generate_mt5_prompt(
        "Présente l'entreprise de façon professionnelle et concise",
        blocs_textuels,
        min_length=40,
        max_length=100
    )

# Fonction pour générer un résumé final
def generer_resume_final_mt5(blocs_textuels):
    """
    Rôle :
    Génère une conclusion ou un résumé global à partir des blocs textuels fournis.

    Fonctionnalité :
    - Utilise un prompt spécifique pour guider la génération ("Fais une conclusion globale...").
    - Produit un texte de synthèse qui résume les informations principales.

    Importance :
    Un résumé final permet de conclure un rapport ou une analyse de manière claire et concise, 
    en mettant en avant les points essentiels.

    Arguments :
    - `blocs_textuels` : Une liste de textes à utiliser comme base pour la génération.

    Retour :
    Une chaîne de caractères contenant le résumé final généré.
    """
    return _generate_mt5_prompt(
        "Fais une conclusion globale sur cette entreprise à partir des informations données",
        blocs_textuels,
        min_length=40,
        max_length=100
    )
