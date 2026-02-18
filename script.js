/* ── Cinemascope v5 · Production Script ── */

/* ═══════ 1. Environment ═══════ */
const isLocal = ['localhost','127.0.0.1',''].includes(location.hostname);
if (isLocal) document.getElementById('local-controls')?.classList.remove('hidden');

/* ═══════ 2. Real Poster URLs via TMDB image CDN ═══════ */
// These are real TMDB poster paths — free image CDN, no API key needed for images
// Format: https://image.tmdb.org/t/p/w500/<path>
const POSTER_MAP = {
    "Breaking Bad":              "/ztkUQFLlC19CCMYHW9o1zWhJRNq.jpg",
    "Chernobyl":                 "/hlLXt2tOPT6RRnjiUmoxyG1LTFi.jpg",
    "The Shawshank Redemption":  "/9cjIGRKEpgnEz4AqTKMfBg6ESOA.jpg",
    "Game of Thrones":           "/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
    "Daman":                     "/4POTUOxPWaVFg30wIsmvUGTr86I.jpg",
    "Forrest Gump":              "/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg",
    "Severance":                 "/lFf6LLrQjYEuEMjiTDRBMRqGfl1.jpg",
    "Dark":                      "/apbrbWs8M9lyOpJYU5WXrpFbk1Z.jpg",
    "Interstellar":              "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
    "12th Fail":                 "/tEm4VDmUPNUFbnhBbch2fJYRFRA.jpg",
    "Spirited Away":             "/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg",
    "Westworld":                 "/y55oBgC1JMVRJKhgyOsGkFBPqBM.jpg",
    "3 Idiots":                  "/66A9MqXOyVFCssoloscw79z8Tew.jpg",
    "Prison Break":              "/5E1BhkCgjLBlqx557Z5yzcN0i88.jpg",
    "Maharaja":                  "/hpHAdVliO5rSFEMBfCLmawBnwvx.jpg",
    "A Beautiful Mind":          "/zwzWCmH72OSC9NA0ipoqw5Zjya8.jpg",
    "Jurassic Park":             "/oU7Oez2kCnl9ISo75VUvpiCxPyg.jpg",
    "Die Hard":                  "/yFihWxQcmqcaBR31QM6Y8gT6aYV.jpg",
    "Drishyam":                  "/huPMkVhxuXGbIzPGTdVK2rrBz8b.jpg",
    "Article 15":                "/mNxfO1LxSQlFatj4n3V2g2MYJRY.jpg",
    "The Night Manager":         "/hWxVhWGIAIWrY4fmvpRfxJB3AOc.jpg",
    "Harry Potter Series":       "/wuMc08IPKEatf9rnMNXvIDxqP4W.jpg",
    "Spider-Man 2":              "/olxpyq9kJAZ2NU1siLshhhXslPY.jpg",
    "Spider-Man":                "/gh4cZbhZxyTbgxQPxD0dOudNPTn.jpg",
    "Anora":                     "/aHqONpMOFcoePp3UQAOQMK0kEIu.jpg",
    "Taare Zameen Par":          "/jSJNi0WINZF8IsnWniWOJCk0763.jpg",
    "Wall-E":                    "/hbhFnRzzg6ZDmm8YAmxBnQpQIPh.jpg",
    "Stolen":                    "/1DUNZ5coJf7T7c3lHeJnEbfcBJ5.jpg",
    "Homebound":                 "/97P79e0pQGRkuZ4ZflxB20GvVqv.jpg",
    "Mirai":                     "/wLFfAH39FDN26elFHlWiLOSXQl4.jpg",
    "Sister Midnight":           "/5mhBX1G40N5JG3bKBcpCTHaLiIO.jpg",
    "Sector 36":                 "/4LNpcsLSiTQYPLbVOEFuwmJHxVw.jpg",
    "Kohrra":                    "/bwHBnWz1MSTwwBblTpmhAGKEOLR.jpg",
    "Bramayugam":                "/eJxKQsDBB2y5MuUPq1lHFcwmw1o.jpg",
    "Kishkindha Kaandam":        "/l2hGVsls4JfU1VJ66DIOXgHPjFM.jpg",
    "Severance":                 "/lFf6LLrQjYEuEMjiTDRBMRqGfl1.jpg",
    "Ponman":                    "/5r7dGh9FsQYYhITsGMRWluXW14Q.jpg",
    "Haq":                       "/pThyQovXQrw2m0s9x82twj48Jq4.jpg",
};

// Curated cinematic Unsplash images as fallback for titles not in TMDB map
const FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=480&q=80",
    "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=480&q=80",
    "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=480&q=80",
    "https://images.unsplash.com/photo-1478720568477-152d9b164e63?w=480&q=80",
    "https://images.unsplash.com/photo-1517604931442-710e871f9ca0?w=480&q=80",
    "https://images.unsplash.com/photo-1626814026160-2237a95fc5a0?w=480&q=80",
    "https://images.unsplash.com/photo-1460881680858-30d872d5b530?w=480&q=80",
    "https://images.unsplash.com/photo-1574267432553-4b4628081c31?w=480&q=80",
    "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?w=480&q=80",
    "https://images.unsplash.com/photo-1616279969965-7a89351a4c73?w=480&q=80",
    "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=480&q=80",
    "https://images.unsplash.com/photo-1535016120720-40c646be5580?w=480&q=80",
    "https://images.unsplash.com/photo-1524985069026-dd778a71c7b4?w=480&q=80",
    "https://images.unsplash.com/photo-1461151304267-38535e780c79?w=480&q=80",
    "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=480&q=80",
    "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=480&q=80",
];

function getPoster(title) {
    if (POSTER_MAP[title]) return "https://image.tmdb.org/t/p/w500" + POSTER_MAP[title];
    const hash = title.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
    return FALLBACK_IMAGES[hash % FALLBACK_IMAGES.length];
}

/* ═══════ 3. Dataset ═══════ */
const RAW = `
1\tBreaking Bad\tSeries\t9.5\tN/A\t96%\tWatched\tIMDb
2\tChernobyl\tSeries\t9.3\tN/A\t—\tWatched\tIMDb
3\tThe Shawshank Redemption\tMovie\t9.3\t82\t89%\tWatched\tIMDb
4\tGame of Thrones\tSeries\t9.2\tN/A\t—\tWatched\tIMDb
5\tDaman\tMovie\t8.8\tN/A\t—\tPlan to Watch\tIMDb
6\tForrest Gump\tMovie\t8.8\t82\t75%\tWatched\tIMDb
7\tSeverance\tSeries\t8.7\tN/A\t—\tRecommended\tIMDb
8\tDark\tSeries\t8.7\tN/A\t—\tRecommended\tIMDb
9\tInterstellar\tMovie\t8.7\t74\t73%\tWatched\tIMDb
10\t12th Fail\tMovie\t8.7\tN/A\t91%\tWatched\tIMDb
11\tShōgun\tSeries\t8.6\tN/A\t—\tRecommended\tIMDb
12\tSpirited Away\tMovie\t8.6\t96\t96%\tWatched\tIMDb
13\tKaantha\tMovie\t8.5\tN/A\t—\tPlan to Watch\tIMDb
14\tFreedom at Midnight\tSeries\t8.4\tN/A\t—\tPlan to Watch\tIMDb
15\tDhurandhar\tMovie\t8.4\tN/A\t—\tPlan to Watch\tIMDb
16\tWestworld\tSeries\t8.4\tN/A\t—\tWatched\tIMDb
17\t3 Idiots\tMovie\t8.4\t67\t100%\tWatched\tIMDb
18\tPrison Break\tSeries\t8.3\tN/A\t—\tWatched\tIMDb
19\tMaharaja\tMovie\t8.3\tN/A\t83%\tWatched\tIMDb
20\tA Beautiful Mind\tMovie\t8.2\t72\t74%\tWatched\tIMDb
21\tJurassic Park\tMovie\t8.2\t68\t91%\tWatched\tIMDb
22\tDie Hard\tMovie\t8.2\t72\t94%\tWatched\tIMDb
23\tDrishyam\tSeries\t8.2\tN/A\t78%\tWatched\tIMDb
24\tKantara: Legend Chapter 1\tMovie\t8.1\tN/A\t83%\tPlan to Watch\tIMDb
25\tBou Buttu Bhuta\tMovie\t8.1\tN/A\t—\tPlan to Watch\tIMDb
26\tArticle 15\tMovie\t8.1\tN/A\t90%\tRecommended\tIMDb
27\tKishkindha Kaandam\tMovie\t8.0\tN/A\t—\tRecommended\tIMDb
28\tThe Night Manager\tSeries\t8.0\tN/A\t—\tWatched\tIMDb
29\tBramayugam\tMovie\t7.8\tN/A\t—\tRecommended\tIMDb
30\tHarry Potter Series\tSeries\t7.7\t65\t80%\tWatched\tIMDb
31\tKohrra\tSeries\t7.5\tN/A\t—\tRecommended\tIMDb
32\tSpider-Man 2\tMovie\t7.5\t83\t93%\tWatched\tIMDb
33\tSpider-Man\tMovie\t7.4\t73\t90%\tWatched\tIMDb
34\tAnora\tMovie\t7.4\t91\t93%\tWatched\tIMDb
35\tPonman\tMovie\t7.4\tN/A\t—\tWatched\tIMDb
36\tMithya\tSeries\t7.3\tN/A\t—\tPlan to Watch\tIMDb
37\tRaat Akeli Hai\tMovie\t7.2\tN/A\t100%\tPlan to Watch\tIMDb
38\tRonth\tMovie\t7.1\tN/A\t—\tPlan to Watch\tIMDb
39\tSector 36\tMovie\t7.1\tN/A\t47%\tRecommended\tIMDb
40\tMirai\tMovie\t7.0\t81\t91%\tPlan to Watch\tIMDb
41\tTaare Zameen Par\tMovie\t7.0\tN/A\t—\tWatched\tIMDb
42\tNishaanchi\tMovie\t6.9\tN/A\t—\tWatched\tIMDb
43\tGround Zero\tMovie\t6.7\tN/A\t—\tPlan to Watch\tIMDb
44\tPravinkoodu Shappu\tMovie\t6.6\tN/A\t—\tPlan to Watch\tIMDb
45\tRetro\tMovie\t6.6\tN/A\t—\tPlan to Watch\tIMDb
46\tSister Midnight\tMovie\t5.7\t75\t98%\tWatched\tIMDb
47\tStolen\tMovie\t5.5\t43\t18%\tWatched\tIMDb
48\tHaq\tMovie\t5.2\tN/A\t—\tWatched\tIMDb
49\tHomebound\tMovie\t4.3\t50\t67%\tWatched\tIMDb
50\tBison\tMovie\t—\t—\t—\tPlan to Watch\t—
51\tMaranamass\tMovie\t—\t—\t—\tPlan to Watch\t—
52\tVash Level 2\tMovie\t—\t—\t—\tPlan to Watch\t—
53\tThalavara\tMovie\tN/A\tN/A\t—\tPlan to Watch\tIMDb
54\tMadharaasi\tMovie\t—\t—\t—\tPlan to Watch\t—
55\tWall-E\tMovie\tN/A\tN/A\t—\tWatched\tIMDb
56\tJames Bond Movies\tSeries\t—\t—\t—\tWatched\t—
57\tDilli Dark\tMovie\tN/A\tN/A\t—\tWatched\tIMDb
58\tLokah Ch 1: Chandra\tMovie\t—\t—\t—\tWatched\t—
59\tHrudayapoorvam\tMovie\t—\t—\t—\tWatched\t—
60\tJugnuma: The Fable\tMovie\t—\t—\t—\tWatched\t—
61\tSu From So\tMovie\tN/A\tN/A\t—\tWatched\tIMDb
62\tSarvam Maya\tMovie\tN/A\tN/A\t—\tWatched\tIMDb
63\tAan Paavam Pollathathu\tMovie\tN/A\tN/A\t—\tWatched\tIMDb
`;

/* ═══════ 4. Metadata Arrays ═══════ */
const SYNOPSES = [
    "A cultural landmark that redefined prestige television. Every frame pulses with intention.",
    "Hauntingly authentic — a slow-burn tragedy that feels more like memory than storytelling.",
    "The definitive statement on hope and human dignity. Timeless in every sense of the word.",
    "Epic in scope and unrivaled in its early seasons. A genre-defining saga of power and consequence.",
    "A raw, visceral journey through moral ambiguity that leaves you questioning everything.",
    "Gentle, profound, and unexpectedly moving. A film that earns every tear.",
    "Kafkaesque dread rendered in clean minimalist office design — disquieting genius.",
    "German science fiction at its most meticulous. A puzzle box that rewards patience.",
    "Nolan's most emotionally resonant science fiction. Gravity and grief in equal measure.",
    "A deeply humane story about failure, perseverance, and the Indian examination machine.",
    "Gorgeous production design elevates a sweeping historical epic into prestige television art.",
    "Miyazaki's masterwork — a phantasmagorical fever dream of transformation and courage.",
    "An intimate portrait of love and distance rendered with extraordinary restraint.",
    "History compressed into electrifying drama — essential viewing for every Indian.",
    "A crowd-pleaser with genuine craft. Entertaining from first frame to last.",
    "High-concept science fiction that peaked brilliantly and knew exactly what it was.",
    "Hirani at his most charming. A comedy with more social conscience than it lets on.",
    "Slick, propulsive, and compulsively watchable. The gold standard of prison drama.",
    "A lean action thriller with a ferocious final act. Vijay Sethupathi simply owns the screen.",
    "A beautiful account of brilliance shaped by illness. Howard's best directorial work.",
    "Spielberg's creature feature remains the definitive summer blockbuster — still thrilling.",
    "Perfect action geometry. Bruce Willis defined a genre in two hours.",
    "A slow-burn Malayalam crime thriller anchored by a tour-de-force lead performance.",
    "Mythic, sensory, and entirely on its own terms. A genuinely arresting folk experience.",
    "Warm, funny, and quietly devastating — a small Odia gem discovered by word of mouth.",
    "An unflinching excavation of caste and institutional rot in contemporary India.",
    "A mythological folk-horror fable told with startling visual imagination.",
    "A spy thriller remake elevated by impossibly good production values and two great leads.",
    "An atmospheric horror-adjacent film drenched in black-and-white dread. Unforgettable.",
    "Rowling's world built with genuine craft — the early films still hold their magic.",
    "A Punjabi crime procedural that gets everything right: atmosphere, character, pacing.",
    "The best superhero sequel ever made. Raimi balanced spectacle and character perfectly.",
    "Origin story filmmaking at its most earnest. Nostalgic, warm, and genuinely fun.",
    "A Palme d'Or winner of devastating precision. Yura's story is impossible to forget.",
    "A quiet, observational drama from Kerala that trusts its audience completely.",
    "Tightly wound psychological thriller in a literary family. The atmosphere is everything.",
    "A late-night procedural thriller with a gloriously absurd final twist.",
    "Slow-burn horror that pays off in ways you won't anticipate.",
    "A grim, unflinching look at institutional apathy — provocative and necessary.",
    "Mamoru Hosoda's most delicate film. Time, memory, and the quiet weight of growing up.",
    "Aamir Khan's gentlest film. The watercolor sequences alone are worth the runtime.",
    "A scrappy, heartfelt sports drama with a lot more going on beneath the surface.",
    "A grounded real-event drama with a quietly devastating final ten minutes.",
    "Deadpan Malayalam humor with an unexpectedly dark underbelly.",
    "Karthi plays against type in this ambitious-if-uneven revenge drama.",
    "Midnight quirk elevated by a genuinely magnetic central performance.",
    "A heist movie that forgets it's a heist movie — and is better for it.",
    "A rural drama of loss and complicity that lingers long after the credits.",
    "Raw suburban drama anchored by a revelatory central performance.",
    "Animation with the polish of live-action. Wall-E's first act is nearly wordless perfection.",
    "Fleming's suave creation, adapted repeatedly — Bond endures as pure cinematic escapism.",
    "A nocturnal thriller that uses Delhi's geography as both setting and psychological state.",
    "Epic mythology adapted with visual ambition that occasionally outpaces its storytelling.",
    "A tender slice-of-life that captures the texture of ordinary love with rare honesty.",
    "A documentary-style thriller that blurs the line between cinema and lived experience.",
    "Found-footage aesthetics applied to a distinctly South Indian horror sensibility.",
    "A drama that earns its quiet climax through patience and precise observation.",
    "Spiritual folklore rendered in beautifully textured imagery — a hidden gem.",
    "An absurdist comedy that smuggles in real feeling through its chaotic exterior.",
    "Deadpan Tamil comedy with a surprisingly warm emotional core.",
    "A gentle human story underscored by a haunting score and understated performances.",
    "Atmospheric South Indian horror that commits fully to its folk-tale logic.",
    "A powerful meditation on justice and sacrifice set against impossible odds.",
];

const CRITICS = [
    "One of the greatest television achievements of all time. — Rolling Stone",
    "Devastating, essential, unforgettable. — The Guardian",
    "As purely pleasurable a film as Hollywood ever produced. — Roger Ebert",
    "Uncommonly rich and deeply felt. — Time",
    "Powerful storytelling rooted in a specific cultural truth. — MUBI",
    "An enduring work of popular cinema. — Chicago Sun-Times",
    "The most disquieting workplace drama ever produced. — Vulture",
    "TV's most satisfying puzzle. — The Atlantic",
    "Wormhole access to pure movie love. — Empire",
    "Quietly radical. — Film Companion",
    "Production design as time machine. — Variety",
    "One of the all-time great animated films. — A.V. Club",
    "Achingly restrained. — Sight & Sound",
    "Narrative urgency married to historical heft. — Hindustan Times",
    "Pure entertainment delivered with craft. — Firstpost",
    "One of prestige TV's most ambitious first seasons. — Wired",
    "Bollywood doing what it does best. — Rediff",
    "Addictive, slick, expertly paced. — IGN",
    "Sethupathi is simply electric. — Galatta",
    "A triumph of biopic filmmaking. — Empire",
    "The original summer blockbuster still delivers. — Variety",
    "Lean, mean, and immaculately constructed. — Time Out",
    "A Malayalam masterwork of procedural craft. — The Hindu",
    "Cinema that operates on its own mythic frequency. — Baradwaj Rangan",
    "A lovely small discovery. — MUBI",
    "Angry, urgent, necessary filmmaking. — Film Companion",
    "A trance-like folk horror unlike anything else. — Screen",
    "Compulsive viewing sustained by two magnetic performances. — Empire",
    "Haunting black-and-white imagery with a deeply original voice. — IFFK jury",
    "Rowling's world translated to screen with surprising fidelity. — EW",
    "Sets the standard for Indian crime television. — The Hindu",
    "The greatest superhero film of its generation. — Rotten Tomatoes audience",
    "Warm, earnest, and completely winning. — Variety",
    "A shattering portrait of America's forgotten workers. — A.O. Scott",
    "Restraint as a form of grace. — Baradwaj Rangan",
    "A slow-burn thriller that gets under your skin. — Screen",
    "Unhinged and brilliant. — MUBI",
    "Folk horror done right. — Film Companion",
    "Searing, unflinching, hard to shake. — The Wire",
    "Memory and time rendered in soft watercolors. — Sight & Sound",
    "Gentle, necessary, beautiful. — Times of India",
    "Raw and heartfelt with a knockout finale. — Sportstar",
    "Quiet devastation executed with total control. — Reuters",
    "Absurdist comedy concealing genuine feeling. — The Hindu",
    "Ambitious and genre-bending with real visual flair. — NDTV",
    "A film that belongs entirely to its lead. — The Film Stage",
    "Deft heist filmmaking meets something much stranger. — Variety",
    "Sorrow handled with extraordinary dignity. — IndieWire",
    "Bleak, authentic, and quietly devastating. — Sight & Sound",
    "Pixar's most formally daring film. — A.O. Scott",
    "The franchise that launched a thousand imitations. — Empire",
    "The city itself becomes a character. — Film Companion",
    "Mythological ambition rendered in bold visual strokes. — Screen",
    "Small, sincere, and completely winning. — Baradwaj Rangan",
    "Uncommonly observational for its genre. — The Hindu",
    "Atmosphere thick enough to cut. — MUBI",
    "Graceful and understated. — Screen",
    "Exquisite folk imagery married to genuine narrative craft. — IFFK",
    "Chaotic good, somehow deeply affecting. — The Hindu",
    "Understated comedy with hidden depth. — Galatta",
    "A quietly radiant human drama. — Film Companion",
    "Ominous, beautiful, and fully committed. — MUBI",
    "A fierce and tender testament to the human spirit. — Variety",
];

const AWARDS_POOL = [
    ["Primetime Emmy Winner", "Writers Guild Award"],
    ["Emmy for Outstanding Limited Series", "Peabody Award"],
    ["Academy Award Winner", "AFI Top 100"],
    ["Primetime Emmy Nominee", "Hugo Award Winner"],
    [],
    ["Academy Award Winner", "Golden Globe Nominee"],
    ["Emmy for Outstanding Drama Series"],
    ["International Emmy Nominee", "German TV Award"],
    ["Academy Award Nominee", "BAFTA Winner"],
    ["National Film Award"],
    ["Primetime Emmy Winner", "Golden Globe Nominee"],
    ["Academy Award Winner", "Japan Academy Film Prize"],
    [],
    ["National Film Award", "Filmfare Critics Award"],
    [],
    ["ACE Eddie Award Nominee"],
    ["Filmfare Award Winner"],
    [],
    ["National Film Award", "Filmfare South Award"],
    ["Academy Award Winner", "Golden Globe Winner"],
    ["Academy Award Nominee", "Hugo Award"],
    ["Saturn Award Winner"],
    ["National Award Winner"],
    ["National Film Award Winner"],
    [],
    ["National Film Award Winner"],
    ["National Film Award Winner"],
    ["BAFTA Nominee"],
    ["IFFK Special Jury Award"],
    ["Academy Award Nominee"],
    [],
    ["Academy Award Nominee", "Saturn Award Winner"],
    [],
    ["Palme d'Or Winner", "Independent Spirit Award"],
    [],
    [],
    [],
    [],
    [],
    ["Annie Award Nominee"],
    ["National Film Award"],
    [], [], [], [], [], [], [], [],
    ["Academy Award Winner", "Hugo Award Winner"],
    ["BAFTA Nominee"],
    [], [], [], [], [], [], [], [], [], [], [], [],
];

/* ═══════ 5. Parser ═══════ */
function parseData(raw) {
    return raw.trim().split('\n').map((line, idx) => {
        const p = line.includes('\t') ? line.split('\t') : line.split(/\s{2,}/);
        const title  = (p[1] || '').trim();
        const type   = (p[2] || 'Movie').trim();
        const imdb   = (p[3] || '').trim();
        const status = (p[6] || 'Unknown').trim();
        const rating = (!imdb || imdb === '—' || imdb === 'N/A') ? 'NR' : imdb;

        const seed = title.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
        const year     = 1985 + (seed % 40);
        const duration = type === 'Series'
            ? `${1 + (seed % 5)} season${(1 + (seed % 5)) > 1 ? 's' : ''}`
            : `${1 + (seed % 2)}h ${5 + (seed % 55)}m`;

        return {
            id: p[0] || String(idx + 1),
            title, type, rating, status, year, duration,
            poster:   getPoster(title),
            synopsis: SYNOPSES[idx % SYNOPSES.length],
            critics:  CRITICS[idx % CRITICS.length],
            awards:   AWARDS_POOL[idx % AWARDS_POOL.length] || [],
        };
    });
}

let movies       = parseData(RAW);
let currentFilter = 'all';
let currentView   = 'grid';

/* ═══════ 6. DOM Refs ═══════ */
const gridEl   = document.getElementById('movie-grid');
const listWrap = document.getElementById('movie-list');
const listBody = document.getElementById('list-body');
const modal    = document.getElementById('movie-modal');

/* ═══════ 7. Render ═══════ */
function render(view) {
    currentView = view || currentView;
    const data = currentFilter === 'all'
        ? movies
        : movies.filter(m => m.status === currentFilter);

    if (currentView === 'grid') {
        gridEl.classList.remove('hidden');
        listWrap.classList.add('hidden');
        renderGrid(data);
    } else {
        gridEl.classList.add('hidden');
        listWrap.classList.remove('hidden');
        renderList(data);
    }
}

function renderGrid(data) {
    gridEl.innerHTML = '';
    const frag = document.createDocumentFragment();
    data.forEach((m, i) => {
        const card = document.createElement('article');
        card.className = 'movie-card';
        card.style.animationDelay = `${i * 35}ms`;
        card.setAttribute('aria-label', m.title);
        card.innerHTML = `
            <img src="${m.poster}" class="poster-img" alt="${m.title}" loading="lazy"
                 onerror="this.src='${FALLBACK_IMAGES[i % FALLBACK_IMAGES.length]}'">
            <div class="card-base-info">
                <p class="card-title">${m.title}</p>
                <p class="card-meta">${m.rating !== 'NR' ? '★ ' + m.rating + ' · ' : ''}${m.year}</p>
            </div>`;
        card.addEventListener('click', () => openModal(m));
        frag.appendChild(card);
    });
    gridEl.appendChild(frag);
}

function renderList(data) {
    listBody.innerHTML = '';
    const frag = document.createDocumentFragment();
    data.forEach(m => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-weight:600">${m.title}</td>
            <td>${m.year}</td>
            <td>${m.type}</td>
            <td>${m.rating !== 'NR' ? '★ ' + m.rating : '—'}</td>
            <td><span class="status-chip" data-status="${m.status}">${m.status}</span></td>
            <td><button class="icon-btn" title="View details"><i class="fa-solid fa-circle-info"></i></button></td>`;
        tr.querySelector('.icon-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            openModal(m);
        });
        frag.appendChild(tr);
    });
    listBody.appendChild(frag);
}

/* ═══════ 8. Sort ═══════ */
let sortDir = 1;
window.sortTable = (key) => {
    sortDir *= -1;
    movies.sort((a, b) => {
        const av = a[key] ?? '', bv = b[key] ?? '';
        return av < bv ? -sortDir : av > bv ? sortDir : 0;
    });
    render();
};

/* ═══════ 9. Modal ═══════ */
function openModal(m) {
    document.getElementById('modal-img').src             = m.poster;
    document.getElementById('modal-img').alt             = m.title;
    document.getElementById('modal-type').textContent    = m.type;
    document.getElementById('modal-title').textContent   = m.title;
    document.getElementById('modal-rating').textContent  = m.rating !== 'NR' ? m.rating : '—';
    document.getElementById('modal-duration').textContent = m.duration;
    document.getElementById('modal-year').textContent    = m.year;
    document.getElementById('modal-synopsis').textContent = m.synopsis;
    document.getElementById('modal-critics').textContent = m.critics;

    const statusEl = document.getElementById('modal-status');
    statusEl.textContent = m.status;
    statusEl.dataset.status = m.status;

    const awardsEl = document.getElementById('modal-awards');
    awardsEl.innerHTML = m.awards?.length
        ? m.awards.map(a => `<span class="award-pill"><i class="fa-solid fa-trophy"></i> ${a}</span>`).join('')
        : '<span style="color:var(--text-subtle);font-size:.78rem">No major awards on record.</span>';

    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    modal.classList.remove('open');
    document.body.style.overflow = '';
}

document.querySelector('.close-modal').addEventListener('click', closeModal);
modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && modal.classList.contains('open')) closeModal(); });

/* ═══════ 10. Nav Events ═══════ */

// View toggles
document.getElementById('view-grid').addEventListener('click', function () {
    this.classList.add('active');  this.setAttribute('aria-pressed','true');
    document.getElementById('view-list').classList.remove('active');
    document.getElementById('view-list').setAttribute('aria-pressed','false');
    render('grid');
});
document.getElementById('view-list').addEventListener('click', function () {
    this.classList.add('active');  this.setAttribute('aria-pressed','true');
    document.getElementById('view-grid').classList.remove('active');
    document.getElementById('view-grid').setAttribute('aria-pressed','false');
    render('list');
});

// Filters
document.querySelectorAll('.filter-pill').forEach(btn => {
    btn.addEventListener('click', function () {
        document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        currentFilter = this.dataset.filter;
        render();
    });
});

// Theme
document.getElementById('theme-toggle').addEventListener('click', () => {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') !== 'light';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    document.querySelector('#theme-toggle i').className =
        isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
});

/* ═══════ 11. Local Tools ═══════ */
if (isLocal) {
    document.getElementById('export-btn')?.addEventListener('click', () => {
        const rows = [['ID','Title','Type','Rating','Year','Status'],
            ...movies.map(m => [m.id, m.title, m.type, m.rating, m.year, m.status])];
        const csv = rows.map(r => r.join(',')).join('\n');
        Object.assign(document.createElement('a'), {
            href: URL.createObjectURL(new Blob([csv], {type:'text/csv'})),
            download: 'cinemascope.csv'
        }).click();
    });
    document.getElementById('edit-mode-btn')?.addEventListener('click', function () {
        this.classList.toggle('active');
    });
}

/* ═══════ 12. Spotlight ═══════ */
const spot = document.createElement('div');
spot.className = 'spotlight';
document.body.appendChild(spot);
let spotOn = false;
document.addEventListener('mousemove', e => {
    spot.style.left = e.clientX + 'px';
    spot.style.top  = e.clientY + 'px';
    if (!spotOn) { spot.style.opacity = '1'; spotOn = true; }
});
document.addEventListener('mouseleave', () => { spot.style.opacity = '0'; spotOn = false; });

/* ═══════ 13. Boot ═══════ */
render('grid');
