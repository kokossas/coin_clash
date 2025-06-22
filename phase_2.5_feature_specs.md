# Coin Clash Phase 2.5: Detailed Feature Specifications

## Table of Contents
1. [Database Schema Specifications](#1-database-schema-specifications)
2. [Character Inventory System](#2-character-inventory-system)
3. [Match Lobby System](#3-match-lobby-system)
4. [Match Execution Updates](#4-match-execution-updates)
5. [API Endpoint Specifications](#5-api-endpoint-specifications)
6. [Background Task Specifications](#6-background-task-specifications)
7. [Integration Points](#7-integration-points)
8. [Mock Payment System](#8-mock-payment-system)
9. [Error Handling Specifications](#9-error-handling-specifications)
10. [State Management](#10-state-management)

---

## 1. Database Schema Specifications

### 1.1 New Table: `owned_characters`

**Purpose**: Store persistent characters owned by players across matches

**Schema Definition**:
```sql
CREATE TABLE owned_characters (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    character_name VARCHAR(50) NOT NULL,
    is_alive BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_match_id INTEGER REFERENCES matches(id),
    revival_count INTEGER DEFAULT 0,
    
    -- Indexes
    INDEX idx_player_alive (player_id, is_alive),
    INDEX idx_last_match (last_match_id)
);
```

**Field Specifications**:
- `player_id`: Foreign key to players table, CASCADE DELETE
- `character_name`: Generated using existing `get_next_character_name()` from `core/common/utils.py`
- `is_alive`: Determines eligibility for match entry. Updated only after match completion
- `last_match_id`: Tracks most recent match participation for history
- `revival_count`: Increments each time character is revived, for analytics

### 1.2 Modified Table: `characters` → `match_characters`

**Purpose**: Rename and modify to represent character instances within a specific match

**Migration Steps**:
1. Rename table `characters` to `match_characters`
2. Add new columns
3. Modify foreign key relationships
4. Migrate existing data

**Schema Definition**:
```sql
ALTER TABLE characters RENAME TO match_characters;

ALTER TABLE match_characters 
    ADD COLUMN owned_character_id INTEGER REFERENCES owned_characters(id),
    ADD COLUMN entry_order INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN elimination_round INTEGER,
    ALTER COLUMN is_alive TYPE BOOLEAN USING (is_alive::boolean);

-- Data migration: Create owned_characters from existing characters
INSERT INTO owned_characters (player_id, character_name, is_alive, last_match_id)
SELECT DISTINCT p.id, c.name, c.is_alive, c.match_id
FROM match_characters c
JOIN players p ON c.owner_username = p.username;

-- Update match_characters with owned_character_id
UPDATE match_characters mc
SET owned_character_id = oc.id
FROM owned_characters oc
JOIN players p ON oc.player_id = p.id
WHERE mc.owner_username = p.username 
AND mc.name = oc.character_name;

-- Drop old columns after verification
ALTER TABLE match_characters 
    DROP COLUMN name,
    DROP COLUMN owner_username;
```

**Field Specifications**:
- `owned_character_id`: Links to persistent character
- `entry_order`: Order in which character joined (1, 2, 3...) for display
- `elimination_round`: NULL if alive, round number when eliminated
- `is_alive`: Real-time status during match execution

### 1.3 New Table: `match_join_requests`

**Purpose**: Track all join attempts and payments for audit trail

**Schema Definition**:
```sql
CREATE TABLE match_join_requests (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    character_ids INTEGER[] NOT NULL,
    entry_fee_total DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT chk_payment_status CHECK (payment_status IN ('pending', 'confirmed', 'failed')),
    CONSTRAINT chk_character_ids_not_empty CHECK (array_length(character_ids, 1) > 0),
    
    -- Indexes
    INDEX idx_match_player (match_id, player_id),
    INDEX idx_payment_status (payment_status)
);
```

### 1.4 Modified Table: `matches`

**Purpose**: Add lobby configuration fields

**Schema Definition**:
```sql
ALTER TABLE matches
    ADD COLUMN creator_wallet_address VARCHAR(100),
    ADD COLUMN min_players INTEGER DEFAULT 3,
    ADD COLUMN max_characters INTEGER DEFAULT 20,
    ADD COLUMN max_characters_per_player INTEGER DEFAULT 3,
    ADD COLUMN kill_award_percentage DECIMAL(5,2) DEFAULT 10.0,
    ADD COLUMN lobby_status VARCHAR(20) DEFAULT 'filling',
    ADD COLUMN countdown_started_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN protocol_fee_percentage DECIMAL(5,2) DEFAULT 10.0,
    
    -- Constraints
    ADD CONSTRAINT chk_lobby_status CHECK (lobby_status IN ('filling', 'ready', 'started', 'completed', 'cancelled')),
    ADD CONSTRAINT chk_min_players CHECK (min_players >= 3 AND min_players <= 50),
    ADD CONSTRAINT chk_max_characters CHECK (max_characters >= min_players AND max_characters <= 100),
    ADD CONSTRAINT chk_max_per_player CHECK (max_characters_per_player >= 1 AND max_characters_per_player <= 5),
    ADD CONSTRAINT chk_kill_award CHECK (kill_award_percentage >= 0 AND kill_award_percentage <= 50);

-- Remove kill_award_rate as it's replaced by percentage
ALTER TABLE matches DROP COLUMN kill_award_rate;
```

### 1.5 New Table: `pending_payouts`

**Purpose**: Track calculated payouts for future settlement

**Schema Definition**:
```sql
CREATE TABLE pending_payouts (
    id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    player_id INTEGER NOT NULL REFERENCES players(id),
    payout_type VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USDC',
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    settled_at TIMESTAMP WITH TIME ZONE,
    settlement_tx_hash VARCHAR(100),
    
    -- Constraints
    CONSTRAINT chk_payout_type CHECK (payout_type IN ('kill_award', 'winner', 'refund')),
    CONSTRAINT chk_amount_positive CHECK (amount > 0),
    
    -- Indexes
    INDEX idx_match_payouts (match_id),
    INDEX idx_player_payouts (player_id),
    INDEX idx_unsettled (settled_at) WHERE settled_at IS NULL
);
```

---

## 2. Character Inventory System

### 2.1 Character Purchase Feature

**Purpose**: Allow players to pre-purchase characters for their inventory

**Implementation Steps**:

1. **Create CharacterInventoryService** in `backend/app/services/character_inventory.py`:
   - Extends existing `CharacterService` from `core/player/service.py`
   - Integrates with `MockPaymentProvider` for Phase 2.5

2. **Service Methods**:

   **2.1.1 `purchase_characters(player_id: int, quantity: int, payment_ref: str) -> List[OwnedCharacter]`**
   
   Business Logic:
   - Validate quantity: 1 ≤ quantity ≤ 10 per request
   - Calculate total cost: quantity × character_base_price (from config)
   - Call MockPaymentProvider.process_deposit(player_id, total_cost)
   - For each character:
     - Generate name using existing `get_next_character_name()`
     - Create `OwnedCharacter` record
     - Set `is_alive = True`
   - Return list of created characters
   
   Error Scenarios:
   - Invalid quantity: Return 400 "Quantity must be between 1 and 10"
   - Payment failure: Return 402 "Payment failed: {reason}"
   - Database error: Rollback transaction, return 500

   **2.1.2 `get_player_inventory(player_id: int, alive_only: bool = False) -> List[OwnedCharacter]`**
   
   Business Logic:
   - Query owned_characters table filtered by player_id
   - If alive_only=True, add WHERE is_alive = TRUE
   - Order by created_at DESC
   - Include last_match details via JOIN if last_match_id is not NULL
   
   Response includes:
   - Character ID, name, is_alive status
   - Last match ID and result if applicable
   - Revival count
   - Created timestamp

### 2.2 Character Revival Feature (Mock Implementation)

**Purpose**: Allow players to revive dead characters (payment mocked in Phase 2.5)

**Implementation Steps**:

1. **Service Methods**:

   **2.2.1 `get_revival_fee() -> Decimal`**
   
   Business Logic:
   - Read from config: `character_revival_fee`
   - Return fixed fee amount (e.g., 0.5 USDC)
   
   **2.2.2 `check_revival_eligibility(character_id: int, player_id: int) -> Dict`**
   
   Business Logic:
   - Verify character exists and belongs to player
   - Check character.is_alive = False
   - Ensure character not currently in any pending/active match
   
   Response:
   ```python
   {
       "eligible": bool,
       "reason": str,  # if not eligible
       "revival_fee": Decimal,
       "character": {...}  # character details
   }
   ```

   **2.2.3 `revive_character(character_id: int, player_id: int, payment_ref: str) -> OwnedCharacter`**
   
   Business Logic:
   - Call check_revival_eligibility first
   - Call MockPaymentProvider.process_deposit(player_id, revival_fee)
   - Update character:
     - Set is_alive = True
     - Increment revival_count
   - Return updated character
   
   Error Scenarios:
   - Character not found: 404
   - Not owner: 403 "Not your character"
   - Already alive: 400 "Character is already alive"
   - In active match: 400 "Character is in an active match"

**Future Integration Point**: Replace MockPaymentProvider with real blockchain payment verification

### 2.3 Database Repository Extensions

Extend existing `SqlCharacterRepo` from `core/player/character_repository.py`:

1. Add new methods:
   - `create_owned_character(player_id, name) -> OwnedCharacter`
   - `get_owned_characters(player_id, alive_only) -> List[OwnedCharacter]`
   - `update_character_alive_status(character_id, is_alive) -> OwnedCharacter`
   - `get_characters_in_matches(character_ids) -> Dict[int, str]` # Returns {char_id: match_status}

---

## 3. Match Lobby System

### 3.1 Match Creation Feature

**Purpose**: Allow players to create custom match lobbies

**Implementation Steps**:

1. **Extend MatchService** in `core/match/service.py`:

   **3.1.1 `create_match_lobby(creator_id: int, params: MatchCreateParams) -> Match`**
   
   Input Validation:
   - entry_fee: Between config min_fee (0.5) and max_fee (5.0)
   - max_characters: Between min_players and 50
   - min_players: Between 3 and max_characters
   - max_characters_per_player: Between 1 and 3
   - kill_award_percentage: Between 0 and 50
   - time_limit_before_start: Between 10 and 300 seconds
   
   Business Logic:
   - Deduct listing fee (0.1 USDC) via MockPaymentProvider
   - Create match record with:
     - lobby_status = 'filling'
     - start_method = 'timeout'
     - start_threshold = time_limit_before_start
     - All custom parameters
   - Do NOT set countdown_started_at yet (waits for min_players)
   - Return created match with ID

   **3.1.2 `get_open_matches(filters: MatchFilters) -> List[Match]`**
   
   Query Logic:
   - WHERE lobby_status = 'filling'
   - Apply optional filters:
     - entry_fee range
     - available slots (calculate from current participants)
     - creator address
   - Order by created_at DESC
   - Include current participant count via subquery

### 3.2 Match Joining Feature

**Purpose**: Allow players to join matches with their characters

**Implementation Steps**:

1. **Service Methods**:

   **3.2.1 `validate_join_request(match_id: int, player_id: int, character_ids: List[int]) -> JoinValidation`**
   
   Validation Steps:
   - Match exists and lobby_status = 'filling'
   - Characters belong to player (JOIN with owned_characters)
   - All characters have is_alive = True
   - Characters not already in this match
   - Characters not in any other pending/active match
   - Player's total characters in match (existing + new) ≤ max_characters_per_player
   - Total match characters (existing + new) ≤ max_characters
   
   Calculate:
   - Total entry fee = len(character_ids) × match.entry_fee
   - Current player character count in match
   - Available slots in match

   **3.2.2 `join_match(match_id: int, player_id: int, character_ids: List[int], payment_ref: str) -> MatchJoinRequest`**
   
   Transaction Steps (MUST be atomic):
   ```
   BEGIN TRANSACTION
   1. Call validate_join_request
   2. Process payment via MockPaymentProvider
   3. Create match_join_request record
   4. For each character_id:
      - Create match_character record
      - Set entry_order = current_match_characters_count + index + 1
      - Link to owned_character_id
   5. Check if this triggers match start conditions
   COMMIT or ROLLBACK
   ```
   
   Post-Join Checks:
   - If first to reach min_players AND countdown not started:
     - Set countdown_started_at = NOW()
     - Schedule background task for auto-start
   - If reached max_characters:
     - Call start_match immediately

   **3.2.3 `get_player_characters_in_match(match_id: int, player_id: int) -> List[MatchCharacter]`**
   
   Query Logic:
   - Get all match_characters for this match and player
   - Include owned_character details
   - Order by entry_order

### 3.3 Match Start Conditions

**Implementation in MatchService**:

1. **`check_and_trigger_match_start(match_id: int) -> bool`**
   
   Logic Flow:
   ```
   IF match.lobby_status != 'filling':
       RETURN False
   
   participant_count = COUNT(match_characters WHERE match_id = match_id)
   unique_players = COUNT(DISTINCT player_id from match_characters)
   
   IF participant_count >= match.max_characters:
       start_match_immediately()
       RETURN True
   
   IF unique_players >= match.min_players AND countdown_started_at IS NULL:
       set_countdown_timer()
       RETURN False
   
   RETURN False
   ```

2. **`handle_countdown_expiry(match_id: int)`**
   
   Called by background scheduler when countdown expires:
   - Verify match still in 'filling' status
   - Check if still has min_players
   - Transition to match start

---

## 4. Match Execution Updates

### 4.1 Integration with Existing MatchEngine

**Purpose**: Modify MatchEngine to work with new character system

**Changes to `core/match/engine.py`**:

1. **Constructor Modifications**:
   ```python
   # Current constructor accepts List[Character]
   # Modify to accept match_id and load MatchCharacters
   
   def __init__(self, match_id: int, ...):
       # Existing init code
       self.match_characters = self._load_match_characters()
       self.participants = self._convert_to_engine_format()
   ```

2. **Character Loading**:
   ```python
   def _load_match_characters(self) -> List[MatchCharacter]:
       # Query all match_characters for this match
       # Include owned_character details
       # Order by entry_order
   ```

3. **Status Update Integration**:
   
   Modify `_apply_elimination` method:
   ```python
   def _apply_elimination(self, character: Character):
       # Existing logic to update in-memory pools
       if character.id in self.alive_pool:
           # ... existing code ...
           
           # NEW: Update database immediately
           self.character_repo.update_match_character_status(
               match_character_id=character.match_character_id,
               is_alive=False,
               elimination_round=self.round_number
           )
   ```
   
   Modify `_apply_revival` method similarly.

4. **Round Delay Implementation**:
   
   In `_run_round` method, add at end:
   ```python
   # After all round logic
   if self.round_delay_enabled:
       delay = self.random.uniform(5.0, 10.0)  # 5-10 seconds
       logger.info("round_delay", extra={"seconds": delay})
       time.sleep(delay)
   ```

### 4.2 Post-Match Synchronization

**New method in MatchEngine**:

```python
def _finalize_match_results(self, winner: Character):
    # Existing winner logic...
    
    # NEW: Sync character states back to inventory
    for mc in self.match_characters:
        self.character_repo.update_owned_character_from_match(
            owned_character_id=mc.owned_character_id,
            is_alive=mc.is_alive,
            last_match_id=self.match_id
        )
```

### 4.3 Event Streaming for Polling

**Extend EventRepo** in `core/match/event_repository.py`:

1. **New Methods**:
   
   **`get_events_since(match_id: int, after_event_id: int = None, after_round: int = None) -> List[MatchEvent]`**
   
   Query Logic:
   - If after_event_id: WHERE id > after_event_id
   - Else if after_round: WHERE round_number > after_round
   - Order by id ASC
   - Limit 50 events per request

   **`get_match_state_summary(match_id: int) -> Dict`**
   
   Returns:
   ```python
   {
       "current_round": int,
       "alive_count": int,
       "dead_count": int,
       "latest_event_id": int,
       "match_status": str,
       "elapsed_time": int  # seconds since start
   }
   ```

---

## 5. API Endpoint Specifications

### 5.1 Character Endpoints

**Base path**: `/api/v1/characters`

#### 5.1.1 POST `/purchase`
**Purpose**: Purchase characters for inventory

Request:
```json
{
    "quantity": 3
}
```

Response (200):
```json
{
    "characters": [
        {
            "id": 123,
            "name": "Ace",
            "is_alive": true,
            "created_at": "2024-01-15T10:00:00Z"
        },
        ...
    ],
    "total_cost": 3.0,
    "payment_status": "confirmed"
}
```

Errors:
- 400: Invalid quantity
- 402: Payment failed
- 500: Server error

#### 5.1.2 GET `/inventory`
**Purpose**: Get player's character inventory

Query params:
- `alive_only`: boolean (default false)
- `page`: int (default 1)
- `limit`: int (default 20, max 100)

Response (200):
```json
{
    "characters": [...],
    "pagination": {
        "page": 1,
        "limit": 20,
        "total": 45
    }
}
```

#### 5.1.3 GET `/{character_id}/revival-fee`
**Purpose**: Get revival fee for a character

Response (200):
```json
{
    "character_id": 123,
    "revival_fee": 0.5,
    "currency": "USDC",
    "character": {
        "name": "Ace",
        "is_alive": false,
        "died_in_match": 456
    }
}
```

### 5.2 Match Endpoints

**Base path**: `/api/v1/matches`

#### 5.2.1 POST `/create`
**Purpose**: Create a new match lobby

Request:
```json
{
    "entry_fee": 1.0,
    "max_characters": 20,
    "min_players": 3,
    "max_characters_per_player": 2,
    "kill_award_percentage": 15.0,
    "time_limit_before_start": 120
}
```

Validation:
- All fields except min_players are required
- Apply min/max constraints from config
- Validate listing fee payment

Response (201):
```json
{
    "match_id": 789,
    "lobby_status": "filling",
    "parameters": {...},
    "created_at": "2024-01-15T10:00:00Z",
    "join_code": "MATCH789"  // For easy sharing
}
```

#### 5.2.2 GET `/open`
**Purpose**: Browse open match lobbies

Query params:
- `min_fee`: decimal
- `max_fee`: decimal
- `has_slots`: boolean
- `page`: int
- `limit`: int

Response (200):
```json
{
    "matches": [
        {
            "match_id": 789,
            "entry_fee": 1.0,
            "current_players": 5,
            "current_characters": 8,
            "max_characters": 20,
            "slots_remaining": 12,
            "countdown_status": "not_started",
            "parameters": {...}
        }
    ],
    "pagination": {...}
}
```

#### 5.2.3 POST `/{match_id}/join`
**Purpose**: Join a match with selected characters

Request:
```json
{
    "character_ids": [123, 124]
}
```

Validation Steps:
1. Validate all characters belong to player
2. Check all characters are alive
3. Verify not exceeding limits
4. Process payment for entry fees

Response (200):
```json
{
    "join_request_id": 999,
    "match_id": 789,
    "characters_entered": 2,
    "total_fee_paid": 2.0,
    "your_total_characters": 2,
    "match_status": {
        "lobby_status": "filling",
        "countdown_started": false,
        "participants": 10,
        "slots_remaining": 10
    }
}
```

Errors:
- 400: Validation failure (detailed reason)
- 402: Payment failed
- 404: Match not found
- 409: Match already started

#### 5.2.4 GET `/{match_id}/events`
**Purpose**: Poll for match events

Query params:
- `after_event_id`: int (for cursor-based polling)
- `after_round`: int (alternative cursor)

Response (200):
```json
{
    "events": [
        {
            "event_id": 1234,
            "round_number": 5,
            "event_type": "direct_kill",
            "scenario_text": "Ace whip-cracks a serving tray, sending Ghost over the rail.",
            "timestamp": "2024-01-15T10:05:23Z"
        }
    ],
    "match_state": {
        "current_round": 5,
        "alive_count": 12,
        "your_characters_alive": 1,
        "match_status": "active"
    },
    "next_cursor": {
        "after_event_id": 1234
    }
}
```

### 5.3 Player Endpoints

**Base path**: `/api/v1/players`

#### 5.3.1 GET `/profile`
**Purpose**: Get current player profile

Response (200):
```json
{
    "player_id": 1,
    "wallet_address": "0x123...",
    "stats": {
        "total_characters": 45,
        "alive_characters": 38,
        "total_matches": 23,
        "wins": 5,
        "total_kills": 127
    },
    "pending_payouts": {
        "kill_awards": 12.5,
        "winner_payouts": 45.0,
        "total": 57.5
    }
}
```

---

## 6. Background Task Specifications

### 6.1 Match Execution Task

**Using existing** `core/scheduler/scheduler.py`:

1. **Task Registration**:
   
   When match should start (immediate or countdown):
   ```python
   task_id = f"match_execute_{match_id}"
   execute_at = datetime.now() if immediate else countdown_end_time
   
   scheduler.schedule_task(
       task_id=task_id,
       execute_at=execute_at,
       callback=execute_match_task,
       match_id=match_id
   )
   ```

2. **Task Implementation**:
   ```python
   def execute_match_task(match_id: int):
       with get_session() as db:
           # Create service instances
           match_service = MatchService(...)
           
           # Verify match still pending
           match = match_service.get_match(match_id)
           if match.lobby_status != 'filling':
               return
           
           # Transition to active
           match_service.update_match_status(match_id, 'active')
           
           # Run engine
           engine = MatchEngine(
               match_id=match_id,
               config=load_config(),
               scenarios=load_scenarios(),
               # ... other dependencies
           )
           
           participants = load_match_characters(match_id)
           winner, log = engine.run_match(participants)
           
           # Calculate payouts
           calculate_and_store_payouts(match_id, winner)
   ```

### 6.2 Countdown Monitor Task

**Purpose**: Auto-start matches when countdown expires

Implementation:
- Scheduled when first player brings match to min_players
- Executes at countdown_started_at + time_limit_before_start
- Calls same execute_match_task

---

## 7. Integration Points

### 7.1 Existing Code Integration

1. **MatchEngine Integration**:
   - File: `core/match/engine.py`
   - Changes: Accept match_id instead of character list
   - Load MatchCharacter records instead of Character
   - Update status in database during execution
   - Add round delays

2. **Repository Extensions**:
   - File: `core/player/character_repository.py`
   - Add methods for owned_characters table
   - Add methods for match_characters status updates

3. **Utils Integration**:
   - File: `core/common/utils.py`
   - Use existing `get_next_character_name()` for character creation
   - No changes needed

4. **Config Integration**:
   - File: `config.yaml`
   - Add new parameters:
     ```yaml
     # Character settings
     character_base_price: 1.0
     character_revival_fee: 0.5
     
     # Match lobby settings  
     listing_fee: 0.1
     round_delay_min: 5.0
     round_delay_max: 10.0
     ```

### 7.2 Service Layer Connections

1. **CharacterService** enhancement:
   - Current file: `core/player/service.py`
   - Extend with inventory methods
   - Keep existing match character logic

2. **MatchService** enhancement:
   - Current file: `core/match/service.py`
   - Add lobby creation logic
   - Modify start conditions
   - Integrate with scheduler

---

## 8. Mock Payment System

### 8.1 MockPaymentProvider Implementation

**File**: `backend/app/services/blockchain/payment/mock_provider.py` (already exists)

**Integration Points**:

1. **Character Purchase**:
   ```python
   # In CharacterInventoryService
   payment_result = await payment_provider.process_deposit(
       wallet_address=f"mock_wallet_{player_id}",
       amount=total_cost,
       currency="USDC"
   )
   ```

2. **Match Entry**:
   ```python
   # In MatchService.join_match
   payment_result = await payment_provider.process_deposit(
       wallet_address=f"mock_wallet_{player_id}",
       amount=entry_fee_total,
       currency="USDC"
   )
   ```

3. **Future Replacement**:
   - Mark all payment calls with comment: `# TODO: Replace with real payment in Phase 3`
   - Use dependency injection for easy swapping
   - Store payment_ref for future reconciliation

### 8.2 Payout Calculation (Store Only)

**In MatchService**:

```python
def calculate_and_store_payouts(match_id: int, winner_character_id: int):
    # Get all match participations
    participants = get_match_characters(match_id)
    
    # Calculate kill awards
    for participant in participants:
        if participant.kills > 0:
            kill_award = min(
                participant.kills * (entry_fee * kill_award_percentage / 100),
                participant.entry_fee  # Cap at original buy-in
            )
            create_pending_payout(
                match_id=match_id,
                player_id=participant.player_id,
                payout_type='kill_award',
                amount=kill_award
            )
    
    # Calculate winner payout
    total_pool = len(participants) * entry_fee
    total_kill_awards = sum(all_kill_awards)
    protocol_fee = total_pool * protocol_fee_percentage / 100
    winner_payout = total_pool - total_kill_awards - protocol_fee
    
    create_pending_payout(
        match_id=match_id,
        player_id=winner.player_id,
        payout_type='winner',
        amount=winner_payout
    )
```

---

## 9. Error Handling Specifications

### 9.1 Validation Errors (400 Bad Request)

Standard format:
```json
{
    "error": "validation_error",
    "message": "Human readable message",
    "details": {
        "field": "specific_field",
        "constraint": "violated_constraint",
        "value": "invalid_value"
    }
}
```

Examples:
- "Quantity must be between 1 and 10"
- "Entry fee must be between 0.5 and 5.0 USDC"
- "Character is not alive"
- "Character already in another active match"

### 9.2 Business Logic Errors (409 Conflict)

Standard format:
```json
{
    "error": "conflict",
    "message": "Human readable message",
    "details": {
        "current_state": "...",
        "attempted_action": "..."
    }
}
```

Examples:
- "Match has already started"
- "Match lobby is full"
- "Player has reached character limit for this match"

### 9.3 Payment Errors (402 Payment Required)

Standard format:
```json
{
    "error": "payment_failed",
    "message": "Payment could not be processed",
    "details": {
        "required_amount": 2.0,
        "currency": "USDC",
        "reason": "insufficient_balance"  // In mock mode
    }
}
```

### 9.4 Database Transaction Errors

Handling:
1. Always use database transactions for multi-step operations
2. On any error, rollback entire transaction
3. Log full error details
4. Return generic 500 to client: "Operation failed, please try again"

---

## 10. State Management

### 10.1 Match State Machine

States and transitions:

```
FILLING → READY → ACTIVE → COMPLETED
   ↓        ↓        ↓
CANCELLED CANCELLED  FAILED
```

Transition rules:
- FILLING → READY: When countdown starts
- READY → ACTIVE: When match execution begins
- ACTIVE → COMPLETED: When match ends normally
- Any → CANCELLED: Admin action or system error
- ACTIVE → FAILED: Match execution error

### 10.2 Character State Tracking

Two-level state:
1. **OwnedCharacter.is_alive**: Persistent across matches
2. **MatchCharacter.is_alive**: During match only

Synchronization:
- Before match: Copy OwnedCharacter.is_alive → MatchCharacter.is_alive
- During match: Update only MatchCharacter.is_alive
- After match: Copy final MatchCharacter.is_alive → OwnedCharacter.is_alive

### 10.3 Join Request States

States:
- pending: Payment not confirmed
- confirmed: Payment confirmed, characters assigned
- failed: Payment failed or validation error

Cleanup:
- Delete 'pending' requests older than 10 minutes
- Keep 'confirmed' and 'failed' for audit trail

### 10.4 Concurrency Control

Critical sections requiring locks:

1. **Match joining**:
   ```sql
   SELECT * FROM matches WHERE id = ? FOR UPDATE;
   -- Validate slots available
   -- Insert match_characters
   -- Update counts
   ```

2. **Character selection**:
   ```sql
   SELECT * FROM owned_characters WHERE id IN (?) FOR UPDATE;
   -- Verify not in other matches
   -- Create match participation
   ```

3. **Countdown start**:
   ```sql
   UPDATE matches 
   SET countdown_started_at = NOW() 
   WHERE id = ? AND countdown_started_at IS NULL;
   ```