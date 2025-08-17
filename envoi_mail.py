"""
Rôle global :
Ce module est conçu pour automatiser l'envoi hebdomadaire des rapports générés par le pipeline de scraping et d'analyse. 
Il utilise le protocole SMTP pour envoyer des emails contenant les rapports en pièce jointe à une liste de destinataires.

Pourquoi il est important :
Dans le pipeline global (scraping → analyse → visualisation → rapport), ce module joue un rôle clé en automatisant 
la distribution des livrables finaux. Cela garantit que les parties prenantes reçoivent les rapports à temps, sans intervention manuelle. 
Il améliore également la communication et la collaboration en rendant les résultats accessibles à l'équipe ou aux clients.

Comment il aide dans le pipeline :
- **Scraping** : Compile les rapports générés à partir des données extraites.
- **Analyse** : Partage les résultats des analyses avec les parties prenantes.
- **Visualisation** : Distribue les rapports contenant des visualisations et des insights.
- **Rapport** : Automatise l'envoi des rapports finaux, réduisant ainsi les tâches manuelles.

Technologies utilisées :
- **smtplib** : Pour gérer la connexion au serveur SMTP et envoyer les emails.
- **email.mime** : Pour créer des emails avec des pièces jointes et un contenu HTML.
- **schedule** : Pour planifier l'envoi automatique des emails à une heure précise.
- **datetime** : Pour inclure la date dans le sujet et le corps de l'email.
- **os** : Pour vérifier l'existence des fichiers à joindre.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import schedule
import time
from datetime import datetime

def send_report_email():
    """
    Rôle :
    Envoie un email contenant les rapports hebdomadaires en pièce jointe.

    Fonctionnalité :
    - Configure la connexion au serveur SMTP.
    - Crée un email avec un contenu HTML et des pièces jointes.
    - Envoie l'email à une liste de destinataires.

    Importance :
    Cette fonction garantit que les rapports générés sont envoyés automatiquement aux destinataires, 
    réduisant ainsi les tâches manuelles et assurant une communication régulière.

    Étapes :
    1. Configure les paramètres SMTP (serveur, port, email expéditeur).
    2. Crée un email avec un sujet, un corps HTML et des pièces jointes.
    3. Envoie l'email via le serveur SMTP.

    Arguments :
    Aucun argument direct. Les paramètres (email expéditeur, destinataires, fichiers joints) sont définis dans le code.

    Retour :
    Aucun retour. Affiche un message de succès ou d'erreur dans la console.
    """
    # Configuration SMTP
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "ikram.khemiri@ensi-uma.tn"
    sender_password = "jiwz nniy jukp hcbq"  # À remplacer par os.getenv() en production
    recipient_emails = ["ikramkhemiri416@gmail.com"]

    # Création du message
    msg = MIMEMultipart()
    msg["From"] = f"Ikram Khemiri <{sender_email}>"
    msg["To"] = ", ".join(recipient_emails)
    msg["Subject"] = f"Rapport Hebdomadaire NaviTrends - {datetime.now().strftime('%d/%m/%Y')}"

    # Corps du mail
    email_body = f"""
    <p>Bonjour l'équipe NaviTrends,</p>
    <p>Veuillez trouver ci-joint les rapports du {datetime.now().strftime('%d/%m/%Y')} :</p>
    <ul>
        <li><strong>rapport_sites.pdf</strong> : Données brutes</li>
        <li><strong>rapport_entreprises.pdf</strong> : Données nettoyées</li>
        <li><strong>rapport_final.pdf</strong> : Analyse complète</li>
    </ul>
    <p>Cordialement,<br>Ikram Khemiri</p>
    """
    msg.attach(MIMEText(email_body, "html"))

    # Pièces jointes
    for file in ["rapport_sites.pdf", "rapport_entreprises.pdf", "rapport_final.pdf"]:
        try:
            with open(file, "rb") as f:
                part = MIMEApplication(f.read(), Name=file)
                part["Content-Disposition"] = f'attachment; filename="{file}"'
                msg.attach(part)
        except FileNotFoundError:
            print(f"⚠ Fichier {file} manquant")

    # Envoi
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_emails, msg.as_string())
        print(f"✅ Rapport envoyé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    except Exception as e:
        print(f"❌ Erreur : {e}")

# Planification
"""
Rôle :
Planifie l'envoi automatique des emails chaque lundi à 9h.

Importance :
Cette section garantit que les rapports sont envoyés régulièrement sans intervention manuelle.

Technologies utilisées :
- **schedule** : Pour planifier l'exécution de la fonction `send_report_email`.
"""
schedule.every().monday.at("09:00").do(send_report_email)

print("🕒 Programme démarré - Envoi automatique configuré (Lundi 9h)")

# Boucle principale
"""
Rôle :
Exécute la planification en vérifiant régulièrement les tâches à exécuter.

Importance :
Cette boucle garantit que la fonction `send_report_email` est exécutée à l'heure prévue.

Technologies utilisées :
- **time.sleep** : Pour réduire la charge CPU en vérifiant les tâches toutes les minutes.
"""
while True:
    schedule.run_pending()
    time.sleep(60)  # Vérifie toutes les minutes
