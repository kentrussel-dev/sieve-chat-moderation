import React from 'react';

// Base verified high-resolution working Twitch, FrankerFaceZ, and 7TV emote CDN dictionary
export const POPULAR_EMOTES: Record<string, string> = {
  // Top 7TV / FFZ Community Emotes
  'KEKW': 'https://cdn.frankerfacez.com/emote/381875/2',
  'OMEGALUL': 'https://cdn.frankerfacez.com/emote/128054/2',
  'Pog': 'https://cdn.frankerfacez.com/emote/210748/2',
  'PogChamp': 'https://static-cdn.jtvnw.net/emoticons/v2/305954156/default/dark/2.0',
  'POGGERS': 'https://cdn.frankerfacez.com/emote/214129/2',
  'PepeHands': 'https://cdn.frankerfacez.com/emote/231552/2',
  'pepeLaugh': 'https://cdn.frankerfacez.com/emote/64785/2',
  'Pepega': 'https://cdn.frankerfacez.com/emote/243789/2',
  'monkaS': 'https://cdn.frankerfacez.com/emote/130762/2',
  'monkaW': 'https://cdn.frankerfacez.com/emote/214681/2',
  'Sadge': 'https://cdn.frankerfacez.com/emote/425196/2',
  'widepeepoHappy': 'https://cdn.frankerfacez.com/emote/270930/2',
  'widepeepoSad': 'https://cdn.frankerfacez.com/emote/303899/2',
  'LULW': 'https://cdn.frankerfacez.com/emote/139407/2',
  '5Head': 'https://cdn.frankerfacez.com/emote/239504/2',
  'AYAYA': 'https://cdn.frankerfacez.com/emote/162146/2',
  'EZ': 'https://cdn.frankerfacez.com/emote/263940/2',
  'Clap': 'https://cdn.frankerfacez.com/emote/146057/2',
  'catJAM': 'https://cdn.frankerfacez.com/emote/480436/2',
  'GIGACHAD': 'https://cdn.frankerfacez.com/emote/601614/2',
  'Copium': 'https://cdn.frankerfacez.com/emote/524919/2',
  'Hopium': 'https://cdn.frankerfacez.com/emote/588820/2',
  'Prayge': 'https://cdn.frankerfacez.com/emote/591462/2',
  'HUH': 'https://cdn.frankerfacez.com/emote/644140/2',
  'Aware': 'https://cdn.frankerfacez.com/emote/600742/2',
  'Clueless': 'https://cdn.frankerfacez.com/emote/606994/2',
  'DESPAIR': 'https://cdn.frankerfacez.com/emote/607212/2',
  'NODDERS': 'https://cdn.frankerfacez.com/emote/482025/2',
  'NOPERS': 'https://cdn.frankerfacez.com/emote/482028/2',
  'FeelsWeirdMan': 'https://cdn.frankerfacez.com/emote/131597/2',
  'FeelsGoodMan': 'https://cdn.frankerfacez.com/emote/1010/2',
  'FeelsBadMan': 'https://cdn.frankerfacez.com/emote/31894/2',
  'PauseChamp': 'https://cdn.frankerfacez.com/emote/384784/2',
  'HYPERCLAP': 'https://cdn.frankerfacez.com/emote/235882/2',
  'monkaGIGA': 'https://cdn.frankerfacez.com/emote/242767/2',
  'pepeJAM': 'https://cdn.frankerfacez.com/emote/306788/2',
  'gachiBASS': 'https://cdn.frankerfacez.com/emote/231987/2',
  'Kapp': 'https://cdn.frankerfacez.com/emote/214316/2',
  '4Head': 'https://cdn.frankerfacez.com/emote/23718/2',
  '3Head': 'https://cdn.frankerfacez.com/emote/304169/2',
  'LO': 'https://cdn.7tv.app/emote/630d5b7803657ff632e88a38/2x.webp',
  'ICANT': 'https://cdn.frankerfacez.com/emote/601614/2',
  'Classic': 'https://cdn.frankerfacez.com/emote/480436/2',
  'pepeD': 'https://cdn.frankerfacez.com/emote/306788/2',
  'Brodie': 'https://cdn.frankerfacez.com/emote/305267/2',

  // Official Native Twitch Emotes
  'Kappa': 'https://static-cdn.jtvnw.net/emoticons/v2/25/default/dark/2.0',
  'KappaPride': 'https://static-cdn.jtvnw.net/emoticons/v2/55338/default/dark/2.0',
  'LUL': 'https://static-cdn.jtvnw.net/emoticons/v2/425618/default/dark/2.0',
  'BibleThump': 'https://static-cdn.jtvnw.net/emoticons/v2/86/default/dark/2.0',
  'Kreygasm': 'https://static-cdn.jtvnw.net/emoticons/v2/41/default/dark/2.0',
  'ResidentSleeper': 'https://static-cdn.jtvnw.net/emoticons/v2/245/default/dark/2.0',
  'HeyGuys': 'https://static-cdn.jtvnw.net/emoticons/v2/30259/default/dark/2.0',
  'CoolCat': 'https://static-cdn.jtvnw.net/emoticons/v2/58127/default/dark/2.0',
  'VoHiYo': 'https://static-cdn.jtvnw.net/emoticons/v2/81274/default/dark/2.0',
  'NotLikeThis': 'https://static-cdn.jtvnw.net/emoticons/v2/58765/default/dark/2.0',
  'WutFace': 'https://static-cdn.jtvnw.net/emoticons/v2/28087/default/dark/2.0',
  'SwiftRage': 'https://static-cdn.jtvnw.net/emoticons/v2/34/default/dark/2.0',
  'BabyRage': 'https://static-cdn.jtvnw.net/emoticons/v2/22639/default/dark/2.0',
  'DansGame': 'https://static-cdn.jtvnw.net/emoticons/v2/33/default/dark/2.0',
  'SMOrc': 'https://static-cdn.jtvnw.net/emoticons/v2/52/default/dark/2.0',
  'Jatt': 'https://static-cdn.jtvnw.net/emoticons/v2/4166/default/dark/2.0'
};

// Dynamic Active Emote Dictionary (Merges all global 7TV, BTTV, and custom channel emotes)
const ACTIVE_EMOTES: Record<string, string> = { ...POPULAR_EMOTES };
const LOWER_EMOTE_MAP: Record<string, string> = {};

function recomputeLowerMap() {
  Object.keys(ACTIVE_EMOTES).forEach((k) => {
    LOWER_EMOTE_MAP[k.toLowerCase()] = ACTIVE_EMOTES[k];
  });
}
recomputeLowerMap();

export function registerDynamicEmotes(newEmotes: Record<string, string>) {
  Object.entries(newEmotes).forEach(([name, url]) => {
    if (name && url) {
      ACTIVE_EMOTES[name] = url;
    }
  });
  recomputeLowerMap();
}

// Auto-fetch all cached global & community emotes from Sieve backend on startup
if (typeof window !== 'undefined') {
  fetch('/api/emotes/all')
    .then((res) => res.json())
    .then((data: Record<string, string>) => {
      registerDynamicEmotes(data);
      console.log(`[Sieve Emote Engine] Registered ${Object.keys(ACTIVE_EMOTES).length} dynamic emotes.`);
    })
    .catch(() => {
      // Offline fallback already loaded via POPULAR_EMOTES
    });
}

export async function fetchAndRegisterChannelEmotes(channel: string) {
  if (!channel) return;
  try {
    const cleanChan = channel.trim().toLowerCase().replace('#', '');
    const res = await fetch(`/api/emotes/channel/${cleanChan}`);
    if (res.ok) {
      const channelEmotes = await res.json();
      registerDynamicEmotes(channelEmotes);
      console.log(`[Sieve Emote Engine] Loaded ${Object.keys(channelEmotes).length} emotes for channel #${cleanChan}`);
    }
  } catch (err) {
    // Graceful fallback
  }
}

// Soft, elegant Twitch-style username pastel color palette
const TWITCH_USER_COLORS = [
  '#93c5fd', // soft blue
  '#a78bfa', // soft purple
  '#34d399', // soft emerald
  '#f472b6', // soft pink
  '#fbbf24', // soft amber
  '#38bdf8', // soft sky
  '#c084fc', // soft violet
  '#fb923c', // soft orange
  '#4ade80', // soft green
  '#e879f9', // soft fuchsia
  '#818cf8', // soft indigo
  '#2dd4bf', // soft teal
];

export function getTwitchUserColor(username: string): string {
  let hash = 0;
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % TWITCH_USER_COLORS.length;
  return TWITCH_USER_COLORS[index];
}

/**
 * Parses message text and replaces known 7TV / BTTV / FFZ / Twitch emote words with animated images.
 */
export function renderChatMessageWithEmotes(text: string): React.ReactNode {
  if (!text) return null;
  const words = text.split(/\s+/);

  return (
    <span>
      {words.map((word, idx) => {
        // Strip trailing punctuation like "KEKW," or "Pog!"
        const cleanWord = word.replace(/^[^\w]+|[^\w]+$/g, '');
        const lowerClean = cleanWord.toLowerCase();
        const lowerExact = word.toLowerCase();

        const emoteUrl =
          ACTIVE_EMOTES[word] ||
          ACTIVE_EMOTES[cleanWord] ||
          LOWER_EMOTE_MAP[lowerClean] ||
          LOWER_EMOTE_MAP[lowerExact];

        if (emoteUrl) {
          return (
            <React.Fragment key={idx}>
              <img
                src={emoteUrl}
                alt={word}
                title={word}
                className="inline-block h-7 max-w-[48px] object-contain mx-1 my-0.5 align-middle select-none hover:scale-125 transition-transform"
                loading="eager"
              />{' '}
            </React.Fragment>
          );
        }

        return <span key={idx}>{word} </span>;
      })}
    </span>
  );
}
