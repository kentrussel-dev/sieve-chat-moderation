import React, { useState } from 'react';
import { DollarSign, TrendingDown, CheckCircle } from 'lucide-react';

export const UsageView: React.FC = () => {
  const [volumeMillions, setVolumeMillions] = useState<number>(10); // 10M default

  const sieveCostPer1M = 2.22;
  const llmCostPer1M = 15.50;
  const t1CostPer1M = 0.50;

  const monthlySieveCost = volumeMillions * sieveCostPer1M;
  const monthlyLLMCost = volumeMillions * llmCostPer1M;
  const monthlySavings = monthlyLLMCost - monthlySieveCost;
  const annualSavings = monthlySavings * 12;
  const savingsPct = (((monthlyLLMCost - monthlySieveCost) / monthlyLLMCost) * 100).toFixed(1);

  return (
    <div className="space-y-8 font-sans">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-luna-orange/15 text-luna-orange shadow-sm">
            <DollarSign className="h-6 w-6" />
          </div>
          <h2 className="text-3xl lg:text-4xl font-black text-white tracking-tight">
            Usage & Cost ROI <span className="text-base font-medium text-slate-400 ml-2.5">economic analysis</span>
          </h2>
        </div>
        <p className="mt-3 text-sm text-slate-300 leading-relaxed max-w-5xl font-normal">
          Interactive economic comparison calculating monthly cloud expenditures, LLM token reduction, and budget savings across scale tiers.
        </p>
      </div>

      {/* Interactive Volume Slider Card */}
      <div className="bg-luna-card rounded-lg p-8 border border-luna-cardBorder shadow-md space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h3 className="text-2xl font-bold text-white tracking-tight">
              Monthly Traffic Volume
            </h3>
            <p className="text-sm text-slate-400 mt-1">
              Adjust volume to simulate moderation load at scale
            </p>
          </div>
          <div className="text-right">
            <span className="text-4xl font-black text-luna-orange font-mono">
              {volumeMillions.toLocaleString()}M
            </span>
            <span className="text-sm text-slate-400 font-sans ml-2">items / month</span>
          </div>
        </div>

        <input
          type="range"
          min="1"
          max="100"
          step="1"
          value={volumeMillions}
          onChange={(e) => setVolumeMillions(parseInt(e.target.value))}
          className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-luna-orange"
        />

        <div className="flex justify-between text-xs font-mono text-slate-400">
          <span>1M / mo</span>
          <span>25M / mo</span>
          <span>50M / mo</span>
          <span>75M / mo</span>
          <span>100M / mo</span>
        </div>
      </div>

      {/* 3 Large KPI Result Boxes */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-sm font-medium">
            <span>Sieve Monthly Cost</span>
            <CheckCircle className="h-4 w-4 text-verdict-passed" />
          </div>
          <div className="text-3xl lg:text-4xl font-black text-white mt-2 font-mono">
            ${monthlySieveCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-1.5 font-sans">
            Based on $2.22 / 1M items
          </div>
        </div>

        <div className="bg-luna-card rounded-lg p-6 border border-luna-cardBorder shadow-md">
          <div className="flex items-center justify-between text-slate-400 text-sm font-medium">
            <span>Pure LLM Monthly Cost</span>
            <span className="text-xs font-bold text-verdict-flagged font-mono">Unoptimized</span>
          </div>
          <div className="text-3xl lg:text-4xl font-black text-slate-300 mt-2 font-mono line-through decoration-verdict-flagged/60">
            ${monthlyLLMCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-400 mt-1.5 font-sans">
            Based on $15.50 / 1M items
          </div>
        </div>

        <div className="bg-luna-card rounded-lg p-6 border border-luna-orange/40 shadow-md">
          <div className="flex items-center justify-between text-slate-300 text-sm font-medium">
            <span>Monthly Cost Reduction</span>
            <TrendingDown className="h-4 w-4 text-luna-orange" />
          </div>
          <div className="text-3xl lg:text-4xl font-black text-luna-orange mt-2 font-mono">
            ${monthlySavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-luna-orangeLight font-bold mt-1.5 font-sans">
            {savingsPct}% Budget Saved (${annualSavings.toLocaleString(undefined, { maximumFractionDigits: 0 })}/yr)
          </div>
        </div>
      </div>

      {/* Comparative Breakdown Table */}
      <div className="bg-luna-card rounded-lg p-8 border border-luna-cardBorder shadow-md">
        <h3 className="text-2xl font-bold text-white tracking-tight mb-6">
          Annual Budget Ledger
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-sm">
            <thead className="text-slate-300 border-b border-luna-cardBorder pb-3">
              <tr className="text-sm font-bold font-sans">
                <th className="pb-3 pr-4 font-bold text-slate-200">Architecture</th>
                <th className="pb-3 pr-4 font-bold text-slate-200">Unit Cost (1M)</th>
                <th className="pb-3 pr-4 font-bold text-slate-200">Monthly Budget</th>
                <th className="pb-3 pr-4 font-bold text-slate-200">Annual Budget</th>
                <th className="pb-3 text-right font-bold text-slate-200">Savings Delta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-luna-cardBorder/50">
              <tr className="hover:bg-luna-tableHover transition-colors">
                <td className="py-4 pr-4 text-slate-300 font-sans text-sm font-medium">1. Tier 1 Only (Local DistilBERT)</td>
                <td className="py-4 pr-4 text-slate-300 font-mono">${t1CostPer1M.toFixed(2)}</td>
                <td className="py-4 pr-4 text-slate-300 font-mono">${(volumeMillions * t1CostPer1M).toFixed(2)}</td>
                <td className="py-4 pr-4 text-slate-300 font-mono">${(volumeMillions * t1CostPer1M * 12).toFixed(2)}</td>
                <td className="py-4 text-right text-slate-500 font-mono">Low Accuracy (96.6%)</td>
              </tr>

              <tr className="hover:bg-luna-tableHover transition-colors">
                <td className="py-4 pr-4 text-slate-300 font-sans text-sm font-medium">2. LLM Only (Pure Frontier Baseline)</td>
                <td className="py-4 pr-4 text-slate-300 font-mono">${llmCostPer1M.toFixed(2)}</td>
                <td className="py-4 pr-4 text-slate-300 font-mono">${monthlyLLMCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td className="py-4 pr-4 text-slate-300 font-mono">${(monthlyLLMCost * 12).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td className="py-4 text-right text-slate-500 font-mono">Baseline ($0.00 saved)</td>
              </tr>

              <tr className="bg-luna-orange/10 hover:bg-luna-orange/15 transition-colors font-semibold">
                <td className="py-4 pr-4 text-white font-bold font-sans text-sm">3. Sieve Pipeline (Tiered Architecture)</td>
                <td className="py-4 pr-4 text-luna-orange font-black font-mono">${sieveCostPer1M.toFixed(2)}</td>
                <td className="py-4 pr-4 text-luna-orange font-black font-mono">${monthlySieveCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td className="py-4 pr-4 text-luna-orange font-black font-mono">${(monthlySieveCost * 12).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td className="py-4 text-right text-luna-orange font-black font-mono">-${annualSavings.toLocaleString(undefined, { maximumFractionDigits: 0 })} / yr</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
