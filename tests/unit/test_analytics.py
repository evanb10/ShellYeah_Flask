from app.logic.analytics import calculate_team_analytics

def test_calculate_team_analytics():
    # Mock Data
    roster = {
        "owner_id": "user123",
        "settings": {
            "wins": 10,
            "losses": 5,
            "ties": 0,
            "fpts": 1500,
            "fpts_decimal": 50
        },
        "players": ["player1", "player2"]
    }
    
    user_map = {
        "user123": {"name": "Test User", "avatar": "test_avatar"}
    }
    
    all_players = {
        "player1": {
            "first_name": "LeBron", "last_name": "James", 
            "age": 38, "fantasy_positions": ["SF", "PF"], "team": "LAL"
        },
        "player2": {
            "first_name": "Luka", "last_name": "Doncic", 
            "age": 24, "fantasy_positions": ["PG"], "team": "DAL"
        }
    }
    
    # Execution
    stats = calculate_team_analytics(roster, user_map, all_players)
    
    # Verification
    assert stats["team_name"] == "Test User"
    assert stats["wins"] == 10
    assert stats["losses"] == 5
    assert stats["total_fpts"] == 1500.5
    
    # Avg Age: (38 + 24) / 2 = 31.0
    assert stats["avg_age"] == 31.0
    
    # Positions
    assert stats["positions"]["SF"] == 1
    assert stats["positions"]["PF"] == 1
    assert stats["positions"]["PG"] == 1
    assert stats["positions"]["C"] == 0
    
    # Roster Details
    assert len(stats["roster_details"]) == 2
    names = [p["name"] for p in stats["roster_details"]]
    assert "LeBron James" in names
    assert "Luka Doncic" in names

def test_calculate_team_analytics_missing_player():
    # Scenario: Roster contains a player ID not in all_players DB
    roster = {
        "owner_id": "user123",
        "settings": {"wins": 0, "losses": 0, "fpts": 0},
        "players": ["unknown_player"]
    }
    user_map = {"user123": {"name": "Test", "avatar": ""}}
    all_players = {}
    
    stats = calculate_team_analytics(roster, user_map, all_players)
    
    assert stats["roster_size"] == 1
    assert len(stats["roster_details"]) == 0 # Should be skipped or handled gracefully?
    # Looking at logic: loop iterates over player_ids, checks `if pid in all_players`.
    # So it skips unknown players.
    
    # NOTE: Roster size is calculated from `len(player_ids)`, so it will be 1.
    # But roster_details will be empty.
    assert stats["roster_size"] == 1
    assert stats["avg_age"] == 0
