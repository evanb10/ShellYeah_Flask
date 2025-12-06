import pytest
from unittest.mock import patch, MagicMock
from app import create_app, db
from datetime import datetime
from app.models import League, Trade, TradeItem, PlayerStats
from app.logic.trade_analyzer import sync_league_history, analyze_user_trades

@pytest.fixture
def test_app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@patch('app.logic.trade_analyzer.sync_drafts')
@patch('app.logic.trade_analyzer.get_league_details')
@patch('app.logic.trade_analyzer.get_transactions')
def test_sync_league_history(mock_get_txns, mock_get_details, mock_sync_drafts, test_app):
    # Setup Mocks
    mock_get_details.return_value = {
        "previous_league_id": None,
        "season": "2024",
        "name": "Test League"
    }
    
    # Mock transactions: 1 trade in round 1, empty otherwise
    def get_txns_side_effect(lid, rnd):
        if rnd == 1:
            return [{
                "transaction_id": "tx1",
                "type": "trade",
                "status": "complete",
                "status_updated": 1700000000000,
                "adds": {"playerA": "roster1"}, 
                "drops": {"playerA": "roster2"},
                "draft_picks": []
            }]
        return []

    mock_get_txns.side_effect = get_txns_side_effect
    
    with test_app.app_context():
        sync_league_history("league1")
        
        # Verify League
        l = League.query.get("league1")
        assert l is not None
        assert l.status == "synced"
        
        # Verify Trade
        t = Trade.query.get("tx1")
        assert t is not None
        
        # Verify Items
        items = TradeItem.query.all()
        assert len(items) == 1
        assert items[0].asset_id == "playerA"

@patch('app.logic.trade_analyzer.sync_league_history')
@patch('app.logic.trade_analyzer.sync_player_stats')
@patch('app.logic.trade_analyzer.get_all_players')
@patch('app.logic.trade_analyzer.get_user_roster_map')
def test_analyze_user_trades(mock_get_map, mock_get_players, mock_sync_stats, mock_sync_hist, test_app):
    # Setup Data in DB
    with test_app.app_context():
        # League
        l = League(id="league1", season="2024", status="synced")
        db.session.add(l)
        
        # Trade: User (roster1) GIVES PlayerA, GETS PlayerB
        t = Trade(id="tx1", league_id="league1", timestamp=1700000000000, date=datetime.now(), status="complete")
        db.session.add(t)
        
        # Item 1: Player A from Roster 1 to Roster 2
        i1 = TradeItem(trade_id="tx1", sender_roster_id=1, receiver_roster_id=2, asset_type="player", asset_id="playerA")
        db.session.add(i1)
        
        # Item 2: Player B from Roster 2 to Roster 1
        i2 = TradeItem(trade_id="tx1", sender_roster_id=2, receiver_roster_id=1, asset_type="player", asset_id="playerB")
        db.session.add(i2)
        
        # Stats
        # Player A (Sent): 1000 pts
        s1 = PlayerStats(id="playerA_2024", player_id="playerA", season="2024", total_fpts=1000)
        db.session.add(s1)
        
        # Player B (Received): 1500 pts
        s2 = PlayerStats(id="playerB_2024", player_id="playerB", season="2024", total_fpts=1500)
        db.session.add(s2)
        
        db.session.commit()
        
        # Mocks
        mock_get_map.return_value = 1 # User is roster 1
        mock_get_players.return_value = {
            "playerA": {"first_name": "A", "last_name": "Name"},
            "playerB": {"first_name": "B", "last_name": "Name"}
        }
        
        results = analyze_user_trades("user1", "league1")
        
        assert len(results) == 1
        r = results[0]
        assert r['net_grade'] == 500 # 1500 (Rec) - 1000 (Sent)
        assert len(r['received']) == 1
        assert r['received'][0]['name'] == "B Name"
