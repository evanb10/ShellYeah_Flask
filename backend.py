import requests
import random
from itertools import combinations
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

SLEEPER_API_BASE = "https://api.sleeper.app/v1"

# --- API Helper Functions ---

def get_user(username):
    """Gets a user's details by username."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/user/{username}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting user: {e}")
        return None

def get_leagues_for_user(user_id, season):
    """Gets all of a user's leagues for a specific season."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/user/{user_id}/leagues/nba/{season}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting leagues: {e}")
        return []

def get_league_details(league_id):
    """Gets settings and details for a specific league."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting league details: {e}")
        return None

def get_rosters(league_id):
    """Gets all rosters and their records for a league."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting rosters: {e}")
        return []

def get_users_in_league(league_id):
    """Gets all users (for team names) in a league."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting users in league: {e}")
        return []

# --- Lottery Logic ---

def perform_nba_lottery(all_teams_data, odds_map):
    """
    Performs the 4-pick lottery draw.
    all_teams_data: A list of dicts, each representing a team with 'seed', 'team_name', 'is_lottery_eligible'
    odds_map: A dict mapping seed (str) to number of combinations (int) for lottery-eligible teams
    """
    
    # 1. Create the "hat" with 1000 combinations assigned to lottery-eligible teams
    hat = []
    lottery_eligible_teams_map = {team['seed']: team['team_name'] for team in all_teams_data if team['is_lottery_eligible']}

    for seed_str, num_combos in odds_map.items():
        seed_int = int(seed_str)
        if seed_int in lottery_eligible_teams_map:
            team_name = lottery_eligible_teams_map[seed_int]
            hat.extend([{"seed": seed_int, "team_name": team_name}] * num_combos)
    
    # Fill any remaining spots if odds don't sum to 1000 (e.g., fewer lottery teams than 14)
    if len(hat) < 1000:
        hat.extend([{"seed": -1, "team_name": "Re-draw"}] * (1000 - len(hat)))
    
    random.shuffle(hat)

    # 2. Draw the top 4 picks
    winners = []
    drawn_team_names = set()

    while len(winners) < 4:
        potential_winner = random.choice(hat)
        
        if potential_winner["seed"] != -1 and potential_winner["team_name"] not in drawn_team_names:
            winners.append(potential_winner)
            drawn_team_names.add(potential_winner["team_name"])

    # 3. Create the final draft order
    final_order = []
    
    # Add the top 4 picks
    for i, winner in enumerate(winners):
        final_order.append({
            "pick": i + 1,
            "team_name": winner["team_name"],
            "original_seed": winner["seed"]
        })

    # Determine which lottery-eligible teams did NOT win a top 4 pick
    non_winning_lottery_teams = [
        team for team in all_teams_data 
        if team['is_lottery_eligible'] and team['team_name'] not in drawn_team_names
    ]
    # Sort them by their original seed (worst record gets higher pick among these)
    non_winning_lottery_teams.sort(key=lambda x: x["seed"])

    # Add the non-winning lottery teams after the top 4
    for team in non_winning_lottery_teams:
        final_order.append({
            "pick": len(final_order) + 1,
            "team_name": team["team_name"],
            "original_seed": team["seed"]
        })

    # Add the non-lottery eligible teams in their original seeded order
    non_lottery_teams = [
        team for team in all_teams_data 
        if not team['is_lottery_eligible']
    ]
    # These teams maintain their original seed order
    non_lottery_teams.sort(key=lambda x: x["seed"])

    for team in non_lottery_teams:
        final_order.append({
            "pick": len(final_order) + 1,
            "team_name": team["team_name"],
            "original_seed": team["seed"]
        })

    return final_order

# --- Flask Routes ---

@app.route('/')
def serve_index():
    """Serves the main HTML file."""
    return send_from_directory('.', 'index.html')

@app.route('/get_leagues', methods=['POST'])
def handle_get_leagues():
    """
    Endpoint to get a user's leagues.
    Expects JSON: {"username": "...", "season": "2025"}
    """
    data = request.json
    username = data.get('username')
    season = data.get('season', '2025') # Default to 2025

    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = get_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404

    leagues = get_leagues_for_user(user['user_id'], season)
    # Filter for NBA leagues and return relevant info
    nba_leagues = []                                                                                                                                
    for lg in leagues:                                                                                                                              
        if lg['sport'] == 'nba':                                                                                                                    
            avatar_id = lg.get('avatar')                                                                                                            
            avatar_url = f"https://sleepercdn.com/avatars/{avatar_id}" if avatar_id else "https://sleepercdn.com/images/v2/icons/league_avatar.png" 
            nba_leagues.append({                                                                                                                    
                "league_id": lg['league_id'],                                                                                                       
                "name": lg['name'],                                                                                                                 
                "status": lg['status'],                                                                                                             
                "avatar_url": avatar_url                                                                                                            
            })                
    return jsonify(nba_leagues)


@app.route('/get_lottery_teams', methods=['POST'])
def handle_get_lottery_teams():
    """
    Endpoint to get the lottery-eligible teams from a league's previous season.
    Expects JSON: {"league_id": "..."}
    """
    data = request.json
    current_league_id = data.get('league_id')
    if not current_league_id:
        return jsonify({"error": "League ID is required"}), 400

    # 1. Get current league to find previous league ID
    current_league = get_league_details(current_league_id)
    if not current_league:
        return jsonify({"error": "Could not fetch current league details"}), 404
    
    prev_league_id = current_league.get('previous_league_id')
    if not prev_league_id:
        return jsonify({"error": "This league does not have a linked previous season."}), 404
        
    # 2. Get settings (playoff teams) and users (team names) from *previous* league
    prev_league_details = get_league_details(prev_league_id)
    if not prev_league_details:
        return jsonify({"error": "Could not fetch previous league details"}), 404
        
    # Get number of playoff teams. Default to 6 if not set.
    playoff_spots = prev_league_details.get('settings', {}).get('playoff_teams', 6)
    total_teams = prev_league_details.get('total_rosters', 12)
    num_lottery_teams = total_teams - playoff_spots

    # 3. Get user map for team names
    users = get_users_in_league(prev_league_id)
    user_map = {}
    for user in users:
        team_name = user.get('metadata', {}).get('team_name') or user.get('display_name')
        user_map[user['user_id']] = team_name

    # 4. Get rosters and sort them by standings
    rosters = get_rosters(prev_league_id)
    if not rosters:
        return jsonify({"error": "Could not fetch previous league rosters"}), 404

    # Sort by wins (fewest first), then by points for (fewest first as tiebreaker)
    # This determines the regular season standings for non-playoff teams.
    # Note: Sleeper's `pts` is `points for`.
    def get_sort_key(roster):
        wins = roster['settings']['wins']
        # Use a high number for points if 'pts' is missing
        pts = float(roster['settings'].get('pts', 99999)) 
        return (wins, pts)

    rosters.sort(key=get_sort_key)
    
    # 5. Populate all teams data, marking lottery eligibility
    all_teams_data = []
    for i, roster in enumerate(rosters):
        owner_id = roster['owner_id']
        team_name = user_map.get(owner_id, f"Team {owner_id}")
        
        is_lottery_eligible = (i < num_lottery_teams)
        
        all_teams_data.append({
            "seed": i + 1, # Seed 1 is the worst team
            "team_name": team_name,
            "wins": roster['settings']['wins'],
            "losses": roster['settings']['losses'],
            "pts": roster['settings'].get('pts', 'N/A'),
            "is_lottery_eligible": is_lottery_eligible
        })

    if not all_teams_data:
        return jsonify({"error": "No teams found for the previous season."}), 404

    return jsonify({"teams": all_teams_data})


import requests
import random
from itertools import combinations
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

SLEEPER_API_BASE = "https://api.sleeper.app/v1"

# --- API Helper Functions ---

def get_user(username):
    """Gets a user's details by username."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/user/{username}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting user: {e}")
        return None

def get_leagues_for_user(user_id, season):
    """Gets all of a user's leagues for a specific season."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/user/{user_id}/leagues/nba/{season}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting leagues: {e}")
        return []

def get_league_details(league_id):
    """Gets settings and details for a specific league."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting league details: {e}")
        return None

def get_rosters(league_id):
    """Gets all rosters and their records for a league."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting rosters: {e}")
        return []

def get_users_in_league(league_id):
    """Gets all users (for team names) in a league."""
    try:
        response = requests.get(f"{SLEEPER_API_BASE}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting users in league: {e}")
        return []

# --- Lottery Logic ---

def perform_nba_lottery(all_teams_data, odds_map):
    """
    Performs the 4-pick lottery draw.
    all_teams_data: A list of dicts, each representing a team with 'seed', 'team_name', 'is_lottery_eligible'
    odds_map: A dict mapping seed (str) to number of combinations (int) for lottery-eligible teams
    """
    
    # 1. Create the "hat" with 1000 combinations assigned to lottery-eligible teams
    hat = []
    lottery_eligible_teams_map = {team['seed']: team['team_name'] for team in all_teams_data if team['is_lottery_eligible']}

    for seed_str, num_combos in odds_map.items():
        seed_int = int(seed_str)
        if seed_int in lottery_eligible_teams_map:
            team_name = lottery_eligible_teams_map[seed_int]
            hat.extend([{"seed": seed_int, "team_name": team_name}] * num_combos)
    
    # Fill any remaining spots if odds don't sum to 1000 (e.g., fewer lottery teams than 14)
    if len(hat) < 1000:
        hat.extend([{"seed": -1, "team_name": "Re-draw"}] * (1000 - len(hat)))
    
    random.shuffle(hat)

    # 2. Draw the top 4 picks
    winners = []
    drawn_team_names = set()

    while len(winners) < 4:
        potential_winner = random.choice(hat)
        
        if potential_winner["seed"] != -1 and potential_winner["team_name"] not in drawn_team_names:
            winners.append(potential_winner)
            drawn_team_names.add(potential_winner["team_name"])

    # 3. Create the final draft order
    final_order = []
    
    # Add the top 4 picks
    for i, winner in enumerate(winners):
        final_order.append({
            "pick": i + 1,
            "team_name": winner["team_name"],
            "original_seed": winner["seed"]
        })

    # Determine which lottery-eligible teams did NOT win a top 4 pick
    non_winning_lottery_teams = [
        team for team in all_teams_data 
        if team['is_lottery_eligible'] and team['team_name'] not in drawn_team_names
    ]
    # Sort them by their original seed (worst record gets higher pick among these)
    non_winning_lottery_teams.sort(key=lambda x: x["seed"])

    # Add the non-winning lottery teams after the top 4
    for team in non_winning_lottery_teams:
        final_order.append({
            "pick": len(final_order) + 1,
            "team_name": team["team_name"],
            "original_seed": team["seed"]
        })

    # Add the non-lottery eligible teams in their original seeded order
    non_lottery_teams = [
        team for team in all_teams_data 
        if not team['is_lottery_eligible']
    ]
    # These teams maintain their original seed order
    non_lottery_teams.sort(key=lambda x: x["seed"])

    for team in non_lottery_teams:
        final_order.append({
            "pick": len(final_order) + 1,
            "team_name": team["team_name"],
            "original_seed": team["seed"]
        })

    return final_order

# --- Flask Routes ---

@app.route('/')
def serve_index():
    """Serves the main HTML file."""
    return send_from_directory('.', 'index.html')

@app.route('/get_leagues', methods=['POST'])
def handle_get_leagues():
    """
    Endpoint to get a user's leagues.
    Expects JSON: {"username": "...", "season": "2025"}
    """
    data = request.json
    username = data.get('username')
    season = data.get('season', '2025') # Default to 2025

    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = get_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404

    leagues = get_leagues_for_user(user['user_id'], season)
    # Filter for NBA leagues and return relevant info
    nba_leagues = []                                                                                                                                
    for lg in leagues:                                                                                                                              
        if lg['sport'] == 'nba':                                                                                                                    
            avatar_id = lg.get('avatar')                                                                                                            
            avatar_url = f"https://sleepercdn.com/avatars/{avatar_id}" if avatar_id else "https://sleepercdn.com/images/v2/icons/league_avatar.png" 
            nba_leagues.append({                                                                                                                    
                "league_id": lg['league_id'],                                                                                                       
                "name": lg['name'],                                                                                                                 
                "status": lg['status'],                                                                                                             
                "avatar_url": avatar_url                                                                                                            
            })                
    return jsonify(nba_leagues)


@app.route('/get_lottery_teams', methods=['POST'])
def handle_get_lottery_teams():
    """
    Endpoint to get the lottery-eligible teams from a league's previous season.
    Expects JSON: {"league_id": "..."}
    """
    data = request.json
    current_league_id = data.get('league_id')
    if not current_league_id:
        return jsonify({"error": "League ID is required"}), 400

    # 1. Get current league to find previous league ID
    current_league = get_league_details(current_league_id)
    if not current_league:
        return jsonify({"error": "Could not fetch current league details"}), 404
    
    prev_league_id = current_league.get('previous_league_id')
    if not prev_league_id:
        return jsonify({"error": "This league does not have a linked previous season."}), 404
        
    # 2. Get settings (playoff teams) and users (team names) from *previous* league
    prev_league_details = get_league_details(prev_league_id)
    if not prev_league_details:
        return jsonify({"error": "Could not fetch previous league details"}), 404
        
    # Get number of playoff teams. Default to 6 if not set.
    playoff_spots = prev_league_details.get('settings', {}).get('playoff_teams', 6)
    total_teams = prev_league_details.get('total_rosters', 12)
    num_lottery_teams = total_teams - playoff_spots

    # 3. Get user map for team names
    users = get_users_in_league(prev_league_id)
    user_map = {}
    for user in users:
        team_name = user.get('metadata', {}).get('team_name') or user.get('display_name')
        user_map[user['user_id']] = team_name

    # 4. Get rosters and sort them by standings
    rosters = get_rosters(prev_league_id)
    if not rosters:
        return jsonify({"error": "Could not fetch previous league rosters"}), 404

    # Sort by wins (fewest first), then by points for (fewest first as tiebreaker)
    # This determines the regular season standings for non-playoff teams.
    # Note: Sleeper's `pts` is `points for`.
    def get_sort_key(roster):
        wins = roster['settings']['wins']
        # Use a high number for points if 'pts' is missing
        pts = float(roster['settings'].get('pts', 99999)) 
        return (wins, pts)

    rosters.sort(key=get_sort_key)
    
    # 5. Populate all teams data, marking lottery eligibility
    all_teams_data = []
    for i, roster in enumerate(rosters):
        owner_id = roster['owner_id']
        team_name = user_map.get(owner_id, f"Team {owner_id}")
        
        is_lottery_eligible = (i < num_lottery_teams)
        
        all_teams_data.append({
            "seed": i + 1, # Seed 1 is the worst team
            "team_name": team_name,
            "wins": roster['settings']['wins'],
            "losses": roster['settings']['losses'],
            "pts": roster['settings'].get('pts', 'N/A'),
            "is_lottery_eligible": is_lottery_eligible
        })

    if not all_teams_data:
        return jsonify({"error": "No teams found for the previous season."}), 404

    return jsonify({"teams": all_teams_data})


@app.route('/run_lottery', methods=['POST'])
def handle_run_lottery():
    """
    Runs the lottery simulation.
    Expects JSON: {
        "teams": [{"seed": 1, "team_name": "Team A", "is_lottery_eligible": true}, ...],
        "odds": {"1": 140, "2": 140, ...}
    }
    """
    data = request.json
    teams = data.get('teams') # This will now be all_teams_data
    odds_map = data.get('odds')

    if not teams or not odds_map:
        return jsonify({"error": "Missing teams or odds data"}), 400

    # The perform_nba_lottery function now expects the full list of teams
    final_order = perform_nba_lottery(teams, odds_map)
    
    return jsonify(final_order)

# --- Main ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)

# --- Main ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)