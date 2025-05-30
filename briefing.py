import os
import smtplib
import feedparser
from datetime import datetime
from email.mime.text import MIMEText

# CONFIG-Secret laden
config = os.getenv("CONFIG")
pairs = config.split(";")
config_dict = dict(pair.split("=", 1) for pair in pairs)

# Mail-Zugangsdaten
openai_api_key = config_dict["OPENAI_API_KEY"]  # Noch nicht genutzt, später für Zusammenfassungen
email_host = config_dict["EMAIL_HOST"]
email_port = int(config_dict["EMAIL_PORT"])
email_user = config_dict["EMAIL_USER"]
email_password = config_dict["EMAIL_PASSWORD"]
email_to = config_dict["EMAIL_TO"]

# RSS-Feeds
feeds = {
    "Wall Street Journal": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "New York Post": "https://nypost.com/feed/",
    "Bloomberg": "https://www.bloomberg.com/feed/podcast/next_china.xml",
    "Financial Times": "https://www.ft.com/?format=rss",
    "Reuters": "https://www.reutersagency.com/feed/?best-topics=china&post_type=best",
    "The Guardian": "https://www.theguardian.com/world/china/rss",
    "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar"
}

def fetch_news(feed_url, max_items=3):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:max_items]:
        title = entry.title
        link = entry.link
        articles.append(f"• {title} ({link})")
    return articles

def generate_briefing(feeds):
    date_str = datetime.now().strftime("%d. %B %Y")
    briefing = [f"# 📰 Daily China Briefing – {date_str}\n"]
    for source, url in feeds.items():
        briefing.append(f"## {source}")
        try:
            articles = fetch_news(url)
            if articles:
                briefing.extend(articles)
            else:
                briefing.append("Keine aktuellen Artikel gefunden.")
        except Exception as e:
            briefing.append(f"Fehler beim Abrufen: {e}")
        briefing.append("")
    return "\n".join(briefing)

def send_email(subject, content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = email_user
    msg["To"] = email_to

    with smtplib.SMTP(email_host, email_port) as server:
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)

if __name__ == "__main__":
    content = generate_briefing(feeds)
    send_email("📰 Daily China Briefing", content)
    print("Briefing verschickt.")
