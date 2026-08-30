import React from 'react';
import { User } from 'lucide-react';

interface HeaderProps {
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
}

export const Header: React.FC<HeaderProps> = () => {
  return (
    <div className="flex h-16 w-full select-none font-sans border-b border-[#2f2f35]">
      
      {/* Top Left Brand Box (Twitch Signature Purple) */}
      <div className="flex w-72 lg:w-80 items-center justify-between bg-[#9146ff] px-5 shadow-sm">
        <div className="flex items-center gap-3">
          <img 
            src="/logo.png" 
            alt="Sieve Logo" 
            className="h-9 w-9 object-contain rounded-md shadow-sm filter drop-shadow hover:scale-105 transition-transform" 
          />
          <span className="text-xl font-black tracking-[0.25em] text-white uppercase">
            SIEVE
          </span>
        </div>
        <span className="text-[11px] text-purple-100 font-bold bg-purple-900/40 px-2 py-0.5 rounded">
          v1.4
        </span>
      </div>

      {/* Top Bar (Twitch Dark Navigation Surface) */}
      <div className="flex flex-1 items-center justify-between bg-[#18181b] px-6">
        
        {/* Left: Studio Sub-Brand / Status */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
            Contextual Toxicity Moderation Mesh
          </span>
        </div>

        {/* Right: Twitch Status badge & User Avatar */}
        <div className="flex items-center gap-6 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              AI MESH
            </span>
            <span className="flex h-5 items-center px-2 rounded bg-[#9146ff] text-[11px] font-black text-white">
              TIER 1 + 2
            </span>
          </div>

          <div className="flex items-center gap-3 pl-5 border-l border-[#2f2f35]">
            <span className="text-[#efeff1] font-semibold text-xs hidden sm:inline">
              moderator@sieve.ai
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#9146ff] text-white overflow-hidden ring-2 ring-purple-400/40">
              <User className="h-4 w-4 text-white" />
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
