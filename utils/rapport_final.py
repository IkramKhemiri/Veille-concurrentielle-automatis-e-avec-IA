# utils/rapport_final.py

import json
import os
from pdf_report import generate_pdf

def main():
    input_path = "resultats_clean.json"
    output_path = "rapport_final.pdf"

    if not os.path.exists(input_path):
        print(f"❌ Le fichier {input_path} n'existe pas. Lance d'abord le nettoyage avec `nettoyage_base.py`.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("⚠️ Aucune donnée trouvée dans resultats_clean.json.")
        return

    success = generate_pdf(data, output_path)
    if success:
        print(f"✅ Rapport généré avec succès → {output_path}")
    else:
        print("❌ Échec de la génération du rapport.")

if __name__ == "__main__":
    main()
