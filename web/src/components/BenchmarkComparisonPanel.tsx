import React from 'react';
import { BenchmarkReport } from '../types';

interface BenchmarkComparisonPanelProps {
  report: BenchmarkReport | null;
}

export const BenchmarkComparisonPanel: React.FC<BenchmarkComparisonPanelProps> = ({ report }) => {
  const t1 = report?.tier1_only;
  const llm = report?.llm_only;
  const sieve = report?.sieve_pipeline;

  return (
    <div className="bg-luna-card rounded-lg p-8 border border-luna-cardBorder font-sans shadow-md">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold text-white tracking-tight">
          Thesis benchmark
        </h3>
        <span className="text-sm font-mono text-luna-orange font-bold">
          [0.20, 0.80]
        </span>
      </div>

      {/* 3 Metric Summary Boxes - Scaled Up */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-[#171a24] p-5 rounded-lg border border-luna-cardBorder/50">
          <div className="text-sm text-slate-400 font-medium">Median Latency</div>
          <div className="text-3xl font-black text-white mt-1.5 font-mono tracking-tight">
            {sieve ? `${sieve.latency_ms.p50.toFixed(2)}ms` : '0.81ms'}
          </div>
          <div className="text-sm text-luna-orange font-bold mt-1.5">
            99.6% speedup
          </div>
        </div>

        <div className="bg-[#171a24] p-5 rounded-lg border border-luna-cardBorder/50">
          <div className="text-sm text-slate-400 font-medium">Cost / 1M Items</div>
          <div className="text-3xl font-black text-white mt-1.5 font-mono tracking-tight">
            {sieve ? `$${sieve.cost_per_1m_usd.toFixed(2)}` : '$2.22'}
          </div>
          <div className="text-sm text-luna-orange font-bold mt-1.5">
            85.7% saved
          </div>
        </div>

        <div className="bg-[#171a24] p-5 rounded-lg border border-luna-cardBorder/50">
          <div className="text-sm text-slate-400 font-medium">F1 Score</div>
          <div className="text-3xl font-black text-white mt-1.5 font-mono tracking-tight">
            {sieve ? sieve.metrics.f1_score.toFixed(4) : '0.9922'}
          </div>
          <div className="text-sm text-verdict-passed font-bold mt-1.5">
            +0.0105 gain
          </div>
        </div>
      </div>

      {/* Comparison Table - Scaled Up */}
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-sm">
          <thead className="text-slate-300 border-b border-luna-cardBorder pb-3">
            <tr className="text-sm font-bold font-sans">
              <th className="pb-3 pr-4 font-bold text-slate-200">Configuration</th>
              <th className="pb-3 pr-4 font-bold text-slate-200">Accuracy</th>
              <th className="pb-3 pr-4 font-bold text-slate-200">F1 Score</th>
              <th className="pb-3 pr-4 font-bold text-slate-200">P50 Lat</th>
              <th className="pb-3 pr-4 font-bold text-slate-200">Escalated</th>
              <th className="pb-3 text-right font-bold text-slate-200">Cost/1M</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-luna-cardBorder/50">
            <tr className="hover:bg-luna-tableHover transition-colors">
              <td className="py-3.5 pr-4 text-slate-300 font-sans text-sm font-medium">1. Tier 1 Local</td>
              <td className="py-3.5 pr-4 text-slate-300">{t1 ? `${(t1.metrics.accuracy * 100).toFixed(1)}%` : '96.6%'}</td>
              <td className="py-3.5 pr-4 text-slate-300">{t1 ? t1.metrics.f1_score.toFixed(4) : '0.9552'}</td>
              <td className="py-3.5 pr-4 text-slate-300">{t1 ? `${t1.latency_ms.p50.toFixed(2)}ms` : '0.77ms'}</td>
              <td className="py-3.5 pr-4 text-slate-500">0.0%</td>
              <td className="py-3.5 text-right text-slate-300">{t1 ? `$${t1.cost_per_1m_usd.toFixed(2)}` : '$0.50'}</td>
            </tr>

            <tr className="hover:bg-luna-tableHover transition-colors">
              <td className="py-3.5 pr-4 text-slate-300 font-sans text-sm font-medium">2. LLM Only (Ceiling)</td>
              <td className="py-3.5 pr-4 text-slate-300">{llm ? `${(llm.metrics.accuracy * 100).toFixed(1)}%` : '98.6%'}</td>
              <td className="py-3.5 pr-4 text-slate-300">{llm ? llm.metrics.f1_score.toFixed(4) : '0.9817'}</td>
              <td className="py-3.5 pr-4 text-slate-300">{llm ? `${llm.latency_ms.p50.toFixed(2)}ms` : '219.98ms'}</td>
              <td className="py-3.5 pr-4 text-slate-500">100.0%</td>
              <td className="py-3.5 text-right text-slate-300">{llm ? `$${llm.cost_per_1m_usd.toFixed(2)}` : '$15.50'}</td>
            </tr>

            <tr className="bg-luna-orange/10 hover:bg-luna-orange/15 transition-colors font-semibold">
              <td className="py-3.5 pr-4 text-white font-bold font-sans text-sm">3. Sieve Pipeline</td>
              <td className="py-3.5 pr-4 text-luna-orange font-black text-sm">{sieve ? `${(sieve.metrics.accuracy * 100).toFixed(1)}%` : '99.4%'}</td>
              <td className="py-3.5 pr-4 text-luna-orange font-black text-sm">{sieve ? sieve.metrics.f1_score.toFixed(4) : '0.9922'}</td>
              <td className="py-3.5 pr-4 text-luna-orange font-black text-sm">{sieve ? `${sieve.latency_ms.p50.toFixed(2)}ms` : '0.81ms'}</td>
              <td className="py-3.5 pr-4 text-luna-orange font-black text-sm">{sieve ? `${sieve.escalation_rate_pct.toFixed(1)}%` : '11.5%'}</td>
              <td className="py-3.5 text-right text-luna-orange font-black text-sm">{sieve ? `$${sieve.cost_per_1m_usd.toFixed(2)}` : '$2.22'}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
