/**
 * Entertainment Tracker - Main Application Logic
 * Works in two modes:
 * - Local mode: Full CRUD via Python server API (editable)
 * - GitHub Pages mode: Read-only, loads library.json directly
 */

(function () {
    'use strict';

    // ===== State =====
    let library = [];
    let isLocalMode = false;
    let editingId = null;

    // ===== DOM Elements =====
    const searchInput = document.getElementById('search-input');
    const filterStatus = document.getElementById('filter-status');
    const filterType = document.getElementById('filter-type');
    const sortBy = document.getElementById('sort-by');
    const viewMode = document.getElementById('view-mode');
    const addItemBtn = document.getElementById('add-item-btn');
    const statsGrid = document.getElementById('stats-grid');
    const libraryGrid = document.getElementById('library-grid');
    const modeBadge = document.getElementById('mode-badge');

    // Modal elements
    const itemModal = document.getElementById('item-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalClose = document.getElementById('modal-close');
    const itemForm = document.getElementById('item-form');
    const formTitle = document.getElementById('form-title');
    const formType = document.getElementById('form-type');
    const formStatus = document.getElementById('form-status');
    const formLanguage = document.getElementById('form-language');
    const formRating = document.getElementById('form-rating');
    const formGenres = document.getElementById('form-genres');
    const formImdbId = document.getElementById('form-imdb-id');
    const formTags = document.getElementById('form-tags');
    const formCancel = document.getElementById('form-cancel');

    // Recommendation modal
    const recModal = document.getElementById('rec-modal');
    const recModalTitle = document.getElementById('rec-modal-title');
    const recModalClose = document.getElementById('rec-modal-close');
    const recContent = document.getElementById('rec-content');

    // ===== Initialization =====
    async function init() {
        await detectMode();
        await loadLibrary();
        renderStats();
        renderLibrary();
        bindEvents();
    }

    async function detectMode() {
        try {
            const resp = await fetch('/api/health', { method: 'GET' });
            if (resp.ok) {
                isLocalMode = true;
                modeBadge.textContent = '✏️ Local — Editable';
                modeBadge.className = 'mode-badge local';
                addItemBtn.style.display = 'inline-block';
            } else {
                setReadonlyMode();
            }
        } catch {
            setReadonlyMode();
        }
    }

    function setReadonlyMode() {
        isLocalMode = false;
        modeBadge.textContent = '👁️ View Only';
        modeBadge.className = 'mode-badge readonly';
        addItemBtn.style.display = 'none';
    }

    // ===== Data Loading =====
    async function loadLibrary() {
        try {
            let resp;
            if (isLocalMode) {
                resp = await fetch('/api/library');
            } else {
                resp = await fetch('data/library.json');
            }
            if (resp.ok) {
                library = await resp.json();
            } else {
                libraryGrid.innerHTML = '<p class="loading">Failed to load library data.</p>';
            }
        } catch (err) {
            libraryGrid.innerHTML = '<p class="loading">Error loading library: ' + escapeHtml(err.message) + '</p>';
        }
    }

    // ===== Stats Rendering =====
    function renderStats() {
        const total = library.length;
        const watched = library.filter(i => i.status === 'Watched').length;
        const watching = library.filter(i => i.status === 'Watching').length;
        const planToWatch = library.filter(i => i.status === 'Plan to Watch').length;
        const recommended = library.filter(i => i.status === 'Recommended').length;
        const movies = library.filter(i => i.type === 'Movie').length;
        const series = library.filter(i => i.type === 'Series').length;
        const watchedRatings = library.filter(i => i.status === 'Watched' && i.rating > 0).map(i => i.rating);
        const avgRating = watchedRatings.length > 0
            ? (watchedRatings.reduce((a, b) => a + b, 0) / watchedRatings.length).toFixed(1)
            : 'N/A';

        statsGrid.innerHTML = [
            statCard(total, 'Total'),
            statCard(watched, 'Watched'),
            statCard(watching, 'Watching'),
            statCard(planToWatch, 'Plan to Watch'),
            statCard(recommended, 'Recommended'),
            statCard(movies, 'Movies'),
            statCard(series, 'Series'),
            statCard(avgRating, 'Avg Rating'),
        ].join('');
    }

    function statCard(value, label) {
        return '<div class="stat-card"><div class="stat-value">' + escapeHtml(String(value)) + '</div><div class="stat-label">' + escapeHtml(label) + '</div></div>';
    }

    // ===== Library Rendering =====
    function renderLibrary() {
        const filtered = getFilteredLibrary();
        if (filtered.length === 0) {
            libraryGrid.innerHTML = '<p class="loading">No items match your filters.</p>';
            return;
        }

        const currentViewMode = viewMode.value;
        
        if (currentViewMode === 'genre') {
            renderGenreView(filtered);
        } else {
            renderTypeLanguageView(filtered);
        }
    }

    function renderTypeLanguageView(items) {
        // Group by Type (Movie/Series) then by Language
        const moviesByLanguage = {};
        const seriesByLanguage = {};

        items.forEach(item => {
            const lang = item.language || 'Other';
            if (item.type === 'Movie') {
                if (!moviesByLanguage[lang]) moviesByLanguage[lang] = [];
                moviesByLanguage[lang].push(item);
            } else {
                if (!seriesByLanguage[lang]) seriesByLanguage[lang] = [];
                seriesByLanguage[lang].push(item);
            }
        });

        let html = '';

        // Render Movies section
        if (Object.keys(moviesByLanguage).length > 0) {
            html += '<div class="section-header">🎥 Movies</div>';
            Object.keys(moviesByLanguage).sort().forEach(lang => {
                html += '<div class="subsection-header">' + escapeHtml(lang) + '</div>';
                html += '<div class="library-grid">';
                moviesByLanguage[lang].forEach(item => {
                    html += renderCard(item);
                });
                html += '</div>';
            });
        }

        // Render Series section
        if (Object.keys(seriesByLanguage).length > 0) {
            html += '<div class="section-header">📺 TV Series</div>';
            Object.keys(seriesByLanguage).sort().forEach(lang => {
                html += '<div class="subsection-header">' + escapeHtml(lang) + '</div>';
                html += '<div class="library-grid">';
                seriesByLanguage[lang].forEach(item => {
                    html += renderCard(item);
                });
                html += '</div>';
            });
        }

        libraryGrid.innerHTML = html;
    }

    function renderGenreView(items) {
        // Group by Genre
        const itemsByGenre = {};
        const noGenreItems = [];

        items.forEach(item => {
            const genres = item.genres || [];
            if (genres.length === 0) {
                noGenreItems.push(item);
            } else {
                // Add item to each of its genres
                genres.forEach(genre => {
                    if (!itemsByGenre[genre]) itemsByGenre[genre] = [];
                    itemsByGenre[genre].push(item);
                });
            }
        });

        let html = '';

        // Render genre sections
        Object.keys(itemsByGenre).sort().forEach(genre => {
            const genreEmoji = getGenreEmoji(genre);
            html += '<div class="section-header">' + genreEmoji + ' ' + escapeHtml(genre) + '</div>';
            html += '<div class="library-grid">';
            // Remove duplicates (items with multiple genres) using Set for O(n) complexity
            const seenIds = new Set();
            const uniqueItems = itemsByGenre[genre].filter(item => {
                if (seenIds.has(item.id)) return false;
                seenIds.add(item.id);
                return true;
            });
            uniqueItems.forEach(item => {
                html += renderCard(item);
            });
            html += '</div>';
        });

        // Render items without genres
        if (noGenreItems.length > 0) {
            html += '<div class="section-header">📋 Other</div>';
            html += '<div class="library-grid">';
            noGenreItems.forEach(item => {
                html += renderCard(item);
            });
            html += '</div>';
        }

        libraryGrid.innerHTML = html;
    }

    function getGenreEmoji(genre) {
        const emojiMap = {
            'Action': '💥',
            'Thriller': '😱',
            'Drama': '🎭',
            'Comedy': '😂',
            'Sci-Fi': '🚀',
            'Horror': '👻',
            'Mystery': '🔍',
            'Crime': '🔪',
            'Fantasy': '🧙',
            'Romance': '💕',
            'Animation': '🎨',
            'Noir': '🌑',
            'Superhero': '🦸',
            'Adventure': '🗺️',
            'Epic': '⚔️',
            'Political': '🏛️',
            'Folk Horror': '🌿',
            'Dark Comedy': '🃏',
            'Time Travel': '⏰',
            'Spy': '🕵️'
        };
        return emojiMap[genre] || '🎬';
    }

    function getFilteredLibrary() {
        let items = [...library];
        const query = searchInput.value.toLowerCase().trim();
        const statusFilter = filterStatus.value;
        const typeFilter = filterType.value;
        const sortValue = sortBy.value;

        if (query) {
            items = items.filter(i =>
                i.title.toLowerCase().includes(query) ||
                (i.tags && i.tags.some(t => t.toLowerCase().includes(query)))
            );
        }
        if (statusFilter !== 'all') {
            items = items.filter(i => i.status === statusFilter);
        }
        if (typeFilter !== 'all') {
            items = items.filter(i => i.type === typeFilter);
        }

        switch (sortValue) {
            case 'title':
                items.sort((a, b) => a.title.localeCompare(b.title));
                break;
            case 'rating-desc':
                items.sort((a, b) => b.rating - a.rating);
                break;
            case 'rating-asc':
                items.sort((a, b) => a.rating - b.rating);
                break;
            case 'id-desc':
                items.sort((a, b) => b.id - a.id);
                break;
            case 'id-asc':
                items.sort((a, b) => a.id - b.id);
                break;
        }

        return items;
    }

    function renderCard(item) {
        const statusClass = item.status.toLowerCase().replace(/\s+/g, '-');
        const ratingDisplay = item.rating > 0 ? '⭐ ' + item.rating + '/10' : '';
        // Show genres if available, otherwise show tags
        const displayTags = item.genres && item.genres.length > 0 ? item.genres : (item.tags || []);
        const tagsHtml = displayTags.map(t => '<span class="tag">' + escapeHtml(t) + '</span>').join('');

        let actionsHtml = '<div class="card-actions">';
        if (isLocalMode) {
            actionsHtml += '<button class="btn btn-small btn-secondary" onclick="app.editItem(' + item.id + ')">✏️ Edit</button>';
        }
        actionsHtml += '<button class="btn btn-small btn-rec" onclick="app.showInfo(' + item.id + ')">🔍 Info</button>';
        if (isLocalMode) {
            actionsHtml += '<button class="btn btn-small btn-danger" onclick="app.deleteItem(' + item.id + ')">🗑️</button>';
        }
        actionsHtml += '</div>';

        return '<div class="item-card">' +
            '<div class="card-header">' +
            '<span class="card-title clickable" onclick="app.showInfo(' + item.id + ')">' + escapeHtml(item.title) + '</span>' +
            (ratingDisplay ? '<span class="card-rating">' + ratingDisplay + '</span>' : '') +
            '</div>' +
            '<div class="card-meta">' +
            '<span class="badge badge-type">' + (item.type === 'Movie' ? '🎥' : '📺') + ' ' + escapeHtml(item.type) + '</span>' +
            '<span class="badge badge-status ' + statusClass + '">' + escapeHtml(item.status) + '</span>' +
            (item.language ? '<span class="badge badge-language">' + escapeHtml(item.language) + '</span>' : '') +
            '</div>' +
            (tagsHtml ? '<div class="card-tags">' + tagsHtml + '</div>' : '') +
            actionsHtml +
            '</div>';
    }

    // ===== CRUD Operations =====
    function openAddModal() {
        editingId = null;
        modalTitle.textContent = 'Add Item';
        formTitle.value = '';
        formType.value = 'Movie';
        formStatus.value = 'Plan to Watch';
        formLanguage.value = 'English';
        formRating.value = '0';
        formGenres.value = '';
        formImdbId.value = '';
        formTags.value = '';
        itemModal.style.display = 'flex';
    }

    function openEditModal(id) {
        const item = library.find(i => i.id === id);
        if (!item) return;
        editingId = id;
        modalTitle.textContent = 'Edit Item';
        formTitle.value = item.title;
        formType.value = item.type;
        formStatus.value = item.status;
        formLanguage.value = item.language || 'English';
        formRating.value = item.rating;
        formGenres.value = (item.genres || []).join(', ');
        formImdbId.value = item.imdbID || '';
        formTags.value = (item.tags || []).join(', ');
        itemModal.style.display = 'flex';
    }

    function closeModal() {
        itemModal.style.display = 'none';
        editingId = null;
    }

    async function saveItem(e) {
        e.preventDefault();
        if (!isLocalMode) return;

        const tags = formTags.value
            .split(',')
            .map(t => t.trim())
            .filter(t => t.length > 0);

        const genres = formGenres.value
            .split(',')
            .map(t => t.trim())
            .filter(t => t.length > 0)
            .slice(0, 3); // Max 3 genres

        const itemData = {
            title: formTitle.value.trim(),
            type: formType.value,
            status: formStatus.value,
            language: formLanguage.value,
            rating: parseFloat(formRating.value) || 0,
            genres: genres,
            imdbID: formImdbId.value.trim() || null,
            tags: tags
        };

        try {
            let resp;
            if (editingId !== null) {
                itemData.id = editingId;
                resp = await fetch('/api/library/' + editingId, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(itemData)
                });
            } else {
                resp = await fetch('/api/library', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(itemData)
                });
            }

            if (resp.ok) {
                await loadLibrary();
                renderStats();
                renderLibrary();
                closeModal();
            } else {
                const err = await resp.text();
                alert('Error saving: ' + err);
            }
        } catch (err) {
            alert('Error saving item: ' + err.message);
        }
    }

    async function deleteItem(id) {
        if (!isLocalMode) return;
        const item = library.find(i => i.id === id);
        if (!item) return;
        if (!confirm('Delete "' + item.title + '"?')) return;

        try {
            const resp = await fetch('/api/library/' + id, { method: 'DELETE' });
            if (resp.ok) {
                await loadLibrary();
                renderStats();
                renderLibrary();
            } else {
                alert('Error deleting item.');
            }
        } catch (err) {
            alert('Error deleting item: ' + err.message);
        }
    }

    // ===== Info & Recommendations =====
    function buildLinksHtml(title, imdbID) {
        const encodedTitle = encodeURIComponent(title);
        const imdbLink = imdbID
            ? '<a href="https://www.imdb.com/title/' + escapeHtml(imdbID) + '/" target="_blank" rel="noopener" class="btn-link imdb-link">🎬 View on IMDb</a>'
            : '<a href="https://www.imdb.com/find/?q=' + encodedTitle + '" target="_blank" rel="noopener" class="btn-link imdb-link">🔍 Search on IMDb</a>';
        return '<div class="rec-links">' +
            '<h3>🔗 External Links</h3>' +
            '<div class="rec-link-list">' +
            imdbLink +
            '<a href="https://www.justwatch.com/in/search?q=' + encodedTitle + '" target="_blank" rel="noopener" class="btn-link streaming-link">📺 Streaming (India)</a>' +
            '</div>' +
            '</div>';
    }

    async function showInfo(id) {
        const item = library.find(i => i.id === id);
        if (!item) return;

        recModalTitle.textContent = '🔍 ' + item.title;
        const linksHtml = buildLinksHtml(item.title, item.imdbID || null);

        if (isLocalMode) {
            recContent.innerHTML = '<p class="loading">Fetching information from IMDb, Rotten Tomatoes, Metacritic...</p>' + linksHtml;
            recModal.style.display = 'flex';

            try {
                const resp = await fetch('/api/recommendations/' + encodeURIComponent(item.title) + '?type=' + encodeURIComponent(item.type));
                if (resp.ok) {
                    const data = await resp.json();
                    renderRecommendations(data, item.title, item.imdbID);
                } else {
                    recContent.innerHTML = '<p class="rec-error">Failed to fetch recommendations. Server returned an error.</p>' + linksHtml;
                }
            } catch (err) {
                recContent.innerHTML = '<p class="rec-error">Could not connect to the recommendation service: ' + escapeHtml(err.message) + '</p>' + linksHtml;
            }
        } else {
            // Read-only mode: show item details and external links
            recContent.innerHTML = '<div class="rec-source">' +
                '<h3>📋 Details</h3>' +
                '<div class="rec-detail">Type: ' + escapeHtml(item.type) + '</div>' +
                '<div class="rec-detail">Status: ' + escapeHtml(item.status) + '</div>' +
                (item.language ? '<div class="rec-detail">Language: ' + escapeHtml(item.language) + '</div>' : '') +
                (item.rating > 0 ? '<div class="rec-detail">Rating: ⭐ ' + item.rating + '/10</div>' : '') +
                (item.genres && item.genres.length > 0 ? '<div class="rec-detail">Genres: ' + item.genres.map(t => escapeHtml(t)).join(', ') + '</div>' : '') +
                (item.tags && item.tags.length > 0 ? '<div class="rec-detail">Tags: ' + item.tags.map(t => escapeHtml(t)).join(', ') + '</div>' : '') +
                '</div>' +
                linksHtml;
            recModal.style.display = 'flex';
        }
    }

    function renderRecommendations(data, title, itemImdbID) {
        let html = '';
        let imdbID = itemImdbID || null;

        if (data.omdb) {
            const o = data.omdb;
            // Use OMDB imdbID if we don't have one already
            if (!imdbID) {
                imdbID = o.imdbID || null;
            }
            html += '<div class="rec-source">' +
                '<h3>📊 OMDB / IMDb</h3>' +
                (o.imdbRating ? '<div class="rec-score">IMDb: ' + escapeHtml(o.imdbRating) + '/10</div>' : '') +
                (o.Metascore && o.Metascore !== 'N/A' ? '<div class="rec-detail">Metascore: ' + escapeHtml(o.Metascore) + '/100</div>' : '') +
                (o.Plot ? '<div class="rec-detail">' + escapeHtml(o.Plot) + '</div>' : '') +
                (o.Genre ? '<div class="rec-detail">Genre: ' + escapeHtml(o.Genre) + '</div>' : '') +
                (o.Director ? '<div class="rec-detail">Director: ' + escapeHtml(o.Director) + '</div>' : '') +
                (o.Actors ? '<div class="rec-detail">Actors: ' + escapeHtml(o.Actors) + '</div>' : '') +
                (o.Year ? '<div class="rec-detail">Year: ' + escapeHtml(o.Year) + '</div>' : '') +
                (o.Awards && o.Awards !== 'N/A' ? '<div class="rec-detail">Awards: ' + escapeHtml(o.Awards) + '</div>' : '') +
                '</div>';

            // Show Rotten Tomatoes from OMDB Ratings array
            if (o.Ratings && Array.isArray(o.Ratings)) {
                o.Ratings.forEach(function (r) {
                    if (r.Source === 'Rotten Tomatoes') {
                        html += '<div class="rec-source">' +
                            '<h3>🍅 Rotten Tomatoes</h3>' +
                            '<div class="rec-score">' + escapeHtml(r.Value) + '</div>' +
                            '</div>';
                    }
                    if (r.Source === 'Metacritic') {
                        html += '<div class="rec-source">' +
                            '<h3>🎯 Metacritic</h3>' +
                            '<div class="rec-score">' + escapeHtml(r.Value) + '</div>' +
                            '</div>';
                    }
                });
            }
        }

        if (!data.omdb) {
            html += '<div class="rec-source"><p class="rec-error">No data found for this title. Try checking the exact title spelling.</p></div>';
        }

        if (data.omdb) {
            const o = data.omdb;
            html += '<div class="rec-summary">' +
                '<h3>📝 Summary</h3>' +
                '<p>' + buildSummary(o) + '</p>' +
                '</div>';
        }

        html += buildLinksHtml(title, imdbID);
        recContent.innerHTML = html;
    }

    function buildSummary(omdb) {
        let parts = [];
        if (omdb.Title) parts.push('"' + omdb.Title + '"');
        if (omdb.Year) parts.push('(' + omdb.Year + ')');
        if (omdb.imdbRating && omdb.imdbRating !== 'N/A') parts.push('has an IMDb rating of ' + omdb.imdbRating + '/10');
        if (omdb.Ratings) {
            omdb.Ratings.forEach(function (r) {
                if (r.Source === 'Rotten Tomatoes') {
                    parts.push('a Rotten Tomatoes score of ' + r.Value);
                }
            });
        }
        if (omdb.Metascore && omdb.Metascore !== 'N/A') parts.push('and a Metascore of ' + omdb.Metascore + '/100');
        return parts.join(' ') + '.';
    }

    function closeRecModal() {
        recModal.style.display = 'none';
    }

    // ===== Event Binding =====
    function bindEvents() {
        searchInput.addEventListener('input', renderLibrary);
        filterStatus.addEventListener('change', renderLibrary);
        filterType.addEventListener('change', renderLibrary);
        sortBy.addEventListener('change', renderLibrary);
        viewMode.addEventListener('change', renderLibrary);
        addItemBtn.addEventListener('click', openAddModal);
        modalClose.addEventListener('click', closeModal);
        formCancel.addEventListener('click', closeModal);
        itemForm.addEventListener('submit', saveItem);
        recModalClose.addEventListener('click', closeRecModal);

        // Close modals on overlay click
        document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
            overlay.addEventListener('click', function () {
                itemModal.style.display = 'none';
                recModal.style.display = 'none';
                editingId = null;
            });
        });
    }

    // ===== Utility =====
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    // Expose functions for onclick handlers
    window.app = {
        editItem: openEditModal,
        deleteItem: deleteItem,
        showInfo: showInfo
    };

    // Boot
    document.addEventListener('DOMContentLoaded', init);
})();
