"""
Base repository interfaces and common repository functionality.
"""

from abc import ABC
from typing import TypeVar
from sqlalchemy.orm import Session

# Define generic type variables for repository pattern
T = TypeVar('T')

class BaseRepo(ABC):
    """Base repository class that all repositories inherit from."""
    
    def __init__(self, db_session: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session
