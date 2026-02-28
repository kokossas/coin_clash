from typing import List
from sqlalchemy.orm import Session

from ..models.models import MatchEvent


class CRUDMatchEvent:

    def get_by_match_id(
        self,
        db: Session,
        match_id: int,
        *,
        after_event_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MatchEvent]:
        q = db.query(MatchEvent).filter(MatchEvent.match_id == match_id)
        if after_event_id is not None:
            q = q.filter(MatchEvent.id > after_event_id)
        return q.order_by(MatchEvent.id).offset(skip).limit(limit).all()


crud_match_event = CRUDMatchEvent()
