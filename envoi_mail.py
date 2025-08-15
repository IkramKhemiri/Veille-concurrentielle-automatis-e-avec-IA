#envoi_mail.py 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import schedule
import time
from datetime import datetime

def send_report_email():
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
schedule.every().monday.at("09:00").do(send_report_email)

print("🕒 Programme démarré - Envoi automatique configuré (Lundi 9h)")

while True:
    schedule.run_pending()
    time.sleep(60)  # Vérifie toutes les minutes