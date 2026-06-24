import pytest
from unittest.mock import patch

@patch('app.api.routes.get_user')
@patch('app.api.routes.get_leagues_for_user')
def test_get_leagues(mock_get_leagues, mock_get_user, client):
    # Mock Data
    mock_get_user.return_value = {"user_id": "12345"}
    mock_get_leagues.return_value = [
        {"league_id": "L1", "name": "NBA League", "sport": "nba", "status": "active", "avatar": "av1"},
        {"league_id": "L2", "name": "NFL League", "sport": "nfl", "status": "active"} # Should be filtered out
    ]

    # Request
    response = client.post('/get_leagues', json={"username": "testuser", "season": "2025"})
    
    # Verify
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "NBA League"
    assert data[0]["league_id"] == "L1"

@patch('app.api.routes.get_user')
def test_get_leagues_user_not_found(mock_get_user, client):
    mock_get_user.return_value = None
    
    response = client.post('/get_leagues', json={"username": "ghost", "season": "2025"})
    
    assert response.status_code == 404
    assert "User not found" in response.get_json()["error"]

@patch('app.api.routes.get_all_players')
@patch('app.api.routes.get_rosters')
@patch('app.api.routes.get_users_in_league')
def test_get_league_analytics(mock_get_users, mock_get_rosters, mock_get_players, client):
    # Mock Data
    mock_get_players.return_value = {"p1": {"first_name": "A", "last_name": "B", "age": 20, "fantasy_positions": ["PG"], "team": "ATL"}}
    
    mock_get_rosters.return_value = [
        {
            "owner_id": "u1", 
            "settings": {"wins": 5, "losses": 5, "fpts": 1000}, 
            "players": ["p1"]
        }
    ]
    
    mock_get_users.return_value = [
        {"user_id": "u1", "display_name": "User 1", "avatar": "def"}
    ]

    response = client.post('/get_league_analytics', json={"league_id": "L1"})
    
    assert response.status_code == 200
    data = response.get_json()
    assert "analytics" in data
    assert len(data["analytics"]) == 1
    assert data["analytics"][0]["team_name"] == "User 1"
    assert data["analytics"][0]["total_fpts"] == 1000.0


@patch('app.api.routes.get_league_details')
@patch('app.api.routes.get_users_in_league')
@patch('app.api.routes.get_rosters')
def test_get_lottery_teams_with_divisions(mock_get_rosters, mock_get_users, mock_get_league_details, client):
    def league_details(league_id):
        if league_id == "L1":
            return {"previous_league_id": "P1"}
        if league_id == "P1":
            return {"settings": {"divisions": 2}, "metadata": {"division_1": "East", "division_2": "West"}}
        return None
    mock_get_league_details.side_effect = league_details

    mock_get_users.return_value = [
        {"user_id": "uA", "display_name": "Team A", "avatar": None},
        {"user_id": "uB", "display_name": "Team B", "avatar": None},
        {"user_id": "uC", "display_name": "Team C", "avatar": None},
        {"user_id": "uD", "display_name": "Team D", "avatar": None},
    ]
    # Returned out of order; the endpoint should seed them worst-first.
    mock_get_rosters.return_value = [
        {"owner_id": "uB", "settings": {"wins": 8, "losses": 2, "fpts": 1100, "division": 1}},
        {"owner_id": "uA", "settings": {"wins": 2, "losses": 8, "fpts": 900, "division": 1}},
        {"owner_id": "uD", "settings": {"wins": 6, "losses": 4, "fpts": 1050, "division": 2}},
        {"owner_id": "uC", "settings": {"wins": 4, "losses": 6, "fpts": 1000, "division": 2}},
    ]

    response = client.post('/get_lottery_teams', json={"league_id": "L1"})

    assert response.status_code == 200
    teams = response.get_json()["teams"]
    assert len(teams) == 4

    # Seeded worst-first by (wins, fpts): A(2), C(4), D(6), B(8)
    assert [t["team_name"] for t in teams] == ["Team A", "Team C", "Team D", "Team B"]
    assert [t["seed"] for t in teams] == [1, 2, 3, 4]

    # Division id + resolved name are attached to every team.
    assert teams[0]["division"] == 1 and teams[0]["division_name"] == "East"
    assert teams[1]["division"] == 2 and teams[1]["division_name"] == "West"


@patch('app.api.routes.get_league_details')
def test_get_lottery_teams_requires_previous_season(mock_get_league_details, client):
    mock_get_league_details.return_value = {"previous_league_id": None}

    response = client.post('/get_lottery_teams', json={"league_id": "L1"})

    assert response.status_code == 404
