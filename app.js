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


const RANDOM_HISTORY_KEY =
    "deriva_random_history";

const RANDOM_SOURCE_KEY =
    "deriva_random_sources";

const RANDOM_CATEGORY_KEY =
    "deriva_random_categories";

const RANDOM_HISTORY_LIMIT = 12;

const RANDOM_SOURCE_LIMIT = 4;

const RANDOM_CATEGORY_LIMIT = 5;


let articles = [];

let currentCategory = null;


/*
 * CARGAR DATOS
 */

async function loadArticles() {

    try {

        const response = await fetch(
            DATA_URL
        );

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }

        const data =
            await response.json();


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


    buttons.forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    const view =
                        button.dataset.view;

                    showView(view);

                }
            );

        }
    );

}


function showView(viewName) {

    const views =
        document.querySelectorAll(
            ".view"
        );


    views.forEach(
        view => {

            view.classList.remove(
                "active-view"
            );

        }
    );


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


    navButtons.forEach(
        button => {

            button.classList.toggle(
                "active",
                button.dataset.view === viewName
            );

        }
    );


    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

}


/*
 * CATEGORÍAS
 */

function getAvailableCategories() {

    const available =
        new Set();


    articles.forEach(
        article => {

            const categories =
                article.categories || [];


            categories.forEach(
                category => {

                    available.add(
                        category
                    );

                }
            );

        }
    );


    return CATEGORY_ORDER.filter(
        category =>
            available.has(category)
    );

}


function renderCategoryGrids() {

    const categories =
        getAvailableCategories();


    const grids =
        document.querySelectorAll(
            ".category-grid"
        );


    grids.forEach(
        grid => {

            grid.innerHTML = "";


            categories.forEach(
                category => {

                    const button =
                        createCategoryButton(
                            category
                        );


                    grid.appendChild(
                        button
                    );

                }
            );

        }
    );

}


function createCategoryButton(
    category
) {

    const button =
        document.createElement(
            "button"
        );


    button.className =
        "category-button";


    button.textContent =
        CATEGORY_LABELS[
            category
        ] || category;


    button.addEventListener(
        "click",
        () => {

            showCategory(
                category
            );

        }
    );


    return button;

}


/*
 * DAME ALGO
 *
 * El objetivo no es recomendar "lo que te gusta".
 * El objetivo es producir una deriva variada.
 */


/*
 * Leer historial de artículos
 */

function getRandomHistory() {

    try {

        const value =
            localStorage.getItem(
                RANDOM_HISTORY_KEY
            );


        if (!value) {

            return [];

        }


        const parsed =
            JSON.parse(value);


        return Array.isArray(parsed)
            ? parsed
            : [];

    } catch {

        return [];

    }

}


/*
 * Guardar historial de artículos
 */

function saveRandomHistory(
    article
) {

    if (!article || !article.id) {

        return;

    }


    let history =
        getRandomHistory();


    history =
        history.filter(
            id =>
                id !== article.id
        );


    history.unshift(
        article.id
    );


    history =
        history.slice(
            0,
            RANDOM_HISTORY_LIMIT
        );


    try {

        localStorage.setItem(
            RANDOM_HISTORY_KEY,
            JSON.stringify(history)
        );

    } catch {

        // Continuar aunque localStorage no esté disponible.

    }

}


/*
 * Historial de fuentes
 */

function getRandomSources() {

    try {

        const value =
            localStorage.getItem(
                RANDOM_SOURCE_KEY
            );


        if (!value) {

            return [];

        }


        const parsed =
            JSON.parse(value);


        return Array.isArray(parsed)
            ? parsed
            : [];

    } catch {

        return [];

    }

}


/*
 * Guardar fuente reciente
 */

function saveRandomSource(
    article
) {

    const source =
        article.source;


    if (!source) {

        return;

    }


    let sources =
        getRandomSources();


    sources =
        sources.filter(
            item =>
                item !== source
        );


    sources.unshift(
        source
    );


    sources =
        sources.slice(
            0,
            RANDOM_SOURCE_LIMIT
        );


    try {

        localStorage.setItem(
            RANDOM_SOURCE_KEY,
            JSON.stringify(sources)
        );

    } catch {

        // Continuar sin memoria de fuentes.

    }

}


/*
 * Historial de categorías
 */

function getRandomCategories() {

    try {

        const value =
            localStorage.getItem(
                RANDOM_CATEGORY_KEY
            );


        if (!value) {

            return [];

        }


        const parsed =
            JSON.parse(value);


        return Array.isArray(parsed)
            ? parsed
            : [];

    } catch {

        return [];

    }

}


/*
 * Guardar categoría reciente
 */

function saveRandomCategories(
    article
) {

    const categories =
        article.categories || [];


    if (!categories.length) {

        return;

    }


    let history =
        getRandomCategories();


    categories.forEach(
        category => {

            history =
                history.filter(
                    item =>
                        item !== category
                );


            history.unshift(
                category
            );

        }
    );


    history =
        history.slice(
            0,
            RANDOM_CATEGORY_LIMIT
        );


    try {

        localStorage.setItem(
            RANDOM_CATEGORY_KEY,
            JSON.stringify(history)
        );

    } catch {

        // Continuar sin memoria de categorías.

    }

}


/*
 * Días desde publicación
 */

function getArticleAgeDays(
    article
) {

    if (!article.published_at) {

        return 365;

    }


    const published =
        new Date(
            article.published_at
        );


    if (
        Number.isNaN(
            published.getTime()
        )
    ) {

        return 365;

    }


    const now =
        new Date();


    const difference =
        now.getTime()
        - published.getTime();


    return Math.max(
        0,
        difference / (
            1000 *
            60 *
            60 *
            24
        )
    );

}


/*
 * Puntuación para "Dame algo"
 */

function scoreRandomArticle(
    article
) {

    let score = 0;


    const history =
        getRandomHistory();


    const recentSources =
        getRandomSources();


    const recentCategories =
        getRandomCategories();


    /*
     * 1. No repetir artículos recientes.
     */

    if (
        history.includes(
            article.id
        )
    ) {

        score -= 1000;

    }


    /*
     * 2. Evitar repetir fuente.
     *
     * No la prohibimos.
     * Solo la hacemos menos probable.
     */

    if (
        recentSources.includes(
            article.source
        )
    ) {

        const position =
            recentSources.indexOf(
                article.source
            );


        score -=
            80 -
            (
                position * 15
            );

    }


    /*
     * 3. Evitar repetir categoría.
     */

    const categories =
        article.categories || [];


    const repeatedCategory =
        categories.some(
            category =>
                recentCategories.includes(
                    category
                )
        );


    if (repeatedCategory) {

        score -= 35;

    }


    /*
     * 4. Favorecer artículos con buena
     * información disponible.
     */

    if (article.description) {

        score += 12;

    }


    if (article.image_url) {

        score += 8;

    }


    if (article.author) {

        score += 4;

    }


    if (
        article.reading_time
    ) {

        score += 3;

    }


    /*
     * 5. Edad del artículo.
     *
     * No queremos convertir Deriva en un
     * lector de noticias de última hora.
     *
     * Tampoco queremos que todo sea arqueología.
     *
     * La antigüedad recibe una pequeña
     * variación aleatoria.
     */

    const age =
        getArticleAgeDays(
            article
        );


    if (age <= 2) {

        score += 10;

    } else if (age <= 7) {

        score += 7;

    } else if (age <= 30) {

        score += 4;

    } else if (age <= 180) {

        score += 2;

    } else {

        score += 1;

    }


    /*
     * 6. Aleatoriedad.
     *
     * Esto es fundamental.
     *
     * Si no existe azar, deja de ser Deriva.
     */

    score +=
        Math.random() * 30;


    return score;

}


/*
 * Elegir artículo
 */

function chooseRandomArticle() {

    if (!articles.length) {

        return null;

    }


    /*
     * Primero intentamos excluir
     * los artículos vistos recientemente.
     */

    const history =
        getRandomHistory();


    let candidates =
        articles.filter(
            article =>
                !history.includes(
                    article.id
                )
        );


    /*
     * Si ya hemos recorrido prácticamente
     * todo el catálogo, permitimos volver
     * a usar artículos.
     */

    if (!candidates.length) {

        candidates =
            articles.slice();

    }


    /*
     * Puntuar candidatos.
     */

    const ranked =
        candidates
            .map(
                article => ({

                    article,

                    score:
                        scoreRandomArticle(
                            article
                        )

                })
            )
            .sort(
                (a, b) =>
                    b.score -
                    a.score
            );


    /*
     * No siempre tomamos el primero.
     *
     * Elegimos entre los tres mejores.
     *
     * Así conservamos una pequeña dosis
     * de imprevisibilidad.
     */

    const pool =
        ranked.slice(
            0,
            Math.min(
                3,
                ranked.length
            )
        );


    const selected =
        pool[
            Math.floor(
                Math.random() *
                pool.length
            )
        ];


    return selected
        ? selected.article
        : candidates[0];

}


/*
 * Mostrar artículo aleatorio
 */

function showRandomArticle() {

    const article =
        chooseRandomArticle();


    if (!article) {

        return;

    }


    saveRandomHistory(
        article
    );


    saveRandomSource(
        article
    );


    saveRandomCategories(
        article
    );


    const container =
        document.getElementById(
            "random-result"
        );


    container.innerHTML =
        createArticleCard(
            article
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

function showCategory(
    category
) {

    currentCategory =
        category;


    showView(
        "explore"
    );


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
        CATEGORY_LABELS[
            category
        ] || category;


    const categoryArticles =
        articles.filter(
            article =>
                (
                    article.categories
                    || []
                ).includes(
                    category
                )
        );


    count.textContent =
        `${categoryArticles.length} artículos`;


    const grid =
        document.getElementById(
            "articles-grid"
        );


    grid.innerHTML = "";


    categoryArticles.forEach(
        article => {

            grid.insertAdjacentHTML(
                "beforeend",
                createArticleCard(
                    article
                )
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
    article
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
            formatSource(
                article.source
                || ""
            )
        );


    const contentType =
        escapeHtml(
            formatContentType(
                article.content_type
                || ""
            )
        );


    const url =
        article.url
        || "#";


    return `
        <article class="article-card">

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

            <div class="article-footer">

                <span class="article-type">
                    ${contentType}
                </span>

                <a
                    class="article-link"
                    href="${escapeAttribute(url)}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Leer →
                </a>

            </div>

        </article>
    `;

}


/*
 * FORMATO
 */

function formatSource(
    source
) {

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


function formatContentType(
    type
) {

    const names = {

        essay:
            "Ensayo",

        analysis:
            "Análisis",

        interview:
            "Entrevista",

        history:
            "Historia",

        podcast:
            "Podcast",

        video:
            "Video",

        review:
            "Reseña",

        list:
            "Lista",

        collection:
            "Colección",

        reportage:
            "Reportaje",

        game:
            "Juego",

        criticism:
            "Crítica",

        fiction:
            "Ficción",

        profile:
            "Perfil",

        cartoon:
            "Caricatura"

    };


    return (
        names[type]
        || type
        || "Artículo"
    );

}


/*
 * LIMPIAR DESCRIPCIONES
 */

function cleanDescription(
    description
) {

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

function escapeHtml(
    value
) {

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


function escapeAttribute(
    value
) {

    return escapeHtml(
        value
    );

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
