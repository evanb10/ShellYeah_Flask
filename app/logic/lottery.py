import random
from typing import Dict, List, Any

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
