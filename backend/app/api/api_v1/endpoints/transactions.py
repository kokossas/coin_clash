from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ....db.session import get_db_dependency
from ....models.models import Player
from ....schemas.transaction import Transaction, TransactionCreate, TransactionUpdate
from ....crud.transaction import crud_transaction
from ....services.auth.dependencies import get_current_player

router = APIRouter()


@router.get("/", response_model=List[Transaction])
def read_transactions(
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100,
):
    return crud_transaction.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=Transaction)
def create_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db_dependency),
):
    return crud_transaction.create(db, obj_in=transaction_in)


@router.get("/{transaction_id}", response_model=Transaction)
def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db_dependency),
):
    transaction = crud_transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/{transaction_id}", response_model=Transaction)
def update_transaction(
    transaction_id: int,
    transaction_in: TransactionUpdate,
    db: Session = Depends(get_db_dependency),
):
    transaction = crud_transaction.get(db, id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return crud_transaction.update(db, db_obj=transaction, obj_in=transaction_in)


@router.get("/player/me", response_model=List[Transaction])
def read_my_transactions(
    current_player: Player = Depends(get_current_player),
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100,
):
    return crud_transaction.get_by_player_id(
        db, player_id=current_player.id, skip=skip, limit=limit,
    )


@router.get("/player/{player_id}", response_model=List[Transaction])
def read_player_transactions(
    player_id: int,
    db: Session = Depends(get_db_dependency),
    skip: int = 0,
    limit: int = 100,
):
    return crud_transaction.get_by_player_id(
        db, player_id=player_id, skip=skip, limit=limit,
    )
