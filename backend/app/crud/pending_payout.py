from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import PendingPayout
from ..schemas.pending_payout import PendingPayoutCreate, PendingPayoutUpdate


class CRUDPendingPayout(CRUDBase[PendingPayout, PendingPayoutCreate, PendingPayoutUpdate]):

    def get_by_match_id(self, db: Session, match_id: int) -> List[PendingPayout]:
        return (
            db.query(PendingPayout)
            .filter(PendingPayout.match_id == match_id)
            .all()
        )

    def get_by_player_id(self, db: Session, player_id: int) -> List[PendingPayout]:
        return (
            db.query(PendingPayout)
            .filter(PendingPayout.player_id == player_id)
            .all()
        )

    def get_unsettled(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[PendingPayout]:
        return (
            db.query(PendingPayout)
            .filter(PendingPayout.settled_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_unsettled_by_player(self, db: Session, player_id: int) -> List[PendingPayout]:
        return (
            db.query(PendingPayout)
            .filter(
                PendingPayout.player_id == player_id,
                PendingPayout.settled_at.is_(None),
            )
            .all()
        )

    def mark_settled(
        self, db: Session, *, payout_id: int, tx_hash: str
    ) -> Optional[PendingPayout]:
        obj = self.get(db, payout_id)
        if obj:
            obj.settled_at = datetime.utcnow()
            obj.settlement_tx_hash = tx_hash
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj


crud_pending_payout = CRUDPendingPayout(PendingPayout)
