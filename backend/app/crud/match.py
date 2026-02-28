from typing import List
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import Match
from ..schemas.match import MatchCreate, MatchUpdate

class CRUDMatch(CRUDBase[Match, MatchCreate, MatchUpdate]):
    """CRUD operations for Match model"""
    
    def get_by_status(self, db: Session, status: str) -> List[Match]:
        """Get matches by status"""
        return db.query(Match).filter(Match.status == status).all()
    
    def create_match(self, db: Session, *, entry_fee: float, kill_award_rate: float, start_method: str, start_threshold: int) -> Match:
        """Create a new match"""
        match = Match(
            entry_fee=entry_fee,
            kill_award_rate=kill_award_rate,
            start_method=start_method,
            start_threshold=start_threshold,
            status="pending"
        )
        db.add(match)
        db.commit()
        db.refresh(match)
        return match
    
    def update_status(self, db: Session, *, match_id: int, status: str) -> Match:
        """Update a match's status"""
        match = self.get(db, match_id)
        if match:
            match.status = status
            db.add(match)
            db.commit()
            db.refresh(match)
        return match
    
    def set_winner(self, db: Session, *, match_id: int, winner_character_id: int) -> Match:
        """Set a match's winner"""
        match = self.get(db, match_id)
        if match:
            match.winner_character_id = winner_character_id
            db.add(match)
            db.commit()
            db.refresh(match)
        return match

crud_match = CRUDMatch(Match)
