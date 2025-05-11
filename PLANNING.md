# Coin Clash Engine Startup Logic - Planning Document

## 1. Scope & Objective

Implement refined match start conditions in the backend engine so that:

* When **player cap** is reached, the match starts **only after all registered players have completed their character purchases**.
* Otherwise, the match starts when the **start timer** expires, and any players who have not purchased characters receive **one default character** (and are charged the standard entry fee for that character).

This is purely backend logic—frontends simply call existing endpoints and poll for status.

## 2. Requirements

1. **Track purchase status** per player per match (no DB schema change if character count serves this).
2. **Create or update** match with a `start_timer_end` timestamp (calculated as `created_at + timer_duration`).
3. **Conditionally transition** match from `pending` to `active` when either:

   * `joined_count >= player_cap` **AND** `purchased_count == joined_count`
   * **OR** current time >= `start_timer_end` (trigger auto-start flow).
4. **Auto-assign and charge defaults**: for each joined-but-not-purchased player when timer expires:

   1. Deduct one entry fee from their balance
   2. Create and assign a character to the match
5. **Invoke** the existing `MatchEngine.run_match(...)` and update match status to `active` before polling begins.

## 3. Architecture & Component Changes

### 3.1 Data Model

* **Match**

  * Add field `start_timer_end: DateTime` (store deadline for auto-start).

### 3.2 Service Layer

#### MatchService

* `create_match(...)`

  * Calculate & persist `start_timer_end` based on `timer_duration`
  * Persist with `status = pending`
  * Schedule background job for `start_timer_end`

* `check_and_start_match(match_id)`

  * Fetch match, `joined_count`, `purchased_count`
  * IF `joined_count >= player_cap` **AND** `purchased_count == joined_count`:

    * Call `start_match(match_id)`

* `start_match(match_id)`

  * IF `match.status != pending`, exit (idempotent guard)
  * For each joined player with zero purchases:

    1. Deduct one entry fee from their balance
    2. Create and assign a character
  * Update `match.status = active` and set `start_timestamp`
  * Invoke `MatchEngine.run_match(...)` asynchronously or via background worker

#### CharacterService

* After successful purchase, call `MatchService.check_and_start_match(match_id)`

### 3.3 Scheduler / Background Tasks

* On match creation, schedule a one-time job at `start_timer_end` to call `MatchService.start_match(match_id)` if still pending
* Use a scheduler (e.g., APScheduler or FastAPI BackgroundTasks) with idempotent execution

## 4. Data Flow

```plaintext
[ Player invokes POST /matches ]
    └─ MatchService.create_match ➔ Match(pending) + timer job scheduled

[ Players join via POST /players/join-match ]
    └─ CharacterService.purchase_chars ➔ MatchService.check_and_start
         ├─ IF cap & all purchased ➔ MatchService.start_match ➔ Engine.run_match
         └─ ELSE ➔ return success, await others or timer

[ At timer expiry (scheduler trigger) ]
    └─ MatchService.start_match (deduct fees + assign defaults + start)
```

## 5. Error Handling & Edge Cases

* **Insufficient Balance**: API returns 4xx; purchase not counted.
* **Late Purchases**: After `match.status` transitions to `active`, reject further purchases with 409 Conflict.
* **Scheduler Overlaps**: Ensure `start_match` is idempotent (no-op if not `pending`).

## 6. Testing & Validation

* **Unit Tests** for both start conditions in `MatchService`:

  * `create_match` sets `start_timer_end`
  * `check_and_start_match` triggers correctly on cap + purchases
  * `start_match` deducts fees, assigns defaults, and sets status
* **Integration Tests** simulating:

  1. Cap reached & all purchases early ➔ immediate start
  2. Timer expires with partial purchases ➔ default assignments + start
  3. No further purchases allowed after start
* **Load Tests** for scheduler and rapid join/purchase scenarios

## 7. Deployment Considerations

* Database migration to add `start_timer_end`
* Feature flag to toggle new startup logic during rollout
* Monitor scheduler execution, match statuses, and billing logs
