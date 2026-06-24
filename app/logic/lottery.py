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


def average_tied_odds(teams, odds_map):
    """
    Tied teams (identical wins and losses) split their combined combinations
    evenly. Only teams that are part of the lottery — i.e. that were assigned
    odds (> 0) on the setup screen — take part, so a tied non-lottery team never
    inherits combinations. Mutates and returns ``odds_map``.
    """
    lottery_teams = [
        t for t in sorted(teams, key=lambda t: t['seed'])
        if int(odds_map.get(str(t['seed']), 0)) > 0
    ]

    groups = []
    if lottery_teams:
        current_group = [lottery_teams[0]]
        for i in range(1, len(lottery_teams)):
            prev = lottery_teams[i - 1]
            curr = lottery_teams[i]
            if prev['wins'] == curr['wins'] and prev['losses'] == curr['losses']:
                current_group.append(curr)
            else:
                groups.append(current_group)
                current_group = [curr]
        groups.append(current_group)

    for group in groups:
        if len(group) > 1:
            total_group_odds = sum(int(odds_map.get(str(t['seed']), 0)) for t in group)
            count = len(group)
            base_share = total_group_odds // count
            remainder = total_group_odds % count

            for team in group:
                value = base_share
                if remainder > 0:
                    value += 1
                    remainder -= 1
                odds_map[str(team['seed'])] = value

    return odds_map
