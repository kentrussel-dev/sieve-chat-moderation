"""
Evaluation metrics computation module for Sieve moderation benchmarking.
Calculates statistical performance, confusion matrix, latency distributions, and cost models.
"""

from typing import Dict, List, Tuple
import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score


def compute_classification_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
    y_t = np.array(y_true)
    y_p = np.array(y_pred)

    prec = float(precision_score(y_t, y_p, zero_division=0))
    rec = float(recall_score(y_t, y_p, zero_division=0))
    f1 = float(f1_score(y_t, y_p, zero_division=0))
    acc = float(np.mean(y_t == y_p))

    tn, fp, fn, tp = confusion_matrix(y_t, y_p, labels=[0, 1]).ravel()

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def compute_latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    if not latencies_ms:
        return {"avg": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

    arr = np.sort(np.array(latencies_ms))
    return {
        "avg": round(float(np.mean(arr)), 2),
        "p50": round(float(np.percentile(arr, 50)), 2),
        "p90": round(float(np.percentile(arr, 90)), 2),
        "p95": round(float(np.percentile(arr, 95)), 2),
        "p99": round(float(np.percentile(arr, 99)), 2),
    }


def compute_projected_cost(
    volume_items: int,
    tier1_inference_cost_per_million: float,
    llm_cost_per_million: float,
    escalation_rate_pct: float
) -> Dict[str, float]:
    """
    Computes projected economic cost for moderating a given volume of content.
    Assumptions:
    - Tier 1 runs on self-hosted compute / CPU instance (~$0.50 per 1M items amortized)
    - LLM API call costs ~$15.00 per 1M items (~150 tokens/request @ $0.075/1M input + $0.30/1M output tokens)
    """
    vol_millions = volume_items / 1_000_000.0
    tier1_cost = vol_millions * tier1_inference_cost_per_million
    llm_escalated_items = volume_items * (escalation_rate_pct / 100.0)
    llm_cost = (llm_escalated_items / 1_000_000.0) * llm_cost_per_million

    total_cost = tier1_cost + llm_cost
    effective_cost_per_million = (total_cost / vol_millions) if vol_millions > 0 else 0.0

    return {
        "tier1_cost_usd": round(tier1_cost, 2),
        "llm_cost_usd": round(llm_cost, 2),
        "total_cost_usd": round(total_cost, 2),
        "cost_per_million_usd": round(effective_cost_per_million, 2)
    }
