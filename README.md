# Coin Clash

Multiplayer survival game where players purchase characters, enter matches, compete through randomized events, and earn rewards. Being built toward a Web3 gambling platform with blockchain settlement.

## Project Structure

```
backend/        FastAPI application — API, ORM models (single source of truth), schemas, CRUD, services
core/           Game engine — match simulation, repositories, scheduler, config/scenario loading
scenarios/      JSON event scenario files (direct_kill, environmental, group, self, story, comeback)
old/            Archived pre-migration PoC. Not imported by anything. Kept as reference.
config.yaml     Game configuration (event weights, fees, player limits, round delays)
docs/           PROJECT_STATUS.md (ground truth audit), PHASE_2.5_SPEC.md (next phase spec)
```

### Backend Services

```
backend/app/services/
  auth/           JWT authentication (base + provider)
  blockchain/     Blockchain abstraction layer — wallet, payment, transaction, asset
                  Each has abstract base + mock provider. Factory with singleton pattern.
                  Error hierarchy + async retry with exponential backoff.
  match_runner.py Wires core/ repos and drives MatchEngine
```

## Current State

**Completed:**
- Phase 1: PostgreSQL migration, FastAPI REST API, JWT auth scaffolding, service layer
- Phase 2: Blockchain abstraction layer (all 4 interfaces + mocks + tests + retry + factory)
- Pre-Phase 2.5 cleanup: player identity migration (wallet_address canonical), model consolidation, engine wiring
- Phase 2.5 Steps 0–6: tech debt, DB models, schemas/CRUD, CharacterInventoryService, MatchLobbyService, payout calculation, engine changes

**Next:** Phase 2.5 Steps 7–8 — API endpoints, background tasks. See `docs/PHASE_2.5_PLAN.md`.

**Known issues:** see `docs/PROJECT_STATUS.md` § "Known Issues"

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 13+

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Database

```bash
createdb coin_clash
```

Set env vars (or use defaults in `backend/app/core/config.py`):
```
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=coin_clash
POSTGRES_PORT=5432
```

### Run

```bash
uvicorn backend.app.main:app --reload
```

API docs at `http://localhost:8000/docs`

### Tests

Run from the project root with the venv activated (`source .venv/bin/activate`):

```bash
python -m pytest
```

This picks up both `backend/tests/` and `core/tests/` via `pyproject.toml` config. Or use the script:

```bash
./run_tests.sh
```
