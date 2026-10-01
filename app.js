const DATA_URL = "data/articles.json";


/*
 * CATEGORÍAS
 */

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


/*
 * MEMORIA DE "DAME ALGO"
 */

const RANDOM_HISTORY_KEY =
    "deriva_random_history";

const RANDOM_SOURCE_KEY =
    "deriva_random_sources";

const RANDOM_CATEGORY_KEY =
    "deriva_random_categories";

const RANDOM_HISTORY_LIMIT = 12;

const RANDOM_SOURCE_LIMIT = 4;

const RANDOM_CATEGORY_LIMIT = 5;


/*
 * MEMORIA DE GUARDADOS
 */

const SAVED_ARTICLES_KEY =
    "deriva_saved_articles";


let articles = [];

let currentCategory = null;


/*
 * CARGAR ARTÍCULOS
 */

async function loadArticles() {

    try {

        const response =
            await fetch(DATA_URL);


        if (!response.ok) {

            throw new Error(
                `No se pudo cargar ${DATA_URL}. HTTP ${response.status}`
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
                "articles.json no contiene una lista de artículos reconocible."
            );

        }


        if (!articles.length) {

            throw new Error(
                "articles.json se cargó correctamente, pero no contiene artículos."
            );

        }


        console.log(
            `Deriva: ${articles.length} artículos cargados.`
        );


        initializeApp();


    } catch (error) {

        console.error(
            "ERROR REAL DE DERIVA:",
            error
        );


        showLoadError(
            error
        );

    }

}


/*
 * INICIALIZAR
 */

function initializeApp() {

    try {

        renderCategoryGrids();

        setupNavigation();

        setupRandomButton();

        setupBackButton();

        setupSavedButtons();

        console.log(
            "Deriva inicializado correctamente."
        );


    } catch (error) {

        console.error(
            "ERROR DURANTE LA INICIALIZACIÓN:",
            error
        );


        showInitializationError(
            error
        );

    }

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


                    if (view) {

                        showView(
                            view
                        );

                    }

                }
            );

        }
    );

}


function showView(
    viewName
) {

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


    if (
        viewName === "saved"
    ) {

        renderSavedArticles();

    }


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
                Array.isArray(
                    article.categories
                )
                    ? article.categories
                    : [];


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
            available.has(
                category
            )
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


    button.type =
        "button";


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
 * ==========================
 * DAME ALGO
 * ==========================
 */


/*
 * HISTORIAL DE ARTÍCULOS
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
            JSON.parse(
                value
            );


        return Array.isArray(
            parsed
        )
            ? parsed
            : [];


    } catch {

        return [];

    }

}


function saveRandomHistory(
    article
) {

    if (
        !article ||
        !article.id
    ) {

        return;

    }


    let history =
        getRandomHistory();


    history =
        history.filter(
            id =>
                String(id) !==
                String(article.id)
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
            JSON.stringify(
                history
            )
        );

    } catch {

        // No pasa nada si localStorage está bloqueado.

    }

}


/*
 * HISTORIAL DE FUENTES
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
            JSON.parse(
                value
            );


        return Array.isArray(
            parsed
        )
            ? parsed
            : [];


    } catch {

        return [];

    }

}


function saveRandomSource(
    article
) {

    if (
        !article ||
        !article.source
    ) {

        return;

    }


    let sources =
        getRandomSources();


    sources =
        sources.filter(
            source =>
                source !==
                article.source
        );


    sources.unshift(
        article.source
    );


    sources =
        sources.slice(
            0,
            RANDOM_SOURCE_LIMIT
        );


    try {

        localStorage.setItem(
            RANDOM_SOURCE_KEY,
            JSON.stringify(
                sources
            )
        );

    } catch {

        // Continuar sin memoria de fuentes.

    }

}


/*
 * HISTORIAL DE CATEGORÍAS
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
            JSON.parse(
                value
            );


        return Array.isArray(
            parsed
        )
            ? parsed
            : [];


    } catch {

        return [];

    }

}


function saveRandomCategories(
    article
) {

    const categories =
        Array.isArray(
            article.categories
        )
            ? article.categories
            : [];


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
            JSON.stringify(
                history
            )
        );

    } catch {

        // Continuar sin memoria de categorías.

    }

}


/*
 * ANTIGÜEDAD DEL ARTÍCULO
 */

function getArticleAgeDays(
    article
) {

    const dateValue =
        article.published_at ||
        article.publication_date ||
        article.date;


    if (!dateValue) {

        return 365;

    }


    const published =
        new Date(
            dateValue
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
        -
        published.getTime();


    return Math.max(
        0,
        difference /
        (
            1000 *
            60 *
            60 *
            24
        )
    );

}


/*
 * PUNTUAR ARTÍCULO
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
     * Evitar artículos recientes.
     */

    if (
        history.some(
            id =>
                String(id) ===
                String(article.id)
        )
    ) {

        score -= 1000;

    }


    /*
     * Evitar repetir fuente.
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
     * Evitar repetir categoría.
     */

    const categories =
        Array.isArray(
            article.categories
        )
            ? article.categories
            : [];


    const repeatedCategory =
        categories.some(
            category =>
                recentCategories.includes(
                    category
                )
        );


    if (
        repeatedCategory
    ) {

        score -= 35;

    }


    /*
     * Premiar artículos con información completa.
     */

    if (
        article.description
    ) {

        score += 12;

    }


    if (
        article.image_url
    ) {

        score += 8;

    }


    if (
        article.author
    ) {

        score += 4;

    }


    if (
        article.reading_time
    ) {

        score += 3;

    }


    /*
     * Antigüedad.
     */

    const age =
        getArticleAgeDays(
            article
        );


    if (
        age <= 2
    ) {

        score += 10;

    } else if (
        age <= 7
    ) {

        score += 7;

    } else if (
        age <= 30
    ) {

        score += 4;

    } else if (
        age <= 180
    ) {

        score += 2;

    } else {

        score += 1;

    }


    /*
     * Azar.
     *
     * Fundamental para que Deriva
     * no se convierta en una lista
     * de recomendaciones predecible.
     */

    score +=
        Math.random() * 30;


    return score;

}


/*
 * ELEGIR ARTÍCULO
 */

function chooseRandomArticle() {

    if (!articles.length) {

        return null;

    }


    const history =
        getRandomHistory();


    let candidates =
        articles.filter(
            article =>
                !history.some(
                    id =>
                        String(id) ===
                        String(article.id)
                )
        );


    /*
     * Si eventualmente hemos recorrido
     * todo el catálogo, permitimos repetir.
     */

    if (!candidates.length) {

        candidates =
            articles.slice();

    }


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
     * Elegir entre los tres mejores.
     */

    const pool =
        ranked.slice(
            0,
            Math.min(
                3,
                ranked.length
            )
        );


    if (!pool.length) {

        return null;

    }


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
 * BOTÓN DAME ALGO
 */

function setupRandomButton() {

    const button =
        document.getElementById(
            "random-button"
        );


    if (!button) {

        return;

    }


    button.addEventListener(
        "click",
        showRandomArticle
    );

}


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


    if (!container) {

        return;

    }


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
 * ==========================
 * GUARDADOS
 * ==========================
 */


/*
 * Obtener IDs guardados
 */

function getSavedArticleIds() {

    try {

        const value =
            localStorage.getItem(
                SAVED_ARTICLES_KEY
            );


        if (!value) {

            return [];

        }


        const parsed =
            JSON.parse(
                value
            );


        return Array.isArray(
            parsed
        )
            ? parsed
            : [];


    } catch {

        return [];

    }

}


/*
 * Guardar IDs
 */

function saveArticleIds(
    ids
) {

    try {

        localStorage.setItem(
            SAVED_ARTICLES_KEY,
            JSON.stringify(
                ids
            )
        );

    } catch {

        // Continuar aunque localStorage no esté disponible.

    }

}


/*
 * Comprobar si está guardado
 */

function isArticleSaved(
    articleId
) {

    if (!articleId) {

        return false;

    }


    return getSavedArticleIds()
        .some(
            id =>
                String(id) ===
                String(articleId)
        );

}


/*
 * Guardar / quitar
 */

function toggleSavedArticle(
    articleId
) {

    if (!articleId) {

        return;

    }


    let savedIds =
        getSavedArticleIds();


    const index =
        savedIds.findIndex(
            id =>
                String(id) ===
                String(articleId)
        );


    if (
        index === -1
    ) {

        savedIds.push(
            articleId
        );

    } else {

        savedIds.splice(
            index,
            1
        );

    }


    saveArticleIds(
        savedIds
    );


    updateSaveButtons(
        articleId
    );


    const savedView =
        document.getElementById(
            "saved-view"
        );


    if (
        savedView &&
        savedView.classList.contains(
            "active-view"
        )
    ) {

        renderSavedArticles();

    }

}


/*
 * Actualizar botones
 */

function updateSaveButtons(
    articleId
) {

    const saved =
        isArticleSaved(
            articleId
        );


    const buttons =
        document.querySelectorAll(
            ".save-button"
        );


    buttons.forEach(
        button => {

            if (
                String(
                    button.dataset.articleId
                ) ===
                String(articleId)
            ) {

                button.textContent =
                    saved
                        ? "♥ Guardado"
                        : "♡ Guardar";


                button.classList.toggle(
                    "saved",
                    saved
                );

            }

        }
    );

}


/*
 * Activar botones de Guardar
 */

function setupSavedButtons() {

    document.addEventListener(
        "click",
        event => {

            const button =
                event.target.closest(
                    ".save-button"
                );


            if (!button) {

                return;

            }


            event.preventDefault();


            toggleSavedArticle(
                button.dataset.articleId
            );

        }
    );

}


/*
 * RENDERIZAR GUARDADOS
 */

function renderSavedArticles() {

    const grid =
        document.getElementById(
            "saved-grid"
        );


    const count =
        document.getElementById(
            "saved-count"
        );


    /*
     * Si todavía no está la vista
     * de Guardados, simplemente no hacemos nada.
     */

    if (
        !grid ||
        !count
    ) {

        return;

    }


    const savedIds =
        getSavedArticleIds();


    const savedArticles =
        savedIds
            .map(
                id =>
                    articles.find(
                        article =>
                            String(
                                article.id
                            ) ===
                            String(id)
                    )
            )
            .filter(
                Boolean
            );


    /*
     * Eliminar de localStorage IDs
     * de artículos que ya no existen.
     */

    const validIds =
        savedArticles.map(
            article =>
                article.id
        );


    if (
        validIds.length !==
        savedIds.length
    ) {

        saveArticleIds(
            validIds
        );

    }


    count.textContent =
        `${savedArticles.length} ${
            savedArticles.length === 1
                ? "artículo"
                : "artículos"
        }`;


    if (
        !savedArticles.length
    ) {

        grid.innerHTML = `
            <p class="empty-state">
                Todavía no has guardado nada.
                Cuando encuentres algo que quieras volver a leer,
                aparecerá aquí.
            </p>
        `;

        return;

    }


    grid.innerHTML = "";


    savedArticles.forEach(
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
 * ==========================
 * EXPLORAR CATEGORÍA
 * ==========================
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


    if (
        !categoryGrid ||
        !results
    ) {

        return;

    }


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


    if (title) {

        title.textContent =
            CATEGORY_LABELS[
                category
            ] || category;

    }


    const categoryArticles =
        articles.filter(
            article =>
                Array.isArray(
                    article.categories
                ) &&
                article.categories.includes(
                    category
                )
        );


    if (count) {

        count.textContent =
            `${categoryArticles.length} artículos`;

    }


    const grid =
        document.getElementById(
            "articles-grid"
        );


    if (!grid) {

        return;

    }


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


    if (!button) {

        return;

    }


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


            if (grid) {

                grid.classList.remove(
                    "hidden"
                );

            }


            if (results) {

                results.classList.add(
                    "hidden"
                );

            }


            currentCategory =
                null;

        }
    );

}


/*
 * ==========================
 * TARJETAS
 * ==========================
 */

function createArticleCard(
    article
) {

    const title =
        escapeHtml(
            article.title ||
            "Sin título"
        );


    const description =
        cleanDescription(
            article.description ||
            ""
        );


    const source =
        escapeHtml(
            formatSource(
                article.source ||
                ""
            )
        );


    const contentType =
        escapeHtml(
            formatContentType(
                article.content_type ||
                ""
            )
        );


    const url =
        article.url ||
        "#";


    const articleId =
        article.id
            ? String(
                article.id
            )
            : "";


    const saved =
        isArticleSaved(
            articleId
        );


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


                <div class="article-actions">

                    <button
                        class="save-button ${
                            saved
                                ? "saved"
                                : ""
                        }"
                        data-article-id="${escapeAttribute(
                            articleId
                        )}"
                        type="button"
                    >
                        ${
                            saved
                                ? "♥ Guardado"
                                : "♡ Guardar"
                        }
                    </button>


                    <a
                        class="article-link"
                        href="${escapeAttribute(
                            url
                        )}"
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
 * ==========================
 * FORMATO
 * ==========================
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
        names[source] ||
        source ||
        "Fuente"
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
        names[type] ||
        type ||
        "Artículo"
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
        temp.textContent ||
        temp.innerText ||
        "";


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
        ) + "..."
    );

}


/*
 * SEGURIDAD
 */

function escapeHtml(
    value
) {

    return String(
        value
    )
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
 * ERRORES
 */

function showLoadError(
    error
) {

    const main =
        document.querySelector(
            "main"
        );


    if (!main) {

        return;

    }


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
            </p>


            <p class="hero-text">
                ${escapeHtml(
                    error.message
                )}
            </p>

        </section>

    `;

}


function showInitializationError(
    error
) {

    const main =
        document.querySelector(
            "main"
        );


    if (!main) {

        return;

    }


    main.innerHTML = `

        <section class="hero">

            <p class="eyebrow">
                DERIVA
            </p>


            <h1>
                Los artículos cargaron,
                pero algo falló al iniciar.
            </h1>


            <p class="hero-text">
                ${escapeHtml(
                    error.message
                )}
            </p>

        </section>

    `;

}


/*
 * ARRANCAR
 */

loadArticles();
