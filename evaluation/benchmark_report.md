# Sieve Benchmark & Evaluation Report

**Evaluation Dataset Size**: 1500 items  
**Calibrated Thresholds**: $\tau_{\text{low}} = 0.20$, $\tau_{\text{high}} = 0.80$  

---

## 1. Tri-Configuration Comparison

| Metric | Tier 1 Only (Local) | LLM Only (Baseline Ceiling) | Sieve Pipeline (Tiered) | Delta (Sieve vs LLM) |
| :--- | :--- | :--- | :--- | :--- |
| **Accuracy** | 96.60% | 98.60% | **99.40%** | +0.80% |
| **Precision** | 96.45% | 98.60% | **99.48%** | +0.88% |
| **Recall** | 94.61% | 97.74% | **98.96%** | +1.22% |
| **F1 Score** | 0.9552 | 0.9817 | **0.9922** | +0.0105 |
| **Latency P50** | 0.88 ms | 219.98 ms | **0.95 ms** | **99.6% faster** |
| **Latency P95** | 1.77 ms | 256.52 ms | **228.65 ms** | -27.87 ms |
| **Escalation Rate** | 0.0% | 100.0% | **11.5%** | - |
| **Cost / 1M msgs** | $0.50 | $15.50 | **$2.22** | **85.7% cost reduction** |

---

## 2. Category-Specific Breakdown

| Content Category | Count | Sieve Escalation % | Tier 1 Accuracy | Sieve Pipeline Accuracy | LLM Only Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `clean` | 825 | 0.0% | 100.0% | **100.0%** | 99.4% |
| `false_alarm_colloquial` | 64 | 79.7% | 84.4% | **95.3%** | 96.9% |
| `sarcasm` | 66 | 100.0% | 87.9% | **97.0%** | 95.5% |
| `sharp_disagreement` | 36 | 27.8% | 72.2% | **100.0%** | 97.2% |
| `subtle_hostility` | 59 | 76.3% | 61.0% | **93.2%** | 89.8% |
| `toxic_blatant` | 450 | 0.0% | 100.0% | **100.0%** | 99.1% |

---

## 3. Qualitative Error Analysis

The table below catalogs representative failure modes observed during test execution:

| Text Snippet | True Label | Sieve Verdict | Tier Resolved | Category | Failure Analysis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Honestly, We executed that deployment flawlessly and termina... | Clean | Toxic | Tier 2 | `false_alarm_colloquial` | Tier 2 LLM Misclassification |
| Look, Another masterclass in missing the point entirely. Tru... | Toxic | Clean | Tier 2 | `sarcasm` | Tier 2 LLM Misclassification |
| We all know why individuals with your background struggle wi... | Toxic | Clean | Tier 2 | `subtle_hostility` | Tier 2 LLM Misclassification |
| Well, The defense completely suffocated the opposing offense... | Clean | Toxic | Tier 2 | `false_alarm_colloquial` | Tier 2 LLM Misclassification |
| Look, We all know why individuals with your background strug... | Toxic | Clean | Tier 2 | `subtle_hostility` | Tier 2 LLM Misclassification |
| Look, It must be nice living in such blissful ignorance of r... | Toxic | Clean | Tier 2 | `subtle_hostility` | Tier 2 LLM Misclassification |
| Well, Bro you absolutely murdered that guitar solo, unreal p... | Clean | Toxic | Tier 2 | `false_alarm_colloquial` | Tier 2 LLM Misclassification |
| Look, Wow, you really outdid yourself finding new ways to fa... | Toxic | Clean | Tier 2 | `sarcasm` | Tier 2 LLM Misclassification |
| You definitely look like the kind of person who would believ... | Toxic | Clean | Tier 2 | `subtle_hostility` | Tier 2 LLM Misclassification |
