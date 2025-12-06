from typing import Dict, Any

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
                "player_id": pid,
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
