from typing import List, Optional
from sqlalchemy.orm import Session

from .base import CRUDBase
from ..models.models import Transaction
from ..schemas.transaction import TransactionCreate, TransactionUpdate

class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    """CRUD operations for Transaction model"""
    
    def get_by_player_id(self, db: Session, player_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
        """Get transactions by player ID"""
        return db.query(Transaction).filter(Transaction.player_id == player_id).offset(skip).limit(limit).all()
    
    def get_by_status(self, db: Session, status: str) -> List[Transaction]:
        """Get transactions by status"""
        return db.query(Transaction).filter(Transaction.status == status).all()
    
    def get_by_provider_tx_id(self, db: Session, provider_tx_id: str) -> Optional[Transaction]:
        """Get transaction by provider transaction ID"""
        return db.query(Transaction).filter(Transaction.provider_tx_id == provider_tx_id).first()
    
    def update_status(self, db: Session, *, transaction_id: int, status: str) -> Transaction:
        """Update a transaction's status"""
        transaction = self.get(db, transaction_id)
        if transaction:
            transaction.status = status
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
        return transaction

crud_transaction = CRUDTransaction(Transaction)
