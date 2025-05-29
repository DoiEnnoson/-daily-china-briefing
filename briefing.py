import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Konfig aus Umgebungsvariable laden
config_string = os.getenv("CONFIG")
if not config_string:
    raise ValueError("CONFIG environment variable not found!")

print("✅ CONFIG wurde geladen.")

# Umwandeln in Dictionary
pairs = config_string.split(";")
config = dict(pair.split("=", 1) for pair in pairs)

# Beispielhafte Briefing-Erzeugung
def generate_briefing():
    print("🧠 Erzeuge Briefing...")
    return "Guten Morgen!\n\nDies ist dein tägliches China-Briefing.\n\n– Wirtschaft\n– Politik\n– Außenbeziehungen\n\nSchönen Tag dir!"

# E-Mail-Versand
def send_email(subject, content):
    print("📤 Sende E-Mail...")
    try:
        msg = MIMEMultipart()
        msg['From'] = config['EMAIL_USER']
        msg['To'] = config['EMAIL_TO']
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain'))

        server = smtplib.SMTP(config['EMAIL_HOST'], int(config['EMAIL_PORT']))
        server.starttls()
        server.login(config['EMAIL_USER'], config['EMAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()

        print("✅ E-Mail wurde gesendet!")
    except Exception as e:
        print("❌ Fehler beim Senden der E-Mail:", e)

# Ablauf starten
if __name__ == "__main__":
    content = generate_briefing()
    send_email("📰 Daily China Briefing", content)
