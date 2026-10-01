import json
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


def audit_basic_stats(articles):
    print_header("ESTADÍSTICAS GENERALES")

    print(f"Artículos: {len(articles)}")

    sources = Counter(
        article.get("source", "unknown")
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
            count / len(articles) * 100
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
    print_header(
        "ARTÍCULOS CLASIFICADOS SOLO COMO CULTURA"
    )

    articles_cultura = []

    for article in articles:

        categories = article.get(
            "categories",
            [],
        )

        if categories == ["cultura"]:
            articles_cultura.append(
                article
            )

    print(
        f"Total: {len(articles_cultura)}"
    )

    for article in articles_cultura:

        print()
        print(
            f"[{article.get('source')}] "
            f"{article.get('title')}"
        )

        print(
            f"  URL: {article.get('url')}"
        )

        description = (
            article.get(
                "description",
                "",
            )
            .replace("\n", " ")
            .strip()
        )

        if len(description) > 180:
            description = (
                description[:180]
                + "..."
            )

        print(
            f"  Descripción: {description}"
        )

        tags = article.get(
            "tags",
            [],
        )

        if tags:
            print(
                f"  Tags: {', '.join(tags)}"
            )

        print(
            f"  Tipo: "
            f"{article.get('content_type')}"
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

        combinations[categories] += 1

    for combination, count in combinations.most_common():

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
                count / total * 100
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
            and "cine" not in categories
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
            and "ciencia" not in categories
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
            and "cine" not in categories
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
