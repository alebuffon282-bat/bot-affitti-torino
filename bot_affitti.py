import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

ZONES = ["Santa Rita", "San Paolo", "Cit Turin", "Crocetta", "Cenisia"]
MAX_PRICE = 600

SEEN_FILE = "seen_ads.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ------------------ UTIL ------------------

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
        body += (
            f"{ad['title']}\n"
            f"{ad['price']}\n"
            f"{ad['source']}\n"
            f"{ad['link']}\n\n"
        )

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)

# ------------------ SUBITO ------------------

def search_subito():
    results = []
    url = "https://www.subito.it/annunci-piemonte/affitto/appartamenti/torino/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for ad in soup.select("a.SmallCard-module_link__hOkzY"):
        title = ad.get_text(strip=True)
        link = "https://www.subito.it" + ad.get("href", "")
        text = title.lower()

        if "bilocale" in text and any(z.lower() in text for z in ZONES):
            results.append({
                "id": link,
                "title": title,
                "price": "Prezzo da verificare",
                "link": link,
                "source": "Subito.it"
            })

    return results

# ------------------ IMMOBILIARE ------------------

def search_immobiliare():
    results = []
    url = (
        "https://www.immobiliare.it/affitto-bilocali/torino/"
        "?prezzoMassimo=600&tipoProprieta=privato"
    )
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for ad in soup.select("a.in-card__title"):
        title = ad.get_text(strip=True)
        link = ad.get("href", "")
        text = title.lower()

        if any(z.lower() in text for z in ZONES):
            results.append({
                "id": link,
                "title": title,
                "price": "≤ 600 €",
                "link": link,
                "source": "Immobiliare.it"
            })

    return results

# ------------------ IDEALISTA ------------------

def search_idealista():
    results = []
    url = (
        "https://www.idealista.it/affitto-case/torino/"
        "con-prezzo_600,stanze-2/"
    )

    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for ad in soup.select("article.item"):
        title_tag = ad.select_one("a.item-link")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = "https://www.idealista.it" + title_tag.get("href", "")
        text = title.lower()

        if any(z.lower() in text for z in ZONES):
            results.append({
                "id": link,
                "title": title,
                "price": "≤ 600 €",
                "link": link,
                "source": "Idealista"
            })

    return results

# ------------------ MAIN ------------------

def main():
    seen = load_seen()
    new_ads = []

    all_ads = (
        search_subito()
        + search_immobiliare()
        + search_idealista()
    )

    for ad in all_ads:
        if ad["id"] not in seen:
            seen.add(ad["id"])
            new_ads.append(ad)

    send_email(new_ads)
    save_seen(seen)

if __name__ == "__main__":
    main()

