import requests
import time
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
import parser
import os

HEADERS = {
    "User-Agent": "SEEgleBot/2.0 (DistributedDiscoveryCrawler)"
}

seed_urls = [
    "https://darky-github.github.io/seed_urls_for_crawlers"
]

queue = deque([(u, 0) for u in seed_urls])
queued = set(seed_urls)

MAX_DEPTH = 3
MAX_PAGES = 30

WORKER_URL = os.getenv("WORKER_URL")
INGEST_SECRET = os.getenv("SEEGLE_INGEST_SECRET")


def normalize(url):
    p = urlparse(url)

    return urlunparse(
        p._replace(
            fragment="",
            query=""
        )
    ).rstrip("/")


def send_to_worker(payload, url):
    if not WORKER_URL or not INGEST_SECRET:
        print("[CONFIG ERROR] Missing WORKER_URL or SEEGLE_INGEST_SECRET")
        return False

    try:
        print(f"[INGEST] Sending → {url}")

        r = requests.post(
            WORKER_URL + "/ingest",
            json=payload,
            headers={
                "x-seegle-secret": INGEST_SECRET,
                "Content-Type": "application/json"
            },
            timeout=20
        )

        print(f"[INGEST] Status {r.status_code} ← {url}")

        try:
            data = r.json()

            if data.get("skipped"):
                print(f"[DEDUPE] Already indexed → {url}")
                return False

        except:
            pass

        return True

    except Exception as e:
        print(f"[INGEST ERROR] {url} → {e}")
        return False


def crawl():
    count = 0

    while queue and count < MAX_PAGES:
        print("\n" + "-" * 60)
        print(f"[QUEUE] Size: {len(queue)} | Crawled: {count}")

        url, depth = queue.popleft()
        url = normalize(url)

        print(f"[CURRENT] {url} (depth={depth})")

        if depth > MAX_DEPTH:
            print("[SKIP] Max depth reached")
            continue

        print("[FETCH] Requesting page...")

        try:
            r = requests.get(
                url,
                headers=HEADERS,
                timeout=15
            )

        except Exception as e:
            print(f"[FETCH ERROR] {url} → {e}")
            continue

        print(f"[FETCH] Status: {r.status_code}")

        if r.status_code != 200:
            print("[SKIP] Non-200 response")
            continue

        data = parser.parse(r.text)

        print(f"[PARSE] title='{data.get('title', '')[:60]}'")
        print(f"[PARSE] chunks={len(data.get('chunks', []))}")
        print(f"[PARSE] links={len(data.get('links', []))}")

        domain = urlparse(url).netloc

        payload = {
            "url": url,
            "title": data.get("title", ""),
            "chunks": data.get("chunks", []),
            "domain": domain,
            "content_length": len(" ".join(data.get("chunks", [])))
        }

        indexed = send_to_worker(payload, url)

        if indexed:
            count += 1

        print("[CRAWL] Extracting links...")

        for link in data.get("links", []):
            if not link:
                continue

            if link.startswith("#"):
                continue

            if "javascript:" in link:
                continue

            if "mailto:" in link:
                continue

            full = normalize(urljoin(url, link))

            if not full.startswith("http"):
                continue

            if full in queued:
                continue

            queued.add(full)

            queue.append((full, depth + 1))

            print(f"[QUEUE ADD] {full}")

        time.sleep(0.5)

    print("\nSEEgle distributed crawl complete")


if __name__ == "__main__":
    crawl()
