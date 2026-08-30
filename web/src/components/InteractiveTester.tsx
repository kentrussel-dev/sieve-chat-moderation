import React, { useState } from 'react';
import { Send, Zap, Sparkles, Tag } from 'lucide-react';
import { ModerationEvent } from '../types';

interface InteractiveTesterProps {
  tauLow: number;
  tauHigh: number;
  onEventProcessed: (event: ModerationEvent) => void;
}

const PRESETS = [
  {
    label: 'L1: Clean',
    dotColor: 'bg-emerald-400',
    text: 'Thank you for sharing this insightful tutorial on Kafka streams.',
  },
  {
    label: 'L2: Gaming Slang',
    dotColor: 'bg-sky-400',
    text: 'Bro you absolutely murdered that play, what the fuck was that clutch KEKW',
  },
  {
    label: 'L3: Sarcasm',
    dotColor: 'bg-amber-400',
    text: 'Another masterclass in missing the point entirely. Truly inspired.',
  },
  {
    label: 'L4: Subtle Hostility',
    dotColor: 'bg-orange-400',
    text: 'We all know why individuals with your background struggle with basic logic.',
  },
  {
    label: 'L5: Toxic Flaming',
    dotColor: 'bg-rose-400',
    text: 'Shut up you moron, nobody asked for your garbage opinion.',
  },
  {
    label: 'L6: Severe Slur',
    dotColor: 'bg-purple-400',
    text: 'kill yourself you worthless loser',
  },
];

const levelBadgeMap: Record<number, {
  label: string;
  dotColor: string;
  badgeText: string;
}> = {
  1: { label: 'L1 Clean', dotColor: 'bg-emerald-400', badgeText: 'text-emerald-400' },
  2: { label: 'L2 Slang', dotColor: 'bg-sky-400', badgeText: 'text-sky-400' },
  3: { label: 'L3 Sarcasm', dotColor: 'bg-amber-400', badgeText: 'text-amber-400' },
  4: { label: 'L4 Hostile', dotColor: 'bg-orange-400', badgeText: 'text-orange-400' },
  5: { label: 'L5 Toxic', dotColor: 'bg-rose-400', badgeText: 'text-rose-400' },
  6: { label: 'L6 Severe', dotColor: 'bg-purple-400', badgeText: 'text-purple-400' },
};

const getEffectiveLevel = (e: ModerationEvent): number => {
  if (typeof e.toxicity_level === 'number' && e.toxicity_level >= 1 && e.toxicity_level <= 6) {
    return e.toxicity_level;
  }
  const score = e.toxicity_score ?? e.tier1_score ?? 0;
  if (score <= 0.15) return 1;
  if (score <= 0.35) return 2;
  if (score <= 0.55) return 3;
  if (score <= 0.70) return 4;
  if (score <= 0.88) return 5;
  return 6;
};

export const InteractiveTester: React.FC<InteractiveTesterProps> = ({
  tauLow,
  tauHigh,
  onEventProcessed,
}) => {
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [burstLoading, setBurstLoading] = useState(false);
  const [lastResult, setLastResult] = useState<ModerationEvent | null>(null);

  const handleModerate = async (textToModerate?: string) => {
    const text = textToModerate || inputText;
    if (!text.trim()) return;

    setLoading(true);
    try {
      const resp = await fetch('/api/moderate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          tau_low: tauLow,
          tau_high: tauHigh,
        }),
      });

      if (resp.ok) {
        const result: ModerationEvent = await resp.json();
        setLastResult(result);
        onEventProcessed(result);
      }
    } catch (err) {
      console.error('Moderation request failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBurst = async (burstType: string, count: number = 50) => {
    setBurstLoading(true);
    try {
      const resp = await fetch('/api/burst', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          count,
          burst_type: burstType,
          tau_low: tauLow,
          tau_high: tauHigh,
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        if (data.items && data.items.length > 0) {
          data.items.forEach((item: ModerationEvent) => onEventProcessed(item));
          setLastResult(data.items[0]);
        }
      }
    } catch (err) {
      console.error('Burst request failed:', err);
    } finally {
      setBurstLoading(false);
    }
  };

  const lvl = lastResult ? getEffectiveLevel(lastResult) : 1;
  const badge = levelBadgeMap[lvl] || levelBadgeMap[1];

  return (
    <div className="bg-[#18181b] rounded-lg p-6 border border-[#2f2f35] font-sans shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            Routing Sandbox
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Test any payload against Mesh 1 scoring, emote suppression, and Mesh 2 LLM reasoning
          </p>
        </div>
        <div className="flex items-center gap-1.5 bg-[#9146ff]/15 border border-[#9146ff]/30 px-2.5 py-1 rounded">
          <Zap className="h-3.5 w-3.5 text-[#bf94ff]" />
          <span className="text-xs font-bold text-[#bf94ff]">Interactive Lab</span>
        </div>
      </div>

      {/* Preset Chips */}
      <div className="mb-3.5 flex flex-wrap gap-2 text-xs">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            onClick={() => {
              setInputText(p.text);
              handleModerate(p.text);
            }}
            className="flex items-center gap-1.5 bg-[#0e0e10] border border-[#2f2f35] px-3 py-1.5 rounded-lg text-slate-300 hover:border-[#9146ff] hover:text-white transition-colors text-xs font-medium"
          >
            <span className={`h-1.5 w-1.5 rounded-full ${p.dotColor}`} />
            <span>{p.label}</span>
          </button>
        ))}
      </div>

      {/* Input Field & Submit Button */}
      <div className="flex gap-2.5">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleModerate()}
          placeholder="Type message to test tiered classification, category detection & LLM escalation..."
          className="flex-1 rounded-lg bg-[#0e0e10] border border-[#2f2f35] px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:border-[#9146ff] focus:outline-none transition-colors"
        />
        <button
          onClick={() => handleModerate()}
          disabled={loading || !inputText.trim()}
          className="flex items-center gap-1.5 rounded-lg bg-[#9146ff] hover:bg-[#772ce8] px-5 py-2.5 text-xs font-bold text-white disabled:opacity-50 transition-colors shadow-lg shadow-[#9146ff]/20"
        >
          <Send className="h-3.5 w-3.5" />
          <span>{loading ? 'Evaluating...' : 'Test'}</span>
        </button>
      </div>

      {/* Evaluation Trace with Linguistic Category Tag & Reasoning */}
      {lastResult && (
        <div className="mt-4 bg-[#0e0e10] rounded-lg border border-[#2f2f35] p-4 font-mono text-xs space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#2f2f35] pb-2.5">
            <div className="flex flex-wrap items-center gap-2">
              {/* Level Badge with dot */}
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#18181b] border border-[#2f2f35] text-[10px] font-mono font-bold">
                <span className={`h-1.5 w-1.5 rounded-full ${badge.dotColor}`} />
                <span className={badge.badgeText}>{badge.label}</span>
                <span className="text-slate-400 ml-0.5">p={(lastResult.toxicity_score ?? lastResult.tier1_score ?? 0).toFixed(2)}</span>
              </span>

              {/* Tier */}
              {lastResult.resolved_by_tier === 'TIER_2' ? (
                <span className="inline-flex items-center gap-1 text-[#bf94ff] bg-[#9146ff]/15 border border-[#9146ff]/30 px-2 py-0.5 rounded text-[10px] font-bold">
                  <Sparkles className="h-3 w-3" />
                  Mesh 2 (LLM Escalated)
                </span>
              ) : (
                <span className="text-slate-400 text-[10px] bg-[#18181b] px-2 py-0.5 rounded border border-[#2f2f35]">
                  Mesh 1 (Local Cleared)
                </span>
              )}

              {/* Category */}
              {lastResult.category && (
                <span className="flex items-center gap-1 text-[10px] text-slate-300 bg-[#18181b] border border-[#2f2f35] px-2 py-0.5 rounded">
                  <Tag className="h-2.5 w-2.5 text-slate-400" />
                  {lastResult.category}
                </span>
              )}
            </div>

            <div className="flex items-center gap-3">
              <span className="text-slate-400 text-[11px]">
                Latency: <strong className="text-white font-mono">{lastResult.total_latency_ms.toFixed(1)}ms</strong>
              </span>
              {lastResult.status === 'PASSED' ? (
                <span className="text-emerald-400 font-bold bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px]">
                  PASSED
                </span>
              ) : (
                <span className="text-rose-400 font-bold bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 rounded text-[10px]">
                  FLAGGED
                </span>
              )}
            </div>
          </div>

          <div className="text-slate-200 font-sans text-xs leading-relaxed">
            "{lastResult.text}"
          </div>

          {lastResult.reasoning && (
            <div className="pt-2 border-t border-[#1f1f23] text-[11px] text-slate-400 font-sans leading-relaxed">
              <strong className="text-[#bf94ff] font-mono">Reasoning:</strong> {lastResult.reasoning}
            </div>
          )}
        </div>
      )}

      {/* Traffic Burst Injection Controls */}
      <div className="mt-4 pt-3.5 border-t border-[#2f2f35] flex items-center justify-between flex-wrap gap-2">
        <span className="text-xs text-slate-400 font-medium">Inject Batch Traffic:</span>
        <div className="flex gap-2">
          <button
            onClick={() => handleBurst('mixed', 50)}
            disabled={burstLoading}
            className="bg-[#0e0e10] border border-[#2f2f35] px-3 py-1.5 rounded-lg text-slate-300 hover:text-white disabled:opacity-40 transition-colors text-xs font-medium"
          >
            +50 Mixed
          </button>
          <button
            onClick={() => handleBurst('nuanced_sarcasm', 50)}
            disabled={burstLoading}
            className="bg-[#0e0e10] border border-amber-500/30 px-3 py-1.5 rounded-lg text-amber-400 hover:text-amber-300 disabled:opacity-40 transition-colors text-xs font-medium"
          >
            +50 Sarcasm
          </button>
          <button
            onClick={() => handleBurst('toxic_spike', 50)}
            disabled={burstLoading}
            className="bg-[#0e0e10] border border-rose-500/30 px-3 py-1.5 rounded-lg text-rose-400 hover:text-rose-300 disabled:opacity-40 transition-colors text-xs font-medium"
          >
            +50 Toxic
          </button>
        </div>
      </div>
    </div>
  );
};
