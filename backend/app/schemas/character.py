from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CharacterBase(BaseModel):
    name: str
    player_id: int

class CharacterCreate(CharacterBase):
    match_id: Optional[int] = None
    owned_character_id: Optional[int] = None
    entry_order: int = 0

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    player_id: Optional[int] = None
    match_id: Optional[int] = None
    is_alive: Optional[bool] = None
    owned_character_id: Optional[int] = None
    entry_order: Optional[int] = None
    elimination_round: Optional[int] = None

class CharacterInDBBase(CharacterBase):
    id: int
    match_id: Optional[int] = None
    is_alive: bool
    created_at: datetime
    owned_character_id: Optional[int] = None
    entry_order: int = 0
    elimination_round: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class Character(CharacterInDBBase):
    pass
