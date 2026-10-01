const DATA_URL = "data/articles.json";

const CATEGORY_LABELS = {
    literatura: "Literatura",
    cine: "Cine",
    television: "Televisión",
    artes_visuales: "Artes visuales",
    ciencia: "Ciencia",
    videojuegos: "Videojuegos",
    musica: "Música",
    filosofia: "Filosofía",
    historia: "Historia",
    cultura: "Cultura",
    tecnologia: "Tecnología",
    sociedad: "Sociedad"
};

const CATEGORY_ORDER = [
    "literatura",
    "cine",
    "ciencia",
    "historia",
    "artes_visuales",
    "musica",
    "filosofia",
    "tecnologia",
    "sociedad",
    "cultura",
    "television",
    "videojuegos"
];

const HISTORY_KEY = "deriva_random_history";
const MAX_RANDOM_HISTORY = 30;

let articles = [];
let currentCategory = null;


/*
 * CARGAR DATOS
 */

async function loadArticles() {

    try {

        const response = await fetch(DATA_URL);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (Array.isArray(data)) {

            articles = data;

        } else if (
            data &&
            Array.isArray(data.articles)
        ) {

            articles = data.articles;

        } else if (
            data &&
            Array.isArray(data.items)
        ) {

            articles = data.items;

        } else if (
            data &&
            Array.isArray(data.data)
        ) {

            articles = data.data;

        } else {

            throw new Error(
                "No se encontró la lista de artículos."
            );
        }

        initializeApp();

    } catch (error) {

        console.error(
            "Error cargando artículos:",
            error
        );

        showLoadError();
    }
}


/*
 * INICIALIZAR
 */

function initializeApp() {

    renderCategoryGrids();

    setupNavigation();

    setupRandomButton();

    setupBackButton();
}


/*
 * NAVEGACIÓN
 */

function setupNavigation() {

    const buttons =
        document.querySelectorAll(
            ".nav-button"
        );

    buttons.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const view =
                    button.dataset.view;

                showView(view);

            }
        );

    });
}


function showView(viewName) {

    const views =
        document.querySelectorAll(
            ".view"
        );

    views.forEach(view => {

        view.classList.remove(
            "active-view"
        );

    });

    const target =
        document.getElementById(
            `${viewName}-view`
        );

    if (target) {

        target.classList.add(
            "active-view"
        );

    }

    const navButtons =
        document.querySelectorAll(
            ".nav-button"
        );

    navButtons.forEach(button => {

        button.classList.toggle(
            "active",
            button.dataset.view === viewName
        );

    });

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


/*
 * CATEGORÍAS
 */

function getAvailableCategories() {

    return CATEGORY_ORDER.filter(
        category => {

            return articles.some(
                article =>
                    (
                        article.categories || []
                    ).includes(category)
            );

        }
    );
}


function renderCategoryGrids() {

    const categories =
        getAvailableCategories();

    const grids =
        document.querySelectorAll(
            ".category-grid"
        );

    grids.forEach(grid => {

        grid.innerHTML = "";

        categories.forEach(category => {

            const button =
                createCategoryButton(
                    category
                );

            grid.appendChild(button);

        });

    });
}


function createCategoryButton(category) {

    const button =
        document.createElement(
            "button"
        );

    button.className =
        "category-button";

    button.textContent =
        CATEGORY_LABELS[category] || category;

    button.addEventListener(
        "click",
        () => {

            showCategory(category);

        }
    );

    return button;
}


/*
 * DAME ALGO
 */

function setupRandomButton() {

    const button =
        document.getElementById(
            "random-button"
        );

    button.addEventListener(
        "click",
        showRandomArticle
    );
}


function getRandomHistory() {

    try {

        const stored =
            localStorage.getItem(
                HISTORY_KEY
            );

        if (!stored) {
            return [];
        }

        const parsed =
            JSON.parse(stored);

        return Array.isArray(parsed)
            ? parsed
            : [];

    } catch {

        return [];
    }
}


function saveRandomHistory(id) {

    if (!id) {
        return;
    }

    let history =
        getRandomHistory();

    history =
        history.filter(
            item => item !== id
        );

    history.unshift(id);

    history =
        history.slice(
            0,
            MAX_RANDOM_HISTORY
        );

    try {

        localStorage.setItem(
            HISTORY_KEY,
            JSON.stringify(history)
        );

    } catch {

        // Si localStorage está bloqueado,
        // simplemente continuamos sin historial.
    }
}


function scoreArticleForRandom(article) {

    let score = 0;

    const history =
        getRandomHistory();

    /*
     * Penalizar artículos ya mostrados.
     */

    if (history.includes(article.id)) {
        score -= 100;
    }

    /*
     * Favorecer artículos con información
     * útil para la interfaz.
     */

    if (article.description) {
        score += 10;
    }

    if (article.image_url) {
        score += 5;
    }

    if (article.author) {
        score += 3;
    }

    if (article.reading_time) {
        score += 3;
    }

    if (
        Array.isArray(article.categories) &&
        article.categories.length
    ) {
        score += 2;
    }

    /*
     * Un pequeño componente aleatorio evita
     * que siempre gane exactamente el mismo artículo.
     */

    score += Math.random() * 20;

    return score;
}


function showRandomArticle() {

    if (!articles.length) {
        return;
    }

    const ranked =
        articles
            .map(article => ({
                article,
                score:
                    scoreArticleForRandom(article)
            }))
            .sort(
                (a, b) =>
                    b.score - a.score
            );

    const article =
        ranked[0].article;

    saveRandomHistory(
        article.id
    );

    const container =
        document.getElementById(
            "random-result"
        );

    container.innerHTML =
        createArticleCard(
            article,
            true
        );

    container.classList.remove(
        "hidden"
    );

    container.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


/*
 * MOSTRAR CATEGORÍA
 */

function showCategory(category) {

    currentCategory =
        category;

    showView("explore");

    const categoryGrid =
        document.getElementById(
            "explore-category-grid"
        );

    const results =
        document.getElementById(
            "category-results"
        );

    categoryGrid.classList.add(
        "hidden"
    );

    results.classList.remove(
        "hidden"
    );

    const title =
        document.getElementById(
            "category-title"
        );

    const count =
        document.getElementById(
            "category-count"
        );

    title.textContent =
        CATEGORY_LABELS[category]
        || category;

    const categoryArticles =
        articles.filter(
            article =>
                (
                    article.categories || []
                ).includes(category)
        );

    count.textContent =
        `${categoryArticles.length} artículos`;

    const grid =
        document.getElementById(
            "articles-grid"
        );

    grid.innerHTML = "";

    if (!categoryArticles.length) {

        grid.innerHTML = `
            <p class="empty-state">
                Todavía no hay artículos en esta categoría.
            </p>
        `;

        return;
    }

    categoryArticles.forEach(
        article => {

            grid.insertAdjacentHTML(
                "beforeend",
                createArticleCard(article)
            );

        }
    );
}


/*
 * VOLVER A CATEGORÍAS
 */

function setupBackButton() {

    const button =
        document.getElementById(
            "back-to-categories"
        );

    button.addEventListener(
        "click",
        () => {

            const grid =
                document.getElementById(
                    "explore-category-grid"
                );

            const results =
                document.getElementById(
                    "category-results"
                );

            grid.classList.remove(
                "hidden"
            );

            results.classList.add(
                "hidden"
            );

            currentCategory =
                null;

        }
    );
}


/*
 * TARJETA DE ARTÍCULO
 */

function createArticleCard(
    article,
    featured = false
) {

    const title =
        escapeHtml(
            article.title
            || "Sin título"
        );

    const description =
        cleanDescription(
            article.description
            || ""
        );

    const source =
        escapeHtml(
            article.source_name
            || formatSource(
                article.source || ""
            )
        );

    const contentType =
        escapeHtml(
            formatContentType(
                article.content_type
                || ""
            )
        );

    const author =
        article.author
            ? escapeHtml(
                article.author
            )
            : "";

    const date =
        formatDate(
            article.published_at
        );

    const readingTime =
        formatReadingTime(
            article.reading_time
        );

    const category =
        formatFirstCategory(
            article.categories
        );

    const image =
        article.image_url
            ? `
                <div class="article-image">
                    <img
                        src="${escapeAttribute(
                            article.image_url
                        )}"
                        alt=""
                        loading="lazy"
                        onerror="this.parentElement.remove()"
                    >
                </div>
            `
            : "";

    const url =
        article.url || "#";

    const metadata =
        [
            contentType,
            category,
            readingTime
        ].filter(Boolean);

    const authorDate =
        [
            author,
            date
        ].filter(Boolean);

    return `
        <article class="
            article-card
            ${featured ? "article-card-featured" : ""}
        ">

            ${image}

            <div class="article-card-content">

                <p class="article-source">
                    ${source}
                </p>

                <h3>
                    ${title}
                </h3>

                ${
                    description
                        ? `
                            <p class="article-description">
                                ${description}
                            </p>
                        `
                        : ""
                }

                ${
                    authorDate.length
                        ? `
                            <p class="article-byline">
                                ${authorDate.join(" · ")}
                            </p>
                        `
                        : ""
                }

                <div class="article-footer">

                    <div class="article-meta">
                        ${
                            metadata
                                .map(
                                    item =>
                                        `<span>${escapeHtml(item)}</span>`
                                )
                                .join(
                                    '<span class="meta-separator">·</span>'
                                )
                        }
                    </div>

                    <a
                        class="article-link"
                        href="${escapeAttribute(url)}"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Leer →
                    </a>

                </div>

            </div>

        </article>
    `;
}


/*
 * FORMATO
 */

function formatSource(source) {

    const names = {

        new_yorker:
            "The New Yorker",

        jot_down:
            "Jot Down",

        paris_review:
            "The Paris Review",

        longreads:
            "Longreads",

        aeon:
            "Aeon",

        quanta:
            "Quanta",

        mubi_notebook:
            "MUBI Notebook",

        public_domain_review:
            "Public Domain Review"

    };

    return (
        names[source]
        || source
        || "Fuente"
    );
}


function formatContentType(type) {

    const names = {

        essay: "Ensayo",
        analysis: "Análisis",
        interview: "Entrevista",
        history: "Historia",
        podcast: "Podcast",
        video: "Video",
        review: "Reseña",
        list: "Lista",
        collection: "Colección",
        reportage: "Reportaje",
        game: "Juego",
        criticism: "Crítica",
        fiction: "Ficción",
        profile: "Perfil",
        cartoon: "Caricatura"

    };

    return (
        names[type]
        || type
        || "Artículo"
    );
}


function formatFirstCategory(categories) {

    if (
        !Array.isArray(categories)
        || !categories.length
    ) {
        return "";
    }

    return (
        CATEGORY_LABELS[
            categories[0]
        ]
        || categories[0]
    );
}


function formatReadingTime(minutes) {

    if (
        minutes === null
        || minutes === undefined
        || minutes === ""
    ) {
        return "";
    }

    const value =
        Number(minutes);

    if (!Number.isFinite(value)) {
        return "";
    }

    return `${value} min`;
}


function formatDate(value) {

    if (!value) {
        return "";
    }

    const date =
        new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return "";
    }

    return new Intl.DateTimeFormat(
        "es-MX",
        {
            day: "numeric",
            month: "short",
            year: "numeric"
        }
    ).format(date);
}


/*
 * LIMPIAR DESCRIPCIONES
 */

function cleanDescription(description) {

    const temp =
        document.createElement(
            "div"
        );

    temp.innerHTML =
        description;

    const text =
        temp.textContent
        || temp.innerText
        || "";

    const clean =
        text
            .replace(
                /\s+/g,
                " "
            )
            .trim();

    if (
        clean.length <= 220
    ) {

        return escapeHtml(
            clean
        );

    }

    return escapeHtml(
        clean.slice(
            0,
            217
        )
        + "..."
    );
}


/*
 * SEGURIDAD BÁSICA
 */

function escapeHtml(value) {

    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


function escapeAttribute(value) {

    return escapeHtml(value);
}


/*
 * ERROR
 */

function showLoadError() {

    const main =
        document.querySelector(
            "main"
        );

    main.innerHTML = `
        <section class="hero">

            <p class="eyebrow">
                DERIVA
            </p>

            <h1>
                Algo salió mal.
            </h1>

            <p class="hero-text">
                No pude cargar los artículos.
                Revisa que data/articles.json
                exista y que estés abriendo
                Deriva desde un servidor.
            </p>

        </section>
    `;
}


/*
 * ARRANCAR
 */

loadArticles();
