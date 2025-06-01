import os
import smtplib
import feedparser
import requests
from datetime import datetime
from email.mime.text import MIMEText

# === Konfiguration aus ENV ===
config = os.getenv("CONFIG")
if not config:
    raise ValueError("CONFIG environment variable not found!")

pairs = config.split(";")
config_dict = dict(pair.split("=", 1) for pair in pairs)

# === RSS-Feeds ===
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

feeds_substack = {
    "Sinocism – Bill Bishop": "https://sinocism.com/feed",
    "ChinaTalk – Jordan Schneider": "https://chinatalk.substack.com/feed",
    "Pekingology": "https://pekingnology.substack.com/feed",
    "The Rare Earth Observer": "https://treo.substack.com/feed",
    "Baiguan": "https://www.baiguan.news/feed",
    "Bert’s Newsletter": "https://berthofman.substack.com/feed",
    "Hong Kong Money Never Sleeps": "https://moneyhk.substack.com/feed",
    "Tracking People’s Daily": "https://trackingpeoplesdaily.substack.com/feed",
    "Interconnected": "https://interconnect.substack.com/feed",
    "Ginger River Review": "https://www.gingerriver.com/feed",
    "The East is Read": "https://www.eastisread.com/feed",
    "Inside China – Fred Gao": "https://www.fredgao.com/feed",
    "China Business Spotlight": "https://chinabusinessspotlight.substack.com/feed",
    "ChinAI Newsletter": "https://chinai.substack.com/feed",
    "Tech Buzz China Insider": "https://techbuzzchina.substack.com/feed",
    "Sinical China": "https://www.sinicalchina.com/feed",
    "Observing China": "https://www.observingchina.org.uk/feed"
}

feeds_scmp_yicai = {
    "SCMP": "https://www.scmp.com/rss/91/feed",
    "Yicai Global": "https://www.yicaiglobal.com/rss/news"
}

china_keywords = [
    "china", "beijing", "shanghai", "hong kong", "li qiang", "xi jinping",
    "taiwan", "cpc", "communist party", "pla", "prc", "macau", "alibaba",
    "tencent", "huawei", "byd", "brics", "belt and road", "made in china"
]

def is_china_related(title):
    return any(kw in title.lower() for kw in china_keywords)

def fetch_news(url, max_items=20):
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries[:max_items]:
        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "")
        link = getattr(entry, "link", "")
        
        # Normalisierte Textbasis
        combined = f"{title} {summary} {link}".lower()

        # China-Filter
        if any(kw in combined for kw in china_keywords):
            if not any(bad in combined for bad in [
                "rapid", "lask", "bundesliga", "champions league", "eurovision", 
                "gaza", "selenskyj", "transgender", "elon musk", "donau-dinos",
                "waymo", "nazi", "papst", "mode", "robotaxi", "quiz", "kulturkriege"
            ]):
                articles.append(f"• {title.strip()} ({link.strip()})")

    return articles or ["Keine aktuellen China-Artikel gefunden."]

def fetch_substack_articles(url):
    return fetch_news(url)

def fetch_ranked_articles(url):
    return fetch_news(url)

def fetch_latest_nbs_data():
    # Platzhalter: spätere API-Anbindung möglich
    return ["Keine aktuellen Veröffentlichungen gefunden."]

def fetch_index_data():
    indices = {
        "Hang Seng Index (HSI)": "^HSI",
        "Hang Seng China Enterprises (HSCEI)": "^HSCE",
        "SSE Composite Index (Shanghai)": "000001.SS",
        "Shenzhen Component Index": "399001.SZ"
    }

    headers = { "User-Agent": "Mozilla/5.0" }
    results = []

    for name, symbol in indices.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            if len(closes) < 2 or not all(closes[-2:]):
                results.append(f"❌ {name}: Keine gültigen Kursdaten verfügbar.")
                continue
            prev_close = closes[-2]
            last_close = closes[-1]
            change = last_close - prev_close
            change_pct = (change / prev_close) * 100
            symbol_arrow = "→" if abs(change_pct) < 0.01 else ("↑" if change > 0 else "↓")
            results.append(f"• {name}: {round(last_close, 2)} {symbol_arrow} ({change_pct:+.2f} %)")
        except Exception as e:
            results.append(f"❌ {name}: Fehler beim Abrufen ({e})")
    return results

def fetch_recent_x_posts(account, name, url, always_include=False):
    return [f"• {name} (@{account}) → {url}"]

x_accounts = [
    {"account": "Sino_Market", "name": "CN Wire", "url": "https://x.com/Sino_Market"},
    {"account": "tonychinaupdate", "name": "China Update", "url": "https://x.com/tonychinaupdate"},
    {"account": "DrewryShipping", "name": "Drewry", "url": "https://x.com/DrewryShipping"},
    {"account": "YuanTalks", "name": "YUAN TALKS", "url": "https://x.com/YuanTalks"},
    {"account": "Brad_Setser", "name": "Brad Setser", "url": "https://x.com/Brad_Setser"},
    {"account": "KennedyCSIS", "name": "Scott Kennedy", "url": "https://x.com/KennedyCSIS"},
    {"account": "HannesZipfel", "name": "Hannes Zipfel", "url": "https://x.com/HannesZipfel"},
    {"account": "BrianTycangco", "name": "Brian Tycangco", "url": "https://x.com/BrianTycangco"},
    {"account": "michaelxpettis", "name": "Michael Pettis", "url": "https://x.com/michaelxpettis"},
    {"account": "niubi", "name": "Bill Bishop", "url": "https://x.com/niubi"},
    {"account": "HAOHONG_CFA", "name": "Hao HONG", "url": "https://x.com/HAOHONG_CFA"},
    {"account": "HuXijin_GT", "name": "Hu Xijin", "url": "https://x.com/HuXijin_GT"},
]

def generate_briefing():
    date_str = datetime.now().strftime("%d. %B %Y")
    briefing = [f"Guten Morgen, Hado!\n\n🗓️ {date_str}\n\n"]
    briefing.append("📬 Dies ist dein tägliches China-Briefing.\n")

    briefing.append("\n## 📊 Börsenindizes China (08:00 Uhr MESZ)")
    briefing.extend(fetch_index_data())

    briefing.append("\n## 📡 Stimmen & Perspektiven von X")
    for acc in x_accounts:
        briefing.extend(fetch_recent_x_posts(acc["account"], acc["name"], acc["url"]))

    briefing.append("\n## 📈 NBS – Nationale Statistikdaten")
    briefing.extend(fetch_latest_nbs_data())

    for source, url in feeds.items():
        briefing.append(f"\n## {source}")
        briefing.extend(fetch_news(url))

    briefing.append("\n## 📬 China-Fokus: Substack-Briefings")
    for source, url in feeds_substack.items():
        briefing.append(f"\n### {source}")
        briefing.extend(fetch_substack_articles(url))

    briefing.append("\n## SCMP – Top-Themen")
    briefing.extend(fetch_ranked_articles(feeds_scmp_yicai["SCMP"]))

    briefing.append("\n## Yicai Global – Top-Themen")
    briefing.extend(fetch_ranked_articles(feeds_scmp_yicai["Yicai Global"]))

    briefing.append("\nEinen erfolgreichen Tag! 🌟")
    return "\n".join(briefing)

# === Senden ===
print("🧠 Erzeuge Briefing...")
briefing_content = generate_briefing()

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
