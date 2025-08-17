# utils/rapport_final.py

"""
Rôle global :
Ce module est le point final du pipeline de scraping et d'analyse. Il génère un rapport PDF professionnel à partir des données 
extraites et nettoyées, en utilisant les résultats stockés dans un fichier JSON. Ce rapport compile toutes les informations 
pertinentes dans un format lisible et partageable.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module est crucial car il transforme les données 
brutes et analysées en un livrable final exploitable. Le rapport PDF est souvent la sortie attendue par les clients ou les 
décideurs, car il présente les résultats de manière claire, structurée et professionnelle.

Comment il aide dans le pipeline :
- **Scraping** : Compile les données extraites pour les rendre lisibles et présentables.
- **Analyse** : Met en avant les résultats des analyses linguistiques et thématiques.
- **Visualisation** : Organise les informations sous forme de sections claires et hiérarchisées.
- **Rapport** : Produit un document final qui peut être partagé ou archivé.

Technologies utilisées :
- **JSON** : Pour charger les données nettoyées et analysées.
- **OS** : Pour vérifier l'existence des fichiers et gérer les chemins.
- **PDF Report (generate_pdf)** : Pour générer un rapport PDF structuré et professionnel.
"""

import json
import os
from pdf_report import generate_pdf

def main():
    """
    Rôle :
    Point d'entrée principal pour générer le rapport PDF final.

    Fonctionnalité :
    - Vérifie l'existence du fichier JSON contenant les données nettoyées.
    - Charge les données JSON.
    - Génère un rapport PDF à partir des données chargées.

    Importance :
    Cette fonction orchestre l'ensemble du processus de génération du rapport final. Elle garantit que les données 
sont correctement chargées et que le rapport est généré avec succès.

    Étapes :
    1. Vérifie si le fichier `resultats_clean.json` existe.
    2. Charge les données JSON.
    3. Appelle la fonction `generate_pdf` pour créer le rapport PDF.
    4. Affiche un message de succès ou d'échec.

    Arguments :
    Aucun argument direct. Les chemins des fichiers d'entrée et de sortie sont définis dans le code.

    Retour :
    Aucun retour. Les résultats sont affichés dans la console.
    """
    input_path = "resultats_clean.json"
    output_path = "rapport_final.pdf"

    # Vérifie si le fichier JSON d'entrée existe
    if not os.path.exists(input_path):
        print(f"❌ Le fichier {input_path} n'existe pas. Lance d'abord le nettoyage avec `nettoyage_base.py`.")
        return

    # Charge les données JSON
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Vérifie si les données sont vides
    if not data:
        print("⚠️ Aucune donnée trouvée dans resultats_clean.json.")
        return

    # Génère le rapport PDF
    success = generate_pdf(data, output_path)
    if success:
        print(f"✅ Rapport généré avec succès → {output_path}")
    else:
        print("❌ Échec de la génération du rapport.")

# Point d'entrée du script
if __name__ == "__main__":
    """
    Rôle :
    Permet d'exécuter le script directement depuis la ligne de commande.

    Fonctionnalité :
    - Appelle la fonction `main` pour lancer le processus de génération du rapport.

    Importance :
    Cette section garantit que le script peut être exécuté de manière autonome, sans dépendre d'autres modules.
    """
