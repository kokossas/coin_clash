from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from ....db.session import get_db_dependency
from ....schemas.player import Player, PlayerCreate, PlayerUpdate
from ....crud.player import crud_player

router = APIRouter()

@router.get("/", response_model=List[Player])
def read_players(
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve players with pagination
    """
    players = crud_player.get_multi(db, skip=skip, limit=limit)
    return players

@router.post("/", response_model=Player)
def create_player(
    player_in: PlayerCreate,
    db: Session = Depends(get_db_dependency)
):
    """
    Create new player
    """
    player = crud_player.get_by_username(db, username=player_in.username)
    if player:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    return crud_player.create(db, obj_in=player_in)

@router.get("/{player_id}", response_model=Player)
def read_player(
    player_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get player by ID
    """
    player = crud_player.get(db, id=player_id)
    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )
    return player

@router.put("/{player_id}", response_model=Player)
def update_player(
    player_id: int,
    player_in: PlayerUpdate,
    db: Session = Depends(get_db_dependency)
):
    """
    Update player
    """
    player = crud_player.get(db, id=player_id)
    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )
    return crud_player.update(db, db_obj=player, obj_in=player_in)

@router.get("/by-username/{username}", response_model=Player)
def read_player_by_username(
    username: str,
    db: Session = Depends(get_db_dependency)
):
    """
    Get player by username
    """
    player = crud_player.get_by_username(db, username=username)
    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )
    return player
