import logging
from analyse.resumeur import generer_introduction_mt5, generer_resume_final_mt5
from analyse.classifier_theme import classer_par_theme as classifier_theme
from scraping.cleaner import nettoyer_texte

def _safe_join_items(items):
    out = []
    for it in items or []:
        if isinstance(it, dict):
            out.append(it.get("content", ""))
        else:
            out.append(str(it))
    return "\n".join([x for x in out if x])

def analyse_semantique_site(data: dict, url: str = None) -> dict:
    """
    Prend l'extracteur output (incluant raw_text). Reformule tout sauf slogan/emails/phones/location.
    Remplit sections vides à partir de raw_text.
    """
    if not data or not isinstance(data, dict):
        return {}

    # Injecter l'URL si fournie
    if url:
        data["url"] = url

    # unwrap data if nested
    if "data" in data and isinstance(data["data"], dict):
        merged = {**data, **data["data"]}
        merged.pop("data", None)
        data = merged

    url = data.get("url", "")
    raw = data.get("raw_text", "") or _safe_join_items(data.get("services", [])) or ""

    # Sections candidates
    services = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("services", [])]
    clients = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("clients", [])]
    techs = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("technologies", [])]
    blog = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("blog", [])]
    jobs = [(it.get("content") if isinstance(it, dict) else str(it)) for it in data.get("jobs", [])]

    # Classif si vide
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

    # Fallback heuristique
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

    # Inputs pour reformulation
    reform_inputs = list(dict.fromkeys([x for x in (services + clients + techs + blog + jobs) if x and len(x) > 10]))

    # Introduction et résumé final
    try:
        intro = generer_introduction_mt5([raw] + reform_inputs)
    except Exception as e:
        logging.warning(f"⚠️ introduction generation failed: {e}")
        intro = data.get("slogan", "") or ""

    try:
        final_resume = generer_resume_final_mt5([raw] + reform_inputs)
    except Exception as e:
        logging.warning(f"⚠️ final resume failed: {e}")
        final_resume = ""

    # Emballage final
    def wrap_list(lst):
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
