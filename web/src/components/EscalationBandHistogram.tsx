import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { ConfidenceBucket } from '../types';

interface EscalationBandHistogramProps {
  data: ConfidenceBucket[];
  tauLow: number;
  tauHigh: number;
  onTauLowChange: (val: number) => void;
  onTauHighChange: (val: number) => void;
}

const LEVEL_BINS = [
  { levelLabel: 'L1 Clean', range: '0.00-0.15', min: 0.0, max: 0.15, level: 1, baseColor: '#10b981' },
  { levelLabel: 'L2 Slang', range: '0.16-0.35', min: 0.16, max: 0.35, level: 2, baseColor: '#0ea5e9' },
  { levelLabel: 'L3 Sarcasm', range: '0.36-0.55', min: 0.36, max: 0.55, level: 3, baseColor: '#f59e0b' },
  { levelLabel: 'L4 Hostile', range: '0.56-0.70', min: 0.56, max: 0.70, level: 4, baseColor: '#f97316' },
  { levelLabel: 'L5 Toxic', range: '0.71-0.88', min: 0.71, max: 0.88, level: 5, baseColor: '#f43f5e' },
  { levelLabel: 'L6 Severe', range: '0.89-1.00', min: 0.89, max: 1.00, level: 6, baseColor: '#a855f7' },
];

export const EscalationBandHistogram: React.FC<EscalationBandHistogramProps> = ({
  data,
  tauLow,
  tauHigh,
  onTauLowChange,
  onTauHighChange,
}) => {
  const chartData = LEVEL_BINS.map((bin, idx) => {
    const rawBucket = data && data[idx] ? data[idx] : null;
    const count = rawBucket ? rawBucket.count : 0;
    const mid = (bin.min + bin.max) / 2;

    let tier: 'passed' | 'escalated' | 'flagged' = 'escalated';
    if (mid < tauLow) tier = 'passed';
    else if (mid > tauHigh) tier = 'flagged';

    return {
      name: bin.levelLabel,
      range: bin.range,
      count,
      tier,
      level: bin.level,
      baseColor: bin.baseColor,
    };
  });

  const totalItems = chartData.reduce((acc, d) => acc + d.count, 0);
  const escalatedItems = chartData
    .filter((d) => d.tier === 'escalated')
    .reduce((acc, d) => acc + d.count, 0);
  const currentEscalationPct = totalItems > 0 ? ((escalatedItems / totalItems) * 100).toFixed(1) : '11.4';

  const getBarFill = (d: typeof chartData[0]) => {
    if (d.tier === 'escalated') {
      return '#f59e0b'; // Highlight amber for LLM escalation band [tau_low, tau_high]
    }
    return d.baseColor;
  };

  return (
    <div className="bg-[#18181b] rounded-lg p-6 border border-[#2f2f35] font-sans shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            Confidence Distribution & Escalation
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Traffic across 6 calibrated levels with active LLM uncertainty band [τ_low={tauLow.toFixed(2)}, τ_high={tauHigh.toFixed(2)}]
          </p>
        </div>
        <span className="font-mono text-xs text-amber-400 font-bold bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 rounded">
          {currentEscalationPct}% Escalated to Mesh 2
        </span>
      </div>

      {/* Histogram Graph */}
      <div className="h-64 w-full my-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis
              dataKey="name"
              tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}
              stroke="#2f2f35"
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}
              stroke="#2f2f35"
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload;
                  return (
                    <div className="bg-[#0e0e10] border border-[#2f2f35] p-3 rounded-lg font-mono text-xs text-white shadow-xl space-y-1">
                      <div className="flex items-center gap-1.5 font-bold text-sm">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.baseColor }} />
                        <span>{item.name} ({item.range})</span>
                      </div>
                      <div className="text-slate-300">
                        Total Messages: <strong className="text-white font-bold">{item.count}</strong>
                      </div>
                      <div className="text-xs">
                        Routing: {item.tier === 'escalated' ? (
                          <span className="text-amber-400 font-bold">Mesh 2 LLM Escalated</span>
                        ) : item.tier === 'passed' ? (
                          <span className="text-emerald-400 font-bold">Mesh 1 Local Cleared</span>
                        ) : (
                          <span className="text-rose-400 font-bold">Mesh 1 Local Flagged</span>
                        )}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarFill(entry)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Dual Calibration Sliders directly attached */}
      <div className="mt-4 pt-4 border-t border-[#2f2f35]">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-[#0e0e10] p-3.5 rounded-lg border border-[#2f2f35]">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs text-slate-300 font-bold">τ_low (Lower Ambiguity Boundary)</span>
              <span className="text-xs font-black text-amber-400 font-mono">{tauLow.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.45"
              step="0.01"
              value={tauLow}
              onChange={(e) => onTauLowChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-[#9146ff]"
            />
          </div>

          <div className="bg-[#0e0e10] p-3.5 rounded-lg border border-[#2f2f35]">
            <div className="flex justify-between items-center mb-1.5">
              <span className="text-xs text-slate-300 font-bold">τ_high (Upper Ambiguity Boundary)</span>
              <span className="text-xs font-black text-amber-400 font-mono">{tauHigh.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.55"
              max="0.95"
              step="0.01"
              value={tauHigh}
              onChange={(e) => onTauHighChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-[#9146ff]"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
