import requests
import time
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
import parser
import os

HEADERS = {
    "User-Agent": "SEEgleBot/1.0 (DiscoveryCrawler)"
}

seed_urls = [
    "https://darky-github.github.io/seed_urls_for_crawlers"
]

queue = deque([(u, 0) for u in seed_urls])
seen = set()

MAX_DEPTH = 3
MAX_PAGES = 30

WORKER_URL = os.getenv("WORKER_URL")
INGEST_SECRET = os.getenv("SEEGLE_INGEST_SECRET")


def normalize(url):
    p = urlparse(url)
    return urlunparse(p._replace(fragment="", query="")).rstrip("/")


def send_to_worker(payload, url):
    if not WORKER_URL or not INGEST_SECRET:
        print("[CONFIG ERROR] Missing WORKER_URL or SEEGLE_INGEST_SECRET")
        return

    try:
        print(f"[INGEST] Sending → {url}")

        r = requests.post(
            WORKER_URL + "/ingest",
            json=payload,
            headers={
                "x-seegle-secret": INGEST_SECRET,
                "Content-Type": "application/json"
            },
            timeout=10
        )

        print(f"[INGEST] Status {r.status_code} ← {url}")

    except Exception as e:
        print(f"[INGEST ERROR] {url} → {e}")


def crawl():
    count = 0

    while queue and count < MAX_PAGES:
        print("\n" + "-" * 60)
        print(f"[QUEUE] Size: {len(queue)} | Crawled: {count}")

        url, depth = queue.popleft()
        url = normalize(url)

        print(f"[CURRENT] {url} (depth={depth})")

        if url in seen:
            print("[SKIP] Already seen")
            continue

        if depth > MAX_DEPTH:
            print("[SKIP] Max depth reached")
            continue

        seen.add(url)

        print(f"[FETCH] Requesting page...")

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
        except Exception as e:
            print(f"[FETCH ERROR] {url} → {e}")
            continue

        print(f"[FETCH] Status: {r.status_code}")

        if r.status_code != 200:
            print("[SKIP] Non-200 response")
            continue

        data = parser.parse(r.text)

        print(f"[PARSE] title='{data.get('title','')[:40]}'")
        print(f"[PARSE] links={len(data.get('links', []))}")

        send_to_worker({
            "url": url,
            "title": data.get("title", ""),
            "text": data.get("text", "")
        }, url)

        count += 1

        print("[CRAWL] Extracting links...")

        for link in data.get("links", []):
            if not link:
                continue

            if link.startswith("#"):
                print("[SKIP LINK] fragment")
                continue

            if "javascript:" in link or "mailto:" in link:
                print("[SKIP LINK] unsafe scheme")
                continue

            full = normalize(urljoin(url, link))

            if not full.startswith("http"):
                continue

            if full in seen:
                print(f"[SKIP LINK] already seen → {full}")
                continue

            queue.append((full, depth + 1))
            print(f"[QUEUE ADD] {full}")

        time.sleep(0.4)

    print("\nSEEgle crawl complete")


if __name__ == "__main__":
    crawl()
