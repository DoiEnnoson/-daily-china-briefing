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

# === Funktionen zum Artikelabruf ===

def fetch_news(feed_url, max_items=20):
    """Filtert nach China-Bezug & entfernt irrelevante oder boulevardeske Inhalte."""
    feed = feedparser.parse(feed_url)
    results = []

    for entry in feed.entries[:max_items]:
        title = entry.title.strip()
        summary = html.unescape(getattr(entry, "summary", ""))
        link = entry.link.strip()
        combined = f"{title} {summary}".lower()

        if any(kw in combined for kw in china_keywords) and not any(bad in combined for bad in excluded_keywords):
            results.append(f"• {title} ({link})")

    return results or ["Keine aktuellen China-Artikel gefunden."]

def fetch_substack_articles(feed_url):
    return fetch_news(feed_url, max_items=10)

# === Spezialfilter für SCMP & Yicai ===

def fetch_ranked_articles(feed_url, max_items=20, top_n=5):
    """Scoring-System zur Relevanzbewertung von Artikeln."""
    feed = feedparser.parse(feed_url)
    articles = []

    important_keywords = [
        "xi", "premier li", "taiwan", "nbs", "gdp", "exports", "export", "imports", "sanctions",
        "policy", "housing", "real estate", "property", "home prices", "house prices", "house market",
        "economy", "tech", "semiconductors", "ai", "tariffs"
    ]
    positive_modifiers = ["analysis", "explainer", "opinion", "policy", "data", "feature", "market"]
    negative_keywords = excluded_keywords  # Wiederverwendung

    for entry in feed.entries[:max_items]:
        title = entry.title.strip()
        summary = html.unescape(getattr(entry, "summary", ""))
        link = entry.link.strip()
        combined = f"{title} {summary}".lower()

        if not any(kw in combined for kw in china_keywords):
            continue

        score = 0
        score += sum(2 for kw in important_keywords if kw in combined)
        score += sum(1 for kw in positive_modifiers if kw in combined)
        score -= sum(2 for kw in negative_keywords if kw in combined)

        if score > 0:
            articles.append((score, f"• {title} ({link})"))

    articles.sort(reverse=True, key=lambda x: x[0])
    return [a for _, a in articles[:top_n]] or ["Keine aktuellen China-Artikel gefunden."]

# === Börsenindizes ===

def fetch_index_data():
    indices = {
        "Hang Seng Index (HSI)": "^HSI",
        "Hang Seng China Enterprises (HSCEI)": "^HSCE",
        "SSE Composite Index (Shanghai)": "000001.SS",
        "Shenzhen Component Index": "399001.SZ"
    }

    headers = {"User-Agent": "Mozilla/5.0"}
    results = []

    for name, symbol in indices.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            if len(closes) < 2 or not all(closes[-2:]):
                results.append(f"❌ {name}: Keine gültigen Kursdaten verfügbar.")
                continue
            prev, last = closes[-2], closes[-1]
            change_pct = (last - prev) / prev * 100
            arrow = "→" if abs(change_pct) < 0.01 else ("↑" if last > prev else "↓")
            results.append(f"• {name}: {round(last, 2)} {arrow} ({change_pct:+.2f} %)")
        except Exception as e:
            results.append(f"❌ {name}: Fehler beim Abrufen ({e})")
    return results

# === NBS-Daten ===

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
        return items or ["Keine aktuellen Veröffentlichungen gefunden."]
    except Exception as e:
        return [f"❌ Fehler beim Abrufen der NBS-Daten: {e}"]

# === Twitter/X Accounts ===

def fetch_recent_x_posts(account, name, url, always_include=False):
    return [f"• {name} (@{account}) → {url}"]
# === China-Filter & Score-Funktionen ===

china_keywords = [
    "china", "beijing", "shanghai", "hong kong", "li qiang", "xi jinping", "taiwan",
    "cpc", "communist party", "pla", "prc", "macau", "alibaba", "tencent", "huawei",
    "byd", "brics", "belt and road", "made in china"
]

excluded_keywords = [
    "bonus", "betting", "sportsbook", "promo code", "odds", "bet365", "casino",
    "gewinnspiel", "wetten", "lotterie", "celebrity", "fashion", "movie", "series",
    "dog", "cat", "baby", "married", "wedding", "love", "dating", "gossip", "bizarre",
    "tiktok prank", "weird", "rapid", "lask", "bundesliga", "champions league", "eurovision",
    "elon musk", "donau-dinos", "robotaxi", "kulturkriege", "papst", "quiz", "selenskyj", "gaza"
]

important_keywords = [
    "xi", "premier li", "taiwan", "nbs", "gdp", "exports", "export", "imports", "sanctions",
    "policy", "housing", "real estate", "property", "home prices", "house prices",
    "economy", "semiconductors", "ai", "tariffs", "market", "central bank", "stocks", "li auto", "byd", "baidu"
]

positive_modifiers = [
    "explainer", "analysis", "opinion", "data", "policy", "official", "market", "feature", "insight"
]

# === Artikel mit Relevanzwertung (z.B. für SCMP, Yicai) ===
def fetch_ranked_articles(feed_url, max_items=20, top_n=5):
    feed = feedparser.parse(feed_url)
    articles = []

    for entry in feed.entries[:max_items]:
        title = entry.title.lower()
        score = 0
        if any(kw in title for kw in excluded_keywords):
            continue
        if any(kw in title for kw in china_keywords):
            score += 1
        if any(kw in title for kw in important_keywords):
            score += 2
        if any(kw in title for kw in positive_modifiers):
            score += 1
        articles.append((score, f"• {entry.title.strip()} ({entry.link.strip()})"))

    articles.sort(reverse=True)
    return [item[1] for item in articles[:top_n]] or ["Keine aktuellen China-Artikel gefunden."]

# === Standard-Nachrichtenfeed (mit China-Filter) ===
def fetch_news(feed_url, max_items=15):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:max_items]:
        content = f"{entry.title} {entry.summary} {entry.link}".lower()
        if any(kw in content for kw in china_keywords):
            if not any(bad in content for bad in excluded_keywords):
                articles.append(f"• {entry.title.strip()} ({entry.link.strip()})")
    return articles or ["Keine aktuellen China-Artikel gefunden."]

# === Substack weiterleiten an normalen Filter ===
def fetch_substack_articles(feed_url):
    return fetch_news(feed_url)

# === NBS-Webscraping ===
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
        return items or ["Keine aktuellen Veröffentlichungen gefunden."]
    except Exception as e:
        return [f"❌ Fehler beim Abrufen der NBS-Daten: {e}"]

# === Börsenindizes (Yahoo Finance) ===
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
            prev_close, last_close = closes[-2], closes[-1]
            change = last_close - prev_close
            change_pct = (change / prev_close) * 100
            direction = "→" if abs(change_pct) < 0.01 else ("↑" if change > 0 else "↓")
            results.append(f"• {name}: {round(last_close, 2)} {direction} ({change_pct:+.2f} %)")
        except Exception as e:
            results.append(f"❌ {name}: Fehler beim Abrufen ({e})")
    return results

# === X-Ticker ===
def fetch_recent_x_posts(account, name, url):
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
