from typing import List, Optional
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import Character
from ..schemas.character import CharacterCreate, CharacterUpdate

class CRUDCharacter(CRUDBase[Character, CharacterCreate, CharacterUpdate]):
    """CRUD operations for Character model"""
    
    def get_by_owner_username(self, db: Session, owner_username: str) -> List[Character]:
        """Get characters by owner username"""
        return db.query(Character).filter(Character.owner_username == owner_username).all()
    
    def get_by_match_id(self, db: Session, match_id: int) -> List[Character]:
        """Get characters by match ID"""
        return db.query(Character).filter(Character.match_id == match_id).all()
    
    def create_character(self, db: Session, *, name: str, owner_username: str) -> Character:
        """Create a new character"""
        character = Character(name=name, owner_username=owner_username)
        db.add(character)
        db.commit()
        db.refresh(character)
        return character
    
    def assign_to_match(self, db: Session, *, character_id: int, match_id: int) -> Character:
        """Assign a character to a match"""
        character = self.get(db, character_id)
        if character:
            character.match_id = match_id
            db.add(character)
            db.commit()
            db.refresh(character)
        return character
    
    def set_alive_status(self, db: Session, *, character_id: int, is_alive: bool) -> Character:
        """Set a character's alive status"""
        character = self.get(db, character_id)
        if character:
            character.is_alive = is_alive
            db.add(character)
            db.commit()
            db.refresh(character)
        return character

crud_character = CRUDCharacter(Character)
