import React from 'react';
import { Activity, BarChart2, DollarSign, FlaskConical, Play, Tv } from 'lucide-react';

export type TabId = 'Activity' | 'LiveChat' | 'Metrics' | 'Usage' | 'RoutingLab' | 'ThesisBenchmark';

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <aside className="w-72 lg:w-80 min-h-[calc(100vh-4rem)] bg-[#1f1f23] text-slate-300 select-none border-r border-[#2f2f35] font-sans">
      <div className="py-6 space-y-8 text-sm">
        
        {/* GROUP 1: Ingestion & Live Feeds */}
        <div>
          <div className="px-6 mb-2.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Live Streaming
          </div>
          <div className="space-y-0.5">
            
            {/* Live Stream Chat (Twitch & Sensai) */}
            <button
              onClick={() => onTabChange('LiveChat')}
              className={`relative w-full flex items-center gap-3 px-6 py-2.5 text-xs font-bold transition-colors ${
                activeTab === 'LiveChat'
                  ? 'text-white bg-[#9146ff]/20 text-[#bf94ff]'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {activeTab === 'LiveChat' && (
                <span className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#9146ff]"></span>
              )}
              <Tv className={`h-4 w-4 ${activeTab === 'LiveChat' ? 'text-[#bf94ff]' : 'text-slate-400'}`} />
              <span>Live Stream Studio</span>
            </button>

            {/* Activity (Overview) */}
            <button
              onClick={() => onTabChange('Activity')}
              className={`relative w-full flex items-center gap-3 px-6 py-2.5 text-xs font-bold transition-colors ${
                activeTab === 'Activity'
                  ? 'text-white bg-[#9146ff]/20 text-[#bf94ff]'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {activeTab === 'Activity' && (
                <span className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#9146ff]"></span>
              )}
              <Activity className={`h-4 w-4 ${activeTab === 'Activity' ? 'text-[#bf94ff]' : 'text-slate-400'}`} />
              <span>Pipeline Activity</span>
            </button>

          </div>
        </div>

        {/* GROUP 2: Telemetry & Observability */}
        <div>
          <div className="px-6 mb-2.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Observability
          </div>
          <div className="space-y-0.5">

            {/* Metrics */}
            <button
              onClick={() => onTabChange('Metrics')}
              className={`relative w-full flex items-center gap-3 px-6 py-2.5 text-xs font-bold transition-colors ${
                activeTab === 'Metrics'
                  ? 'text-white bg-[#9146ff]/20 text-[#bf94ff]'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {activeTab === 'Metrics' && (
                <span className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#9146ff]"></span>
              )}
              <BarChart2 className={`h-4 w-4 ${activeTab === 'Metrics' ? 'text-[#bf94ff]' : 'text-slate-400'}`} />
              <span>Real-Time Metrics</span>
            </button>

            {/* Usage / Cost */}
            <button
              onClick={() => onTabChange('Usage')}
              className={`relative w-full flex items-center gap-3 px-6 py-2.5 text-xs font-bold transition-colors ${
                activeTab === 'Usage'
                  ? 'text-white bg-[#9146ff]/20 text-[#bf94ff]'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {activeTab === 'Usage' && (
                <span className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#9146ff]"></span>
              )}
              <DollarSign className={`h-4 w-4 ${activeTab === 'Usage' ? 'text-[#bf94ff]' : 'text-slate-400'}`} />
              <span>Usage & Cost ROI</span>
            </button>

          </div>
        </div>

        {/* GROUP 3: Sieve Engine */}
        <div>
          <div className="px-6 mb-2.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Sieve Engine
          </div>
          <div className="space-y-0.5">
            
            {/* Routing Lab */}
            <button
              onClick={() => onTabChange('RoutingLab')}
              className={`relative w-full flex items-center gap-3 px-6 py-2.5 text-xs font-bold transition-colors ${
                activeTab === 'RoutingLab'
                  ? 'text-white bg-[#9146ff]/20 text-[#bf94ff]'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {activeTab === 'RoutingLab' && (
                <span className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#9146ff]"></span>
              )}
              <Play className={`h-4 w-4 ${activeTab === 'RoutingLab' ? 'text-[#bf94ff]' : 'text-slate-400'}`} />
              <span>Routing Lab</span>
            </button>

            {/* Thesis Benchmark */}
            <button
              onClick={() => onTabChange('ThesisBenchmark')}
              className={`relative w-full flex items-center gap-3 px-6 py-2.5 text-xs font-bold transition-colors ${
                activeTab === 'ThesisBenchmark'
                  ? 'text-white bg-[#9146ff]/20 text-[#bf94ff]'
                  : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
              }`}
            >
              {activeTab === 'ThesisBenchmark' && (
                <span className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#9146ff]"></span>
              )}
              <FlaskConical className={`h-4 w-4 ${activeTab === 'ThesisBenchmark' ? 'text-[#bf94ff]' : 'text-slate-400'}`} />
              <span>Thesis Benchmark</span>
            </button>

          </div>
        </div>

      </div>
    </aside>
  );
};
