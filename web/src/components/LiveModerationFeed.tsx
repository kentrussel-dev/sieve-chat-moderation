import React from 'react';
import { ModerationEvent } from '../types';
import { renderChatMessageWithEmotes, getTwitchUserColor } from '../utils/emoteParser';

interface LiveModerationFeedProps {
  events: ModerationEvent[];
}

const levelBadgeMap: Record<number, {
  label: string;
  dotColor: string;
  badgeText: string;
}> = {
  1: {
    label: 'L1 Clean',
    dotColor: 'bg-emerald-400',
    badgeText: 'text-emerald-400/90',
  },
  2: {
    label: 'L2 Slang',
    dotColor: 'bg-sky-400',
    badgeText: 'text-sky-400/90',
  },
  3: {
    label: 'L3 Sarcasm',
    dotColor: 'bg-amber-400',
    badgeText: 'text-amber-400/90',
  },
  4: {
    label: 'L4 Hostile',
    dotColor: 'bg-orange-400',
    badgeText: 'text-orange-400/90',
  },
  5: {
    label: 'L5 Toxic',
    dotColor: 'bg-rose-400',
    badgeText: 'text-rose-400/90',
  },
  6: {
    label: 'L6 Severe',
    dotColor: 'bg-purple-400',
    badgeText: 'text-purple-400/90',
  }
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

export const LiveModerationFeed: React.FC<LiveModerationFeedProps> = ({ events }) => {
  return (
    <div className="bg-[#18181b] rounded-lg p-6 border border-[#2f2f35] h-full font-sans shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            Live Stream Pipeline Activity
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time multi-tiered moderation decisions across incoming chat events
          </p>
        </div>
        <span className="text-xs font-mono bg-[#0e0e10] border border-[#2f2f35] px-2.5 py-1 rounded text-[#bf94ff] font-bold">
          {events.length} captured
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead className="text-slate-400 border-b border-[#2f2f35] pb-3">
            <tr className="text-xs font-bold font-sans uppercase tracking-wider text-slate-400">
              <th className="pb-3 pr-3">Event ID</th>
              <th className="pb-3 pr-3">Message Snippet</th>
              <th className="pb-3 pr-3">Severity & Score</th>
              <th className="pb-3 pr-3">Tier</th>
              <th className="pb-3 pr-3">Latency</th>
              <th className="pb-3 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#2f2f35]/50">
            {events.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-12 text-slate-500 font-mono text-xs">
                  No pipeline activity recorded yet. Connect to a live stream or inject test traffic.
                </td>
              </tr>
            ) : (
              events.slice(0, 10).map((evt) => {
                const lvl = getEffectiveLevel(evt);
                const badge = levelBadgeMap[lvl] || levelBadgeMap[1];
                const isTier2 = evt.resolved_by_tier === 'TIER_2';
                const isPassed = evt.status === 'PASSED';
                const userColor = getTwitchUserColor(evt.username || 'user');
                const scoreValue = (evt.toxicity_score ?? evt.tier1_score ?? 0).toFixed(2);

                return (
                  <tr key={evt.id} className="hover:bg-white/[0.02] transition-colors">
                    {/* Event ID */}
                    <td className="py-2.5 pr-3 text-slate-500 font-mono text-[11px] font-medium whitespace-nowrap">
                      {evt.id}
                    </td>

                    {/* Message Snippet with 7TV Emote Rendering */}
                    <td className="py-2.5 pr-3 font-sans text-xs max-w-[280px] truncate text-slate-200" title={evt.text}>
                      <span style={{ color: userColor }} className="font-bold mr-1.5 text-xs">
                        {evt.username || 'user'}:
                      </span>
                      <span>{renderChatMessageWithEmotes(evt.text)}</span>
                    </td>

                    {/* Level Badge with subtle dot */}
                    <td className="py-2.5 pr-3 whitespace-nowrap">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#1f1f23] border border-[#2f2f35] text-[10px] font-mono">
                        <span className={`h-1.5 w-1.5 rounded-full ${badge.dotColor}`} />
                        <span className={badge.badgeText}>{badge.label}</span>
                        <span className="text-slate-400 font-bold ml-0.5">p={scoreValue}</span>
                      </span>
                    </td>

                    {/* Tier */}
                    <td className="py-2.5 pr-3 whitespace-nowrap">
                      {isTier2 ? (
                        <span className="text-[#bf94ff] text-[10px] font-mono font-medium">
                          Mesh 2 LLM
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[10px] font-mono">
                          Mesh 1 Local
                        </span>
                      )}
                    </td>

                    {/* Latency */}
                    <td className="py-2.5 pr-3 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                      {evt.total_latency_ms.toFixed(1)}ms
                    </td>

                    {/* Status */}
                    <td className="py-2.5 text-right whitespace-nowrap">
                      {isPassed ? (
                        <span className="text-emerald-400/90 font-mono text-[10px] font-bold">
                          PASSED
                        </span>
                      ) : (
                        <span className="text-rose-400/90 font-mono text-[10px] font-bold">
                          FLAGGED
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
