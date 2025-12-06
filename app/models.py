from app import db
from datetime import datetime

class League(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(100))
    season = db.Column(db.String(10))
    previous_league_id = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(20))

class Trade(db.Model):
    id = db.Column(db.String(64), primary_key=True) # sleeper transaction id
    league_id = db.Column(db.String(64), db.ForeignKey('league.id'))
    timestamp = db.Column(db.Integer) # Unix timestamp
    date = db.Column(db.DateTime) # Calculated from timestamp for easier querying
    status = db.Column(db.String(20)) # complete
    
    items = db.relationship('TradeItem', backref='trade', lazy='dynamic')

class TradeItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.String(64), db.ForeignKey('trade.id'))
    sender_roster_id = db.Column(db.Integer)
    receiver_roster_id = db.Column(db.Integer)
    asset_type = db.Column(db.String(20)) # 'player' or 'pick'
    asset_id = db.Column(db.String(64)) # player_id or generic pick info
    
    # Metadata for grading
    asset_name = db.Column(db.String(100)) # Snapshot of name
    
class PlayerStats(db.Model):
    # Cache for seasonal stats to calculate grades
    id = db.Column(db.String(64), primary_key=True) # player_id_season
    player_id = db.Column(db.String(64))
    season = db.Column(db.String(10))
    total_fpts = db.Column(db.Float)
    gp = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class DraftPick(db.Model):
    # Stores the RESULT of a pick (who was picked)
    id = db.Column(db.String(64), primary_key=True) # draft_id_pick_no
    draft_id = db.Column(db.String(64))
    league_id = db.Column(db.String(64))
    season = db.Column(db.String(10))
    
    round = db.Column(db.Integer)
    original_roster_id = db.Column(db.Integer) # The roster this slot belonged to originally
    
    player_id = db.Column(db.String(64))
    player_name = db.Column(db.String(100)) # Snapshot

