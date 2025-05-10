from pydantic import BaseModel

class MatchCreate(BaseModel):
    entry_fee: float
    kill_award_rate: float
    start_method: str   # "cap" or "timeout"
    start_threshold: int

class MatchResponse(BaseModel):
    match_id: int
