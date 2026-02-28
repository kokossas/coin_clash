from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class MatchJoinRequestBase(BaseModel):
    match_id: int
    player_id: int
    entry_fee_total: Decimal
    protocol_fee: Decimal


class MatchJoinRequestCreate(MatchJoinRequestBase):
    character_ids: List[int]


class MatchJoinRequestUpdate(BaseModel):
    payment_status: Optional[str] = None
    confirmed_at: Optional[datetime] = None


class MatchJoinRequestInDBBase(MatchJoinRequestBase):
    id: int
    payment_status: str
    created_at: datetime
    confirmed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MatchJoinRequest(MatchJoinRequestInDBBase):
    pass
