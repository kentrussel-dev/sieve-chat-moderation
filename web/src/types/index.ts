export type VerdictStatus = 'PASSED' | 'FLAGGED';
export type TierLevel = 'TIER_0' | 'TIER_1' | 'TIER_2';

export interface ToxicityBandConfig {
  level: number;
  min_score: number;
  max_score: number;
  label: string;
  description: string;
}

export interface EmoteMatch {
  name: string;
  category: string;
  source: string;
}

export interface ModerationEvent {
  id: string;
  text: string;
  username?: string;
  channel?: string;
  source?: string;
  tier1_score: number;
  toxicity_score?: number;
  toxicity_level?: number;
  level_label?: string;
  flagged_for_review?: boolean;
  emotes?: EmoteMatch[];
  streamer_caption_context?: string | null;
  caption_context_available?: boolean;
  status: VerdictStatus;
  resolved_by_tier: TierLevel;
  category?: string;
  tier1_latency_ms?: number;
  tier2_latency_ms?: number;
  total_latency_ms: number;
  reasoning?: string;
  timestamp: string;
}

export interface ConfidenceBucket {
  bucket: string;
  count: number;
  tier: 'passed' | 'escalated' | 'flagged';
  level?: number;
  label?: string;
}

export interface TelemetryState {
  items_raw_total: number;
  items_passed_total: number;
  items_flagged_total: number;
  items_escalated_total: number;
  items_review_queue_total?: number;
  emotes_detected_total?: number;
  rate_raw_per_sec: number;
  rate_passed_per_sec: number;
  rate_flagged_per_sec: number;
  rate_escalated_per_sec: number;
  recent_events: ModerationEvent[];
  confidence_distribution: ConfidenceBucket[];
}

export interface ConfigMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  tp: number;
  fp: number;
  tn: number;
  fn: number;
}

export interface LatencyStats {
  avg: number;
  p50: number;
  p90: number;
  p95: number;
  p99: number;
}

export interface PipelineBenchmarkMetrics {
  metrics: ConfigMetrics;
  latency_ms: LatencyStats;
  cost_per_1m_usd: number;
  cost_per_million?: number;
  escalation_rate_pct: number;
}

export interface BenchmarkReport {
  num_test_samples: number;
  tier1_only?: PipelineBenchmarkMetrics;
  llm_only?: PipelineBenchmarkMetrics;
  sieve_pipeline?: PipelineBenchmarkMetrics;
  precision?: number;
  recall?: number;
  f1_score?: number;
  p50_latency_ms?: number;
  p99_latency_ms?: number;
  estimated_cost_per_million?: number;
  dataset?: string;
}
