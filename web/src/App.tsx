import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar, TabId } from './components/Sidebar';
import { TierFlowDiagram } from './components/TierFlowDiagram';
import { EscalationBandHistogram } from './components/EscalationBandHistogram';
import { BenchmarkComparisonPanel } from './components/BenchmarkComparisonPanel';
import { LiveModerationFeed } from './components/LiveModerationFeed';
import { InteractiveTester } from './components/InteractiveTester';
import { LiveChatStreamer } from './components/LiveChatStreamer';
import { MetricsView } from './components/MetricsView';
import { UsageView } from './components/UsageView';
import { RoutingLabView } from './components/RoutingLabView';
import { ThesisBenchmarkView } from './components/ThesisBenchmarkView';
import { TelemetryState, BenchmarkReport, ModerationEvent } from './types';
import { Activity as ActivityIcon } from 'lucide-react';

const INITIAL_TELEMETRY: TelemetryState = {
  items_raw_total: 12450,
  items_passed_total: 9820,
  items_flagged_total: 1210,
  items_escalated_total: 1420,
  rate_raw_per_sec: 48.5,
  rate_passed_per_sec: 38.2,
  rate_flagged_per_sec: 4.7,
  rate_escalated_per_sec: 5.6,
  recent_events: [],
  confidence_distribution: [
    { bucket: '0.0-0.1', count: 520, tier: 'passed' },
    { bucket: '0.1-0.2', count: 290, tier: 'passed' },
    { bucket: '0.2-0.3', count: 140, tier: 'escalated' },
    { bucket: '0.3-0.4', count: 85, tier: 'escalated' },
    { bucket: '0.4-0.5', count: 65, tier: 'escalated' },
    { bucket: '0.5-0.6', count: 70, tier: 'escalated' },
    { bucket: '0.6-0.7', count: 95, tier: 'escalated' },
    { bucket: '0.7-0.8', count: 110, tier: 'escalated' },
    { bucket: '0.8-0.9', count: 310, tier: 'flagged' },
    { bucket: '0.9-1.0', count: 480, tier: 'flagged' },
  ],
};

export const App: React.FC = () => {
  const [telemetry, setTelemetry] = useState<TelemetryState>(INITIAL_TELEMETRY);
  const [benchmarkReport, setBenchmarkReport] = useState<BenchmarkReport | null>(null);
  const [tauLow, setTauLow] = useState<number>(0.20);
  const [tauHigh, setTauHigh] = useState<number>(0.80);
  const [activeTab, setActiveTab] = useState<TabId>('LiveChat');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    fetch('/api/benchmark')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setBenchmarkReport(data);
      })
      .catch((err) => console.log('Notice: benchmark API unavailable', err));

    const interval = setInterval(() => {
      fetch('/api/telemetry')
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) setTelemetry(data);
        })
        .catch(() => {});
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  const handleEventProcessed = (newEvent: ModerationEvent) => {
    setTelemetry((prev) => ({
      ...prev,
      recent_events: [newEvent, ...prev.recent_events.slice(0, 99)],
      items_raw_total: prev.items_raw_total + 1,
      items_passed_total: newEvent.status === 'PASSED' ? prev.items_passed_total + 1 : prev.items_passed_total,
      items_flagged_total: newEvent.status === 'FLAGGED' ? prev.items_flagged_total + 1 : prev.items_flagged_total,
      items_escalated_total: newEvent.resolved_by_tier === 'TIER_2' ? prev.items_escalated_total + 1 : prev.items_escalated_total,
    }));
  };

  const filteredEvents = telemetry.recent_events.filter(
    (e) => !searchQuery || e.text.toLowerCase().includes(searchQuery.toLowerCase()) || e.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-luna-canvas text-[#e2e8f0] flex flex-col font-sans">
      {/* Top Header */}
      <Header
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      <div className="flex flex-1">
        {/* Functional Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {/* Dynamic View Router with Persistent Tab State */}
        <main className="flex-1 p-10 space-y-8 max-w-[1700px] overflow-y-auto">
          
          {/* TAB 0: Live Stream Chat (Twitch & Sensai) */}
          <div className={activeTab === 'LiveChat' ? 'block' : 'hidden'}>
            <LiveChatStreamer
              events={filteredEvents}
              onEventProcessed={handleEventProcessed}
            />
          </div>

          {/* TAB 1: Activity (Main Overview) */}
          <div className={activeTab === 'Activity' ? 'block space-y-8' : 'hidden'}>
            <div>
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-luna-orange/15 text-luna-orange shadow-sm">
                  <ActivityIcon className="h-6 w-6" />
                </div>
                <h2 className="text-3xl lg:text-4xl font-black text-white tracking-tight">
                  Activity <span className="text-base font-medium text-slate-400 ml-2.5">sieve pipeline</span>
                </h2>
              </div>
              <p className="mt-3 text-sm text-slate-300 leading-relaxed max-w-5xl font-normal">
                Monitoring view provide real time data from geographically distributed servers. Coarse classifier (Mesh 1) resolves ~88.5% of traffic in &lt;1ms; only ambiguous or borderline cases within the uncertainty band [τ_low to τ_high] escalate to the general-purpose LLM (Mesh 2).
              </p>
            </div>

            {/* Section 1: Server & Stream Activity */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
              <div className="xl:col-span-5">
                <TierFlowDiagram
                  telemetry={telemetry}
                  tauLow={tauLow}
                  tauHigh={tauHigh}
                />
              </div>

              <div className="xl:col-span-7">
                <LiveModerationFeed events={filteredEvents} />
              </div>
            </div>

            {/* Section 2: Calibration, Lab & Thesis Benchmark */}
            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
              <div className="xl:col-span-6 space-y-8">
                <EscalationBandHistogram
                  data={telemetry.confidence_distribution}
                  tauLow={tauLow}
                  tauHigh={tauHigh}
                  onTauLowChange={setTauLow}
                  onTauHighChange={setTauHigh}
                />

                <InteractiveTester
                  tauLow={tauLow}
                  tauHigh={tauHigh}
                  onEventProcessed={handleEventProcessed}
                />
              </div>

              <div className="xl:col-span-6">
                <BenchmarkComparisonPanel report={benchmarkReport} />
              </div>
            </div>
          </div>

          {/* TAB 2: Metrics */}
          <div className={activeTab === 'Metrics' ? 'block' : 'hidden'}>
            <MetricsView telemetry={telemetry} />
          </div>

          {/* TAB 3: Usage & Cost ROI */}
          <div className={activeTab === 'Usage' ? 'block' : 'hidden'}>
            <UsageView />
          </div>

          {/* TAB 4: Routing Lab */}
          <div className={activeTab === 'RoutingLab' ? 'block' : 'hidden'}>
            <RoutingLabView
              confidenceDistribution={telemetry.confidence_distribution}
              tauLow={tauLow}
              tauHigh={tauHigh}
              onTauLowChange={setTauLow}
              onTauHighChange={setTauHigh}
              onEventProcessed={handleEventProcessed}
            />
          </div>

          {/* TAB 5: Thesis Benchmark */}
          <div className={activeTab === 'ThesisBenchmark' ? 'block' : 'hidden'}>
            <ThesisBenchmarkView report={benchmarkReport} />
          </div>

        </main>
      </div>
    </div>
  );
};

export default App;
