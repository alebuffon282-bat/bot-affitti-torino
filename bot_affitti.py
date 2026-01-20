import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import json

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

ZONES = ["Santa Rita", "San Paolo", "Cit Turin", "Crocetta", "Cenisia"]
MAX_PRICE = 600

SEEN_FILE = "seen_ads.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_email(ads):
    if not ads:
        return

    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = EMAIL
    msg["Subject"] = "Nuovi bilocali in affitto a Torino"

    body = ""
    for ad in ads:
        body += f"{ad['title']}\n{ad['price']}\n{ad['link']}\n\n"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)

def search_subito():
    results = []
    url = "https://www.subito.it/annunci-piemonte/affitto/appartamenti/torino/"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")

    for ad in soup.select("a.SmallCard-module_link__hOkzY"):
        title = ad.get_text(strip=True)
        link = "https://www.subito.it" + ad.get("href", "")
        text = title.lower()

        if any(z.lower() in text for z in ZONES) and "bilocale" in text:
            results.append({
                "id": link,
                "title": title,
                "price": "",
                "link": link
            })
    return results

def main():
    seen = load_seen()
    new_ads = []

    for ad in search_subito():
        if ad["id"] not in seen:
            seen.add(ad["id"])
            new_ads.append(ad)

    # EMAIL DI TEST FORZATA SE NON CI SONO ANNUNCI
    if not new_ads:
        new_ads.append({
            "title": "EMAIL DI TEST - Bot Affitti Torino",
            "price": "Test riuscito",
            "link": "Il bot funziona correttamente"
        })

    send_email(new_ads)
    save_seen(seen)


if __name__ == "__main__":
    main()
