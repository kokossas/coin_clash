from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PlayerBase(BaseModel):
    username: str

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(PlayerBase):
    username: Optional[str] = None
    balance: Optional[float] = None
    wins: Optional[int] = None
    kills: Optional[int] = None
    total_sui_earned: Optional[float] = None
    wallet_address: Optional[str] = None
    wallet_chain_id: Optional[str] = None

class PlayerInDBBase(PlayerBase):
    id: int
    balance: float
    wins: int
    kills: int
    total_sui_earned: float
    created_at: datetime
    wallet_address: Optional[str] = None
    wallet_chain_id: Optional[str] = None
    
    class Config:
        orm_mode = True

class Player(PlayerInDBBase):
    pass
