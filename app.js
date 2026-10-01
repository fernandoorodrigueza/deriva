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

        const data = await response.json();


        /*
         * articles.json puede ser:
         *
         * [
         *   {...},
         *   {...}
         * ]
         *
         * o:
         *
         * {
         *   "articles": [...]
         * }
         */

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

    const buttons = document.querySelectorAll(
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


function showRandomArticle() {

    if (!articles.length) {
        return;
    }


    const randomIndex =
        Math.floor(
            Math.random()
            * articles.length
        );


    const article =
        articles[randomIndex];


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
        clean.length
        <= 220
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
