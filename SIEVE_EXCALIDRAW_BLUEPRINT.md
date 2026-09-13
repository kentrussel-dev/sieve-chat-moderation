# Sieve Architecture: Excalidraw Blueprint & Interview Script

Use this reference to draw **Sieve** from scratch in Excalidraw and explain it to an interviewer.

---

## The 5-Zone Flow (Left to Right)

```
[ZONE 1: INGESTION]          [ZONE 2: TIER 1 FAST PATH]    [ZONE 3: DECISION BANDS]       [ZONE 4: TIER 2 LLM]         [ZONE 5: OUTPUTS]

+--------------------+       +--------------------+        +--------------------+        +--------------------+        +-----------------+
| Twitch / Game Logs |------>| Go Tier 1 Router   |------->| Calibrated Bands   |------->| Go Tier 2 Worker   |------->| content.passed  |
| 7TV Emote Resolver |       | (Worker Pool 8x)   |        | tau_low = 0.20     |        | (Backoff + Jitter) |        | (Clean Stream)  |
+--------------------+       +--------------------+        | tau_high = 0.80    |        +--------------------+        +-----------------+
          |                            |                   +--------------------+                  |                            ^
          v                            v                             |                             v                            |
+--------------------+       +--------------------+                  |                   +--------------------+                 |
| Go Producer        |       | Local ML (FastAPI) |                  +------------------>| Frontier LLM API   |-----------------+
| Kafka: content.raw |       | < 1ms Inference    |                  |  (11.5% traffic)  | (Nuance / Sarcasm) |                 |
+--------------------+       +--------------------+                  |                   +--------------------+                 v
                                                                     |                                                 +-----------------+
                                                                     +------------------------------------------------>| content.flagged |
                                                                                                                       | (Violations)    |
                                                                                                                       +-----------------+
```

---

## Zone-by-Zone Breakdown: What to Draw & Say

### Zone 1: Ingestion & Raw Buffer
- **What to draw**:
  - `Twitch Chat / Gaming Logs / 7TV Emotes`
  - `Go Producer Service`
  - `Kafka Topic: content.raw` (KRaft partitioned)
- **What to say**:
  > *"Traffic arrives from live streams or in-game chat. Our Go producer assigns a UUID and timestamp, wraps it into a standardized `ContentEvent` schema, and writes it directly to the partitioned Kafka topic `content.raw`."*

---

### Zone 2: Tier 1 Fast-Path
- **What to draw**:
  - `Go Tier 1 Router (8x Worker Pool)`
  - `Local ML Classifier (FastAPI / Scikit-Learn / ONNX)`
- **What to say**:
  > *"Tier 1 is an in-cluster Go consumer running an 8-worker pool. It evaluates messages against a local, calibrated ML classifier over pooled HTTP connections. Inference takes under 1 millisecond and returns a calibrated toxicity probability score $p \in [0.0, 1.0]$ with zero per-token cloud API cost."*

---

### Zone 3: Calibrated Decision Bands (The Core Innovation)
- **What to draw**:
  - A 3-tier bracket:
    1. **$p < 0.20$ ($\tau_{\text{low}}$)**: 88.5% of traffic $\rightarrow$ Direct to `content.passed` (<1ms).
    2. **$0.20 \le p \le 0.80$**: 11.5% of traffic $\rightarrow$ Route to `content.escalated`.
    3. **$p > 0.80$ ($\tau_{\text{high}}$)**: High-severity violation $\rightarrow$ Direct to `content.flagged` (<1ms).
- **What to say**:
  > *"Instead of using a naive binary threshold like $p > 0.5$, we calibrated an empirical uncertainty band between $0.20$ and $0.80$. 
  > 88.5% of messages are high-confidence clean or blatant toxicity and are finalized immediately in sub-millisecond time. Only the 11.5% ambiguous cases—such as subtle sarcasm or gaming colloquialisms—are escalated."*

---

### Zone 4: Tier 2 LLM Escalation
- **What to draw**:
  - `Kafka Topic: content.escalated` (Shock Absorber buffer)
  - `Go Tier 2 Worker`
  - `Frontier LLM API` (External)
- **What to say**:
  > *"The `content.escalated` Kafka topic acts as a shock absorber. The Tier 2 Go consumer pulls ambiguous messages and queries a frontier LLM using structured JSON schemas. We implement exponential backoff with full jitter to gracefully handle HTTP 429 rate limits without ever degrading the Tier 1 fast-path."*

---

### Zone 5: Output Streams & Observability
- **What to draw**:
  - `content.passed` (Sent to live game/chat UI)
  - `content.flagged` (Sent to moderation review / shadowban)
  - `React Live Stream Studio` (WebSockets for real-time telemetry & threshold tuning)
- **What to say**:
  > *"Final verdicts are published to `content.passed` or `content.flagged`. A React studio connects via WebSockets to monitor queue lag, real-time toxicity histograms, and allows live threshold tuning."*

---

## ⚡ The 3 Numbers You Must Memorize for the Interview:
1. **99.40% Accuracy / 0.9922 F1** (Matches or outperforms pure LLM).
2. **0.81 ms P50 Latency** (99.6% reduction from pure LLM's 220ms).
3. **85.7% Cost Reduction** (Only 11.5% of traffic escalated to paid LLM API).
