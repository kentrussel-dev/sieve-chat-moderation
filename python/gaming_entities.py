"""
Gaming Entities Disambiguation Module for Sieve.
Loads verified gaming proper nouns, publishers, game titles, and champions from config/gaming_entities.json
and detects entity mentions in chat messages to provide strong disambiguating signals.
"""

import json
import os
import re
from typing import Dict, List, Optional

ENTITIES_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "gaming_entities.json")


class GamingEntityDetector:
    def __init__(self):
        self.entity_map: Dict[str, Dict] = {}
        self.pattern_map: Dict[str, re.Pattern] = {}
        self.load_entities()

    def load_entities(self):
        if os.path.exists(ENTITIES_FILE):
            try:
                with open(ENTITIES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.entity_map = data.get("entities", {})
                    for name in self.entity_map.keys():
                        # Create case-insensitive boundary regex for multi-word or single-word entities
                        escaped = re.escape(name)
                        self.pattern_map[name] = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            except Exception as e:
                print(f"Notice: Failed to load gaming entities config: {e}")

    def detect_entities(self, text: str) -> List[Dict]:
        """Detects any recognized gaming entities present in the text."""
        if not text:
            return []

        matches = []
        for name, pattern in self.pattern_map.items():
            if pattern.search(text):
                info = self.entity_map.get(name, {})
                matches.append({
                    "name": name,
                    "type": info.get("type", "entity"),
                    "canonical_name": info.get("canonical_name", name),
                    "description": info.get("description", "")
                })

        return matches

    def format_for_llm_prompt(self, entities: List[Dict]) -> str:
        if not entities:
            return "None"
        return ", ".join([f"{e['name']} ({e['type']}: {e['canonical_name']})" for e in entities])


# Singleton detector instance
global_entity_detector = GamingEntityDetector()


def get_gaming_entities(text: str) -> List[Dict]:
    return global_entity_detector.detect_entities(text)


if __name__ == "__main__":
    sample = "Riot Games just announced a new patch for Valorant and Overwatch, we riot if it sucks KEKW"
    detected = get_gaming_entities(sample)
    print(f"Sample: '{sample}'")
    print(f"Detected Entities: {detected}")
    print(f"Prompt Injection: {global_entity_detector.format_for_llm_prompt(detected)}")
