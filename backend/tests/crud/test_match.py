from sqlalchemy.orm import Session

from app.crud.match import crud_match
from app.schemas.match import MatchCreate
from app.models.models import Match

def test_create_match(db_session: Session):
    entry_fee = 1.5
    kill_award_rate = 0.6
    start_method = "timeout"
    start_threshold = 60
    
    match_in = MatchCreate(
        entry_fee=entry_fee,
        kill_award_rate=kill_award_rate,
        start_method=start_method,
        start_threshold=start_threshold
    )
    match = crud_match.create(db_session, obj_in=match_in)
    
    assert match.entry_fee == entry_fee
    assert match.kill_award_rate == kill_award_rate
    assert match.start_method == start_method
    assert match.start_threshold == start_threshold
    assert match.status == "pending"
    assert match.blockchain_tx_id is None
    assert match.blockchain_settlement_status is None

def test_get_match(db_session: Session, test_match: Match):
    match = crud_match.get(db_session, id=test_match.id)
    assert match
    assert match.id == test_match.id
    assert match.entry_fee == test_match.entry_fee
    assert match.kill_award_rate == test_match.kill_award_rate

def test_get_by_status(db_session: Session, test_match: Match):
    matches = crud_match.get_by_status(db_session, status=test_match.status)
    assert len(matches) > 0
    assert test_match.id in [m.id for m in matches]

def test_update_status(db_session: Session, test_match: Match):
    new_status = "active"
    updated_match = crud_match.update_status(
        db_session, match_id=test_match.id, status=new_status
    )
    
    assert updated_match.status == new_status

def test_set_winner(db_session: Session, test_match: Match, test_character):
    updated_match = crud_match.set_winner(
        db_session, match_id=test_match.id, winner_character_id=test_character.id
    )
    
    assert updated_match.winner_character_id == test_character.id
