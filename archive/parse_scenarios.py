# /home/ubuntu/coin_clash/parse_scenarios.py
import json
import re
import os
from core.config_loader import load_config

config = load_config()
SCENARIO_DIR            = config["scenario_dir"]
EXISTING_SCENARIOS_FILE = config["existing_scenarios_file"]
NEW_SCENARIOS_FILE      = config["new_scenarios_file"]

CATEGORY_MAP = {
    "Direct Kills": "direct_kill",
    "Self-Eliminations": "self",
    "Environmental / Accidental Deaths": "environmental",
    "Group Eliminations": "group",
    "Non-Elimination Chaos": "story", # Map Non-Elimination Chaos to story
    "Comeback Scenarios": "comeback"
}

def parse_markdown_scenarios(filepath):
    scenarios = {cat: [] for cat in CATEGORY_MAP.values()}
    current_category_key = None
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("### ") or line.startswith("## "):
                    # Extract category name, handling variations
                    category_name = line.replace("###", "").replace("##", "").replace("(Additional)", "").strip(" *:")
                    current_category_key = CATEGORY_MAP.get(category_name)
                    if not current_category_key:
                        print(f"Warning: Unmapped category found in {filepath}: {category_name}")
                elif current_category_key and (line.startswith("*") or re.match(r"^\d+\.", line)):
                    # Extract scenario text, removing list markers and leading titles
                    text = re.sub(r"^\*\s*", "", line)
                    text = re.sub(r"^\d+\.\s*", "", text)
                    text = re.sub(r"^\*\*.*?\*\*\s*–\s*", "", text) # Remove bold title like **Deck-Draw Duel** –
                    text = text.strip()
                    # Remove potential item find notes for JSON
                    text = re.sub(r"\s*\(Item Find:.*?\)$", "", text)
                    if text:
                        scenarios[current_category_key].append({"text": text})
    except FileNotFoundError:
        print(f"Error: File not found {filepath}")
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return scenarios

def main():
    os.makedirs(SCENARIO_DIR, exist_ok=True)

    print("Parsing existing scenarios...")
    existing = parse_markdown_scenarios(EXISTING_SCENARIOS_FILE)
    print("Parsing new scenarios...")
    new = parse_markdown_scenarios(NEW_SCENARIOS_FILE)

    # Combine scenarios
    combined_scenarios = {cat: [] for cat in CATEGORY_MAP.values()}
    for category in combined_scenarios:
        combined_scenarios[category].extend(existing.get(category, []))
        combined_scenarios[category].extend(new.get(category, []))
        print(f"Category 	{category}	 has {len(combined_scenarios[category])} scenarios.")


    # Write JSON files
    for category, scenario_list in combined_scenarios.items():
        if scenario_list: # Only write if there are scenarios
            filepath = os.path.join(SCENARIO_DIR, f"{category}.json")
            try:
                with open(filepath, "w") as f:
                    json.dump(scenario_list, f, indent=2)
                print(f"Successfully wrote {len(scenario_list)} scenarios to {filepath}")
            except Exception as e:
                print(f"Error writing {filepath}: {e}")
        else:
             print(f"Skipping empty category: {category}")

if __name__ == "__main__":
    main()


