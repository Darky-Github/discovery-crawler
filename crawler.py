import requests
import time
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
import parser
import os

HEADERS = {"User-Agent": "SEEgleBot/1.0"}

seed_urls = [
    "https://darky-github.github.io/seed_urls_for_crawlers"
]

queue = deque([(u, 0) for u in seed_urls])
seen = set()

MAX_DEPTH = 3
MAX_PAGES = 50

WORKER_URL = os.getenv("WORKER_URL")
INGEST_SECRET = os.getenv("SEEGLE_INGEST_SECRET")


def normalize(url):
    p = urlparse(url)
    return urlunparse(p._replace(fragment="", query="")).rstrip("/")


def send(data):
    try:
        requests.post(
            WORKER_URL,
            json=data,
            headers={"x-seegle-secret": INGEST_SECRET},
            timeout=10
        )
    except:
        pass


def crawl():
    count = 0

    while queue and count < MAX_PAGES:
        url, depth = queue.popleft()
        url = normalize(url)

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

        send({
            "url": url,
            "title": data["title"],
            "text": data["text"]
        })

        count += 1

        for link in data["links"]:
            full = normalize(urljoin(url, link))
            if full.startswith("http"):
                queue.append((full, depth + 1))

        time.sleep(0.5)


if __name__ == "__main__":
    crawl()
