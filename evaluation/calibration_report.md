# Sieve Mesh 1 Toxicity Band Calibration Report

- **Total Evaluated Samples:** 992
- **Overall Band Separation Accuracy:** 27.92%

## 6-Level Band Separation Breakdown

| Level | Label | Configured Score Band | Sample Count | Mean Score ± Std | Median (P50) | Band Acc |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Level 1** | Clean | `[0.00, 0.15]` | 686 | `0.274 ± 0.166` | **`0.258`** | **25.2%** |
| **Level 2** | Gaming Slang (False Alarm) | `[0.16, 0.35]` | 32 | `0.289 ± 0.122` | **`0.290`** | **53.1%** |
| **Level 3** | Ambiguous / Sarcastic | `[0.36, 0.55]` | 44 | `0.698 ± 0.295` | **`0.770`** | **9.1%** |
| **Level 4** | Subtle Hostility | `[0.56, 0.70]` | 156 | `0.447 ± 0.191` | **`0.447`** | **19.9%** |
| **Level 5** | Toxic | `[0.71, 0.88]` | 69 | `0.817 ± 0.190` | **`0.887`** | **24.6%** |
| **Level 6** | Severe/Extreme | `[0.89, 1.00]` | 5 | `0.878 ± 0.092` | **`0.833`** | **40.0%** |

## 6x6 Band Confusion Matrix

| Human \ Pred | L1 (Clean) | L2 (Slang) | L3 (Ambiguous) | L4 (Hostility) | L5 (Toxic) | L6 (Severe) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Level 1** | 206 | 316 | 120 | 33 | 8 | 3 |
| **Level 2** | 6 | 17 | 8 | 1 | 0 | 0 |
| **Level 3** | 1 | 9 | 4 | 5 | 6 | 19 |
| **Level 4** | 7 | 55 | 47 | 31 | 16 | 0 |
| **Level 5** | 0 | 2 | 8 | 6 | 17 | 36 |
| **Level 6** | 0 | 0 | 0 | 0 | 3 | 2 |
