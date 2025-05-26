from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CharacterBase(BaseModel):
    name: str
    owner_username: str

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(CharacterBase):
    name: Optional[str] = None
    owner_username: Optional[str] = None
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
