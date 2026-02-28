import os

import yaml

from .game_config import GameConfig

DEFAULT_CONFIG_PATH = os.getenv(
    "CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml"),
)


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> GameConfig:
    """Loads game configuration from a YAML file and returns a typed GameConfig."""
    try:
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            raise ValueError("Config file is not a valid YAML dictionary.")
        return GameConfig(**raw)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing configuration file: {e}")
