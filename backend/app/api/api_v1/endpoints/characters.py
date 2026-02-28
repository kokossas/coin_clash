from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ....db.session import get_db_dependency
from ....schemas.character import Character, CharacterCreate, CharacterUpdate
from ....crud.character import crud_character

router = APIRouter()

@router.get("/", response_model=List[Character])
def read_characters(
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve characters with pagination
    """
    characters = crud_character.get_multi(db, skip=skip, limit=limit)
    return characters

@router.post("/", response_model=Character)
def create_character(
    character_in: CharacterCreate,
    db: Session = Depends(get_db_dependency)
):
    """
    Create new character
    """
    return crud_character.create(db, obj_in=character_in)

@router.get("/{character_id}", response_model=Character)
def read_character(
    character_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Get character by ID
    """
    character = crud_character.get(db, id=character_id)
    if not character:
        raise HTTPException(
            status_code=404,
            detail="Character not found"
        )
    return character

@router.put("/{character_id}", response_model=Character)
def update_character(
    character_id: int,
    character_in: CharacterUpdate,
    db: Session = Depends(get_db_dependency)
):
    """
    Update character
    """
    character = crud_character.get(db, id=character_id)
    if not character:
        raise HTTPException(
            status_code=404,
            detail="Character not found"
        )
    return crud_character.update(db, db_obj=character, obj_in=character_in)

@router.post("/{character_id}/assign-to-match/{match_id}", response_model=Character)
def assign_character_to_match(
    character_id: int,
    match_id: int,
    db: Session = Depends(get_db_dependency)
):
    """
    Assign character to match
    """
    character = crud_character.get(db, id=character_id)
    if not character:
        raise HTTPException(
            status_code=404,
            detail="Character not found"
        )
    return crud_character.assign_to_match(db, character_id=character_id, match_id=match_id)
