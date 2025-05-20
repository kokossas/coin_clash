from fastapi import APIRouter

from .endpoints import players, matches, characters, auth, transactions

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(characters.router, prefix="/characters", tags=["characters"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
