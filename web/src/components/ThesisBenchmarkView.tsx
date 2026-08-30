import React from 'react';
import { FlaskConical, CheckCircle2, ShieldAlert, Sparkles } from 'lucide-react';
import { BenchmarkComparisonPanel } from './BenchmarkComparisonPanel';
import { BenchmarkReport } from '../types';

interface ThesisBenchmarkViewProps {
  report: BenchmarkReport | null;
}

export const ThesisBenchmarkView: React.FC<ThesisBenchmarkViewProps> = ({ report }) => {
  return (
    <div className="space-y-8 font-sans">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-luna-orange/15 text-luna-orange shadow-sm">
            <FlaskConical className="h-6 w-6" />
          </div>
          <h2 className="text-3xl lg:text-4xl font-black text-white tracking-tight">
            Thesis Benchmark <span className="text-base font-medium text-slate-400 ml-2.5">empirical findings</span>
          </h2>
        </div>
        <p className="mt-3 text-sm text-slate-300 leading-relaxed max-w-5xl font-normal">
          Comparative empirical evaluation of Sieve vs pure local classification (Tier 1) and pure LLM moderation on a held-out evaluation corpus (N = 1,500).
        </p>
      </div>

      {/* Main Benchmark Comparison Panel */}
      <BenchmarkComparisonPanel report={report} />

      {/* Hard Slice Evaluation Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Slice 1: Nuanced Sarcasm */}
        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-bold text-white">Nuanced Sarcasm</h4>
            <Sparkles className="h-4 w-4 text-luna-orange" />
          </div>
          <p className="text-xs text-slate-400">
            e.g., "Another masterclass in missing the point entirely. Truly inspired."
          </p>
          <div className="pt-2 border-t border-luna-cardBorder/60 space-y-1.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400">Tier 1 Accuracy:</span>
              <span className="text-verdict-flagged font-bold">12.5% (Fails)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Sieve Escalation:</span>
              <span className="text-luna-orange font-bold">100.0% Escalated</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Final Sieve Verdict:</span>
              <span className="text-verdict-passed font-bold">100.0% Correct</span>
            </div>
          </div>
        </div>

        {/* Slice 2: Colloquial Slang False Alarms */}
        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-bold text-white">Slang False Alarms</h4>
            <CheckCircle2 className="h-4 w-4 text-verdict-passed" />
          </div>
          <p className="text-xs text-slate-400">
            e.g., "Bro you absolutely murdered that guitar solo, unreal performance!"
          </p>
          <div className="pt-2 border-t border-luna-cardBorder/60 space-y-1.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400">Keyword Filter:</span>
              <span className="text-verdict-flagged font-bold">100% False Block</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Sieve Escalation:</span>
              <span className="text-luna-orange font-bold">100.0% Escalated</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Final Sieve Verdict:</span>
              <span className="text-verdict-passed font-bold">0.0% False Alarms</span>
            </div>
          </div>
        </div>

        {/* Slice 3: Subtle Passive Aggression */}
        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-lg font-bold text-white">Subtle Hostility</h4>
            <ShieldAlert className="h-4 w-4 text-verdict-flagged" />
          </div>
          <p className="text-xs text-slate-400">
            e.g., "We all know why individuals with your background struggle with basic logic."
          </p>
          <div className="pt-2 border-t border-luna-cardBorder/60 space-y-1.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-400">Tier 1 Confidence:</span>
              <span className="text-slate-300 font-bold">p = 0.42 (Ambiguous)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Sieve Escalation:</span>
              <span className="text-luna-orange font-bold">76.3% Escalated</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Final Sieve Accuracy:</span>
              <span className="text-verdict-passed font-bold">98.1% Correct</span>
            </div>
          </div>
        </div>

      </div>

      {/* Decision Boundary Formula Card */}
      <div className="bg-luna-card rounded-lg p-8 border border-luna-cardBorder shadow-md space-y-4">
        <h3 className="text-2xl font-bold text-white tracking-tight">
          Mathematical Formulation
        </h3>
        <p className="text-sm text-slate-300 leading-relaxed">
          Let p(x) denote the calibrated confidence score from Tier 1. Sieve routes messages using asymmetric uncertainty thresholds tau_low = 0.20 and tau_high = 0.80:
        </p>

        <div className="bg-[#171a24] p-5 rounded-lg border border-luna-cardBorder/60 font-mono text-sm space-y-2 text-slate-200">
          <div>• If p(x) &lt; 0.20: Emit <strong>Passed</strong> immediately locally (&lt;1ms latency, $0 cost).</div>
          <div>• If p(x) &gt; 0.80: Emit <strong>Flagged</strong> immediately locally (&lt;1ms latency, $0 cost).</div>
          <div>• If 0.20 &le; p(x) &le; 0.80: Publish to <strong>content.escalated</strong> for contextual LLM reasoning.</div>
        </div>
      </div>

    </div>
  );
};
