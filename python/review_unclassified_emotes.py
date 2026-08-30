"""
Unclassified Emote Review Script for Sieve.
Identifies unclassified or missing emotes in config/emote_context.json and computes
their occurrence frequency in recent chat logs, allowing targeted prioritization.
"""

import argparse
import collections
import json
import os
import re
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(__file__))
from emote_fetcher import load_cached_emotes

EMOTE_CONTEXT_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "emote_context.json")
CONDA_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "conda", "conda_train.csv")
SENSAI_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "evaluation", "sensai_train_dataset.json")


def load_emote_context() -> Dict[str, Dict]:
    if os.path.exists(EMOTE_CONTEXT_PATH):
        with open(EMOTE_CONTEXT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("emotes", {})
    return {}


def scan_chat_logs_for_emote_counts(emote_names: set) -> collections.Counter:
    """Scans local chat corpora to count how often each emote appeared in real chats."""
    counts = collections.Counter()

    # 1. Scan Sensai Live Chat Dataset
    if os.path.exists(SENSAI_DATA_PATH):
        try:
            with open(SENSAI_DATA_PATH, "r", encoding="utf-8") as f:
                sensai_data = json.load(f)
            for item in sensai_data:
                words = re.findall(r"\b\w+\b", item.get("text", ""))
                for w in words:
                    if w in emote_names:
                        counts[w] += 1
        except Exception:
            pass

    # 2. Scan CONDA Dota 2 Dataset
    if os.path.exists(CONDA_DATA_PATH):
        try:
            import pandas as pd
            df = pd.read_csv(CONDA_DATA_PATH)
            for text in df["utterance"].dropna():
                words = re.findall(r"\b\w+\b", str(text))
                for w in words:
                    if w in emote_names:
                        counts[w] += 1
        except Exception:
            pass

    return counts


def main():
    parser = argparse.ArgumentParser(description="Review Unclassified Emotes for Sieve")
    parser.add_argument("--top", type=int, default=25, help="Number of top unclassified emotes to display")
    args = parser.parse_args()

    cached_emotes = load_cached_emotes()
    classified_map = load_emote_context()

    unclassified_emotes = []
    classified_counts = collections.defaultdict(int)

    for emote_name in cached_emotes.keys():
        context_info = classified_map.get(emote_name)
        if not context_info or context_info.get("category") == "unclassified":
            unclassified_emotes.append(emote_name)
        else:
            cat = context_info.get("category", "unclassified")
            classified_counts[cat] += 1

    # Scan chat logs for frequency
    freq_counts = scan_chat_logs_for_emote_counts(set(cached_emotes.keys()))

    # Sort unclassified emotes by frequency
    sorted_unclassified = sorted(
        unclassified_emotes,
        key=lambda name: freq_counts.get(name, 0),
        reverse=True
    )

    print("\n" + "=" * 76)
    print("           SIEVE EMOTE SENTIMENT & CONTEXT REVIEW REPORT")
    print("=" * 76)
    print(f"Total Cached Emotes:         {len(cached_emotes):,}")
    print(f"Total Classified Emotes:     {len(classified_map) - len([e for e, v in classified_map.items() if v.get('category') == 'unclassified']):,}")
    print(f"Total Unclassified Emotes:   {len(unclassified_emotes):,}")
    print("-" * 76)
    print("Current Category Breakdown:")
    for cat, count in classified_counts.items():
        print(f"  • {cat:<22} : {count:,} emotes")
    print("-" * 76)

    print(f"\nTop {min(args.top, len(sorted_unclassified))} Unclassified Emotes (Prioritized by Chat Occurrence Frequency):")
    print(f"{'Rank':<5} {'Emote Name':<20} {'Source':<10} {'Chat Frequency':<15} {'Status'}")
    print("-" * 76)

    for i, name in enumerate(sorted_unclassified[:args.top], 1):
        src = cached_emotes.get(name, {}).get("source", "unknown")
        freq = freq_counts.get(name, 0)
        status = "Needs Human Review" if freq > 0 else "Low Frequency / Pending"
        print(f"{i:<5} {name:<20} {src:<10} {freq:<15} {status}")

    print("-" * 76)
    print("To label an emote, add an entry to config/emote_context.json under:")
    print('  "EMOTE_NAME": { "category": "playful/laughing" | "celebratory" | "sarcasm-marker" | "hostile/mocking" }')
    print("=" * 76 + "\n")


if __name__ == "__main__":
    main()
