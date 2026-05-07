from bs4 import BeautifulSoup

def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.text.strip() if soup.title else ""

    text = soup.get_text(" ", strip=True)
    text = text[:6000]

    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            links.append(href)

    return {
        "title": title,
        "text": text,
        "links": links
    }
