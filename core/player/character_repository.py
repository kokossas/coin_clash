"""
Character repository implementation for database operations related to characters.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..common.repository import BaseRepo
from ..database.models import Character

class CharacterRepo(BaseRepo):
    """Repository interface for character operations."""
    
    def create_character(self, name: str, owner_username: str) -> Character:
        """
        Create a new character.
        
        Args:
            name: The character's name
            owner_username: Username of the owner player
            
        Returns:
            The created Character object
        """
        pass

    def get_character_by_id(self, character_id: int) -> Optional[Character]:
        """
        Get a character by ID.
        
        Args:
            character_id: The character's ID
            
        Returns:
            Character object if found, None otherwise
        """
        pass

    def get_characters_by_owner(self, owner_username: str) -> List[Character]:
        """
        Get all characters owned by a player.
        
        Args:
            owner_username: Username of the owner player
            
        Returns:
            List of Character objects
        """
        pass

    def update_character_status(self, character_id: int, is_alive: bool) -> Optional[Character]:
        """
        Update a character's alive status.
        
        Args:
            character_id: The character's ID
            is_alive: Whether the character is alive
            
        Returns:
            Updated Character object if found, None otherwise
        """
        pass

    def assign_character_to_match(self, character_id: int, match_id: int) -> Optional[Character]:
        """
        Assign a character to a match.
        
        Args:
            character_id: The character's ID
            match_id: The match's ID
            
        Returns:
            Updated Character object if found, None otherwise
        """
        pass


class SqlCharacterRepo(CharacterRepo):
    """SQL implementation of CharacterRepo interface."""
    
    def create_character(self, name: str, owner_username: str) -> Character:
        db_character = Character(name=name, owner_username=owner_username)
        self.db.add(db_character)
        self.db.flush()
        return db_character

    def get_character_by_id(self, character_id: int) -> Optional[Character]:
        return self.db.query(Character).filter(Character.id == character_id).first()

    def get_characters_by_owner(self, owner_username: str) -> List[Character]:
        return self.db.query(Character).filter(Character.owner_username == owner_username).all()

    def update_character_status(self, character_id: int, is_alive: bool) -> Optional[Character]:
        character = self.get_character_by_id(character_id)
        if character:
            character.is_alive = 1 if is_alive else 0
        return character

    def assign_character_to_match(self, character_id: int, match_id: int) -> Optional[Character]:
        character = self.get_character_by_id(character_id)
        if character:
            character.match_id = match_id
        return character
