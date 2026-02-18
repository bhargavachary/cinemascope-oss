/* --- 1. Data Ingestion & Parsing --- */

// The raw string provided in the prompt
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

// Helper: Hallucinate images based on title keywords to ensure high fidelity demo
const getImage = (title, type) => {
    const keyword = title.split(' ')[0];
    const category = type === 'Series' ? 'tv' : 'movie';
    // Using Unsplash Source for persistent demo images
    return `https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=500&q=80&txt=${keyword}`;
};

const parseData = (raw) => {
    const lines = raw.trim().split('\n');
    return lines.map(line => {
        // Splitting by tabs based on the visual structure of the prompt copy-paste
        const parts = line.split('\t');
        // Handle varied line lengths/formats gracefully
        const id = parts[0];
        const title = parts[1];
        const type = parts[2];
        const rating = parts[3] === '—' || parts[3] === 'N/A' ? 'NR' : parts[3];
        const status = parts[6] || parts[parts.length - 2]; // Fallback for messier lines
        
        return {
            id,
            title,
            type,
            rating,
            status: status?.trim(),
            // Hallucinated Data for the "Next Gen" feel
            poster: `https://placehold.co/400x600/1a1a1a/FFF?text=${encodeURIComponent(title)}`, 
            backdrop: `https://placehold.co/1200x600/111/333?text=${encodeURIComponent(title + " Backdrop")}`,
            synopsis: `A gripping ${type.toLowerCase()} that explores the depths of human emotion in ${title}. A must-watch masterpiece.`,
            year: Math.floor(Math.random() * (2024 - 1990) + 1990),
            duration: `${Math.floor(Math.random() * 2) + 1}h ${Math.floor(Math.random() * 59)}m`
        };
    });
};

let movies = parseData(rawDataString);
let currentEditId = null;

/* --- 2. Core Rendering --- */

const grid = document.getElementById('movie-grid');

function renderCards(filter = 'all') {
    grid.innerHTML = '';
    
    const filteredMovies = filter === 'all' 
        ? movies 
        : movies.filter(m => {
            if(filter === 'Recommended') return m.status === 'Recommended';
            if(filter === 'Watched') return m.status === 'Watched';
            return m.type === filter;
        });

    filteredMovies.forEach(movie => {
        const card = document.createElement('article');
        card.className = 'movie-card';
        card.setAttribute('data-id', movie.id);
        
        card.innerHTML = `
            <img src="${movie.poster}" class="poster-img" alt="${movie.title}" loading="lazy">
            <div class="card-overlay">
                <h3 class="card-title">${movie.title}</h3>
                <div class="card-meta">
                    <span class="rating-badge">${movie.rating}</span>
                    <span>${movie.type}</span>
                </div>
                <button class="quick-book" onclick="openModal('${movie.id}')">
                    <i class="fa-solid fa-ticket"></i> Get Tickets
                </button>
            </div>
        `;
        
        // Add Physics
        card.addEventListener('mousemove', handleTilt);
        card.addEventListener('mouseleave', resetTilt);
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.quick-book')) openModal(movie.id);
        });

        grid.appendChild(card);
    });
}

/* --- 3. Physics / Micro-interactions --- */

function handleTilt(e) {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Calculate rotation range (-15 to 15 deg)
    const xRot = -((y - rect.height/2) / rect.height) * 15;
    const yRot = ((x - rect.width/2) / rect.width) * 15;
    
    card.style.transform = `perspective(1000px) rotateX(${xRot}deg) rotateY(${yRot}deg) scale3d(1.02, 1.02, 1.02)`;
}

function resetTilt(e) {
    e.currentTarget.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
}

/* --- 4. Modal & Booking System --- */

const modal = document.getElementById('movie-modal');
const closeModalBtn = document.querySelector('.close-modal');

function openModal(id) {
    const movie = movies.find(m => m.id === id);
    if(!movie) return;

    // Populate Modal
    document.getElementById('modal-title').innerText = movie.title;
    document.getElementById('modal-rating').innerText = movie.rating;
    document.getElementById('modal-year').innerText = movie.year;
    document.getElementById('modal-genre').innerText = movie.type;
    document.getElementById('modal-duration').innerText = movie.duration;
    document.getElementById('modal-desc').innerText = movie.synopsis;
    document.getElementById('modal-backdrop-img').src = movie.backdrop;

    // Randomize Occupancy
    const occupancy = Math.floor(Math.random() * (90 - 40) + 40);
    document.getElementById('occupancy-fill').style.width = `${occupancy}%`;

    // Hallucinate Cast
    const castContainer = document.getElementById('modal-cast');
    castContainer.innerHTML = '';
    for(let i=0; i<6; i++) {
        castContainer.innerHTML += `
            <div class="cast-member">
                <img src="https://i.pravatar.cc/150?img=${i + 10}" class="cast-avatar" alt="Actor">
                <div style="font-size:0.7rem; color:#aaa;">Actor ${i+1}</div>
            </div>
        `;
    }

    // Reset Booking View
    document.querySelector('.seat-map-view').classList.add('hidden');
    document.querySelector('.success-view').classList.add('hidden');
    document.querySelector('.modal-body').classList.remove('hidden');

    // Generate Showtimes
    const times = ['10:30 AM', '1:15 PM', '4:45 PM', '8:00 PM'];
    const timeContainer = document.getElementById('showtimes-container');
    timeContainer.innerHTML = '';
    times.forEach(t => {
        timeContainer.innerHTML += `<span class="showtime-chip" onclick="selectTime(this)">${t}</span>`;
    });

    modal.classList.add('open');
}

closeModalBtn.addEventListener('click', () => {
    modal.classList.remove('open');
});

// Showtimes
window.selectTime = function(el) {
    document.querySelectorAll('.showtime-chip').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
}

// Booking Flow
document.getElementById('start-booking-btn').addEventListener('click', () => {
    document.querySelector('.modal-body').classList.add('hidden'); // actually hide main body via css or scroll
    // Better UX: Overlay the seat map
    document.querySelector('.seat-map-view').classList.remove('hidden');
    generateSeats();
});

function generateSeats() {
    const seatGrid = document.getElementById('seats-grid');
    seatGrid.innerHTML = '';
    let price = 0;
    
    // 64 Seats
    for(let i=0; i<64; i++) {
        const seat = document.createElement('div');
        seat.className = 'seat';
        
        // Randomly book some
        if(Math.random() < 0.3) {
            seat.classList.add('booked');
        } else {
            seat.addEventListener('click', () => {
                if(seat.classList.contains('selected')) {
                    seat.classList.remove('selected');
                    price -= 12;
                } else {
                    seat.classList.add('selected');
                    price += 12;
                }
                document.getElementById('total-price').innerText = price;
            });
        }
        seatGrid.appendChild(seat);
    }
}

document.getElementById('confirm-booking').addEventListener('click', () => {
    document.querySelector('.seat-map-view').classList.add('hidden');
    document.querySelector('.success-view').classList.remove('hidden');
});

/* --- 5. Filters & Edit Mode Features --- */

// Filter Logic
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        renderCards(e.target.dataset.filter);
    });
});

// Theme Toggle
document.getElementById('theme-toggle').addEventListener('click', () => {
    const body = document.body;
    const current = body.getAttribute('data-theme');
    body.setAttribute('data-theme', current === 'light' ? 'dark' : 'light');
    const icon = document.querySelector('#theme-toggle i');
    icon.classList.toggle('fa-sun');
    icon.classList.toggle('fa-moon');
});

/* --- 6. Edit/Import/Export System --- */

const editBtn = document.getElementById('edit-mode-btn');
const tableContainer = document.getElementById('edit-table-container');
const gridContainer = document.getElementById('movie-grid');

let editMode = false;

editBtn.addEventListener('click', () => {
    editMode = !editMode;
    if(editMode) {
        editBtn.style.background = 'var(--primary)';
        editBtn.style.color = 'white';
        gridContainer.classList.add('hidden');
        tableContainer.classList.remove('hidden');
        renderEditTable();
    } else {
        editBtn.style.background = 'transparent';
        editBtn.style.color = 'var(--primary)';
        gridContainer.classList.remove('hidden');
        tableContainer.classList.add('hidden');
        renderCards(); // Re-render grid with updates
    }
});

function renderEditTable() {
    const tbody = document.getElementById('edit-table-body');
    tbody.innerHTML = '';
    movies.forEach((m, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input class="edit-input" value="${m.title}" onchange="updateMovie(${index}, 'title', this.value)"></td>
            <td><input class="edit-input" value="${m.type}" onchange="updateMovie(${index}, 'type', this.value)"></td>
            <td><input class="edit-input" value="${m.rating}" onchange="updateMovie(${index}, 'rating', this.value)"></td>
            <td><input class="edit-input" value="${m.status}" onchange="updateMovie(${index}, 'status', this.value)"></td>
            <td><button class="icon-btn" onclick="deleteMovie(${index})"><i class="fa-solid fa-trash"></i></button></td>
        `;
        tbody.appendChild(row);
    });
}

window.updateMovie = (index, field, value) => {
    movies[index][field] = value;
    // Local persistence could be added here: localStorage.setItem('movies', JSON.stringify(movies));
};

window.deleteMovie = (index) => {
    movies.splice(index, 1);
    renderEditTable();
};

// Export to CSV
document.getElementById('export-btn').addEventListener('click', () => {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "ID,Title,Type,Rating,Status\n";
    
    movies.forEach(m => {
        csvContent += `${m.id},${m.title},${m.type},${m.rating},${m.status}\n`;
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "cinemascope_data.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

// Import CSV
document.getElementById('import-file').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();
    
    reader.onload = function(evt) {
        const text = evt.target.result;
        // Simple CSV parser
        const rows = text.split('\n').slice(1); // skip header
        const newMovies = rows.filter(r => r).map(row => {
            const cols = row.split(',');
            return {
                id: cols[0],
                title: cols[1],
                type: cols[2],
                rating: cols[3],
                status: cols[4],
                poster: `https://placehold.co/400x600/1a1a1a/FFF?text=${encodeURIComponent(cols[1])}`,
                backdrop: `https://placehold.co/1200x600/111/333?text=${encodeURIComponent(cols[1])}`,
                synopsis: "Imported movie.",
                year: "2024",
                duration: "2h"
            };
        });
        
        movies = newMovies;
        if(editMode) renderEditTable();
        else renderCards();
        alert(`Imported ${newMovies.length} titles.`);
    };
    
    reader.readAsText(file);
});

// Init
renderCards();
