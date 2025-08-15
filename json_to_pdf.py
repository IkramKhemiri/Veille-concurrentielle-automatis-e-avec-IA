#json_to_pdf.py
"""
GENERATEUR DE RAPPORT ENTREPRISES - VERSION FINALE
"""

import json
from fpdf import FPDF
from datetime import datetime
import re
import os
from pathlib import Path

# ===================== CONFIGURATION =====================
INPUT_JSON = "resultats_clean.json"
LOGO_MAPPING = "logo_mapping.json"
OUTPUT_PDF = "rapport_final.pdf"
REPORT_LOGO = "logos/logo-navitrends.png"
DEFAULT_COMPANY_LOGO = "logos/default-logo.png"
REPORT_TITLE = "Rapport d'Analyse des Entreprises"
REPORT_AUTHOR = "STE NaviTrends Analytics"

# Style Configuration
PRIMARY_COLOR = (0, 80, 155)
SECONDARY_COLOR = (100, 150, 200)
TEXT_COLOR = (40, 40, 40)
COVER_BG_COLOR = (240, 245, 250)
LOGO_MAX_SIZE = (40, 40)  # Taille des logos d'entreprises
COVER_LOGO_SIZE = 80  # Taille du logo principal sur la couverture

class ProfessionalPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=25)
        self.logo_mapping = self.load_logo_mapping()
        self.set_author(REPORT_AUTHOR)
        self.set_creator("Navitrend Report Generator")
        self.default_font = 'helvetica'
        self.alias_nb_pages()

    def load_logo_mapping(self):
        """Charge la configuration des logos"""
        try:
            with open(LOGO_MAPPING, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                
            valid_mapping = {}
            for company, logo_path in mapping.items():
                if os.path.exists(logo_path):
                    valid_mapping[company] = logo_path
                else:
                    print(f"[WARNING] Logo spécifié introuvable: {logo_path}")
            
            if "Default" in mapping and not os.path.exists(mapping["Default"]):
                print(f"[WARNING] Logo par défaut spécifié introuvable: {mapping['Default']}")
            elif not os.path.exists(DEFAULT_COMPANY_LOGO):
                print(f"[WARNING] Logo par défaut standard introuvable: {DEFAULT_COMPANY_LOGO}")
            
            return valid_mapping
        except Exception as e:
            print(f"[ERREUR] Impossible de charger logo_mapping.json: {e}")
            return {}

    def get_company_logo(self, company_name):
        """Trouve le logo approprié pour une entreprise"""
        if not company_name or not isinstance(company_name, str):
            return None
            
        # 1. Correspondance exacte
        if company_name in self.logo_mapping:
            path = self.logo_mapping[company_name]
            if os.path.exists(path):
                return path
        
        # 2. Correspondance insensible à la casse
        lower_name = company_name.lower()
        for name, path in self.logo_mapping.items():
            if name.lower() == lower_name and os.path.exists(path):
                return path
        
        # 3. Logo par défaut
        default_path = self.logo_mapping.get("Default", DEFAULT_COMPANY_LOGO)
        if os.path.exists(default_path):
            return default_path
        
        return None

    def safe_image(self, path, x=None, y=None, w=0, h=0):
        """Tente de charger une image avec gestion des erreurs"""
        try:
            if x is not None and y is not None:
                self.image(path, x=x, y=y, w=w, h=h)
            else:
                self.image(path, w=w, h=h)
            return True
        except Exception as e:
            print(f"[WARNING] Impossible de charger l'image {path}: {str(e)[:100]}")
            return False

    def clean_text_for_pdf(self, text):
        """Nettoie le texte pour éviter les problèmes d'encodage"""
        if not isinstance(text, str):
            text = str(text)
        
        # Remplace les caractères spéciaux problématiques
        replacements = {
            '•': '-',       # Remplace les puces
            '“': '"',       # Guillemets doubles
            '”': '"',
            '‘': "'",      # Guillemets simples
            '’': "'",
            '–': '-',      # Tirets
            '—': '--',
            'é': 'e',      # Accents
            'è': 'e',
            'ê': 'e',
            'à': 'a',
            'ù': 'u',
            'ç': 'c',
            'î': 'i',
            'ï': 'i',
            'ô': 'o',
            'û': 'u'
        }
        
        for orig, repl in replacements.items():
            text = text.replace(orig, repl)
        
        # Supprime les autres caractères non-ASCII
        text = text.encode('latin-1', errors='replace').decode('latin-1')
        return text

    def header(self):
        """En-tête de page - Maintenant simplifié avec juste le titre du rapport"""
        self.set_font(self.default_font, 'B', 14)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, REPORT_TITLE, ln=1)
        
        # Ligne de séparation
        self.set_draw_color(*SECONDARY_COLOR)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        """Pied de page"""
        self.set_y(-15)
        self.set_font(self.default_font, 'I', 8)
        self.set_text_color(150, 150, 150)
        page_num = f"Page {self.page_no()}/{{nb}}"
        self.cell(0, 10, self.clean_text_for_pdf(f"{page_num} • {REPORT_AUTHOR} • {datetime.now().strftime('%d/%m/%Y')}"), 0, 0, 'C')

    def create_cover_page(self):
        """Page de couverture améliorée"""
        self.add_page()
        self.set_fill_color(*COVER_BG_COLOR)
        self.rect(0, 0, 210, 297, 'F')

        # Titre principal
        self.set_y(130)
        self.set_font(self.default_font, 'B', 28)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 20, REPORT_TITLE, ln=1, align='C')

        # Sous-titre
        self.set_font(self.default_font, '', 18)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "Analyse sectorielle complète", ln=1, align='C')
        

        # Logo principal centré et plus grand
        if os.path.exists(REPORT_LOGO):
            self.image(REPORT_LOGO, x=(210-COVER_LOGO_SIZE)/2, y=40, w=COVER_LOGO_SIZE)
        else:
            print(f"[WARNING] Logo principal introuvable: {REPORT_LOGO}")
        
        # Informations complémentaires
        self.set_y(200)
        self.set_font(self.default_font, 'I', 14)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, datetime.now().strftime("%B %Y"), ln=1, align='C')
        
        # Auteur
        self.set_font(self.default_font, 'B', 16)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, REPORT_AUTHOR, ln=1, align='C')
        
        # Note de bas de page
        self.set_y(-30)
        self.set_font(self.default_font, 'I', 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "Document généré automatiquement - Données confidentielles", 0, 0, 'C')

    def create_introduction(self):
        """Page d'introduction enrichie"""
        self.add_page()
        self.set_font(self.default_font, 'B', 18)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 15, "Introduction", ln=1)
        self.line(10, self.get_y(), 50, self.get_y())
        self.ln(15)
        
        # Introduction détaillée
        intro_text = """
Ce rapport exhaustif présente une analyse approfondie des entreprises sélectionnées dans notre base de données. 
Réalisé par NaviTrends Analytics, ce document offre une vision complète du paysage sectoriel avec :

- Une fiche détaillée pour chaque entreprise
- L'analyse des services et technologies clés
- La cartographie des secteurs clients
- Une évaluation des positionnements stratégiques

Méthodologie :
Notre processus rigoureux combine :
1. Collecte de données multi-sources
2. Vérification et validation des informations
3. Analyse par notre plateforme d'intelligence artificielle
4. Génération automatisée de rapports

Structure du rapport :
- Une fiche par entreprise avec logo et informations clés
- Une synthèse des activités principales
- L'analyse des technologies utilisées
- Le détail des secteurs clients servis
"""
        self.set_font(self.default_font, '', 12)
        self.set_text_color(*TEXT_COLOR)
        self.multi_cell(0, 6, self.clean_text_for_pdf(intro_text))
        
        # Ajout d'une section sur l'utilisation du rapport
        self.ln(10)
        self.set_font(self.default_font, 'B', 14)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, "Utilisation du rapport", ln=1)
        self.line(10, self.get_y(), 50, self.get_y())
        self.ln(5)
        
        usage_text = """
Ce document constitue un outil précieux pour :
- L'analyse concurrentielle
- L'identification de partenaires potentiels
- La veille technologique
- L'étude de marché sectorielle

Les logos des entreprises sont affichés lorsqu'ils sont disponibles. Les informations présentées ont été vérifiées mais peuvent être sujettes à changement.
"""
        self.set_font(self.default_font, '', 11)
        self.multi_cell(0, 6, self.clean_text_for_pdf(usage_text))

    def add_company_section(self, company_data):
        """Ajoute une section entreprise avec logo sous le nom"""
        if not company_data or not company_data.get('name'):
            return
            
        self.current_company = company_data
        self.add_page()
        
        # Nom de l'entreprise (sans logo dans l'en-tête)
        self.set_y(30)
        self.set_font(self.default_font, 'B', 18)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, self.clean_text_for_pdf(company_data['name']), ln=1, align='C')
        
        # Logo centré sous le nom
        logo_path = self.get_company_logo(company_data['name'])
        if logo_path and self.safe_image(logo_path, x=(210-LOGO_MAX_SIZE[0])/2, y=45, 
                                       w=LOGO_MAX_SIZE[0], h=LOGO_MAX_SIZE[1]):
            self.ln(LOGO_MAX_SIZE[1] + 10)  # Espacement après le logo
        else:
            self.ln(15)  # Espacement même sans logo
        
        # Introduction de l'entreprise
        if company_data.get('introduction'):
            self.set_font(self.default_font, 'I', 12)
            self.set_text_color(80, 80, 80)
            self.multi_cell(0, 7, self.clean_text_for_pdf(company_data['introduction']))
            self.ln(10)
        
        # Informations de base
        self.set_font(self.default_font, 'B', 12)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(40, 8, "Site web:", ln=0)
        self.set_font(self.default_font, '', 10)
        self.set_text_color(*SECONDARY_COLOR)
        self.cell(0, 8, self.clean_text_for_pdf(company_data.get('url', 'Non disponible')), ln=1)
        self.ln(8)
        
        # Sections détaillées
        self.add_section("Services Principaux", company_data.get('services'))
        self.add_section("Technologies Utilisées", company_data.get('technologies'))
        self.add_section("Secteurs Clients", company_data.get('clients'))
        self.add_section("Description Complète", company_data.get('full_content'), is_list=False)

    def add_section(self, title, content, is_list=True):
        """Ajoute une section avec contenu"""
        if not content:
            return
            
        self.set_font(self.default_font, 'B', 14)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 10, f"{self.clean_text_for_pdf(title)}:", ln=1)
        self.line(10, self.get_y(), 50, self.get_y())
        self.ln(8)
        
        self.set_font(self.default_font, '', 11)
        self.set_text_color(*TEXT_COLOR)
        
        if is_list and isinstance(content, list):
            for item in content:
                if item:  # Ignore les éléments vides
                    if isinstance(item, dict):
                        text = f"- {self.clean_text_for_pdf(item.get('name', ''))}: {self.clean_text_for_pdf(item.get('description', ''))}"
                    else:
                        text = f"- {self.clean_text_for_pdf(item)}"
                    self.multi_cell(0, 7, text)
                    self.ln(4)
        else:
            self.multi_cell(0, 7, self.clean_text_for_pdf(str(content)))
        
        self.ln(12)

def generate_pdf_report():
    """Génère le rapport PDF complet"""
    # Vérification des fichiers
    required_files = {
        INPUT_JSON: "Fichier de données JSON",
        LOGO_MAPPING: "Configuration des logos"
    }
    
    for file, desc in required_files.items():
        if not os.path.exists(file):
            print(f"[ERREUR] {desc} introuvable: {file}")
            return
    
    # Chargement des données
    try:
        with open(INPUT_JSON, 'r', encoding='utf-8') as f:
            companies = [c for c in json.load(f) if c and c.get('name')]  # Filtre les entreprises sans nom
    except Exception as e:
        print(f"[ERREUR] Impossible de charger {INPUT_JSON}: {e}")
        return
    
    if not companies:
        print("[ERREUR] Aucune entreprise valide trouvée dans le fichier JSON")
        return
    
    # Création du PDF
    print(f"Début de la génération du PDF pour {len(companies)} entreprises...")
    pdf = ProfessionalPDF()
    
    try:
        # Pages initiales
        pdf.create_cover_page()
        pdf.create_introduction()
        
        # Fiches entreprises
        for idx, company in enumerate(companies, 1):
            name = company.get('name', 'Sans nom')
            print(f"Traitement {idx}/{len(companies)}: {name[:50]}...")
            pdf.add_company_section(company)
        
        # Sauvegarde finale
        pdf.output(OUTPUT_PDF)
        print(f"\nRapport généré avec succès: {OUTPUT_PDF}")
        print(f"Entreprises incluses: {len(companies)}")
        
    except Exception as e:
        print(f"\n[ERREUR CRITIQUE] Échec de génération: {e}")

if __name__ == "__main__":
    generate_pdf_report()