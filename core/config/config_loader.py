# /home/ubuntu/coin_clash/core/config/config_loader.py

"""Configuration loading utilities for Coin Clash."""

import os
import yaml
from typing import Dict, Any

DEFAULT_CONFIG_PATH = os.getenv(
    "CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
)

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        if not isinstance(config, dict):
            raise ValueError("Config file is not a valid YAML dictionary.")
        # Basic validation (can be expanded)
        required_keys = [
            "min_fee", "default_fee", "max_fee",
            "kill_award_rate_min", "kill_award_rate_default", "kill_award_rate_max",
            "num_players_min", "num_players_default", "num_players_max",
            "chars_per_player_min", "chars_per_player_max",
            "primary_event_weights", "extra_events", "lethal_modifiers",
            "scenario_dir",
        ]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing configuration file: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred while loading config: {e}")

# Example usage:
# if __name__ == "__main__":
#     try:
#         config = load_config()
#         print("Config loaded successfully:")
#         print(config)
#     except (FileNotFoundError, ValueError, RuntimeError) as e:
#         print(f"Error: {e}")

