from typing import List, Optional
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import MatchJoinRequest, MatchJoinRequestCharacter
from ..schemas.match_join_request import MatchJoinRequestCreate, MatchJoinRequestUpdate


class CRUDMatchJoinRequest(CRUDBase[MatchJoinRequest, MatchJoinRequestCreate, MatchJoinRequestUpdate]):

    def get_by_match_id(self, db: Session, match_id: int) -> List[MatchJoinRequest]:
        return (
            db.query(MatchJoinRequest)
            .filter(MatchJoinRequest.match_id == match_id)
            .all()
        )

    def get_by_match_and_player(
        self, db: Session, match_id: int, player_id: int
    ) -> Optional[MatchJoinRequest]:
        return (
            db.query(MatchJoinRequest)
            .filter(
                MatchJoinRequest.match_id == match_id,
                MatchJoinRequest.player_id == player_id,
            )
            .first()
        )

    def get_confirmed_by_match(self, db: Session, match_id: int) -> List[MatchJoinRequest]:
        return (
            db.query(MatchJoinRequest)
            .filter(
                MatchJoinRequest.match_id == match_id,
                MatchJoinRequest.payment_status == "confirmed",
            )
            .all()
        )

    def create_with_characters(
        self,
        db: Session,
        *,
        match_id: int,
        player_id: int,
        entry_fee_total: float,
        owned_character_ids: List[int],
    ) -> MatchJoinRequest:
        join_request = MatchJoinRequest(
            match_id=match_id,
            player_id=player_id,
            entry_fee_total=entry_fee_total,
        )
        db.add(join_request)
        db.flush()  # get id before creating junction rows

        for oc_id in owned_character_ids:
            db.add(MatchJoinRequestCharacter(
                join_request_id=join_request.id,
                owned_character_id=oc_id,
            ))

        db.flush()
        return join_request

    def update_payment_status(
        self, db: Session, *, request_id: int, status: str, confirmed_at=None
    ) -> Optional[MatchJoinRequest]:
        obj = self.get(db, request_id)
        if obj:
            obj.payment_status = status
            if confirmed_at:
                obj.confirmed_at = confirmed_at
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj


crud_match_join_request = CRUDMatchJoinRequest(MatchJoinRequest)
