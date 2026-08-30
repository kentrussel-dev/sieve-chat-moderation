"""
Emote Parser & Context Extractor for Sieve.
Reuses the 7TV/BTTV/FFZ/Twitch emote matching logic to extract emote tokens from chat messages
and enriches each detected emote with its verified sentiment/context classification.
"""

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

EMOTE_CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "emote_context.json")
EMOTE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "emotes_cache.json")


@dataclass
class EmoteMatch:
    name: str
    category: str  # playful/laughing, celebratory, sarcasm-marker, hostile/mocking, unclassified
    source: str    # 7tv, bttv, ffz, twitch


class EmoteContextParser:
    def __init__(self):
        self.emote_context_map: Dict[str, str] = {}
        self.known_emotes: Dict[str, str] = {}  # name -> source
        self.lower_to_canonical: Dict[str, str] = {}
        self.load_configurations()

    def load_configurations(self):
        # 1. Load sentiment classifications from config/emote_context.json
        if os.path.exists(EMOTE_CONTEXT_FILE):
            try:
                with open(EMOTE_CONTEXT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, info in data.get("emotes", {}).items():
                        self.emote_context_map[name] = info.get("category", "unclassified")
            except Exception as e:
                print(f"Notice: Failed to load emote context config: {e}")

        # 2. Load known emote vocabulary from cache
        if os.path.exists(EMOTE_CACHE_FILE):
            try:
                with open(EMOTE_CACHE_FILE, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    for name, item in cdata.get("emotes", {}).items():
                        self.known_emotes[name] = item.get("source", "7tv")
            except Exception:
                pass

        # 3. Add default core dictionary (mirrors web/src/utils/emoteParser.tsx)
        default_emotes = {
            "KEKW": "7tv", "OMEGALUL": "ffz", "Pog": "ffz", "PogChamp": "twitch",
            "POGGERS": "ffz", "PepeHands": "ffz", "pepeLaugh": "ffz", "Pepega": "ffz",
            "monkaS": "ffz", "monkaW": "ffz", "Sadge": "ffz", "LULW": "ffz", "LUL": "twitch",
            "catJAM": "ffz", "GIGACHAD": "ffz", "Copium": "ffz", "Hopium": "ffz",
            "Prayge": "ffz", "HUH": "ffz", "Aware": "ffz", "Clueless": "ffz",
            "DESPAIR": "ffz", "NODDERS": "ffz", "NOPERS": "ffz", "Kappa": "twitch",
            "Kapp": "ffz", "FeelsGoodMan": "ffz", "FeelsBadMan": "ffz", "WeirdChamp": "ffz",
            "5Head": "ffz", "BabyRage": "twitch", "4Head": "ffz", "3Head": "ffz",
            "LO": "7tv", "ICANT": "7tv", "pepeD": "7tv", "Classic": "7tv"
        }
        for name, src in default_emotes.items():
            if name not in self.known_emotes:
                self.known_emotes[name] = src

        # Build case-insensitive lookup
        self.lower_to_canonical = {k.lower(): k for k in self.known_emotes.keys()}

    def extract_emotes_from_text(self, text: str) -> List[EmoteMatch]:
        """Extracts all detected emotes and their sentiment context categories."""
        if not text:
            return []

        words = text.split()
        matches: List[EmoteMatch] = []
        seen = set()

        for raw_word in words:
            # Strip outer punctuation (e.g. "KEKW!", "(Pog)", "monkaS...")
            clean_word = re.sub(r"^[^\w]+|[^\w]+$", "", raw_word)
            canonical_name = None

            if raw_word in self.known_emotes:
                canonical_name = raw_word
            elif clean_word in self.known_emotes:
                canonical_name = clean_word
            elif clean_word.lower() in self.lower_to_canonical:
                canonical_name = self.lower_to_canonical[clean_word.lower()]

            if canonical_name and canonical_name not in seen:
                seen.add(canonical_name)
                cat = self.emote_context_map.get(canonical_name, "unclassified")
                src = self.known_emotes.get(canonical_name, "7tv")
                matches.append(EmoteMatch(name=canonical_name, category=cat, source=src))

        return matches

    def format_for_llm_prompt(self, matches: List[EmoteMatch]) -> str:
        """Formats emote matches for readable injection into Mesh 2 LLM prompt."""
        if not matches:
            return "None"
        items = [f"{m.name} [{m.category}]" for m in matches]
        return ", ".join(items)

    def get_scoring_adjustments(self) -> Dict[str, Dict]:
        if os.path.exists(EMOTE_CONTEXT_FILE):
            try:
                with open(EMOTE_CONTEXT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("scoring_adjustments", {})
            except Exception:
                pass
        return {}

    def apply_post_scoring_adjustment(
        self,
        raw_score: float,
        detected_emotes: List[EmoteMatch],
        is_severe: bool = False
    ) -> Tuple[float, str]:
        """
        Applies configurable post-scoring adjustment based on emote categories.
        Does NOT require model retraining.
        """
        if is_severe or not detected_emotes:
            return raw_score, ""

        adjustments = self.get_scoring_adjustments()
        has_playful = any(e.category == "playful/laughing" for e in detected_emotes)
        has_celebratory = any(e.category == "celebratory" for e in detected_emotes)
        has_mocking = any(e.category == "hostile/mocking" for e in detected_emotes)

        adj_score = raw_score
        note = ""

        if (has_playful or has_celebratory) and not has_mocking:
            cfg = adjustments.get("playful/laughing", {"multiplier": 0.40, "max_clamped_score": 0.25})
            multiplier = cfg.get("multiplier", 0.40)
            max_clamp = cfg.get("max_clamped_score", 0.25)
            adj_score = min(round(raw_score * multiplier, 4), max_clamp)
            em_names = [e.name for e in detected_emotes if e.category in ["playful/laughing", "celebratory"]]
            note = f"Emote post-adjustment ({em_names}): {raw_score:.3f} -> {adj_score:.3f}"

        elif has_mocking:
            cfg = adjustments.get("hostile/mocking", {"multiplier": 1.25, "min_floor_score": 0.62})
            multiplier = cfg.get("multiplier", 1.25)
            min_floor = cfg.get("min_floor_score", 0.62)
            adj_score = min(1.0, max(round(raw_score * multiplier, 4), min_floor))
            em_names = [e.name for e in detected_emotes if e.category == "hostile/mocking"]
            note = f"Mocking emote escalation ({em_names}): {raw_score:.3f} -> {adj_score:.3f}"

        return adj_score, note


# Singleton instance
global_emote_parser = EmoteContextParser()


def get_message_emotes(text: str) -> List[EmoteMatch]:
    return global_emote_parser.extract_emotes_from_text(text)


def apply_emote_adjustments(raw_score: float, detected_emotes: List[EmoteMatch], is_severe: bool = False) -> Tuple[float, str]:
    return global_emote_parser.apply_post_scoring_adjustment(raw_score, detected_emotes, is_severe)


if __name__ == "__main__":
    sample = "Bro you completely destroyed him KEKW PogChamp that was so clean Copium"
    extracted = get_message_emotes(sample)
    print(f"Sample: '{sample}'")
    print(f"Extracted Emotes: {extracted}")
    print(f"LLM Prompt Injection: {global_emote_parser.format_for_llm_prompt(extracted)}")
