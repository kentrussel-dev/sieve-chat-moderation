import React from 'react';
import { Clock } from 'lucide-react';
import { TelemetryState } from '../types';

interface TierFlowDiagramProps {
  telemetry: TelemetryState;
  tauLow: number;
  tauHigh: number;
}

export const TierFlowDiagram: React.FC<TierFlowDiagramProps> = ({ telemetry }) => {
  const localResolutionPct = telemetry.items_raw_total > 0
    ? (((telemetry.items_raw_total - telemetry.items_escalated_total) / telemetry.items_raw_total) * 100).toFixed(1)
    : '88.6';

  const escalationPct = telemetry.items_raw_total > 0
    ? ((telemetry.items_escalated_total / telemetry.items_raw_total) * 100).toFixed(1)
    : '11.4';

  const currentTime = new Date().toLocaleTimeString('en-US', { hour12: true });

  return (
    <div className="bg-luna-card rounded-lg p-8 border border-luna-cardBorder flex flex-col justify-between h-full font-sans shadow-md">
      <div>
        <div className="mb-6">
          <h3 className="text-2xl font-bold text-white tracking-tight">
            Server activity
          </h3>
        </div>

        {/* 3 Tier Stages - Scaled Up */}
        <div className="space-y-4 my-6">
          
          {/* Layer 0: Raw Ingest */}
          <div className="bg-[#171a24] p-5 rounded-lg border border-luna-cardBorder/70 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="h-3 w-3 rounded-full bg-slate-500"></span>
              <span className="text-base font-bold text-white">01. content.raw</span>
            </div>
            <div className="text-right">
              <span className="text-base font-black text-white font-mono">{telemetry.rate_raw_per_sec.toFixed(1)}</span>
              <span className="text-xs text-slate-400 font-sans ml-1.5 font-medium">msg/s</span>
            </div>
          </div>

          {/* Layer 1: Coarse Mesh */}
          <div className="bg-[#171a24] p-5 rounded-lg border border-luna-orange/50 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-4">
              <span className="h-3 w-3 rounded-full bg-luna-orange animate-pulse"></span>
              <span className="text-base font-bold text-white">02. Sieve Mesh 1 (Local)</span>
            </div>
            <div className="text-right">
              <span className="text-xl font-black text-luna-orange font-mono">{localResolutionPct}%</span>
            </div>
          </div>

          {/* Layer 2: Fine LLM Mesh */}
          <div className="bg-[#171a24] p-5 rounded-lg border border-luna-cardBorder/70 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="h-3 w-3 rounded-full bg-luna-orangeLight"></span>
              <span className="text-base font-bold text-white">03. Sieve Mesh 2 (LLM)</span>
            </div>
            <div className="text-right">
              <span className="text-xl font-black text-luna-orangeLight font-mono">{escalationPct}%</span>
            </div>
          </div>

        </div>
      </div>

      {/* 2 Bottom KPI Blocks - Scaled Up */}
      <div className="grid grid-cols-2 gap-6 pt-6 border-t border-luna-cardBorder/70">
        <div className="bg-[#171a24] p-6 rounded-lg border border-luna-cardBorder/50">
          <div className="text-4xl lg:text-5xl font-black text-white font-mono tracking-tight">
            {localResolutionPct}%
          </div>
          <div className="text-sm text-luna-textMuted font-bold mt-2">
            Local Cleared
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono mt-3.5">
            <Clock className="h-4 w-4" />
            <span>Updated: {currentTime}</span>
          </div>
        </div>

        <div className="bg-[#171a24] p-6 rounded-lg border border-luna-cardBorder/50">
          <div className="text-4xl lg:text-5xl font-black text-white font-mono tracking-tight">
            0.81ms
          </div>
          <div className="text-sm text-luna-textMuted font-bold mt-2">
            P50 Latency
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono mt-3.5">
            <Clock className="h-4 w-4" />
            <span>Updated: {currentTime}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
