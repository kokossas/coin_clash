# Project Status — Ground Truth Audit

Last updated: 2026-02-28

---

## Architecture

```
old/          Archived pre-migration PoC (SQLite, owner_username identity). Reference only — nothing imports it.
core/         Adapted game engine. Match simulation, repos, scheduler, config loader, scenario loader.
              Imports ORM models from backend/app/models/models.py.
backend/      FastAPI application. Single source of truth for ORM models, schemas, CRUD, API, services.
              Imports core/ for match execution (via backend/app/services/match_runner.py).
scripts/      Dev tools. Match simulator (no DB required).
scenarios/    JSON scenario files consumed by core/match/scenario_loader.py.
config.yaml   Game config (event weights, fees, player limits, round delays, character pricing). Loaded as typed GameConfig model via core/config/config_loader.py.
```

## Database

- **Production target**: PostgreSQL (configured in `backend/app/core/config.py` via env vars)
- **Tests**: In-memory SQLite (`backend/tests/conftest.py`)
- **Migrations**: `alembic` is in `requirements.txt` but never configured. No `alembic/` directory exists.

## ORM Models (`backend/app/models/models.py`)

| Model | Key Fields |
|-------|-----------|
| Player | id (PK), wallet_address (unique, non-null), username (nullable), balance, wins, kills, total_earnings, wallet_chain_id |
| Character | id (PK), name, player_id (FK→players.id), match_id (FK→matches.id, nullable), is_alive, owned_character_id (FK→owned_characters.id), entry_order, elimination_round |
| Match | id (PK), entry_fee, kill_award_rate, start_method, start_threshold, start_timer_end, start_timestamp, end_timestamp, winner_character_id, status, blockchain_tx_id, blockchain_settlement_status, creator_wallet_address, min_players, max_characters, max_characters_per_player, countdown_started_at |
| MatchEvent | id (PK), match_id, round_number, event_type, scenario_source, scenario_text, affected_character_ids |
| Item | id (PK), name, type, rarity, description, on_find_hook_info, on_award_hook_info, token_id, token_uri |
| PlayerItem | player_id+item_id (composite PK), quantity |
| Transaction | id (PK), player_id, amount, currency, tx_type, status, provider, provider_tx_id |
| OwnedCharacter | id (PK), player_id (FK→players.id), character_name, is_alive, last_match_id (FK→matches.id), revival_count |
| MatchJoinRequest | id (PK), match_id (FK→matches.id), player_id (FK→players.id), entry_fee_total, protocol_fee, payment_status, confirmed_at |
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

- **MatchEngine** (`core/match/engine.py`): full simulation with event types, elimination, revival, round delay, post-match owned_character sync
- **Core repos**: PlayerRepo, CharacterRepo, MatchRepo, EventRepo, ItemRepo — all use backend ORM models
- **match_runner** (`backend/app/services/match_runner.py`): wires all core deps, loads config/scenarios, runs engine, triggers payout calculation and auto-settlement
- **Scheduler** (`core/scheduler/scheduler.py`): thread-based task scheduler with priority queue, match start scheduling
- **Blockchain abstraction layer** (`backend/app/services/blockchain/`): complete and tested
  - Wallet, Payment, Transaction, Asset — each with abstract base + mock provider
  - Factory with singleton pattern
  - Error hierarchy (Temporary/Permanent/Unknown) + async retry with exponential backoff
  - Full test coverage in `backend/tests/services/blockchain/`
- **CharacterInventoryService** (`backend/app/services/character_inventory.py`): purchase, inventory, revive
- **MatchLobbyService** (`backend/app/services/match_lobby.py`): create lobby, join match (atomic), check start conditions, payout calculation with tiered protocol fees
- **Payout calculator** (`backend/app/services/payout_calculator.py`): pure payout math extracted from MatchLobbyService — no DB/ORM dependency. Used by both the service (DB wrapper) and the simulator.
- **Match simulator** (`scripts/simulate_match.py`): CLI dev tool. Runs MatchEngine with in-memory stubs, real scenarios/config, computes payouts via payout_calculator. Supports uniform (`--chars-per-player`) and mixed (`--char-distribution 3,1,2,1`) character distributions with per-player tiered protocol fees.
- **SettlementService** (`backend/app/services/settlement.py`): iterates unsettled pending_payouts, calls PaymentProvider.process_withdrawal, marks settled. Auto-triggered post-match; manual endpoint as fallback.
- **FastAPI app**: CORS, wallet-signature auth (challenge/verify + `get_current_player` dependency), protected mutating endpoints, CRUD endpoints for players/characters/matches/transactions, Phase 2.5 endpoints (character purchase/inventory/revive, match create/open/join/events/status, player profile/match-history), match results endpoint, manual settle endpoint, `TaskScheduler` started on app lifespan
- **Auth flow** (`backend/app/services/auth/`): `POST /auth/challenge` issues nonce, `POST /auth/verify` verifies wallet signature via `WalletProvider`, auto-creates Player if new wallet, returns JWT with `wallet_address` + `player_id`. `get_current_player` dependency extracts JWT and resolves to `Player` DB row. Mutating endpoints (create/join/settle match, purchase/revive character, update player, profile) are protected. Read-only endpoints (open matches, match status/results/events, match history) remain public.
- **Config consolidation** (`core/config/game_config.py`): typed `GameConfig` pydantic model loaded from `config.yaml`. `load_config()` returns `GameConfig` instead of raw dict. All consumers use attribute access. Dead game values (`DEFAULT_FEE`, `KILL_AWARD_RATE_DEFAULT`) removed from pydantic `Settings`.
- **Scenario files**: 6 JSON files in `scenarios/` (comeback, direct_kill, environmental, group, self, story)

## Implementation Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | `characters` → `match_characters` rename strategy | Rename `__tablename__` in ORM in-place. Manual DDL rename needed on existing DB. |
| 2 | `created_at` on Match schema | `BaseModel` mixin provides it. No change needed. |
| 3 | `PlayerService` username-based lookups | Addressed in prerequisites (Step 0, items 9–11). |
| 4 | `MatchCreate` schema | Added `status` field (default `"pending"`) so `create_match_lobby` can set `"filling"`. |
| 5 | `CharacterCreate` schema | Added `match_id` and `entry_order` for `join_match` Character row creation. |
| 6 | `create_with_characters` atomicity | Changed from `commit`+`refresh` to `flush` so `join_match` controls the transaction boundary. |
| 7 | Auth for endpoints | Wallet-signature auth implemented (Phase 3). `get_current_player` dependency protects mutating endpoints. Player identity derived from JWT, no longer passed in request bodies. |
| 8 | `MatchEvent` schema/CRUD | Added `backend/app/schemas/match_event.py` and `backend/app/crud/match_event.py` for the events polling endpoint. |
| 9 | `TaskScheduler` lifecycle | Started/stopped via FastAPI lifespan handler in `main.py`. Countdown scheduling and round delay were already wired in Steps 4–6. |
| 10 | Protocol fee model | Replaced flat `protocol_fee_percentage` on Match with per-join `protocol_fee` on MatchJoinRequest. Tiered rates (1→10%, 2→8%, 3→6%) from `config.yaml`. Calculated at join time for auditability. |
| 11 | Settlement strategy | Auto-settlement after payout calculation in match_runner. Failure doesn't fail the match — payouts stay unsettled, retryable via `POST /matches/{id}/settle`. |
| 12 | Match results endpoint | `GET /matches/{id}/results` aggregates winner, per-player kills (from MatchEvent), and payout breakdown (including settlement status). |
| 13 | Auth flow | Wallet-signature challenge/verify. Nonce stored in-memory on `JWTAuthProvider` (matches mock-provider pattern). Production would use Redis/DB with TTL. |
| 14 | JWT payload | `sub` = `wallet_address`, `player_id` = int. `get_current_player` resolves JWT → `Player` DB row. |
| 15 | Player auto-creation | `POST /auth/verify` creates Player row if wallet_address not in DB. |
| 16 | Endpoint protection | Mutating endpoints (create/join/settle, purchase/revive, update player, profile) require Bearer token. Read-only public endpoints unchanged. Generic CRUD endpoints left unprotected (admin concern, out of scope). |
| 17 | player_id in request bodies | Removed from `JoinMatchRequest`, `PurchaseRequest`, `ReviveRequest`, `CreateLobbyRequest`. Derived from JWT via `get_current_player`. |
| 18 | Config consolidation | Typed `GameConfig` pydantic model. All consumers (`MatchEngine`, scripts, backend services) use attribute access. |

## Known Issues

### ~~Dual config systems with conflicting values~~ (Resolved)
- Resolved: typed `GameConfig` model (`core/config/game_config.py`) is now the single source of truth for game values. `load_config()` returns `GameConfig` instead of `Dict[str, Any]`. Dead game values (`DEFAULT_FEE`, `KILL_AWARD_RATE_DEFAULT`) removed from pydantic `Settings`. Infra config (DB, JWT, CORS) remains in pydantic-settings as intended.

### SUI naming throughout codebase
- Rename done: `total_earnings` / `add_earnings` in model + repo, `currency="USDC"` in tests.
- One stale `# TODO: Implement actual SUI transfer/logging` comment remains in `core/match/engine.py` `run_match`.
- Docstring examples in `backend/app/services/blockchain/payment/base.py` and `transaction/base.py` still mention "SUI" as an example currency code — cosmetic only.

### Engine payout changes (Steps 4-5)
- `_calculate_payouts` removed from engine. `add_earnings` removed from `_handle_direct_kill` (kill tracking via `add_kill` retained). Balance manipulation removed from `run_match`.
- Payouts now computed post-match by `MatchLobbyService.calculate_and_store_payouts` (calls pure `calculate_payouts` from `payout_calculator.py`, then persists results). Protocol fee summed from per-join `protocol_fee` values on confirmed `MatchJoinRequest` rows.
- `match_runner.py` calls `calculate_and_store_payouts` after `engine.run_match()`, then triggers `SettlementService.settle_match()` (failure logged, doesn't block).

### Minor issues
- None currently tracked. Previous items (EventRepo sort column, character_repository bool assignment, Pydantic v1 orm_mode in new schemas) all fixed in `496bea9` / `13d1f39`.
