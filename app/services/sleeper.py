import requests
from flask import current_app
from typing import Dict, Any, Optional, List

# In-memory cache for the heavy players DB
PLAYERS_CACHE = {}

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
        # Accessing config via current_app usually requires an app context, 
        # but for simple constants we can also just hardcode or import if we prefer not to use app context here.
        # However, using current_app is more "Flask-way".
        api_base = current_app.config['SLEEPER_API_BASE']
        response = requests.get(f"{api_base}/players/nba")
        response.raise_for_status()
        PLAYERS_CACHE = response.json()
        print(f"Loaded {len(PLAYERS_CACHE)} players.")
        return PLAYERS_CACHE
    except requests.exceptions.RequestException as e:
        print(f"Error getting players: {e}")
        return {}

def get_user(username: str) -> Optional[Dict[str, Any]]:
    try:
        api_base = current_app.config['SLEEPER_API_BASE']
        response = requests.get(f"{api_base}/user/{username}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting user: {e}")
        return None

def get_leagues_for_user(user_id: str, season: str) -> List[Dict[str, Any]]:
    try:
        api_base = current_app.config['SLEEPER_API_BASE']
        response = requests.get(f"{api_base}/user/{user_id}/leagues/nba/{season}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting leagues: {e}")
        return []

def get_league_details(league_id: str) -> Optional[Dict[str, Any]]:
    try:
        api_base = current_app.config['SLEEPER_API_BASE']
        response = requests.get(f"{api_base}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting league details: {e}")
        return None

def get_rosters(league_id: str) -> List[Dict[str, Any]]:
    try:
        api_base = current_app.config['SLEEPER_API_BASE']
        response = requests.get(f"{api_base}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting rosters: {e}")
        return []

def get_users_in_league(league_id: str) -> List[Dict[str, Any]]:
    try:
        api_base = current_app.config['SLEEPER_API_BASE']
        response = requests.get(f"{api_base}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting users in league: {e}")
        return []

def get_transactions(league_id: str, round_num: int) -> List[Dict[str, Any]]:
    try:
        api_base = current_app.config['SLEEPER_API_BASE']
        response = requests.get(f"{api_base}/league/{league_id}/transactions/{round_num}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting transactions for week {round_num}: {e}")
        return []
