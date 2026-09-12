import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "config" / "sources.json"


def load_sources():
    with SOURCES_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        source
        for source in data["sources"]
        if source.get("enabled", True)
    ]


def fetch_feed(url):
    request = Request(
        url,
        headers={
            "User-Agent": "Deriva/0.1 (+personal reading project)"
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            body = response.read()

        return {
            "ok": True,
            "status": status,
            "content_type": content_type,
            "body": body,
            "error": None,
        }

    except HTTPError as e:
        return {
            "ok": False,
            "status": e.code,
            "content_type": e.headers.get("Content-Type", ""),
            "body": b"",
            "error": f"HTTP {e.code}: {e.reason}",
        }

    except URLError as e:
        return {
            "ok": False,
            "status": None,
            "content_type": "",
            "body": b"",
            "error": f"URL error: {e.reason}",
        }

    except Exception as e:
        return {
            "ok": False,
            "status": None,
            "content_type": "",
            "body": b"",
            "error": str(e),
        }


def parse_feed(body):
    root = ET.fromstring(body)

    tag = root.tag.lower()

    if tag.endswith("rss") or tag.endswith("rdf"):
        items = root.findall(".//item")
    elif tag.endswith("feed"):
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    else:
        items = root.findall(".//item")

    return len(items)


def test_source(source):
    name = source["name"]
    endpoints = source.get("endpoints", [])
    fallback_endpoints = source.get("fallback_endpoints", [])

    all_endpoints = endpoints + fallback_endpoints

    for url in all_endpoints:
        print(f"  Probando: {url}")

        result = fetch_feed(url)

        if not result["ok"]:
            print(f"  ERROR: {result['error']}")
            continue

        try:
            item_count = parse_feed(result["body"])

            print(
                f"  PASS: HTTP {result['status']} | "
                f"{item_count} entradas | "
                f"{result['content_type']}"
            )

            return True

        except ET.ParseError as e:
            print(f"  ERROR XML: {e}")

    print(f"  FAIL: {name} no tiene un endpoint RSS funcional.")
    return False


def main():
    print("=" * 60)
    print("DERIVA - PRUEBA DE FUENTES")
    print("=" * 60)
    print()

    sources = load_sources()

    passed = 0
    failed = 0

    for source in sources:
        print(f"[{source['name']}]")

        if test_source(source):
            passed += 1
        else:
            failed += 1

        print()

    print("=" * 60)
    print(f"RESULTADO: {passed}/{len(sources)} fuentes funcionando")
    print("=" * 60)

    if failed:
        print(f"FALLAS: {failed}")
        sys.exit(1)

    print("TODAS LAS FUENTES FUNCIONAN.")
    sys.exit(0)


if __name__ == "__main__":
    main()
