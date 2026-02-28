# Coin Clash

Multiplayer survival game where players purchase characters, enter matches, compete through randomized events, and earn rewards. Being built toward a Web3 gambling platform with blockchain settlement.

## Project Structure

```
backend/        FastAPI application — API, ORM models (single source of truth), schemas, CRUD, services
core/           Game engine — match simulation, repositories, scheduler, config/scenario loading
scenarios/      JSON event scenario files (direct_kill, environmental, group, self, story, comeback)
scripts/        Dev tools (match simulator)
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
  character_inventory.py  Purchase, inventory, revive owned characters
  match_lobby.py          Create lobby, join match, check start conditions, payout calculation
  match_runner.py         Wires core/ repos and drives MatchEngine, triggers settlement
  settlement.py           Settle pending payouts via PaymentProvider (auto + manual)
  payout_calculator.py    Pure payout math (no DB) — used by match_lobby and simulator
```

## Current State

**Completed:**
- Phase 1: PostgreSQL migration, FastAPI REST API, JWT auth scaffolding, service layer
- Phase 2: Blockchain abstraction layer (all 4 interfaces + mocks + tests + retry + factory)
- Pre-Phase 2.5 cleanup: player identity migration (wallet_address canonical), model consolidation, engine wiring
- Phase 2.5 Steps 0–8: tech debt, DB models, schemas/CRUD, CharacterInventoryService, MatchLobbyService, payout calculation, engine changes, API endpoints, background tasks
- Game economy completion: tiered protocol fees (per-join, from config.yaml), SettlementService (auto + manual), match results endpoint

**Next:** Phase 3 — Auth / wallet signature verification. See `docs/PROJECT_STATUS.md`.

**Known issues:** see `docs/PROJECT_STATUS.md` § "Known Issues"

## Simulator

Run a full match simulation without a database:

```bash
# Uniform: 6 players, 2 chars each
python scripts/simulate_match.py --players 6 --chars-per-player 2 --entry-fee 1.0 --seed 42

# Mixed distribution: 4 players with 3, 1, 2, 1 chars respectively
python scripts/simulate_match.py --char-distribution 3,1,2,1 --entry-fee 1.0 --seed 7
```

Outputs round-by-round match log and economic summary (pool, protocol fees, kill awards, winner payout). Uses real scenarios from `scenarios/` and config from `config.yaml`. `--char-distribution` overrides `--players` and `--chars-per-player`.

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
