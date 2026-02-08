/**
 * Entertainment Tracker - Main Application Logic (Refactored for New UI)
 * Works in two modes:
 * - Local mode: Full CRUD via Python server API (editable)
 * - GitHub Pages mode: Read-only, loads library.json directly
 * 
 * New features:
 * - Sidebar navigation with view switching
 * - Dashboard view with statistics
 * - Dynamic filter chip rendering
 * - Responsive mobile sidebar toggle
 */

(function () {
    'use strict';

    // ===== State =====
    let library = [];
    let isLocalMode = false;
    let editingId = null;
    let currentView = 'all'; // 'all', 'movies', 'series', 'dashboard'
    
    // Performance optimization: Virtual rendering
    let renderCache = new Map();
    let visibleItems = [];
    const ITEMS_PER_BATCH = 20; // Render 20 items at a time
    let currentBatch = 0;
    
    // Poster cache
    const posterCache = new Map();
    const OMDB_API_KEY = ''; // User can add their key if they want poster fetching

    // ===== DOM Elements =====
    
    // Sidebar
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const navItems = document.querySelectorAll('.nav-item');
    
    // Main content areas
    const librarySection = document.querySelector('.library-section');
    const dashboardSection = document.querySelector('.dashboard-section');
    
    // Toolbar & Controls
    const searchInput = document.getElementById('search-input');
    const filterStatus = document.getElementById('filter-status');
    const filterType = document.getElementById('filter-type');
    const sortBy = document.getElementById('sort-by');
    const viewMode = document.getElementById('view-mode');
    const addItemBtn = document.getElementById('add-item-btn');
    const filterToggleBtn = document.querySelector('[data-toggle="filter-panel"]');
    const filterPanel = document.querySelector('.filter-panel');
    const filterChips = document.querySelector('#filter-chips');
    const layoutToggleBtn = document.getElementById('layout-toggle-btn');
    const resultsCount = document.querySelector('.results-count');
    
    // Library
    const libraryGrid = document.getElementById('library-grid');
    
    // Dashboard
    const statsGrid = document.getElementById('stats-grid');
    
    // Mode badge
    const modeBadge = document.querySelector('.mode-badge') || document.querySelector('[data-mode-badge]');

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
        setupSidebarNavigation();
        setupResponsiveMenu();
        renderDashboard(); // Render dashboard for initial load
        renderStats();
        loadLayoutMode();
        renderLibrary();
        bindEvents();
    }

    async function detectMode() {
        try {
            const resp = await fetch('/api/health', { method: 'GET' });
            if (resp.ok) {
                isLocalMode = true;
                if (modeBadge) {
                    modeBadge.textContent = '✏️ Editable';
                    modeBadge.className = 'mode-badge local';
                }
                if (addItemBtn) addItemBtn.style.display = 'inline-flex';
            } else {
                setReadonlyMode();
            }
        } catch {
            setReadonlyMode();
        }
    }

    function setReadonlyMode() {
        isLocalMode = false;
        if (modeBadge) {
            modeBadge.textContent = '👁️ View Only';
            modeBadge.className = 'mode-badge readonly';
        }
        if (addItemBtn) addItemBtn.style.display = 'none';
    }

    // ===== Data Loading =====
    async function loadLibrary() {
        showSkeletons();
        try {
            let resp;
            if (isLocalMode) {
                resp = await fetch('/api/library');
            } else {
                resp = await fetch('data/library.json');
            }
            if (resp.ok) {
                library = await resp.json();
                // Preload posters for first batch
                preloadPosters(library.slice(0, ITEMS_PER_BATCH));
            } else {
                if (libraryGrid) libraryGrid.innerHTML = '<div class="no-results"><p>Failed to load library data.</p></div>';
            }
        } catch (err) {
            if (libraryGrid) libraryGrid.innerHTML = '<div class="no-results"><p>Error loading library: ' + escapeHtml(err.message) + '</p></div>';
        }
    }
    
    // ===== Poster Fetching (OMDB API) =====
    async function fetchPoster(item) {
        // Check cache first
        if (posterCache.has(item.id)) {
            return posterCache.get(item.id);
        }
        
        // If no IMDB ID or no API key, return null
        if (!item.imdbID || !OMDB_API_KEY) {
            posterCache.set(item.id, null);
            return null;
        }
        
        try {
            const response = await fetch(`https://www.omdbapi.com/?i=${item.imdbID}&apikey=${OMDB_API_KEY}`);
            const data = await response.json();
            
            if (data.Response === 'True' && data.Poster && data.Poster !== 'N/A') {
                posterCache.set(item.id, data.Poster);
                return data.Poster;
            }
        } catch (err) {
            console.warn('Failed to fetch poster for', item.title, err);
        }
        
        posterCache.set(item.id, null);
        return null;
    }
    
    async function preloadPosters(items) {
        if (!OMDB_API_KEY) return;
        
        // Preload posters in batches to avoid rate limiting
        const promises = items.map(item => fetchPoster(item));
        await Promise.allSettled(promises);
    }

    function showSkeletons() {
        if (!libraryGrid) return;
        let html = '';
        for (let i = 0; i < 6; i++) {
            html += '<div class="skeleton-card">' +
                '<div class="skeleton skeleton-title"></div>' +
                '<div class="skeleton skeleton-meta"></div>' +
                '<div class="skeleton skeleton-tags"></div>' +
                '<div class="skeleton skeleton-actions"></div>' +
                '</div>';
        }
        libraryGrid.innerHTML = html;
    }

    // ===== Sidebar Navigation =====
    function setupSidebarNavigation() {
        navItems.forEach(item => {
            item.addEventListener('click', function () {
                const view = this.getAttribute('data-view');
                if (view) {
                    switchView(view);
                    // Close sidebar on mobile after selection
                    if (window.innerWidth < 768) {
                        sidebar.classList.remove('open');
                    }
                }
            });
        });
    }

    function switchView(view) {
        currentView = view;
        
        // Update active nav item
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-view') === view) {
                item.classList.add('active');
            }
        });

        // Show/hide sections
        if (librarySection) {
            librarySection.style.display = view === 'dashboard' ? 'none' : 'flex';
        }
        if (dashboardSection) {
            dashboardSection.style.display = view === 'dashboard' ? 'flex' : 'none';
        }

        if (view === 'dashboard') {
            renderDashboard();
        } else {
            // Apply type filter based on view
            if (view === 'movies') {
                if (filterType) filterType.value = 'Movie';
            } else if (view === 'series') {
                if (filterType) filterType.value = 'Series';
            } else {
                if (filterType) filterType.value = 'all';
            }
            renderLibrary();
        }
    }

    function setupResponsiveMenu() {
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function () {
                sidebar.classList.toggle('open');
            });
        }

        // Close sidebar when clicking outside on mobile
        if (window.innerWidth < 768) {
            document.addEventListener('click', function (e) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            });
        }
    }

    // ===== Filter Panel & Chips =====
    function updateFilterChips() {
        if (!filterChips) return;

        const chips = [];
        if (filterStatus && filterStatus.value !== 'all') {
            chips.push({ label: 'Status: ' + filterStatus.value, value: 'status' });
        }
        if (filterType && filterType.value !== 'all') {
            chips.push({ label: 'Type: ' + filterType.value, value: 'type' });
        }

        filterChips.innerHTML = chips.map(chip => 
            '<div class="chip">' +
            escapeHtml(chip.label) +
            '<button class="chip-close" onclick="app.removeChip(\'' + chip.value + '\')" title="Remove filter">×</button>' +
            '</div>'
        ).join('');
    }

    function removeChip(filterType) {
        if (filterType === 'status' && filterStatus) {
            filterStatus.value = 'all';
        } else if (filterType === 'type' && filterType) {
            filterType.value = 'all';
        }
        updateFilterChips();
        renderLibrary();
    }

    // ===== Stats & Dashboard =====
    function renderStats() {
        if (!statsGrid) return;
        
        // Ensure container has correct class for Bento Layout
        statsGrid.className = 'bento-grid';

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
            : '0.0';
        const isEmpty = total === 0;
        const emptyValue = '—';
            
        // Icons (inlined for simplicity in vanilla JS)
        const iLib = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>';
        const iStar = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>';
        const iPlay = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>';
        const iCheck = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
        const iClock = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';

        statsGrid.innerHTML = [
            bentoCard('Total Library', isEmpty ? emptyValue : total, 'bento-col-2 bento-blue', iLib, isEmpty),
            bentoCard('Avg Score', isEmpty ? emptyValue : avgRating, 'bento-purple', iStar, isEmpty),
            bentoCard('Watching', isEmpty ? emptyValue : watching, 'bento-green', iPlay, isEmpty),
            bentoCard('Completed', isEmpty ? emptyValue : watched, '', iCheck, isEmpty),
            bentoCard('Planning', isEmpty ? emptyValue : planToWatch, 'bento-yellow', iClock, isEmpty),
            bentoCard('Movies', isEmpty ? emptyValue : movies, '', '🎬', isEmpty),
            bentoCard('Series', isEmpty ? emptyValue : series, '', '📺', isEmpty),
            bentoCard('Recs', isEmpty ? emptyValue : recommended, '', '✨', isEmpty),
        ].join('');
    }

    function bentoCard(title, value, classes = '', icon = '', isGhost = false) {
        const ghostClass = isGhost ? ' is-ghost' : '';
        const ghostNote = isGhost ? '<div class="bento-ghost">No data yet</div>' : '';
        return '<div class="bento-card ' + classes + ghostClass + '">' +
               '<div class="bento-icon">' + icon + '</div>' + 
               '<div>' +
               '<div class="bento-title">' + escapeHtml(title) + '</div>' +
               '<div class="bento-value">' + escapeHtml(String(value)) + '</div>' +
               ghostNote +
               '</div>' +
               '</div>';
    }

    function renderDashboard() {
        renderStats();
        
        // Placeholder for future chart sections
        // const chartsContainer = dashboardSection?.querySelector('.dashboard-charts');
        // if (chartsContainer) {
        //     chartsContainer.innerHTML = '<div class="chart-card"><h3>Popular Genres</h3><div class="chart-placeholder">Chart coming soon</div></div>';
        // }
    }

    // ===== Library Rendering =====
    function renderLibrary() {
        const filtered = getFilteredLibrary();
        
        // Update results count
        if (resultsCount) {
            resultsCount.textContent = filtered.length + ' result' + (filtered.length !== 1 ? 's' : '');
        }

        // Update filter chips
        updateFilterChips();

        if (filtered.length === 0) {
            if (libraryGrid) {
                libraryGrid.innerHTML = '<div class="no-results" style="grid-column: 1 / -1;">' +
                    '<div class="no-results-icon">🔍</div>' +
                    '<h3>No items found</h3>' +
                    '<p>Try adjusting your search or filters</p>' +
                    '</div>';
            }
            return;
        }

        const currentViewMode = viewMode ? viewMode.value : 'type-language';
        
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
                const langItems = moviesByLanguage[lang];
                html += '<div class="subsection-header">' + escapeHtml(lang) + '<span class="section-count">(' + langItems.length + ')</span></div>';
                if (document.body.classList.contains('layout-grouped')) {
                    html += '<div class="library-bento grouped">';
                    langItems.forEach(item => { html += renderCard(item); });
                    html += '</div>';
                } else {
                    html += '<div class="library-bento">';
                    langItems.forEach(item => { html += renderCard(item); });
                    html += '</div>';
                }
            });
        }

        // Render Series section
        if (Object.keys(seriesByLanguage).length > 0) {
            html += '<div class="section-header">📺 TV Series</div>';
            Object.keys(seriesByLanguage).sort().forEach(lang => {
                const langItems = seriesByLanguage[lang];
                html += '<div class="subsection-header">' + escapeHtml(lang) + '<span class="section-count">(' + langItems.length + ')</span></div>';
                if (document.body.classList.contains('layout-grouped')) {
                    html += '<div class="library-bento grouped">';
                    langItems.forEach(item => { html += renderCard(item); });
                    html += '</div>';
                } else {
                    html += '<div class="library-bento">';
                    langItems.forEach(item => { html += renderCard(item); });
                    html += '</div>';
                }
            });
        }

        if (libraryGrid) libraryGrid.innerHTML = html;
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
            
            const seenIds = new Set();
            const uniqueItems = itemsByGenre[genre].filter(item => {
                if (seenIds.has(item.id)) return false;
                seenIds.add(item.id);
                return true;
            });

            if (document.body.classList.contains('layout-grouped')) {
                html += '<div class="library-bento grouped">';
                uniqueItems.forEach(item => { html += renderCard(item); });
                html += '</div>';
            } else {
                html += '<div class="library-bento">';
                uniqueItems.forEach(item => { html += renderCard(item); });
                html += '</div>';
            }
        });

        // Render items without genres
        if (noGenreItems.length > 0) {
            html += '<div class="section-header">📋 Other</div>';
            html += '<div class="library-bento">';
            noGenreItems.forEach(item => {
                html += renderCard(item);
            });
            html += '</div>';
        }

        if (libraryGrid) libraryGrid.innerHTML = html;
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
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const statusFilter = filterStatus ? filterStatus.value : 'all';
        const typeFilter = filterType ? filterType.value : 'all';
        const sortValue = sortBy ? sortBy.value : 'id-asc';

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

    /**
     * Determines the visual weight of an item based on its data.
     * @param {Object} item 
     * @returns {string} 'card-hero', 'card-wide', 'card-tall', or 'card-square'
     */
    function getItemVisualWeight(item) {
        // Hero: Exceptional rating (9.0+)
        if (item.rating >= 9.0) return 'card-hero';
        
        // Wide: Series or "Watching" status often fits dashboard style
        if (item.type === 'Series' || item.status === 'Watching') return 'card-wide';
        
        // Tall: Portrait posters work best for standard movies
        if (item.type === 'Movie' && item.rating >= 7.0) return 'card-tall';
        
        // Default: Square for compactness in dense grid
        return 'card-square';
    }

    function renderCard(item) {
        const ratingDisplay = item.rating > 0 ? item.rating.toFixed(1) : 'N/A';
        const genres = item.genres && item.genres.length > 0 ? item.genres.slice(0, 2).join(' • ') : 'General';
        
        // Determine layout class
        const layoutClass = getItemVisualWeight(item);

        // Check internal asset path first (served via asset pipeline)
        // Note: For GitHub Pages or local server, we assume images/{id}.webp exists
        // However, we can't easily check for file existence in client-side JS without a HEAD request or 404 handler.
        // We will default to trying the local path, with fallback to cache/gradient.
        
        const localPosterPath = 'images/' + item.id + '.webp';
        
        // Logic: 
        // 1. Try local path (via background-image, letting browser handle 404 implicitly? No, visual glitch)
        // 2. Fallback to cached OMDB URL?
        // 3. Fallback to gradient.
        
        // Improved: Use an `img` tag for the poster to handle onerror, 
        // OR rely on our posterCache if we haven't run the asset pipeline.
        
        // For this specific 'Mosaic' request, we assume the Asset Pipeline HAS run or will run.
        // We will prioritize the local image.
        
        // Check if we have a cached valid poster URL (remote)
        const remotePosterUrl = posterCache.get(item.id);
        
        // Generate a stable color
        let hash = 0;
        for (let i = 0; i < item.title.length; i++) hash = item.title.charCodeAt(i) + ((hash << 5) - hash);
        const h = Math.abs(hash % 360);
        const gradientStyle = 'background: linear-gradient(135deg, hsl(' + h + ', 60%, 25%) 0%, hsl(' + ((h + 60)%360) + ', 60%, 15%) 100%)';
        
        // We set background-image to local path. If it fails, we need a fallback.
        // CSS multiple backgrounds: url('local'), url('remote'), linear-gradient...
        // Browser uses the first one that works? No, it stacks them.
        
        // Better approach: Set style to local. If we know it might fail, we should use JS image preloading or 
        // just set the background. If 404, it shows nothing? 
        // Let's use the local path if isLocalMode or if we assume assets exist.
        // Let's use the standard `style` attribute stack.
        
        let bgStyle;
        if (remotePosterUrl) {
           // Fallback stack: Local -> Remote -> Gradient
           bgStyle = `background-image: url('${localPosterPath}'), url('${remotePosterUrl}'); background-color: hsl(${h}, 60%, 20%);`;
        } else {
           bgStyle = `background-image: url('${localPosterPath}'); ${gradientStyle}`; 
        }

        // Action buttons
        let actionsHtml = '<div class="card-actions-hover">';
        if (isLocalMode) {
             actionsHtml += '<button class="action-icon" onclick="event.stopPropagation(); app.editItem(' + item.id + ')" title="Edit"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>';
             actionsHtml += '<button class="action-icon" onclick="event.stopPropagation(); app.deleteItem(' + item.id + ')" title="Delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>';
        } else {
             actionsHtml += '<button class="action-icon" onclick="event.stopPropagation(); app.showInfo(' + item.id + ')" title="Info"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg></button>';
        }
        actionsHtml += '</div>';

        return '<div class="item-card ' + layoutClass + '" role="button" tabindex="0" onclick="app.showInfo(' + item.id + ')" onkeypress="if(event.key===\'Enter\' || event.key===\' \'){ event.preventDefault(); app.showInfo(' + item.id + '); }" data-item-id="' + item.id + '">' +
               '<div class="card-poster" style="' + bgStyle + '"></div>' +
               '<div class="card-overlay" aria-hidden="true"></div>' +
               actionsHtml +
               '<div class="card-content">' +
               '<span class="card-title">' + escapeHtml(item.title) + '</span>' +
               '<div class="card-meta-row">' +
               '<span>' + escapeHtml(genres) + '</span>' +
               '<span><span class="card-rating-star">★</span> ' + ratingDisplay + '</span>' +
               '</div>' +
               '</div>' + // Close content
               '</div>'; // Close card
    }

    // ===== CRUD Operations =====
    function openAddModal() {
        editingId = null;
        if (modalTitle) modalTitle.textContent = 'Add Item';
        if (formTitle) formTitle.value = '';
        if (formType) formType.value = 'Movie';
        if (formStatus) formStatus.value = 'Plan to Watch';
        if (formLanguage) formLanguage.value = 'English';
        if (formRating) formRating.value = '0';
        if (formGenres) formGenres.value = '';
        if (formImdbId) formImdbId.value = '';
        if (formTags) formTags.value = '';
        if (itemModal) itemModal.style.display = 'flex';
    }

    function openEditModal(id) {
        const item = library.find(i => i.id === id);
        if (!item) return;
        editingId = id;
        if (modalTitle) modalTitle.textContent = 'Edit Item';
        if (formTitle) formTitle.value = item.title;
        if (formType) formType.value = item.type;
        if (formStatus) formStatus.value = item.status;
        if (formLanguage) formLanguage.value = item.language || 'English';
        if (formRating) formRating.value = item.rating;
        if (formGenres) formGenres.value = (item.genres || []).join(', ');
        if (formImdbId) formImdbId.value = item.imdbID || '';
        if (formTags) formTags.value = (item.tags || []).join(', ');
        if (itemModal) itemModal.style.display = 'flex';
    }

    function closeModal() {
        if (itemModal) itemModal.style.display = 'none';
        editingId = null;
    }

    async function saveItem(e) {
        e.preventDefault();
        if (!isLocalMode) return;

        const tags = formTags ? formTags.value
            .split(',')
            .map(t => t.trim())
            .filter(t => t.length > 0) : [];

        const genres = formGenres ? formGenres.value
            .split(',')
            .map(t => t.trim())
            .filter(t => t.length > 0)
            .slice(0, 3) : [];

        const itemData = {
            title: formTitle ? formTitle.value.trim() : '',
            type: formType ? formType.value : 'Movie',
            status: formStatus ? formStatus.value : 'Plan to Watch',
            language: formLanguage ? formLanguage.value : 'English',
            rating: formRating ? parseFloat(formRating.value) || 0 : 0,
            genres: genres,
            imdbID: formImdbId ? formImdbId.value.trim() || null : null,
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

        if (recModalTitle) recModalTitle.textContent = '🔍 ' + item.title;
        const linksHtml = buildLinksHtml(item.title, item.imdbID || null);

        if (isLocalMode && recContent) {
            recContent.innerHTML = '<p class="loading">Fetching information from IMDb, Rotten Tomatoes, Metacritic...</p>' + linksHtml;
            if (recModal) recModal.style.display = 'flex';

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
            if (recContent) {
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
            }
            if (recModal) recModal.style.display = 'flex';
        }
    }

    function renderRecommendations(data, title, itemImdbID) {
        let html = '';
        let imdbID = itemImdbID || null;

        if (data.omdb) {
            const o = data.omdb;
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
        if (recContent) recContent.innerHTML = html;
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
        if (recModal) recModal.style.display = 'none';
    }

    // ===== Event Binding =====
    function bindEvents() {
        if (searchInput) searchInput.addEventListener('input', renderLibrary);
        if (filterStatus) filterStatus.addEventListener('change', renderLibrary);
        if (filterType) filterType.addEventListener('change', renderLibrary);
        if (sortBy) sortBy.addEventListener('change', renderLibrary);
        if (viewMode) viewMode.addEventListener('change', renderLibrary);
        if (addItemBtn) addItemBtn.addEventListener('click', openAddModal);
        if (filterToggleBtn) {
            filterToggleBtn.addEventListener('click', function () {
                if (filterPanel) {
                    filterPanel.style.display = filterPanel.style.display === 'none' ? 'block' : 'none';
                }
            });
        }
        if (modalClose) modalClose.addEventListener('click', closeModal);
        if (formCancel) formCancel.addEventListener('click', closeModal);
        if (itemForm) itemForm.addEventListener('submit', saveItem);
        if (recModalClose) recModalClose.addEventListener('click', closeRecModal);
        if (layoutToggleBtn) layoutToggleBtn.addEventListener('click', cycleLayout);

        // Keyboard shortcut: press 'l' to cycle layout when not typing
        document.addEventListener('keydown', function (e) {
            if ((e.key === 'l' || e.key === 'L') && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)) {
                cycleLayout();
            }
        });

        // Close modals on overlay click
        document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
            overlay.addEventListener('click', function () {
                if (itemModal) itemModal.style.display = 'none';
                if (recModal) recModal.style.display = 'none';
                editingId = null;
            });
        });
    }

    function loadLayoutMode() {
        const mode = localStorage.getItem('layoutMode') || 'compact';
        setLayoutMode(mode);
    }

    function setLayoutMode(mode) {
        document.body.classList.remove('layout-compact','layout-grouped');
        document.body.classList.add('layout-' + mode);
        if (layoutToggleBtn) {
            layoutToggleBtn.textContent = mode === 'compact' ? '🔎 Compact' : '📚 Grouped';
            layoutToggleBtn.setAttribute('aria-pressed', mode);
        }
        localStorage.setItem('layoutMode', mode);
    }

    function cycleLayout() {
        const order = ['compact','grouped'];
        const current = document.body.classList.contains('layout-grouped') ? 'grouped' : 'compact';
        const next = order[(order.indexOf(current)+1) % order.length];
        setLayoutMode(next);
        renderLibrary(); // Re-render to apply layout changes
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
        showInfo: showInfo,
        removeChip: removeChip
    };

    // Boot
    document.addEventListener('DOMContentLoaded', init);
})();
