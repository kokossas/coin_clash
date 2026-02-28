from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class TransactionBase(BaseModel):
    player_id: int
    amount: float
    currency: str
    tx_type: str
    status: str
    provider: str

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    player_id: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    tx_type: Optional[str] = None
    status: Optional[str] = None
    provider: Optional[str] = None
    provider_tx_id: Optional[str] = None

class TransactionInDBBase(TransactionBase):
    id: int
    provider_tx_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class Transaction(TransactionInDBBase):
    pass
