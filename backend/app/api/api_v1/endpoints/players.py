from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ....crud.match import crud_match
from ....crud.pending_payout import crud_pending_payout
from ....crud.player import crud_player
from ....db.session import get_db_dependency
from ....models.models import Character, Match
from ....schemas.pending_payout import PendingPayout as PendingPayoutSchema
from ....schemas.player import Player, PlayerCreate, PlayerUpdate

router = APIRouter()


class PlayerProfile(BaseModel):
    id: int
    wallet_address: str
    username: Optional[str] = None
    balance: float
    wins: int
    kills: int
    total_earnings: float
    pending_payouts: List[PendingPayoutSchema]


class MatchHistoryEntry(BaseModel):
    match_id: int
    status: str
    entry_fee: float
    character_count: int
    created_at: str


@router.get("/profile", response_model=PlayerProfile)
def get_player_profile(
    player_id: int,
    db: Session = Depends(get_db_dependency),
):
    player = crud_player.get(db, id=player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    payouts = crud_pending_payout.get_unsettled_by_player(db, player_id=player_id)
    return PlayerProfile(
        id=player.id,
        wallet_address=player.wallet_address,
        username=player.username,
        balance=player.balance,
        wins=player.wins,
        kills=player.kills,
        total_earnings=player.total_earnings,
        pending_payouts=payouts,
    )


@router.get("/{address}/match-history", response_model=List[MatchHistoryEntry])
def get_match_history(
    address: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_dependency),
):
    player = crud_player.get_by_wallet_address(db, wallet_address=address)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    rows = (
        db.query(
            Character.match_id,
            func.count(Character.id).label("char_count"),
        )
        .filter(Character.player_id == player.id, Character.match_id.isnot(None))
        .group_by(Character.match_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not rows:
        return []

    match_ids = [r[0] for r in rows]
    char_counts = {r[0]: r[1] for r in rows}
    matches = db.query(Match).filter(Match.id.in_(match_ids)).all()

    return [
        MatchHistoryEntry(
            match_id=m.id,
            status=m.status,
            entry_fee=m.entry_fee,
            character_count=char_counts.get(m.id, 0),
            created_at=m.created_at.isoformat(),
        )
        for m in matches
    ]


# --- Existing generic CRUD endpoints below ---


@router.get("/", response_model=List[Player])
def read_players(
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100,
):
    return crud_player.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=Player)
def create_player(
    player_in: PlayerCreate,
    db: Session = Depends(get_db_dependency),
):
    existing = crud_player.get_by_wallet_address(db, wallet_address=player_in.wallet_address)
    if existing:
        raise HTTPException(status_code=400, detail="Wallet address already registered")
    return crud_player.create(db, obj_in=player_in)


@router.get("/{player_id}", response_model=Player)
def read_player(
    player_id: int,
    db: Session = Depends(get_db_dependency),
):
    player = crud_player.get(db, id=player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.put("/{player_id}", response_model=Player)
def update_player(
    player_id: int,
    player_in: PlayerUpdate,
    db: Session = Depends(get_db_dependency),
):
    player = crud_player.get(db, id=player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return crud_player.update(db, db_obj=player, obj_in=player_in)


@router.get("/by-username/{username}", response_model=Player)
def read_player_by_username(
    username: str,
    db: Session = Depends(get_db_dependency),
):
    player = crud_player.get_by_username(db, username=username)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
