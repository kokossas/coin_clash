"""
Player service for Coin Clash.
This module handles the business logic for player operations including character purchases.
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..match.service import MatchService
from sqlalchemy.orm import Session

from backend.app.models.models import Player, Character
from .repository import PlayerRepo
from .character_repository import CharacterRepo
from ..match.repository import MatchRepo
from ..common.exceptions import InsufficientBalanceError, MatchAlreadyActiveError

# Import MatchService at function/method level to avoid circular imports

logger = logging.getLogger(__name__)

class CharacterService:
    """Service for character management and purchases."""
    
    def __init__(self, 
                 player_repo: PlayerRepo, 
                 character_repo: CharacterRepo, 
                 match_repo: MatchRepo,
                 match_service: 'MatchService',
                 db_session: Session):
        """
        Initialize the character service.
        
        Args:
            player_repo: Repository for player operations
            character_repo: Repository for character operations
            match_repo: Repository for match operations
            match_service: Service for match operations
            db_session: Database session
        """
        self.player_repo = player_repo
        self.character_repo = character_repo
        self.match_repo = match_repo
        self.match_service = match_service
        self.db = db_session
    
    def purchase_character(self, 
                          username: str, 
                          match_id: int, 
                          character_name: str) -> Character:
        """
        Purchase a character for a player in a specific match.
        
        Args:
            username: Player's username
            match_id: Match ID
            character_name: Name for the character
            
        Returns:
            The created Character
            
        Raises:
            InsufficientBalanceError: If player can't afford the entry fee
            MatchAlreadyActiveError: If match has already started
        """
        # Get match and verify it's still pending
        match = self.match_repo.get_match_by_id(match_id)
        if not match:
            raise ValueError(f"Match with ID {match_id} not found")
            
        if match.status != "pending":
            raise MatchAlreadyActiveError(f"Match {match_id} is already {match.status}")
        
        # Get player and verify they can afford the entry fee
        player = self.player_repo.get_player_by_username(username)
        if not player:
            player = self.player_repo.create_player(username)
            
        if player.balance < match.entry_fee:
            raise InsufficientBalanceError(
                f"Insufficient balance: {player.balance}, required: {match.entry_fee}"
            )
        
        # Create character
        character = self.character_repo.create_character(
            name=character_name,
            player_id=player.id
        )
        
        # Assign to match
        self.character_repo.assign_character_to_match(character.id, match_id)
        
        # Deduct entry fee
        self.player_repo.update_player_balance(player.id, -match.entry_fee)
        
        logger.info(
            "character_purchased",
            extra={
                "username": username,
                "match_id": match_id,
                "character_id": character.id,
                "character_name": character_name,
                "fee": match.entry_fee
            }
        )
        
        # Check if match can be started now
        self.match_service.check_and_start_match(match_id)
        
        self.db.commit()
        return character


class PlayerService:
    """Service for player management operations."""
    
    def __init__(self, player_repo: PlayerRepo, db_session: Session):
        """
        Initialize the player service.
        
        Args:
            player_repo: Repository for player operations
            db_session: Database session
        """
        self.player_repo = player_repo
        self.db = db_session
    
    def get_player(self, username: str) -> Optional[Player]:
        """
        Get a player by username.
        
        Args:
            username: Player's username
            
        Returns:
            Player if found, None otherwise
        """
        return self.player_repo.get_player_by_username(username)
    
    def create_player(self, username: str) -> Player:
        """
        Create a new player.
        
        Args:
            username: Player's username
            
        Returns:
            The created Player
        """
        player = self.player_repo.create_player(username)
        self.db.commit()
        return player
    
    def add_balance(self, player_id: int, amount: float) -> Optional[Player]:
        """
        Add balance to a player's account.
        
        Args:
            player_id: Player's ID
            amount: Amount to add (can be negative to deduct)
            
        Returns:
            Updated Player if found, None otherwise
        """
        player = self.player_repo.update_player_balance(player_id, amount)
        if player:
            self.db.commit()
        return player
    
    def get_player_stats(self, username: str) -> dict:
        """
        Get a player's stats including wins, kills, and earnings.
        
        Args:
            username: Player's username
            
        Returns:
            Dictionary of player stats or empty dict if player not found
        """
        player = self.player_repo.get_player_by_username(username)
        if not player:
            return {}
            
        return {
            "username": player.username,
            "balance": player.balance,
            "wins": player.wins,
            "kills": player.kills,
            "total_earnings": player.total_sui_earned
        }
