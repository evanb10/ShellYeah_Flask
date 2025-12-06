from app.logic.lottery import perform_nba_lottery

def test_perform_nba_lottery_logic():
    # Setup
    # 4 Teams, flat odds for simplicity (250 each)
    teams_by_seed = {
        1: {"team_name": "Team A", "avatar": "avatar_a"},
        2: {"team_name": "Team B", "avatar": "avatar_b"},
        3: {"team_name": "Team C", "avatar": "avatar_c"},
        4: {"team_name": "Team D", "avatar": "avatar_d"}
    }
    
    odds_map = {
        "1": 250,
        "2": 250,
        "3": 250,
        "4": 250
    }

    # Execution
    results = perform_nba_lottery(teams_by_seed, odds_map)

    # Verification
    assert len(results) == 4
    
    # Check structure
    first_pick = results[0]
    assert "pick" in first_pick
    assert "team_name" in first_pick
    assert "original_seed" in first_pick
    assert first_pick["pick"] == 1
    
    # Ensure all teams are present
    team_names = [r["team_name"] for r in results]
    assert "Team A" in team_names
    assert "Team B" in team_names
    assert "Team C" in team_names
    assert "Team D" in team_names

def test_perform_nba_lottery_with_non_lottery_teams():
    # Scenario: 6 teams total, only top 4 have lottery odds
    teams_by_seed = {
        1: {"team_name": "Lottery 1", "avatar": "a"},
        2: {"team_name": "Lottery 2", "avatar": "b"},
        3: {"team_name": "Lottery 3", "avatar": "c"},
        4: {"team_name": "Lottery 4", "avatar": "d"},
        5: {"team_name": "Non-Lott 5", "avatar": "e"},
        6: {"team_name": "Non-Lott 6", "avatar": "f"}
    }
    
    # Top 4 get all odds (250 each)
    odds_map = {
        "1": 250,
        "2": 250,
        "3": 250,
        "4": 250,
        "5": 0,
        "6": 0
    }

    results = perform_nba_lottery(teams_by_seed, odds_map)
    
    assert len(results) == 6
    
    # Check that picks 5 and 6 are strictly assigned to seed 5 and 6
    # because they have 0 odds and should fall to the bottom in seed order
    pick_5 = next(r for r in results if r["pick"] == 5)
    pick_6 = next(r for r in results if r["pick"] == 6)
    
    assert pick_5["team_name"] == "Non-Lott 5"
    assert pick_6["team_name"] == "Non-Lott 6"
