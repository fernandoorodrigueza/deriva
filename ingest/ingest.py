import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "config" / "sources.json"
OUTPUT_FILE = ROOT / "data" / "articles.json"

USER_AGENT = "Deriva/0.1 (+personal reading project)"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )
        f.write("\n")


def fetch_url(url):
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"
        }
    )

    with urlopen(request, timeout=30) as response:
        return response.read()


def strip_html(text):
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_url(url):
    if not url:
        return ""

    url = url.strip()

    url = url.replace("http://", "https://", 1)

    url = url.split("#", 1)[0]

    # Remove common tracking parameters.
    url = re.sub(
        r"([?&])(utm_[^=&]+|fbclid|gclid|mc_cid|mc_eid)=[^&]*",
        "",
        url,
        flags=re.IGNORECASE
    )

    url = url.rstrip("?&")

    return url.rstrip("/")


def article_id(url):
    normalized = normalize_url(url)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def parse_date(value):
    if not value:
        return None

    value = value.strip()

    # RFC 822 / RSS dates.
    try:
        from email.utils import parsedate_to_datetime

        date = parsedate_to_datetime(value)

        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        return date.astimezone(timezone.utc).isoformat()
    except Exception:
        pass

    # ISO dates.
    try:
        value = value.replace("Z", "+00:00")

        date = datetime.fromisoformat(value)

        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        return date.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def text_from_element(element):
    if element is None:
        return ""

    return strip_html(
        "".join(element.itertext())
    )


def first_text(element, paths):
    for path in paths:
        found = element.find(path)

        if found is not None:
            value = text_from_element(found)

            if value:
                return value

    return ""


def find_link(element):
    # RSS
    link = element.find("link")

    if link is not None:
        if link.text and link.text.strip():
            return link.text.strip()

        href = link.attrib.get("href")

        if href:
            return href.strip()

    # Atom
    atom_links = element.findall(
        "{http://www.w3.org/2005/Atom}link"
    )

    for link in atom_links:
        rel = link.attrib.get("rel", "alternate")

        if rel == "alternate":
            href = link.attrib.get("href")

            if href:
                return href.strip()

    return ""


def parse_feed(xml_data):
    root = ET.fromstring(xml_data)

    root_tag = root.tag.lower()

    articles = []

    # RSS
    if root_tag.endswith("rss") or root_tag.endswith("rdf"):
        items = root.findall(".//item")

        for item in items:
            title = first_text(
                item,
                ["title"]
            )

            url = find_link(item)

            description = first_text(
                item,
                ["description", "summary"]
            )

            author = first_text(
                item,
                [
                    "author",
                    "creator",
                    "{http://purl.org/dc/elements/1.1/}creator"
                ]
            )

            published = first_text(
                item,
                [
                    "pubDate",
                    "date",
                    "{http://purl.org/dc/elements/1.1/}date"
                ]
            )

            categories = []

            for category in item.findall("category"):
                value = text_from_element(category)

                if value:
                    categories.append(value)

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "description": description,
                    "author": author,
                    "published_at": parse_date(published),
                    "categories_raw": categories
                }
            )

    # Atom
    elif root_tag.endswith("feed"):
        items = root.findall(
            "{http://www.w3.org/2005/Atom}entry"
        )

        for item in items:
            title = first_text(
                item,
                ["{http://www.w3.org/2005/Atom}title"]
            )

            url = find_link(item)

            description = first_text(
                item,
                [
                    "{http://www.w3.org/2005/Atom}summary",
                    "{http://www.w3.org/2005/Atom}content"
                ]
            )

            author = first_text(
                item,
                [
                    "{http://www.w3.org/2005/Atom}author/"
                    "{http://www.w3.org/2005/Atom}name"
                ]
            )

            published = first_text(
                item,
                [
                    "{http://www.w3.org/2005/Atom}published",
                    "{http://www.w3.org/2005/Atom}updated"
                ]
            )

            categories = []

            for category in item.findall(
                "{http://www.w3.org/2005/Atom}category"
            ):
                value = category.attrib.get("term", "")

                if value:
                    categories.append(value)

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "description": description,
                    "author": author,
                    "published_at": parse_date(published),
                    "categories_raw": categories
                }
            )

    return articles


def clean_article(article, source):
    url = normalize_url(article.get("url", ""))
    title = article.get("title", "").strip()

    if not url or not title:
        return None

    return {
        "id": article_id(url),
        "source": source["id"],
        "source_name": source["name"],
        "title": title,
        "author": article.get("author", "").strip(),
        "url": url,
        "published_at": article.get("published_at"),
        "description": article.get("description", "").strip(),
        "image_url": None,
        "categories": article.get("categories_raw", []),
        "tags": [],
        "reading_time": None,
        "reading_time_source": None,
        "reading_time_estimated": False,
        "access": "unknown",
        "content_type": "unknown",
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def load_existing_articles():
    if not OUTPUT_FILE.exists():
        return []

    try:
        data = load_json(OUTPUT_FILE)

        if isinstance(data, dict):
            return data.get("articles", [])

        return data

    except Exception:
        return []


def ingest_source(source):
    print(f"[{source['name']}]")

    endpoint = source["endpoints"][0]

    print(f"  Descargando: {endpoint}")

    try:
        xml_data = fetch_url(endpoint)

        raw_articles = parse_feed(xml_data)

        articles = []

        for raw_article in raw_articles:
            article = clean_article(
                raw_article,
                source
            )

            if article:
                articles.append(article)

        print(
            f"  OK: {len(articles)} artículos procesados"
        )

        return articles

    except HTTPError as error:
        print(
            f"  ERROR HTTP {error.code}: {error.reason}"
        )

    except URLError as error:
        print(
            f"  ERROR URL: {error.reason}"
        )

    except ET.ParseError as error:
        print(
            f"  ERROR XML: {error}"
        )

    except Exception as error:
        print(
            f"  ERROR: {error}"
        )

    return []


def deduplicate(articles):
    unique = {}

    for article in articles:
        article_id_value = article["id"]

        if article_id_value not in unique:
            unique[article_id_value] = article

    return list(unique.values())


def sort_articles(articles):
    return sorted(
        articles,
        key=lambda article: (
            article.get("published_at") or "",
            article.get("title") or ""
        ),
        reverse=True
    )


def main():
    print("=" * 60)
    print("DERIVA - INGESTA DE ARTÍCULOS")
    print("=" * 60)
    print()

    config = load_json(SOURCES_FILE)

    sources = [
        source
        for source in config["sources"]
        if source.get("enabled", True)
    ]

    existing_articles = load_existing_articles()

    print(
        f"Artículos existentes: {len(existing_articles)}"
    )
    print()

    new_articles = []

    for source in sources:
        articles = ingest_source(source)

        new_articles.extend(articles)

        print()

    combined = existing_articles + new_articles

    combined = deduplicate(combined)
    combined = sort_articles(combined)

    output = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "article_count": len(combined),
        "articles": combined
    }

    save_json(
        OUTPUT_FILE,
        output
    )

    print("=" * 60)
    print(
        f"RESULTADO: {len(combined)} artículos únicos"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
