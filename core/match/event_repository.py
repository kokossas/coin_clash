"""
Event repository implementation for database operations related to match events.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..common.repository import BaseRepo
from backend.app.models.models import MatchEvent

class EventRepo(BaseRepo):
    """Repository interface for match event operations."""
    
    def create_match_event(self, match_id: int, round_number: int, event_type: str, scenario_source: str, scenario_text: str, affected_character_ids: str) -> MatchEvent:
        """
        Create a new match event.
        
        Args:
            match_id: The match's ID
            round_number: The round number in which the event occurred
            event_type: Type of event (e.g., "direct_kill", "environmental")
            scenario_source: Source of the scenario (e.g., scenario ID or "generated")
            scenario_text: Text description of the event
            affected_character_ids: Comma-separated list of affected character IDs
            
        Returns:
            The created MatchEvent object
        """
        pass

    def get_events_for_match(self, match_id: int) -> List[MatchEvent]:
        """
        Get all events for a match, ordered by timestamp.
        
        Args:
            match_id: The match's ID
            
        Returns:
            List of MatchEvent objects
        """
        pass


class SqlEventRepo(EventRepo):
    """SQL implementation of EventRepo interface."""
    
    def create_match_event(self, match_id: int, round_number: int, event_type: str, scenario_source: str, scenario_text: str, affected_character_ids: str) -> MatchEvent:
        db_event = MatchEvent(
            match_id=match_id,
            round_number=round_number,
            event_type=event_type,
            scenario_source=scenario_source,
            scenario_text=scenario_text,
            affected_character_ids=affected_character_ids
        )
        self.db.add(db_event)
        self.db.flush()
        return db_event

    def get_events_for_match(self, match_id: int) -> List[MatchEvent]:
        return self.db.query(MatchEvent).filter(MatchEvent.match_id == match_id).order_by(MatchEvent.created_at).all()
