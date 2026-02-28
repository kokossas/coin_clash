from sqlalchemy.orm import Session

from app.crud.transaction import crud_transaction
from app.schemas.transaction import TransactionCreate
from app.models.models import Transaction

def test_create_transaction(db_session: Session):
    player_id = 1
    amount = 25.0
    currency = "USDC"
    tx_type = "deposit"
    status = "pending"
    provider = "mock"
    
    transaction_in = TransactionCreate(
        player_id=player_id,
        amount=amount,
        currency=currency,
        tx_type=tx_type,
        status=status,
        provider=provider
    )
    transaction = crud_transaction.create(db_session, obj_in=transaction_in)
    
    assert transaction.player_id == player_id
    assert transaction.amount == amount
    assert transaction.currency == currency
    assert transaction.tx_type == tx_type
    assert transaction.status == status
    assert transaction.provider == provider
    assert transaction.provider_tx_id is None

def test_get_transaction(db_session: Session, test_transaction: Transaction):
    transaction = crud_transaction.get(db_session, id=test_transaction.id)
    assert transaction
    assert transaction.id == test_transaction.id
    assert transaction.player_id == test_transaction.player_id
    assert transaction.amount == test_transaction.amount

def test_get_by_player_id(db_session: Session, test_transaction: Transaction):
    transactions = crud_transaction.get_by_player_id(db_session, player_id=test_transaction.player_id)
    assert len(transactions) > 0
    assert test_transaction.id in [t.id for t in transactions]

def test_get_by_status(db_session: Session, test_transaction: Transaction):
    transactions = crud_transaction.get_by_status(db_session, status=test_transaction.status)
    assert len(transactions) > 0
    assert test_transaction.id in [t.id for t in transactions]

def test_update_status(db_session: Session, test_transaction: Transaction):
    new_status = "failed"
    updated_transaction = crud_transaction.update_status(
        db_session, transaction_id=test_transaction.id, status=new_status
    )
    
    assert updated_transaction.status == new_status
