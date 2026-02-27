# Phase 2.5 Specification — Character Inventory, Match Lobbies, Mock Payments

---

## Goal

Add character inventory (persistent ownership across matches), match lobby creation/joining, mock payment integration, and round delays to the existing engine. No real blockchain. No frontend.

---

## Prerequisites — Tech Debt Fixes

These must be completed before any Phase 2.5 feature work.

| # | Issue | Fix | Files |
|---|-------|-----|-------|
| 1 | Tests use `owner_username` and missing `wallet_address` | Update all fixtures and assertions to use `player_id`/`wallet_address` | `backend/tests/conftest.py`, `backend/tests/api/test_characters.py`, `backend/tests/crud/test_character.py` |
| 2 | `MatchInDBBase` timestamps required but null on creation | Make `start_timestamp` and `end_timestamp` `Optional[datetime]` | `backend/app/schemas/match.py` |
| 3 | `pydantic-settings` missing from requirements | Add `pydantic-settings>=2.0` | `backend/requirements.txt` |
| 4 | `CharacterService.purchase_character` takes `username` | Change to `player_id: int` | `core/player/service.py` |
| 5 | Duplicate `get_next_character_name()`, global counter | Remove duplicate, replace global counter with DB-backed sequence or atomic approach | `core/common/utils.py` |
| 6 | Redundant simple payment mock | Delete directory | `backend/app/services/payment/` |
| 7 | Legacy SQLite URL in config | Remove `database_url` from `config.yaml` and from `required_keys` in loader | `config.yaml`, `core/config/config_loader.py` |

---

## Database Changes

Target: PostgreSQL only. All new tables use `SERIAL` primary keys and `TIMESTAMP WITH TIME ZONE` for dates.

### New Tables

**`owned_characters`** — persistent character inventory

| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PK |
| player_id | INTEGER | FK→players.id, NOT NULL |
| character_name | VARCHAR(50) | NOT NULL |
| is_alive | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| last_match_id | INTEGER | FK→matches.id, NULLABLE |
| revival_count | INTEGER | DEFAULT 0 |

Indexes: `(player_id, is_alive)`, `(last_match_id)`

**`match_join_requests`** — audit trail for join attempts

| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PK |
| match_id | INTEGER | FK→matches.id, NOT NULL |
| player_id | INTEGER | FK→players.id, NOT NULL |
| entry_fee_total | DECIMAL(10,2) | NOT NULL |
| payment_status | VARCHAR(20) | DEFAULT 'pending', CHECK IN ('pending','confirmed','failed') |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| confirmed_at | TIMESTAMPTZ | NULLABLE |

Indexes: `(match_id, player_id)`, `(payment_status)`

**`match_join_request_characters`** — junction table (replaces `INTEGER[]` array)

| Column | Type | Constraints |
|--------|------|-------------|
| join_request_id | INTEGER | FK→match_join_requests.id, NOT NULL |
| owned_character_id | INTEGER | FK→owned_characters.id, NOT NULL |

PK: `(join_request_id, owned_character_id)`

**`pending_payouts`** — calculated payouts for future settlement

| Column | Type | Constraints |
|--------|------|-------------|
| id | SERIAL | PK |
| match_id | INTEGER | FK→matches.id, NOT NULL |
| player_id | INTEGER | FK→players.id, NOT NULL |
| payout_type | VARCHAR(20) | NOT NULL, CHECK IN ('kill_award','winner','refund') |
| amount | DECIMAL(10,2) | NOT NULL, CHECK > 0 |
| currency | VARCHAR(10) | DEFAULT 'USDC' |
| calculated_at | TIMESTAMPTZ | DEFAULT NOW() |
| settled_at | TIMESTAMPTZ | NULLABLE |
| settlement_tx_hash | VARCHAR(100) | NULLABLE |

Indexes: `(match_id)`, `(player_id)`, partial on `(settled_at) WHERE settled_at IS NULL`

### Modified Tables

**`characters` → rename to `match_characters`**

New columns:
- `owned_character_id` INTEGER FK→owned_characters.id
- `entry_order` INTEGER NOT NULL DEFAULT 0
- `elimination_round` INTEGER NULLABLE

After data migration, drop `name` column (name lives on `owned_characters`).

**`matches` — extend with lobby fields**

New columns:
- `creator_wallet_address` VARCHAR(100)
- `min_players` INTEGER DEFAULT 3, CHECK 3–50
- `max_characters` INTEGER DEFAULT 20, CHECK ≥ min_players AND ≤ 100
- `max_characters_per_player` INTEGER DEFAULT 3, CHECK 1–5
- `protocol_fee_percentage` DECIMAL(5,2) DEFAULT 10.0
- `countdown_started_at` TIMESTAMPTZ NULLABLE

**`matches.status` — extended state machine** (replaces adding a separate `lobby_status`)

```
pending → filling → active → completed
            ↓         ↓
         cancelled   failed
```

- `pending`: created, not yet open for joins (legacy compat)
- `filling`: lobby open, accepting joins
- `active`: match running
- `completed`: match finished normally
- `cancelled`: lobby cancelled before start
- `failed`: match execution error

---

## Service Layer

### CharacterInventoryService (NEW)

Location: `backend/app/services/character_inventory.py`

Methods:
- `purchase_characters(player_id, quantity, payment_ref) → List[OwnedCharacter]`
  - Validate quantity 1–10
  - Process payment via blockchain MockPaymentProvider
  - Generate names via fixed `get_next_character_name()`
  - Create `owned_characters` records
- `get_player_inventory(player_id, alive_only=False) → List[OwnedCharacter]`
- `revive_character(character_id, player_id, payment_ref) → OwnedCharacter`
  - Verify ownership, verify dead, verify not in active match
  - Process revival fee payment
  - Set `is_alive=True`, increment `revival_count`

### MatchLobbyService (NEW or extend existing MatchService)

Location: extend `core/match/service.py` or new `backend/app/services/match_lobby.py`

Methods:
- `create_match_lobby(creator_id, params) → Match`
  - Validate params against config min/max
  - Deduct listing fee (0.1 USDC) via MockPaymentProvider
  - Create match with `status='filling'`
- `join_match(match_id, player_id, character_ids, payment_ref) → MatchJoinRequest`
  - Atomic transaction:
    1. Validate match is `filling`
    2. Validate characters: owned by player, alive, not in another pending/active match
    3. Validate limits: per-player and total
    4. Process entry fee payment
    5. Create `match_join_request` + junction rows
    6. Create `match_characters` records
    7. Check start conditions
- `check_start_conditions(match_id) → bool`
  - If unique_players ≥ min_players and countdown not started → start countdown
  - If total characters ≥ max_characters → start immediately

### Payment Integration

Use `backend/app/services/blockchain/payment/mock_provider.py` for all payment flows:
- Character purchases
- Match entry fees
- Listing fees
- Revival fees

All calls go through `BlockchainServiceFactory.get_payment_provider()`.

### Payout Calculation

On match completion:
- Kill awards: `kills × entry_fee × kill_award_rate`, capped at player's total entry fee
- Protocol fee: `total_pool × protocol_fee_percentage / 100`
- Winner payout: `total_pool - total_kill_awards - protocol_fee`
- All stored as `pending_payouts` records (settlement is future phase)

---

## Match Engine Changes

File: `core/match/engine.py`

1. **Round delay**: after each round's logic completes, sleep `random.uniform(5.0, 10.0)` seconds (configurable via config). Only when `round_delay_enabled=True`.

2. **Post-match sync**: after match ends, sync `match_characters.is_alive` back to `owned_characters.is_alive` and set `owned_characters.last_match_id`.

No other engine changes. Character loading and status updates during match already work via existing repos.

---

## API Endpoints

All under existing router structure: `/api/v1/...`

### Character Inventory
- `POST /api/v1/characters/purchase` — buy characters for inventory
- `GET /api/v1/characters/inventory` — list owned characters (query: `alive_only`, pagination)
- `GET /api/v1/characters/{id}/revival-fee` — get revival cost
- `POST /api/v1/characters/{id}/revive` — revive dead character

### Match Lobby
- `POST /api/v1/matches/create` — create lobby with params
- `GET /api/v1/matches/open` — browse filling lobbies (filters: fee range, available slots)
- `POST /api/v1/matches/{id}/join` — join with selected characters
- `GET /api/v1/matches/{id}/events` — poll match events (cursor: `after_event_id`)
- `GET /api/v1/matches/{id}/status` — current match state summary

### Player
- `GET /api/v1/players/profile` — stats + pending payouts
- `GET /api/v1/players/{address}/match-history` — past matches

---

## Background Tasks

Use existing `core/scheduler/scheduler.py` `TaskScheduler`:

- **Countdown expiry**: scheduled when first join brings match to `min_players`. Fires `start_match` at `countdown_started_at + time_limit`.
- **Match execution**: `match_runner.run_match_background(match_id, db)` — already exists, add round delay support.

---

## Config Additions

Add to `config.yaml`:

```yaml
character_base_price: 1.0
character_revival_fee: 0.5
listing_fee: 0.1
round_delay_min: 5.0
round_delay_max: 10.0
```

---

## Out of Scope

- Alembic migration setup (separate task)
- Auth / wallet signature verification (Phase 3)
- Frontend
- Real blockchain integration
- Tournament system
- Moving `core/` repos into `backend/`
