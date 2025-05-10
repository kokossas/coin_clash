from fastapi import FastAPI
from api.routers.matches import router as matches_router

app = FastAPI(title="Coin Clash API")
app.include_router(matches_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
