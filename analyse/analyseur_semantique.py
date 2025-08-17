"""
Rôle global :
Ce module est un analyseur sémantique conçu pour traiter et enrichir les données extraites d'un site web. 
Il reformule, complète et structure les informations brutes pour les rendre exploitables dans des étapes ultérieures du pipeline.

Importance :
L'analyse sémantique est une étape clé dans le pipeline global (scraping → analyse → visualisation → rapport). 
Elle permet de transformer des données brutes en informations organisées et compréhensibles, facilitant ainsi leur utilisation dans des rapports ou des visualisations. 
Sans cette étape, les données extraites seraient souvent incomplètes ou non exploitables.

Technologies utilisées :
- `logging` : pour la gestion des erreurs et des avertissements.
- Modules personnalisés : `resumeur` pour la génération de résumés, `classifier_theme` pour la classification thématique, et `cleaner` pour le nettoyage des textes.
- Techniques NLP (Natural Language Processing) : utilisées pour reformuler et structurer les données textuelles.
"""

import logging
from analyse.resumeur import generer_introduction_mt5, generer_resume_final_mt5
from analyse.classifier_theme import classer_par_theme as classifier_theme
from scraping.cleaner import nettoyer_texte

# Fonction utilitaire pour joindre les éléments d'une liste en une chaîne de texte.
def _safe_join_items(items):
    """
    Rôle :
    Combine les éléments d'une liste en une seule chaîne de texte, en s'assurant que chaque élément est valide.

    Fonctionnalité :
    - Vérifie si chaque élément est un dictionnaire ou une chaîne.
    - Extrait le contenu pertinent des dictionnaires ou convertit les éléments en chaînes.
    - Filtre les éléments vides ou non pertinents.

    Importance :
    Cette fonction garantit que les données textuelles sont correctement formatées avant d'être utilisées dans l'analyse.
    """
    out = []
    for it in items or []:
        if isinstance(it, dict):
            out.append(it.get("content", ""))
        else:
            out.append(str(it))
    return "\n".join([x for x in out if x])

# Fonction principale pour l'analyse sémantique d'un site web.
def analyse_semantique_site(data: dict, url: str = None) -> dict:
    """
    Rôle :
    Analyse et enrichit les données extraites d'un site web. Reformule les sections textuelles, complète les données manquantes, 
    et structure les informations pour une utilisation ultérieure.

    Fonctionnalité :
    - Injecte l'URL dans les données si elle est fournie.
    - Déstructure les données imbriquées pour simplifier leur traitement.
    - Identifie et complète les sections clés (services, clients, technologies, blog, jobs) à partir des données brutes.
    - Utilise un classificateur thématique pour remplir les sections vides.
    - Applique des heuristiques pour détecter des informations pertinentes dans le texte brut.
    - Génère une introduction et un résumé final à l'aide de modèles NLP.
    - Nettoie et structure les données pour les rendre exploitables.

    Importance :
    Cette fonction est essentielle pour transformer des données brutes en informations organisées, 
    facilitant leur intégration dans des rapports ou des visualisations.

    Arguments :
    - `data` : Dictionnaire contenant les données extraites d'un site web.
    - `url` : URL du site web (facultatif).

    Retour :
    Un dictionnaire structuré contenant les informations analysées et enrichies.
    """
    if not data or not isinstance(data, dict):
        return {}

    # Injecter l'URL si fournie
    if url:
        data["url"] = url

    # Déstructure les données si elles sont imbriquées
    if "data" in data and isinstance(data["data"], dict):
        merged = {**data, **data["data"]}
        merged.pop("data", None)
        data = merged

    url = data.get("url", "")
    raw = data.get("raw_text", "") or _safe_join_items(data.get("services", [])) or ""

    # Extraction des sections candidates
    services = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("services", [])]
    clients = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("clients", [])]
    techs = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("technologies", [])]
    blog = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("blog", [])]
    jobs = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("jobs", [])]

    # Classification thématique pour compléter les sections vides
    try:
        classified = classifier_theme(raw)
        if not services and classified.get("services"):
            services = classified["services"]
        if not clients and classified.get("clients"):
            clients = classified["clients"]
        if not techs and classified.get("technologies"):
            techs = classified["technologies"]
        if not blog and classified.get("blog"):
            blog = classified["blog"]
        if not jobs and classified.get("jobs"):
            jobs = classified["jobs"]
    except Exception as e:
        logging.debug(f"⚠️ classifier_theme failed: {e}")

    # Heuristiques pour détecter des informations dans le texte brut
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not services:
        services = [l for l in lines if any(k in l.lower() for k in ["service", "solution", "offre", "produit", "what we do"])][:8]
    if not clients:
        clients = [l for l in lines if any(k in l.lower() for k in ["client", "référence", "they trust", "nos clients"])][:8]
    if not techs:
        techs = [l for l in lines if any(k in l.lower() for k in ["python", "javascript", "react", "aws", "azure", "docker", "php", "java", "node", "django"])][:10]
    if not blog:
        blog = [l for l in lines if any(k in l.lower() for k in ["blog", "article", "news", "actualité"])][:6]
    if not jobs:
        jobs = [l for l in lines if any(k in l.lower() for k in ["job", "career", "poste", "recrutement", "hiring"])][:6]

    # Préparation des entrées pour la reformulation
    reform_inputs = list(dict.fromkeys([x for x in (services + clients + techs + blog + jobs) if x and len(x) > 10]))

    # Génération de l'introduction
    try:
        intro = generer_introduction_mt5([raw] + reform_inputs)
    except Exception as e:
        logging.warning(f"⚠️ introduction generation failed: {e}")
        intro = data.get("slogan", "") or ""

    # Génération du résumé final
    try:
        final_resume = generer_resume_final_mt5([raw] + reform_inputs)
    except Exception as e:
        logging.warning(f"⚠️ final resume failed: {e}")
        final_resume = ""

    # Fonction utilitaire pour structurer les listes
    def wrap_list(lst):
        """
        Rôle :
        Nettoie et structure les éléments d'une liste pour les rendre exploitables.

        Fonctionnalité :
        - Nettoie chaque élément de la liste en supprimant les caractères inutiles.
        - Structure chaque élément sous forme de dictionnaire avec l'URL et le contenu.

        Importance :
        Cette fonction garantit que les données sont prêtes pour une utilisation dans des rapports ou des visualisations.
        """
        out = []
        for it in lst:
            if isinstance(it, dict):
                c = it.get("content", "")
            else:
                c = str(it)
            c = nettoyer_texte(c).strip()
            if c:
                out.append({"url": url, "content": c})
        return out

    # Retourne les données enrichies et structurées
    return {
        "name": data.get("name", ""),
        "url": url,
        "slogan": data.get("slogan", ""),
        "introduction": intro,
        "presentation": [data.get("summary", "")] if data.get("summary") else [],
        "services": wrap_list(services),
        "clients": wrap_list(clients),
        "technologies": wrap_list(techs),
        "blog": wrap_list(blog),
        "jobs": wrap_list(jobs),
        "emails": data.get("emails", []),
        "phones": data.get("phones", []),
        "offres": data.get("offres", []),
        "nouveautes": data.get("nouveautes", []),
        "raw_text": raw,
        "resume_final": final_resume
    }
