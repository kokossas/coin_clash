from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ....db.session import get_db_dependency
from ....schemas.match import Match, MatchCreate, MatchUpdate
from ....crud.match import crud_match

router = APIRouter()

@router.get("/", response_model=List[Match])
def read_matches(
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve matches with pagination
    """
    matches = crud_match.get_multi(db, skip=skip, limit=limit)
    return matches

@router.post("/", response_model=Match)
def create_match(
    match_in: MatchCreate,
    db: Session = Depends(get_db_dependency)
):
    """
    Create new match
    """
    return crud_match.create(db, obj_in=match_in)

@router.get("/{match_id}", response_model=Match)
def read_match(
    match_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get match by ID
    """
    match = crud_match.get(db, id=match_id)
    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found"
        )
    return match

@router.put("/{match_id}", response_model=Match)
def update_match(
    match_id: int,
    match_in: MatchUpdate,
    db: Session = Depends(get_db_dependency)
):
    """
    Update match
    """
    match = crud_match.get(db, id=match_id)
    if not match:
        raise HTTPException(
            status_code=404,
            detail="Match not found"
        )
    return crud_match.update(db, db_obj=match, obj_in=match_in)
