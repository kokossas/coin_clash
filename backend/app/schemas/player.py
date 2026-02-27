from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PlayerBase(BaseModel):
    wallet_address: str
    username: Optional[str] = None

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
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
    wallet_chain_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class Player(PlayerInDBBase):
    pass
