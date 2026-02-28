import json
import os
from typing import Dict, List
import logging
from ..config.config_loader import load_config

logger = logging.getLogger(__name__)

config = load_config()
SCENARIO_DIR = config["scenario_dir"]

# Define expected scenario categories based on config/logic
EXPECTED_CATEGORIES = [
    "direct_kill",
    "self",
    "environmental",
    "group",
    "story", # Corresponds to non-lethal story events
    "comeback" # Although comeback is an event type, scenarios might be defined for flavor
]

# Define event types that map to scenario categories
# Note: Some events might not have dedicated scenario files (e.g., item finds might be part of 'story')
EVENT_TYPE_TO_CATEGORY = {
    "direct_kill": "direct_kill",
    "self": "self",
    "environmental": "environmental",
    "group": "group",
    "story": "story", # Primary non-lethal
    "non_lethal_story": "story", # Extra non-lethal
    "extra_lethal": ["direct_kill", "environmental"], # Extra lethal can pull from these
    "comeback": "comeback" # Or could just be a generic message
    # Item finds might be embedded in 'story' scenarios or handled separately
}

def load_scenarios(scenario_dir: str = SCENARIO_DIR) -> Dict[str, List[Dict[str, str]]]:
    """Loads all scenarios from JSON files in the specified directory."""
    scenarios = {category: [] for category in EXPECTED_CATEGORIES}
    scenario_files = {}
    try:
        for filename in os.listdir(scenario_dir):
            if filename.endswith(".json"):
                category_name = filename.replace(".json", "")
                if category_name in EXPECTED_CATEGORIES:
                    scenario_files[category_name] = os.path.join(scenario_dir, filename)
                else:
                    from ..common.exceptions import SkipEvent
                    raise SkipEvent(f"Ignoring unexpected scenario file: {filename}")

        for category, filepath in scenario_files.items():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Expecting a list of objects, each with at least a 'text' field
                        valid_scenarios = []
                        for i, item in enumerate(data):
                            if isinstance(item, dict) and "text" in item and isinstance(item["text"], str):
                                # Add a unique ID based on category and index
                                item["id"] = f"{category}_{i:03d}"
                                valid_scenarios.append(item)
                            else:
                                logger.warning(
                                    "invalid_scenario_format",
                                    extra={
                                        "filepath": filepath,
                                        "item_index": i,
                                        "item": item
                                    }
                                )
                        scenarios[category] = valid_scenarios
                        logger.info(
                            "scenarios_loaded",
                            extra={
                                "filepath": filepath,
                                "count": len(valid_scenarios)
                            }
                        )
                    else:
                        logger.error(
                            "invalid_scenario_json_format",
                            extra={
                                "filepath": filepath,
                                "expected": "list"
                            }
                        )
            except json.JSONDecodeError:
                logger.error(
                    "scenario_json_decode_error",
                    exc_info=True,
                    extra={
                        "filepath": filepath
                    }
                )
            except Exception:
                logger.error(
                    "scenario_file_read_error",
                    exc_info=True,
                    extra={
                        "filepath": filepath
                    }
                )

        # Check if any expected categories are missing or empty
        for category in EXPECTED_CATEGORIES:
            if not scenarios.get(category):
                # Allow comeback to be empty initially
                if category != "comeback":
                     logger.warning(
                        "no_valid_scenarios_for_category",
                        extra={
                            "category": category
                        }
                    )

        return scenarios

    except FileNotFoundError:
        logger.error(
            "scenario_directory_not_found",
            extra={
                "scenario_dir": scenario_dir
            }
        )
        return {category: [] for category in EXPECTED_CATEGORIES} # Return empty structure
    except Exception:
        logger.error(
            "scenario_loader_unexpected_error",
            exc_info=True
        )
        return {category: [] for category in EXPECTED_CATEGORIES}

