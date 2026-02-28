from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....crud.player import crud_player
from ....db.session import get_db_dependency
from ....schemas.auth import ChallengeRequest, ChallengeResponse, VerifyRequest
from ....schemas.player import PlayerCreate
from ....schemas.token import Token
from ....services.auth.jwt_provider import JWTAuthProvider

router = APIRouter()
_auth_provider = JWTAuthProvider()


@router.post("/challenge", response_model=ChallengeResponse)
async def request_challenge(body: ChallengeRequest):
    nonce = await _auth_provider.create_challenge(body.wallet_address)
    return ChallengeResponse(
        wallet_address=body.wallet_address.lower(),
        nonce=nonce,
    )


@router.post("/verify", response_model=Token)
async def verify_signature(
    body: VerifyRequest,
    db: Session = Depends(get_db_dependency),
):
    is_valid = await _auth_provider.verify_challenge(
        wallet_address=body.wallet_address,
        signature=body.signature,
        nonce=body.nonce,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature or expired nonce",
        )

    addr = body.wallet_address.lower()
    player = crud_player.get_by_wallet_address(db, wallet_address=addr)
    if player is None:
        player = crud_player.create(db, obj_in=PlayerCreate(wallet_address=addr))

    access_token = await _auth_provider.generate_token(
        wallet_address=addr,
        player_id=player.id,
    )
    return Token(access_token=access_token, token_type="bearer")
