from flask import jsonify, request, current_app
from app.api import api_bp
from app.services.sleeper import (
    get_all_players, get_user, get_leagues_for_user, get_league_details, 
    get_rosters, get_users_in_league, get_transactions
)
from app.logic.lottery import perform_nba_lottery, average_tied_odds
from app.logic.analytics import calculate_team_analytics
from app.logic.trade_analyzer import analyze_user_trades, sync_league_history
import random

@api_bp.route('/analyze_trades', methods=['POST'])
def handle_analyze_trades():
    data = request.json
    league_id = data.get('league_id')
    username = data.get('username')
    
    if not league_id or not username:
        return jsonify({"error": "League ID and Username are required"}), 400
        
    user = get_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    try:
        results = analyze_user_trades(user['user_id'], league_id)
        return jsonify({"trades": results})
    except Exception as e:
        print(f"Error analyzing trades: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/get_player_details', methods=['POST'])
def handle_get_player_details():
    data = request.json
    player_id = data.get('player_id')
    
    if not player_id:
        return jsonify({"error": "Player ID is required"}), 400
        
    # Ensure players are loaded
    all_players = get_all_players()
    player = all_players.get(player_id)
    
    if not player:
        return jsonify({"error": "Player not found"}), 404
        
    details = {
        "full_name": f"{player.get('first_name', '')} {player.get('last_name', '')}".strip(),
        "team": player.get('team') or "FA",
        "position": player.get('position'),
        "number": player.get('number'),
        "height": player.get('height'),
        "weight": player.get('weight'),
        "age": player.get('age'),
        "college": player.get('college'),
        "experience": player.get('years_exp'),
        "injury_status": player.get('injury_status'),
        "injury_body_part": player.get('injury_body_part'),
        "injury_notes": player.get('injury_notes'),
        "news_search_query": f"{player.get('first_name', '')} {player.get('last_name', '')} injury news"
    }
    
    return jsonify(details)

@api_bp.route('/get_leagues', methods=['POST'])
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
    avatar_base = current_app.config['SLEEPER_AVATAR_BASE']
    nba_leagues = [
        {
            "league_id": lg['league_id'], 
            "name": lg['name'], 
            "status": lg['status'],
            "avatar": f"{avatar_base}/{lg['avatar']}" if lg.get('avatar') else None
        }
        for lg in leagues if lg['sport'] == 'nba'
    ]
    return jsonify(nba_leagues)

@api_bp.route('/get_lottery_teams', methods=['POST'])
def handle_get_lottery_teams():
    data = request.json
    current_league_id = data.get('league_id')
    if not current_league_id:
        return jsonify({"error": "League ID is required"}), 400

    current_league = get_league_details(current_league_id)
    if not current_league:
        return jsonify({"error": "Could not fetch current league"}), 404
    
    prev_league_id = current_league.get('previous_league_id')
    if not prev_league_id:
        return jsonify({"error": "No previous season found linked to this league."}), 404
        
    # Pull the previous league's details too, so we can resolve division names.
    prev_league = get_league_details(prev_league_id) or {}
    prev_metadata = prev_league.get('metadata', {}) or {}

    def division_name(division_id):
        if division_id is None:
            return None
        return prev_metadata.get(f'division_{division_id}') or f'Division {division_id}'
    
    users = get_users_in_league(prev_league_id)
    avatar_base = current_app.config['SLEEPER_AVATAR_BASE']
    user_map = {}
    for user in users:
        display_name = user.get('metadata', {}).get('team_name') or user.get('display_name')
        avatar_id = user.get('avatar')
        user_map[user['user_id']] = {
            "name": display_name,
            "avatar": f"{avatar_base}/{avatar_id}" if avatar_id else None
        }

    rosters = get_rosters(prev_league_id)
    
    # Seed worst-first by record, using points-for as the tie-breaker. The shuffle
    # only breaks exact (wins, fpts) ties, matching the previous behaviour.
    random.shuffle(rosters)
    rosters.sort(key=lambda r: (r['settings']['wins'], r['settings'].get('fpts', 0)))
    
    lottery_teams_data = []
    for i, roster in enumerate(rosters):
        user_info = user_map.get(roster['owner_id'], {"name": f"Team {roster['owner_id']}", "avatar": None})
        division_id = roster.get('settings', {}).get('division')
        lottery_teams_data.append({
            "seed": i + 1,
            "team_name": user_info["name"],
            "avatar": user_info["avatar"],
            "wins": roster['settings']['wins'],
            "losses": roster['settings']['losses'],
            "division": division_id,
            "division_name": division_name(division_id)
        })

    return jsonify({"teams": lottery_teams_data})

@api_bp.route('/get_league_analytics', methods=['POST'])
def handle_get_analytics():
    data = request.json
    league_id = data.get('league_id')
    if not league_id:
        return jsonify({"error": "League ID is required"}), 400

    all_players = get_all_players()
    if not all_players:
        return jsonify({"error": "Could not load player database."}), 500

    rosters = get_rosters(league_id)
    users = get_users_in_league(league_id)
    
    avatar_base = current_app.config['SLEEPER_AVATAR_BASE']
    user_map = {}
    for user in users:
        display_name = user.get('metadata', {}).get('team_name') or user.get('display_name')
        avatar_id = user.get('avatar')
        user_map[user['user_id']] = {
            "name": display_name,
            "avatar": f"{avatar_base}/{avatar_id}" if avatar_id else None
        }

    analytics_data = []
    for roster in rosters:
        if not roster.get('owner_id'): continue
        stats = calculate_team_analytics(roster, user_map, all_players)
        analytics_data.append(stats)

    analytics_data.sort(key=lambda x: x['total_fpts'], reverse=True)

    return jsonify({"analytics": analytics_data})

@api_bp.route('/get_league_trades', methods=['POST'])
def handle_get_league_trades():
    data = request.json
    league_id = data.get('league_id')
    if not league_id:
        return jsonify({"error": "League ID is required"}), 400

    all_players = get_all_players()
    rosters = get_rosters(league_id)
    users = get_users_in_league(league_id)
    
    avatar_base = current_app.config['SLEEPER_AVATAR_BASE']
    roster_map = {}
    for roster in rosters:
        rid = roster['roster_id']
        owner_id = roster['owner_id']
        user = next((u for u in users if u['user_id'] == owner_id), None)
        name = "Unknown"
        avatar = None
        if user:
            name = user.get('metadata', {}).get('team_name') or user.get('display_name')
            avatar = f"{avatar_base}/{user['avatar']}" if user.get('avatar') else None
        
        roster_map[rid] = {
            "name": name,
            "avatar": avatar,
            "owner_id": owner_id
        }

    all_trades = []
    # Fetch a reasonable number of weeks
    for w in range(1, 25): 
        txs = get_transactions(league_id, w)
        for tx in txs:
            if tx['status'] == 'complete' and tx['type'] == 'trade':
                processed_tx = {
                    "transaction_id": tx['transaction_id'],
                    "week": w,
                    "timestamp": tx['status_updated'], 
                    "rosters_involved": []
                }
                
                trade_details = {} 
                
                for rid in tx['roster_ids']:
                    trade_details[rid] = {"received_players": [], "received_picks": []}

                if tx.get('adds'):
                    for pid, rid in tx['adds'].items():
                        if rid in trade_details:
                            p_data = all_players.get(pid, {})
                            p_name = f"{p_data.get('first_name','')} {p_data.get('last_name','')}".strip() or "Unknown Player"
                            trade_details[rid]['received_players'].append({
                                "player_id": pid,
                                "name": p_name,
                                "position": p_data.get('position')
                            })

                if tx.get('draft_picks'):
                    for pick in tx['draft_picks']:
                        rid = pick['owner_id']
                        if rid in trade_details:
                            desc = f"{pick['season']} Round {pick['round']}"
                            trade_details[rid]['received_picks'].append({
                                "description": desc,
                                "season": pick['season'],
                                "round": pick['round']
                            })
                
                for rid, details in trade_details.items():
                    r_info = roster_map.get(rid, {"name": f"Roster {rid}", "avatar": None})
                    processed_tx['rosters_involved'].append({
                        "team_name": r_info['name'],
                        "avatar": r_info['avatar'],
                        "received_players": details['received_players'],
                        "received_picks": details['received_picks']
                    })
                
                all_trades.append(processed_tx)
    
    all_trades.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({"trades": all_trades})

@api_bp.route('/run_lottery', methods=['POST'])
def handle_run_lottery():
    data = request.json
    teams = data.get('teams')
    odds_map = data.get('odds') 
    
    teams.sort(key=lambda t: t['seed'])

    # Tied teams share their combined combinations equally, but only teams that are
    # actually in the lottery (assigned odds > 0) take part.
    average_tied_odds(teams, odds_map)

    teams_by_seed = {team['seed']: team for team in teams}
    final_order = perform_nba_lottery(teams_by_seed, odds_map)
    return jsonify(final_order)
