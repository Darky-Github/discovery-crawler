from bs4 import BeautifulSoup
import re

CHUNK_SIZE = 1800

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text, size=CHUNK_SIZE):
    chunks = []

    for i in range(0, len(text), size):
        chunk = text[i:i + size].strip()

        if len(chunk) > 120:
            chunks.append(chunk)

    return chunks

def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "footer",
        "nav",
        "aside",
        "form"
    ]):
        tag.decompose()

    title = ""

    if soup.title:
        title = clean_text(soup.title.text)

    text = soup.get_text(" ", strip=True)

    text = clean_text(text)

    text = text[:15000]

    chunks = chunk_text(text)

    links = []

    for a in soup.find_all("a"):
        href = a.get("href")

        if href:
            links.append(href)

    return {
        "title": title,
        "chunks": chunks,
        "links": links
    }
