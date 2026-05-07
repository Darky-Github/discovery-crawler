import requests
from collections import deque
import time
import re
from urllib.parse import urljoin, urlparse, urlunparse
from datetime import datetime
import parser

HEADERS = {
    "User-Agent": "SEEgleBot/1.0"
}

seed_urls = [
    "https://darky-github.github.io/seed_urls_for_crawlers"
]

queue = deque([(url, 0) for url in seed_urls])

MAX_DEPTH = 3
MAX_PAGES = 50

seen = set()

INGESTION_ENDPOINT = "https://YOUR_WORKER_URL/ingest"


def normalize_url(url):
    parsed = urlparse(url)
    return urlunparse(parsed._replace(fragment="", query="")).rstrip("/")


def tokenize(text):
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    return words


def send_to_worker(doc):
    try:
        requests.post(
            INGESTION_ENDPOINT,
            json=doc,
            timeout=10
        )
    except Exception as e:
        print("Ingest failed:", e)


def crawl():
    count = 0

    while queue and count < MAX_PAGES:
        url, depth = queue.popleft()
        url = normalize_url(url)

        if url in seen or depth > MAX_DEPTH:
            continue

        seen.add(url)

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
        except:
            continue

        if r.status_code != 200:
            continue

        data = parser.parse(r.text)

        doc = {
            "id": url,
            "url": url,
            "title": data.get("title", ""),
            "text": data.get("text", ""),
            "timestamp": datetime.utcnow().isoformat()
        }

        send_to_worker(doc)

        count += 1

        for link in data["links"]:
            if not link:
                continue

            full = normalize_url(urljoin(url, link))

            if full.startswith("http") and full not in seen:
                queue.append((full, depth + 1))

    print("Crawl complete")


if __name__ == "__main__":
    crawl()
