const API_URL = ''; // Relative path
let currentMode = 'lottery';
let activeLeagueId = null;
let lotteryTeams = [];
let finalDraftOrder = [];
let fetchedLeaguesCache = null;
let currentAnalyticsData = []; // Store analytics data for drill-down
let activeRosterData = [];
let sortState = { column: 'name', direction: 'asc' };

// DOM Shortcuts
const dom = {
    loading: document.getElementById('loading-indicator'),
    error: document.getElementById('error-message'),
    step1: document.getElementById('step-1-username'),
    step2: document.getElementById('step-2-leagues'),
    lotteryCont: document.getElementById('lottery-container'),
    analyticsCont: document.getElementById('analytics-container'),
    analyticsDash: document.getElementById('analytics-dashboard'),
    tradesCont: document.getElementById('trades-container'),
    tradesDash: document.getElementById('trades-dashboard'),
    tradesList: document.getElementById('trades-list'),
    setupSec: document.getElementById('step-3-setup'),
    resultsSec: document.getElementById('step-4-results'),
    leaguesList: document.getElementById('leagues-list'),
    teamsTable: document.getElementById('lottery-teams-table'),
    analyticsTable: document.getElementById('analytics-table'),
    resultsGrid: document.getElementById('results-grid'),
    oddsCounter: document.getElementById('odds-counter'),
    usernameIn: document.getElementById('username-input'),
    seasonIn: document.getElementById('season-input'),
    oddsPreset: document.getElementById('odds-preset'),
    revealBtn: document.getElementById('reveal-picks-btn'),
    navLottery: document.getElementById('nav-lottery'),
    navAnalytics: document.getElementById('nav-analytics'),
    navTrades: document.getElementById('nav-trades'),
    userDisplay: document.getElementById('user-display'),
    currentUserSpan: document.getElementById('current-user-span'),
    logoutBtn: document.getElementById('logout-btn'),
    navLogoutBtn: document.getElementById('nav-logout-btn'),
    helpModal: document.getElementById('help-modal'),
    helpContent: document.getElementById('help-content'),
    // Team Details View Shortcuts
    teamDetailsView: document.getElementById('team-details-view'),
    teamHeaderInfo: document.getElementById('team-header-info'),
    statAvgPts: document.getElementById('stat-avg-pts'),
    statTotalPts: document.getElementById('stat-total-pts'),
    statAvgAge: document.getElementById('stat-avg-age'),
    statRosterSize: document.getElementById('stat-roster-size'),
    teamViewRoster: document.getElementById('team-view-roster'),
    // Player Details View Shortcuts
    playerDetailsView: document.getElementById('player-details-view'),
    playerName: document.getElementById('player-name'),
    playerMeta: document.getElementById('player-meta'),
    playerHeight: document.getElementById('player-height'),
    playerWeight: document.getElementById('player-weight'),
    playerAge: document.getElementById('player-age'),
    playerExp: document.getElementById('player-exp'),
    playerInitials: document.getElementById('player-initials'),
    playerNumberBg: document.getElementById('player-number-bg'),
    statusIndicator: document.getElementById('status-indicator'),
    injuryDetail: document.getElementById('injury-detail'),
    injuryNotes: document.getElementById('injury-notes'),
    newsLink: document.getElementById('news-link')
};

const ODDS_PRESETS = { 
    "nba-2025": { 
        "6": { 1: 190, 2: 190, 3: 190, 4: 170, 5: 140, 6: 120 }, // 14 Teams (6 Eligible)
        "4": { 1: 255, 2: 255, 3: 255, 4: 235 },                 // 10/12 Teams (4 Eligible)
        "2": { 1: 500, 2: 500 },                                 // 8 Teams (2 Eligible)
        "default": { 1: 250, 2: 250, 3: 250, 4: 250 }            // Fallback
    } 
};

// --- Initialization ---
window.onload = () => {
    const savedUser = localStorage.getItem('shell_username');
    if (savedUser) {
        dom.usernameIn.value = savedUser;
        dom.currentUserSpan.textContent = savedUser;
        dom.userDisplay.classList.remove('hidden');
        if (dom.navLogoutBtn) dom.navLogoutBtn.classList.remove('hidden');
        fetchLeagues();
    }
};

function handleLogout() {
    localStorage.removeItem('shell_username');
    location.reload();
}

dom.logoutBtn.onclick = handleLogout;
if (dom.navLogoutBtn) dom.navLogoutBtn.onclick = handleLogout;

// --- Help System Logic ---
function openHelp() {
    let content = "";
    
    // Logic to determine current "Screen" based on visibility
    if (!dom.step1.classList.contains('hidden')) {
        content = `
            <h4 class="text-xl font-bold text-white mb-2">Step 1: Login</h4>
            <p>Enter your <strong>Sleeper Username</strong> to get started.</p>
            <p class="mt-2 text-sm text-emerald-300">We'll fetch all your leagues automatically. Make sure the Season year matches your league settings!</p>
        `;
    } else if (!dom.step2.classList.contains('hidden')) {
        content = `
            <h4 class="text-xl font-bold text-white mb-2">Step 2: Select League</h4>
            <p>Choose which league you want to manage.</p>
            <p class="mt-2 text-sm text-emerald-300">Use the toggle at the top right to switch between <strong>Lottery Mode</strong> (for draft simulation), <strong>Analytics Mode</strong> (for stats), and <strong>Trades Mode</strong> (for history).</p>
        `;
    } else if (!dom.analyticsDash.classList.contains('hidden')) {
        content = `
            <h4 class="text-xl font-bold text-white mb-2">Analytics Dashboard</h4>
            <p>View stats for every team in your league.</p>
            <p class="mt-2"><strong>Click on any team</strong> to view their full roster and detailed breakdown.</p>
        `;
    } else if (!dom.tradesDash.classList.contains('hidden')) {
        content = `
            <h4 class="text-xl font-bold text-white mb-2">Trade Tracker</h4>
            <p>Review all completed trades in your league for the selected season.</p>
            <p class="mt-2 text-sm text-emerald-300">We analyze transaction logs to show who moved where.</p>
        `;
    } else if (!dom.teamDetailsView.classList.contains('hidden')) {
        content = `
            <h4 class="text-xl font-bold text-white mb-2">Team Details</h4>
            <p>Deep dive into a specific team's roster.</p>
            <p class="mt-2 text-sm text-emerald-300">Check average ages, positions, and NBA team affiliations. Click a player to see their status.</p>
        `;
    } else if (!dom.playerDetailsView.classList.contains('hidden')) {
        content = `
            <h4 class="text-xl font-bold text-white mb-2">Player Bio</h4>
            <p>View individual player stats, physical profile, and injury reports.</p>
            <p class="mt-2 text-sm text-emerald-300">Use the 'Search Recent News' button to find the latest updates online.</p>
        `;
    } else if (!dom.setupSec.classList.contains('hidden')) {
        content = `
            <h4 class="text-xl font-bold text-white mb-2">Lottery Setup</h4>
            <p>Configure the odds for your draft lottery.</p>
            <ul class="list-disc list-inside mt-2 text-sm text-emerald-300 space-y-1">
                <li><strong>Preset:</strong> Use 'NBA 2025' for weighted odds or 'Flat' for equal odds.</li>
                <li><strong>Total:</strong> Must equal exactly 1000 combinations to run.</li>
            </ul>
        `;
    } else if (!dom.resultsSec.classList.contains('hidden')) {
        content = `
            <h4 class="text-xl font-bold text-white mb-2">Lottery Results</h4>
            <p>It's time to find out who gets the #1 pick!</p>
            <p class="mt-2 text-sm text-emerald-300">Click the <strong>Reveal Picks</strong> button to auto-reveal picks 5-14. Then, manually click the top 4 cards for maximum suspense!</p>
        `;
    } else {
        content = "<p>Welcome to ShellYeah! Navigate using the buttons on screen.</p>";
    }

    dom.helpContent.innerHTML = content;
    dom.helpModal.classList.remove('hidden');
}

function closeHelp() {
    dom.helpModal.classList.add('hidden');
}

// --- Team Details Drill-Down ---
function hideTeamDetails() {
    dom.teamDetailsView.classList.add('hidden');
    dom.analyticsDash.classList.remove('hidden');
    window.scrollTo(0, 0);
}

function showTeamDetails(teamIndex) {
    const team = currentAnalyticsData[teamIndex];
    if (!team) return;

    // 1. Populate Header
    const avatarHtml = team.avatar 
        ? `<img src="${team.avatar}" class="w-16 h-16 rounded-full border-4 border-orange-500 shadow-lg">` 
        : `<div class="w-16 h-16 rounded-full border-4 border-orange-500 bg-emerald-900 flex items-center justify-center text-2xl shadow-lg">🐢</div>`;
    
    dom.teamHeaderInfo.innerHTML = `
        ${avatarHtml}
        <div>
            <h2 class="text-3xl font-black text-white leading-none brand-font">${team.team_name}</h2>
            <p class="text-emerald-400 font-mono font-bold mt-1">${team.wins}W - ${team.losses}L</p>
        </div>
    `;

    // 2. Populate Stats Grid
    dom.statAvgPts.textContent = team.avg_fpts_week;
    dom.statTotalPts.textContent = team.total_fpts;
    dom.statAvgAge.textContent = team.avg_age;
    dom.statRosterSize.textContent = team.roster_size;

    // 3. Setup and Render Roster
    activeRosterData = team.roster_details ? [...team.roster_details] : [];
    
    // Default Sort: Name Ascending
    sortState = { column: 'name', direction: 'asc' };
    activeRosterData.sort((a, b) => a.name.localeCompare(b.name));
    
    renderRosterTable();

    // 4. Switch Views
    dom.analyticsDash.classList.add('hidden');
    dom.teamDetailsView.classList.remove('hidden');
    window.scrollTo(0, 0);
}

function renderRosterTable() {
    let tableRows = '';
    if (activeRosterData && activeRosterData.length > 0) {
        activeRosterData.forEach(p => {
            tableRows += `
                <tr class="hover:bg-emerald-700/50 transition last:border-0 cursor-pointer group" onclick="showPlayerDetails('${p.player_id}')">
                    <td class="px-6 py-4 font-bold text-white whitespace-nowrap group-hover:text-orange-300 transition">${p.name}</td>
                    <td class="px-6 py-4 text-center"><span class="pos-badge pos-${p.position}">${p.position}</span></td>
                    <td class="px-6 py-4 text-center text-emerald-300 font-mono">${p.team}</td>
                    <td class="px-6 py-4 text-center text-emerald-400">${p.age}</td>
                </tr>
            `;
        });
    } else {
        tableRows = '<tr><td colspan="4" class="text-center py-8 text-emerald-400 italic">No players found on this roster.</td></tr>';
    }
    dom.teamViewRoster.innerHTML = tableRows;
    updateSortIndicators();
}

function sortRoster(column) {
    // Toggle direction if clicking same column
    if (sortState.column === column) {
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else {
        sortState.column = column;
        sortState.direction = 'asc';
    }

    activeRosterData.sort((a, b) => {
        let valA = a[column];
        let valB = b[column];

        // Special handling for numbers or specific fields
        if (column === 'age') {
            // Handle N/A for age
            const numA = valA === 'N/A' ? -1 : parseFloat(valA);
            const numB = valB === 'N/A' ? -1 : parseFloat(valB);
            // Sort N/A to bottom usually, but let's just sort strictly
            if (numA < numB) return sortState.direction === 'asc' ? -1 : 1;
            if (numA > numB) return sortState.direction === 'asc' ? 1 : -1;
            return 0;
        } 
        
        // Default string sort
        if (valA < valB) return sortState.direction === 'asc' ? -1 : 1;
        if (valA > valB) return sortState.direction === 'asc' ? 1 : -1;
        return 0;
    });

    renderRosterTable();
}

function updateSortIndicators() {
    const cols = ['name', 'position', 'team', 'age'];
    const arrows = { 'asc': '▲', 'desc': '▼' };
    
    cols.forEach(col => {
        const el = document.getElementById(`sort-indicator-${col}`);
        if (el) {
            el.textContent = (sortState.column === col) ? arrows[sortState.direction] : '';
        }
    });
}

// --- Player Details View ---
async function showPlayerDetails(playerId) {
    if (!playerId) return;
    
    const data = await fetchApi('/get_player_details', { player_id: playerId });
    if (!data) return;

    // Populate Basic Info
    dom.playerName.textContent = data.full_name;
    dom.playerMeta.textContent = `${data.team} • #${data.number || '00'} • ${data.position}`;
    
    // Convert height from inches to feet and inches
    let formattedHeight = "N/A";
    if (data.height) {
        const totalInches = parseInt(data.height);
        if (!isNaN(totalInches)) {
            const feet = Math.floor(totalInches / 12);
            const inches = totalInches % 12;
            formattedHeight = `${feet}'${inches}"`;
        }
    }
    dom.playerHeight.textContent = formattedHeight;

    dom.playerWeight.textContent = data.weight ? `${data.weight} lbs` : "N/A";
    dom.playerAge.textContent = data.age || "N/A";
    dom.playerExp.textContent = data.experience ? `${data.experience} Yrs` : "Rookie";
    
    // Generate Initials
    const initials = data.full_name.split(' ').map(n => n[0]).join('').substring(0, 2);
    dom.playerInitials.textContent = initials;
    dom.playerNumberBg.textContent = data.number || "";

    // Status Logic
    const status = data.injury_status || "Active";
    let statusColor = "bg-green-600 text-white";
    let statusText = "ACTIVE";
    
    if (status === "Questionable") { statusColor = "bg-yellow-500 text-emerald-900"; statusText = "QUESTIONABLE"; }
    else if (status === "IR") { statusColor = "bg-red-600 text-white"; statusText = "IR"; }
    else if (status === "Out") { statusColor = "bg-red-600 text-white"; statusText = "OUT"; }
    else if (status === "Doubtful") { statusColor = "bg-orange-500 text-white"; statusText = "DOUBTFUL"; }
    else if (status === "Day-to-Day") { statusColor = "bg-blue-500 text-white"; statusText = "DAY-TO-DAY"; }

    dom.statusIndicator.className = `px-4 py-2 rounded-lg font-bold text-sm uppercase tracking-wide ${statusColor}`;
    dom.statusIndicator.textContent = statusText;

    // Injury Detail
    if (data.injury_body_part || data.injury_notes) {
        dom.injuryDetail.textContent = data.injury_body_part ? `${data.injury_body_part} Issue` : "Undisclosed Injury";
        dom.injuryNotes.textContent = data.injury_notes || "No additional notes provided.";
    } else {
        dom.injuryDetail.textContent = "Healthy";
        dom.injuryNotes.textContent = "Ready to play.";
    }

    // News Link
    dom.newsLink.href = `https://www.google.com/search?q=${encodeURIComponent(data.news_search_query)}&tbm=nws`;

    // Transition View
    dom.teamDetailsView.classList.add('hidden');
    dom.playerDetailsView.classList.remove('hidden');
    window.scrollTo(0, 0);
}

function hidePlayerDetails() {
    dom.playerDetailsView.classList.add('hidden');
    dom.teamDetailsView.classList.remove('hidden');
    window.scrollTo(0, 0);
}

// --- Navigation & State Management ---
function switchMode(mode) {
    currentMode = mode;
    
    // Reset Buttons
    const resetBtn = (el) => {
        el.classList.replace('bg-orange-500', 'text-emerald-200');
        el.classList.replace('text-white', 'hover:bg-emerald-800');
        el.classList.remove('shadow-orange-500/50');
    };
    const activeBtn = (el) => {
        el.classList.replace('text-emerald-200', 'bg-orange-500');
        el.classList.replace('hover:bg-emerald-800', 'text-white');
        el.classList.add('shadow-orange-500/50');
    };

    resetBtn(dom.navLottery);
    resetBtn(dom.navAnalytics);
    resetBtn(dom.navTrades);

    dom.lotteryCont.classList.add('hidden');
    dom.analyticsCont.classList.add('hidden');
    dom.tradesCont.classList.add('hidden');

    if (mode === 'lottery') {
        activeBtn(dom.navLottery);
        dom.lotteryCont.classList.remove('hidden');
    } else if (mode === 'analytics') {
        activeBtn(dom.navAnalytics);
        dom.analyticsCont.classList.remove('hidden');
    } else if (mode === 'trades') {
        activeBtn(dom.navTrades);
        dom.tradesCont.classList.remove('hidden');
    }

    // Ensure we are at the root of the section
    dom.teamDetailsView.classList.add('hidden');
    dom.playerDetailsView.classList.add('hidden'); 
    
    if(mode === 'analytics' && dom.analyticsCont.classList.contains('hidden') === false) {
            dom.analyticsDash.classList.remove('hidden');
    }
        if(mode === 'trades' && dom.tradesCont.classList.contains('hidden') === false) {
            dom.tradesDash.classList.remove('hidden');
    }


    // State Persistence Logic
    if (fetchedLeaguesCache && fetchedLeaguesCache.length > 0) {
        renderLeaguesList(fetchedLeaguesCache);
        dom.step1.classList.add('hidden');
        dom.step2.classList.remove('hidden');
        
        dom.setupSec.classList.add('hidden');
        dom.resultsSec.classList.add('hidden');
        
        if (mode === 'lottery') dom.analyticsDash.classList.add('hidden');
    } else {
        dom.step1.classList.remove('hidden');
        dom.step2.classList.add('hidden');
    }
}

// --- API Utilities ---
function showLoading(show) { dom.loading.classList.toggle('hidden', !show); }
function showError(msg) { 
    dom.error.textContent = "⚠️ " + msg; 
    dom.error.classList.remove('hidden');
    setTimeout(() => dom.error.classList.add('hidden'), 5000);
}
async function fetchApi(ep, body) {
    showLoading(true);
    try {
        const r = await fetch(`${API_URL}${ep}`, {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.error || 'Error');
        return d;
    } catch (e) { showError(e.message); return null; } 
    finally { showLoading(false); }
}

// --- Logic ---
async function fetchLeagues() {
    const username = dom.usernameIn.value;
    if (!username) return;

    localStorage.setItem('shell_username', username);
    dom.currentUserSpan.textContent = username;
    dom.userDisplay.classList.remove('hidden');
    if (dom.navLogoutBtn) dom.navLogoutBtn.classList.remove('hidden');

    const leagues = await fetchApi('/get_leagues', { username: username, season: dom.seasonIn.value });
    
    if (leagues) {
        fetchedLeaguesCache = leagues;
        renderLeaguesList(leagues);
        dom.step1.classList.add('hidden');
        dom.step2.classList.remove('hidden');
    }
}

function renderLeaguesList(leagues) {
    dom.leaguesList.innerHTML = leagues.length ? '' : '<p class="text-emerald-300 italic">No NBA leagues found in the turtle nest.</p>';
    leagues.forEach(l => {
        const btn = document.createElement('button');
        btn.className = "w-full text-left bg-emerald-900/50 hover:bg-emerald-700 p-4 rounded-xl transition mb-2 border-2 border-emerald-600 flex justify-between items-center group";
        
        const avatarHtml = l.avatar 
            ? `<img src="${l.avatar}" class="w-12 h-12 rounded-full border-2 border-orange-500 object-cover mr-4">` 
            : `<div class="w-12 h-12 rounded-full border-2 border-orange-500 bg-emerald-900 flex items-center justify-center text-2xl mr-4">🐢</div>`;
        
        btn.innerHTML = `
            <div class="flex items-center justify-between w-full">
                <div class="flex items-center">
                    ${avatarHtml}
                    <strong class="text-white text-lg group-hover:text-orange-300 transition">${l.name}</strong>
                </div>
                <span class="text-xs bg-emerald-950 px-2 py-1 rounded text-emerald-400 font-mono">${l.status}</span>
            </div>
        `;
        btn.onclick = () => handleSelectLeague(l.league_id);
        dom.leaguesList.appendChild(btn);
    });
}

document.getElementById('find-leagues-btn').onclick = fetchLeagues;

async function handleSelectLeague(id) {
    activeLeagueId = id;
    if (currentMode === 'lottery') {
        const data = await fetchApi('/get_lottery_teams', { league_id: id });
        if (data && data.teams) {
            lotteryTeams = data.teams;
            populateLotteryTable();
            updateOdds();
            dom.setupSec.classList.remove('hidden');
            dom.step2.classList.add('hidden');
        }
    } else if (currentMode === 'analytics') {
        const data = await fetchApi('/get_league_analytics', { league_id: id });
        if (data && data.analytics) {
            currentAnalyticsData = data.analytics; // Store for modal
            renderAnalytics(data.analytics);
            dom.analyticsDash.classList.remove('hidden');
            dom.step2.classList.add('hidden');
        }
    } else if (currentMode === 'trades') {
        // Don't fetch immediately. Let user click Sync.
        // Show dashboard directly
        dom.tradesDash.classList.remove('hidden');
        dom.step2.classList.add('hidden');
        // Clear previous timeline
        document.getElementById('trade-timeline').innerHTML = `
            <div class="text-center text-emerald-500 italic py-10">
                Click "Sync & Analyze" above to load your complete trade history.
            </div>
        `;
    }
}

// --- Trade Analysis Logic ---
document.getElementById('run-trade-analysis-btn').addEventListener('click', handleAnalyzeTrades);

async function handleAnalyzeTrades() {
    const leagueId = activeLeagueId; // Need to capture this
    const username = localStorage.getItem('shell_username');
    
    if (!leagueId || !username) return;

    const btn = document.getElementById('run-trade-analysis-btn');
    const loader = document.getElementById('trade-loading');
    
    btn.classList.add('hidden');
    loader.classList.remove('hidden');

    const data = await fetchApi('/analyze_trades', { league_id: leagueId, username: username });
    
    loader.classList.add('hidden');
    btn.classList.remove('hidden');
    btn.textContent = "Re-Sync Trades";

    if (data && data.trades) {
        renderTradeTimeline(data.trades);
    }
}

function renderTradeTimeline(trades) {
    const container = document.getElementById('trade-timeline');
    if (trades.length === 0) {
        container.innerHTML = '<p class="text-center text-emerald-300 text-lg">No trades found in your history!</p>';
        return;
    }

    let html = '';
    trades.forEach((t, index) => {
        const isLeft = index % 2 === 0;
        const gradeColor = t.net_grade > 0 ? 'text-green-400' : (t.net_grade < 0 ? 'text-red-400' : 'text-gray-400');
        const gradeBg = t.net_grade > 0 ? 'bg-green-900/30 border-green-600' : (t.net_grade < 0 ? 'bg-red-900/30 border-red-600' : 'bg-gray-800 border-gray-600');
        const gradeIcon = t.net_grade > 0 ? '📈' : (t.net_grade < 0 ? '📉' : '⚖️');
        
        // Build Assets Lists
        const buildList = (assets, title) => {
            if (!assets.length) return '';
            return `
                <div class="mb-3">
                    <p class="text-xs font-bold text-emerald-500 uppercase mb-1">${title}</p>
                    ${assets.map(a => `
                        <div class="flex justify-between items-center text-sm bg-black/20 rounded px-2 py-1 mb-1">
                            <span class="text-white">${a.name}</span>
                            <span class="font-mono text-xs text-emerald-400">${a.type === 'player' ? Math.round(a.score) + ' pts' : ''}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        };

        html += `
            <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <!-- Icon -->
                <div class="flex items-center justify-center w-10 h-10 rounded-full border-4 border-emerald-800 bg-emerald-600 text-white shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                    ${gradeIcon}
                </div>
                
                <!-- Card -->
                <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-emerald-900/80 p-6 rounded-xl border-2 border-emerald-700 shadow-xl backdrop-blur-sm hover:border-orange-500 transition transform hover:-translate-y-1">
                    <div class="flex justify-between items-start mb-4 border-b border-emerald-800 pb-2">
                        <div>
                            <span class="font-bold text-white text-lg">${t.date}</span>
                            <span class="text-xs text-emerald-400 block font-mono">Season: ${t.season}</span>
                        </div>
                        <div class="text-right">
                            <div class="font-black text-2xl ${gradeColor} drop-shadow-md">${t.net_grade > 0 ? '+' : ''}${Math.round(t.net_grade)}</div>
                            <span class="text-xs uppercase tracking-widest text-emerald-500 font-bold">Net Value</span>
                        </div>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div class="${t.net_grade > 0 ? 'bg-green-900/20' : ''} rounded p-2">
                            ${buildList(t.received, "Received")}
                        </div>
                        <div class="${t.net_grade < 0 ? 'bg-red-900/20' : ''} rounded p-2">
                            ${buildList(t.sent, "Sent Away")}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderTrades(trades) {
    dom.tradesList.innerHTML = trades.length ? '' : '<p class="text-emerald-300 italic">No trades found for this season.</p>';
    
    trades.forEach(t => {
        const date = new Date(t.timestamp).toLocaleDateString();
        
        let rostersHtml = '';
        t.rosters_involved.forEach(roster => {
            const avatarImg = roster.avatar 
                ? `<img src="${roster.avatar}" class="w-10 h-10 rounded-full border border-orange-500">`
                : `<div class="w-10 h-10 rounded-full bg-emerald-900 border border-orange-500 flex items-center justify-center text-xs font-bold">T${roster.team_name[0]}</div>`;
            
            let itemsHtml = '';
            
            // Players
            if (roster.received_players.length > 0) {
                itemsHtml += `<div class="mb-2"><p class="text-xs font-bold text-emerald-400 uppercase mb-1">Received Players</p>`;
                roster.received_players.forEach(p => {
                    itemsHtml += `
                        <div class="flex items-center gap-2 mb-1 bg-emerald-900/50 p-1 rounded">
                            <span class="pos-badge pos-${p.position}">${p.position}</span>
                            <span class="text-white font-bold text-sm">${p.name}</span>
                        </div>`;
                });
                itemsHtml += `</div>`;
            }
            
            // Picks
            if (roster.received_picks.length > 0) {
                itemsHtml += `<div class="mb-2"><p class="text-xs font-bold text-emerald-400 uppercase mb-1">Received Picks</p>`;
                roster.received_picks.forEach(pick => {
                    itemsHtml += `
                        <div class="flex items-center gap-2 mb-1 bg-emerald-900/50 p-1 rounded">
                            <span class="text-orange-400 font-mono text-xs">🎲</span>
                            <span class="text-white font-bold text-sm">${pick.description}</span>
                        </div>`;
                });
                itemsHtml += `</div>`;
            }
            
            if (!itemsHtml) itemsHtml = `<p class="text-gray-500 text-xs italic">Nothing received (maybe FAAB?)</p>`;

            rostersHtml += `
                <div class="flex-1 bg-emerald-900/30 p-4 rounded-xl border border-emerald-700/50">
                    <div class="flex items-center gap-3 mb-3 pb-3 border-b border-emerald-700/30">
                        ${avatarImg}
                        <span class="font-bold text-white">${roster.team_name}</span>
                    </div>
                    <div>${itemsHtml}</div>
                </div>
            `;
        });

        const tradeCard = document.createElement('div');
        tradeCard.className = "bg-emerald-900/50 border-2 border-emerald-700 p-6 rounded-2xl shadow-lg";
        tradeCard.innerHTML = `
            <div class="flex justify-between items-center mb-4">
                <span class="bg-orange-600 text-white text-xs font-bold px-3 py-1 rounded-full shadow-md">TRADE</span>
                <span class="text-emerald-400 text-sm font-mono font-bold">Week ${t.week} • ${date}</span>
            </div>
            <div class="flex flex-col md:flex-row gap-4">
                ${rostersHtml}
            </div>
        `;
        dom.tradesList.appendChild(tradeCard);
    });
}

function renderAnalytics(teams) {
    dom.analyticsTable.innerHTML = '';
    teams.forEach((t, index) => {
        const avatarImg = t.avatar ? `<img src="${t.avatar}" class="team-avatar-sm">` : `<div class="team-avatar-sm bg-emerald-700 inline-flex items-center justify-center text-xs">${t.team_name[0]}</div>`;
        
        let posHtml = '';
        ['PG', 'SG', 'SF', 'PF', 'C'].forEach(p => {
            if (t.positions[p] > 0) posHtml += `<span class="pos-badge pos-${p}">${p}:${t.positions[p]}</span>`;
        });

        const tr = document.createElement('tr');
        tr.className = "hover:bg-emerald-700/50 transition cursor-pointer group border-b border-emerald-800/30";
        tr.onclick = () => showTeamDetails(index); // UPDATED: Call showTeamDetails
        tr.innerHTML = `
            <td class="px-4 py-4 whitespace-nowrap flex items-center group-hover:text-orange-200 transition">${avatarImg} <span class="font-bold text-white">${t.team_name}</span></td>
            <td class="px-4 py-4 whitespace-nowrap font-mono text-emerald-300">${t.wins}-${t.losses}</td>
            <td class="px-4 py-4 whitespace-nowrap"><div class="text-sm font-bold text-white">${t.avg_age} <span class="text-xs text-emerald-400 font-normal">yrs</span></div></td>
            <td class="px-4 py-4 whitespace-nowrap"><div class="text-sm font-bold text-orange-400">${t.avg_fpts_week} <span class="text-xs text-emerald-400 font-normal">pts</span></div></td>
            <td class="px-4 py-4"><div class="flex flex-wrap gap-1">${posHtml}</div></td>
        `;
        dom.analyticsTable.appendChild(tr);
    });
}

dom.oddsPreset.onchange = updateOdds;
function populateLotteryTable() {
    dom.teamsTable.innerHTML = '';
    lotteryTeams.forEach(t => {
        const avatarImg = t.avatar ? `<img src="${t.avatar}" class="team-avatar-sm border-emerald-500">` : '';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="px-4 py-3 font-bold text-emerald-300">#${t.seed}</td>
            <td class="px-4 py-3 flex items-center font-semibold">${avatarImg} ${t.team_name}</td>
            <td class="px-4 py-3 text-emerald-400 font-mono">${t.wins}-${t.losses}</td>
            <td class="px-4 py-3"><input type="number" data-seed="${t.seed}" class="odds-input w-20 bg-emerald-900 text-white p-2 rounded border border-emerald-600 focus:border-orange-500 outline-none text-center font-mono" value="0"></td>
        `;
        dom.teamsTable.appendChild(tr);
    });
    document.querySelectorAll('.odds-input').forEach(i => i.addEventListener('input', calculateTotalOdds));
}

function updateOdds() {
    const preset = dom.oddsPreset.value;
    const inputs = document.querySelectorAll('.odds-input');
    const totalTeams = lotteryTeams.length;
    
    let eligibleCount = 4; // Default
    if (totalTeams === 14) eligibleCount = 6;
    else if (totalTeams === 12 || totalTeams === 10) eligibleCount = 4;
    else if (totalTeams === 8) eligibleCount = 2;

    if (preset === 'flat') {
        const share = Math.floor(1000 / eligibleCount);
        inputs.forEach((inp, i) => { 
            const seed = i + 1;
            if (seed <= eligibleCount) {
                inp.value = (i === 0) ? share + (1000 - (share * eligibleCount)) : share;
            } else {
                inp.value = 0;
            }
        });
    } else {
        const mapData = ODDS_PRESETS['nba-2025'];
        const map = mapData[eligibleCount] || mapData['default'];
        inputs.forEach((inp, i) => {
            const seed = i + 1;
            inp.value = map[seed] || 0;
        });
    }
    calculateTotalOdds();
}

function calculateTotalOdds() {
    let sum = 0;
    document.querySelectorAll('.odds-input').forEach(i => sum += parseInt(i.value) || 0);
    dom.oddsCounter.textContent = `Total: ${sum}/1000`;
    if (sum === 1000) {
        dom.oddsCounter.className = "text-sm font-bold bg-green-600 px-4 py-2 rounded-lg font-mono text-white border border-green-400 shadow-lg shadow-green-900/50";
    } else {
        dom.oddsCounter.className = "text-sm font-bold bg-red-600 px-4 py-2 rounded-lg font-mono text-white border border-red-400";
    }
}

document.getElementById('run-lottery-btn').onclick = async () => {
    const oddsMap = {};
    document.querySelectorAll('.odds-input').forEach(i => oddsMap[i.dataset.seed] = parseInt(i.value)||0);
    const sum = Object.values(oddsMap).reduce((a,b)=>a+b,0);
    if (sum !== 1000 && !confirm(`Odds sum to ${sum}, not 1000. Run anyway?`)) return;
    
    const data = await fetchApi('/run_lottery', { teams: lotteryTeams, odds: oddsMap });
    if (data) {
        finalDraftOrder = data;
        renderResults();
        dom.resultsSec.classList.remove('hidden');
        dom.setupSec.classList.add('hidden');
    }
};

function renderResults() {
    dom.resultsGrid.innerHTML = '';
    dom.revealBtn.classList.remove('hidden');
    dom.revealBtn.disabled = false;
    finalDraftOrder.sort((a,b) => a.pick - b.pick);
    
    finalDraftOrder.forEach(pick => {
        const isTop4 = pick.pick <= 4;
        const avatarHtml = pick.avatar ? `<img src="${pick.avatar}" class="team-avatar">` : `<div class="team-avatar bg-emerald-200 flex items-center justify-center text-2xl font-bold text-emerald-800">${pick.team_name[0]}</div>`;
        
        const cardHtml = `
            <div class="h-64 card-scene" data-pick-number="${pick.pick}">
                <div class="card ${isTop4 ? '' : 'is-flipped'} cursor-pointer">
                    <!-- FRONT: THE SHELL -->
                    <div class="card-face card-face-front">
                        <div class="text-6xl mb-2 drop-shadow-lg">🐢</div>
                        <span class="text-4xl font-black text-emerald-900 font-mono">#${pick.pick}</span>
                        <span class="text-xs text-emerald-100 mt-2 font-bold tracking-widest">CLICK TO HATCH</span>
                    </div>
                    <!-- BACK: THE REVEAL -->
                    <div class="card-face card-face-back">
                        <span class="text-xs font-black text-orange-600 mb-2 tracking-widest">PICK #${pick.pick}</span>
                        ${avatarHtml}
                        <span class="text-lg font-bold text-center px-2 leading-tight text-gray-800 brand-font">${pick.team_name}</span>
                        <span class="text-xs text-gray-500 mt-2 font-mono">Seed: ${pick.original_seed} • Odds: ${pick.final_odds}/1000</span>
                    </div>
                </div>
            </div>`;
        dom.resultsGrid.innerHTML += cardHtml;
    });

    document.querySelectorAll('.card-scene').forEach(scene => {
        if (parseInt(scene.dataset.pickNumber) <= 4) {
            scene.onclick = () => {
                const card = scene.querySelector('.card');
                if (!card.classList.contains('is-flipped')) {
                    card.classList.add('is-flipped');
                    if (scene.dataset.pickNumber === "1") {
                        confetti({ 
                            particleCount: 200, 
                            spread: 100, 
                            origin: { y: 0.6 }, 
                            colors: ['#10b981', '#f97316', '#ffffff'] 
                        });
                    }
                }
            };
        }
    });
}

dom.revealBtn.onclick = async () => {
    dom.revealBtn.disabled = true;
    const picks = finalDraftOrder.filter(p => p.pick > 4).sort((a,b) => b.pick - a.pick);
    for (const p of picks) {
        const card = document.querySelector(`.card-scene[data-pick-number="${p.pick}"] .card`);
        if (card) { card.classList.add('is-flipped'); await new Promise(r => setTimeout(r, 300)); }
    }
    dom.revealBtn.classList.add('hidden');
};

document.getElementById('start-over-btn').onclick = () => {
    switchMode('lottery');
    if (fetchedLeaguesCache) {
        renderLeaguesList(fetchedLeaguesCache);
        dom.step1.classList.add('hidden');
        dom.step2.classList.remove('hidden');
    } else {
        dom.step1.classList.remove('hidden');
        dom.step2.classList.add('hidden');
    }
};

switchMode('lottery');
