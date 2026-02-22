# Pre-Phase 2.5 Foundation Cleanup

## Purpose

Prerequisite structural work before Phase 2.5 can begin. No new game features.
Resolves two problems:
- Data layer is split across two isolated stacks (`core/` and `backend/`) with duplicate models
- Player identity is wrong — `username` is the canonical identity, `wallet_address` is an afterthought

---

## Decisions

- `wallet_address`: non-null, unique — canonical player identity (on-chain)
- `username`: nullable, display name only. Auto-assigned as `Player_{wallet_address[:6]}` if not provided at creation
- `Player.id` (integer PK): internal FK used everywhere — never `wallet_address` as FK
- `backend/app/models/models.py`: single source of truth for all ORM models
- `core/database/models.py`: deleted
- `core/` repos: kept in place, imports redirected to backend models and session
- `MatchEngine`: stays in `core/`, unchanged except consequence of identity field change
- `__main__.py`: retired — backend is the entry point
- Auth (wallet signature verification): Phase 3, out of scope here

---

## Step 1 — Fix Player identity in `backend/app/models/models.py`

**Changes to `Player`:**
- `wallet_address`: `String`, non-null, unique
- `username`: `String`, nullable (display name, auto-assigned if null)
- Remove unique constraint from `username`

**Changes to `Character`:**
- Add `player_id`: `Integer`, FK to `players.id`, non-null
- Remove `owner_username`: `String` FK to `players.username`
- Update `display_name` property: `"{name} ({username})"` — requires join or eager load of player

**Impact on other backend models:**
- No other models reference `owner_username` directly

---

## Step 2 — Update backend schemas and CRUD

**`backend/app/schemas/player.py`:**
- `PlayerCreate`: replace `username: str` (required) with `wallet_address: str` (required), `username: Optional[str]`
- `PlayerBase` and response schemas updated to reflect nullable username

**`backend/app/crud/player.py`:**
- `get_by_username`: keep, but username is now nullable/non-unique — behaviour unchanged for lookup
- Add `get_by_wallet_address(wallet_address: str) -> Optional[Player]`
- `create`: auto-assign username if null — `Player_{wallet_address[:6]}`

**`backend/app/schemas/character.py`:**
- Replace `owner_username: str` with `player_id: int`

**`backend/app/crud/character.py`:**
- `get_by_owner_username` → `get_by_player_id(player_id: int)`
- `create_character`: takes `player_id` not `owner_username`

---

## Step 3 — Delete `core/database/models.py`, redirect core repos

**Delete:**
- `core/database/models.py`

**Update imports in:**
- `core/player/repository.py`: import `Player`, `PlayerItem` from `backend.app.models.models`
- `core/player/character_repository.py`: import `Character` from `backend.app.models.models`
- `core/player/item_repository.py`: import `Item`, `PlayerItem` from `backend.app.models.models`
- `core/match/repository.py`: import `Match`, `Character` from `backend.app.models.models`
- `core/match/event_repository.py`: import `MatchEvent` from `backend.app.models.models`
- `core/match/engine.py`: import `Character` from `backend.app.models.models`

**Update session usage in core repos:**
- `core/common/repository.py` (`BaseRepo`): currently takes a `Session` — no change needed, session is injected
- `core/database/db.py`: retired, callers replaced with `backend/app/db/session.py`

**Update `core/database/__init__.py`:** remove model imports

---

## Step 4 — Fix MatchEngine consequence of identity change

`Character` no longer has `owner_username`. Engine uses it in two places:

**`_handle_direct_kill`:**
- Currently: `player_repo.get_player_by_username(killer.owner_username)`
- After: `player_repo.get_player_by_id(killer.player_id)`

**`run_match` (winner block):**
- Currently: `player_repo.get_player_by_username(winner.owner_username)`
- After: `player_repo.get_player_by_id(winner.player_id)`

**`PlayerRepo` additions:**
- Add `get_player_by_id(player_id: int) -> Optional[Player]` to interface and `SqlPlayerRepo`

**`Character.display_name` property:**
- Currently: `f"{self.name} ({self.owner_username})"`
- After: requires access to player's username. Two options:
  - Add `player` relationship to `Character` model (already exists in backend model as `player_owner`) and use `self.player_owner.username`
  - This relationship is already defined in `backend/app/models/models.py` — no new code needed once models are consolidated

---

## Step 5 — Wire MatchEngine into backend

**Create `backend/app/services/match_runner.py`:**
- Single function: `run_match_background(match_id: int, db: Session) -> None`
- Instantiates all `core/` repos with the provided session
- Loads config via `core/config/config_loader.py`
- Loads scenarios via `core/match/scenario_loader.py`
- Instantiates `MatchEngine` with all dependencies
- Loads participants (characters assigned to match) from DB
- Calls `engine.run_match(participants)`
- This function is the target for `BackgroundTasks` and the scheduler

**Update `core/match/service.py` `_run_match`:**
- Replace the broken stub (passes `scenarios={}`, `event_repo=None`) with a call to `match_runner.run_match_background`

---

## Step 6 — Retire `__main__.py`

- Delete `__main__.py`
- `core/` simulation entry point is no longer needed — backend is the entry point

---

## File Change Summary

| File | Action |
|------|--------|
| `backend/app/models/models.py` | Modify — Player identity + Character FK |
| `backend/app/schemas/player.py` | Modify |
| `backend/app/schemas/character.py` | Modify |
| `backend/app/crud/player.py` | Modify |
| `backend/app/crud/character.py` | Modify |
| `core/player/repository.py` | Modify — imports only |
| `core/player/character_repository.py` | Modify — imports + method signatures |
| `core/player/item_repository.py` | Modify — imports only |
| `core/match/repository.py` | Modify — imports only |
| `core/match/event_repository.py` | Modify — imports only |
| `core/match/engine.py` | Modify — owner_username → player_id |
| `core/database/models.py` | Delete |
| `core/database/db.py` | Delete |
| `core/database/__init__.py` | Modify |
| `backend/app/services/match_runner.py` | Create |
| `__main__.py` | Delete |

---

## Out of Scope

- Alembic / database migrations setup
- Auth implementation (wallet signature verification)
- Phase 2.5 features (OwnedCharacter, lobby, payments)
- Moving repos from `core/` to `backend/`
- Any test changes
- API endpoint changes beyond what schema/crud changes require
