/**
 * Cinemascope — Application Logic
 * ─────────────────────────────────
 * Unified controller for Table + Mosaic views.
 * Loads data from assets/manifest.json, applies local overrides,
 * and renders to whichever view is active.
 *
 * Design principles:
 *   • Single source of truth for state
 *   • Pure render functions (state → DOM)
 *   • Debounced search
 *   • Stagger animations via CSS animation-delay
 *   • Keyboard-accessible modals
 */
(function () {
    'use strict';

    /* ═══════════════════════════════════════════════════
       STATE
       ═══════════════════════════════════════════════════ */
    let allItems = [];
    let activeStatus = 'all';
    let activeType   = 'all';
    let activeSort   = 'imdb_rating';
    let searchQuery  = '';
    let currentView  = localStorage.getItem('cinemascope-view') || 'table';
    let currentItem  = null;
    const isLocal    = ['localhost', '127.0.0.1', '0.0.0.0'].includes(location.hostname);

    /* ═══════════════════════════════════════════════════
       DOM REFS  (resolved once on boot)
       ═══════════════════════════════════════════════════ */
    const $ = (s) => document.querySelector(s);
    const $$ = (s) => document.querySelectorAll(s);

    const dom = {
        statsSummary:  $('#stats-summary'),
        viewToggle:    $('#view-toggle'),
        viewIcon:      $('#view-toggle-icon'),
        viewLabel:     $('#view-toggle-label'),
        sortSelect:    $('#sort-select'),
        searchInput:   $('#search-input'),
        resultsCount:  $('#results-count'),
        tableView:     $('#table-view'),
        tableBody:     $('#table-body'),
        mosaicView:    $('#mosaic-view'),
        emptyState:    $('#empty-state'),
        modalBackdrop: $('#modal-backdrop'),
        modalClose:    $('#modal-close'),
        modalPoster:   $('#modal-poster'),
        modalTitle:    $('#modal-title'),
        modalSubtitle: $('#modal-subtitle'),
        modalMeta:     $('#modal-meta'),
        modalPlot:     $('#modal-plot'),
        modalLinks:    $('#modal-links'),
        adminRefresh:  $('#admin-refresh'),
    };

    /* ═══════════════════════════════════════════════════
       BOOT
       ═══════════════════════════════════════════════════ */
    document.addEventListener('DOMContentLoaded', boot);

    async function boot() {
        applyView(currentView);
        bindEvents();
        try {
            const resp = await fetch('assets/manifest.json');
            if (!resp.ok) throw new Error('Manifest not found');
            const raw = await resp.json();
            const checked = await checkPosters(raw);
            allItems = applyOverrides(checked);
            renderStats();
            render();
        } catch (err) {
            console.error('Boot error:', err);
            showEmpty();
        }
    }

    /* ═══════════════════════════════════════════════════
       DATA HELPERS
       ═══════════════════════════════════════════════════ */
    function getOverrides() {
        try { return JSON.parse(localStorage.getItem('metadata_overrides_v1') || '{}'); }
        catch { return {}; }
    }

    function applyOverrides(items) {
        const ov = getOverrides();
        return items.map(item => {
            const o = ov[item.title];
            return o ? Object.assign({}, item, o) : item;
        });
    }

    async function checkPosters(items) {
        const results = await Promise.allSettled(
            items.map(item => {
                const url = 'assets/posters/' + item.src;
                return fetch(url, { method: 'HEAD' })
                    .then(r => { item.has_poster = r.ok; return item; })
                    .catch(() => { item.has_poster = false; return item; });
            })
        );
        return results.map(r => r.value || r.reason);
    }

    /* ═══════════════════════════════════════════════════
       FILTER + SORT
       ═══════════════════════════════════════════════════ */
    function getFiltered() {
        return allItems.filter(item => {
            if (activeStatus !== 'all' && item.status !== activeStatus) return false;
            if (activeType !== 'all' && item.type !== activeType) return false;
            if (searchQuery && !item.title.toLowerCase().includes(searchQuery)) return false;
            return true;
        });
    }

    function applySorted(items) {
        const list = items.slice();
        const num = v => {
            if (!v) return -1;
            if (typeof v === 'number') return v;
            const s = String(v).replace('%', '');
            return parseFloat(s) || -1;
        };
        switch (activeSort) {
            case 'title':
                list.sort((a, b) => a.title.localeCompare(b.title));
                break;
            case 'imdb_rating':
                list.sort((a, b) => num(b.imdb_rating) - num(a.imdb_rating));
                break;
            case 'metascore':
                list.sort((a, b) => num(b.metascore) - num(a.metascore));
                break;
            case 'rotten_tomatoes':
                list.sort((a, b) => num(b.rotten_tomatoes) - num(a.rotten_tomatoes));
                break;
            case 'status':
                list.sort((a, b) => a.status.localeCompare(b.status));
                break;
        }
        // Push items without posters to end
        const withPoster = list.filter(i => i.has_poster);
        const noPoster   = list.filter(i => !i.has_poster);
        return withPoster.concat(noPoster);
    }

    /* ═══════════════════════════════════════════════════
       RENDER ORCHESTRATOR
       ═══════════════════════════════════════════════════ */
    function render() {
        const filtered = applySorted(getFiltered());
        dom.resultsCount.textContent = filtered.length + ' shown';

        if (filtered.length === 0) {
            showEmpty();
            return;
        }
        hideEmpty();

        if (currentView === 'table') {
            renderTable(filtered);
        } else {
            renderMosaic(filtered);
        }
    }

    function showEmpty() {
        dom.tableView.style.display = 'none';
        dom.mosaicView.style.display = 'none';
        dom.emptyState.style.display = 'block';
    }

    function hideEmpty() {
        dom.emptyState.style.display = 'none';
        if (currentView === 'table') {
            dom.tableView.style.display = '';
            dom.mosaicView.style.display = 'none';
        } else {
            dom.tableView.style.display = 'none';
            dom.mosaicView.style.display = '';
        }
    }

    /* ═══════════════════════════════════════════════════
       TABLE RENDERER
       ═══════════════════════════════════════════════════ */
    function renderTable(items) {
        const frag = document.createDocumentFragment();

        items.forEach((item, idx) => {
            const tr = document.createElement('tr');

            // Rating color class
            const imdbVal = parseFloat(item.imdb_rating) || 0;
            const ratingClass = imdbVal >= 8 ? 'rating-high' : imdbVal >= 6 ? 'rating-mid' : 'rating-low';

            // Status class
            const statusKey = item.status === 'Watched' ? 's-watched'
                            : item.status === 'Recommended' ? 's-recommended'
                            : 's-planned';

            const imdbLink = item.imdb_id
                ? '<a href="https://www.imdb.com/title/' + esc(item.imdb_id) + '" target="_blank" rel="noopener">IMDb↗</a>'
                : '—';

            tr.innerHTML =
                '<td class="col-num">' + (idx + 1) + '</td>' +
                '<td class="col-title"><button class="table-title" data-idx="' + idx + '">' + esc(item.title) + '</button></td>' +
                '<td class="col-type hide-sm">' + esc(item.type) + '</td>' +
                '<td class="col-rating rating-cell ' + ratingClass + '">' + (item.imdb_rating || '—') + '</td>' +
                '<td class="col-meta hide-md">' + (item.metascore || '—') + '</td>' +
                '<td class="col-rt hide-md">' + (item.rotten_tomatoes || '—') + '</td>' +
                '<td class="col-status"><span class="table-status ' + statusKey + '">' + esc(item.status) + '</span></td>' +
                '<td class="col-link hide-sm">' + imdbLink + '</td>';

            frag.appendChild(tr);
        });

        dom.tableBody.innerHTML = '';
        dom.tableBody.appendChild(frag);

        // Bind title clicks
        dom.tableBody.querySelectorAll('.table-title').forEach(btn => {
            btn.addEventListener('click', () => {
                const i = parseInt(btn.dataset.idx, 10);
                openModal(items[i]);
            });
        });
    }

    /* ═══════════════════════════════════════════════════
       MOSAIC RENDERER
       ═══════════════════════════════════════════════════ */
    function renderMosaic(items) {
        const frag = document.createDocumentFragment();
        const staggerCap = 40; // max delay items

        items.forEach((item, idx) => {
            const card = document.createElement('div');
            card.className = 'card';
            card.setAttribute('role', 'button');
            card.setAttribute('tabindex', '0');
            if (idx < staggerCap) {
                card.style.animationDelay = (idx * 30) + 'ms';
            }

            const statusKey = item.status === 'Watched' ? 's-watched'
                            : item.status === 'Recommended' ? 's-recommended'
                            : 's-planned';

            const meta = [item.language, item.type].filter(Boolean).join(' · ');
            const year = item.year ? ' (' + item.year + ')' : '';
            const ratingStr = item.imdb_rating ? '⭐ ' + item.imdb_rating : '';

            const img = document.createElement('img');
            img.alt = item.title;
            img.loading = idx < 12 ? 'eager' : 'lazy';
            img.width = item.width || 300;
            img.height = item.height || 450;
            if (item.has_poster) {
                img.src = 'assets/posters/' + item.src;
            } else {
                // Generate gradient placeholder
                let h = 0;
                for (let c = 0; c < item.title.length; c++) h = item.title.charCodeAt(c) + ((h << 5) - h);
                h = Math.abs(h % 360);
                img.style.background = 'linear-gradient(135deg, hsl(' + h + ',50%,25%), hsl(' + ((h+80)%360) + ',50%,15%))';
                img.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450"/>';
            }

            const overlay = document.createElement('div');
            overlay.className = 'card-overlay';
            overlay.innerHTML =
                '<span class="card-badge ' + statusKey + '">' + esc(item.status) + '</span>' +
                '<div class="card-info-title">' + esc(item.title) + year + '</div>' +
                '<div class="card-info-meta">' + esc(meta) + '</div>' +
                (ratingStr ? '<div class="card-info-rating">' + ratingStr + '</div>' : '');

            card.appendChild(img);
            card.appendChild(overlay);

            card.addEventListener('click', () => openModal(item));
            card.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    openModal(item);
                }
            });

            frag.appendChild(card);
        });

        dom.mosaicView.innerHTML = '';
        dom.mosaicView.appendChild(frag);
    }

    /* ═══════════════════════════════════════════════════
       STATS
       ═══════════════════════════════════════════════════ */
    function renderStats() {
        const t = allItems.length;
        const w = allItems.filter(i => i.status === 'Watched').length;
        const r = allItems.filter(i => i.status === 'Recommended').length;
        const p = allItems.filter(i => i.status === 'Plan to Watch').length;
        dom.statsSummary.textContent =
            t + ' titles · ' + w + ' watched · ' + r + ' recommended · ' + p + ' planned';
    }

    /* ═══════════════════════════════════════════════════
       VIEW TOGGLE
       ═══════════════════════════════════════════════════ */
    function applyView(view) {
        currentView = view;
        localStorage.setItem('cinemascope-view', view);
        if (view === 'table') {
            dom.viewIcon.textContent = '◫';
            dom.viewLabel.textContent = 'Mosaic';
        } else {
            dom.viewIcon.textContent = '☰';
            dom.viewLabel.textContent = 'Table';
        }
    }

    function toggleView() {
        applyView(currentView === 'table' ? 'mosaic' : 'table');
        render();
    }

    /* ═══════════════════════════════════════════════════
       MODAL
       ═══════════════════════════════════════════════════ */
    function openModal(item) {
        currentItem = item;

        if (item.has_poster) {
            dom.modalPoster.src = 'assets/posters/' + item.src;
        } else {
            dom.modalPoster.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450"/>';
        }
        dom.modalPoster.alt = item.title;
        dom.modalTitle.textContent = item.title;

        const subtitle = [item.year, item.type, item.language].filter(Boolean).join(' · ');
        dom.modalSubtitle.textContent = subtitle;
        dom.modalPlot.textContent = item.plot || 'Plot unavailable.';

        let meta = '';
        meta += '<div><span>Status</span>' + esc(item.status) + '</div>';
        meta += '<div><span>Runtime</span>' + esc(item.runtime || '—') + '</div>';
        meta += '<div><span>IMDb</span>' + esc(item.imdb_rating || '—') + '</div>';
        meta += '<div><span>Metascore</span>' + esc(item.metascore || '—') + '</div>';
        meta += '<div><span>Rotten Tomatoes</span>' + esc(item.rotten_tomatoes || '—') + '</div>';
        meta += '<div><span>Genres</span>' + esc(item.genres && item.genres.length ? item.genres.join(', ') : '—') + '</div>';
        meta += '<div><span>Tags</span>' + esc(item.tags && item.tags.length ? item.tags.join(', ') : '—') + '</div>';
        meta += '<div><span>Streaming</span>' + esc(item.streaming_name || '—') + '</div>';
        dom.modalMeta.innerHTML = meta;

        let links = '';
        if (item.imdb_id) {
            links += '<a href="https://www.imdb.com/title/' + esc(item.imdb_id) + '" target="_blank" rel="noopener">IMDb ↗</a>';
        }
        if (item.streaming_url) {
            links += '<a href="' + esc(item.streaming_url) + '" target="_blank" rel="noopener">' + esc(item.streaming_name || 'Watch') + '</a>';
        }
        if (item.wikipedia) {
            links += '<a href="' + esc(item.wikipedia) + '" target="_blank" rel="noopener">Wikipedia</a>';
        }
        dom.modalLinks.innerHTML = links;

        dom.adminRefresh.style.display = isLocal ? 'inline-flex' : 'none';
        dom.modalBackdrop.classList.add('open');
        dom.modalBackdrop.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        dom.modalBackdrop.classList.remove('open');
        dom.modalBackdrop.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        currentItem = null;
    }

    function refreshMetadata(item) {
        if (!isLocal || !item) return;
        fetch('/api/refresh_metadata/' + item.id, { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (!data || !data.item) return;
                const ov = getOverrides();
                ov[item.title] = Object.assign({}, ov[item.title] || {}, {
                    imdb_id: data.item.imdb_id || data.item.imdbID || item.imdb_id,
                    imdb_rating: data.item.imdb_rating || item.imdb_rating,
                    metascore: data.item.metascore || item.metascore,
                    rotten_tomatoes: data.item.rotten_tomatoes || item.rotten_tomatoes,
                    runtime: data.item.runtime || item.runtime,
                    wikipedia: data.item.wikipedia || item.wikipedia,
                    plot: data.item.plot || item.plot,
                });
                localStorage.setItem('metadata_overrides_v1', JSON.stringify(ov));
                allItems = applyOverrides(allItems);
                render();
                const updated = allItems.find(i => i.title === item.title);
                if (updated) openModal(updated);
            })
            .catch(err => console.warn('Refresh failed:', err));
    }

    /* ═══════════════════════════════════════════════════
       EVENT BINDING
       ═══════════════════════════════════════════════════ */
    function bindEvents() {
        // View toggle
        dom.viewToggle.addEventListener('click', toggleView);

        // Status filters
        $$('[data-status]').forEach(btn => {
            btn.addEventListener('click', () => {
                $$('[data-status]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                activeStatus = btn.dataset.status;
                render();
            });
        });

        // Type filters
        $$('[data-type]').forEach(btn => {
            btn.addEventListener('click', () => {
                $$('[data-type]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                activeType = btn.dataset.type;
                render();
            });
        });

        // Sort
        dom.sortSelect.addEventListener('change', e => {
            activeSort = e.target.value;
            render();
        });

        // Search (debounced)
        let debounceTimer;
        dom.searchInput.addEventListener('input', e => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                searchQuery = e.target.value.toLowerCase().trim();
                render();
            }, 200);
        });

        // Modal close
        dom.modalClose.addEventListener('click', closeModal);
        dom.modalBackdrop.addEventListener('click', e => {
            if (e.target === dom.modalBackdrop) closeModal();
        });
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') closeModal();
        });

        // Admin refresh
        dom.adminRefresh.addEventListener('click', () => {
            if (currentItem) refreshMetadata(currentItem);
        });

        // Keyboard shortcut: 'v' to toggle view (when not focused on input)
        document.addEventListener('keydown', e => {
            if (e.key === 'v' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)) {
                toggleView();
            }
        });
    }

    /* ═══════════════════════════════════════════════════
       UTILITY
       ═══════════════════════════════════════════════════ */
    function esc(text) {
        if (text == null) return '';
        const d = document.createElement('div');
        d.appendChild(document.createTextNode(String(text)));
        return d.innerHTML;
    }

})();
