import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import xml.etree.ElementTree as ET

import requests


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "sources.json"
DATA_PATH = BASE_DIR / "data" / "articles.json"


# ============================================================
# CONFIGURACIÓN
# ============================================================

USER_AGENT = (
    "Deriva/0.1 (+https://github.com/fernandoorodrigueza/deriva)"
)

REQUEST_TIMEOUT = 30

MASTER_CATEGORIES = [
    "literatura",
    "cine",
    "television",
    "artes_visuales",
    "ciencia",
    "videojuegos",
    "musica",
    "filosofia",
    "historia",
    "cultura",
    "tecnologia",
    "sociedad",
]


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value):
    if value is None:
        return ""

    value = html.unescape(str(value))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def canonical_url(url):
    if not url:
        return ""

    url = url.strip()

    try:
        parts = urlsplit(url)

        clean = urlunsplit(
            (
                parts.scheme,
                parts.netloc,
                parts.path.rstrip("/"),
                "",
                "",
            )
        )

        return clean

    except Exception:
        return url


def make_id(url):
    normalized = canonical_url(url)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def first_text(element, paths, namespaces):
    """
    Busca el primer elemento que exista entre varios paths.
    """

    for path in paths:
        try:
            node = element.find(
                path,
                namespaces,
            )
        except SyntaxError:
            continue

        if node is not None:
            text = node.text

            if text and text.strip():
                return normalize_text(text)

    return ""


def get_namespaces():
    return {
        "atom": "http://www.w3.org/2005/Atom",
        "dc": "http://purl.org/dc/elements/1.1/",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "media": "http://search.yahoo.com/mrss/",
    }


# ============================================================
# CARGA DE CONFIGURACIÓN
# ============================================================

def load_config():
    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def load_sources():
    """
    sources.json tiene esta estructura:

    {
        "version": "...",
        "defaults": {...},
        "sources": [
            {...}
        ]
    }
    """

    config = load_config()

    sources = config.get(
        "sources",
        [],
    )

    if not isinstance(sources, list):
        raise ValueError(
            "config/sources.json: "
            "'sources' debe ser una lista."
        )

    return sources


def load_defaults():
    config = load_config()

    defaults = config.get(
        "defaults",
        {},
    )

    if not isinstance(defaults, dict):
        return {}

    return defaults


# ============================================================
# ARTÍCULOS EXISTENTES
# ============================================================

def load_existing_articles():
    if not DATA_PATH.exists():
        return []

    try:
        with open(
            DATA_PATH,
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        articles = data.get(
            "articles",
            [],
        )

        if isinstance(articles, list):
            return articles

    except (
        json.JSONDecodeError,
        OSError,
    ) as exc:
        print(
            "Advertencia: no se pudo leer "
            f"articles.json: {exc}"
        )

    return []


# ============================================================
# FECHAS
# ============================================================

def normalize_date(value):
    if not value:
        return None

    value = value.strip()

    # ISO 8601
    try:
        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.isoformat()

    except ValueError:
        pass

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(
                value,
                fmt,
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.isoformat()

        except ValueError:
            continue

    return value


# ============================================================
# ENLACES
# ============================================================

def extract_link(item, namespaces):

    # RSS
    link = first_text(
        item,
        ["link"],
        namespaces,
    )

    if link:
        return link

    # Atom
    for node in item.findall(
        "atom:link",
        namespaces,
    ):
        href = node.attrib.get(
            "href"
        )

        if href:
            rel = node.attrib.get(
                "rel",
                "alternate",
            )

            if rel in (
                "alternate",
                "",
            ):
                return href

    # GUID como último recurso
    guid = first_text(
        item,
        ["guid"],
        namespaces,
    )

    return guid


# ============================================================
# IMÁGENES
# ============================================================

def extract_image(item, namespaces):

    # RSS enclosure
    for enclosure in item.findall(
        "enclosure"
    ):
        url = enclosure.attrib.get(
            "url",
            "",
        )

        media_type = enclosure.attrib.get(
            "type",
            "",
        )

        if url and (
            media_type.startswith("image/")
            or not media_type
        ):
            return url

    # Media RSS
    for media in item.findall(
        "media:content",
        namespaces,
    ):
        url = media.attrib.get(
            "url",
            "",
        )

        media_type = media.attrib.get(
            "type",
            "",
        )

        if url and (
            media_type.startswith("image/")
            or not media_type
        ):
            return url

    # Thumbnail
    for thumbnail in item.findall(
        "media:thumbnail",
        namespaces,
    ):
        url = thumbnail.attrib.get(
            "url",
            "",
        )

        if url:
            return url

    return None


# ============================================================
# CATEGORÍAS ORIGINALES DEL FEED
# ============================================================

def extract_feed_categories(
    item,
    namespaces,
):
    categories = []

    for node in item.findall(
        "category"
    ):
        text = normalize_text(
            node.text
        )

        if text:
            categories.append(text)

    for node in item.findall(
        "media:category",
        namespaces,
    ):
        text = normalize_text(
            node.text
        )

        if text:
            categories.append(text)

    # Eliminar duplicados conservando orden
    result = []
    seen = set()

    for category in categories:
        key = category.lower()

        if key not in seen:
            seen.add(key)
            result.append(category)

    return result


# ============================================================
# CLASIFICACIÓN DE TIPO DE CONTENIDO
# ============================================================

def classify_content_type(
    title,
    description,
    url,
    source_id,
    feed_categories,
):

    text = " ".join(
        [
            title or "",
            description or "",
            url or "",
            " ".join(feed_categories),
        ]
    ).lower()

    path = (
        urlsplit(url).path
        if url
        else ""
    ).lower()

    # --------------------------------------------------------
    # Casos específicos por fuente
    # --------------------------------------------------------

    if source_id == "new_yorker":

        if (
            "/puzzles-and-games-dept/" in path
            or "/games/" in path
            or "puzzles & games" in text
        ):
            return "game"

        if (
            "/podcast/" in path
            or "podcast" in text
        ):
            return "podcast"

        if (
            "/newsletter/" in path
            or "newsletter" in text
        ):
            return "newsletter"

        if (
            "/cartoon/" in path
            or "cartoon" in text
        ):
            return "cartoon"

    if source_id == "aeon":

        if (
            "/videos/" in path
            or "video" in text
        ):
            return "video"

    if source_id == "longreads":

        list_patterns = [
            "top 5 longreads",
            "reading list",
            "best of",
            "weekly",
            "links",
            "recommended reading",
        ]

        if any(
            pattern in text
            for pattern in list_patterns
        ):
            return "list"

    if source_id == "mubi_notebook":

        if (
            "rushes" in text
            or "/rushes" in path
        ):
            return "collection"

    # --------------------------------------------------------
    # Reglas generales
    # --------------------------------------------------------

    if re.search(
        r"\b(podcast|podcasts)\b",
        text,
    ):
        return "podcast"

    if re.search(
        r"\b(video|watch)\b",
        text,
    ) and (
        "video" in path
        or "videos" in path
    ):
        return "video"

    if re.search(
        r"\bnewsletter\b",
        text,
    ):
        return "newsletter"

    if re.search(
        r"\b(game|games|puzzle|puzzles)\b",
        text,
    ) and (
        "game" in path
        or "puzzle" in path
        or "games" in path
    ):
        return "game"

    if re.search(
        r"\b(interview|entrevista|"
        r"conversation with|talks with|"
        r"dialogue with)\b",
        text,
    ):
        return "interview"

    if re.search(
        r"\b(review|reviews|reseña|"
        r"reseñas|book review|"
        r"film review|movie review)\b",
        text,
    ):
        return "review"

    if re.search(
        r"\b(profile|perfil)\b",
        text,
    ):
        return "profile"

    if re.search(
        r"\b(reportage|reportaje|"
        r"investigation|investigación|"
        r"feature)\b",
        text,
    ):
        return "reportage"

    if re.search(
        r"\b(criticism|crítica|critique)\b",
        text,
    ):
        return "criticism"

    if re.search(
        r"\b(analysis|análisis|essay|ensayo)\b",
        text,
    ):
        return "analysis"

    if re.search(
        r"\b(explainer|explained|explicado|"
        r"cómo funciona|how does)\b",
        text,
    ):
        return "explainer"

    if re.search(
        r"\b(poem|poetry|poesía|poema)\b",
        text,
    ):
        return "poetry"

    if re.search(
        r"\b(fiction|ficción|"
        r"short story|cuento)\b",
        text,
    ):
        return "fiction"

    if re.search(
        r"\b(history|historia|historical)\b",
        text,
    ):
        return "history"

    if re.search(
        r"\b(list|lista|top \d+|best of)\b",
        text,
    ):
        return "list"

    return "essay"


# ============================================================
# CLASIFICACIÓN DE CATEGORÍAS
# ============================================================

CATEGORY_KEYWORDS = {

    "literatura": [
        "literature",
        "literary",
        "literary criticism",
        "literary history",
        "novel",
        "novels",
        "novelist",
        "novelists",
        "poetry",
        "poem",
        "poems",
        "poet",
        "poets",
        "book",
        "books",
        "fiction",
        "short story",
        "short stories",
        "prose",
        "memoir",
        "memoirs",
        "essayist",
        "essayists",
        "publisher",
        "publishers",
        "manuscript",
        "manuscripts",
        "literatura",
        "literario",
        "literaria",
        "novela",
        "novelas",
        "novelista",
        "poesía",
        "poema",
        "poemas",
        "poeta",
        "poetas",
        "libro",
        "libros",
        "ficción",
        "cuento",
        "cuentos",
        "prosa",
        "memoria",
        "memorias",
        "ensayista",
        "editorial",
        "manuscrito",
        "manuscritos",
    ],

    "cine": [
        "film",
        "films",
        "film director",
        "film directors",
        "filmmaker",
        "filmmakers",
        "movie",
        "movies",
        "cinema",
        "cinematic",
        "actor",
        "actors",
        "actress",
        "actresses",
        "screenwriter",
        "screenwriting",
        "screenplay",
        "screenplays",
        "film festival",
        "film festivals",
        "cine",
        "película",
        "películas",
        "cineasta",
        "cineastas",
        "actriz",
        "actrices",
        "actor",
        "actores",
        "guionista",
        "guion",
        "guionistas",
        "festival de cine",
    ],

    "television": [
        "television",
        "television series",
        "tv series",
        "showrunner",
        "streaming",
        "televisión",
        "serie de televisión",
        "series de televisión",
        "serie de tv",
        "series de tv",
    ],

    "artes_visuales": [
        "visual art",
        "visual arts",
        "visual artist",
        "visual artists",
        "painting",
        "paintings",
        "painter",
        "painters",
        "photography",
        "photographer",
        "photographers",
        "sculpture",
        "sculptor",
        "sculptors",
        "drawing",
        "drawings",
        "illustration",
        "illustrator",
        "illustrators",
        "printmaking",
        "engraving",
        "engraver",
        "portrait",
        "portraits",
        "museum",
        "museums",
        "gallery",
        "galleries",
        "artwork",
        "artworks",
        "arte visual",
        "artes visuales",
        "artista visual",
        "artistas visuales",
        "pintura",
        "pinturas",
        "pintor",
        "pintores",
        "fotografía",
        "fotógrafo",
        "fotógrafos",
        "escultura",
        "escultor",
        "escultores",
        "dibujo",
        "dibujos",
        "ilustración",
        "ilustrador",
        "ilustradores",
        "grabado",
        "grabados",
        "retrato",
        "retratos",
        "museo",
        "museos",
        "galería",
        "galerías",
        "obra de arte",
        "obras de arte",
    ],

    "ciencia": [
        "science",
        "scientist",
        "scientists",
        "biology",
        "biologist",
        "physics",
        "physicist",
        "chemistry",
        "chemist",
        "astronomy",
        "astronomer",
        "evolution",
        "genetics",
        "geneticist",
        "mathematics",
        "mathematician",
        "math",
        "medicine",
        "medical",
        "neuroscience",
        "neuroscientist",
        "ecology",
        "ecologist",
        "ciencia",
        "científico",
        "científica",
        "científicos",
        "biología",
        "biólogo",
        "física",
        "físico",
        "química",
        "químico",
        "astronomía",
        "astrónomo",
        "evolución",
        "genética",
        "genetista",
        "matemáticas",
        "matemático",
        "medicina",
        "médico",
        "neurociencia",
        "neurocientífico",
        "ecología",
        "ecólogo",
    ],

    "videojuegos": [
        "video game",
        "video games",
        "video-game",
        "video games",
        "gaming",
        "gamer",
        "gamers",
        "videogame",
        "videogames",
        "videojuego",
        "videojuegos",
        "jugador de videojuegos",
    ],

    "musica": [
        "music",
        "musician",
        "musicians",
        "album",
        "albums",
        "song",
        "songs",
        "singer",
        "singers",
        "composer",
        "composers",
        "concert",
        "concerts",
        "jazz",
        "rock",
        "pop music",
        "música",
        "músico",
        "músicos",
        "álbum",
        "álbumes",
        "canción",
        "canciones",
        "cantante",
        "cantantes",
        "compositor",
        "compositores",
        "concierto",
        "conciertos",
    ],

    "filosofia": [
        "philosophy",
        "philosopher",
        "philosophers",
        "ethics",
        "metaphysics",
        "epistemology",
        "existentialism",
        "existential",
        "ontology",
        "philosophical",
        "filosofía",
        "filósofo",
        "filósofos",
        "ética",
        "metafísica",
        "epistemología",
        "existencialismo",
        "existencial",
        "ontología",
        "filosófico",
    ],

    "historia": [
        "history",
        "historical",
        "historian",
        "historians",
        "ancient history",
        "medieval",
        "renaissance",
        "empire",
        "war",
        "wars",
        "revolution",
        "archaeology",
        "archaeological",
        "historia",
        "histórico",
        "histórica",
        "historiador",
        "historiadores",
        "historia antigua",
        "medieval",
        "renacimiento",
        "imperio",
        "guerra",
        "guerras",
        "revolución",
        "arqueología",
        "arqueológico",
    ],

    "tecnologia": [
        "technology",
        "technologies",
        "tech",
        "artificial intelligence",
        "machine learning",
        "ai",
        "software",
        "internet",
        "computer",
        "computing",
        "algorithm",
        "algorithms",
        "robot",
        "robots",
        "digital technology",
        "tecnología",
        "tecnologías",
        "inteligencia artificial",
        "aprendizaje automático",
        "computación",
        "algoritmo",
        "algoritmos",
        "robot",
        "robots",
        "tecnología digital",
    ],

    "sociedad": [
        "society",
        "social",
        "politics",
        "political",
        "economy",
        "economic",
        "business",
        "migration",
        "immigration",
        "labor",
        "work",
        "education",
        "inequality",
        "class",
        "community",
        "communities",
        "sociedad",
        "social",
        "política",
        "político",
        "política",
        "economía",
        "económico",
        "negocios",
        "migración",
        "inmigración",
        "trabajo",
        "laboral",
        "educación",
        "desigualdad",
        "clase social",
        "comunidad",
        "comunidades",
    ],
}



def keyword_matches(text, keyword):
    """
    Busca keywords como palabras o expresiones completas.

    Evita coincidencias accidentales dentro de otras palabras.

    Ejemplo:

        "art" NO coincide con "parenting".
        "film" SÍ coincide con "film director".
        "video game" SÍ coincide con "video game history".
    """

    keyword = keyword.lower().strip()

    if not keyword:
        return False

    escaped = re.escape(keyword)

    pattern = (
        r"(?<!\w)"
        + escaped
        + r"(?!\w)"
    )

    return bool(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
    )


def classify_categories(
    title,
    description,
    source_id,
    feed_categories,
):

    text = " ".join(
        [
            title or "",
            description or "",
            " ".join(feed_categories),
        ]
    ).lower()

    scores = {
        category: 0
        for category in MASTER_CATEGORIES
    }

    # --------------------------------------------------------
    # Puntuación por keywords
    # --------------------------------------------------------

    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if keyword_matches(
                text,
                keyword,
            ):
                scores[category] += 1

    # --------------------------------------------------------
    # Reglas específicas por fuente
    # --------------------------------------------------------

    if source_id == "mubi_notebook":
        scores["cine"] += 3

    if source_id == "quanta":
        scores["ciencia"] += 3

    if source_id == "public_domain_review":
        scores["historia"] += 1
        scores["artes_visuales"] += 1

    # --------------------------------------------------------
    # Ordenar categorías por puntuación
    # --------------------------------------------------------

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    # --------------------------------------------------------
    # Categorías con evidencia fuerte
    #
    # 2 o más coincidencias.
    # --------------------------------------------------------

    strong_categories = [
        category
        for category, score in ranked
        if score >= 2
    ]

    if strong_categories:
        return strong_categories[:3]

    # --------------------------------------------------------
    # Si ninguna categoría tiene evidencia fuerte,
    # conservamos solamente la mejor categoría.
    # --------------------------------------------------------

    best_categories = [
        category
        for category, score in ranked
        if score > 0
    ]

    if best_categories:
        return best_categories[:1]

    # --------------------------------------------------------
    # Si no hay ninguna evidencia:
    # cultura.
    # --------------------------------------------------------

    return ["cultura"]


# ============================================================
# TIEMPO DE LECTURA
# ============================================================

READING_TIME_BY_TYPE = {

    "essay": 8,
    "analysis": 8,
    "reportage": 10,
    "criticism": 7,
    "review": 6,
    "profile": 7,
    "interview": 8,
    "explainer": 7,
    "history": 8,
    "fiction": 8,
    "poetry": 5,
    "collection": 5,
    "list": 4,
    "newsletter": 4,

    "podcast": None,
    "video": None,
    "game": None,
    "cartoon": None,
}


def extract_reading_time(text):

    if not text:
        return None

    patterns = [

        r"(\d+)\s*"
        r"(?:min|mins|minute|minutes)"
        r"\s*(?:read|reading)?",

        r"(\d+)\s*"
        r"(?:minutos?|min)"
        r"\s*(?:de lectura)?",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return int(
                match.group(1)
            )

    return None


def estimate_reading_time(
    title,
    description,
    content_type,
    source_id,
):

    text = " ".join(
        [
            title or "",
            description or "",
        ]
    )

    detected = extract_reading_time(
        text
    )

    if detected is not None:
        return (
            detected,
            "feed",
            False,
        )

    estimated = READING_TIME_BY_TYPE.get(
        content_type
    )

    if estimated is not None:
        return (
            estimated,
            "estimated",
            True,
        )

    source_defaults = {

        "new_yorker": 8,
        "jot_down": 10,
        "paris_review": 8,
        "longreads": 10,
        "aeon": 8,
        "quanta": 7,
        "mubi_notebook": 6,
        "public_domain_review": 8,
    }

    estimated = source_defaults.get(
        source_id,
        8,
    )

    return (
        estimated,
        "estimated",
        True,
    )


# ============================================================
# PARSEO DE UN ITEM RSS/ATOM
# ============================================================

def parse_item(
    item,
    source,
    namespaces,
):

    source_id = source["id"]
    source_name = source["name"]

    title = first_text(
        item,
        ["title"],
        namespaces,
    )

    url = extract_link(
        item,
        namespaces,
    )

    description = first_text(
        item,
        [
            "description",
            "content:encoded",
            "atom:summary",
        ],
        namespaces,
    )

    author = first_text(
        item,
        [
            "author",
            "dc:creator",
            "atom:author/atom:name",
        ],
        namespaces,
    )

    published = first_text(
        item,
        [
            "pubDate",
            "dc:date",
            "published",
            "updated",
            "atom:published",
            "atom:updated",
        ],
        namespaces,
    )

    image_url = extract_image(
        item,
        namespaces,
    )

    feed_categories = (
        extract_feed_categories(
            item,
            namespaces,
        )
    )

    if not title or not url:
        return None

    url = canonical_url(url)

    if not url:
        return None

    title = normalize_text(title)
    description = normalize_text(
        description
    )
    author = normalize_text(
        author
    )

    content_type = classify_content_type(
        title=title,
        description=description,
        url=url,
        source_id=source_id,
        feed_categories=feed_categories,
    )

    categories = classify_categories(
        title=title,
        description=description,
        source_id=source_id,
        feed_categories=feed_categories,
    )

    (
        reading_time,
        reading_source,
        estimated,
    ) = estimate_reading_time(
        title=title,
        description=description,
        content_type=content_type,
        source_id=source_id,
    )

    article = {

        "id": make_id(url),

        "source": source_id,

        "source_name": source_name,

        "title": title,

        "author": author,

        "url": url,

        "published_at": normalize_date(
            published
        ),

        "description": description,

        "image_url": image_url,

        "categories": categories,

        "tags": feed_categories,

        "reading_time": reading_time,

        "reading_time_source": reading_source,

        "reading_time_estimated": estimated,

        "access": "unknown",

        "content_type": content_type,

        "fetched_at": now_iso(),
    }

    return article


# ============================================================
# PARSEO DEL FEED
# ============================================================

def parse_feed(
    xml_content,
    source,
):

    namespaces = get_namespaces()

    root = ET.fromstring(
        xml_content
    )

    items = []

    # RSS / RDF
    rss_items = root.findall(
        ".//item"
    )

    for item in rss_items:

        article = parse_item(
            item,
            source,
            namespaces,
        )

        if article:
            items.append(article)

    # Atom
    if not rss_items:

        atom_items = root.findall(
            ".//atom:entry",
            namespaces,
        )

        for item in atom_items:

            article = parse_item(
                item,
                source,
                namespaces,
            )

            if article:
                items.append(article)

    return items


# ============================================================
# DESCARGA DE UNA FUENTE
# ============================================================

def fetch_source(source):

    name = source["name"]
    source_id = source["id"]

    endpoints = source.get(
        "endpoints",
        [],
    )

    if not endpoints:

        print(
            f"[{source_id}] "
            "No tiene endpoints."
        )

        return []

    print(
        f"\nProcesando: {name}"
    )

    all_articles = []

    headers = {

        "User-Agent": USER_AGENT,

        "Accept": (
            "application/rss+xml, "
            "application/atom+xml, "
            "application/xml, "
            "text/xml, "
            "*/*"
        ),
    }

    for endpoint in endpoints:

        try:

            print(
                f"  Descargando: "
                f"{endpoint}"
            )

            response = requests.get(
                endpoint,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            articles = parse_feed(
                response.content,
                source,
            )

            print(
                f"  Encontrados: "
                f"{len(articles)}"
            )

            all_articles.extend(
                articles
            )

        except requests.RequestException as exc:

            print(
                f"  ERROR HTTP: {exc}"
            )

        except ET.ParseError as exc:

            print(
                f"  ERROR XML: {exc}"
            )

        except Exception as exc:

            print(
                "  ERROR procesando feed: "
                f"{type(exc).__name__}: "
                f"{exc}"
            )

    # Deduplicar dentro de la fuente
    unique = {}

    for article in all_articles:

        unique[
            article["id"]
        ] = article

    return list(
        unique.values()
    )


# ============================================================
# DEDUPLICACIÓN GENERAL
# ============================================================

def deduplicate_articles(
    articles
):

    unique = {}

    for article in articles:

        article_id = article.get(
            "id"
        )

        if not article_id:

            url = article.get(
                "url",
                "",
            )

            if not url:
                continue

            article_id = make_id(
                url
            )

            article["id"] = article_id

        unique[
            article_id
        ] = article

    return list(
        unique.values()
    )


# ============================================================
# ORDEN
# ============================================================

def sort_articles(
    articles
):

    def sort_key(article):

        return article.get(
            "published_at"
        ) or ""

    return sorted(
        articles,
        key=sort_key,
        reverse=True,
    )


# ============================================================
# GUARDAR
# ============================================================

def save_articles(
    articles
):

    DATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {

        "generated_at": now_iso(),

        "article_count": len(
            articles
        ),

        "articles": articles,
    }

    with open(
        DATA_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nGuardado: "
        f"{DATA_PATH}"
    )

    print(
        f"Artículos totales: "
        f"{len(articles)}"
    )


# ============================================================
# ESTADÍSTICAS
# ============================================================

def print_stats(
    articles
):

    print(
        "\n" + "=" * 60
    )

    print(
        "ESTADÍSTICAS"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # Por fuente
    # --------------------------------------------------------

    by_source = {}

    for article in articles:

        source = article.get(
            "source",
            "unknown",
        )

        by_source[source] = (
            by_source.get(
                source,
                0,
            ) + 1
        )

    for source, count in sorted(
        by_source.items()
    ):

        print(
            f"  {source}: {count}"
        )

    # --------------------------------------------------------
    # Por tipo
    # --------------------------------------------------------

    by_type = {}

    for article in articles:

        content_type = article.get(
            "content_type",
            "unknown",
        )

        by_type[
            content_type
        ] = (
            by_type.get(
                content_type,
                0,
            ) + 1
        )

    print(
        "\nPor tipo de contenido:"
    )

    for (
        content_type,
        count,
    ) in sorted(
        by_type.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):

        print(
            f"  {content_type}: {count}"
        )

    # --------------------------------------------------------
    # Por categoría
    # --------------------------------------------------------

    by_category = {}

    for article in articles:

        for category in article.get(
            "categories",
            [],
        ):

            by_category[
                category
            ] = (
                by_category.get(
                    category,
                    0,
                ) + 1
            )

    print(
        "\nPor categoría:"
    )

    for (
        category,
        count,
    ) in sorted(
        by_category.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):

        print(
            f"  {category}: {count}"
        )

    print(
        "=" * 60
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Iniciando ingestión de Deriva..."
    )

    print(
        f"Config: {CONFIG_PATH}"
    )

    print(
        f"Salida: {DATA_PATH}"
    )

    sources = load_sources()

    defaults = load_defaults()

    max_items = defaults.get(
        "max_items_per_run",
        100,
    )

    existing_articles = (
        load_existing_articles()
    )

    print(
        f"\nArtículos existentes: "
        f"{len(existing_articles)}"
    )

    all_new_articles = []

    for source in sources:

        enabled = source.get(
            "enabled",
            defaults.get(
                "enabled",
                True,
            ),
        )

        if not enabled:

            print(
                f"\nOmitiendo "
                f"{source['name']}: "
                "deshabilitada."
            )

            continue

        articles = fetch_source(
            source
        )

        # Limitar cantidad por fuente
        if max_items:
            articles = articles[
                :max_items
            ]

        all_new_articles.extend(
            articles
        )

    print(
        f"\nArtículos nuevos "
        f"encontrados: "
        f"{len(all_new_articles)}"
    )

    # Combinar con artículos previos
    combined = (
        existing_articles
        + all_new_articles
    )

    # Deduplicar
    combined = deduplicate_articles(
        combined
    )

    # Ordenar
    combined = sort_articles(
        combined
    )

    print(
        f"Artículos después de "
        f"deduplicar: "
        f"{len(combined)}"
    )

    save_articles(
        combined
    )

    print_stats(
        combined
    )

    print(
        "\nIngestión terminada "
        "correctamente."
    )


if __name__ == "__main__":
    main()
