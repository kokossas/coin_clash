import datetime
from typing import Optional, Tuple

from abc import abstractmethod

from ..common.repository import BaseRepo
from backend.app.models.models import Match, Character

class MatchRepo(BaseRepo):
    """Repository interface for match operations."""
    
    @abstractmethod
    def create_match(self, entry_fee: float, kill_award_rate: float, start_method: str, start_threshold: int, timer_duration: int = None) -> Match:
        """
        Create a new match.
        
        Args:
            entry_fee: Cost to enter one character in the match
            kill_award_rate: Rate at which kill rewards are calculated
            start_method: Method to determine when match starts ("cap" or "timeout")
            start_threshold: Threshold value for the start method (player cap or seconds)
            timer_duration: Duration in seconds for timer-based starts (optional)
        """
        pass

    @abstractmethod
    def get_match_by_id(self, match_id: int) -> Optional[Match]:
        """Get a match by ID."""
        pass

    @abstractmethod
    def update_match_status(self, match_id: int, status: str) -> Optional[Match]:
        """Update a match's status."""
        pass

    @abstractmethod
    def set_match_start_time(self, match_id: int) -> Optional[Match]:
        """Set the start timestamp of a match to the current time."""
        pass

    @abstractmethod
    def set_match_end_time(self, match_id: int) -> Optional[Match]:
        """Set the end timestamp of a match to the current time."""
        pass

    @abstractmethod
    def set_match_winner(self, match_id: int, winner_character_id: int) -> Optional[Match]:
        """Set the winner of a match."""
        pass
        
    @abstractmethod
    def set_start_timer_end(self, match_id: int, timer_duration: int) -> Optional[Match]:
        """Set the start timer end timestamp for a match."""
        pass
        
    @abstractmethod
    def get_match_participant_counts(self, match_id: int) -> Tuple[int, int]:
        """Get the count of joined players and those who have purchased characters."""
        pass


class SqlMatchRepo(MatchRepo):
    """SQL implementation of MatchRepo interface."""
    
    def create_match(self, entry_fee: float, kill_award_rate: float, start_method: str, start_threshold: int, timer_duration: int = None) -> Match:
        db_match = Match(
            entry_fee=entry_fee,
            kill_award_rate=kill_award_rate,
            start_method=start_method,
            start_threshold=start_threshold,
            status="pending"
        )
        
        if timer_duration is not None and timer_duration > 0:
            db_match.start_timer_end = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=timer_duration)
            
        self.db.add(db_match)
        self.db.flush()
        return db_match

    def get_match_by_id(self, match_id: int) -> Optional[Match]:
        return self.db.query(Match).filter(Match.id == match_id).first()

    def update_match_status(self, match_id: int, status: str) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.status = status
        return match

    def set_match_start_time(self, match_id: int) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.start_timestamp = datetime.datetime.now(datetime.timezone.utc)
        return match

    def set_match_end_time(self, match_id: int) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.end_timestamp = datetime.datetime.now(datetime.timezone.utc)
        return match

    def set_match_winner(self, match_id: int, winner_character_id: int) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.winner_character_id = winner_character_id
        return match
        
    def set_start_timer_end(self, match_id: int, timer_duration: int) -> Optional[Match]:
        match = self.get_match_by_id(match_id)
        if match:
            match.start_timer_end = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=timer_duration)
        return match
        
    def get_match_participant_counts(self, match_id: int) -> Tuple[int, int]:
        match = self.get_match_by_id(match_id)
        if not match:
            return (0, 0)
            
        characters = self.db.query(Character).filter(Character.match_id == match_id).all()
        
        joined_players = set()
        character_counts = {}
        
        for character in characters:
            joined_players.add(character.player_id)
            character_counts[character.player_id] = character_counts.get(character.player_id, 0) + 1
        
        joined_count = len(joined_players)
        purchased_count = len([p for p in joined_players if character_counts.get(p, 0) > 0])
        
        return (joined_count, purchased_count)
