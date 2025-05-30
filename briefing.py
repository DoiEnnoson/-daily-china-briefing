import os
import smtplib
import feedparser
import requests
from bs4 import BeautifulSoup
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
    # ===============================
    # 📺 Anglo-American Media
    # ===============================
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "New York Post": "https://nypost.com/feed/",
    "Bloomberg": "https://www.bloomberg.com/feed/podcast/next_china.xml",
    "Financial Times": "https://www.ft.com/?format=rss",
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=china&post_type=best",
    "The Guardian": "https://www.theguardian.com/world/china/rss",
    "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar",

    # ===============================
    # 📰 Deutsche Medien
    # ===============================
    "Welt": "https://www.welt.de/feeds/section/wirtschaft.rss",
    "FAZ": "https://www.faz.net/rss/aktuell/",
    "Frankfurter Rundschau": "https://www.fr.de/rss.xml",
    "Tagesspiegel": "https://www.tagesspiegel.de/rss.xml",
    "Der Standard": "https://www.derstandard.at/rss",

    # ===============================
    # 🧠 Think Tanks & Institute
    # ===============================
    "MERICS": "https://merics.org/en/rss.xml",
    "CSIS": "https://www.csis.org/rss.xml",
    "CREA (Energy & Clean Air)": "https://energyandcleanair.org/feed/",
    "Brookings": "https://www.brookings.edu/feed/",
    "Peterson Institute": "https://www.piie.com/rss/all",
    "CFR – Council on Foreign Relations": "https://www.cfr.org/rss.xml",
    "RAND Corporation": "https://www.rand.org/rss.xml",
    "Chatham House": "https://www.chathamhouse.org/rss.xml",
    "Lowy Institute": "https://www.lowyinstitute.org/the-interpreter/rss.xml"
}

def fetch_news(feed_url, max_items=10):
    """Ruft Nachrichtenartikel ab, filtert nach China-Bezug & entfernt Werbung."""
    feed = feedparser.parse(feed_url)

    china_keywords = [
        # Englisch
        "china", "beijing", "shanghai", "hong kong", "xi jinping", "taiwan", "pla",
        "cpc", "communist party", "prc", "belt and road", "huawei", "byd", "tiktok",
        # Deutsch
        "china", "peking", "shanghai", "hongkong", "xi jinping", "taiwan", "kpch",
        "volksbefreiungsarmee", "seidenstraße", "huawei", "alibaba", "byd", "tiktok"
    ]

    excluded_keywords = [
        "bonus", "betting", "sportsbook", "promo code", "odds", "bet365", "casino",
        "gewinnspiel", "wetten", "lotterie"
    ]

    articles = []
    for entry in feed.entries[:max_items]:
        title = entry.title.lower()
        link = entry.link
        if any(keyword in title for keyword in china_keywords) and not any(bad in title for bad in excluded_keywords):
            articles.append(f"• {entry.title} ({link})")
    return articles

def fetch_latest_nbs_data():
    """Holt die neuesten Veröffentlichungen vom Statistikamt der VR China (NBS)."""
    url = "https://www.stats.gov.cn/sj/zxfb/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        items = []

        for li in soup.select("ul.list_009 li")[:5]:  # nur die ersten 5 Beiträge prüfen
            a = li.find("a")
            if a and a.text:
                title = a.text.strip()
                link = "https://www.stats.gov.cn" + a["href"]
                items.append(f"• {title} ({link})")
        return items if items else ["Keine aktuellen Veröffentlichungen gefunden."]
    except Exception as e:
        return [f"❌ Fehler beim Abrufen der NBS-Daten: {e}"]

def generate_briefing(feeds):
    """Erstellt das tägliche China-Briefing als Text."""
    date_str = datetime.now().strftime("%d. %B %Y")
    briefing = [f"Guten Morgen, Hado!\n\n🗓️ {date_str}\n\n"]
    briefing.append("📬 Dies ist dein tägliches China-Briefing.\n")

    # === NBS: Statistikamt China ===
    briefing.append("\n## 📈 NBS – Nationale Statistikdaten")
    nbs_items = fetch_latest_nbs_data()
    briefing.extend(nbs_items)

    # === RSS-Feeds ===
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
