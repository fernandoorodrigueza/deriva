import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

import requests


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "config" / "sources.json"
DATA_FILE = ROOT / "data" / "articles.json"

USER_AGENT = "Deriva/0.2 (+personal reading project)"

# Categorías maestras de Deriva.
MASTER_CATEGORIES = {
    "literatura": [
        "literature",
        "literatura",
        "book",
        "books",
        "poem",
        "poetry",
        "fiction",
        "novel",
        "novela",
        "cuento",
        "poesia",
        "libro",
        "reading",
        "writer",
        "writing",
        "author",
        "authors",
    ],
    "cine": [
        "film",
        "films",
        "movie",
        "movies",
        "cinema",
        "cine",
        "director",
        "directors",
        "filmmaker",
        "filmmakers",
        "pelicula",
        "peliculas",
        "locarno",
        "screening",
        "mubi",
    ],
    "television": [
        "television",
        "tv",
        "television",
        "series",
        "sitcom",
        "show",
        "streaming",
    ],
    "artes_visuales": [
        "art",
        "arts",
        "visual",
        "painting",
        "photograph",
        "photography",
        "drawing",
        "sculpture",
        "museum",
        "gallery",
        "arte",
        "artes",
        "pintura",
        "fotografia",
        "escultura",
        "museo",
    ],
    "ciencia": [
        "science",
        "physics",
        "biology",
        "math",
        "mathematics",
        "chemistry",
        "cosmology",
        "evolution",
        "genetics",
        "fossil",
        "quantum",
        "ciencia",
        "fisica",
        "biologia",
        "matematica",
        "matematicas",
    ],
    "videojuegos": [
        "video game",
        "video games",
        "videogame",
        "videogames",
        "gaming",
        "game design",
        "videojuego",
        "videojuegos",
    ],
    "musica": [
        "music",
        "musical",
        "song",
        "songs",
        "album",
        "opera",
        "jazz",
        "rock",
        "flamenco",
        "musica",
        "cancion",
        "canciones",
        "album",
        "opera",
    ],
    "filosofia": [
        "philosophy",
        "philosopher",
        "ethics",
        "epistemology",
        "metaphysics",
        "filosofia",
        "filosofo",
        "etica",
    ],
    "historia": [
        "history",
        "historical",
        "archive",
        "archives",
        "medieval",
        "ancient",
        "war",
        "historia",
        "historical",
        "historico",
        "archivo",
    ],
    "cultura": [
        "culture",
        "cultural",
        "anthropology",
        "anthropological",
        "religion",
        "religious",
        "culture",
        "cultura",
        "cultural",
    ],
    "tecnologia": [
        "technology",
        "tech",
        "artificial intelligence",
        "ai",
        "internet",
        "software",
        "computing",
        "digital",
        "technology",
        "tecnologia",
        "inteligencia artificial",
        "algorithms",
    ],
    "sociedad": [
        "society",
        "social",
        "politics",
        "political",
        "economy",
        "economics",
        "education",
        "work",
        "labor",
        "immigration",
        "sociedad",
        "social",
        "politica",
        "economia",
        "trabajo",
        "educacion",
    ],
}


# Tipos de contenido.
CONTENT_TYPES = [
    "essay",
    "review",
    "interview",
    "profile",
    "reportage",
    "criticism",
    "analysis",
    "fiction",
    "poetry",
    "history",
    "explainer",
    "video",
    "podcast",
    "game",
    "list",
    "newsletter",
    "cartoon",
]


def normalize_text(value):
    """Normaliza texto para búsquedas y reglas."""
    if not value:
        return ""

    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )

    value = value.lower()
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_url(url):
    """Elimina tracking y normaliza la URL para deduplicación."""
    if not url:
        return ""

    parts = urlsplit(url.strip())

    query = []

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        key_lower = key.lower()

        if key_lower.startswith("utm_"):
            continue

        if key_lower in {
            "fbclid",
            "gclid",
            "mc_cid",
            "mc_eid",
            "ref",
            "ref_src",
        }:
            continue

        query.append((key, value))

    clean_query = urlencode(query)

    path = parts.path.rstrip("/")

    return urlunsplit(
        (
            "https",
            parts.netloc.lower(),
            path,
            clean_query,
            "",
        )
    )


def make_id(url):
    """ID estable basado en URL canónica."""
    return hashlib.sha256(
        normalize_url(url).encode("utf-8")
    ).hexdigest()


def strip_html(text):
    """Elimina HTML sencillo de descripciones RSS."""
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def first_text(element, paths):
    """Devuelve el primer texto encontrado entre varias rutas XML."""
    for path in paths:
        node = element.find(path)

        if node is not None and node.text:
            return node.text.strip()

    return ""


def get_namespaces(root):
    """Obtiene namespaces declarados en el XML."""
    namespaces = {
        "content": "http://purl.org/rss/1.0/modules/content/",
        "media": "http://search.yahoo.com/mrss/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "atom": "http://www.w3.org/2005/Atom",
    }

    return namespaces


def extract_image(item, namespaces):
    """Intenta encontrar una imagen asociada al artículo."""
    # RSS enclosure
    enclosure = item.find("enclosure")

    if enclosure is not None:
        media_type = enclosure.attrib.get("type", "")

        if media_type.startswith("image/"):
            return enclosure.attrib.get("url")

    # Media RSS
    media_content = item.find("media:content", namespaces)

    if media_content is not None:
        media_type = media_content.attrib.get("type", "")

        if media_type.startswith("image/") or media_content.attrib.get("url"):
            return media_content.attrib.get("url")

    media_thumbnail = item.find("media:thumbnail", namespaces)

    if media_thumbnail is not None:
        return media_thumbnail.attrib.get("url")

    return None


def parse_feed(xml_text):
    """
    Convierte RSS/RDF/Atom en una lista homogénea.
    """
    root = ET.fromstring(xml_text)
    namespaces = get_namespaces(root)

    items = []

    # RSS / RSS 1.0 / RDF
    rss_items = root.findall(".//item")

    if rss_items:
        for item in rss_items:
            title = first_text(
                item,
                ["title"],
            )

            url = first_text(
                item,
                ["link"],
            )

            description = first_text(
                item,
                [
                    "description",
                    "content:encoded",
                ],
            )

            author = first_text(
                item,
                [
                    "author",
                    "dc:creator",
                ],
            )

            published = first_text(
                item,
                [
                    "pubDate",
                    "dc:date",
                ],
            )

            categories = []

            for category in item.findall("category"):
                if category.text:
                    categories.append(category.text.strip())

            image_url = extract_image(
                item,
                namespaces,
            )

            items.append(
                {
                    "title": title,
                    "url": url,
                    "description": strip_html(description),
                    "author": author,
                    "published_at": published,
                    "categories": categories,
                    "image_url": image_url,
                }
            )

        return items

    # Atom
    atom_entries = root.findall(
        ".//atom:entry",
        namespaces,
    )

    for entry in atom_entries:
        title = first_text(
            entry,
            ["{http://www.w3.org/2005/Atom}title"],
        )

        url = ""

        for link in entry.findall(
            "{http://www.w3.org/2005/Atom}link"
        ):
            rel = link.attrib.get("rel", "alternate")

            if rel == "alternate":
                url = link.attrib.get("href", "")
                break

        description = first_text(
            entry,
            [
                "{http://www.w3.org/2005/Atom}summary",
                "{http://www.w3.org/2005/Atom}content",
            ],
        )

        author = ""

        author_node = entry.find(
            "atom:author/atom:name",
            namespaces,
        )

        if author_node is not None and author_node.text:
            author = author_node.text.strip()

        published = first_text(
            entry,
            [
                "{http://www.w3.org/2005/Atom}published",
                "{http://www.w3.org/2005/Atom}updated",
            ],
        )

        categories = []

        for category in entry.findall(
            "atom:category",
            namespaces,
        ):
            term = category.attrib.get("term")

            if term:
                categories.append(term)

        image_url = extract_image(
            entry,
            namespaces,
        )

        items.append(
            {
                "title": title,
                "url": url,
                "description": strip_html(description),
                "author": author,
                "published_at": published,
                "categories": categories,
                "image_url": image_url,
            }
        )

    return items


def classify_content_type(article):
    """
    Clasificación heurística del tipo de contenido.

    Las reglas específicas de fuente tienen prioridad sobre
    las reglas generales.
    """
    source = article.get("source", "")
    title = normalize_text(article.get("title"))
    description = normalize_text(article.get("description"))
    categories = normalize_text(
        " ".join(article.get("categories") or [])
    )
    url = normalize_text(article.get("url"))

    text = " ".join(
        [
            title,
            description,
            categories,
            url,
        ]
    )

    # -----------------------------------------
    # Reglas específicas
    # -----------------------------------------

    if source == "new_yorker":
        if (
            "/podcast/" in url
            or "podcast" in title
            or "podcast" in categories
        ):
            return "podcast"

        if (
            "shuffalo" in text
            or "puzzles" in text
            or "/games/" in url
            or "game" in categories
        ):
            return "game"

        if "cartoon" in text or "cartoons" in text:
            return "cartoon"

        if "newsletter" in text:
            return "newsletter"

    if source == "aeon":
        if (
            "video" in text
            or "/videos/" in url
        ):
            return "video"

    if source == "longreads":
        if (
            "top 5 longreads" in title
            or "reading list" in title
            or "reading list" in description
        ):
            return "list"

    if source == "mubi_notebook":
        if "rushes" in title:
            return "list"

    # -----------------------------------------
    # Reglas generales
    # -----------------------------------------

    if re.search(r"\bpodcasts?\b", text):
        return "podcast"

    if re.search(r"\bnewsletter\b", text):
        return "newsletter"

    if re.search(
        r"\bcartoon\b|\bcartoons\b|\bcomic strip\b|\bcomics\b",
        text,
    ):
        return "cartoon"

    if (
        re.search(r"\b(puzzle|puzzles|game|games)\b", text)
        and (
            "play " in title
            or "crossword" in text
            or "shuffalo" in text
        )
    ):
        return "game"

    if re.search(
        r"\b(reading list|list of|top \d+)\b",
        title,
    ):
        return "list"

    # -----------------------------------------
    # Formatos editoriales
    # -----------------------------------------

    editorial_rules = [
        (
            "interview",
            [
                "interview",
                "entrevista",
                "conversation with",
                "conversacion con",
            ],
        ),
        (
            "review",
            [
                "review",
                "reseña",
                "resena",
            ],
        ),
        (
            "profile",
            [
                "profile",
                "perfil",
                "portrait of",
            ],
        ),
        (
            "reportage",
            [
                "reportage",
                "reportaje",
                "feature",
            ],
        ),
        (
            "essay",
            [
                "essay",
                "ensayo",
            ],
        ),
        (
            "fiction",
            [
                "fiction",
                "ficcion",
                "cuento",
            ],
        ),
        (
            "poetry",
            [
                "poem",
                "poetry",
                "poema",
                "poesia",
            ],
        ),
        (
            "history",
            [
                "history",
                "historia",
                "historical",
                "historico",
            ],
        ),
        (
            "explainer",
            [
                "what is",
                "how does",
                "how do",
                "explained",
                "explanation",
                "que es",
                "como funciona",
            ],
        ),
    ]

    for content_type, keywords in editorial_rules:
        if any(keyword in title for keyword in keywords):
            return content_type

        if any(keyword in categories for keyword in keywords):
            return content_type

    # Si no podemos determinar una forma concreta,
    # lo dejamos como análisis.
    return "analysis"


def classify_categories(article):
    """
    Asigna categorías maestras mediante coincidencias
    de título, descripción y categorías originales.
    """
    title = normalize_text(article.get("title"))
    description = normalize_text(article.get("description"))

    original_categories = normalize_text(
        " ".join(article.get("categories") or [])
    )

    author = normalize_text(article.get("author"))

    text = " ".join(
        [
            title,
            description,
            original_categories,
            author,
        ]
    )

    scores = {
        category: 0
        for category in MASTER_CATEGORIES
    }

    for category, keywords in MASTER_CATEGORIES.items():
        for keyword in keywords:
            keyword = normalize_text(keyword)

            if not keyword:
                continue

            if keyword in text:
                # Frases de varias palabras son una señal
                # ligeramente más fuerte.
                scores[category] += (
                    2 if " " in keyword else 1
                )

    # -----------------------------------------
    # Prioridades por fuente
    # -----------------------------------------

    source = article.get("source")

    if source == "quanta":
        scores["ciencia"] += 5

    if source == "mubi_notebook":
        scores["cine"] += 6

    if source == "public_domain_review":
        scores["historia"] += 2
        scores["artes_visuales"] += 2

    if source == "paris_review":
        scores["literatura"] += 2

    # -----------------------------------------
    # Selección
    # -----------------------------------------

    ranked = sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0]),
    )

    categories = [
        category
        for category, score in ranked
        if score >= 2
    ]

    # Máximo tres categorías para evitar
    # artículos etiquetados como "todo".
    return categories[:3]


def estimate_reading_time(article):
    """
    Estima tiempo de lectura.

    Importante:
    el RSS normalmente no contiene el texto completo,
    por lo que esta estimación NO pretende representar
    la longitud real del artículo.

    La dejamos como estimación de baja confianza.
    """
    if article.get("reading_time"):
        return (
            article["reading_time"],
            article.get(
                "reading_time_source",
                "source",
            ),
            bool(
                article.get(
                    "reading_time_estimated",
                    False,
                )
            ),
        )

    source = article.get("source")

    # Cuando el RSS no da una cifra real,
    # usamos una estimación conservadora por fuente.
    defaults = {
        "new_yorker": 8,
        "jot_down": 10,
        "paris_review": 8,
        "longreads": 12,
        "aeon": 10,
        "quanta": 9,
        "mubi_notebook": 8,
        "public_domain_review": 12,
    }

    minutes = defaults.get(source, 8)

    return (
        minutes,
        "source_default_estimate",
        True,
    )


def normalize_article(article):
    """
    Completa y normaliza un artículo existente o nuevo.
    """
    article = dict(article)

    article["url"] = normalize_url(
        article.get("url", "")
    )

    article["id"] = make_id(
        article["url"]
    )

    if not article.get("categories"):
        article["categories"] = []

    if not article.get("tags"):
        article["tags"] = []

    # Si no existe imagen nueva, conservamos la anterior.
    if not article.get("image_url"):
        article["image_url"] = None

    article["content_type"] = classify_content_type(
        article
    )

    article["categories"] = classify_categories(
        article
    )

    (
        reading_time,
        reading_time_source,
        reading_time_estimated,
    ) = estimate_reading_time(article)

    article["reading_time"] = reading_time
    article["reading_time_source"] = (
        reading_time_source
    )
    article["reading_time_estimated"] = (
        reading_time_estimated
    )

    if not article.get("access"):
        article["access"] = "unknown"

    return article


def fetch_source(source):
    """
    Descarga y procesa un feed.
    Si una fuente falla, no detiene todo el proceso.
    """
    name = source["name"]
    endpoints = source.get("endpoints", [])

    for endpoint in endpoints:
        try:
            print(
                f"[{name}] Descargando {endpoint}"
            )

            response = requests.get(
                endpoint,
                headers={
                    "User-Agent": USER_AGENT,
                },
                timeout=30,
            )

            response.raise_for_status()

            items = parse_feed(
                response.text
            )

            print(
                f"[{name}] {len(items)} elementos encontrados"
            )

            articles = []

            for item in items:
                url = normalize_url(
                    item.get("url", "")
                )

                if not url:
                    continue

                article = {
                    "id": make_id(url),
                    "source": name,
                    "source_name": source.get(
                        "display_name",
                        name,
                    ),
                    "title": item.get(
                        "title",
                        "",
                    ),
                    "author": item.get(
                        "author",
                        "",
                    ),
                    "url": url,
                    "published_at": item.get(
                        "published_at",
                        "",
                    ),
                    "description": item.get(
                        "description",
                        "",
                    ),
                    "image_url": item.get(
                        "image_url"
                    ),
                    "categories": item.get(
                        "categories",
                        [],
                    ),
                    "tags": [],
                    "reading_time": None,
                    "reading_time_source": None,
                    "reading_time_estimated": False,
                    "access": "unknown",
                    "content_type": "unknown",
                    "fetched_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }

                article = normalize_article(
                    article
                )

                articles.append(article)

            return articles

        except Exception as error:
            print(
                f"[{name}] Error con {endpoint}: "
                f"{error}"
            )

    print(
        f"[{name}] No se pudo procesar ninguna URL."
    )

    return []


def load_existing():
    """Carga artículos existentes."""
    if not DATA_FILE.exists():
        return []

    try:
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        articles = data.get(
            "articles",
            [],
        )

        # También normalizamos los artículos
        # antiguos.
        return [
            normalize_article(article)
            for article in articles
        ]

    except Exception as error:
        print(
            f"No se pudo leer {DATA_FILE}: {error}"
        )
        return []


def save_articles(articles):
    """Guarda el archivo final."""
    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Deduplicación final por ID.
    unique = {}

    for article in articles:
        article = normalize_article(article)

        if not article.get("id"):
            continue

        unique[article["id"]] = article

    articles = list(
        unique.values()
    )

    # Más recientes primero.
    articles.sort(
        key=lambda article: (
            article.get(
                "published_at",
                "",
            )
            or ""
        ),
        reverse=True,
    )

    output = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "article_count": len(articles),
        "articles": articles,
    }

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Guardados {len(articles)} artículos."
    )


def main():
    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        sources = json.load(file)

    existing = load_existing()

    print(
        f"Artículos existentes: "
        f"{len(existing)}"
    )

    fetched = []

    for source in sources:
        articles = fetch_source(source)
        fetched.extend(articles)

    print(
        f"Artículos nuevos encontrados: "
        f"{len(fetched)}"
    )

    all_articles = existing + fetched

    save_articles(all_articles)

    # Estadísticas útiles para GitHub Actions.
    final_articles = load_existing()

    content_types = {}

    for article in final_articles:
        content_type = article.get(
            "content_type",
            "unknown",
        )

        content_types[content_type] = (
            content_types.get(
                content_type,
                0,
            )
            + 1
        )

    categories = {}

    for article in final_articles:
        for category in article.get(
            "categories",
            [],
        ):
            categories[category] = (
                categories.get(
                    category,
                    0,
                )
                + 1
            )

    print("\nTipos de contenido:")

    for content_type, count in sorted(
        content_types.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        print(
            f"  {content_type}: {count}"
        )

    print("\nCategorías:")

    for category, count in sorted(
        categories.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        print(
            f"  {category}: {count}"
        )


if __name__ == "__main__":
    main()
