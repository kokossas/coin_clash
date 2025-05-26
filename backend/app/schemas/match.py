from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MatchBase(BaseModel):
    entry_fee: float
    kill_award_rate: float
    start_method: str
    start_threshold: int

class MatchCreate(MatchBase):
    pass

class MatchUpdate(MatchBase):
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

class MatchInDBBase(MatchBase):
    id: int
    start_timer_end: Optional[datetime] = None
    start_timestamp: datetime
    end_timestamp: datetime
    winner_character_id: Optional[int] = None
    status: str
    created_at: datetime
    blockchain_tx_id: Optional[str] = None
    blockchain_settlement_status: Optional[str] = None
    
    class Config:
        orm_mode = True

class Match(MatchInDBBase):
    pass
