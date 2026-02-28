from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ....crud.match import crud_match
from ....crud.match_event import crud_match_event
from ....crud.pending_payout import crud_pending_payout
from ....db.session import get_db_dependency
from ....models.models import Character, Match, MatchEvent as MatchEventModel
from ....schemas.match import Match as MatchSchema, MatchCreate, MatchUpdate
from ....schemas.match_event import MatchEvent as MatchEventSchema
from ....schemas.match_join_request import MatchJoinRequest as MatchJoinRequestSchema
from ....schemas.pending_payout import PendingPayout as PendingPayoutSchema
from ....services.match_lobby import MatchLobbyService
from ....services.settlement import SettlementService

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


class PlayerResultEntry(BaseModel):
    player_id: int
    kills: int
    payouts: List[PendingPayoutSchema]


class MatchResultsResponse(BaseModel):
    match_id: int
    status: str
    winner_player_id: Optional[int] = None
    winner_character_id: Optional[int] = None
    players: List[PlayerResultEntry]


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


@router.post("/{match_id}/settle", response_model=List[PendingPayoutSchema])
async def settle_match(
    match_id: int,
    db: Session = Depends(get_db_dependency),
):
    match = crud_match.get(db, id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != "completed":
        raise HTTPException(status_code=400, detail="Match is not completed")
    service = SettlementService()
    return await service.settle_match(db, match_id)


@router.get("/{match_id}/results", response_model=MatchResultsResponse)
def get_match_results(
    match_id: int,
    db: Session = Depends(get_db_dependency),
):
    match = crud_match.get(db, id=match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status not in ("completed", "failed"):
        raise HTTPException(status_code=400, detail="Match has not ended")

    characters = (
        db.query(Character).filter(Character.match_id == match_id).all()
    )
    char_to_player = {c.id: c.player_id for c in characters}
    player_ids = {c.player_id for c in characters}

    kill_events = (
        db.query(MatchEventModel)
        .filter(
            MatchEventModel.match_id == match_id,
            MatchEventModel.event_type == "direct_kill",
        )
        .all()
    )
    kills_per_player: dict[int, int] = {pid: 0 for pid in player_ids}
    for event in kill_events:
        if not event.affected_character_ids:
            continue
        killer_char_id = int(event.affected_character_ids.split(",")[0].strip())
        killer_player_id = char_to_player.get(killer_char_id)
        if killer_player_id is not None:
            kills_per_player[killer_player_id] = kills_per_player.get(killer_player_id, 0) + 1

    payouts = crud_pending_payout.get_by_match_id(db, match_id)
    payouts_by_player: dict[int, list] = {pid: [] for pid in player_ids}
    for p in payouts:
        payouts_by_player.setdefault(p.player_id, []).append(p)

    winner_player_id = None
    if match.winner_character_id is not None:
        winner_player_id = char_to_player.get(match.winner_character_id)

    players = [
        PlayerResultEntry(
            player_id=pid,
            kills=kills_per_player.get(pid, 0),
            payouts=payouts_by_player.get(pid, []),
        )
        for pid in player_ids
    ]

    return MatchResultsResponse(
        match_id=match.id,
        status=match.status,
        winner_player_id=winner_player_id,
        winner_character_id=match.winner_character_id,
        players=players,
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
