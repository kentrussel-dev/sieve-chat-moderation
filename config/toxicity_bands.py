"""
Configurable 6-Level Calibrated Toxicity Bands & Routing Configuration for Sieve.
Centralizes score ranges, semantic level labels, descriptions, and routing margins.
"""

import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ToxicityBand:
    level: int
    min_score: float
    max_score: float
    label: str
    description: str
    default_action: str  # "PASS", "PASS_REVIEW_QUEUE", "ESCALATE_LLM", "FLAG", "FLAG_TIER_0"


# Named Band Constants (1 to 6)
LEVEL_1_CLEAN = ToxicityBand(
    level=1,
    min_score=0.00,
    max_score=0.15,
    label="Clean",
    description="Normal, positive, or neutral chat (greetings, gg/glhf, casual talk)",
    default_action="PASS"
)

LEVEL_2_GAMING_SLANG = ToxicityBand(
    level=2,
    min_score=0.16,
    max_score=0.35,
    label="Gaming Slang (False Alarm)",
    description="Contains trigger words ('kill', 'destroy', 'murdered that play') but non-hostile in context",
    default_action="PASS_REVIEW_QUEUE"
)

LEVEL_3_AMBIGUOUS_SARCASTIC = ToxicityBand(
    level=3,
    min_score=0.36,
    max_score=0.55,
    label="Ambiguous / Sarcastic",
    description="Tone unclear without context; dry sarcasm, backhanded comments",
    default_action="ESCALATE_LLM"
)

LEVEL_4_SUBTLE_HOSTILITY = ToxicityBand(
    level=4,
    min_score=0.56,
    max_score=0.70,
    label="Subtle Hostility",
    description="Passive-aggressive, mocking, condescension without explicit insults",
    default_action="ESCALATE_LLM"
)

LEVEL_5_TOXIC = ToxicityBand(
    level=5,
    min_score=0.71,
    max_score=0.88,
    label="Toxic",
    description="Direct insults, flaming, targeted harassment",
    default_action="FLAG"
)

LEVEL_6_SEVERE_EXTREME = ToxicityBand(
    level=6,
    min_score=0.89,
    max_score=1.00,
    label="Severe/Extreme",
    description="Slurs, threats, hate speech, extremist content, doxxing",
    default_action="FLAG_TIER_0"
)

ALL_BANDS: List[ToxicityBand] = [
    LEVEL_1_CLEAN,
    LEVEL_2_GAMING_SLANG,
    LEVEL_3_AMBIGUOUS_SARCASTIC,
    LEVEL_4_SUBTLE_HOSTILITY,
    LEVEL_5_TOXIC,
    LEVEL_6_SEVERE_EXTREME,
]

BAND_BY_LEVEL: Dict[int, ToxicityBand] = {band.level: band for band in ALL_BANDS}

# Configurable Routing Margins (Tuning Parameters)
LEVEL_2_REVIEW_MARGIN = 0.03   # Near Level 2/3 boundary (score >= 0.32) -> send to review queue
LEVEL_5_OVERRIDE_MARGIN = 0.03 # Near Level 4/5 boundary (score <= 0.74) -> allow Mesh 2 override


def map_score_to_band(score: float) -> ToxicityBand:
    """
    Maps a continuous calibrated score [0.00, 1.00] to its corresponding ToxicityBand.
    Uses sequential upper-bound evaluation to prevent floating-point discretization gaps.
    """
    s = max(0.00, min(1.00, float(score)))
    if s <= LEVEL_1_CLEAN.max_score:
        return LEVEL_1_CLEAN
    elif s <= LEVEL_2_GAMING_SLANG.max_score:
        return LEVEL_2_GAMING_SLANG
    elif s <= LEVEL_3_AMBIGUOUS_SARCASTIC.max_score:
        return LEVEL_3_AMBIGUOUS_SARCASTIC
    elif s <= LEVEL_4_SUBTLE_HOSTILITY.max_score:
        return LEVEL_4_SUBTLE_HOSTILITY
    elif s <= LEVEL_5_TOXIC.max_score:
        return LEVEL_5_TOXIC
    else:
        return LEVEL_6_SEVERE_EXTREME


def export_bands_to_json(filepath: Optional[str] = None) -> str:
    """Exports band definitions to JSON for cross-service portability (Go, TypeScript)."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), "toxicity_bands.json")
    
    payload = {
        "bands": [asdict(b) for b in ALL_BANDS],
        "routing_margins": {
            "level_2_review_margin": LEVEL_2_REVIEW_MARGIN,
            "level_5_override_margin": LEVEL_5_OVERRIDE_MARGIN
        }
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return filepath


if __name__ == "__main__":
    out = export_bands_to_json()
    print(f"Exported toxicity bands configuration to {out}")
