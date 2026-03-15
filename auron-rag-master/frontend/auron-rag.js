// ─── Section → Rubrika mapping ───────────────────────────────────────────────
const SECTION_MAP = {
    'o-spolecnosti':    ['Marketing'],
    'organizace':       ['Správa majetku'],
    'pracovni-informace': ['Výroba', 'Nákup'],
    'zivot-a-kariera':  ['Personální informace'],
    'sluzby':           ['IT', 'IT Provoz'],
    'odmenovani':       ['Investice'],
    'strategie':        ['Vývoj'],
};

// Track where user was before going to an article (for back navigation)
let _prevSection = 'dashboard';

// ─── Helpers ─────────────────────────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ─── Article cards ────────────────────────────────────────────────────────────
function buildCard(article) {
    const excerpt = article.text.length > 120
        ? article.text.slice(0, 120) + '…'
        : article.text;
    return `
        <div class="card p-6 flex flex-col cursor-pointer" onclick="showArticle('${escapeHtml(article.slug)}')">
            <span class="text-xs font-bold text-[#3b82f6] uppercase mb-1">${escapeHtml(article.rubrika)}</span>
            <h3 class="text-base font-bold text-gray-800 mb-1 leading-snug">${escapeHtml(article.nazev)}</h3>
            <p class="text-gray-400 text-xs mb-3">${escapeHtml(article.datum)}</p>
            <p class="text-gray-600 text-sm flex-grow">${escapeHtml(excerpt)}</p>
            <a href="${escapeHtml(article.url)}" class="text-[#1e3a8a] font-semibold text-sm mt-4 inline-block hover:underline"
               onclick="event.stopPropagation()">Číst více &rarr;</a>
        </div>`;
}

function renderSection(containerId, rubrikyList) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const articles = ARTICLES.filter(a => rubrikyList.includes(a.rubrika));
    container.innerHTML = articles.length
        ? articles.map(buildCard).join('')
        : '<p class="text-gray-400">Žádné články v této sekci.</p>';
}

function renderAktuality() {
    const container = document.getElementById('aktuality-cards');
    if (!container) return;
    // 3 newest (ARTICLES already sorted newest-first by generate_data_js.py)
    const latest = ARTICLES.slice(0, 3);
    container.innerHTML = latest.map(article => `
        <div class="card flex flex-col md:flex-row overflow-hidden cursor-pointer"
             onclick="showArticle('${escapeHtml(article.slug)}')">
            <div class="md:w-1/4 bg-[#1e3a8a] flex items-center justify-center p-6">
                <i class="fas fa-newspaper text-3xl text-white opacity-70"></i>
            </div>
            <div class="p-6 md:w-3/4">
                <span class="text-xs font-bold text-[#3b82f6] uppercase">${escapeHtml(article.rubrika)}</span>
                <h3 class="text-lg font-bold mt-1 mb-2 text-gray-800">${escapeHtml(article.nazev)}</h3>
                <p class="text-gray-400 text-xs mb-2">${escapeHtml(article.datum)}</p>
                <p class="text-gray-600 text-sm mb-4">${escapeHtml(article.text.slice(0, 140))}…</p>
                <a href="${escapeHtml(article.url)}" class="text-[#1e3a8a] font-semibold text-sm hover:underline"
                   onclick="event.stopPropagation()">Číst více &rarr;</a>
            </div>
        </div>`).join('');
}

// ─── Article detail ───────────────────────────────────────────────────────────
function showArticle(slug, pushHistory = true) {
    const article = ARTICLES.find(a => a.slug === slug);
    if (!article) return;

    const container = document.getElementById('article-content');
    container.innerHTML = `
        <span class="text-xs font-bold text-[#3b82f6] uppercase">${escapeHtml(article.rubrika)}</span>
        <h1 class="text-2xl font-bold text-gray-900 mt-2 mb-1">${escapeHtml(article.nazev)}</h1>
        <p class="text-gray-400 text-sm mb-6">${escapeHtml(article.datum)}</p>
        <hr class="mb-6 border-gray-200">
        <p class="article-body text-gray-700 leading-relaxed">${escapeHtml(article.text)}</p>`;

    // Only push history when not called from a hashchange (browser already added the entry)
    if (pushHistory) {
        history.pushState(null, '', article.url);
    }

    _prevSection = document.querySelector('.content-section.active')?.id || 'dashboard';
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.getElementById('article-detail').classList.add('active');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    window.scrollTo(0, 0);
}

function goBack() {
    history.replaceState(null, '', window.location.pathname);
    showSection(_prevSection);
}

// ─── Hash-based routing ───────────────────────────────────────────────────────
function handleHash() {
    const hash = window.location.hash;
    if (hash.startsWith('#/article/')) {
        const slug = decodeURIComponent(hash.replace('#/article/', ''));
        showArticle(slug, false);
    }
}

window.addEventListener('hashchange', () => {
    const hash = window.location.hash;
    if (hash.startsWith('#/article/')) {
        const slug = decodeURIComponent(hash.replace('#/article/', ''));
        showArticle(slug, false);
    } else {
        showSection(_prevSection);
    }
});

window.addEventListener('popstate', () => {
    const hash = window.location.hash;
    if (hash.startsWith('#/article/')) {
        handleHash();
    } else {
        // Back to a regular section
        showSection(_prevSection);
    }
});

// ─── Navigation ───────────────────────────────────────────────────────────────
function showSection(id, el) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    if (el) {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        el.classList.add('active');
    }
    // Clear hash when navigating to a regular section
    if (window.location.hash) {
        history.pushState(null, '', window.location.pathname);
    }
    window.scrollTo(0, 0);
}

function toggleMobileMenu() {
    document.getElementById('main-menu').classList.toggle('hidden');
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
async function handleAuronGPT() {
    const input = document.getElementById('gpt-input');
    const output = document.getElementById('chat-output');
    const query = input.value.trim();

    if (!query) return;

    output.classList.remove('hidden');
    output.innerHTML += `
        <div class="flex justify-end chat-message">
            <div class="bg-blue-100 text-blue-900 px-4 py-2 rounded-lg rounded-tr-none max-w-[85%] shadow-sm">
                ${escapeHtml(query)}
            </div>
        </div>`;
    input.value = '';
    output.scrollTop = output.scrollHeight;

    const loadingId = 'load-' + Date.now();
    output.innerHTML += `
        <div id="${loadingId}" class="flex justify-start chat-message mt-2">
            <div class="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-2">
                <i class="fas fa-robot text-gray-400 text-xs"></i>
            </div>
            <div class="bg-gray-50 px-4 py-2 rounded-lg rounded-tl-none border border-gray-100">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
        </div>`;
    output.scrollTop = output.scrollHeight;

    try {
        const response = await fetch('/api/rag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, top_k: 5 })
        });

        if (!response.ok) throw new Error('HTTP error status: ' + response.status);

        const data = await response.json();
        document.getElementById(loadingId).remove();

        const sourcesHtml = data.sources.filter(s => s.url).map(s => `
            <a href="${escapeHtml(s.url)}" class="flex items-center gap-2 px-3 py-2 bg-blue-50 hover:bg-blue-100 rounded-lg text-xs text-[#1e3a8a] font-medium transition-colors">
                <i class="fas fa-file-alt flex-shrink-0"></i>
                <span>${escapeHtml(s.title || s.url)}</span>
            </a>`).join('');

        output.innerHTML += `
            <div class="flex justify-start chat-message mt-2">
                <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center mr-2 flex-shrink-0 shadow-md">
                    <i class="fas fa-brain text-xs"></i>
                </div>
                <div class="flex flex-col max-w-[90%] gap-2">
                    <div class="bg-white border border-gray-200 text-gray-800 px-4 py-3 rounded-lg rounded-tl-none shadow-sm text-sm">
                        ${escapeHtml(data.answer)}
                    </div>
                    ${sourcesHtml ? `<div class="flex flex-col gap-1">${sourcesHtml}</div>` : ''}
                </div>
            </div>`;

        output.scrollTop = output.scrollHeight;

    } catch (error) {
        console.error('Error:', error);
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        output.innerHTML += `
            <div class="flex justify-start chat-message mt-2">
                <div class="bg-red-50 border border-red-200 px-4 py-3 rounded-lg text-red-800 text-sm">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    Chyba při komunikaci se serverem. Zkuste znovu.
                </div>
            </div>`;

        output.scrollTop = output.scrollHeight;
    }
}

function clearChat() {
    document.getElementById('chat-output').innerHTML = '';
    document.getElementById('chat-output').classList.add('hidden');
}

function handleEnter(e) {
    if (e.key === 'Enter') handleAuronGPT();
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Render all nav sections
    Object.entries(SECTION_MAP).forEach(([sectionId, rubrikyList]) => {
        renderSection('cards-' + sectionId, rubrikyList);
    });

    // Render dashboard aktuality
    renderAktuality();

    // Handle direct URL with article hash
    if (window.location.hash.startsWith('#/article/')) {
        handleHash();
    }
});
