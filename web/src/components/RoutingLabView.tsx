import React from 'react';
import { Play } from 'lucide-react';
import { EscalationBandHistogram } from './EscalationBandHistogram';
import { InteractiveTester } from './InteractiveTester';
import { ConfidenceBucket, ModerationEvent } from '../types';

interface RoutingLabViewProps {
  confidenceDistribution: ConfidenceBucket[];
  tauLow: number;
  tauHigh: number;
  onTauLowChange: (val: number) => void;
  onTauHighChange: (val: number) => void;
  onEventProcessed: (event: ModerationEvent) => void;
}

export const RoutingLabView: React.FC<RoutingLabViewProps> = ({
  confidenceDistribution,
  tauLow,
  tauHigh,
  onTauLowChange,
  onTauHighChange,
  onEventProcessed,
}) => {
  return (
    <div className="space-y-8 font-sans">
      
      {/* Header */}
      <div>
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-luna-orange/15 text-luna-orange shadow-sm">
            <Play className="h-6 w-6" />
          </div>
          <h2 className="text-3xl lg:text-4xl font-black text-white tracking-tight">
            Routing Lab <span className="text-base font-medium text-slate-400 ml-2.5">live simulation & calibration</span>
          </h2>
        </div>
        <p className="mt-3 text-sm text-slate-300 leading-relaxed max-w-5xl font-normal">
          Interactive evaluation sandbox for injecting test payloads, modifying the uncertainty decision boundaries [τ_low, τ_high], and testing burst traffic patterns in real-time.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        
        {/* Left: Confidence Distribution with Interactive Sliders (6 cols) */}
        <div className="xl:col-span-6">
          <EscalationBandHistogram
            data={confidenceDistribution}
            tauLow={tauLow}
            tauHigh={tauHigh}
            onTauLowChange={onTauLowChange}
            onTauHighChange={onTauHighChange}
          />
        </div>

        {/* Right: Interactive Routing Lab & Traffic Generator (6 cols) */}
        <div className="xl:col-span-6">
          <InteractiveTester
            tauLow={tauLow}
            tauHigh={tauHigh}
            onEventProcessed={onEventProcessed}
          />
        </div>

      </div>

    </div>
  );
};
