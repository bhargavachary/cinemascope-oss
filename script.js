/* --- 1. Environment & Setup --- */
// Check if running locally (localhost or IP) vs GitHub Pages
const isLocal = ['localhost', '127.0.0.1', ''].includes(window.location.hostname);
if (isLocal) {
    document.getElementById('local-controls').classList.remove('hidden');
}

/* --- 2. Data Parsing & Enrichment --- */
const rawDataString = `
1	Breaking Bad	Series	9.5	N/A	96%	Watched	IMDb↗
2	Chernobyl	Series	9.3	N/A	—	Watched	IMDb↗
3	The Shawshank Redemption	Movie	9.3	82	89%	Watched	IMDb↗
4	Game of Thrones	Series	9.2	N/A	—	Watched	IMDb↗
5	Daman	Movie	8.8	N/A	—	Plan to Watch	IMDb↗
6	Forrest Gump	Movie	8.8	82	75%	Watched	IMDb↗
7	Severance	Series	8.7	N/A	—	Recommended	IMDb↗
8	Dark	Series	8.7	N/A	—	Recommended	IMDb↗
9	Interstellar	Movie	8.7	74	73%	Watched	IMDb↗
10	12th Fail	Movie	8.7	N/A	91%	Watched	IMDb↗
11	Shōgun	Series	8.6	N/A	—	Recommended	IMDb↗
12	Spirited Away	Movie	8.6	96	96%	Watched	IMDb↗
13	Kaantha	Movie	8.5	N/A	—	Plan to Watch	IMDb↗
14	Freedom at Midnight	Series	8.4	N/A	—	Plan to Watch	IMDb↗
15	Dhurandhar	Movie	8.4	N/A	—	Plan to Watch	IMDb↗
16	Westworld	Series	8.4	N/A	—	Watched	IMDb↗
17	3 Idiots	Movie	8.4	67	100%	Watched	IMDb↗
18	Prison Break	Series	8.3	N/A	—	Watched	IMDb↗
19	Maharaja	Movie	8.3	N/A	83%	Watched	IMDb↗
20	A Beautiful Mind	Movie	8.2	72	74%	Watched	IMDb↗
21	Jurassic Park	Movie	8.2	68	91%	Watched	IMDb↗
22	Die Hard	Movie	8.2	72	94%	Watched	IMDb↗
23	Drishyam	Series	8.2	N/A	78%	Watched	IMDb↗
24	Kantara: Legend Chapter 1	Movie	8.1	N/A	83%	Plan to Watch	IMDb↗
25	Bou Buttu Bhuta	Movie	8.1	N/A	—	Plan to Watch	IMDb↗
26	Article 15	Movie	8.1	N/A	90%	Recommended	IMDb↗
27	Kishkindha Kaandam	Movie	8.0	N/A	—	Recommended	IMDb↗
28	The Night Manager	Series	8.0	N/A	—	Watched	IMDb↗
29	Bramayugam	Movie	7.8	N/A	—	Recommended	IMDb↗
30	Harry Potter Series	Series	7.7	65	80%	Watched	IMDb↗
31	Kohrra	Series	7.5	N/A	—	Recommended	IMDb↗
32	Spider-Man 2	Movie	7.5	83	93%	Watched	IMDb↗
33	Spider-Man	Movie	7.4	73	90%	Watched	IMDb↗
34	Anora	Movie	7.4	91	93%	Watched	IMDb↗
35	Ponman	Movie	7.4	N/A	—	Watched	IMDb↗
36	Mithya	Series	7.3	N/A	—	Plan to Watch	IMDb↗
37	Raat Akeli Hai	Movie	7.2	N/A	100%	Plan to Watch	IMDb↗
38	Ronth	Movie	7.1	N/A	—	Plan to Watch	IMDb↗
39	Sector 36	Movie	7.1	N/A	47%	Recommended	IMDb↗
40	Mirai	Movie	7.0	81	91%	Plan to Watch	IMDb↗
41	Taare Zameen Par	Movie	7.0	N/A	—	Watched	IMDb↗
42	Nishaanchi	Movie	6.9	N/A	—	Watched	IMDb↗
43	Ground Zero	Movie	6.7	N/A	—	Plan to Watch	IMDb↗
44	Pravinkoodu Shappu	Movie	6.6	N/A	—	Plan to Watch	IMDb↗
45	Retro	Movie	6.6	N/A	—	Plan to Watch	IMDb↗
46	Sister Midnight	Movie	5.7	75	98%	Watched	IMDb↗
47	Stolen	Movie	5.5	43	18%	Watched	IMDb↗
48	Haq	Movie	5.2	N/A	—	Watched	IMDb↗
49	Homebound	Movie	4.3	50	67%	Watched	IMDb↗
50	Bison	Movie	—	—	—	Plan to Watch	—
51	Maranamass	Movie	—	—	—	Plan to Watch	—
52	Vash Level 2	Movie	—	—	—	Plan to Watch	—
53	Thalavara	Movie	N/A	N/A	—	Plan to Watch	IMDb↗
54	Madharaasi	Movie	—	—	—	Plan to Watch	—
55	Wall-E	Movie	N/A	N/A	—	Watched	IMDb↗
56	James Bond Movies	Series	—	—	—	Watched	—
57	Dilli Dark	Movie	N/A	N/A	—	Watched	IMDb↗
58	Lokah Ch 1: Chandra	Movie	—	—	—	Watched	—
59	Hrudayapoorvam	Movie	—	—	—	Watched	—
60	Jugnuma: The Fable	Movie	—	—	—	Watched	—
61	Su From So	Movie	N/A	N/A	—	Watched	IMDb↗
62	Sarvam Maya	Movie	N/A	N/A	—	Watched	IMDb↗
63	Aan Paavam Pollathathu	Movie	N/A	N/A	—	Watched	IMDb↗
`;

// Helper: Generate a reliable placeholder poster if API is missing
const getPoster = (title) => {
    const bg = '1a1a1a';
    const color = 'e50914'; // Cinema Red
    return `https://placehold.co/400x600/${bg}/${color}?text=${encodeURIComponent(title)}&font=lora`;
};

const parseData = (raw) => {
    const lines = raw.trim().split('\n');
    return lines.map(line => {
        const parts = line.split('\t');
        const title = parts[1];
        const type = parts[2];
        const rating = parts[3] === '—' || parts[3] === 'N/A' ? 'NR' : parts[3];
        const status = parts[6] || parts[parts.length - 2] || 'Unknown';

        // Hallucinated "Archivist" Metadata
        return {
            id: parts[0],
            title: title,
            type: type,
            rating: rating,
            status: status.trim(),
            poster: getPoster(title),
            backdrop: `https://placehold.co/1200x600/0f0f0f/333?text=${encodeURIComponent(title + " Still")}`,
            synopsis: `An in-depth exploration of the human condition in this defining ${type.toLowerCase()}. The cinematography of ${title} captures the essence of its era.`,
            year: Math.floor(Math.random() * (2024 - 1980) + 1980),
            duration: `${Math.floor(Math.random() * 2) + 1}h ${Math.floor(Math.random() * 59)}m`,
            critics: "A triumph of storytelling. Visuals that haunt you long after the credits roll.",
            awards: Math.random() > 0.5 ? ["Palme d'Or Nominee", "Best Cinematography"] : [],
            festivals: ["Sundance '23", "TIFF '24"]
        };
    });
};

let movies = parseData(rawDataString);
let currentFilter = 'all';

/* --- 3. Rendering Logic (Grid vs List) --- */

const gridEl = document.getElementById('movie-grid');
const listEl = document.getElementById('list-body');
const gridContainer = document.getElementById('movie-grid');
const listContainer = document.getElementById('movie-list');

function render(viewMode = 'grid') {
    const filtered = movies.filter(m => {
        if (currentFilter === 'all') return true;
        if (currentFilter === 'Watched') return m.status === 'Watched';
        if (currentFilter === 'Recommended') return m.status === 'Recommended';
        if (currentFilter === 'Plan to Watch') return m.status === 'Plan to Watch';
        return true;
    });

    if (viewMode === 'grid') {
        gridContainer.classList.remove('hidden');
        listContainer.classList.add('hidden');
        renderGrid(filtered);
    } else {
        gridContainer.classList.add('hidden');
        listContainer.classList.remove('hidden');
        renderList(filtered);
    }
}

function renderGrid(data) {
    gridEl.innerHTML = '';
    data.forEach((m) => {
        const card = document.createElement('article');
        card.className = 'movie-card';
        // Add random delays for the "Living Mosaic" feel
        card.style.animationDelay = `-${Math.random() * 5}s`;

        card.innerHTML = `<img src="${m.poster}" class="poster-img" alt="${m.title}">`;
        card.onclick = () => openModal(m);
        gridEl.appendChild(card);
    });
}

function renderList(data) {
    listEl.innerHTML = '';
    data.forEach(m => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="font-weight:bold; color:white;">${m.title}</td>
            <td>${m.year}</td>
            <td><span class="badge" style="background:#333">${m.type}</span></td>
            <td><i class="fa-solid fa-star" style="color:#e50914"></i> ${m.rating}</td>
            <td>${m.status}</td>
            <td><button class="icon-btn" onclick='openModal(${JSON.stringify(m).replace(/'/g, "&#39;")})'>
                <i class="fa-solid fa-eye"></i>
            </button></td>
        `;
        listEl.appendChild(row);
    });
}

/* --- 4. Sorting Logic --- */
let sortDir = 1;
window.sortTable = (key) => {
    sortDir *= -1;
    movies.sort((a, b) => {
        if (a[key] < b[key]) return -1 * sortDir;
        if (a[key] > b[key]) return 1 * sortDir;
        return 0;
    });
    render(listContainer.classList.contains('hidden') ? 'grid' : 'list');
};

/* --- 5. Archivist Modal --- */
const modal = document.getElementById('movie-modal');

function openModal(movie) {
    // If passed as object from grid, use it. If string ID, find it.
    const m = (typeof movie === 'string') ? movies.find(x => x.id === movie) : movie;
    if (!m) return;

    document.getElementById('modal-title').innerText = m.title;
    document.getElementById('modal-rating').innerText = m.rating;
    document.getElementById('modal-year').innerText = m.year;
    document.getElementById('modal-type').innerText = m.type;
    document.getElementById('modal-duration').innerText = m.duration;
    document.getElementById('modal-synopsis').innerText = m.synopsis;
    document.getElementById('modal-critics').innerText = m.critics;
    document.getElementById('modal-status').innerText = m.status;
    document.getElementById('modal-backdrop-img').src = m.backdrop;

    // Awards
    const awardsContainer = document.getElementById('modal-awards');
    awardsContainer.innerHTML = m.awards.length
        ? m.awards.map(a => `<span class="award-pill"><i class="fa-solid fa-trophy"></i> ${a}</span>`).join('')
        : '<span style="color:#666">No major awards recorded.</span>';

    // Festivals
    const festContainer = document.getElementById('modal-festivals');
    festContainer.innerHTML = m.festivals.map(f => `<li>${f}</li>`).join('');

    modal.classList.add('open');
}

document.querySelector('.close-modal').addEventListener('click', () => {
    modal.classList.remove('open');
});

// Close modal on backdrop click
modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('open');
});

/* --- 6. Event Listeners --- */

// View Toggles
document.getElementById('view-grid').addEventListener('click', function () {
    this.classList.add('active');
    document.getElementById('view-list').classList.remove('active');
    render('grid');
});

document.getElementById('view-list').addEventListener('click', function () {
    this.classList.add('active');
    document.getElementById('view-grid').classList.remove('active');
    render('list');
});

// Filters
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        currentFilter = e.target.dataset.filter;
        const mode = listContainer.classList.contains('hidden') ? 'grid' : 'list';
        render(mode);
    });
});

// Theme Toggle
document.getElementById('theme-toggle').addEventListener('click', () => {
    const current = document.body.getAttribute('data-theme');
    document.body.setAttribute('data-theme', current === 'light' ? 'dark' : 'light');
    const icon = document.querySelector('#theme-toggle i');
    icon.classList.toggle('fa-sun');
    icon.classList.toggle('fa-moon');
});

// Edit Mode (Only for Localhost)
if (isLocal) {
    document.getElementById('edit-mode-btn').addEventListener('click', () => {
        alert("Edit functionality active. (Simulated for Demo)");
        // Logic to switch to editable table rows would go here
    });
}

// Initial Render
render('grid');
