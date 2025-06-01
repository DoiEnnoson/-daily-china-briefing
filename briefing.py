import os
import smtplib
import feedparser
import json
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

# ===============================
# 📡 RSS-Feeds der Nachrichtenquellen
# ===============================
feeds = {
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "New York Post": "https://nypost.com/feed/",
    "Bloomberg": "https://www.bloomberg.com/feed/podcast/next_china.xml",
    "Financial Times": "https://www.ft.com/?format=rss",
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=china&post_type=best",
    "The Guardian": "https://www.theguardian.com/world/china/rss",
    "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar",
    "Welt": "https://www.welt.de/feeds/section/wirtschaft.rss",
    "FAZ": "https://www.faz.net/rss/aktuell/",
    "Frankfurter Rundschau": "https://www.fr.de/rss.xml",
    "Tagesspiegel": "https://www.tagesspiegel.de/rss.xml",
    "Der Standard": "https://www.derstandard.at/rss",
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

# ===============================
# 📡 Stimmen & Perspektiven von X
# ===============================
x_accounts = [
    {"account": "Sino_Market", "name": "CN Wire", "url": "https://x.com/Sino_Market", "always": True},
    {"account": "tonychinaupdate", "name": "China Update", "url": "https://x.com/tonychinaupdate", "always": True},
    {"account": "DrewryShipping", "name": "Drewry", "url": "https://x.com/DrewryShipping", "always": True},
    {"account": "YuanTalks", "name": "YUAN TALKS", "url": "https://x.com/YuanTalks", "always": True},
    {"account": "Brad_Setser", "name": "Brad Setser", "url": "https://x.com/Brad_Setser", "always": True},
    {"account": "KennedyCSIS", "name": "Scott Kennedy", "url": "https://x.com/KennedyCSIS", "always": True},
    {"account": "HannesZipfel", "name": "Hannes Zipfel", "url": "https://x.com/HannesZipfel", "always": True},
    {"account": "BrianTycangco", "name": "Brian Tycangco", "url": "https://x.com/BrianTycangco", "always": True},
    {"account": "michaelxpettis", "name": "Michael Pettis", "url": "https://x.com/michaelxpettis", "always": True},
    {"account": "niubi", "name": "Bill Bishop", "url": "https://x.com/niubi", "always": True},
    {"account": "HAOHONG_CFA", "name": "Hao HONG", "url": "https://x.com/HAOHONG_CFA", "always": True},
    {"account": "HuXijin_GT", "name": "Hu Xijin", "url": "https://x.com/HuXijin_GT", "always": True},
]

# ===============================
# 🔧 Dummy-Funktionen
# ===============================
def fetch_index_data():
    return ["• Hang Seng Index (HSI): 23289.77 ↓ (-1.20 %)"]  # Dummywerte

def fetch_recent_x_posts(account, name, url, always_include=False):
    """Platzhalter-Funktion für X-Posts – später API oder Scraper einfügen."""
    must_include = [
        "sino_market", "tonychinaupdate", "drewryshipping", "yuantalks",
        "brad_setser", "kennedycsis", "hanneszipfel", "briantycangco",
        "michaelxpettis", "niubi", "haohong_cfa", "huxijin_gt"
    ]
    if always_include or account.lower() in must_include:
        return [f"• {name} (@{account}) → {url}"]
    else:
        return []

def fetch_latest_nbs_data():
    return ["Keine aktuellen Veröffentlichungen gefunden."]  # Dummy

def fetch_news(url):
    return []  # Dummy

# ===============================
# ✨ Briefing erstellen
# ===============================
def generate_briefing(feeds):
    date_str = datetime.now().strftime("%d. %B %Y")
    briefing = [f"Guten Morgen, Hado!\n\n🗓️ {date_str}\n\n"]
    briefing.append("📬 Dies ist dein tägliches China-Briefing.\n")

    # === Börsendaten ===
    briefing.append("\n## 📊 Börsenindizes China (08:00 Uhr MESZ)")
    index_data = fetch_index_data()
    briefing.extend(index_data)

    # === Stimmen von X ===
    briefing.append("\n## 📡 Stimmen & Perspektiven von X")
    for acc in x_accounts:
        posts = fetch_recent_x_posts(acc["account"], acc["name"], acc["url"], always_include=acc["always"])
        if posts:
            briefing.extend(posts)

    # === NBS-Daten ===
    briefing.append("\n## 📈 NBS – Nationale Statistikdaten")
    nbs_items = fetch_latest_nbs_data()
    briefing.extend(nbs_items)

    # === Nachrichtenquellen ===
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

# ===============================
# 🚀 Script starten
# ===============================
print("🧠 Erzeuge Briefing...")
briefing_content = generate_briefing(feeds)

msg = MIMEText(briefing_content, "plain", "utf-8")
msg["Subject"] = "📰 Dein tägliches China-Briefing"
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
