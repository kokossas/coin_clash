from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PendingPayoutBase(BaseModel):
    match_id: int
    player_id: int
    payout_type: str
    amount: Decimal


class PendingPayoutCreate(PendingPayoutBase):
    currency: str = "USDC"


class PendingPayoutUpdate(BaseModel):
    settled_at: Optional[datetime] = None
    settlement_tx_hash: Optional[str] = None


class PendingPayoutInDBBase(PendingPayoutBase):
    id: int
    currency: str
    calculated_at: datetime
    settled_at: Optional[datetime] = None
    settlement_tx_hash: Optional[str] = None

    class Config:
        orm_mode = True


class PendingPayout(PendingPayoutInDBBase):
    pass
