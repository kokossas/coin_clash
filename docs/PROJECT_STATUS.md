# Project Status — Ground Truth Audit

Last updated: 2026-02-27

---

## Architecture

```
old/          Archived pre-migration PoC (SQLite, owner_username identity). Reference only — nothing imports it.
core/         Adapted game engine. Match simulation, repos, scheduler, config loader, scenario loader.
              Imports ORM models from backend/app/models/models.py.
backend/      FastAPI application. Single source of truth for ORM models, schemas, CRUD, API, services.
              Imports core/ for match execution (via backend/app/services/match_runner.py).
scenarios/    JSON scenario files consumed by core/match/scenario_loader.py.
config.yaml   Game config (event weights, fees, protocol cut). Also contains legacy SQLite URL (see tech debt).
```

## Database

- **Production target**: PostgreSQL (configured in `backend/app/core/config.py` via env vars)
- **Tests**: In-memory SQLite (`backend/tests/conftest.py`)
- **Legacy**: `config.yaml` contains `database_url: "sqlite:///data/coin_clash.db"` — used only by `core/config/config_loader.py`, which requires it as a key. Not used by backend.
- **Migrations**: `alembic` is in `requirements.txt` but never configured. No `alembic/` directory exists.

## ORM Models (`backend/app/models/models.py`)

| Model | Key Fields |
|-------|-----------|
| Player | id (PK), wallet_address (unique, non-null), username (nullable), balance, wins, kills, total_sui_earned, wallet_chain_id |
| Character | id (PK), name, player_id (FK→players.id), match_id (FK→matches.id, nullable), is_alive |
| Match | id (PK), entry_fee, kill_award_rate, start_method, start_threshold, start_timer_end, start_timestamp, end_timestamp, winner_character_id, status, blockchain_tx_id, blockchain_settlement_status |
| MatchEvent | id (PK), match_id, round_number, event_type, scenario_source, scenario_text, affected_character_ids |
| Item | id (PK), name, type, rarity, description, on_find_hook_info, on_award_hook_info, token_id, token_uri |
| PlayerItem | player_id+item_id (composite PK), quantity |
| Transaction | id (PK), player_id, amount, currency, tx_type, status, provider, provider_tx_id |

Player identity: `wallet_address` is canonical (non-null, unique). `username` is display-only, auto-assigned as `Player_{wallet_address[:6]}` if null.

## Completed Migration Work (Pre-Phase 2.5 Cleanup)

All 6 steps from `docs/pre_phase_2.5_cleanup.md` are done in production code:

1. Player identity fixed — `wallet_address` non-null unique, `username` nullable
2. Character FK changed — `player_id` (int FK) replaces `owner_username`
3. `core/database/models.py` deleted, core repos import from `backend.app.models.models`
4. MatchEngine uses `player_id` (not `owner_username`) in `_handle_direct_kill` and `run_match`
5. `backend/app/services/match_runner.py` created — wires core repos and drives MatchEngine
6. `__main__.py` deleted

## What's Working

- **MatchEngine** (`core/match/engine.py`): full simulation with event types, elimination, revival, payouts
- **Core repos**: PlayerRepo, CharacterRepo, MatchRepo, EventRepo, ItemRepo — all use backend ORM models
- **match_runner** (`backend/app/services/match_runner.py`): wires all core deps, loads config/scenarios, runs engine
- **Scheduler** (`core/scheduler/scheduler.py`): thread-based task scheduler with priority queue, match start scheduling
- **Blockchain abstraction layer** (`backend/app/services/blockchain/`): complete and tested
  - Wallet, Payment, Transaction, Asset — each with abstract base + mock provider
  - Factory with singleton pattern
  - Error hierarchy (Temporary/Permanent/Unknown) + async retry with exponential backoff
  - Full test coverage in `backend/tests/services/blockchain/`
- **FastAPI app**: CORS, JWT auth scaffolding, CRUD endpoints for players/characters/matches/transactions
- **Scenario files**: 6 JSON files in `scenarios/` (comeback, direct_kill, environmental, group, self, story)

## Known Broken Things

### Tests not updated after identity migration
- `backend/tests/conftest.py`: `test_player` fixture creates `Player` without `wallet_address` (non-null column) — will fail
- `backend/tests/conftest.py`: `test_character` fixture uses `owner_username=test_player.username` — column doesn't exist
- `backend/tests/api/test_characters.py`: sends `owner_username` in create payload, asserts `owner_username` in responses
- `backend/tests/crud/test_character.py`: creates `CharacterCreate` with `owner_username`, calls `get_by_owner_username` (method doesn't exist)

### Schema bug
- `backend/app/schemas/match.py` `MatchInDBBase`: `start_timestamp: datetime` and `end_timestamp: datetime` are required fields, but these columns are null until match starts/ends. Any match read before completion will fail Pydantic validation. Fix: make both `Optional[datetime]`.

### Missing dependency
- `pydantic-settings` not in `backend/requirements.txt`. `backend/app/core/config.py` imports `from pydantic_settings import BaseSettings` — install will fail in clean env.

### Code issues
- `CharacterService.purchase_character` (`core/player/service.py`): takes `username: str` param, calls `get_player_by_username`. Should take `player_id: int` or `wallet_address: str` to match the new identity model.
- `core/common/utils.py`: `get_next_character_name()` defined twice (second shadows first). Both use module-level global counters that reset on process restart and aren't shared across workers.
- `backend/app/services/payment/`: redundant simple mock (player_id-based, no state tracking). The canonical mock is `backend/app/services/blockchain/payment/mock_provider.py` (wallet_address-based, balance tracking, tx history, configurable delays/failures). Nothing imports the simple mock.
- `config.yaml` + `core/config/config_loader.py`: `database_url` is a required key in the loader but the value (`sqlite:///data/coin_clash.db`) is legacy. Backend doesn't use it. Removing the key requires also removing it from `required_keys` in the loader.
