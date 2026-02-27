from typing import List, Optional
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import OwnedCharacter
from ..schemas.owned_character import OwnedCharacterCreate, OwnedCharacterUpdate


class CRUDOwnedCharacter(CRUDBase[OwnedCharacter, OwnedCharacterCreate, OwnedCharacterUpdate]):

    def get_by_player_id(
        self, db: Session, player_id: int, *, alive_only: bool = False
    ) -> List[OwnedCharacter]:
        q = db.query(OwnedCharacter).filter(OwnedCharacter.player_id == player_id)
        if alive_only:
            q = q.filter(OwnedCharacter.is_alive.is_(True))
        return q.all()

    def get_by_ids_and_player(
        self, db: Session, ids: List[int], player_id: int
    ) -> List[OwnedCharacter]:
        return (
            db.query(OwnedCharacter)
            .filter(
                OwnedCharacter.id.in_(ids),
                OwnedCharacter.player_id == player_id,
            )
            .all()
        )

    def set_alive(self, db: Session, *, character_id: int, is_alive: bool) -> Optional[OwnedCharacter]:
        obj = self.get(db, character_id)
        if obj:
            obj.is_alive = is_alive
            if is_alive:
                obj.revival_count += 1
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj

    def set_last_match(self, db: Session, *, character_id: int, match_id: int) -> Optional[OwnedCharacter]:
        obj = self.get(db, character_id)
        if obj:
            obj.last_match_id = match_id
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj


crud_owned_character = CRUDOwnedCharacter(OwnedCharacter)
