from pydantic import BaseModel
from typing import Optional

class TokenBase(BaseModel):
    access_token: str
    token_type: str

class Token(TokenBase):
    pass

class TokenPayload(BaseModel):
    sub: Optional[int] = None
