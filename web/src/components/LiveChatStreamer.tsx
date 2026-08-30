import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Tv,
  Play,
  RefreshCw,
  Eye,
  EyeOff,
  ExternalLink,
  MessageSquare,
  Radio,
  Trash2,
  ArrowDown,
  Swords,
  ArrowUpDown,
  Filter,
  ChevronDown,
  Check
} from 'lucide-react';
import { ModerationEvent } from '../types';
import { renderChatMessageWithEmotes, getTwitchUserColor, fetchAndRegisterChannelEmotes } from '../utils/emoteParser';

interface LiveChatStreamerProps {
  events: ModerationEvent[];
  categoryBuffers?: Record<string | number, ModerationEvent[]>;
  onEventProcessed?: (event: ModerationEvent) => void;
}

export type FilterType = 'all' | '1' | '2' | '3' | '4' | '5' | '6' | 'review';

export const LiveChatStreamer: React.FC<LiveChatStreamerProps> = ({ events, categoryBuffers }) => {
  const [channelInput, setChannelInput] = useState('');
  const [twitchConnected, setTwitchConnected] = useState(false);
  const [twitchChannel, setTwitchChannel] = useState('');
  const [twitchLoading, setTwitchLoading] = useState(false);

  const [sensaiRunning, setSensaiRunning] = useState(false);
  const [sensaiRate] = useState(15);

  const [condaRunning, setCondaRunning] = useState(false);
  const [condaRate] = useState(20);

  // Moderation filter settings
  const [redactToxic, setRedactToxic] = useState(false);
  const [revealedIds, setRevealedIds] = useState<Record<string, boolean>>({});

  // 6-Level Filter & Sorting State
  const [selectedLevelFilter, setSelectedLevelFilter] = useState<FilterType>('all');
  const [sortBy, setSortBy] = useState<'live' | 'score_desc' | 'score_asc' | 'latency_desc'>('live');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [isSortOpen, setIsSortOpen] = useState(false);
  const filterDropdownRef = useRef<HTMLDivElement>(null);
  const sortDropdownRef = useRef<HTMLDivElement>(null);

  // Close custom dropdowns on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (filterDropdownRef.current && !filterDropdownRef.current.contains(event.target as Node)) {
        setIsFilterOpen(false);
      }
      if (sortDropdownRef.current && !sortDropdownRef.current.contains(event.target as Node)) {
        setIsSortOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Scroll lock & "Go to live" state
  const [isScrolledUp, setIsScrolledUp] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isHistoryExtended, setIsHistoryExtended] = useState(false);

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const prevEventsLengthRef = useRef<number>(0);
  const programmaticScrollLockRef = useRef<boolean>(false);

  // Poll status periodically
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const [tRes, sRes, cRes] = await Promise.all([
          fetch('/api/twitch/status').then((r) => (r.ok ? r.json() : null)),
          fetch('/api/sensai/status').then((r) => (r.ok ? r.json() : null)),
          fetch('/api/conda/status').then((r) => (r.ok ? r.json() : null)),
        ]);

        if (tRes) {
          setTwitchConnected(tRes.connected);
          setTwitchChannel(tRes.channel || '');
        }
        if (sRes) setSensaiRunning(sRes.running);
        if (cRes) setCondaRunning(cRes.running);
      } catch (err) {
        console.error('Status poll error:', err);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 1500);
    return () => clearInterval(interval);
  }, []);

  // Single source of truth for message level resolution
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

  // Persistent category-specific buffers: retains up to 100 messages for EACH filter category
  const [categoryBuckets, setCategoryBuckets] = useState<Record<string, ModerationEvent[]>>({
    '1': [],
    '2': [],
    '3': [],
    '4': [],
    '5': [],
    '6': [],
    'review': [],
  });

  const seenIdsRef = useRef<Set<string>>(new Set());

  // Ingest incoming events and categoryBuffers into persistent category buckets (Capped at 100 per level)
  useEffect(() => {
    let hasNew = false;

    setCategoryBuckets((prev) => {
      const next: Record<string, ModerationEvent[]> = {
        '1': [...(prev['1'] || [])],
        '2': [...(prev['2'] || [])],
        '3': [...(prev['3'] || [])],
        '4': [...(prev['4'] || [])],
        '5': [...(prev['5'] || [])],
        '6': [...(prev['6'] || [])],
        'review': [...(prev['review'] || [])],
      };

      // 1. Sync from server categoryBuffers prop (Authoritative persistence from backend)
      if (categoryBuffers) {
        Object.entries(categoryBuffers).forEach(([k, list]) => {
          const key = String(k);
          if (next[key] && Array.isArray(list)) {
            // Traverse from oldest to newest (list is ordered newest-first)
            for (let i = list.length - 1; i >= 0; i--) {
              const item = list[i];
              if (item && item.id && !seenIdsRef.current.has(item.id)) {
                seenIdsRef.current.add(item.id);
                next[key].push(item);
                hasNew = true;
              }
            }
            if (next[key].length > 100) {
              next[key] = next[key].slice(-100);
            }
          }
        });
      }

      // 2. Ingest from live events stream
      if (events && events.length > 0) {
        for (let i = events.length - 1; i >= 0; i--) {
          const e = events[i];
          if (e && e.id && !seenIdsRef.current.has(e.id)) {
            seenIdsRef.current.add(e.id);
            hasNew = true;

            const levelKey = String(getEffectiveLevel(e));
            if (next[levelKey]) {
              next[levelKey].push(e);
              if (next[levelKey].length > 100) {
                next[levelKey] = next[levelKey].slice(-100);
              }
            }

            if (e.flagged_for_review) {
              next['review'].push(e);
              if (next['review'].length > 100) {
                next['review'] = next['review'].slice(-100);
              }
            }
          }
        }
      }

      return hasNew ? next : prev;
    });
  }, [events, categoryBuffers]);

  // Compute 6-Level Live Counts directly from the 100-message retained category buckets
  const countL1 = categoryBuckets['1']?.length || 0;
  const countL2 = categoryBuckets['2']?.length || 0;
  const countL3 = categoryBuckets['3']?.length || 0;
  const countL4 = categoryBuckets['4']?.length || 0;
  const countL5 = categoryBuckets['5']?.length || 0;
  const countL6 = categoryBuckets['6']?.length || 0;
  const countReview = categoryBuckets['review']?.length || 0;

  // Chronological message calculation & Category-Retained Filtering
  const displayedMessages = useMemo(() => {
    let sourceList: ModerationEvent[] = [];

    if (selectedLevelFilter === 'all') {
      // In 'All Messages' view, show full live stream (newest at bottom)
      sourceList = [...events].reverse();
    } else if (selectedLevelFilter === 'review') {
      // In 'Review Queue' view, show all retained review messages (up to 100)
      sourceList = [...(categoryBuckets['review'] || [])].reverse();
    } else {
      // In specific level view (L1..L6), show all retained messages for this level (up to 100)
      const levelKey = String(selectedLevelFilter);
      sourceList = [...(categoryBuckets[levelKey] || [])].reverse();
    }

    let filtered = [...sourceList];

    if (sortBy === 'score_desc') {
      filtered.sort((a, b) => (b.toxicity_score ?? b.tier1_score) - (a.toxicity_score ?? a.tier1_score));
    } else if (sortBy === 'score_asc') {
      filtered.sort((a, b) => (a.toxicity_score ?? a.tier1_score) - (b.toxicity_score ?? b.tier1_score));
    } else if (sortBy === 'latency_desc') {
      filtered.sort((a, b) => b.total_latency_ms - a.total_latency_ms);
    }

    return isHistoryExtended ? filtered : filtered.slice(-100);
  }, [events, categoryBuckets, selectedLevelFilter, sortBy, isHistoryExtended]);

  // Handle incoming messages & auto-scroll (only in live mode)
  useEffect(() => {
    const newItems = events.length - prevEventsLengthRef.current;
    prevEventsLengthRef.current = events.length;

    if (sortBy === 'live') {
      if (isScrolledUp) {
        if (newItems > 0) {
          setUnreadCount((prev) => prev + newItems);
        }
      } else {
        if (chatContainerRef.current && !programmaticScrollLockRef.current) {
          chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
      }
    }
  }, [events, isScrolledUp, sortBy]);

  // Detect user scroll position
  const handleChatScroll = () => {
    if (!chatContainerRef.current || programmaticScrollLockRef.current || sortBy !== 'live') return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 60;

    if (isAtBottom) {
      setIsScrolledUp(false);
      setUnreadCount(0);
      setIsHistoryExtended(false);
    } else {
      setIsScrolledUp(true);
      setIsHistoryExtended(true);
    }
  };

  // Jump back to live feed and snap back to max 100 messages within the ACTIVE filter
  const handleGoToLive = () => {
    programmaticScrollLockRef.current = true;
    setIsScrolledUp(false);
    setUnreadCount(0);
    setIsHistoryExtended(false);
    // Keep active level filter - DO NOT reset to 'all'

    setTimeout(() => {
      if (chatContainerRef.current) {
        chatContainerRef.current.scrollTo({
          top: chatContainerRef.current.scrollHeight,
          behavior: 'smooth'
        });
      }
      setTimeout(() => {
        if (chatContainerRef.current) {
          chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
        programmaticScrollLockRef.current = false;
      }, 350);
    }, 50);
  };

  // Switch filter tab and smoothly reset scroll
  const handleSelectTab = (tab: FilterType) => {
    setSelectedLevelFilter(tab);
    setIsScrolledUp(false);
    setUnreadCount(0);
    setIsHistoryExtended(false);
    setTimeout(() => {
      if (chatContainerRef.current) {
        chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
      }
    }, 20);
  };

  const handleTwitchConnect = async () => {
    const channelToUse = channelInput.trim().toLowerCase().replace('#', '');
    if (!channelToUse) return;

    setTwitchLoading(true);
    try {
      if (twitchConnected) {
        await fetch('/api/twitch/disconnect', { method: 'POST' });
        setTwitchConnected(false);
        setTwitchChannel('');
      } else {
        await fetch('/api/telemetry/clear', { method: 'POST' });
        const resp = await fetch('/api/twitch/connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ channel: channelToUse }),
        });
        if (resp.ok) {
          seenIdsRef.current.clear();
          setCategoryBuckets({
            '1': [],
            '2': [],
            '3': [],
            '4': [],
            '5': [],
            '6': [],
            'review': [],
          });
          setTwitchConnected(true);
          setTwitchChannel(channelToUse);
          setChannelInput(channelToUse);
          setIsScrolledUp(false);
          setUnreadCount(0);
          setIsHistoryExtended(false);
          fetchAndRegisterChannelEmotes(channelToUse);
        }
      }
    } catch (err) {
      console.error('Twitch connection error:', err);
    } finally {
      setTwitchLoading(false);
    }
  };

  const handleSensaiToggle = async () => {
    try {
      if (sensaiRunning) {
        await fetch('/api/sensai/stop', { method: 'POST' });
        setSensaiRunning(false);
      } else {
        await fetch('/api/sensai/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rate_per_sec: sensaiRate }),
        });
        setSensaiRunning(true);
      }
    } catch (err) {
      console.error('Sensai toggle error:', err);
    }
  };

  const handleCondaToggle = async () => {
    try {
      if (condaRunning) {
        await fetch('/api/conda/stop', { method: 'POST' });
        setCondaRunning(false);
      } else {
        await fetch('/api/conda/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rate_per_sec: condaRate }),
        });
        setCondaRunning(true);
      }
    } catch (err) {
      console.error('CONDA toggle error:', err);
    }
  };

  const handleClearChat = async () => {
    try {
      seenIdsRef.current.clear();
      setCategoryBuckets({
        '1': [],
        '2': [],
        '3': [],
        '4': [],
        '5': [],
        '6': [],
        'review': [],
      });
      await fetch('/api/telemetry/clear', { method: 'POST' });
    } catch (err) {}
  };

  const toggleReveal = (id: string) => {
    setRevealedIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const currentHostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

  // 6-Level Minimal Badge Styling Map (Clean, Subdued, Professional)
  const levelThemeMap: Record<number, {
    dotColor: string;
    badgeText: string;
    badgeLabel: string;
  }> = {
    1: {
      dotColor: 'bg-emerald-400',
      badgeText: 'text-emerald-400/90',
      badgeLabel: 'L1 Clean'
    },
    2: {
      dotColor: 'bg-sky-400',
      badgeText: 'text-sky-400/90',
      badgeLabel: 'L2 Slang'
    },
    3: {
      dotColor: 'bg-amber-400',
      badgeText: 'text-amber-400/90',
      badgeLabel: 'L3 Sarcasm'
    },
    4: {
      dotColor: 'bg-orange-400',
      badgeText: 'text-orange-400/90',
      badgeLabel: 'L4 Hostile'
    },
    5: {
      dotColor: 'bg-rose-400',
      badgeText: 'text-rose-400/90',
      badgeLabel: 'L5 Toxic'
    },
    6: {
      dotColor: 'bg-purple-400',
      badgeText: 'text-purple-400/90',
      badgeLabel: 'L6 Severe'
    }
  };

  return (
    <div className="space-y-6">
      {/* Stream Control & Ingestion Toolbar */}
      <div className="bg-[#18181b] p-4 rounded-lg border border-[#2f2f35] shadow-xl">
        <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
          
          {/* Channel Connection Input */}
          <div className="flex items-center gap-3 w-full lg:w-auto">
            <div className="relative flex-1 sm:w-80">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#adadb8]">
                <Tv className="h-4 w-4" />
              </div>
              <input
                type="text"
                value={channelInput}
                onChange={(e) => setChannelInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleTwitchConnect()}
                placeholder="Enter Twitch channel name..."
                className="w-full pl-9 pr-4 py-2 bg-[#0e0e10] text-white text-sm rounded-lg border border-[#2f2f35] focus:outline-none focus:border-[#9146ff] transition-colors"
              />
            </div>
            
            <button
              onClick={handleTwitchConnect}
              disabled={twitchLoading}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
                twitchConnected
                  ? 'bg-rose-900/80 hover:bg-rose-800 text-rose-200 border border-rose-700/50'
                  : 'bg-[#9146ff] hover:bg-[#772ce8] text-white shadow-lg shadow-[#9146ff]/20'
              }`}
            >
              {twitchLoading ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              ) : twitchConnected ? (
                <>
                  <Radio className="h-3.5 w-3.5 fill-current text-rose-400 animate-pulse" />
                  Disconnect
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-current" />
                  Connect Live
                </>
              )}
            </button>
          </div>

          {/* Stream Datasets & Action Buttons */}
          <div className="flex items-center gap-2.5 flex-wrap justify-end w-full lg:w-auto">
            {/* CONDA In-Game Dota 2 Match Replay Toggle */}
            <button
              onClick={handleCondaToggle}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                condaRunning
                  ? 'bg-[#1f1f23] border-emerald-500/50 text-white'
                  : 'bg-[#1f1f23] border-[#2f2f35] text-slate-400 hover:text-white'
              }`}
              title="Replays real in-game match chats from the CONDA dataset"
            >
              {condaRunning ? (
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              ) : (
                <Swords className="h-3.5 w-3.5 text-slate-400" />
              )}
              <span>{condaRunning ? `CONDA (${condaRate}/s)` : 'CONDA Game Replay'}</span>
            </button>

            {/* Sensai Dataset Replay Toggle */}
            <button
              onClick={handleSensaiToggle}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
                sensaiRunning
                  ? 'bg-[#1f1f23] border-[#9146ff]/50 text-white'
                  : 'bg-[#1f1f23] border-[#2f2f35] text-slate-400 hover:text-white'
              }`}
            >
              {sensaiRunning ? (
                <span className="h-2 w-2 rounded-full bg-[#bf94ff] animate-pulse" />
              ) : (
                <Play className="h-3.5 w-3.5 fill-current text-slate-400" />
              )}
              <span>{sensaiRunning ? `Sensai (${sensaiRate}/s)` : 'Sensai Live Replay'}</span>
            </button>

            {/* Clear Chat */}
            <button
              onClick={handleClearChat}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1f1f23] border border-[#2f2f35] text-slate-400 hover:text-rose-400 transition-colors"
              title="Clear all messages"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clear</span>
            </button>
          </div>

        </div>
      </div>

      {/* Main Split Layout: Live Video Stream + 6-Level Moderated Chat Studio */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-stretch">
        
        {/* Left Column: Live Twitch Video Player (7 Cols) */}
        <div className="xl:col-span-7 flex flex-col bg-[#18181b] rounded-lg border border-[#2f2f35] overflow-hidden shadow-2xl min-h-[620px]">
          
          <div className="bg-[#1f1f23] px-4 py-2.5 border-b border-[#2f2f35] flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              {twitchConnected ? (
                <>
                  <span className="h-2.5 w-2.5 rounded-full bg-[#eb0400] animate-pulse" />
                  <span className="text-xs font-bold text-white tracking-wide uppercase">
                    Twitch Live Stream: <span className="text-[#bf94ff] font-mono">twitch.tv/{twitchChannel}</span>
                  </span>
                </>
              ) : (
                <>
                  <span className="h-2.5 w-2.5 rounded-full bg-slate-600" />
                  <span className="text-xs font-bold text-[#adadb8] tracking-wide uppercase">
                    Stream Offline / Disconnected
                  </span>
                </>
              )}
            </div>
            {twitchConnected && (
              <a
                href={`https://twitch.tv/${twitchChannel}`}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-semibold text-[#bf94ff] hover:text-white flex items-center gap-1 transition-colors"
              >
                <span>Watch on Twitch</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>

          <div className="flex-1 relative flex items-center justify-center bg-black min-h-[550px]">
            {twitchConnected && twitchChannel ? (
              <iframe
                src={`https://player.twitch.tv/?channel=${twitchChannel}&parent=${currentHostname}&muted=true&autoplay=true`}
                height="100%"
                width="100%"
                allowFullScreen
                className="absolute inset-0 w-full h-full border-0"
                title="Twitch Player"
              />
            ) : (
              <div className="text-center p-8 text-slate-500 space-y-3">
                <Tv className="h-16 w-16 mx-auto stroke-1 opacity-40 text-slate-400" />
                <div className="font-mono text-xs uppercase tracking-wider text-slate-400 font-bold">
                  No Active Twitch Stream Connected
                </div>
                <p className="text-xs text-slate-500 max-w-sm mx-auto font-sans leading-relaxed">
                  Enter any active streamer name or click <span className="text-slate-300 font-mono font-bold">CONDA Game Replay</span> to stream in-game chat data.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: 6-Level Moderated Live Stream Chat (5 Cols) */}
        <div className="xl:col-span-5 flex flex-col bg-[#18181b] rounded-lg border border-[#2f2f35] shadow-2xl relative">
          
          {/* Studio Chat Header */}
          <div className="p-3 bg-[#18181b] border-b border-[#2f2f35] flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-[#bf94ff]" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                Stream Chat
              </span>
              <span className="bg-[#0e0e10] text-[10px] font-mono px-2 py-0.5 rounded text-slate-400 border border-[#2f2f35]">
                {events.length}
              </span>
            </div>

            {/* Quick Actions, Custom Dark Filter Dropdown & Custom Dark Sorting Dropdown */}
            <div className="flex items-center gap-2 flex-wrap">
              {/* Custom Dark Level Filter Dropdown */}
              <div ref={filterDropdownRef} className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setIsFilterOpen(!isFilterOpen);
                    setIsSortOpen(false);
                  }}
                  className="flex items-center gap-1.5 bg-[#0e0e10] hover:bg-[#27272a] border border-[#2f2f35] hover:border-[#9146ff] px-2.5 py-1 rounded text-[10px] font-bold text-white transition-all cursor-pointer shadow-sm"
                >
                  <Filter className="h-3 w-3 text-slate-400" />
                  {selectedLevelFilter === '1' && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />}
                  {selectedLevelFilter === '2' && <span className="h-1.5 w-1.5 rounded-full bg-sky-400" />}
                  {selectedLevelFilter === '3' && <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />}
                  {selectedLevelFilter === '4' && <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />}
                  {selectedLevelFilter === '5' && <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />}
                  {selectedLevelFilter === '6' && <span className="h-1.5 w-1.5 rounded-full bg-purple-400" />}
                  {selectedLevelFilter === 'review' && <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />}
                  
                  <span className={
                    selectedLevelFilter === '1' ? 'text-emerald-400' :
                    selectedLevelFilter === '2' ? 'text-sky-400' :
                    selectedLevelFilter === '3' ? 'text-amber-400' :
                    selectedLevelFilter === '4' ? 'text-orange-400' :
                    selectedLevelFilter === '5' ? 'text-rose-400' :
                    selectedLevelFilter === '6' ? 'text-purple-400' :
                    selectedLevelFilter === 'review' ? 'text-amber-300' :
                    'text-slate-200'
                  }>
                    {selectedLevelFilter === 'all' && `All (${events.length})`}
                    {selectedLevelFilter === '1' && `L1 Clean (${countL1})`}
                    {selectedLevelFilter === '2' && `L2 Slang (${countL2})`}
                    {selectedLevelFilter === '3' && `L3 Sarcasm (${countL3})`}
                    {selectedLevelFilter === '4' && `L4 Hostile (${countL4})`}
                    {selectedLevelFilter === '5' && `L5 Toxic (${countL5})`}
                    {selectedLevelFilter === '6' && `L6 Severe (${countL6})`}
                    {selectedLevelFilter === 'review' && `Review (${countReview})`}
                  </span>
                  <ChevronDown className={`h-3 w-3 text-slate-400 transition-transform duration-200 ${isFilterOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Dark Popover Menu */}
                {isFilterOpen && (
                  <div className="absolute right-0 top-full mt-1.5 z-50 w-52 bg-[#18181b] border border-[#2f2f35] rounded-lg shadow-2xl p-1 font-sans text-xs space-y-0.5 animate-in fade-in zoom-in-95 duration-100">
                    <div className="px-2 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                      Filter Severity Tier
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        handleSelectTab('all');
                        setIsFilterOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        selectedLevelFilter === 'all' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <span className="text-slate-200">All Messages</span>
                      <div className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
                        <span>{events.length}</span>
                        {selectedLevelFilter === 'all' && <Check className="h-3.5 w-3.5 text-[#bf94ff]" />}
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        handleSelectTab('1');
                        setIsFilterOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        selectedLevelFilter === '1' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-emerald-400 shrink-0" />
                        <span className="text-emerald-400 font-bold">L1 Clean</span>
                      </div>
                      <div className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
                        <span>{countL1}</span>
                        {selectedLevelFilter === '1' && <Check className="h-3.5 w-3.5 text-emerald-400" />}
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        handleSelectTab('2');
                        setIsFilterOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        selectedLevelFilter === '2' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-sky-400 shrink-0" />
                        <span className="text-sky-400 font-bold">L2 Slang</span>
                      </div>
                      <div className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
                        <span>{countL2}</span>
                        {selectedLevelFilter === '2' && <Check className="h-3.5 w-3.5 text-sky-400" />}
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        handleSelectTab('3');
                        setIsFilterOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        selectedLevelFilter === '3' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-amber-400 shrink-0" />
                        <span className="text-amber-400 font-bold">L3 Sarcasm</span>
                      </div>
                      <div className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
                        <span>{countL3}</span>
                        {selectedLevelFilter === '3' && <Check className="h-3.5 w-3.5 text-amber-400" />}
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        handleSelectTab('4');
                        setIsFilterOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        selectedLevelFilter === '4' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-orange-400 shrink-0" />
                        <span className="text-orange-400 font-bold">L4 Hostile</span>
                      </div>
                      <div className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
                        <span>{countL4}</span>
                        {selectedLevelFilter === '4' && <Check className="h-3.5 w-3.5 text-orange-400" />}
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        handleSelectTab('5');
                        setIsFilterOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        selectedLevelFilter === '5' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-rose-400 shrink-0" />
                        <span className="text-rose-400 font-bold">L5 Toxic</span>
                      </div>
                      <div className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
                        <span>{countL5}</span>
                        {selectedLevelFilter === '5' && <Check className="h-3.5 w-3.5 text-rose-400" />}
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        handleSelectTab('6');
                        setIsFilterOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        selectedLevelFilter === '6' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-purple-400 shrink-0" />
                        <span className="text-purple-400 font-bold">L6 Severe</span>
                      </div>
                      <div className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
                        <span>{countL6}</span>
                        {selectedLevelFilter === '6' && <Check className="h-3.5 w-3.5 text-purple-400" />}
                      </div>
                    </button>

                    {countReview > 0 && (
                      <button
                        type="button"
                        onClick={() => {
                          handleSelectTab('review');
                          setIsFilterOpen(false);
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                          selectedLevelFilter === 'review' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="h-2 w-2 rounded-full bg-amber-400 shrink-0" />
                          <span className="text-amber-300 font-bold">Review Queue</span>
                        </div>
                        <div className="flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
                          <span>{countReview}</span>
                          {selectedLevelFilter === 'review' && <Check className="h-3.5 w-3.5 text-amber-400" />}
                        </div>
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Custom Dark Sort Dropdown */}
              <div ref={sortDropdownRef} className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setIsSortOpen(!isSortOpen);
                    setIsFilterOpen(false);
                  }}
                  className="flex items-center gap-1.5 bg-[#0e0e10] hover:bg-[#27272a] border border-[#2f2f35] hover:border-[#9146ff] px-2.5 py-1 rounded text-[10px] font-bold text-white transition-all cursor-pointer shadow-sm"
                >
                  <ArrowUpDown className="h-3 w-3 text-slate-400" />
                  <span className="text-slate-200">
                    {sortBy === 'live' && 'Live Feed'}
                    {sortBy === 'score_desc' && 'Highest (p=1→0)'}
                    {sortBy === 'score_asc' && 'Cleanest (p=0→1)'}
                    {sortBy === 'latency_desc' && 'Slowest Latency'}
                  </span>
                  <ChevronDown className={`h-3 w-3 text-slate-400 transition-transform duration-200 ${isSortOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Dark Sort Popover Menu */}
                {isSortOpen && (
                  <div className="absolute right-0 top-full mt-1.5 z-50 w-48 bg-[#18181b] border border-[#2f2f35] rounded-lg shadow-2xl p-1 font-sans text-xs space-y-0.5 animate-in fade-in zoom-in-95 duration-100">
                    <div className="px-2 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                      Sort Stream
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        setSortBy('live');
                        setIsSortOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        sortBy === 'live' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <span>Live Stream Feed</span>
                      {sortBy === 'live' && <Check className="h-3.5 w-3.5 text-[#bf94ff]" />}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setSortBy('score_desc');
                        setIsSortOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        sortBy === 'score_desc' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <span>Highest Severity (p=1→0)</span>
                      {sortBy === 'score_desc' && <Check className="h-3.5 w-3.5 text-[#bf94ff]" />}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setSortBy('score_asc');
                        setIsSortOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        sortBy === 'score_asc' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <span>Lowest Severity (p=0→1)</span>
                      {sortBy === 'score_asc' && <Check className="h-3.5 w-3.5 text-[#bf94ff]" />}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setSortBy('latency_desc');
                        setIsSortOpen(false);
                      }}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition-colors cursor-pointer text-left ${
                        sortBy === 'latency_desc' ? 'bg-[#27272a] text-white font-bold' : 'text-slate-300 hover:bg-[#27272a]/70 hover:text-white'
                      }`}
                    >
                      <span>Slowest Latency</span>
                      {sortBy === 'latency_desc' && <Check className="h-3.5 w-3.5 text-[#bf94ff]" />}
                    </button>
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={() => setRedactToxic(!redactToxic)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded text-[10px] font-bold border transition-colors cursor-pointer ${
                  redactToxic
                    ? 'bg-rose-950/40 border-rose-600/50 text-rose-300'
                    : 'bg-[#0e0e10] border-[#2f2f35] text-slate-400 hover:text-white'
                }`}
                title="Redact / Hide flagged messages"
              >
                {redactToxic ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                {redactToxic ? 'Redact On' : 'Redact'}
              </button>
            </div>
          </div>

          {/* Chat Messages Stream Area (Sleek, Minimal Twitch Chat) */}
          <div
            key={`chat-container-${selectedLevelFilter}`}
            ref={chatContainerRef}
            onScroll={handleChatScroll}
            className="flex-1 p-2.5 overflow-y-auto space-y-1 font-sans text-xs bg-[#0e0e10] select-text relative"
            style={{ maxHeight: '560px', minHeight: '560px' }}
          >
            {displayedMessages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[520px] text-slate-500 font-mono text-xs space-y-2 select-none">
                <div className="text-sm font-bold text-slate-400">
                  {selectedLevelFilter === 'all'
                    ? 'No messages in chat feed.'
                    : `No Level ${selectedLevelFilter} messages detected.`}
                </div>
                <div className="text-[11px] text-slate-500">
                  {selectedLevelFilter === '6'
                    ? 'Level 6 (Severe / Extreme) messages will appear here when detected.'
                    : 'Messages matching this filter will stream here in real-time.'}
                </div>
              </div>
            ) : (
              displayedMessages.map((evt) => {
                const lvl = getEffectiveLevel(evt);
                const theme = levelThemeMap[lvl] || levelThemeMap[1];
                const isPassed = evt.status === 'PASSED';
                const isTier2 = evt.resolved_by_tier === 'TIER_2';
                const isFlagged = !isPassed;
                const userColor = getTwitchUserColor(evt.username || 'user');
                const isRedacted = redactToxic && isFlagged && !revealedIds[evt.id];
                const scoreValue = (evt.toxicity_score ?? evt.tier1_score ?? 0).toFixed(2);

                // Row highlight based on severity:
                // Level 4 (Hostile): Orange subtle highlight + left border
                // Level 5 (Toxic): Rose subtle highlight + left border
                // Level 6 (Severe): Purple subtle highlight + left border
                let rowHighlightClass = 'hover:bg-white/[0.02] border-b border-[#1f1f23]/40';
                if (lvl === 4) {
                  rowHighlightClass = 'bg-orange-950/20 border-l-2 border-l-orange-400 border-b border-orange-950/30 hover:bg-orange-950/30';
                } else if (lvl === 5) {
                  rowHighlightClass = 'bg-rose-950/25 border-l-2 border-l-rose-500 border-b border-rose-950/40 hover:bg-rose-950/35';
                } else if (lvl === 6) {
                  rowHighlightClass = 'bg-purple-950/30 border-l-2 border-l-purple-500 border-b border-purple-950/50 hover:bg-purple-950/40';
                }

                return (
                  <div
                    key={evt.id}
                    className={`group px-2.5 py-1.5 rounded transition-colors flex items-start justify-between gap-2 ${rowHighlightClass}`}
                  >
                    <div className="flex items-baseline gap-1.5 flex-1 min-w-0 flex-wrap">
                      {/* Timestamp */}
                      <span className="text-[10px] text-slate-500 font-mono select-none shrink-0">
                        {evt.timestamp || 'now'}
                      </span>

                      {/* Minimal Level Badge with small dot */}
                      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono shrink-0 border ${
                        lvl === 4 ? 'bg-orange-950/40 border-orange-500/40' :
                        lvl === 5 ? 'bg-rose-950/40 border-rose-500/40' :
                        lvl === 6 ? 'bg-purple-950/40 border-purple-500/40' :
                        'bg-[#18181b] border-[#2f2f35]'
                      }`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${theme.dotColor}`} />
                        <span className={theme.badgeText}>{theme.badgeLabel}</span>
                        <span className="text-slate-400 font-bold ml-0.5">p={scoreValue}</span>
                      </span>

                      {evt.flagged_for_review && (
                        <span className="text-[9px] font-mono font-bold text-amber-400/90 bg-amber-500/10 px-1 py-0.5 rounded border border-amber-500/20 shrink-0">
                          Review
                        </span>
                      )}

                      {/* Username */}
                      <span
                        style={{ color: userColor }}
                        className="font-bold text-xs hover:underline cursor-pointer shrink-0"
                      >
                        {evt.username || 'Chatter'}:
                      </span>

                      {/* Message Content */}
                      <span className="text-[#efeff1] text-xs leading-relaxed break-words">
                        {isRedacted ? (
                          <span className="text-rose-400 text-xs italic bg-rose-950/30 px-2 py-0.5 rounded border border-rose-900/40">
                            [Message hidden: {evt.category || 'Toxicity detected'}]
                            <button
                              onClick={() => toggleReveal(evt.id)}
                              className="ml-2 text-slate-300 hover:text-white underline font-bold"
                            >
                              Show
                            </button>
                          </span>
                        ) : (
                          renderChatMessageWithEmotes(evt.text)
                        )}
                      </span>
                    </div>

                    {/* Subtle Tier / Latency indicator on the right edge */}
                    <div className="text-[10px] font-mono text-slate-500 select-none shrink-0 pt-0.5 pl-2 opacity-50 group-hover:opacity-100 transition-opacity">
                      {isTier2 ? (
                        <span className="text-[#bf94ff]">Mesh 2 ({evt.total_latency_ms.toFixed(0)}ms)</span>
                      ) : (
                        <span>{evt.total_latency_ms.toFixed(1)}ms</span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Floating "See New Messages" Snap-Back Button */}
          {sortBy === 'live' && isScrolledUp && (
            <div className="absolute bottom-4 left-0 right-0 flex justify-center z-20 pointer-events-none">
              <button
                onClick={handleGoToLive}
                className="pointer-events-auto bg-[#9146ff] hover:bg-[#772ce8] text-white font-bold text-xs px-4 py-1.5 rounded-full shadow-2xl flex items-center gap-1.5 border border-[#bf94ff]/40 animate-bounce transition-transform"
              >
                <ArrowDown className="h-3.5 w-3.5" />
                <span>See new messages {unreadCount > 0 && `(${unreadCount})`}</span>
              </button>
            </div>
          )}

        </div>

      </div>
    </div>
  );
};
