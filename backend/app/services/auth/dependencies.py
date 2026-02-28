from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ...crud.player import crud_player
from ...db.session import get_db_dependency
from ...models.models import Player
from .jwt_provider import JWTAuthProvider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/verify")
_auth_provider = JWTAuthProvider()


async def get_current_player(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_dependency),
) -> Player:
    payload = await _auth_provider.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    player = crud_player.get(db, id=payload["player_id"])
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Player not found",
        )
    return player
