# Phase 2.5 Execution Plan

---

## Step 0: Prerequisites (Tech Debt)

| # | Issue | Fix | Files | Status |
|---|-------|-----|-------|--------|
| 1 | `pydantic-settings` missing from requirements | Add `pydantic-settings>=2.0` | `backend/requirements.txt` | ✅ Done |
| 2 | `MatchInDBBase` timestamps required but null on creation | Make `start_timestamp` and `end_timestamp` `Optional[datetime]` | `backend/app/schemas/match.py` | ✅ Done |
| 3 | `conftest.py` fixtures broken (missing `wallet_address`, uses `owner_username`) | Rewrite fixtures with `wallet_address`, `player_id`; centralize `random_string` | `backend/tests/conftest.py` | ✅ Done |
| 4 | `test_characters.py` API tests use `owner_username` | Rewrite to use `player_id` | `backend/tests/api/test_characters.py` | ✅ Done |
| 5 | `test_character.py` CRUD tests use `owner_username`, call nonexistent methods | Rewrite to use `player_id`, call `get_by_player_id` | `backend/tests/crud/test_character.py` | ✅ Done |
| 6 | `test_players.py` API tests create without `wallet_address` | Add `wallet_address` to all create payloads | `backend/tests/api/test_players.py` | ✅ Done |
| 7 | `test_player.py` CRUD tests create without `wallet_address` | Add `wallet_address` to `PlayerCreate`, add `get_by_wallet_address` test | `backend/tests/crud/test_player.py` | ✅ Done |
| 8 | `CharacterService.purchase_character` takes `username` | Change to `player_id: int` | `core/player/service.py` | ✅ Done |
| 9 | `PlayerService` uses username-based lookups | Change to `wallet_address`/`player_id` based | `core/player/service.py` | ✅ Done |
| 10 | `PlayerRepo` missing `get_player_by_wallet_address`; `create_player` takes username | Add wallet method; change `create_player(wallet_address, username=None)` | `core/player/repository.py` | ✅ Done |
| 11 | `create_player` endpoint checks username uniqueness | Check `wallet_address` uniqueness instead | `backend/app/api/api_v1/endpoints/players.py` | ✅ Done |
| 12 | Duplicate `get_next_character_name()` | Remove second definition | `core/common/utils.py` | ✅ Done |
| 13 | Redundant simple payment mock | Delete `backend/app/services/payment/` | `backend/app/services/payment/` | ✅ Done |
| 14 | Legacy `database_url` in config | Remove from `config.yaml` and `required_keys` in loader | `config.yaml`, `core/config/config_loader.py` | ✅ Done |

**Verification:** `pytest backend/tests/` — blocked on missing pip/dependencies on dev machine.

---

## Step 1: Database Changes (New + Modified Models)

| Task | Details | Files | Status |
|------|---------|-------|--------|
| New model: `OwnedCharacter` | Persistent character inventory (player_id, character_name, is_alive, last_match_id, revival_count) | `backend/app/models/models.py` | ✅ Done |
| New model: `MatchJoinRequest` | Audit trail for join attempts (match_id, player_id, entry_fee_total, payment_status) | `backend/app/models/models.py` | ✅ Done |
| New model: `MatchJoinRequestCharacter` | Junction table (join_request_id, owned_character_id) | `backend/app/models/models.py` | ✅ Done |
| New model: `PendingPayout` | Calculated payouts (match_id, player_id, payout_type, amount, settled_at) | `backend/app/models/models.py` | ✅ Done |
| Modify `Character` | Add `owned_character_id`, `entry_order`, `elimination_round` | `backend/app/models/models.py` | ✅ Done |
| Modify `Match` | Add lobby fields (creator_wallet_address, min/max players, protocol_fee_percentage, countdown_started_at); extend status values | `backend/app/models/models.py` | ✅ Done |
| Config additions | `character_base_price`, `character_revival_fee`, `listing_fee`, `round_delay_min`, `round_delay_max` | `config.yaml` | ✅ Done |

---

## Step 2: Schemas + CRUD

| Task | Files | Status |
|------|-------|--------|
| Schemas for `OwnedCharacter` | `backend/app/schemas/owned_character.py` | ✅ Done |
| Schemas for `MatchJoinRequest` | `backend/app/schemas/match_join_request.py` | ✅ Done |
| Schemas for `PendingPayout` | `backend/app/schemas/pending_payout.py` | ✅ Done |
| Update `Match` schemas for lobby fields | `backend/app/schemas/match.py` | ✅ Done |
| Update `Character` schemas for new columns | `backend/app/schemas/character.py` | ✅ Done |
| CRUD for `OwnedCharacter` | `backend/app/crud/owned_character.py` | ✅ Done |
| CRUD for `MatchJoinRequest` | `backend/app/crud/match_join_request.py` | ✅ Done |
| CRUD for `PendingPayout` | `backend/app/crud/pending_payout.py` | ✅ Done |

---

## Step 3: CharacterInventoryService

| Task | Files | Status |
|------|-------|--------|
| `purchase_characters(player_id, quantity, payment_ref)` | `backend/app/services/character_inventory.py` | ⬜ |
| `get_player_inventory(player_id, alive_only)` | `backend/app/services/character_inventory.py` | ⬜ |
| `revive_character(character_id, player_id, payment_ref)` | `backend/app/services/character_inventory.py` | ⬜ |
| Integration with `BlockchainServiceFactory.get_payment_provider()` | `backend/app/services/character_inventory.py` | ⬜ |

---

## Step 4: MatchLobbyService

| Task | Files | Status |
|------|-------|--------|
| `create_match_lobby(creator_id, params)` | `backend/app/services/match_lobby.py` | ⬜ |
| `join_match(match_id, player_id, character_ids, payment_ref)` — atomic transaction | `backend/app/services/match_lobby.py` | ⬜ |
| `check_start_conditions(match_id)` | `backend/app/services/match_lobby.py` | ⬜ |

---

## Step 5: Payout Calculation

| Task | Files | Status |
|------|-------|--------|
| Kill awards: `kills × entry_fee × kill_award_rate`, capped at player's total entry fee | `backend/app/services/match_lobby.py` or engine | ⬜ |
| Protocol fee: `total_pool × protocol_fee_percentage / 100` | same | ⬜ |
| Winner payout: `total_pool - kill_awards - protocol_fee` | same | ⬜ |
| Store as `pending_payouts` records | same | ⬜ |

---

## Step 6: Match Engine Changes

| Task | Files | Status |
|------|-------|--------|
| Round delay: `random.uniform(min, max)` seconds, behind `round_delay_enabled` flag | `core/match/engine.py` | ⬜ |
| Post-match sync: `match_characters.is_alive` → `owned_characters.is_alive`, set `last_match_id` | `core/match/engine.py` | ⬜ |

---

## Step 7: API Endpoints

| Endpoint | Method | Files | Status |
|----------|--------|-------|--------|
| `/api/v1/characters/purchase` | POST | `backend/app/api/api_v1/endpoints/characters.py` | ⬜ |
| `/api/v1/characters/inventory` | GET | same | ⬜ |
| `/api/v1/characters/{id}/revival-fee` | GET | same | ⬜ |
| `/api/v1/characters/{id}/revive` | POST | same | ⬜ |
| `/api/v1/matches/create` | POST | `backend/app/api/api_v1/endpoints/matches.py` | ⬜ |
| `/api/v1/matches/open` | GET | same | ⬜ |
| `/api/v1/matches/{id}/join` | POST | same | ⬜ |
| `/api/v1/matches/{id}/events` | GET | same | ⬜ |
| `/api/v1/matches/{id}/status` | GET | same | ⬜ |
| `/api/v1/players/profile` | GET | `backend/app/api/api_v1/endpoints/players.py` | ⬜ |
| `/api/v1/players/{address}/match-history` | GET | same | ⬜ |

---

## Step 8: Background Tasks

| Task | Files | Status |
|------|-------|--------|
| Countdown expiry scheduling via `TaskScheduler` | `backend/app/services/match_lobby.py`, `core/scheduler/scheduler.py` | ⬜ |
| Wire round delay into `match_runner` | `backend/app/services/match_runner.py` | ⬜ |

---

## Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | `characters` → `match_characters` rename strategy | (b) Rename `__tablename__` in ORM in-place. Manual DDL rename needed on existing DB. |
| 2 | `created_at` on Match schema | Confirmed: `BaseModel` mixin provides it. No change needed. |
| 3 | `PlayerService` username-based lookups | Addressed in prerequisites (Step 0, items 9–11). |

---

## Out of Scope

- Alembic migration setup
- Auth / wallet signature verification (Phase 3)
- Frontend
- Real blockchain integration
- Tournament system
- Moving `core/` repos into `backend/`
