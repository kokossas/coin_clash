from contextlib import contextmanager
from .models import SessionLocal

@contextmanager
def get_session():
    """
    Context-managed DB session: commits on success, rolls back on error,
    and always closes the session.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()