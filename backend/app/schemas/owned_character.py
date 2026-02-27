from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class OwnedCharacterBase(BaseModel):
    player_id: int
    character_name: str


class OwnedCharacterCreate(OwnedCharacterBase):
    pass


class OwnedCharacterUpdate(BaseModel):
    is_alive: Optional[bool] = None
    last_match_id: Optional[int] = None
    revival_count: Optional[int] = None


class OwnedCharacterInDBBase(OwnedCharacterBase):
    id: int
    is_alive: bool
    created_at: datetime
    last_match_id: Optional[int] = None
    revival_count: int

    model_config = ConfigDict(from_attributes=True)


class OwnedCharacter(OwnedCharacterInDBBase):
    pass
