"""
Extraction and preprocessing utility for the Sensai Toxic Chat dataset (uetchy/sensai).
Loads real-world YouTube and VTuber live stream chats from Kaggle parquet files,
cleans and balances the dataset, and saves structured train and test splits for Sieve.
"""

import glob
import json
import os
import random
import re
from typing import Dict, List, Tuple
import pandas as pd


SENSAI_CACHE_DIR = r"C:\Users\Kent Russel\.cache\kagglehub\datasets\uetchy\sensai\versions\3"


def clean_chat_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    # Remove excessive repeated chars (e.g. "looooooool" -> "loool")
    text = re.sub(r'(.)\1{4,}', r'\1\1\1', text)
    return text.strip()


def load_sensai_dataset(max_samples_per_class: int = 4000) -> Tuple[List[Dict], List[Dict]]:
    flagged_files = glob.glob(os.path.join(SENSAI_CACHE_DIR, "chats_flagged_*.parquet"))
    nonflag_files = glob.glob(os.path.join(SENSAI_CACHE_DIR, "chats_nonflag_*.parquet"))

    print(f"Found {len(flagged_files)} flagged parquet files and {len(nonflag_files)} non-flagged files.")

    flagged_texts = []
    for f in flagged_files:
        try:
            df = pd.read_parquet(f)
            if "body" in df.columns:
                texts = df["body"].dropna().astype(str).tolist()
                for t in texts:
                    cleaned = clean_chat_text(t)
                    # Filter out purely non-latin or ultra-short single character spam
                    if len(cleaned) >= 3:
                        flagged_texts.append(cleaned)
                    if len(flagged_texts) >= max_samples_per_class * 2:
                        break
        except Exception as e:
            print(f"Warning reading {f}: {e}")
        if len(flagged_texts) >= max_samples_per_class * 2:
            break

    nonflag_texts = []
    for f in nonflag_files:
        try:
            df = pd.read_parquet(f)
            if "body" in df.columns:
                texts = df["body"].dropna().astype(str).tolist()
                for t in texts:
                    cleaned = clean_chat_text(t)
                    if len(cleaned) >= 3:
                        nonflag_texts.append(cleaned)
                    if len(nonflag_texts) >= max_samples_per_class * 2:
                        break
        except Exception as e:
            print(f"Warning reading {f}: {e}")
        if len(nonflag_texts) >= max_samples_per_class * 2:
            break

    random.seed(42)
    random.shuffle(flagged_texts)
    random.shuffle(nonflag_texts)

    flagged_samples = flagged_texts[:max_samples_per_class]
    nonflag_samples = nonflag_texts[:max_samples_per_class]

    print(f"Extracted {len(flagged_samples)} flagged live chat messages and {len(nonflag_samples)} non-flagged messages.")

    # 70% Train, 30% Test
    split_idx = int(max_samples_per_class * 0.70)

    train_data = []
    test_data = []

    # Non-flagged (Clean live chat)
    for i, t in enumerate(nonflag_samples[:split_idx]):
        train_data.append({
            "id": f"sensai_train_clean_{i:05d}",
            "text": t,
            "label": 0,
            "category": "live_chat_clean",
            "tier_difficulty": "live_stream",
            "source": "uetchy/sensai"
        })
    for i, t in enumerate(nonflag_samples[split_idx:]):
        test_data.append({
            "id": f"sensai_test_clean_{i:05d}",
            "text": t,
            "label": 0,
            "category": "live_chat_clean",
            "tier_difficulty": "live_stream",
            "source": "uetchy/sensai"
        })

    # Flagged (Toxic / Deleted live chat)
    for i, t in enumerate(flagged_samples[:split_idx]):
        train_data.append({
            "id": f"sensai_train_flagged_{i:05d}",
            "text": t,
            "label": 1,
            "category": "live_chat_toxic",
            "tier_difficulty": "live_stream",
            "source": "uetchy/sensai"
        })
    for i, t in enumerate(flagged_samples[split_idx:]):
        test_data.append({
            "id": f"sensai_test_flagged_{i:05d}",
            "text": t,
            "label": 1,
            "category": "live_chat_toxic",
            "tier_difficulty": "live_stream",
            "source": "uetchy/sensai"
        })

    random.shuffle(train_data)
    random.shuffle(test_data)

    return train_data, test_data


def save_sensai_datasets():
    train_data, test_data = load_sensai_dataset(max_samples_per_class=4000)
    
    out_dir = os.path.join(os.path.dirname(__file__), "..", "evaluation")
    os.makedirs(out_dir, exist_ok=True)
    
    train_path = os.path.join(out_dir, "sensai_train_dataset.json")
    test_path = os.path.join(out_dir, "sensai_test_dataset.json")

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)

    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(train_data)} Sensai train samples to {train_path}")
    print(f"Saved {len(test_data)} Sensai test samples to {test_path}")


if __name__ == "__main__":
    save_sensai_datasets()
