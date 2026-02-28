from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class MatchBase(BaseModel):
    entry_fee: float
    kill_award_rate: float
    start_method: str
    start_threshold: int

class MatchCreate(MatchBase):
    status: str = "pending"
    creator_wallet_address: Optional[str] = None
    min_players: int = 3
    max_characters: int = 20
    max_characters_per_player: int = 3

class MatchUpdate(BaseModel):
    entry_fee: Optional[float] = None
    kill_award_rate: Optional[float] = None
    start_method: Optional[str] = None
    start_threshold: Optional[int] = None
    start_timer_end: Optional[datetime] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    winner_character_id: Optional[int] = None
    status: Optional[str] = None
    blockchain_tx_id: Optional[str] = None
    blockchain_settlement_status: Optional[str] = None
    creator_wallet_address: Optional[str] = None
    min_players: Optional[int] = None
    max_characters: Optional[int] = None
    max_characters_per_player: Optional[int] = None
    countdown_started_at: Optional[datetime] = None

class MatchInDBBase(MatchBase):
    id: int
    start_timer_end: Optional[datetime] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    winner_character_id: Optional[int] = None
    status: str
    created_at: datetime
    blockchain_tx_id: Optional[str] = None
    blockchain_settlement_status: Optional[str] = None
    creator_wallet_address: Optional[str] = None
    min_players: int = 3
    max_characters: int = 20
    max_characters_per_player: int = 3
    countdown_started_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Match(MatchInDBBase):
    pass
