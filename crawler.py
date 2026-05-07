import requests
from collections import deque
import time
import re
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "SEEgleBot/1.0"}

seed_urls = ["https://darky-github.github.io/seed_urls_for_crawlers"]

queue = deque([(u, 0) for u in seed_urls])
seen = set()

MAX_DEPTH = 3
MAX_PAGES = 50

WORKER_ENDPOINT = "https://YOUR-WORKER.workers.dev/ingest"


def normalize(url):
    p = urlparse(url)
    return urlunparse(p._replace(fragment="", query="")).rstrip("/")


def extract(html):
    soup = BeautifulSoup(html, "html.parser")

    for t in soup(["script", "style"]):
        t.decompose()

    text = soup.get_text(" ", strip=True)[:6000]

    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            links.append(href)

    title = soup.title.text.strip() if soup.title else ""

    return title, text, links


def send_to_worker(payload):
    try:
        requests.post(WORKER_ENDPOINT, json=payload, timeout=10)
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

        title, text, links = extract(r.text)

        send_to_worker({
            "url": url,
            "title": title,
            "text": text
        })

        count += 1

        for l in links:
            full = normalize(urljoin(url, l))
            if full.startswith("http"):
                queue.append((full, depth + 1))

        time.sleep(0.5)


if __name__ == "__main__":
    crawl()
