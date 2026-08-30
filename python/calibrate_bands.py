"""
Calibration & Band Separation Analysis for Sieve Mesh 1 Classifier.
Evaluates continuous calibrated toxicity scores [0.00, 1.00] against human-annotated
6-level ground truth labels to verify band boundaries and separation margins.
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

# Add paths for config and imports
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "config"))

from config.toxicity_bands import (
    ALL_BANDS,
    BAND_BY_LEVEL,
    LEVEL_1_CLEAN,
    LEVEL_2_GAMING_SLANG,
    LEVEL_3_AMBIGUOUS_SARCASTIC,
    LEVEL_4_SUBTLE_HOSTILITY,
    LEVEL_5_TOXIC,
    LEVEL_6_SEVERE_EXTREME,
    map_score_to_band,
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "tier1_model.joblib")


def load_or_create_validation_dataset(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads labeled validation data (columns: utterance/text, human_level (1-6)).
    If no user CSV is supplied, loads a standard validation set mapped from real
    annotated sources (CONDA in-game validation + LMSYS ToxicChat + Sieve edge cases).
    """
    if data_path and os.path.exists(data_path):
        print(f"Loading user validation dataset from {data_path}...")
        if data_path.endswith(".csv"):
            df = pd.read_csv(data_path)
        else:
            with open(data_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            df = pd.DataFrame(raw)

        # Normalize column names
        text_col = "utterance" if "utterance" in df.columns else "text"
        level_col = "human_level" if "human_level" in df.columns else "level"
        if text_col not in df.columns or level_col not in df.columns:
            raise ValueError(f"Dataset must contain text column ('utterance' or 'text') and level column ('human_level' or 'level'). Found: {list(df.columns)}")

        df = df[[text_col, level_col]].rename(columns={text_col: "utterance", level_col: "human_level"})
        df["human_level"] = df["human_level"].astype(int)
        return df

    # Construct validation set from real domain sources
    print("Constructing multi-source calibration validation set from CONDA, LMSYS, and Sieve test sets...")
    records = []

    # 1. Real CONDA Dota 2 validation rows
    conda_valid = os.path.join(os.path.dirname(__file__), "..", "data", "conda", "conda_valid.csv")
    if os.path.exists(conda_valid):
        df_c = pd.read_csv(conda_valid)
        for _, row in df_c.head(600).iterrows():
            utt = str(row.get("utterance", "")).replace("[SEPA]", " ").strip()
            if len(utt) < 2:
                continue
            intent = str(row.get("intentClass", "O")).upper()
            if intent == "O":
                level = 1  # Clean
            elif intent == "A":
                level = 2  # Gaming Slang / Combat banter
            elif intent == "I":
                level = 3  # Sarcasm / Implicit
            elif intent == "E":
                level = 5  # Direct Toxic
            else:
                level = 1
            records.append({"utterance": utt, "human_level": level, "source": "CONDA Dota 2"})

    # 2. LMSYS ToxicChat test rows
    lmsys_test = os.path.join(os.path.dirname(__file__), "..", "evaluation", "lmsys_test_dataset.json")
    if os.path.exists(lmsys_test):
        with open(lmsys_test, "r", encoding="utf-8") as f:
            l_data = json.load(f)
        for item in l_data[:400]:
            text = item.get("text", "")
            is_tox = item.get("label", 0)
            if is_tox == 0:
                level = 1
            else:
                level = 5 if any(w in text.lower() for w in ["idiot", "moron", "trash", "shut up"]) else 4
            records.append({"utterance": text, "human_level": level, "source": "LMSYS ToxicChat"})

    # 3. Severe slur examples for Level 6
    severe_samples = [
        ("kill yourself right now", 6),
        ("go die in a fire you worthless piece of garbage", 6),
        ("you complete idiot moron choke and die", 6),
        ("pathetic loser hope your family dies", 6),
        ("shut up you brainless retard", 6),
    ]
    for text, level in severe_samples:
        records.append({"utterance": text, "human_level": level, "source": "Severe Baseline"})

    df_out = pd.DataFrame(records)
    print(f"Constructed calibration dataset with {len(df_out):,} samples across human levels 1-6.")
    return df_out


def run_calibration_evaluation(model, df: pd.DataFrame) -> Dict:
    """Computes continuous scores, band mapping, and separation statistics."""
    texts = df["utterance"].tolist()
    human_levels = df["human_level"].tolist()

    probs = model.predict_proba(texts)[:, 1]
    df["raw_score"] = probs
    df["predicted_band"] = [map_score_to_band(p).level for p in probs]
    df["predicted_label"] = [map_score_to_band(p).label for p in probs]
    df["is_exact_band_match"] = df["human_level"] == df["predicted_band"]

    level_stats = {}
    for level in range(1, 7):
        subset = df[df["human_level"] == level]
        band = BAND_BY_LEVEL[level]
        if len(subset) == 0:
            continue

        scores = subset["raw_score"].values
        in_band_count = np.sum((scores >= band.min_score) & (scores <= band.max_score))

        level_stats[level] = {
            "label": band.label,
            "configured_band": f"[{band.min_score:.2f}, {band.max_score:.2f}]",
            "count": int(len(subset)),
            "mean_score": round(float(np.mean(scores)), 4),
            "std_score": round(float(np.std(scores)), 4),
            "min_score": round(float(np.min(scores)), 4),
            "p25_score": round(float(np.percentile(scores, 25)), 4),
            "median_p50": round(float(np.median(scores)), 4),
            "p75_score": round(float(np.percentile(scores, 75)), 4),
            "max_score": round(float(np.max(scores)), 4),
            "band_accuracy": round(float(in_band_count / len(subset)), 4)
        }

    # Confusion matrix (6 x 6)
    conf_matrix = np.zeros((6, 6), dtype=int)
    for h, p in zip(human_levels, df["predicted_band"]):
        if 1 <= h <= 6 and 1 <= p <= 6:
            conf_matrix[h - 1, p - 1] += 1

    overall_band_accuracy = float(np.mean(df["is_exact_band_match"]))

    return {
        "total_samples": len(df),
        "overall_band_accuracy": round(overall_band_accuracy, 4),
        "level_statistics": level_stats,
        "confusion_matrix": conf_matrix.tolist()
    }


def print_ascii_distribution(level_stats: Dict[int, Dict]):
    """Renders a clean ASCII distribution chart of score ranges per level."""
    print("\n" + "=" * 78)
    print("      MESH 1 CALIBRATED SCORE DISTRIBUTION BY HUMAN LEVEL (1-6)")
    print("=" * 78)
    print(f"{'Lvl':<4} {'Label':<28} {'Config Band':<14} {'Mean +/- Std':<14} {'Median':<8} {'Band Acc'}")
    print("-" * 78)
    for lvl, s in level_stats.items():
        print(f"L{lvl:<3} {s['label']:<28} {s['configured_band']:<14} {s['mean_score']:.2f} +/- {s['std_score']:.2f}  {s['median_p50']:.2f}     {s['band_accuracy']*100:>5.1f}%")
    print("-" * 78)

    print("\nVisual Score Range Distribution (0.00 -----------> 1.00):")
    for lvl, s in level_stats.items():
        min_p = s["min_score"]
        p25 = s["p25_score"]
        med = s["median_p50"]
        p75 = s["p75_score"]
        max_p = s["max_score"]

        # 40-character bar representation
        bar = list(" " * 40)
        start_idx = int(min_p * 39)
        end_idx = int(max_p * 39)
        q1_idx = int(p25 * 39)
        q3_idx = int(p75 * 39)
        med_idx = int(med * 39)

        for i in range(start_idx, end_idx + 1):
            if 0 <= i < 40:
                bar[i] = "-"
        for i in range(q1_idx, q3_idx + 1):
            if 0 <= i < 40:
                bar[i] = "#"
        if 0 <= med_idx < 40:
            bar[med_idx] = "|"

        bar_str = "".join(bar)
        print(f"L{lvl} [{s['label'][:14]:<14}] |{bar_str}| (p50: {med:.2f})")
    print("   [0.00" + " " * 32 + "1.00]")
    print("=" * 78 + "\n")


def generate_calibration_report(results: Dict, out_dir: str):
    """Writes markdown report and JSON summary."""
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "band_calibration_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    md_path = os.path.join(out_dir, "calibration_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Sieve Mesh 1 Toxicity Band Calibration Report\n\n")
        f.write(f"- **Total Evaluated Samples:** {results['total_samples']:,}\n")
        f.write(f"- **Overall Band Separation Accuracy:** {results['overall_band_accuracy']*100:.2f}%\n\n")
        f.write("## 6-Level Band Separation Breakdown\n\n")
        f.write("| Level | Label | Configured Score Band | Sample Count | Mean Score ± Std | Median (P50) | Band Acc |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for lvl, s in results["level_statistics"].items():
            f.write(f"| **Level {lvl}** | {s['label']} | `{s['configured_band']}` | {s['count']:,} | `{s['mean_score']:.3f} ± {s['std_score']:.3f}` | **`{s['median_p50']:.3f}`** | **{s['band_accuracy']*100:.1f}%** |\n")

        f.write("\n## 6x6 Band Confusion Matrix\n\n")
        f.write("| Human \\ Pred | L1 (Clean) | L2 (Slang) | L3 (Ambiguous) | L4 (Hostility) | L5 (Toxic) | L6 (Severe) |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for i, row in enumerate(results["confusion_matrix"]):
            f.write(f"| **Level {i+1}** | " + " | ".join(str(c) for c in row) + " |\n")

    print(f"Saved Calibration Report to: {md_path}")
    print(f"Saved Calibration JSON to:   {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Calibrate Sieve 6-Level Toxicity Bands")
    parser.add_argument("--data", type=str, default=None, help="Path to labeled validation CSV (columns: utterance, human_level)")
    parser.add_argument("--model", type=str, default=MODEL_PATH, help="Path to trained Tier 1 model joblib")
    parser.add_argument("--out-dir", type=str, default=os.path.join(os.path.dirname(__file__), "..", "evaluation"))
    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"Error: Model not found at {args.model}. Please run train.py first.")
        sys.exit(1)

    model = joblib.load(args.model)
    df = load_or_create_validation_dataset(args.data)
    results = run_calibration_evaluation(model, df)

    print_ascii_distribution(results["level_statistics"])
    generate_calibration_report(results, args.out_dir)


if __name__ == "__main__":
    main()
