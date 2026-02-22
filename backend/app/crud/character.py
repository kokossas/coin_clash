from typing import List, Optional
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import Character
from ..schemas.character import CharacterCreate, CharacterUpdate

class CRUDCharacter(CRUDBase[Character, CharacterCreate, CharacterUpdate]):
    """CRUD operations for Character model"""

    def get_by_player_id(self, db: Session, player_id: int) -> List[Character]:
        return db.query(Character).filter(Character.player_id == player_id).all()

    def get_by_match_id(self, db: Session, match_id: int) -> List[Character]:
        return db.query(Character).filter(Character.match_id == match_id).all()

    def create_character(self, db: Session, *, name: str, player_id: int) -> Character:
        character = Character(name=name, player_id=player_id)
        db.add(character)
        db.commit()
        db.refresh(character)
        return character

    def assign_to_match(self, db: Session, *, character_id: int, match_id: int) -> Optional[Character]:
        character = self.get(db, character_id)
        if character:
            character.match_id = match_id
            db.add(character)
            db.commit()
            db.refresh(character)
        return character

    def set_alive_status(self, db: Session, *, character_id: int, is_alive: bool) -> Optional[Character]:
        character = self.get(db, character_id)
        if character:
            character.is_alive = is_alive
            db.add(character)
            db.commit()
            db.refresh(character)
        return character

crud_character = CRUDCharacter(Character)
