# utils/pdf_report.py

from fpdf import FPDF
import os
import unicodedata
import re
import textwrap
from typing import List, Dict, Union


class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)

    def header(self):
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 16)
            self.set_text_color(0, 70, 140)
            self.cell(0, 10, 'Rapport de veille concurrentielle', ln=1, align='C')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def nettoyer_caracteres_non_latin1(texte: str) -> str:
    substitutions = {
        "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-",
        "…": "...", "•": "-", "™": "(TM)", "®": "(R)", "©": "(C)", "€": "EUR", "→": "->"
    }
    for old, new in substitutions.items():
        texte = texte.replace(old, new)
    return texte.encode('latin-1', 'ignore').decode('latin-1')


EXCLUDED_PATTERNS = [
    r"^https?://\S+$", r"^www\.\S+$", r"^api\s+for\s+developers",
    r"^read more$", r"^learn more$", r"^more$", r"^login$", r"^sign up$",
    r"terms and conditions", r"^\s*$"
]

def nettoyer_texte(txt: str) -> str:
    if not isinstance(txt, str): return ""
    txt = unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode('ascii')
    txt = re.sub(r'[\r\n\t]+', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

def est_ligne_inutile(ligne: str) -> bool:
    return any(re.search(p, ligne.strip(), re.IGNORECASE) for p in EXCLUDED_PATTERNS) or len(ligne.strip()) < 5

def nettoyer_bloc(txt: Union[str, List[str]]) -> str:
    if isinstance(txt, list):
        txt = "\n".join(str(l) for l in txt)
    lignes = txt.splitlines()
    propres = []
    deja_vu = set()
    for ligne in lignes:
        ligne = nettoyer_texte(ligne)
        if est_ligne_inutile(ligne): continue
        ligne_claire = ligne.lower().strip()
        if ligne_claire in deja_vu: continue
        propres.append(ligne)
        deja_vu.add(ligne_claire)
    return "\n".join(propres)

def couper_ligne_longue(ligne: str, largeur_max: int = 90) -> List[str]:
    return textwrap.wrap(ligne, width=largeur_max)

def ajouter_titre(pdf: PDF, titre: str, niveau: int = 1):
    taille = 14 if niveau == 1 else 12
    gras = 'B' if niveau == 1 else ''
    pdf.set_font('Arial', gras, taille)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, nettoyer_caracteres_non_latin1(titre), ln=1, fill=True)
    pdf.ln(3)

def ajouter_paragraphe(pdf: PDF, texte: str, indent: int = 0):
    texte = nettoyer_bloc(texte)
    if not texte: return
    pdf.set_font('Arial', '', 11)
    lignes = re.split(r'(?<=[.!?])\s+', texte)
    for ligne in lignes:
        for ligne_courte in couper_ligne_longue(ligne.strip()):
            if indent: pdf.cell(indent)
            pdf.multi_cell(0, 6, nettoyer_caracteres_non_latin1(ligne_courte))
    pdf.ln(2)

def lister_contenu(pdf: PDF, elements: List[str], indent: int = 5):
    propres = [nettoyer_texte(el) for el in elements if isinstance(el, str) and not est_ligne_inutile(el)]
    propres = list(set([el for el in propres if len(el) > 5]))
    for el in propres:
        pdf.set_font('Arial', '', 11)
        for ligne in couper_ligne_longue(f"- {el}"):
            if indent: pdf.cell(indent)
            pdf.multi_cell(0, 6, nettoyer_caracteres_non_latin1(ligne))
    pdf.ln(2)


def generate_pdf(donnees: List[Dict], chemin_pdf: str) -> bool:
    try:
        pdf = PDF()
        pdf.add_page()

        for idx, site in enumerate(donnees):
            # ✅ Fusionner les champs de site["data"] si présents
            if "data" in site and isinstance(site["data"], dict):
                for key, value in site["data"].items():
                    site.setdefault(key, value)

            nom = nettoyer_texte(site.get("name", "Nom inconnu"))
            url = site.get("url", "")
            ajouter_titre(pdf, nom, niveau=1)
            pdf.set_font('Arial', 'U', 11)
            pdf.set_text_color(0, 0, 255)
            pdf.cell(0, 6, nettoyer_caracteres_non_latin1(url), ln=1, link=url)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

            ajouter_titre(pdf, "Résumé synthétique", niveau=2)
            ajouter_paragraphe(pdf, site.get("resume", "Résumé non disponible."))

            for section, titre in [
                ("presentation", "Présentation"),
                ("services", "Services / Offres"),
                ("technologies", "Technologies utilisées"),
                ("clients", "Clients / Références"),
                ("blog", "Blog / Actualités"),
                ("phones", "Téléphones"),
                ("emails", "Emails")
            ]:
                contenu = site.get(section, "")
                if not contenu: continue
                ajouter_titre(pdf, titre, 2)
                if isinstance(contenu, list):
                    liste = [item["content"] if isinstance(item, dict) and "content" in item else str(item) for item in contenu]
                    lister_contenu(pdf, liste)
                elif isinstance(contenu, str):
                    ajouter_paragraphe(pdf, contenu)

            nouveautes = site.get("novelty", []) or site.get("nouveautes", [])
            if nouveautes:
                ajouter_titre(pdf, "🆕 Nouveautés détectées", niveau=2)
                if isinstance(nouveautes, list):
                    lister_contenu(pdf, nouveautes)
                elif isinstance(nouveautes, str):
                    ajouter_paragraphe(pdf, nouveautes)

            if idx < len(donnees) - 1:
                pdf.add_page()

        dossier = os.path.dirname(chemin_pdf)
        if dossier and not os.path.exists(dossier):
            os.makedirs(dossier)
        pdf.output(chemin_pdf)
        print(f"✅ Rapport PDF généré : {chemin_pdf}")
        return True

    except Exception as e:
        print(f"❌ Erreur PDF : {str(e)}")
        return False
