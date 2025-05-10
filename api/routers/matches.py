from fastapi import APIRouter, Depends, HTTPException
from core.repositories import SqlMatchRepo
from api.schemas import MatchCreate, MatchResponse
from api.deps import get_db

router = APIRouter(prefix="/matches", tags=["matches"])

@router.post("/", response_model=MatchResponse)
def create_match(payload: MatchCreate, db = Depends(get_db)):
    repo = SqlMatchRepo(db)
    # This will add & flush, but commit happens when the request ends
    match = repo.create_match(
        entry_fee=payload.entry_fee,
        kill_award_rate=payload.kill_award_rate,
        start_method=payload.start_method,
        start_threshold=payload.start_threshold
    )  # id populated after flush :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}
    return {"match_id": match.id}
