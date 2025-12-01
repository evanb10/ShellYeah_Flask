import requests
import random
from typing import List, Dict, Any, Optional
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SLEEPER_API_BASE = "https://api.sleeper.app/v1"
SLEEPER_AVATAR_BASE = "https://sleepercdn.com/avatars/thumbs"

# In-memory cache for the heavy players DB
PLAYERS_CACHE = {}

# --- API Helper Functions ---

def get_all_players() -> Dict[str, Any]:
    """
    Fetches all NBA players from Sleeper. 
    Cached in memory because the payload is large (~5MB).
    """
    global PLAYERS_CACHE
    if PLAYERS_CACHE:
        return PLAYERS_CACHE
    
    try:
        print("Fetching all players from Sleeper (this happens once)...")
        response = requests.get(f"{SLEEPER_API_BASE}/players/nba")
        response.raise_for_status()
        PLAYERS_CACHE = response.json()
        print(f"Loaded {len(PLAYERS_CACHE)} players.")
        return PLAYERS_CACHE
    except requests.exceptions.RequestException as e:
        print(f"Error getting players: {e}")
        return {}

def get_user(username: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/user/{username}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting user: {e}")
        return None

def get_leagues_for_user(user_id: str, season: str) -> List[Dict[str, Any]]:
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/user/{user_id}/leagues/nba/{season}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting leagues: {e}")
        return []

def get_league_details(league_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting league details: {e}")
        return None

def get_rosters(league_id: str) -> List[Dict[str, Any]]:
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting rosters: {e}")
        return []

def get_users_in_league(league_id: str) -> List[Dict[str, Any]]:
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting users in league: {e}")
        return []

# --- Lottery Logic ---

def perform_nba_lottery(teams_by_seed: Dict[int, Dict[str, Any]], odds_map: Dict[str, int]) -> List[Dict[str, Any]]:
    hat = []
    for seed_str, num_combos in odds_map.items():
        seed_int = int(seed_str)
        if seed_int in teams_by_seed:
            team_data = teams_by_seed[seed_int]
            hat.extend([{"seed": seed_int, "team_data": team_data}] * num_combos)
    
    if len(hat) < 1000:
        hat.extend([{"seed": -1, "team_data": None}] * (1000 - len(hat)))
    
    random.shuffle(hat)

    winners = []
    drawn_team_ids = set()

    while len(winners) < 4:
        potential_winner = random.choice(hat)
        if potential_winner["seed"] != -1:
            team_name = potential_winner["team_data"]["team_name"]
            if team_name not in drawn_team_ids:
                winners.append(potential_winner)
                drawn_team_ids.add(team_name)

    final_order = []
    for i, winner in enumerate(winners):
        original_seed = winner["seed"]
        final_odds = odds_map.get(str(original_seed), 0)
        final_order.append({
            "pick": i + 1,
            "team_name": winner["team_data"]["team_name"],
            "avatar": winner["team_data"].get("avatar"),
            "original_seed": original_seed,
            "final_odds": final_odds
        })

    remaining_teams = []
    for seed, team_data in teams_by_seed.items():
        if team_data["team_name"] not in drawn_team_ids:
            remaining_teams.append({"seed": seed, "team_data": team_data})
            
    remaining_teams.sort(key=lambda x: x["seed"])
    
    for i, item in enumerate(remaining_teams):
        original_seed = item["seed"]
        final_odds = odds_map.get(str(original_seed), 0)
        final_order.append({
            "pick": 5 + i,
            "team_name": item["team_data"]["team_name"],
            "avatar": item["team_data"].get("avatar"),
            "original_seed": original_seed,
            "final_odds": final_odds
        })

    return final_order

# --- Analytics Logic ---

def calculate_team_analytics(roster: Dict, user_map: Dict, all_players: Dict) -> Dict:
    """Calculates detailed stats for a single roster."""
    
    owner_id = roster['owner_id']
    user_info = user_map.get(owner_id, {"name": f"Team {owner_id}", "avatar": None})
    
    # 1. Basic Team Info
    wins = roster['settings']['wins']
    losses = roster['settings']['losses']
    ties = roster['settings'].get('ties', 0)
    total_games = wins + losses + ties
    total_fpts = float(roster['settings'].get('fpts', 0)) + (float(roster['settings'].get('fpts_decimal', 0)) / 100)
    
    avg_fpts_week = total_fpts / total_games if total_games > 0 else 0
    
    # 2. Player Analysis
    player_ids = roster.get('players', [])
    ages = []
    positions = {"PG": 0, "SG": 0, "SF": 0, "PF": 0, "C": 0, "G": 0, "F": 0}
    roster_details = []
    
    for pid in player_ids:
        if pid in all_players:
            p_data = all_players[pid]
            
            # Age
            age = p_data.get('age')
            if age:
                ages.append(age)
            
            # Positions (Sleeper uses 'fantasy_positions' list, e.g. ["PG", "SG"])
            p_positions = p_data.get('fantasy_positions', [])
            primary_pos = p_positions[0] if p_positions else "UNK"
            
            if p_positions:
                # We count the primary position (first in list) or all? 
                # Let's count all valid occurrences for coverage
                for pos in p_positions:
                    if pos in positions:
                        positions[pos] += 1
            
            roster_details.append({
                "name": f"{p_data.get('first_name', '')} {p_data.get('last_name', '')}".strip(),
                "position": primary_pos,
                "age": age if age else "N/A",
                "team": p_data.get('team') or "FA"
            })

    avg_age = sum(ages) / len(ages) if ages else 0
    
    # "Avg Fantasy PPG / Player" proxy:
    # Since we don't have individual stats easily, we calculate:
    # "Average contribution per roster spot" = Team Avg Weekly Score / Roster Size
    roster_size = len(player_ids)
    avg_ppg_per_player_proxy = avg_fpts_week / roster_size if roster_size > 0 else 0

    return {
        "team_name": user_info["name"],
        "avatar": user_info["avatar"],
        "wins": wins,
        "losses": losses,
        "avg_age": round(avg_age, 1),
        "positions": positions,
        "avg_fpts_week": round(avg_fpts_week, 1),
        "avg_ppg_player": round(avg_ppg_per_player_proxy, 1),
        "total_fpts": round(total_fpts, 1),
        "roster_size": roster_size,
        "roster_details": sorted(roster_details, key=lambda x: x['name'])
    }

# --- Flask Routes ---

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/get_leagues', methods=['POST'])
def handle_get_leagues():
    data = request.json
    username = data.get('username')
    season = data.get('season', '2025')

    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = get_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404

    leagues = get_leagues_for_user(user['user_id'], season)
    nba_leagues = [
        {
            "league_id": lg['league_id'], 
            "name": lg['name'], 
            "status": lg['status'],
            "avatar": f"{SLEEPER_AVATAR_BASE}/{lg['avatar']}" if lg.get('avatar') else None
        }
        for lg in leagues if lg['sport'] == 'nba'
    ]
    return jsonify(nba_leagues)

@app.route('/get_lottery_teams', methods=['POST'])
def handle_get_lottery_teams():
    data = request.json
    current_league_id = data.get('league_id')
    if not current_league_id:
        return jsonify({"error": "League ID is required"}), 400

    # Logic: Get Previous Season -> Get Teams -> Sort by Record
    # REQUIREMENT: The Lottery Simulator must uses the PREVIOUS season's data.
    current_league = get_league_details(current_league_id)
    if not current_league:
        return jsonify({"error": "Could not fetch current league"}), 404
    
    prev_league_id = current_league.get('previous_league_id')
    if not prev_league_id:
        return jsonify({"error": "No previous season found linked to this league."}), 404
        
    prev_league_details = get_league_details(prev_league_id)
    
    users = get_users_in_league(prev_league_id)
    user_map = {}
    for user in users:
        display_name = user.get('metadata', {}).get('team_name') or user.get('display_name')
        avatar_id = user.get('avatar')
        user_map[user['user_id']] = {
            "name": display_name,
            "avatar": f"{SLEEPER_AVATAR_BASE}/{avatar_id}" if avatar_id else None
        }

    rosters = get_rosters(prev_league_id)
    
    # REQUIREMENT: "Random drawing decides who picks first between teams with same record"
    # We shuffle first to randomize ties, then sort by wins to establish the record-based order.
    random.shuffle(rosters)
    rosters.sort(key=lambda r: r['settings']['wins'])
    
    lottery_teams_data = []
    for i, roster in enumerate(rosters):
        user_info = user_map.get(roster['owner_id'], {"name": f"Team {roster['owner_id']}", "avatar": None})
        lottery_teams_data.append({
            "seed": i + 1,
            "team_name": user_info["name"],
            "avatar": user_info["avatar"],
            "wins": roster['settings']['wins'],
            "losses": roster['settings']['losses']
        })

    return jsonify({"teams": lottery_teams_data})

@app.route('/get_league_analytics', methods=['POST'])
def handle_get_analytics():
    """
    New Endpoint: Calculates analytics for ALL teams in the CURRENT selected league.
    REQUIREMENT: Analytics must use the CURRENT season's data.
    """
    data = request.json
    league_id = data.get('league_id')
    if not league_id:
        return jsonify({"error": "League ID is required"}), 400

    # 1. Ensure players are loaded (Lazy Load)
    all_players = get_all_players()
    if not all_players:
        return jsonify({"error": "Could not load player database."}), 500

    # 2. Get League Context
    rosters = get_rosters(league_id)
    users = get_users_in_league(league_id)
    
    # Map Users
    user_map = {}
    for user in users:
        display_name = user.get('metadata', {}).get('team_name') or user.get('display_name')
        avatar_id = user.get('avatar')
        user_map[user['user_id']] = {
            "name": display_name,
            "avatar": f"{SLEEPER_AVATAR_BASE}/{avatar_id}" if avatar_id else None
        }

    # 3. Calculate Analytics for each team
    analytics_data = []
    for roster in rosters:
        # Skip rosters with no owners if necessary, or keep them
        if not roster.get('owner_id'): continue
        
        stats = calculate_team_analytics(roster, user_map, all_players)
        analytics_data.append(stats)

    # Sort by Total FPTS descending by default
    analytics_data.sort(key=lambda x: x['total_fpts'], reverse=True)

    return jsonify({"analytics": analytics_data})

@app.route('/run_lottery', methods=['POST'])
def handle_run_lottery():
    data = request.json
    teams = data.get('teams')
    odds_map = data.get('odds') # {'1': 140, '2': 140, ...} as passed from frontend
    
    # Ensure teams are sorted by seed to match odds_map keys
    teams.sort(key=lambda t: t['seed'])

    # Logic to split odds for tied teams
    # 1. Group teams by record
    groups = []
    if teams:
        current_group = [teams[0]]
        for i in range(1, len(teams)):
            prev = teams[i-1]
            curr = teams[i]
            if prev['wins'] == curr['wins'] and prev['losses'] == curr['losses']:
                current_group.append(curr)
            else:
                groups.append(current_group)
                current_group = [curr]
        groups.append(current_group)

    # 2. Calculate and re-distribute odds for each group
    for group in groups:
        if len(group) > 1:
            # Calculate total odds assigned to these slots by the user
            total_group_odds = 0
            seed_keys = []
            for team in group:
                seed_str = str(team['seed'])
                seed_keys.append(seed_str)
                total_group_odds += int(odds_map.get(seed_str, 0))
            
            # Distribute evenly
            count = len(group)
            base_share = total_group_odds // count
            remainder = total_group_odds % count
            
            # Assign back to odds_map
            # Since teams are sorted by seed, the first team in 'group' has the highest seed (lowest number)
            # and thus gets priority for the remainder, matching the 'random drawing winner' logic.
            for i, team in enumerate(group):
                seed_str = str(team['seed'])
                value = base_share
                if remainder > 0:
                    value += 1
                    remainder -= 1
                odds_map[seed_str] = value

    teams_by_seed = {team['seed']: team for team in teams}
    final_order = perform_nba_lottery(teams_by_seed, odds_map)
    return jsonify(final_order)

if __name__ == '__main__':
    app.run(debug=True, port=5000)