from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ....db.session import get_db_dependency
from ....schemas.character import Character, CharacterCreate, CharacterUpdate
from ....schemas.owned_character import OwnedCharacter
from ....crud.character import crud_character
from ....services.character_inventory import CharacterInventoryService
from core.config.config_loader import load_config
from pydantic import BaseModel

router = APIRouter()


class PurchaseRequest(BaseModel):
    player_id: int
    quantity: int
    payment_ref: str


class ReviveRequest(BaseModel):
    player_id: int
    payment_ref: str


class RevivalFeeResponse(BaseModel):
    character_id: int
    revival_fee: float
    currency: str = "USDC"


@router.post("/purchase", response_model=List[OwnedCharacter])
async def purchase_characters(
    body: PurchaseRequest,
    db: Session = Depends(get_db_dependency),
):
    service = CharacterInventoryService()
    try:
        return await service.purchase_characters(
            db,
            player_id=body.player_id,
            quantity=body.quantity,
            payment_ref=body.payment_ref,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inventory", response_model=List[OwnedCharacter])
def get_inventory(
    player_id: int,
    alive_only: bool = False,
    db: Session = Depends(get_db_dependency),
):
    service = CharacterInventoryService()
    return service.get_player_inventory(db, player_id=player_id, alive_only=alive_only)


@router.get("/{character_id}/revival-fee", response_model=RevivalFeeResponse)
def get_revival_fee(character_id: int):
    config = load_config()
    return RevivalFeeResponse(
        character_id=character_id,
        revival_fee=config["character_revival_fee"],
    )


@router.post("/{character_id}/revive", response_model=OwnedCharacter)
async def revive_character(
    character_id: int,
    body: ReviveRequest,
    db: Session = Depends(get_db_dependency),
):
    service = CharacterInventoryService()
    try:
        return await service.revive_character(
            db,
            character_id=character_id,
            player_id=body.player_id,
            payment_ref=body.payment_ref,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Existing generic CRUD endpoints below ---


@router.get("/", response_model=List[Character])
def read_characters(
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100,
):
    return crud_character.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=Character)
def create_character(
    character_in: CharacterCreate,
    db: Session = Depends(get_db_dependency),
):
    return crud_character.create(db, obj_in=character_in)


@router.get("/{character_id}", response_model=Character)
def read_character(
    character_id: int,
    db: Session = Depends(get_db_dependency),
):
    character = crud_character.get(db, id=character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.put("/{character_id}", response_model=Character)
def update_character(
    character_id: int,
    character_in: CharacterUpdate,
    db: Session = Depends(get_db_dependency),
):
    character = crud_character.get(db, id=character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return crud_character.update(db, db_obj=character, obj_in=character_in)


@router.post("/{character_id}/assign-to-match/{match_id}", response_model=Character)
def assign_character_to_match(
    character_id: int,
    match_id: int,
    db: Session = Depends(get_db_dependency),
):
    character = crud_character.get(db, id=character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return crud_character.assign_to_match(db, character_id=character_id, match_id=match_id)
