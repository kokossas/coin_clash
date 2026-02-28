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
                          player_id: int, 
                          match_id: int, 
                          character_name: str) -> Character:
        """
        Purchase a character for a player in a specific match.
        
        Args:
            player_id: Player's ID
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
        player = self.player_repo.get_player_by_id(player_id)
        if not player:
            raise ValueError(f"Player with ID {player_id} not found")
            
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
                "player_id": player_id,
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
        self.player_repo = player_repo
        self.db = db_session
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        return self.player_repo.get_player_by_id(player_id)
    
    def get_player_by_wallet(self, wallet_address: str) -> Optional[Player]:
        return self.player_repo.get_player_by_wallet_address(wallet_address)
    
    def create_player(self, wallet_address: str, username: Optional[str] = None) -> Player:
        player = self.player_repo.create_player(wallet_address=wallet_address, username=username)
        self.db.commit()
        return player
    
    def add_balance(self, player_id: int, amount: float) -> Optional[Player]:
        player = self.player_repo.update_player_balance(player_id, amount)
        if player:
            self.db.commit()
        return player
    
    def get_player_stats(self, player_id: int) -> dict:
        player = self.player_repo.get_player_by_id(player_id)
        if not player:
            return {}
            
        return {
            "wallet_address": player.wallet_address,
            "username": player.username,
            "balance": player.balance,
            "wins": player.wins,
            "kills": player.kills,
            "total_earnings": player.total_earnings
        }
