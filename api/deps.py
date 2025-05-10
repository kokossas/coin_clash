from fastapi import Depends
from core.db import get_session

def get_db():
    # FastAPI will call this per-request to yield a transactional session
    with get_session() as session:
        yield session
