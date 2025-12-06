from app import db
from app.models import League, Trade, TradeItem, PlayerStats, DraftPick
from app.services.sleeper import (
    get_league_details, get_transactions, get_rosters, get_nba_stats, 
    get_all_players, get_drafts_for_league, get_draft, get_draft_picks
)
from datetime import datetime
import re

def sync_league_history(league_id):
    """
    Walks back the league history from the given league_id,
    syncing leagues and their trades to the database.
    """
    print(f"Syncing league {league_id}...")
    
    # Check if league exists in DB
    existing_league = League.query.get(league_id)
    
    # Backfill/Maintenance: Ensure drafts are synced even if league is known
    if existing_league:
        sync_drafts(league_id, existing_league.season)
    
    if existing_league and existing_league.status == 'synced':
        print(f"League {league_id} already synced.")
        if existing_league.previous_league_id:
            sync_league_history(existing_league.previous_league_id)
        return

    # Fetch details
    details = get_league_details(league_id)
    if not details:
        return

    prev_id = details.get('previous_league_id')
    season = details.get('season')
    name = details.get('name')

    # Create/Update League
    if not existing_league:
        league = League(
            id=league_id,
            name=name,
            season=season,
            previous_league_id=prev_id,
            status='syncing'
        )
        db.session.add(league)
    else:
        existing_league.status = 'syncing'
    
    db.session.commit()

    # Sync Transactions for this league
    sync_transactions(league_id, season)
    
    # Sync Drafts (if not covered above, e.g. new league creation)
    sync_drafts(league_id, season)

    # Mark as synced
    league = League.query.get(league_id)
    league.status = 'synced'
    db.session.commit()

    # Recurse
    if prev_id:
        sync_league_history(prev_id)

def sync_drafts(league_id, season):
    # Fetch drafts associated with this league
    drafts = get_drafts_for_league(league_id)
    if not drafts:
        return

    # Usually there is one main draft, but could be supplemental.
    # We want the one that matches our season usually.
    # Draft object has 'season'.
    
    all_players = None # Lazy load
    
    # Get Rosters to map Owner ID -> Roster ID
    rosters = get_rosters(league_id)
    
    owner_to_roster_map = {}
    for r in rosters:
        owner_to_roster_map[r['owner_id']] = r['roster_id']

    for d in drafts:
        d_id = d['draft_id']
        d_status = d['status']
        
        if d_status != 'complete':
            continue # Only care about completed drafts
            
        # Get full draft info (order)
        full_draft = get_draft(d_id)
        if not full_draft:
            continue
            
        draft_order = full_draft.get('draft_order', {})
        # draft_order: { "user_id": slot_number } 
        # Invert to map Slot -> User ID (Owner)
        slot_to_owner = {v: k for k, v in draft_order.items()}
        
        # Get picks
        picks = get_draft_picks(d_id)
        
        for p in picks:
            slot = p['draft_slot']
            round_num = p['round']
            
            # Who owns this slot? (User ID)
            original_owner_id = slot_to_owner.get(str(slot)) or slot_to_owner.get(int(slot))
            
            if not original_owner_id:
                continue

            # Convert Owner ID -> Roster ID
            original_roster_id = owner_to_roster_map.get(original_owner_id)
            if not original_roster_id:
                continue
                
            # Check if exists
            uid = f"{d_id}_{p['pick_no']}"
            if DraftPick.query.get(uid):
                continue
            
            # Get Name
            if not all_players:
                all_players = get_all_players()
            
            p_data = all_players.get(p['player_id'], {})
            p_name = f"{p_data.get('first_name','')} {p_data.get('last_name','')}".strip()
            
            dp = DraftPick(
                id=uid,
                draft_id=d_id,
                league_id=league_id,
                season=season,
                round=round_num,
                original_roster_id=original_roster_id, # Storing actual Roster ID (1-12)
                player_id=p['player_id'],
                player_name=p_name
            )
            db.session.add(dp)
            
    db.session.commit()

def sync_transactions(league_id, season):
    # We need all players to map IDs to names if needed, but we can do lazy loading
    # For now, let's just store IDs.
    
    # NBA seasons are roughly 25 weeks including playoffs
    for round_num in range(1, 26):
        txns = get_transactions(league_id, round_num)
        if not txns:
            # Empty week usually means season over or future
            # But some weeks might be empty in middle. 
            # Sleeper returns [] for future weeks?
            continue

        for txn in txns:
            if txn['type'] != 'trade':
                continue
            
            txn_id = txn['transaction_id']
            if Trade.query.get(txn_id):
                continue # Already saved

            # Create Trade
            trade = Trade(
                id=txn_id,
                league_id=league_id,
                timestamp=txn['status_updated'], # or created
                date=datetime.fromtimestamp(txn['status_updated'] / 1000.0),
                status=txn['status']
            )
            db.session.add(trade)

            # Process Adds/Drops (Trades in Sleeper are adds/drops mapping)
            # txn['adds'] = {player_id: roster_id} (Receiver)
            # txn['drops'] = {player_id: roster_id} (Sender)
            
            # Adds (Receiver)
            if txn.get('adds'):
                for player_id, roster_id in txn['adds'].items():
                    # Find who sent this? 
                    # In Sleeper trade, 'drops' tells us who sent it.
                    # But a 3-way trade is complex.
                    # Simply: This item moved TO roster_id.
                    # We need to find FROM roster_id.
                    # It's in 'drops'.
                    
                    sender_id = None
                    if txn.get('drops') and player_id in txn['drops']:
                        sender_id = txn['drops'][player_id]
                    
                    item = TradeItem(
                        trade_id=txn_id,
                        sender_roster_id=sender_id,
                        receiver_roster_id=roster_id,
                        asset_type='player',
                        asset_id=player_id
                    )
                    db.session.add(item)
            
            # Picks
            for pick in txn.get('draft_picks', []):
                item = TradeItem(
                    trade_id=txn_id,
                    sender_roster_id=pick['previous_owner_id'],
                    receiver_roster_id=pick['owner_id'],
                    asset_type='pick',
                    asset_id=f"{pick['season']} Round {pick['round']} ({pick['roster_id']})" # Storing origin roster as ID
                )
                db.session.add(item)
                
    db.session.commit()

def get_user_roster_map(league_id, user_id):
    """Finds the roster_id for a user in a specific league"""
    rosters = get_rosters(league_id)
    for r in rosters:
        if r['owner_id'] == user_id:
            return r['roster_id']
    return None

def sync_player_stats(season):
    # Check if we have stats for this season
    if PlayerStats.query.filter_by(season=season).first():
        return # Already have them
        
    print(f"Fetching stats for {season}...")
    stats_data = get_nba_stats(season)
    if not stats_data:
        return

    for pid, data in stats_data.items():
        # data has "gp", "pts", etc.
        # We need a scoring setting to calculate "fpts".
        # For MVP, let's use a standard scoring or just 'pts' if that's all we have?
        # Sleeper stats object usually has calculated 'pts_std', 'pts_ppr', etc?
        # Or just raw stats.
        # Let's check keys. Usually "pts" is points scored.
        # Let's assume we want total fantasy points if available, or just Points as proxy.
        
        # Note: Sleeper stats response key is player_id
        fpts = data.get('pts', 0) # Fallback to raw points for now
        
        # If 'gp' is 0, skip?
        gp = data.get('gp', 0)
        
        ps = PlayerStats(
            id=f"{pid}_{season}",
            player_id=pid,
            season=season,
            total_fpts=fpts,
            gp=gp
        )
        db.session.add(ps)
    
    db.session.commit()

def analyze_user_trades(user_id, current_league_id):
    # 1. Sync History
    sync_league_history(current_league_id)
    
    # 2. Collect all leagues in chain
    leagues = []
    curr = League.query.get(current_league_id)
    while curr:
        leagues.append(curr)
        if curr.previous_league_id:
            curr = League.query.get(curr.previous_league_id)
        else:
            curr = None
            
    # 3. Sync stats for all those seasons
    for l in leagues:
        sync_player_stats(l.season)

    results = []
    
    # 4. Find trades
    all_players = get_all_players()
    
    for l in leagues:
        roster_id = get_user_roster_map(l.id, user_id)
        if not roster_id:
            continue
            
        # Find trades for this roster
        # We need trades where this roster was sender OR receiver
        trades = Trade.query.filter_by(league_id=l.id).all()
        
        for t in trades:
            # Check items
            involved = False
            received_assets = []
            sent_assets = []
            
            # Query items
            items = TradeItem.query.filter_by(trade_id=t.id).all()
            
            for item in items:
                is_receiver = (item.receiver_roster_id == roster_id)
                is_sender = (item.sender_roster_id == roster_id)
                
                if not (is_receiver or is_sender):
                    continue
                
                involved = True
                
                # Get Name
                name = item.asset_id
                score = 0
                
                # Logic to resolve stats
                resolved_pid = None
                
                if item.asset_type == 'player':
                    p_data = all_players.get(item.asset_id, {})
                    name = f"{p_data.get('first_name', '')} {p_data.get('last_name', '')}"
                    resolved_pid = item.asset_id
                    
                elif item.asset_type == 'pick':
                    # Parse ID: "{season} Round {round} ({roster_id})"
                    # Use regex to be safe
                    match = re.search(r"(\d{4}) Round (\d+) \((\d+)\)", item.asset_id)
                    if match:
                        pk_season, pk_round, pk_orig_roster = match.groups()
                        
                        # Find Draft Pick
                        dp = DraftPick.query.filter_by(
                            season=pk_season,
                            round=int(pk_round),
                            original_roster_id=int(pk_orig_roster)
                        ).first()
                        # Note: We need to filter by league? 
                        # A league might have multiple drafts? 
                        # Usually season + round + original_roster is unique enough within a league chain context.
                        # But technically we should filter by league_id OR related leagues?
                        # Since we sync all drafts in chain, we can just find *any* match in our DB that belongs to this chain.
                        # However, DraftPick has `league_id`.
                        # The pick belongs to the league where the draft happened.
                        # That league_id should match `pk_season`'s league ID in the chain.
                        
                        if dp:
                            name = f"{item.asset_id} -> Picked: {dp.player_name}"
                            resolved_pid = dp.player_id
                
                # If we have a resolved player (direct or from pick), get stats
                if resolved_pid:
                    # Get Score (Season Total for the season the trade happened? Or the season the pick was for?)
                    # Prompt says "potential valuations".
                    # Usually, if I trade for a 2024 Pick, I care about the 2024 Stats of the player picked.
                    # If I trade for a Player in 2023, I care about 2023 Stats.
                    # Current logic uses `l.season` (Trade Season).
                    # If the pick is for a FUTURE season (e.g. Trade in 2023 for 2025 pick),
                    # `l.season` is 2023. We won't find 2023 stats for a 2025 rookie.
                    # We should check stats for the `pick's season` if it's a pick.
                    
                    target_season = l.season
                    if item.asset_type == 'pick' and match:
                        target_season = match.groups()[0] # Use pick's season
                        
                        # Ensure we have stats for that season (might not be synced if it's future relative to trade but past relative to now)
                        sync_player_stats(target_season)
                    
                    stat = PlayerStats.query.get(f"{resolved_pid}_{target_season}")
                    if stat:
                        score = stat.total_fpts

                asset_obj = {
                    "type": item.asset_type,
                    "name": name,
                    "score": score
                }
                
                if is_receiver:
                    received_assets.append(asset_obj)
                else:
                    sent_assets.append(asset_obj)
            
            if involved:
                # Calculate Net Grade
                total_received = sum(a['score'] for a in received_assets)
                total_sent = sum(a['score'] for a in sent_assets)
                net_grade = total_received - total_sent
                
                results.append({
                    "date": t.date.strftime("%Y-%m-%d"),
                    "season": l.season,
                    "received": received_assets,
                    "sent": sent_assets,
                    "net_grade": net_grade,
                    "grade_label": "W" if net_grade > 0 else "L" if net_grade < 0 else "-"
                })
                
    # Sort by date desc
    results.sort(key=lambda x: x['date'], reverse=True)
    return results
