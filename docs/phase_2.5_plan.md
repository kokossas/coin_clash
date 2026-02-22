# Coin Clash: Phase 2.5 - Core Integration & Character Inventory Implementation

## 1. Executive Summary

Phase 2.5 bridges the gap between the existing core game engine and the Web3 gambling platform vision. The primary focus is on implementing the character inventory system, connecting the game engine to API endpoints, and introducing round delays for player engagement. Real payment integration is deferred to a future phase, with mock providers used for testing the complete flow.

## 2. Core Requirements

### 2.1 Character Inventory System (New)
- Players pre-purchase characters that persist in their account
- Characters have persistent `is_alive` status across matches
- Dead characters cannot enter new matches until revived
- Revival requires payment (mocked in this phase)

### 2.2 Match Creation & Joining
- Players create match lobbies with configurable parameters
- Players select pre-owned alive characters to enter matches
- Entry fee charged per character entered (mock payments)
- Match starts via countdown timer or capacity reached

### 2.3 Mock Payment Integration
- Use MockPaymentProvider for all payment flows
- Simulate character purchases and match entry fees
- Track pending payouts for future settlement
- Test complete flow without real blockchain

### 2.4 Game Experience
- 5-10 second rounds for suspense
- Event feed polling for match updates
- Independent match execution timing

## 3. Technical Architecture

### 3.1 System Components

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Web Interface     │────▶│    API Gateway      │────▶│   Game Service      │
│  (Player Actions)   │     │    (FastAPI)        │     │  (Business Logic)   │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                      │                            │
                                      ▼                            ▼
                            ┌─────────────────────┐     ┌─────────────────────┐
                            │     Database        │     │   Match Engine      │
                            │   (PostgreSQL)      │     │  (Core Game Logic)  │
                            └─────────────────────┘     └─────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────────┐
                            │ Mock Payment Service │
                            │  (Testing Only)      │
                            └─────────────────────┘
```

### 3.2 Data Model Extensions

#### Character Ownership Model
```
Player
  ├── id
  ├── wallet_address
  ├── wallet_chain_id
  └── owned_characters (new relationship)

OwnedCharacter (NEW TABLE)
  ├── id
  ├── player_id (FK)
  ├── character_name
  ├── is_alive
  ├── created_at
  ├── last_match_id (FK, nullable)
  └── revival_count

MatchCharacter (MODIFIED)
  ├── id
  ├── match_id (FK)
  ├── owned_character_id (FK) (replaces direct character creation)
  ├── is_alive (updates during match as events occur)
  ├── entry_order
  └── elimination_round (nullable - which round they died)
```

#### Match Lobby Model
```
Match (EXTENDED)
  ├── creator_wallet_address (NEW)
  ├── min_players (NEW - defaults to 3)
  ├── max_characters_per_player (NEW)
  ├── kill_award_percentage (NEW - replaces fixed rate)
  ├── lobby_status (NEW - filling/ready/started/completed)
  └── countdown_started_at (NEW)

MatchJoinRequest (NEW TABLE)
  ├── id
  ├── match_id (FK)
  ├── player_id (FK)
  ├── character_ids (Array of owned_character_id)
  ├── entry_fee_total
  ├── payment_status (pending/confirmed/failed) (mock in this phase)
  └── created_at
```

### 3.3 Service Layer Architecture

#### Character Inventory Service (NEW)
```
CharacterInventoryService:
  - purchase_characters(player_id, quantity, payment_tx) → List[OwnedCharacter]
  - get_player_characters(player_id, alive_only=False) → List[OwnedCharacter]
  - revive_character(character_id, payment_tx) → OwnedCharacter
  - validate_characters_for_match(character_ids) → bool
```

#### Match Lobby Service (ENHANCED)
```
MatchLobbyService:
  - create_match_lobby(creator_id, match_params) → Match
  - join_match(match_id, player_id, character_ids, payment_tx) → MatchJoinRequest
  - check_match_start_conditions(match_id) → bool
  - finalize_match_results(match_id) → MatchResult
```

#### Payment Integration Service (Mock Only)
```
MockPaymentService:
  - simulate_deposit(player_id, amount) → PaymentResult
  - calculate_payouts(match_id) → PayoutDistribution
  - record_pending_payout(player_id, amount, type) → PendingPayout
```

## 4. End-to-End Flows

### 4.1 Character Purchase Flow (Mock Payment)
```
1. Player provides mock wallet address
2. Player requests character purchase (quantity)
3. API uses MockPaymentProvider to simulate payment
4. API creates OwnedCharacter records
5. Player sees characters in inventory
```

### 4.2 Match Creation & Joining Flow (Mock Payment)
```
1. Player creates match lobby:
   - POST /matches/create
   - Parameters: entry_fee, max_characters, kill_award_%, etc.
   - Mock listing fee deduction (0.1 USDC)
   - Match created in "filling" status

2. Players browse open matches:
   - GET /matches/open
   - Filter by parameters, available slots

3. Player joins match:
   - Select alive characters from inventory
   - Calculate total entry fee (fee × num_characters)
   - API uses MockPaymentProvider for payment simulation
   - POST /matches/{id}/join with mock payment
   - API reserves slots immediately

4. Match start conditions check:
   - On each confirmed join:
     * If first to reach min_players (3) → start countdown
     * If max_characters reached → start immediately
   - Background job monitors countdown expiry

5. Match transitions to "ready" then "started"
```

### 4.3 Match Execution Flow
```
1. Match starts → Create MatchEngine instance
2. Load scenario data from files
3. Initialize participants from MatchCharacter records:
   - Load all MatchCharacters for the match
   - Create character references with is_alive status
   - Pass to MatchEngine.run_match()

4. Execute rounds with delays:
   - Process round logic
   - Update MatchCharacter.is_alive in database
   - Store events in database
   - Wait 5-10 seconds
   - Repeat until one survivor

5. On elimination/revival:
   - Update MatchCharacter.is_alive immediately
   - Track elimination_round if character dies
   - Maintain alive_pool and dead_pool in engine

6. On completion:
   - Sync final MatchCharacter states to OwnedCharacter
   - Calculate kill awards and winner payout
   - Store payout calculations for future settlement
   - Mark match as "completed"
```

### 4.4 Post-Match Flow
```
1. Match completion triggers:
   - Update MatchCharacter final states
   - Sync OwnedCharacter.is_alive from match results
   - Calculate kill awards and winner payout
   - Store payout calculations for future settlement
   - Mark match as "completed"

2. Players can view:
   - Final match results
   - Characters that died (need revival)
   - Pending payouts (to be settled in future phase)
```

## 5. API Endpoint Design

### 5.1 Character Management
```
POST   /characters/purchase      (mock payment for testing)
GET    /characters/inventory
POST   /characters/{id}/revive   (deferred - needs payment)
GET    /characters/{id}/revival-fee
```

### 5.2 Match Management
```
POST   /matches/create
GET    /matches/open
GET    /matches/{id}
POST   /matches/{id}/join       (mock payment for testing)
GET    /matches/{id}/events
GET    /matches/{id}/status
```

### 5.3 Player Stats
```
GET    /players/profile
GET    /players/{address}/stats
GET    /players/{address}/match-history
```

## 6. Implementation Plan

### 6.1 Database Schema Updates
1. Create `owned_characters` table
2. Create `match_join_requests` table
3. Modify `characters` to reference `owned_characters`
4. Add new fields to `matches` table
5. Create proper indexes for query performance

### 6.2 Character Inventory System
1. Implement `OwnedCharacter` model and repository
2. Create `CharacterInventoryService`
3. Add character purchase endpoints
4. Implement inventory viewing endpoints
5. Add character revival logic

### 6.3 Match Creation & Lobby System
1. Extend `Match` model with lobby fields
2. Implement match creation with parameters
3. Create join request validation
4. Add countdown timer logic
5. Implement player slot management

### 6.4 Game Engine Integration
1. Modify `MatchEngine` to work with `MatchCharacter` records
2. Update character status in `MatchCharacter` during match events
3. Add round delay mechanism (5-10 seconds)
4. Create background task for match execution using existing scheduler
5. Implement event streaming for polling
6. Add post-match sync of `OwnedCharacter.is_alive` status

### 6.5 Testing Infrastructure
1. Create test fixtures for owned characters
2. Mock payment flows with `MockPaymentProvider`
3. Test concurrent match execution
4. Verify countdown timer edge cases
5. Test character status synchronization

## 7. Technical Considerations

### 7.1 Concurrency & Race Conditions
- **Match Joining**: Use database locks when reserving character slots
- **Payment Processing**: Implement idempotent payment verification
- **Character Selection**: Prevent using same character in multiple pending matches
- **Countdown Timers**: Handle edge cases where multiple players join simultaneously

### 7.2 Match Start Failures
**Avoiding Refund Transaction Fees**: 
- Instead of refunding when matches fail to start, consider:
  - **Escrow approach**: Don't capture payment until match confirms start
  - **Credit system**: Convert failed entry fees to platform credits for future use
  - **Minimum player guarantee**: Only create matches when minimum players are ready
- For Phase 2.5, use mock payments to test these flows without real fees

### 7.3 Performance Optimization
- **Database Queries**: Index on (player_id, is_alive) for character queries
- **Event Polling**: Implement cursor-based pagination for event feeds
- **Batch Operations**: Process multiple joins/payments in single transaction
- **Caching**: Cache match parameters and player stats

### 7.4 Error Handling
- **Payment Failures**: Graceful handling with clear user messaging
- **Match Start Failures**: Rollback all joins and issue refunds
- **Character State**: Ensure consistency between match and inventory status
- **Network Issues**: Retry logic for blockchain operations

### 7.5 State Management
- **Match Lifecycle**: Clear state transitions with validation
- **Character Lifecycle**: Enforce business rules (no dead chars in matches)
- **Payment Lifecycle**: Track from initiation through settlement
- **Inventory Consistency**: Sync character status after each match

## 8. Migration Strategy

### 8.1 From Simulation to Real Game
1. Preserve existing `MatchEngine` logic
2. Adapt character creation to use inventory system
3. Replace simulated payments with real payment service
4. Add round delays without changing game logic

### 8.2 Database Migration
1. Create new tables without breaking existing
2. Migrate existing characters to owned_characters
3. Update foreign key relationships
4. Backfill any missing data

### 8.3 Configuration Updates
1. Add new match parameter ranges
2. Configure round delay settings
3. Set revival fee amounts
4. Define treasury addresses per network

## 9. Security Considerations

### 9.1 Parameter Validation
- Enforce min/max on all match parameters
- Validate character ownership before joining
- Prevent negative or overflow amounts
- Ensure characters are alive before match entry

### 9.2 State Validation
- Prevent using same character in multiple pending matches
- Validate match state transitions
- Ensure atomic updates for character status
- Prevent race conditions in match joining