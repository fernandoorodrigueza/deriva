import json
import re
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "articles.json"


def load_articles():
    with open(
        DATA_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)

    # Si el JSON es directamente una lista de artículos.
    if isinstance(data, list):
        return data

    # Si el JSON contiene los artículos dentro de una propiedad.
    if isinstance(data, dict):

        for key in (
            "articles",
            "items",
            "data",
        ):
            value = data.get(key)

            if isinstance(value, list):
                return value

    raise ValueError(
        "No se encontró una lista de artículos "
        "en data/articles.json"
    )


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def keyword_matches(text, keyword):
    """
    Comprueba si una palabra o expresión aparece
    como palabra completa.

    Evita falsos positivos como:
    'ai' dentro de otra palabra.
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


def audit_basic_stats(articles):
    print_header(
        "ESTADÍSTICAS GENERALES"
    )

    print(
        f"Artículos: {len(articles)}"
    )

    sources = Counter(
        article.get(
            "source",
            "unknown",
        )
        for article in articles
    )

    categories = Counter()

    for article in articles:

        for category in article.get(
            "categories",
            [],
        ):
            categories[category] += 1

    content_types = Counter(
        article.get(
            "content_type",
            "unknown",
        )
        for article in articles
    )

    print("\nPor fuente:")

    for source, count in sources.most_common():

        print(
            f"  {source}: {count}"
        )

    print("\nPor categoría:")

    for category, count in categories.most_common():

        percentage = (
            count
            / len(articles)
            * 100
        )

        print(
            f"  {category}: "
            f"{count} "
            f"({percentage:.1f}%)"
        )

    print("\nPor tipo de contenido:")

    for content_type, count in content_types.most_common():

        print(
            f"  {content_type}: {count}"
        )


def audit_cultura(articles):
    """
    Analiza los artículos clasificados únicamente
    como 'cultura'.

    No intenta reclasificarlos.
    Solo busca señales que indiquen que podrían
    pertenecer también a una categoría específica.
    """

    culture_only = [
        article
        for article in articles
        if article.get(
            "categories",
            [],
        ) == ["cultura"]
    ]

    print_header(
        "CULTURA: ANÁLISIS AUTOMÁTICO"
    )

    print(
        "Artículos clasificados únicamente "
        f"como 'cultura': {len(culture_only)}"
    )

    if not culture_only:

        print(
            "No hay artículos para analizar."
        )

        return

    # --------------------------------------------------
    # 1. Cultura por fuente
    # --------------------------------------------------

    by_source = Counter(
        article.get(
            "source",
            "unknown",
        )
        for article in culture_only
    )

    print("\nPOR FUENTE")

    for source, count in by_source.most_common():

        percentage = (
            count
            / len(culture_only)
            * 100
        )

        print(
            f"  {source}: "
            f"{count} "
            f"({percentage:.1f}%)"
        )

    # --------------------------------------------------
    # 2. Palabras que pueden indicar otra categoría
    # --------------------------------------------------

    category_signal_words = {

        "cine": [
            "film",
            "films",
            "filmmaker",
            "filmmaking",
            "cinema",
            "movie",
            "movies",
            "director",
            "screenplay",
            "actor",
            "actress",
            "documentary",
        ],

        "literatura": [
            "book",
            "books",
            "novel",
            "novels",
            "poetry",
            "poem",
            "poems",
            "poet",
            "author",
            "authors",
            "literary",
            "literature",
            "manuscript",
        ],

        "ciencia": [
            "science",
            "scientist",
            "physics",
            "physicist",
            "biology",
            "biologist",
            "chemistry",
            "chemical",
            "astronomy",
            "astronomer",
            "medicine",
            "medical",
            "cancer",
            "oncology",
            "diagnosis",
            "diagnostic",
            "cell",
            "cells",
            "cellular",
            "disease",
            "diseases",
            "clinical",
        ],

        "musica": [
            "music",
            "musician",
            "musicians",
            "song",
            "songs",
            "album",
            "albums",
            "composer",
            "singer",
            "concert",
        ],

        "artes_visuales": [
            "painting",
            "paintings",
            "painter",
            "photograph",
            "photography",
            "photographer",
            "sculpture",
            "sculptor",
            "drawing",
            "drawings",
            "illustration",
            "illustrator",
            "diagram",
            "diagrams",
            "anatomy",
            "anatomical",
        ],

        "historia": [
            "history",
            "historical",
            "ancient",
            "medieval",
            "empire",
            "war",
            "century",
            "archaeology",
            "archaeological",
        ],

        "tecnologia": [
            "technology",
            "technological",
            "computer",
            "computing",
            "software",
            "internet",
            "algorithm",
            "artificial intelligence",
            "ai",
        ],

        "sociedad": [
            "society",
            "social",
            "politics",
            "political",
            "migration",
            "migrant",
            "immigration",
            "inequality",
            "gender",
            "race",
        ],
    }

    candidate_counts = Counter()

    candidate_examples = defaultdict(
        list
    )

    # --------------------------------------------------
    # 3. Analizar cada artículo cultura
    # --------------------------------------------------

    for article in culture_only:

        title = article.get(
            "title",
            "",
        )

        description = article.get(
            "description",
            "",
        )

        url = article.get(
            "url",
            "",
        )

        tags = article.get(
            "tags",
            [],
        )

        text = " ".join(
            [
                title,
                description,
                url,
                " ".join(tags),
            ]
        ).lower()

        article_signals = []

        for category, keywords in (
            category_signal_words.items()
        ):

            matches = []

            for keyword in keywords:

                if keyword_matches(
                    text,
                    keyword,
                ):
                    matches.append(
                        keyword
                    )

            if matches:

                article_signals.append(
                    (
                        category,
                        matches,
                    )
                )

        if not article_signals:
            continue

        # La categoría con más señales
        # se considera la candidata principal.
        article_signals.sort(
            key=lambda item: len(
                item[1]
            ),
            reverse=True,
        )

        category, matches = (
            article_signals[0]
        )

        candidate_counts[
            category
        ] += 1

        # Solo guardamos hasta cinco ejemplos
        # por categoría para no llenar el log.
        if (
            len(
                candidate_examples[
                    category
                ]
            )
            < 5
        ):

            candidate_examples[
                category
            ].append(
                {
                    "title": title,
                    "source": article.get(
                        "source",
                        "unknown",
                    ),
                    "matches": matches,
                }
            )

    # --------------------------------------------------
    # 4. Resumen de posibles problemas
    # --------------------------------------------------

    print(
        "\nPOSIBLES SEÑALES "
        "DE OTRA CATEGORÍA"
    )

    if not candidate_counts:

        print(
            "  No se encontraron señales claras."
        )

    else:

        for category, count in (
            candidate_counts.most_common()
        ):

            percentage = (
                count
                / len(culture_only)
                * 100
            )

            print(
                f"  {category}: "
                f"{count} "
                f"({percentage:.1f}%)"
            )

            for example in (
                candidate_examples[
                    category
                ]
            ):

                print(
                    f"    - "
                    f"[{example['source']}] "
                    f"{example['title']}"
                )

                print(
                    "      señales: "
                    + ", ".join(
                        example[
                            "matches"
                        ]
                    )
                )


def audit_cultura_sin_senales(articles):
    """
    Identifica artículos clasificados únicamente
    como cultura que no muestran señales fuertes
    de ninguna categoría específica.

    Estos son los candidatos más razonables
    para permanecer como 'cultura'.
    """

    culture_only = [
        article
        for article in articles
        if article.get(
            "categories",
            [],
        ) == ["cultura"]
    ]

    print_header(
        "CULTURA SIN SEÑALES ESPECÍFICAS"
    )

    strong_signals = [
        "film",
        "cinema",
        "movie",
        "filmmaker",
        "book",
        "novel",
        "poetry",
        "poem",
        "author",
        "literature",
        "science",
        "scientist",
        "physics",
        "biology",
        "medicine",
        "medical",
        "cancer",
        "cell",
        "disease",
        "music",
        "musician",
        "song",
        "album",
        "painting",
        "photography",
        "sculpture",
        "drawing",
        "illustration",
        "history",
        "historical",
        "archaeology",
        "technology",
        "computer",
        "software",
    ]

    without_signals = []

    for article in culture_only:

        text = " ".join(
            [
                article.get(
                    "title",
                    "",
                ),
                article.get(
                    "description",
                    "",
                ),
                article.get(
                    "url",
                    "",
                ),
                " ".join(
                    article.get(
                        "tags",
                        [],
                    )
                ),
            ]
        ).lower()

        found = False

        for keyword in strong_signals:

            if keyword_matches(
                text,
                keyword,
            ):
                found = True
                break

        if not found:

            without_signals.append(
                article
            )

    print(
        "Artículos sin señales temáticas "
        f"fuertes: {len(without_signals)}"
    )

    if culture_only:

        percentage = (
            len(without_signals)
            / len(culture_only)
            * 100
        )

        print(
            f"Proporción: {percentage:.1f}%"
        )

    print()
    print(
        "Estos artículos son los candidatos "
        "más razonables para permanecer "
        "como 'cultura'."
    )


def audit_category_combinations(articles):
    print_header(
        "COMBINACIONES DE CATEGORÍAS"
    )

    combinations = Counter()

    for article in articles:

        categories = tuple(
            sorted(
                article.get(
                    "categories",
                    [],
                )
            )
        )

        combinations[
            categories
        ] += 1

    for combination, count in (
        combinations.most_common()
    ):

        label = " + ".join(
            combination
        )

        print(
            f"  {count:3}  {label}"
        )


def audit_source_categories(articles):
    print_header(
        "CATEGORÍAS POR FUENTE"
    )

    source_categories = defaultdict(
        Counter
    )

    for article in articles:

        source = article.get(
            "source",
            "unknown",
        )

        for category in article.get(
            "categories",
            [],
        ):

            source_categories[
                source
            ][category] += 1

    for source in sorted(
        source_categories
    ):

        print()
        print(source)

        total = sum(
            source_categories[
                source
            ].values()
        )

        for category, count in (
            source_categories[
                source
            ].most_common()
        ):

            percentage = (
                count
                / total
                * 100
            )

            print(
                f"  {category}: "
                f"{count} "
                f"({percentage:.1f}%)"
            )


def audit_suspicious_combinations(
    articles
):
    print_header(
        "POSIBLES CLASIFICACIONES SOSPECHOSAS"
    )

    suspicious = []

    for article in articles:

        categories = set(
            article.get(
                "categories",
                [],
            )
        )

        url = (
            article.get(
                "url",
                "",
            )
            .lower()
        )

        source = article.get(
            "source",
            "",
        )

        # New Yorker Front Row
        # debería estar relacionado con cine.
        if (
            source == "new_yorker"
            and "/the-front-row/" in url
            and "cine"
            not in categories
        ):

            suspicious.append(
                (
                    "New Yorker Front Row "
                    "sin cine",
                    article,
                )
            )

        # New Yorker Books
        # debería estar relacionado con literatura.
        if (
            source == "new_yorker"
            and "/books/" in url
            and "literatura"
            not in categories
        ):

            suspicious.append(
                (
                    "New Yorker Books "
                    "sin literatura",
                    article,
                )
            )

        # New Yorker cartoons
        # debería estar relacionado con artes visuales.
        if (
            source == "new_yorker"
            and "/cartoons/" in url
            and "artes_visuales"
            not in categories
        ):

            suspicious.append(
                (
                    "New Yorker Cartoon "
                    "sin artes_visuales",
                    article,
                )
            )

        # Quanta debería tener ciencia.
        if (
            source == "quanta"
            and "ciencia"
            not in categories
        ):

            suspicious.append(
                (
                    "Quanta sin ciencia",
                    article,
                )
            )

        # MUBI Notebook debería tener cine.
        if (
            source == "mubi_notebook"
            and "cine"
            not in categories
        ):

            suspicious.append(
                (
                    "MUBI sin cine",
                    article,
                )
            )

    print(
        f"Total detectados: "
        f"{len(suspicious)}"
    )

    for reason, article in suspicious:

        print()

        print(
            f"  {reason}"
        )

        print(
            f"  [{article.get('source')}] "
            f"{article.get('title')}"
        )

        print(
            f"  Categorías: "
            f"{article.get('categories')}"
        )

        print(
            f"  URL: "
            f"{article.get('url')}"
        )


def main():

    print(
        "Auditoría de categorías de Deriva"
    )

    print(
        f"Archivo: {DATA_PATH}"
    )

    articles = load_articles()

    audit_basic_stats(
        articles
    )

    audit_cultura(
        articles
    )

    audit_cultura_sin_senales(
        articles
    )

    audit_category_combinations(
        articles
    )

    audit_source_categories(
        articles
    )

    audit_suspicious_combinations(
        articles
    )

    print_header(
        "AUDITORÍA TERMINADA"
    )


if __name__ == "__main__":
    main()
