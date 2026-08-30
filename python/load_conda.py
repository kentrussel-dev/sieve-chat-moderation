"""
CONDA In-Game Toxicity & Slang Dataset Loader & Preprocessor.
Extracts dual-annotated in-game chat samples (Weld et al., 2021) with utterance intent
(Explicit Toxic, Implicit Sarcasm, Aggressive Slang, Clean) and token-level slot classifications.
"""

import json
import os
import re
import pandas as pd
from typing import Dict, List, Tuple

CONDA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "conda")
EVAL_DIR = os.path.join(os.path.dirname(__file__), "..", "evaluation")

TRAIN_CSV = os.path.join(CONDA_DIR, "conda_train.csv")
VALID_CSV = os.path.join(CONDA_DIR, "conda_valid.csv")
FULL_CSV = os.path.join(CONDA_DIR, "45k_final_version.csv")
LEXICON_CSV = os.path.join(CONDA_DIR, "lexicon_refined_1209.csv")


def clean_utterance(text: str) -> str:
    if not isinstance(text, str):
        return ""
    # Clean separator artifacts [SEPA] while preserving spacing
    cleaned = re.sub(r"\[SEPA\]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def extract_conda_lexicon() -> Dict[str, str]:
    """Extracts domain gaming dictionary: Characters (C), Dota terms (D), Slang (S), Toxic (T)."""
    if not os.path.exists(LEXICON_CSV):
        return {}

    df = pd.read_csv(LEXICON_CSV)
    lexicon_map = {}

    for col in ["C", "D", "S", "T", "P"]:
        if col in df.columns:
            words = df[col].dropna().astype(str).str.lower().tolist()
            for w in words:
                w = w.strip()
                if len(w) >= 2:
                    lexicon_map[w] = col

    print(f"Extracted {len(lexicon_map):,} unique tokens from CONDA gaming lexicon.")
    return lexicon_map


def load_and_balance_conda(
    max_train_samples: int = 12000,
    max_test_samples: int = 4000
) -> Tuple[List[Dict], List[Dict]]:
    """Loads, cleans, and balances the CONDA in-game dataset."""
    os.makedirs(EVAL_DIR, exist_ok=True)

    if not os.path.exists(TRAIN_CSV) or not os.path.exists(VALID_CSV):
        raise FileNotFoundError(f"CONDA CSV files not found in {CONDA_DIR}")

    df_train = pd.read_csv(TRAIN_CSV)
    df_valid = pd.read_csv(VALID_CSV)

    def process_df(df: pd.DataFrame) -> List[Dict]:
        records = []
        for _, row in df.iterrows():
            raw_utt = row.get("utterance", "")
            cleaned = clean_utterance(raw_utt)
            if not cleaned or len(cleaned) < 2:
                continue

            intent = str(row.get("intentClass", "O")).strip().upper()
            slot_tokens = str(row.get("slotTokens", ""))

            # Binary Label Mapping:
            # E (Explicit Toxic) -> 1
            # I (Implicit Toxic / Sarcasm / Griefing) -> 1
            # A (Aggressive Slang / Game Banter) -> 0 (Benign false-alarm gaming slang)
            # O (Other / Clean discussion) -> 0 (Clean)
            if intent in ["E", "I"]:
                label = 1
                toxic_type = "explicit_toxic" if intent == "E" else "implicit_sarcasm"
            else:
                label = 0
                toxic_type = "gaming_slang_false_alarm" if intent == "A" else "clean_gaming"

            records.append({
                "text": cleaned,
                "label": label,
                "source": "conda_dota2",
                "intent_class": intent,
                "toxic_type": toxic_type,
                "slot_tokens": slot_tokens,
                "conversation_id": row.get("conversationId", 0),
                "player_id": str(row.get("playerId", "Player")),
                "chat_time": row.get("chatTime", 0)
            })
        return records

    train_records = process_df(df_train)
    valid_records = process_df(df_valid)

    # Balance train records: toxic vs clean
    toxic_train = [r for r in train_records if r["label"] == 1]
    clean_train = [r for r in train_records if r["label"] == 0]

    # Subsample to balanced quota
    quota_per_class = max_train_samples // 2
    balanced_train = toxic_train[:quota_per_class] + clean_train[:quota_per_class]

    # Balance test records
    toxic_test = [r for r in valid_records if r["label"] == 1]
    clean_test = [r for r in valid_records if r["label"] == 0]
    test_quota = max_test_samples // 2
    balanced_test = toxic_test[:test_quota] + clean_test[:test_quota]

    # Save to evaluation directory
    train_out = os.path.join(EVAL_DIR, "conda_train_dataset.json")
    test_out = os.path.join(EVAL_DIR, "conda_test_dataset.json")

    with open(train_out, "w", encoding="utf-8") as f:
        json.dump(balanced_train, f, indent=2)

    with open(test_out, "w", encoding="utf-8") as f:
        json.dump(balanced_test, f, indent=2)

    # Save lexicon map
    lexicon_map = extract_conda_lexicon()
    lex_out = os.path.join(EVAL_DIR, "conda_lexicon.json")
    with open(lex_out, "w", encoding="utf-8") as f:
        json.dump(lexicon_map, f, indent=2)

    print(f"CONDA Dataset processed:")
    print(f"  - Train Set: {len(balanced_train):,} samples (Toxic: {len([r for r in balanced_train if r['label'] == 1])}, Clean: {len([r for r in balanced_train if r['label'] == 0])}) -> {train_out}")
    print(f"  - Test Set:  {len(balanced_test):,} samples (Toxic: {len([r for r in balanced_test if r['label'] == 1])}, Clean: {len([r for r in balanced_test if r['label'] == 0])}) -> {test_out}")
    print(f"  - Lexicon:   {len(lexicon_map):,} tokens -> {lex_out}")

    return balanced_train, balanced_test


if __name__ == "__main__":
    load_and_balance_conda()
