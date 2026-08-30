"""
Integration script for LMSYS ToxicChat dataset (https://huggingface.co/datasets/lmsys/toxic-chat).
Loads real-world human-annotated user conversations from Chatbot Arena,
processes them into Sieve schemas, and saves them for training and evaluation.
"""

import json
import os
from typing import Dict, List, Tuple
from datasets import load_dataset


def load_lmsys_toxic_chat() -> Tuple[List[Dict], List[Dict]]:
    print("Loading lmsys/toxic-chat dataset from Hugging Face...")
    raw_train = load_dataset("lmsys/toxic-chat", "toxicchat0124", split="train")
    raw_test = load_dataset("lmsys/toxic-chat", "toxicchat0124", split="test")

    train_data = []
    for idx, item in enumerate(raw_train):
        text = item.get("user_input", "").strip()
        if not text:
            continue
        is_toxic = int(item.get("toxicity", 0))
        train_data.append({
            "id": f"lmsys_train_{idx:05d}",
            "text": text,
            "label": is_toxic,
            "category": "toxic_real" if is_toxic else "clean_real",
            "tier_difficulty": "real_world",
            "jailbreaking": int(item.get("jailbreaking", 0)),
            "source": "lmsys/toxic-chat"
        })

    test_data = []
    for idx, item in enumerate(raw_test):
        text = item.get("user_input", "").strip()
        if not text:
            continue
        is_toxic = int(item.get("toxicity", 0))
        test_data.append({
            "id": f"lmsys_test_{idx:05d}",
            "text": text,
            "label": is_toxic,
            "category": "toxic_real" if is_toxic else "clean_real",
            "tier_difficulty": "real_world",
            "jailbreaking": int(item.get("jailbreaking", 0)),
            "source": "lmsys/toxic-chat"
        })

    print(f"Processed {len(train_data)} LMSYS train samples and {len(test_data)} test samples.")
    return train_data, test_data


def save_processed_datasets():
    train_data, test_data = load_lmsys_toxic_chat()
    
    out_dir = os.path.join(os.path.dirname(__file__), "..", "evaluation")
    os.makedirs(out_dir, exist_ok=True)
    
    train_path = os.path.join(out_dir, "lmsys_train_dataset.json")
    test_path = os.path.join(out_dir, "lmsys_test_dataset.json")

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)

    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"Saved LMSYS train dataset to: {train_path}")
    print(f"Saved LMSYS test dataset to:  {test_path}")


if __name__ == "__main__":
    save_processed_datasets()
