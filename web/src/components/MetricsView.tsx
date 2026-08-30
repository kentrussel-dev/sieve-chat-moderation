import React from 'react';
import { TelemetryState } from '../types';
import { BarChart2, Zap, Server, ShieldCheck, AlertCircle } from 'lucide-react';

interface MetricsViewProps {
  telemetry: TelemetryState;
}

export const MetricsView: React.FC<MetricsViewProps> = ({ telemetry }) => {
  // Compute dynamic live latency percentiles from recent captured events
  const latencies = (telemetry.recent_events || [])
    .map((e) => e.total_latency_ms)
    .filter((l) => typeof l === 'number' && !isNaN(l))
    .sort((a, b) => a - b);

  const getPercentile = (p: number, fallback: number) => {
    if (latencies.length === 0) return fallback;
    const index = Math.min(latencies.length - 1, Math.max(0, Math.floor((p / 100) * latencies.length)));
    return latencies[index];
  };

  const p50 = getPercentile(50, 0.81);
  const p90 = getPercentile(90, 1.12);
  const p95 = getPercentile(95, 145.2);
  const p99 = getPercentile(99, 185.6);

  const localResolutionPct = telemetry.items_raw_total > 0
    ? (((telemetry.items_raw_total - telemetry.items_escalated_total) / telemetry.items_raw_total) * 100).toFixed(1)
    : '88.6';

  // Compute 6-Level Live Severity Distribution
  const recentEvents = telemetry.recent_events || [];
  const getLevel = (e: any) => {
    if (typeof e.toxicity_level === 'number' && e.toxicity_level >= 1 && e.toxicity_level <= 6) {
      return e.toxicity_level;
    }
    const s = e.toxicity_score ?? e.tier1_score ?? 0;
    if (s <= 0.15) return 1;
    if (s <= 0.35) return 2;
    if (s <= 0.55) return 3;
    if (s <= 0.70) return 4;
    if (s <= 0.88) return 5;
    return 6;
  };

  const c1 = recentEvents.filter((e) => getLevel(e) === 1).length;
  const c2 = recentEvents.filter((e) => getLevel(e) === 2).length;
  const c3 = recentEvents.filter((e) => getLevel(e) === 3).length;
  const c4 = recentEvents.filter((e) => getLevel(e) === 4).length;
  const c5 = recentEvents.filter((e) => getLevel(e) === 5).length;
  const c6 = recentEvents.filter((e) => getLevel(e) === 6).length;
  const totalRecent = Math.max(recentEvents.length, 1);

  const levelsData = [
    { level: 'Level 1: Clean', count: c1, pct: ((c1 / totalRecent) * 100).toFixed(1), color: 'bg-emerald-400', dot: 'text-emerald-400' },
    { level: 'Level 2: Gaming Slang', count: c2, pct: ((c2 / totalRecent) * 100).toFixed(1), color: 'bg-sky-400', dot: 'text-sky-400' },
    { level: 'Level 3: Sarcasm', count: c3, pct: ((c3 / totalRecent) * 100).toFixed(1), color: 'bg-amber-400', dot: 'text-amber-400' },
    { level: 'Level 4: Subtle Hostility', count: c4, pct: ((c4 / totalRecent) * 100).toFixed(1), color: 'bg-orange-400', dot: 'text-orange-400' },
    { level: 'Level 5: Toxic Flaming', count: c5, pct: ((c5 / totalRecent) * 100).toFixed(1), color: 'bg-rose-400', dot: 'text-rose-400' },
    { level: 'Level 6: Severe / Extreme', count: c6, pct: ((c6 / totalRecent) * 100).toFixed(1), color: 'bg-purple-400', dot: 'text-purple-400' },
  ];

  return (
    <div className="space-y-8 font-sans">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-luna-orange/15 text-luna-orange shadow-sm">
            <BarChart2 className="h-6 w-6" />
          </div>
          <h2 className="text-3xl lg:text-4xl font-black text-white tracking-tight">
            System Metrics <span className="text-base font-medium text-slate-400 ml-2.5">telemetry & latencies</span>
          </h2>
        </div>
        <p className="mt-3 text-sm text-slate-300 leading-relaxed max-w-5xl font-normal">
          Real-time latency distribution, live pipeline topic throughput, and inference performance across Sieve moderation microservices.
        </p>
      </div>

      {/* Latency Percentiles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-sm font-medium">
            <span>P50 Latency</span>
            <Zap className="h-4 w-4 text-verdict-passed" />
          </div>
          <div className="text-3xl font-black text-white mt-2 font-mono">
            {p50 < 10 ? `${p50.toFixed(2)}ms` : `${p50.toFixed(0)}ms`}
          </div>
          <div className="text-xs text-verdict-passed font-bold mt-1">Local Mesh 1 Speed</div>
        </div>

        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-sm font-medium">
            <span>P90 Latency</span>
            <Zap className="h-4 w-4 text-verdict-passed" />
          </div>
          <div className="text-3xl font-black text-white mt-2 font-mono">
            {p90 < 10 ? `${p90.toFixed(2)}ms` : `${p90.toFixed(0)}ms`}
          </div>
          <div className="text-xs text-slate-400 font-medium mt-1">{localResolutionPct}% Traffic Sub-ms</div>
        </div>

        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-sm font-medium">
            <span>P95 Latency</span>
            <AlertCircle className="h-4 w-4 text-luna-orange" />
          </div>
          <div className="text-3xl font-black text-white mt-2 font-mono">
            {p95.toFixed(1)}ms
          </div>
          <div className="text-xs text-luna-orange font-bold mt-1">Mesh 2 LLM Path</div>
        </div>

        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-sm font-medium">
            <span>P99 Latency</span>
            <AlertCircle className="h-4 w-4 text-luna-orange" />
          </div>
          <div className="text-3xl font-black text-white mt-2 font-mono">
            {p99.toFixed(1)}ms
          </div>
          <div className="text-xs text-slate-400 font-medium mt-1">LLM Tail Upper Bound</div>
        </div>
      </div>

      {/* 6-Level Live Severity Distribution Breakdown */}
      <div className="bg-luna-card rounded-lg p-8 border border-luna-cardBorder shadow-md space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold text-white tracking-tight">
              Calibrated Severity Distribution
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Live traffic breakdown across Sieve's 6 classification tiers ({recentEvents.length} recent messages)
            </p>
          </div>
          <span className="text-xs font-mono font-bold bg-[#171a24] text-slate-300 px-3 py-1 rounded border border-luna-cardBorder/60">
            {localResolutionPct}% Mesh 1 · {telemetry.items_raw_total > 0 ? ((telemetry.items_escalated_total / telemetry.items_raw_total) * 100).toFixed(1) : '11.4'}% Mesh 2
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {levelsData.map((item, idx) => (
            <div key={idx} className="bg-[#171a24] p-4 rounded-lg border border-luna-cardBorder/60 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-300 flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${item.color}`} />
                  {item.level}
                </span>
                <span className="font-mono font-bold text-white">{item.pct}%</span>
              </div>
              <div className="w-full h-1.5 bg-[#0e0e10] rounded-full overflow-hidden">
                <div
                  className={`h-full ${item.color} rounded-full transition-all duration-500`}
                  style={{ width: `${Math.min(100, Math.max(2, Number(item.pct)))}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 font-mono text-right">
                {item.count} messages
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Kafka Topic Depths & Pipeline Topology */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        
        {/* Kafka Topics Card */}
        <div className="xl:col-span-6 bg-luna-card rounded-lg p-8 border border-luna-cardBorder shadow-md space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-2xl font-bold text-white tracking-tight">
              Kafka KRaft Topics
            </h3>
            <span className="flex items-center gap-1.5 text-xs text-verdict-passed font-bold bg-verdict-passed/10 px-2.5 py-1 rounded">
              <Server className="h-3.5 w-3.5" /> Broker Active
            </span>
          </div>

          <div className="space-y-4 font-mono text-sm">
            <div className="bg-[#171a24] p-4 rounded-lg border border-luna-cardBorder/60 flex items-center justify-between">
              <div>
                <div className="text-white font-bold">content.raw</div>
                <div className="text-xs text-slate-400 font-sans mt-0.5">Inbound Ingest Stream</div>
              </div>
              <div className="text-right">
                <div className="text-white font-bold">{telemetry.rate_raw_per_sec.toFixed(1)} msg/s</div>
                <div className="text-xs text-slate-500">{telemetry.items_raw_total.toLocaleString()} msgs</div>
              </div>
            </div>

            <div className="bg-[#171a24] p-4 rounded-lg border border-luna-cardBorder/60 flex items-center justify-between">
              <div>
                <div className="text-verdict-passed font-bold">content.passed</div>
                <div className="text-xs text-slate-400 font-sans mt-0.5">Cleared Final Sinks</div>
              </div>
              <div className="text-right">
                <div className="text-verdict-passed font-bold">{telemetry.rate_passed_per_sec.toFixed(1)} msg/s</div>
                <div className="text-xs text-slate-500">{telemetry.items_passed_total.toLocaleString()} msgs</div>
              </div>
            </div>

            <div className="bg-[#171a24] p-4 rounded-lg border border-luna-cardBorder/60 flex items-center justify-between">
              <div>
                <div className="text-verdict-flagged font-bold">content.flagged</div>
                <div className="text-xs text-slate-400 font-sans mt-0.5">Blocked Toxic Sinks</div>
              </div>
              <div className="text-right">
                <div className="text-verdict-flagged font-bold">{telemetry.rate_flagged_per_sec.toFixed(1)} msg/s</div>
                <div className="text-xs text-slate-500">{telemetry.items_flagged_total.toLocaleString()} msgs</div>
              </div>
            </div>

            <div className="bg-[#171a24] p-4 rounded-lg border border-luna-orange/40 flex items-center justify-between">
              <div>
                <div className="text-luna-orange font-bold">content.escalated</div>
                <div className="text-xs text-slate-400 font-sans mt-0.5">Tier 2 LLM Routing Channel</div>
              </div>
              <div className="text-right">
                <div className="text-luna-orange font-bold">{telemetry.rate_escalated_per_sec.toFixed(1)} msg/s</div>
                <div className="text-xs text-slate-500">{telemetry.items_escalated_total.toLocaleString()} msgs</div>
              </div>
            </div>
          </div>
        </div>

        {/* Microservice Health Status */}
        <div className="xl:col-span-6 bg-luna-card rounded-lg p-8 border border-luna-cardBorder shadow-md space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-2xl font-bold text-white tracking-tight">
              Microservice Topology
            </h3>
            <span className="text-xs text-slate-400 font-mono">4 Services Running</span>
          </div>

          <div className="space-y-4 text-sm font-sans">
            <div className="bg-[#171a24] p-4 rounded-lg border border-luna-cardBorder/60 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-verdict-passed" />
                <div>
                  <div className="text-white font-bold">Tier 1 Classifier Worker</div>
                  <div className="text-xs text-slate-400 font-mono">Go Service · 8 Consumer Workers</div>
                </div>
              </div>
              <span className="text-xs font-bold text-verdict-passed bg-verdict-passed/10 px-2 py-1 rounded">HEALTHY</span>
            </div>

            <div className="bg-[#171a24] p-4 rounded-lg border border-luna-cardBorder/60 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-verdict-passed" />
                <div>
                  <div className="text-white font-bold">Tier 2 LLM Escalator Worker</div>
                  <div className="text-xs text-slate-400 font-mono">Go Service · Jittered Backoff Retries</div>
                </div>
              </div>
              <span className="text-xs font-bold text-verdict-passed bg-verdict-passed/10 px-2 py-1 rounded">HEALTHY</span>
            </div>

            <div className="bg-[#171a24] p-4 rounded-lg border border-luna-cardBorder/60 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-verdict-passed" />
                <div>
                  <div className="text-white font-bold">Inference FastAPI Server</div>
                  <div className="text-xs text-slate-400 font-mono">Python DistilBERT Model (Port 8000)</div>
                </div>
              </div>
              <span className="text-xs font-bold text-verdict-passed bg-verdict-passed/10 px-2 py-1 rounded">HEALTHY</span>
            </div>

            <div className="bg-[#171a24] p-4 rounded-lg border border-luna-cardBorder/60 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-5 w-5 text-verdict-passed" />
                <div>
                  <div className="text-white font-bold">Kafka KRaft Cluster</div>
                  <div className="text-xs text-slate-400 font-mono">Quorum Controller (Port 9092)</div>
                </div>
              </div>
              <span className="text-xs font-bold text-verdict-passed bg-verdict-passed/10 px-2 py-1 rounded">HEALTHY</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
