#runall.py
import os
import subprocess
import time
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SCRIPTS = [
    "multi_scraper.py",
    "nettoyage_base.py", 
    "json_to_pdf.py",
    "nlp_tfidf_visualisation.py",
    "dashboard.py",
    "envoi_mail.py"
]

REQUIRED_FILES = {
    "rapport_sites.pdf": "Généré par multi_scraper.py",
    "rapport_entreprises.pdf": "Généré par json_to_pdf.py",
    "rapport_final.pdf": "Généré par nlp_tfidf_visualisation.py"
}

def validate_environment():
    """Vérifie que tous les fichiers requis existent avant l'exécution"""
    missing = []
    for file, source in REQUIRED_FILES.items():
        if not os.path.exists(file):
            missing.append(f"{file} ({source})")
    
    if missing:
        logger.error("❌ Fichiers manquants :\n" + "\n".join(missing))
        return False
    return True

def run_script(script_name):
    """Exécute un script Python avec gestion des erreurs"""
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