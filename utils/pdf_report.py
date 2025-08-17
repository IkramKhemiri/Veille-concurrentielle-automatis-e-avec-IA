"""
Rôle global :
Ce module est conçu pour générer des rapports PDF professionnels à partir des données extraites et analysées. 
Il organise les informations de manière structurée et lisible, en incluant des sections comme les résumés, les services, 
les technologies utilisées, les clients, les nouveautés, et bien plus encore.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle crucial en transformant 
les données brutes et analysées en un document final exploitable. Le rapport PDF est un livrable clé qui permet de 
présenter les résultats de manière claire et professionnelle, que ce soit pour des clients, des équipes internes ou des décideurs.

Comment il aide dans le pipeline :
- **Scraping** : Compile les données extraites pour les rendre lisibles et présentables.
- **Analyse** : Met en avant les résultats des analyses linguistiques et thématiques.
- **Visualisation** : Organise les informations sous forme de sections claires et hiérarchisées.
- **Rapport** : Produit un document final qui peut être partagé ou archivé.

Technologies utilisées :
- **FPDF** : Pour générer des fichiers PDF avec des mises en page personnalisées.
- **Textwrap** : Pour gérer les lignes longues et les couper proprement.
- **Regex** : Pour nettoyer et normaliser les textes.
- **OS** : Pour gérer les chemins de fichiers et créer des répertoires si nécessaire.
"""

from fpdf import FPDF
import os
import unicodedata
import re
import textwrap
from typing import List, Dict, Union


class PDF(FPDF):
    """
    Classe personnalisée pour gérer la mise en page et les styles du rapport PDF.
    - Ajoute un en-tête avec le titre du rapport.
    - Ajoute un pied de page avec le numéro de page.
    """
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)

    def header(self):
        """
        Rôle :
        Ajoute un en-tête au début de chaque page.
        - Affiche le titre principal du rapport sur la première page.

        Importance :
        L'en-tête donne une identité visuelle au rapport et facilite sa compréhension.
        """
        if self.page_no() == 1:
            self.set_font('Arial', 'B', 16)
            self.set_text_color(0, 70, 140)
            self.cell(0, 10, 'Rapport de veille concurrentielle', ln=1, align='C')
            self.ln(10)

    def footer(self):
        """
        Rôle :
        Ajoute un pied de page avec le numéro de page.

        Importance :
        Le pied de page améliore la navigation dans le document, surtout pour les rapports longs.
        """
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def nettoyer_caracteres_non_latin1(texte: str) -> str:
    """
    Rôle :
    Nettoie les caractères non pris en charge par l'encodage Latin-1.

    Fonctionnalité :
    - Remplace les caractères spéciaux par des équivalents standards.
    - Supprime les caractères non pris en charge.

    Importance :
    Cette fonction garantit que le texte est compatible avec l'encodage utilisé par FPDF.

    Arguments :
    - `texte` : Une chaîne de caractères à nettoyer.

    Retour :
    Une chaîne de caractères nettoyée.
    """
    substitutions = {
        "’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-",
        "…": "...", "•": "-", "™": "(TM)", "®": "(R)", "©": "(C)", "€": "EUR", "→": "->"
    }
    for old, new in substitutions.items():
        texte = texte.replace(old, new)
    return texte.encode('latin-1', 'ignore').decode('latin-1')

def nettoyer_texte(txt: str) -> str:
    """
    Rôle :
    Nettoie et normalise un texte brut.

    Fonctionnalité :
    - Supprime les retours à la ligne, les tabulations et les espaces multiples.
    - Normalise les caractères spéciaux.

    Importance :
    Cette fonction garantit que le texte est propre et prêt à être affiché dans le rapport.

    Arguments :
    - `txt` : Une chaîne de caractères à nettoyer.

    Retour :
    Une chaîne de caractères nettoyée.
    """
    if not isinstance(txt, str): 
        return ""
    txt = unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode('ascii')
    txt = re.sub(r'[\r\n\t]+', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

def est_ligne_inutile(ligne: str) -> bool:
    """
    Rôle :
    Vérifie si une ligne de texte est inutile.

    Fonctionnalité :
    - Compare la ligne à une liste de motifs exclus (ex. URLs, phrases génériques).
    - Vérifie la longueur minimale de la ligne.

    Importance :
    Cette fonction filtre les lignes inutiles pour améliorer la qualité du contenu du rapport.

    Arguments :
    - `ligne` : Une chaîne de caractères représentant une ligne de texte.

    Retour :
    `True` si la ligne est inutile, sinon `False`.
    """
    EXCLUDED_PATTERNS = [
        r"^https?://\S+$", r"^www\.\S+$", r"^api\s+for\s+developers",
        r"^read more$", r"^learn more$", r"^more$", r"^login$", r"^sign up$",
        r"terms and conditions", r"^\s*$"
    ]
    return any(re.search(p, ligne.strip(), re.IGNORECASE) for p in EXCLUDED_PATTERNS) or len(ligne.strip()) < 5

def nettoyer_bloc(txt: Union[str, List[str]]) -> str:
    """
    Rôle :
    Nettoie un bloc de texte ou une liste de lignes.

    Fonctionnalité :
    - Supprime les lignes inutiles.
    - Élimine les doublons.

    Importance :
    Cette fonction garantit que les blocs de texte affichés dans le rapport sont clairs et pertinents.

    Arguments :
    - `txt` : Une chaîne de caractères ou une liste de lignes à nettoyer.

    Retour :
    Une chaîne de caractères nettoyée.
    """
    if isinstance(txt, list):
        txt = "\n".join(str(l) for l in txt)
    lignes = txt.splitlines()
    propres = []
    deja_vu = set()
    for ligne in lignes:
        ligne = nettoyer_texte(ligne)
        if est_ligne_inutile(ligne): 
            continue
        ligne_claire = ligne.lower().strip()
        if ligne_claire in deja_vu: 
            continue
        propres.append(ligne)
        deja_vu.add(ligne_claire)
    return "\n".join(propres)

def couper_ligne_longue(ligne: str, largeur_max: int = 90) -> List[str]:
    """
    Rôle :
    Coupe une ligne trop longue en plusieurs lignes plus courtes.

    Fonctionnalité :
    - Utilise `textwrap` pour diviser les lignes longues en segments.

    Importance :
    Cette fonction garantit que le texte s'affiche correctement dans le rapport PDF.

    Arguments :
    - `ligne` : Une chaîne de caractères représentant une ligne de texte.
    - `largeur_max` : La largeur maximale d'une ligne.

    Retour :
    Une liste de lignes coupées.
    """
    return textwrap.wrap(ligne, width=largeur_max)

def ajouter_titre(pdf: PDF, titre: str, niveau: int = 1):
    """
    Rôle :
    Ajoute un titre ou un sous-titre au rapport PDF.

    Fonctionnalité :
    - Définit la taille et le style de la police en fonction du niveau du titre.
    - Ajoute un fond coloré pour les titres principaux.

    Importance :
    Les titres structurent le rapport et facilitent la navigation.

    Arguments :
    - `pdf` : L'instance du document PDF.
    - `titre` : Le texte du titre.
    - `niveau` : Le niveau du titre (1 pour les titres principaux, 2 pour les sous-titres).
    """
    taille = 14 if niveau == 1 else 12
    gras = 'B' if niveau == 1 else ''
    pdf.set_font('Arial', gras, taille)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, nettoyer_caracteres_non_latin1(titre), ln=1, fill=True)
    pdf.ln(3)

def ajouter_paragraphe(pdf: PDF, texte: str, indent: int = 0):
    """
    Rôle :
    Ajoute un paragraphe de texte au rapport PDF.

    Fonctionnalité :
    - Nettoie le texte et le divise en lignes courtes.
    - Ajoute une indentation si spécifiée.

    Importance :
    Cette fonction garantit que les paragraphes sont lisibles et bien formatés.

    Arguments :
    - `pdf` : L'instance du document PDF.
    - `texte` : Le texte à ajouter.
    - `indent` : L'espace d'indentation (en pixels).
    """
    texte = nettoyer_bloc(texte)
    if not texte: 
        return
    pdf.set_font('Arial', '', 11)
    lignes = re.split(r'(?<=[.!?])\s+', texte)
    for ligne in lignes:
        for ligne_courte in couper_ligne_longue(ligne.strip()):
            if indent: 
                pdf.cell(indent)
            pdf.multi_cell(0, 6, nettoyer_caracteres_non_latin1(ligne_courte))
    pdf.ln(2)

def lister_contenu(pdf: PDF, elements: List[str], indent: int = 5):
    """
    Rôle :
    Ajoute une liste d'éléments au rapport PDF.

    Fonctionnalité :
    - Nettoie et filtre les éléments inutiles.
    - Ajoute chaque élément sous forme de liste à puces.

    Importance :
    Cette fonction permet de présenter des informations sous forme de listes claires et organisées.

    Arguments :
    - `pdf` : L'instance du document PDF.
    - `elements` : Une liste de chaînes de caractères à afficher.
    - `indent` : L'espace d'indentation (en pixels).
    """
    propres = [nettoyer_texte(el) for el in elements if isinstance(el, str) and not est_ligne_inutile(el)]
    propres = list(set([el for el in propres if len(el) > 5]))
    for el in propres:
        pdf.set_font('Arial', '', 11)
        for ligne in couper_ligne_longue(f"- {el}"):
            if indent: 
                pdf.cell(indent)
            pdf.multi_cell(0, 6, nettoyer_caracteres_non_latin1(ligne))
    pdf.ln(2)

def generate_pdf(donnees: List[Dict], chemin_pdf: str) -> bool:
    """
    Rôle :
    Génère un rapport PDF à partir des données extraites et analysées.

    Fonctionnalité :
    - Parcourt les données des sites pour ajouter des sections comme le résumé, les services, les technologies, etc.
    - Ajoute des titres, des paragraphes et des listes au rapport.
    - Sauvegarde le rapport dans un fichier PDF.

    Importance :
    Cette fonction produit le livrable final du pipeline, un rapport PDF structuré et professionnel.

    Arguments :
    - `donnees` : Une liste de dictionnaires contenant les données des sites.
    - `chemin_pdf` : Le chemin du fichier PDF de sortie.

    Retour :
    `True` si le rapport est généré avec succès, sinon `False`.
    """
    try:
        pdf = PDF()
        pdf.add_page()

        for idx, site in enumerate(donnees):
            # Fusionner les champs de site["data"] si présents
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
                if not contenu: 
                    continue
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
