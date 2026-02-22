"""
Match service for Coin Clash.
This module handles the business logic for match creation, starting, and completion.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models.models import Match, Character
from ..player.repository import PlayerRepo
from ..player.character_repository import CharacterRepo
from .repository import MatchRepo
from ..common.exceptions import MatchAlreadyActiveError

logger = logging.getLogger(__name__)

class MatchService:
    """Service for managing match lifecycle: creation, starting, and completion."""
    
    def __init__(self, 
                 match_repo: MatchRepo, 
                 player_repo: PlayerRepo, 
                 character_repo: CharacterRepo,
                 db_session: Session):
        """
        Initialize the match service.
        
        Args:
            match_repo: Repository for match operations
            player_repo: Repository for player operations
            character_repo: Repository for character operations
            db_session: Database session
        """
        self.match_repo = match_repo
        self.player_repo = player_repo
        self.character_repo = character_repo
        self.db = db_session
        
    def create_match(self, 
                     entry_fee: float, 
                     kill_award_rate: float, 
                     start_method: str, 
                     start_threshold: int) -> Match:
        """
        Create a new match with specified parameters.
        
        Args:
            entry_fee: Cost to enter a character in the match
            kill_award_rate: Multiplier for kill rewards
            start_method: Either "cap" (start when player cap reached) or "timeout" (start after timer)
            start_threshold: Value for cap or timer duration in seconds
            
        Returns:
            The created Match object
        """
        timer_duration = start_threshold if start_method == "timeout" else None
        
        # Create the match with start_timer_end calculated from timer_duration
        match = self.match_repo.create_match(
            entry_fee=entry_fee,
            kill_award_rate=kill_award_rate,
            start_method=start_method,
            start_threshold=start_threshold,
            timer_duration=timer_duration
        )
        
        logger.info(
            "match_created",
            extra={
                "match_id": match.id,
                "start_method": start_method,
                "start_threshold": start_threshold,
                "timer_end": match.start_timer_end.isoformat() if match.start_timer_end else None
            }
        )
        
        # If using timer, schedule match start at timer end
        if match.start_timer_end:
            # Here we'd schedule a task to start the match when the timer expires
            # This would typically be done with a task scheduler
            pass
        
        self.db.commit()
        return match
        
    def check_and_start_match(self, match_id: int) -> bool:
        """
        Check if match can be started based on player cap and purchases.
        
        Args:
            match_id: The ID of the match to check
            
        Returns:
            True if match was started, False otherwise
        """
        # Get match details
        match = self.match_repo.get_match_by_id(match_id)
        if not match or match.status != "pending":
            return False
            
        # Check if player cap has been reached and all players have characters
        joined_count, purchased_count = self.match_repo.get_match_participant_counts(match_id)
        
        # Start the match if cap is reached and all players have purchased
        if (match.start_method == "cap" and 
            joined_count >= match.start_threshold and 
            purchased_count == joined_count):
            
            logger.info(
                "starting_match_cap_condition",
                extra={
                    "match_id": match_id,
                    "joined_count": joined_count,
                    "purchased_count": purchased_count
                }
            )
            
            return self.start_match(match_id)
            
        return False
    
    def start_match(self, match_id: int) -> bool:
        """
        Start a match, handling auto-assignment of default characters if needed.
        
        Args:
            match_id: The ID of the match to start
            
        Returns:
            True if match was started, False otherwise
        """
        # Get match
        match = self.match_repo.get_match_by_id(match_id)
        
        # Guard: match must exist and be in pending state
        if not match or match.status != "pending":
            if match and match.status != "pending":
                logger.info(
                    "match_already_started",
                    extra={"match_id": match_id, "status": match.status}
                )
            return False
        
        try:
            # Get all characters and players in this match
            characters = self.db.query(Character).filter(Character.match_id == match_id).all()
            
            # Group characters by player_id
            player_characters: dict = {}
            for character in characters:
                if character.player_id not in player_characters:
                    player_characters[character.player_id] = []
                player_characters[character.player_id].append(character)
            
            # Find players who joined but haven't purchased characters
            joined_player_ids = set(player_characters.keys())
            players_without_purchases = [
                pid for pid in joined_player_ids
                if len(player_characters.get(pid, [])) == 0
            ]
            
            # Auto-assign default characters to players without purchases
            for player_id in players_without_purchases:
                self._assign_default_character(player_id, match_id, match.entry_fee)
                
            # Set match as active
            self.match_repo.update_match_status(match_id, "active")
            self.match_repo.set_match_start_time(match_id)
            
            # Invoke match engine to run the match (would typically be async)
            self._run_match(match_id)
            
            logger.info(
                "match_started",
                extra={
                    "match_id": match_id,
                    "auto_assigned_count": len(players_without_purchases)
                }
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "match_start_failed",
                extra={"match_id": match_id, "error": str(e)}
            )
            return False
    
    def _assign_default_character(self, 
                                  player_id: int, 
                                  match_id: int, 
                                  entry_fee: float) -> Optional[Character]:
        """
        Create and assign a default character to a player for this match,
        deducting the entry fee from their balance.
        """
        player = self.player_repo.get_player_by_id(player_id)
        if not player:
            logger.warning(
                "player_not_found_for_default_assignment",
                extra={"player_id": player_id, "match_id": match_id}
            )
            return None
            
        if player.balance < entry_fee:
            logger.warning(
                "insufficient_balance_for_default_assignment",
                extra={
                    "player_id": player_id,
                    "match_id": match_id,
                    "balance": player.balance,
                    "required": entry_fee
                }
            )
            return None
            
        self.player_repo.update_player_balance(player.id, -entry_fee)
        
        character = self.character_repo.create_character(
            name=f"Default_{player.username}_{match_id}",
            player_id=player.id
        )
        
        self.character_repo.assign_character_to_match(character.id, match_id)
        
        logger.info(
            "default_character_assigned",
            extra={
                "player_id": player_id,
                "match_id": match_id,
                "character_id": character.id
            }
        )
        
        return character
    
    def _run_match(self, match_id: int):
        from backend.app.services.match_runner import run_match_background
        run_match_background(match_id, self.db)
