import os
import smtplib
import feedparser
import requests
from datetime import datetime
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# === 🔐 Konfiguration aus ENV-Variable ===
config = os.getenv("CONFIG")
if not config:
    raise ValueError("CONFIG environment variable not found!")
pairs = config.split(";")
config_dict = dict(pair.split("=", 1) for pair in pairs)

# === Nachrichtenquellen ===
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

# === Substack-Feeds ===
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

# === SCMP & Yicai ===
feeds_scmp_yicai = {
    "SCMP": "https://www.scmp.com/rss/91/feed",
    "Yicai Global": "https://www.yicaiglobal.com/rss/news"
}
import html

def is_china_related(text):
    return any(kw in text.lower() for kw in china_keywords)

def fetch_news(url, max_items=20):
    """Normale China-News mit Keyword-Filter & Blacklist."""
    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries[:max_items]:
        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", "")
        link = getattr(entry, "link", "")

        combined = f"{title} {summary}".lower()

        if is_china_related(combined) and not any(bad in combined for bad in excluded_keywords):
            articles.append(f"• {title.strip()} ({link.strip()})")

    return articles or ["Keine aktuellen China-Artikel gefunden."]

def fetch_substack_articles(url):
    return fetch_news(url, max_items=10)

def fetch_ranked_articles(feed_url, max_items=20, top_n=5):
    """Spezialfunktion für SCMP & Yicai mit Scoresystem."""
    important_keywords = [
        "xi", "premier li", "taiwan", "nbs", "gdp", "exports", "export", "imports", "sanctions",
        "policy", "housing", "real estate", "property", "home prices", "house prices", "house market",
        "economy", "tech", "semiconductors", "ai", "tariffs"
    ]

    positive_modifiers = [
        "explainer", "analysis", "opinion", "data", "policy", "official", "market", "feature"
    ]

    negative_keywords = excluded_keywords  # für Klarheit

    feed = feedparser.parse(feed_url)
    scored = []

    for entry in feed.entries[:max_items]:
        title = entry.title.strip()
        link = entry.link.strip()
        full = f"{title} {html.unescape(getattr(entry, 'summary', ''))}".lower()

        score = 0
        score += sum(2 for kw in important_keywords if kw in full)
        score += sum(1 for kw in positive_modifiers if kw in full)
        score -= sum(2 for kw in negative_keywords if kw in full)

        if is_china_related(full):
            scored.append((score, f"• {title} ({link})"))

    scored.sort(reverse=True, key=lambda x: x[0])
    top = [entry for score, entry in scored if score > 0][:top_n]
    return top or ["Keine aktuellen China-Artikel gefunden."]

def fetch_latest_nbs_data():
    url = "https://www.stats.gov.cn/sj/zxfb/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        items = []
        for li in soup.select("ul.list_009 li")[:5]:
            a = li.find("a")
            if a and a.text:
                title = a.text.strip()
                link = "https://www.stats.gov.cn" + a["href"]
                items.append(f"• {title} ({link})")
        return items if items else ["Keine aktuellen Veröffentlichungen gefunden."]
    except Exception as e:
        return [f"❌ Fehler beim Abrufen der NBS-Daten: {e}"]

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
# === Briefing-Generator ===

def generate_briefing():
    date_str = datetime.now().strftime("%d. %B %Y")
    briefing = [f"Guten Morgen, Hado!\n\n🗓️ {date_str}\n\n"]
    briefing.append("📬 Dies ist dein tägliches China-Briefing.\n")

    # Börse
    briefing.append("\n## 📊 Börsenindizes China (08:00 Uhr MESZ)")
    briefing.extend(fetch_index_data())

    # X-Ticker
    briefing.append("\n## 📡 Stimmen & Perspektiven von X")
    for acc in x_accounts:
        briefing.extend(fetch_recent_x_posts(acc["account"], acc["name"], acc["url"]))

    # Statistikamt
    briefing.append("\n## 📈 NBS – Nationale Statistikdaten")
    briefing.extend(fetch_latest_nbs_data())

    # Nachrichtenfeeds
    for source, url in feeds.items():
        briefing.append(f"\n## {source}")
        briefing.extend(fetch_news(url))

    # Substack
    briefing.append("\n## 📬 China-Fokus: Substack-Briefings")
    for source, url in feeds_substack.items():
        briefing.append(f"\n### {source}")
        briefing.extend(fetch_substack_articles(url))

    # SCMP & Yicai mit Score-Filter
    briefing.append("\n## SCMP – Top-Themen")
    briefing.extend(fetch_ranked_articles(feeds_scmp_yicai["SCMP"]))

    briefing.append("\n## Yicai Global – Top-Themen")
    briefing.extend(fetch_ranked_articles(feeds_scmp_yicai["Yicai Global"]))

    # Abschluss
    briefing.append("\nEinen erfolgreichen Tag! 🌟")
    return "\n".join(briefing)


# === E-Mail-Versand ===

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
