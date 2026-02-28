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
| Character | id (PK), name, player_id (FK→players.id), match_id (FK→matches.id, nullable), is_alive, owned_character_id (FK→owned_characters.id), entry_order, elimination_round |
| Match | id (PK), entry_fee, kill_award_rate, start_method, start_threshold, start_timer_end, start_timestamp, end_timestamp, winner_character_id, status, blockchain_tx_id, blockchain_settlement_status, creator_wallet_address, min_players, max_characters, max_characters_per_player, protocol_fee_percentage, countdown_started_at |
| MatchEvent | id (PK), match_id, round_number, event_type, scenario_source, scenario_text, affected_character_ids |
| Item | id (PK), name, type, rarity, description, on_find_hook_info, on_award_hook_info, token_id, token_uri |
| PlayerItem | player_id+item_id (composite PK), quantity |
| Transaction | id (PK), player_id, amount, currency, tx_type, status, provider, provider_tx_id |
| OwnedCharacter | id (PK), player_id (FK→players.id), character_name, is_alive, last_match_id (FK→matches.id), revival_count |
| MatchJoinRequest | id (PK), match_id (FK→matches.id), player_id (FK→players.id), entry_fee_total, payment_status, confirmed_at |
| MatchJoinRequestCharacter | join_request_id+owned_character_id (composite PK) |
| PendingPayout | id (PK), match_id (FK→matches.id), player_id (FK→players.id), payout_type, amount, currency, calculated_at, settled_at, settlement_tx_hash |

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

## Known Issues

### Dual config systems with conflicting values
- `backend/app/core/config.py` (pydantic-settings, env-var driven): `KILL_AWARD_RATE_DEFAULT = 0.5`
- `config.yaml` (YAML, loaded by `core/config/config_loader.py`): `kill_award_rate_default: 0.1`
- They don't cross paths today — engine reads YAML only, FastAPI Settings used for infra/DB only — but it's a latent source-of-truth conflict.
- Consolidating config systems is an architectural decision outside Phase 2.5 scope.

### SUI naming throughout codebase
- `Player.total_sui_earned` column, `add_sui_earned()` repo method, schema fields, engine calls — all reference "SUI" but project uses USDC.
- Test fixtures also hardcode `currency="SUI"`.
- Pending rename to `total_earnings` / `add_earnings`.

### Engine payout issues
- `_handle_direct_kill` pays kill awards immediately via `add_sui_earned`. `_calculate_payouts` re-estimates them at match end. Double-counting.
- `_calculate_payouts` reads `config["protocol_cut"]["1"]` (tiered YAML config) instead of `Match.protocol_fee_percentage` (per-match column defined in Phase 2.5 spec).

### Minor issues
- `core/match/event_repository.py`: `.order_by(MatchEvent.timestamp)` — column doesn't exist, should be `.created_at`.
- `core/player/character_repository.py`: `character.is_alive = 1 if is_alive else 0` — sets int on Boolean column.
- `backend/app/schemas/match_join_request.py`, `pending_payout.py`: use Pydantic v1 `orm_mode = True` while all other schemas use v2 `ConfigDict(from_attributes=True)`.
