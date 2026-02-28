from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ....crud.match import crud_match
from ....crud.match_event import crud_match_event
from ....db.session import get_db_dependency
from ....models.models import Character, Match
from ....schemas.match import Match as MatchSchema, MatchCreate, MatchUpdate
from ....schemas.match_event import MatchEvent as MatchEventSchema
from ....schemas.match_join_request import MatchJoinRequest as MatchJoinRequestSchema
from ....services.match_lobby import MatchLobbyService

router = APIRouter()


class CreateLobbyRequest(BaseModel):
    creator_wallet_address: str
    entry_fee: float
    kill_award_rate: float
    start_method: str
    start_threshold: int
    min_players: int = 3
    max_characters: int = 20
    max_characters_per_player: int = 3
    protocol_fee_percentage: Decimal = Decimal("10.0")


class JoinMatchRequest(BaseModel):
    player_id: int
    character_ids: List[int]
    payment_ref: str


class MatchStatusResponse(BaseModel):
    match_id: int
    status: str
    entry_fee: float
    total_characters: int
    unique_players: int
    max_characters: int
    min_players: int
    countdown_started_at: Optional[str] = None
    winner_character_id: Optional[int] = None


@router.post("/create", response_model=MatchSchema)
async def create_match_lobby(
    body: CreateLobbyRequest,
    db: Session = Depends(get_db_dependency),
):
    service = MatchLobbyService()
    try:
        return await service.create_match_lobby(
            db,
            creator_wallet_address=body.creator_wallet_address,
            entry_fee=body.entry_fee,
            kill_award_rate=body.kill_award_rate,
            start_method=body.start_method,
            start_threshold=body.start_threshold,
            min_players=body.min_players,
            max_characters=body.max_characters,
            max_characters_per_player=body.max_characters_per_player,
            protocol_fee_percentage=body.protocol_fee_percentage,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/open", response_model=List[MatchSchema])
def get_open_matches(
    min_fee: Optional[float] = None,
    max_fee: Optional[float] = None,
    has_slots: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_dependency),
):
    q = db.query(Match).filter(Match.status == "filling")
    if min_fee is not None:
        q = q.filter(Match.entry_fee >= min_fee)
    if max_fee is not None:
        q = q.filter(Match.entry_fee <= max_fee)
    matches = q.offset(skip).limit(limit).all()
    if has_slots:
        result = []
        for m in matches:
            count = (
                db.query(func.count(Character.id))
                .filter(Character.match_id == m.id)
                .scalar()
            ) or 0
            if count < m.max_characters:
                result.append(m)
        return result
    return matches


@router.post("/{match_id}/join", response_model=MatchJoinRequestSchema)
async def join_match(
    match_id: int,
    body: JoinMatchRequest,
    db: Session = Depends(get_db_dependency),
):
    service = MatchLobbyService()
    try:
        return await service.join_match(
            db,
            match_id=match_id,
            player_id=body.player_id,
            owned_character_ids=body.character_ids,
            payment_ref=body.payment_ref,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{match_id}/events", response_model=List[MatchEventSchema])
def get_match_events(
    match_id: int,
    after_event_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db_dependency),
):
    match = crud_match.get(db, id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return crud_match_event.get_by_match_id(
        db, match_id, after_event_id=after_event_id, limit=limit,
    )


@router.get("/{match_id}/status", response_model=MatchStatusResponse)
def get_match_status(
    match_id: int,
    db: Session = Depends(get_db_dependency),
):
    match = crud_match.get(db, id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    characters = (
        db.query(Character).filter(Character.match_id == match_id).all()
    )
    unique_players = len({c.player_id for c in characters})

    return MatchStatusResponse(
        match_id=match.id,
        status=match.status,
        entry_fee=match.entry_fee,
        total_characters=len(characters),
        unique_players=unique_players,
        max_characters=match.max_characters,
        min_players=match.min_players,
        countdown_started_at=(
            match.countdown_started_at.isoformat()
            if match.countdown_started_at
            else None
        ),
        winner_character_id=match.winner_character_id,
    )


# --- Existing generic CRUD endpoints below ---


@router.get("/", response_model=List[MatchSchema])
def read_matches(
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100,
):
    return crud_match.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=MatchSchema)
def create_match(
    match_in: MatchCreate,
    db: Session = Depends(get_db_dependency),
):
    return crud_match.create(db, obj_in=match_in)


@router.get("/{match_id}", response_model=MatchSchema)
def read_match(
    match_id: int,
    db: Session = Depends(get_db_dependency),
):
    match = crud_match.get(db, id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.put("/{match_id}", response_model=MatchSchema)
def update_match(
    match_id: int,
    match_in: MatchUpdate,
    db: Session = Depends(get_db_dependency),
):
    match = crud_match.get(db, id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return crud_match.update(db, db_obj=match, obj_in=match_in)
