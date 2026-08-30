import sys
import os

# Link to root config
root_config = os.path.join(os.path.dirname(__file__), "..", "..", "config")
if root_config not in sys.path:
    sys.path.insert(0, root_config)

from toxicity_bands import (
    ToxicityBand,
    LEVEL_1_CLEAN,
    LEVEL_2_GAMING_SLANG,
    LEVEL_3_AMBIGUOUS_SARCASTIC,
    LEVEL_4_SUBTLE_HOSTILITY,
    LEVEL_5_TOXIC,
    LEVEL_6_SEVERE_EXTREME,
    ALL_BANDS,
    BAND_BY_LEVEL,
    LEVEL_2_REVIEW_MARGIN,
    LEVEL_5_OVERRIDE_MARGIN,
    map_score_to_band,
    export_bands_to_json,
)
