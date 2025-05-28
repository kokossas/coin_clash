# /home/ubuntu/coin_clash/__main__.py

import logging
import os
import sys

# Add project root to path to allow imports like core.engine
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.config.config_loader import load_config
from core.match.scenario_loader import load_scenarios
from core.database.models import init_db, Player, Character
from core.database.db import get_session
from core.player.repository import SqlPlayerRepo
from core.player.character_repository import SqlCharacterRepo
from core.match.repository import SqlMatchRepo
from core.match.event_repository import SqlEventRepo
from core.player.item_repository import SqlItemRepo
from core.match.engine import MatchEngine
from core.common.utils import SeedableRandom, get_next_character_name
from core.config.logging_config import JSONFormatter

logger = logging.getLogger()
logger.setLevel(logging.INFO)

json_handler = logging.StreamHandler(sys.stdout)
json_handler.setFormatter(JSONFormatter())
logger.handlers = [json_handler]

# --- Constants --- 
DEFAULT_SEED = 42 # set to None for random seed
CHARACTER_NAME_LIST_PATH = None # Use internal list from utils

def setup_repositories(db_session):
    """Initializes and returns all repository instances."""
    return {
        "player": SqlPlayerRepo(db_session),
        "character": SqlCharacterRepo(db_session),
        "match": SqlMatchRepo(db_session),
        "event": SqlEventRepo(db_session),
        "item": SqlItemRepo(db_session)
    }

def simulate_character_purchases(config: dict, players: list[Player], repos: dict, match_id: int, random_gen: SeedableRandom) -> list[Character]:
    """Simulates players purchasing characters for a match."""
    participants = []
    player_repo = repos["player"]
    char_repo = repos["character"]
    entry_fee = config["default_fee"] # Use default fee for simulation
    min_chars = config["chars_per_player_min"]
    max_chars = config["chars_per_player_max"]

    logger.info(
        "simulating_character_purchases_started",
        extra={"player_count": len(players)}
    )

    total_fees_collected = 0
    protocol_cut_total = 0

    for player in players:
        num_chars_to_buy = random_gen.randint(min_chars, max_chars)
        logger.debug(
            "player_buying_characters",
            extra={
                "username": player.username,
                "num_characters": num_chars_to_buy
            }
        )

        # --- Fee Calculation & Protocol Cut --- 
        # Determine protocol cut rate based on number of characters bought *by this player*
        cut_rate_key = str(num_chars_to_buy)
        protocol_cut_rate = config["protocol_cut"].get(cut_rate_key)
        if protocol_cut_rate is None:
            # Fallback if specific number isn't in config (e.g., if max_chars > 3)
            # Use the rate for the highest defined tier or a default? Let's use highest defined.
            max_tier = max(config["protocol_cut"].keys(), key=int)
            protocol_cut_rate = config["protocol_cut"][max_tier]
            logger.warning(
                "protocol_cut_rate_fallback",
                extra={
                    "requested_chars": num_chars_to_buy,
                    "fallback_tier": max_tier,
                    "used_rate": protocol_cut_rate
                }
            )
        
        fee_per_char = entry_fee
        total_cost = num_chars_to_buy * fee_per_char
        cut_amount = total_cost * protocol_cut_rate
        net_fee_to_pool = total_cost - cut_amount

        total_fees_collected += total_cost
        protocol_cut_total += cut_amount

        # --- Stubbed Payment --- 
        # Deduct fee from player balance (assuming they have enough for simulation)
        # In a real scenario, check balance before allowing purchase
        # player_repo.update_player_balance(player.id, -total_cost)
        logger.info(
            "player_charged",
            extra={
                "username": player.username,
                "charged_amount": total_cost,
                "protocol_cut": cut_amount,
                "added_to_pool": net_fee_to_pool
            }
        )

        # --- Create Characters --- 
        for _ in range(num_chars_to_buy):
            char_name = get_next_character_name() # Get sequential name
            character = char_repo.create_character(name=char_name, owner_username=player.username)
            # Assign character to the match immediately
            char_repo.assign_character_to_match(character.id, match_id)
            participants.append(character)
            logger.debug(
                "character_created",
                extra={
                    "match_id": match_id,
                    "character_id": character.id,
                    "display_name": character.display_name
                }
            )

    logger.info(
        "purchase_summary",
        extra={
            "total_fees": total_fees_collected,
            "total_protocol_cut": protocol_cut_total
        }
    )
    # TODO: Store protocol_cut_total somewhere accessible to the engine's payout calculation?
    # Maybe update the Match object with this info?

    return participants

def run_simulation(seed: int = DEFAULT_SEED):
    """Runs a full game simulation."""
    logger.info("simulation_started")
    random_gen = SeedableRandom(seed)
    logger.info(
        "using_random_seed",
        extra={"seed": seed}
    )

    # 1. Load Config & Scenarios
    try:
        config = load_config()
        logger.info("Configuration loaded successfully.")
        # Load scenarios directly from the JSON directory
        scenarios = load_scenarios(config["scenario_dir"])

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(
            "config_or_scenarios_load_failed",
            extra={"error": str(e)}
        )
        return

    # 2. Initialize Database & Repositories
    init_db()  # Ensure tables are created
    with get_session() as db_session:
        repos = setup_repositories(db_session)
        logger.info("Database and repositories initialized.")

        # 3. Initialize or Load Players
        num_players = config["num_players_default"]
        players = repos["player"].get_all_players(limit=num_players)
        if len(players) < num_players:
            logger.info(
                "players_discovery",
                extra={
                    "existing_players": len(players),
                    "players_to_create": num_players - len(players)
                }
            )
            for i in range(len(players), num_players):
                username = f"Player_{i+1:03d}"
                player = repos["player"].get_or_create_player(username)
                # Give some starting balance for simulation if needed
                # repos["player"].update_player_balance(player.id, 100.0) 
                players.append(player)
        logger.info(
            "players_ready",
            extra={"total_players": len(players)}
        )

        # 4. Create Match
        match = repos["match"].create_match(
            entry_fee=config["default_fee"],
            kill_award_rate=config["kill_award_rate_default"],
            start_method='cap', # Using cap for simulation
            start_threshold=1 # Start immediately after purchases for simulation
        )
        logger.info(
            "match_created",
            extra={"match_id": match.id}
        )

        # 5. Simulate Purchases
        participants = simulate_character_purchases(config, players, repos, match.id, random_gen)
        if len(participants) < config["num_players_min"] * config["chars_per_player_min"]:
            logger.error(
                "not_enough_participants",
                extra={"participant_count": len(participants), "minimum_required": config["players_min"] * config["chars_per_player_min"]}
            )
            return
        logger.info(
            "participants_summary",
            extra={"total_participants": len(participants)}
        )

        # 6. Initialize & Run Match Engine
        engine = MatchEngine(
            match_id=match.id,
            config=config,
            scenarios=scenarios,
            player_repo=repos["player"],
            character_repo=repos["character"],
            match_repo=repos["match"],
            event_repo=repos["event"],
            item_repo=repos["item"],
            random_seed=seed
        )
        
        logger.info(
            "match_engine_starting",
            extra={"match_id": match.id}
        )
        winner, match_log = engine.run_match(participants)

        # 7. Print Results
        logger.info("simulation_completed")
        print("\n===== Match Log =====")
        for line in match_log:
            print(line)
        print("=====================")

        if winner:
            logger.info(
                "final_winner_declared",
                extra={"winner_display_name": winner.display_name, "match_id": match.id}
            )
            # Display player stats post-match (optional)
            # winner_player = repos["player"].get_player_by_username(winner.owner_username)
            # print(f"Winner Stats ({winner_player.username}): Wins={winner_player.wins}, Kills={winner_player.kills}, Balance={winner_player.balance:.2f}")
        else:
            logger.warning(
                "match_ended_without_winner",
                extra={"match_id": match.id}
            )


# if __name__ == "__main__":
#     # You can pass a seed as a command line argument
#     sim_seed = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SEED
#     run_simulation(seed=sim_seed)

# # if __name__ == "__main__":
# #     # Batch simulate 100 matches; logs go to all_runs.log
# #     for seed in range(1, 45):
# #         logger.info(f"========== Starting simulation for seed: {seed} ==========")
# #         run_simulation(seed=seed)

def main():
    # decide between single-run and batch-run
    args = sys.argv[1:]

    if args and args[0] == "batch":
        file_handler = logging.FileHandler("tests/all_runs.log")
        file_handler.setFormatter(JSONFormatter())
        logging.getLogger().addHandler(file_handler)

        for seed in range(1, 50):
            logging.getLogger().info(
                "batch_start_seed",
                extra={"seed": seed}
            )
            run_simulation(seed=seed)
    else:
        # single-run mode: optionally pass a seed number
        sim_seed = int(args[0]) if args else DEFAULT_SEED
        run_simulation(seed=sim_seed)

if __name__ == "__main__":
    main()