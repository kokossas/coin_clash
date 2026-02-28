from abc import ABC
from typing import TypeVar
from sqlalchemy.orm import Session

T = TypeVar('T')

class BaseRepo(ABC):
    """Base repository class that all repositories inherit from."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
