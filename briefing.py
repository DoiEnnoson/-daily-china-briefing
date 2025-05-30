import os
import smtplib
import feedparser
from datetime import datetime
from email.mime.text import MIMEText

# 🔐 Konfiguration aus ENV-Variable "CONFIG"
config = os.getenv("CONFIG")
if not config:
    raise ValueError("CONFIG environment variable not found!")

pairs = config.split(";")
config_dict = dict(pair.split("=", 1) for pair in pairs)

# 📡 RSS-Feeds der Nachrichtenquellen
feeds = {
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "New York Post": "https://nypost.com/feed/",
    "Bloomberg": "https://www.bloomberg.com/feed/podcast/next_china.xml",
    "Financial Times": "https://www.ft.com/?format=rss",
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=china&post_type=best",
    "The Guardian": "https://www.theguardian.com/world/china/rss",
    "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar"
}

def fetch_news(feed_url, max_items=10):
    """Ruft Nachrichtenartikel ab, filtert nach China-Bezug & entfernt Werbung."""
    feed = feedparser.parse(feed_url)
    china_keywords = [
        "china", "beijing", "shanghai", "hong kong", "li qiang", "xi jinping",
        "taiwan", "cpc", "communist party", "pla", "brics", "belt and road",
        "chinese", "macau", "sino-", "prc", "tencent", "alibaba", "huawei", "byd"
    ]
    excluded_keywords = [
        "bonus", "betting", "sportsbook", "promo code", "odds", "bet365", "casino"
    ]
    articles = []
    for entry in feed.entries[:max_items]:
        title = entry.title.lower()
        link = entry.link
        if any(keyword in title for keyword in china_keywords) and not any(bad in title for bad in excluded_keywords):
            articles.append(f"• {entry.title} ({link})")
    return articles


def generate_briefing(feeds):
    """Erstellt das tägliche China-Briefing als Text."""
    date_str = datetime.now().strftime("%d. %B %Y")
    briefing = [f"Guten Morgen, Hado!\n\n🗓️ {date_str}\n\n"]
    briefing.append("📬 Dies ist dein tägliches China-Briefing.\n")
    for source, url in feeds.items():
        briefing.append(f"\n## {source}")
        try:
            articles = fetch_news(url)
            if articles:
                briefing.extend(articles)
            else:
                briefing.append("Keine aktuellen Artikel gefunden.")
        except Exception as e:
            briefing.append(f"Fehler beim Abrufen: {e}")
    briefing.append("\nEinen erfolgreichen Tag! 🌟")
    return "\n".join(briefing)

# 📦 Inhalt erzeugen
print("🧠 Erzeuge Briefing...")
briefing_content = generate_briefing(feeds)

# ✉️ E-Mail vorbereiten
msg = MIMEText(briefing_content, "plain", "utf-8")
msg["Subject"] = "📰 Dein tägliches China-Briefing"
msg["From"] = config_dict["EMAIL_USER"]
msg["To"] = config_dict["EMAIL_TO"]

print("📤 Sende E-Mail...")

# 📬 E-Mail senden
try:
    with smtplib.SMTP(config_dict["EMAIL_HOST"], int(config_dict["EMAIL_PORT"])) as server:
        server.starttls()
        server.login(config_dict["EMAIL_USER"], config_dict["EMAIL_PASSWORD"])
        server.send_message(msg)
    print("✅ E-Mail wurde gesendet!")
except Exception as e:
    print("❌ Fehler beim Senden der E-Mail:", str(e))
