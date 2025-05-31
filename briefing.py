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
    # 📺 Anglo-American Media
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "New York Post": "https://nypost.com/feed/",
    "Bloomberg": "https://www.bloomberg.com/feed/podcast/next_china.xml",
    "Financial Times": "https://www.ft.com/?format=rss",
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=china&post_type=best",
    "The Guardian": "https://www.theguardian.com/world/china/rss",
    "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar",

    # 📰 Deutsche Medien
    "Welt": "https://www.welt.de/feeds/section/wirtschaft.rss",
    "FAZ": "https://www.faz.net/rss/aktuell/",
    "Frankfurter Rundschau": "https://www.fr.de/rss.xml",
    "Tagesspiegel": "https://www.tagesspiegel.de/rss.xml",
    "Der Standard": "https://www.derstandard.at/rss",

    # 🧠 Think Tanks & Institute
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
# 📬 Substack-Briefings
# ===============================
feeds_substack = {
    "Sinocism – Bill Bishop": "https://sinocism.com/feed",
    "ChinaTalk – Jordan Schneider": "https://chinatalk.substack.com/feed",
    "Pekingology": "https://pekingnology.substack.com/feed",
    "The Rare Earth Observer": "https://treo.substack.com/feed",  # China-Filter nötig
    "Baiguan": "https://www.baiguan.news/feed",
    "Bert’s Newsletter": "https://berthofman.substack.com/feed",
    "Hong Kong Money Never Sleeps": "https://moneyhk.substack.com/feed",
    "Tracking People’s Daily": "https://trackingpeoplesdaily.substack.com/feed",
    "Interconnected": "https://interconnect.substack.com/feed",  # China-Filter nötig
    "Ginger River Review": "https://www.gingerriver.com/feed",
    "The East is Read": "https://www.eastisread.com/feed",
    "Inside China – Fred Gao": "https://www.fredgao.com/feed",
    "China Business Spotlight": "https://chinabusinessspotlight.substack.com/feed",
    "ChinAI Newsletter": "https://chinai.substack.com/feed",
    "Tech Buzz China Insider": "https://techbuzzchina.substack.com/feed",
    "Sinical China": "https://www.sinicalchina.com/feed",
    "Observing China": "https://www.observingchina.org.uk/feed"
}

# ===============================
# 📰 SCMP & Yicai (mit Relevanz-Scoring)
# ===============================
feeds_scmp_yicai = {
    "SCMP": "https://www.scmp.com/rss/91/feed",
    "Yicai Global": "https://www.yicaiglobal.com/rss/news"
}


def fetch_news(feed_url, max_items=10):
    feed = feedparser.parse(feed_url)
    china_keywords = [
        "china", "beijing", "shanghai", "hong kong", "xi jinping", "taiwan", "pla",
        "cpc", "communist party", "prc", "belt and road", "huawei", "byd", "tiktok",
        "peking", "hongkong", "kpch", "volksbefreiungsarmee", "seidenstraße", "alibaba"
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


def fetch_substack_articles(feed_url, max_items=5, filter_china=False):
    feed = feedparser.parse(feed_url)
    china_keywords = [
        "china", "beijing", "xi", "ccp", "taiwan", "hong kong", "shanghai", "cpc", "prc", "chinese"
    ]
    articles = []
    for entry in feed.entries[:max_items]:
        title = entry.title
        if filter_china:
            if not any(kw in title.lower() for kw in china_keywords):
                continue
        articles.append(f"• {title} ({entry.link})")
    return articles


def fetch_ranked_articles(feed_url, max_items=10, top_n=5):
    feed = feedparser.parse(feed_url)
    important_keywords = [
        "xi", "premier li", "taiwan", "nbs", "gdp", "exports", "export", "imports", "sanctions",
        "policy", "housing", "real estate", "property", "home prices", "house prices", "house market",
        "economy", "tech", "semiconductors", "ai", "tariffs"
    ]
    positive_modifiers = [
        "explainer", "analysis", "opinion", "data", "policy", "official", "market", "feature"
    ]
    negative_keywords = [
        "celebrity", "video", "weird", "love", "dog", "bizarre", "tourist", "fashion", "movie", "series"
    ]
    scored_articles = []
    for entry in feed.entries[:max_items]:
        title = entry.title.lower()
        score = 0
        if any(kw in title for kw in important_keywords):
            score += 2
        if any(mod in title for mod in positive_modifiers):
            score += 1
        if any(bad in title for bad in negative_keywords):
            score -= 2
        if len(title.split()) <= 4:
            score -= 1
        scored_articles.append((score, f"• {entry.title} ({entry.link})"))
    scored_articles.sort(reverse=True, key=lambda x: x[0])
    return [item[1] for item in scored_articles[:top_n]]


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
    headers = {"User-Agent": "Mozilla/5.0"}
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
            formatted = f"• {name}: {round(last_close, 2)} {symbol_arrow} ({change_pct:+.2f} %)"
            results.append(formatted)
        except Exception as e:
            results.append(f"❌ {name}: Fehler beim Abrufen ({e})")
    return results


def generate_briefing(feeds):
    date_str = datetime.now().strftime("%d. %B %Y")
    briefing = [f"Guten Morgen, Hado!\n\n🗓️ {date_str}\n\n"]
    briefing.append("📬 Dies ist dein tägliches China-Briefing.\n")

    # Börsendaten
    briefing.append("\n## 📊 Börsenindizes China (08:00 Uhr MESZ)")
    briefing.extend(fetch_index_data())

    # Statistikamt
    briefing.append("\n## 📈 NBS – Nationale Statistikdaten")
    briefing.extend(fetch_latest_nbs_data())

    # Klassische Medien
    for source, url in feeds.items():
        briefing.append(f"\n## {source}")
        try:
            articles = fetch_news(url)
            briefing.extend(articles or ["Keine aktuellen Artikel gefunden."])
        except Exception as e:
            briefing.append(f"Fehler beim Abrufen: {e}")

    # Substack
    briefing.append("\n## 📬 China-Fokus: Substack-Briefings")
    for source, url in feeds_substack.items():
        briefing.append(f"\n### {source}")
        try:
            if "Rare Earth Observer" in source or "Interconnected" in source:
                articles = fetch_substack_articles(url, filter_china=True)
            else:
                articles = fetch_substack_articles(url)
            briefing.extend(articles or ["Keine aktuellen Artikel gefunden."])
        except Exception as e:
            briefing.append(f"Fehler beim Abrufen: {e}")

    # SCMP/Yicai
    briefing.append("\n## SCMP – Top-Themen")
    briefing.extend(fetch_ranked_articles(feeds_scmp_yicai["SCMP"]) or ["Keine relevanten Artikel gefunden."])

    briefing.append("\n## Yicai Global – Top-Themen")
    briefing.extend(fetch_ranked_articles(feeds_scmp_yicai["Yicai Global"]) or ["Keine relevanten Artikel gefunden."])

    briefing.append("\nEinen erfolgreichen Tag! 🌟")
    return "\n".join(briefing)


# ✉️ E-Mail erzeugen & senden
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
