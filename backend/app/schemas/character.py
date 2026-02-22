from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CharacterBase(BaseModel):
    name: str
    player_id: int

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    player_id: Optional[int] = None
    match_id: Optional[int] = None
    is_alive: Optional[bool] = None

class CharacterInDBBase(CharacterBase):
    id: int
    match_id: Optional[int] = None
    is_alive: bool
    created_at: datetime

    class Config:
        orm_mode = True

class Character(CharacterInDBBase):
    pass
