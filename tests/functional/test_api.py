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
