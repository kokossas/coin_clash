from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class MatchEventBase(BaseModel):
    match_id: int
    round_number: int
    event_type: str
    scenario_source: Optional[str] = None
    scenario_text: str
    affected_character_ids: Optional[str] = None


class MatchEvent(MatchEventBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
