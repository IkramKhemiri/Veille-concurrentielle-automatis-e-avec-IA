"""
Rôle global :
Ce module orchestre l'exécution complète du pipeline de traitement, allant du scraping des données à leur analyse, 
visualisation et envoi des rapports. Il exécute chaque étape dans l'ordre, vérifie les prérequis, et gère les erreurs 
pour garantir une exécution fluide et cohérente.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module est essentiel car il automatise 
l'ensemble du processus. Il permet de s'assurer que toutes les étapes sont exécutées correctement, dans le bon ordre, 
et que les résultats finaux sont prêts à être partagés. Cela réduit les interventions manuelles et garantit une efficacité maximale.

Comment il aide dans le pipeline :
- **Scraping** : Lance le script de scraping pour collecter les données.
- **Analyse** : Exécute les scripts de nettoyage et d'analyse pour structurer et enrichir les données.
- **Visualisation** : Génère des visualisations et des rapports PDF.
- **Rapport** : Automatise l'envoi des rapports finaux par email.

Technologies utilisées :
- **Subprocess** : Pour exécuter les scripts Python externes et capturer leurs sorties.
- **Logging** : Pour suivre l'exécution du pipeline et enregistrer les erreurs ou succès.
- **OS** : Pour vérifier l'existence des fichiers requis.
- **Datetime** : Pour inclure des informations temporelles dans les logs.
"""

import os
import subprocess
import time
import logging
from datetime import datetime

# Configuration du logging
"""
Rôle :
Configure le système de journalisation pour enregistrer les événements importants, les erreurs et les succès.

Importance :
Permet de suivre l'exécution du pipeline, d'identifier les problèmes rapidement et de conserver un historique des exécutions.

Technologies utilisées :
- **Logging** : Pour enregistrer les événements dans un fichier et les afficher dans la console.
"""
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Liste des scripts à exécuter dans l'ordre
SCRIPTS = [
    "multi_scraper.py",
    "nettoyage_base.py", 
    "json_to_pdf.py",
    "nlp_tfidf_visualisation.py",
    "dashboard.py",
    "envoi_mail.py"
]

# Fichiers requis pour valider l'environnement
REQUIRED_FILES = {
    "rapport_sites.pdf": "Généré par multi_scraper.py",
    "rapport_entreprises.pdf": "Généré par json_to_pdf.py",
    "rapport_final.pdf": "Généré par nlp_tfidf_visualisation.py"
}

def validate_environment():
    """
    Rôle :
    Vérifie que tous les fichiers requis pour le pipeline existent.

    Fonctionnalité :
    - Parcourt la liste des fichiers requis.
    - Vérifie leur existence sur le disque.
    - Affiche un message d'erreur si des fichiers sont manquants.

    Importance :
    Garantit que le pipeline dispose des fichiers nécessaires pour fonctionner correctement.

    Retour :
    `True` si tous les fichiers requis sont présents, sinon `False`.
    """
    missing = []
    for file, source in REQUIRED_FILES.items():
        if not os.path.exists(file):
            missing.append(f"{file} ({source})")
    
    if missing:
        logger.error("❌ Fichiers manquants :\n" + "\n".join(missing))
        return False
    return True

def run_script(script_name):
    """
    Rôle :
    Exécute un script Python en tant que sous-processus.

    Fonctionnalité :
    - Lance le script avec `subprocess.run`.
    - Capture la sortie standard et les erreurs.
    - Enregistre les résultats dans les logs.

    Importance :
    Permet d'exécuter chaque étape du pipeline de manière isolée, avec une gestion robuste des erreurs.

    Arguments :
    - `script_name` : Le nom du script à exécuter.

    Retour :
    `True` si le script s'exécute avec succès, sinon `False`.
    """
    logger.info(f"🚀 Lancement de {script_name}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["python", script_name],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Journalisation de la sortie
        if result.stdout:
            logger.debug(f"Sortie de {script_name}:\n{result.stdout}")
        
        duration = time.time() - start_time
        logger.info(f"✅ {script_name} terminé avec succès (en {duration:.2f}s)")
        return True
        
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        logger.error(f"❌ Erreur dans {script_name} (après {duration:.2f}s):")
        logger.error(f"Code sortie: {e.returncode}")
        logger.error(f"Erreur:\n{e.stderr}")
        return False

def main():
    """
    Rôle :
    Point d'entrée principal pour exécuter le pipeline complet.

    Fonctionnalité :
    - Valide l'environnement en vérifiant les fichiers requis.
    - Exécute chaque script dans l'ordre défini.
    - Gère les erreurs et interrompt le pipeline si un script échoue.

    Importance :
    Ordonne et supervise l'exécution de toutes les étapes du pipeline, garantissant une exécution fluide et cohérente.

    Étapes :
    1. Valide l'environnement.
    2. Exécute les scripts un par un.
    3. Enregistre les résultats dans les logs.

    Retour :
    Aucun retour. Les résultats sont affichés dans la console et enregistrés dans les logs.
    """
    logger.info("="*60)
    logger.info(f"🔄 Début du pipeline le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    logger.info("="*60)
    
    if not validate_environment():
        return
    
    for script in SCRIPTS:
        success = run_script(script)
        if not success:
            logger.error(f"⛔ Pipeline interrompu - {script} a échoué")
            return
        
        # Pause entre les scripts pour éviter les conflits
        time.sleep(2)
    
    logger.info("="*60)
    logger.info(f"🏁 Pipeline terminé avec succès le {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    logger.info("="*60)

if __name__ == "__main__":
    main()
