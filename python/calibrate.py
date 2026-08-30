"""
Threshold Calibration Engine for Sieve Moderation Pipeline.
Performs empirical parameter sweep over uncertainty thresholds [tau_low, tau_high]
to find optimal operating points on the Pareto frontier (Escalation Rate vs F1 vs Cost).
"""

import argparse
import json
import os
from typing import Dict, List, Tuple

import joblib
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from dataset import generate_evaluation_dataset, load_dataset


def sweep_thresholds(
    model,
    val_texts: List[str],
    val_labels: List[int],
    tau_low_range: np.ndarray,
    tau_high_range: np.ndarray,
    llm_oracle_accuracy: float = 0.98,
    cost_tier1_per_1m: float = 0.50,
    cost_llm_per_1m: float = 15.00
) -> List[Dict]:
    """
    Simulates the tiered pipeline on validation data across combinations of [tau_low, tau_high].
    In Tier 2 escalation, the simulated LLM oracle resolves cases with high accuracy.
    """
    probs = model.predict_proba(val_texts)[:, 1]
    n_samples = len(val_labels)
    results = []

    for tau_low in tau_low_range:
        for tau_high in tau_high_range:
            if tau_low >= tau_high:
                continue

            tier1_resolved = 0
            tier2_escalated = 0
            final_predictions = []

            for i in range(n_samples):
                p = probs[i]
                true_label = val_labels[i]

                if p < tau_low:
                    # High confidence clean -> Tier 1 passes
                    final_predictions.append(0)
                    tier1_resolved += 1
                elif p > tau_high:
                    # High confidence toxic -> Tier 1 flags
                    final_predictions.append(1)
                    tier1_resolved += 1
                else:
                    # Borderline -> Escalated to Tier 2 (LLM oracle)
                    tier2_escalated += 1
                    # Simulate LLM oracle with realistic high accuracy
                    is_correct = np.random.rand() < llm_oracle_accuracy
                    llm_pred = true_label if is_correct else (1 - true_label)
                    final_predictions.append(llm_pred)

            final_preds_arr = np.array(final_predictions)
            val_labels_arr = np.array(val_labels)

            f1 = float(f1_score(val_labels_arr, final_preds_arr, zero_division=0))
            prec = float(precision_score(val_labels_arr, final_preds_arr, zero_division=0))
            rec = float(recall_score(val_labels_arr, final_preds_arr, zero_division=0))
            acc = float(np.mean(final_preds_arr == val_labels_arr))
            
            escalation_rate = (tier2_escalated / n_samples) * 100.0
            
            # Blended cost model per 1M items: Cost_T1 + (Escalation_Rate * Cost_LLM)
            blended_cost_per_1m = cost_tier1_per_1m + (escalation_rate / 100.0) * cost_llm_per_1m

            results.append({
                "tau_low": round(float(tau_low), 2),
                "tau_high": round(float(tau_high), 2),
                "escalation_rate_pct": round(escalation_rate, 2),
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "blended_cost_per_1m_usd": round(blended_cost_per_1m, 2)
            })

    return results


def main():
    parser = argparse.ArgumentParser(description="Calibrate Sieve Confidence Thresholds")
    parser.add_argument("--model-path", type=str, default="./models/tier1_model.joblib")
    parser.add_argument("--data-path", type=str, default="../evaluation/synthetic_dataset.json")
    parser.add_argument("--output-json", type=str, default="../evaluation/calibration_results.json")
    args = parser.parse_args()

    np.random.seed(42)

    full_model_path = os.path.join(os.path.dirname(__file__), args.model_path)
    full_data_path = os.path.join(os.path.dirname(__file__), args.data_path)
    full_out_path = os.path.join(os.path.dirname(__file__), args.output_json)

    if not os.path.exists(full_data_path):
        data = generate_evaluation_dataset(2000)
        os.makedirs(os.path.dirname(full_data_path), exist_ok=True)
        with open(full_data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        with open(full_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    if not os.path.exists(full_model_path):
        print("Trained model not found. Training model first...")
        import train
        model = train.train_fast_calibrated_model(
            [d["text"] for d in data],
            [d["label"] for d in data]
        )
        os.makedirs(os.path.dirname(full_model_path), exist_ok=True)
        joblib.dump(model, full_model_path)
    else:
        model = joblib.load(full_model_path)

    texts = [item["text"] for item in data]
    labels = [item["label"] for item in data]

    _, val_texts, _, val_labels = train_test_split(
        texts, labels, test_size=0.3, random_state=42, stratify=labels
    )

    tau_low_grid = np.arange(0.10, 0.45, 0.05)
    tau_high_grid = np.arange(0.60, 0.95, 0.05)

    print(f"Sweeping {len(tau_low_grid)} x {len(tau_high_grid)} threshold combinations on {len(val_texts)} validation samples...")
    results = sweep_thresholds(model, val_texts, val_labels, tau_low_grid, tau_high_grid)

    # Sort by F1 score descending
    results_sorted = sorted(results, key=lambda x: (x["f1_score"], -x["escalation_rate_pct"]), reverse=True)

    os.makedirs(os.path.dirname(full_out_path), exist_ok=True)
    with open(full_out_path, "w", encoding="utf-8") as f:
        json.dump(results_sorted, f, indent=2)

    print(f"\nCalibration complete. Top 5 Operating Points by F1:")
    print(f"{'tau_low':<10} {'tau_high':<10} {'Escalated %':<14} {'F1 Score':<12} {'Accuracy':<10} {'Cost ($/1M)':<12}")
    print("-" * 68)
    for r in results_sorted[:5]:
        print(f"{r['tau_low']:<10.2f} {r['tau_high']:<10.2f} {r['escalation_rate_pct']:<14.1f} {r['f1_score']:<12.4f} {r['accuracy']:<10.4f} ${r['blended_cost_per_1m_usd']:<11.2f}")

    # Find the knee of the curve: best F1 with escalation rate <= 15%
    budget_constrained = [r for r in results_sorted if r["escalation_rate_pct"] <= 15.0]
    if budget_constrained:
        best_budget = max(budget_constrained, key=lambda x: x["f1_score"])
        print(f"\nRecommended Balanced Operating Point (Escalation <= 15%):")
        print(f"  tau_low = {best_budget['tau_low']:.2f}, tau_high = {best_budget['tau_high']:.2f}")
        print(f"  Escalation Rate: {best_budget['escalation_rate_pct']:.1f}%")
        print(f"  F1 Score:        {best_budget['f1_score']:.4f}")
        print(f"  Cost / 1M msgs:  ${best_budget['blended_cost_per_1m_usd']:.2f}")


if __name__ == "__main__":
    main()
