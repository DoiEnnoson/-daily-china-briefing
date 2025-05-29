import os
import smtplib
from email.mime.text import MIMEText

# Konfiguration aus ENV laden
config = os.getenv("CONFIG")
if not config:
    raise ValueError("CONFIG environment variable not found!")

pairs = config.split(";")
config_dict = dict(pair.split("=", 1) for pair in pairs)

# Beispiel-Inhalt für das Briefing
briefing_content = """
Guten Morgen, Hado

📅 Dies ist dein tägliches China-Briefing – Testversion.

🌏 Wirtschaft:
– Chinas Industrieproduktion stieg im April um 6,7 % im Jahresvergleich.
– Tesla senkt erneut die Preise in China – Konkurrenzdruck durch BYD wächst.

🏛️ Politik:
– Premier Li Qiang empfängt eine Delegation aus Deutschland.
– Hongkongs Sicherheitsgesetz sorgt für neue Spannungen mit den USA.

🌐 Außenbeziehungen:
– China und Brasilien vertiefen ihre Kooperation im Agrarsektor.
– Neue Spannungen im Südchinesischen Meer mit den Philippinen.

🧪 Dies ist ein Testinhalt. Morgen bekommst du echte Daten 😉

Einen erfolgreichen neuen Tag! 
"""

print("✅ CONFIG wurde geladen.")
print("🧠 Erzeuge Briefing...")

# E-Mail vorbereiten
msg = MIMEText(briefing_content)
msg["Subject"] = "Dein tägliches China-Briefing"
msg["From"] = config_dict["EMAIL_USER"]
msg["To"] = config_dict["EMAIL_TO"]

print("📤 Sende E-Mail...")

try:
    with smtplib.SMTP(config_dict["EMAIL_HOST"], int(config_dict["EMAIL_PORT"])) as server:
        server.starttls()
        server.login(config_dict["EMAIL_USER"], config_dict["EMAIL_PASSWORD"])
        server.send_message(msg)
    print("✅ E-Mail wurde gesendet!")
except Exception as e:
    print("❌ Fehler beim Senden der E-Mail:", str(e))
