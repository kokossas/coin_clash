# Scripts

Development and testing utilities for Coin Clash.

## Match Simulation

### simulate_match.py

Run a full match simulation without a database. Uses real game engine, scenarios, and config.

**Usage:**

```bash
# Default 4-player match
python scripts/simulate_match.py

# Uniform distribution: 6 players, 2 chars each
python scripts/simulate_match.py --players 6 --chars-per-player 2 --entry-fee 1.0 --seed 42

# Custom distribution: 4 players with 3, 1, 2, 1 chars respectively
python scripts/simulate_match.py --char-distribution 3,1,2,1 --entry-fee 1.0 --seed 7

# Extreme scenarios
python scripts/simulate_match.py --players 50 --entry-fee 5.0 --kill-award-rate 0.5 --seed 99
```

**Parameters:**

- `--players`: Number of players (3-50, default: 4)
- `--chars-per-player`: Characters per player (1-3, default: 1)
- `--char-distribution`: Comma-separated chars per player (overrides --players and --chars-per-player)
- `--entry-fee`: Entry fee per character (0.5-5.0, default: 1.0)
- `--kill-award-rate`: Kill reward rate (0.0-0.5, default: 0.1)
- `--seed`: Random seed for reproducibility (default: 42)

**Output:**

- Round-by-round match log with event descriptions
- Economic summary: pool, protocol fees, kill awards, winner payout
- Validates against config constraints from `config.yaml`

### batch_simulate.py

Batch test runner for `simulate_match.py`. Runs 24 scenarios covering edge cases and validates economic invariants.

**Usage:**

```bash
# Run all scenarios
python scripts/batch_simulate.py

# Filter by category
python scripts/batch_simulate.py --filter boundary
python scripts/batch_simulate.py --filter economic
python scripts/batch_simulate.py --filter distribution

# Verbose output (show full match logs)
python scripts/batch_simulate.py --verbose
```

**Test Categories:**

- `boundary`: Min/max values (players, chars, fees, kill rates)
- `distribution`: Asymmetric player power (whales vs minnows)
- `economic`: Protocol fee tiers, high/low stakes combinations
- `normal`: Typical match configurations
- `randomness`: Same config with different seeds

**Validation:**

Each scenario validates:
- Total pool = characters × entry_fee
- Protocol fee + pool_after_protocol = total_pool
- Kill awards + winner payout ≤ pool_after_protocol
- No negative values

**Exit codes:**
- 0: All tests passed
- 1: One or more tests failed
