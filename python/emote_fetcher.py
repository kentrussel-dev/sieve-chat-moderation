"""
Emote Fetcher Module for Sieve.
Pulls, merges, and normalizes live emote sets from BTTV and 7TV REST APIs into a unified local cache.
Supports both Global and Channel-specific emote sets with offline fallback and TTL caching.
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

CACHE_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "emotes_cache.json")
GLOBAL_CACHE_TTL_SECONDS = 86400  # 24 hours

# Direct API Endpoints
BTTV_GLOBAL_URL = "https://api.betterttv.net/3/cached/emotes/global"
BTTV_CHANNEL_URL_TEMPLATE = "https://api.betterttv.net/3/cached/users/twitch/{channel_id}"

# 7TV v3 API Endpoints
SEVENTV_GLOBAL_URL = "https://7tv.io/v3/emote-sets/global"
SEVENTV_CHANNEL_URL_TEMPLATE = "https://7tv.io/v3/users/twitch/{channel_id}"

# Common Twitch Channel Name to Numeric ID Mapping (for fast zero-auth lookup)
POPULAR_CHANNEL_IDS = {
    "caedrel": "92038375",
    "tarik": "44445592",
    "shroud": "37402112",
    "xqc": "71092938",
    "pokimane": "44445592",
    "ibai": "40972890",
    "hasanabi": "207813352"
}


def resolve_twitch_username_to_id(username: str) -> Optional[str]:
    """Resolves a Twitch username to its numerical Twitch user ID."""
    clean_user = username.strip().lower().replace("#", "")
    if clean_user in POPULAR_CHANNEL_IDS:
        return POPULAR_CHANNEL_IDS[clean_user]

    # Optional public resolver fallback (IVR Twitch lookup API)
    try:
        req = urllib.request.Request(
            f"https://api.ivr.fi/v2/twitch/user?login={clean_user}",
            headers={"User-Agent": "Sieve-Emote-Fetcher/1.0"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
                return str(data[0]["id"])
    except Exception as e:
        # Fallback to None if external lookup fails
        pass

    return None


def fetch_bttv_global_emotes() -> List[Dict]:
    """Fetches global BTTV emotes."""
    emotes = []
    try:
        req = urllib.request.Request(BTTV_GLOBAL_URL, headers={"User-Agent": "Sieve-Moderation/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw_data = json.loads(resp.read().decode("utf-8"))
            for item in raw_data:
                emotes.append({
                    "name": item.get("code", ""),
                    "source": "bttv",
                    "id": str(item.get("id", "")),
                    "animated": bool(item.get("animated", False)),
                    "scope": "global",
                    "channel_id": None
                })
        print(f"Fetched {len(emotes)} global emotes from BTTV.")
    except Exception as e:
        print(f"Notice: BTTV global fetch skipped or offline ({e}).")
    return emotes


def fetch_7tv_global_emotes() -> List[Dict]:
    """Fetches global 7TV (v3) emotes."""
    emotes = []
    try:
        req = urllib.request.Request(SEVENTV_GLOBAL_URL, headers={"User-Agent": "Sieve-Moderation/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw_data = json.loads(resp.read().decode("utf-8"))
            emote_list = raw_data.get("emotes", [])
            for item in emote_list:
                data = item.get("data", {})
                emotes.append({
                    "name": item.get("name", ""),
                    "source": "7tv",
                    "id": str(item.get("id", "")),
                    "animated": bool(data.get("animated", False)),
                    "scope": "global",
                    "channel_id": None
                })
        print(f"Fetched {len(emotes)} global emotes from 7TV.")
    except Exception as e:
        print(f"Notice: 7TV global fetch skipped or offline ({e}).")
    return emotes


def fetch_channel_emotes(channel_name_or_id: str) -> List[Dict]:
    """Fetches channel-specific emotes from BTTV and 7TV."""
    channel_id = channel_name_or_id
    if not channel_name_or_id.isdigit():
        resolved = resolve_twitch_username_to_id(channel_name_or_id)
        if resolved:
            channel_id = resolved
        else:
            print(f"Could not resolve numeric ID for channel: {channel_name_or_id}")
            return []

    emotes = []

    # 1. BTTV Channel Emotes
    try:
        url = BTTV_CHANNEL_URL_TEMPLATE.format(channel_id=channel_id)
        req = urllib.request.Request(url, headers={"User-Agent": "Sieve-Moderation/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw_data = json.loads(resp.read().decode("utf-8"))
            all_bttv = raw_data.get("channelEmotes", []) + raw_data.get("sharedEmotes", [])
            for item in all_bttv:
                emotes.append({
                    "name": item.get("code", ""),
                    "source": "bttv",
                    "id": str(item.get("id", "")),
                    "animated": bool(item.get("animated", False)),
                    "scope": "channel",
                    "channel_id": str(channel_id)
                })
    except Exception:
        pass

    # 2. 7TV Channel Emotes
    try:
        url = SEVENTV_CHANNEL_URL_TEMPLATE.format(channel_id=channel_id)
        req = urllib.request.Request(url, headers={"User-Agent": "Sieve-Moderation/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw_data = json.loads(resp.read().decode("utf-8"))
            emote_set = raw_data.get("emote_set", {})
            for item in emote_set.get("emotes", []):
                emotes.append({
                    "name": item.get("name", ""),
                    "source": "7tv",
                    "id": str(item.get("id", "")),
                    "animated": bool(item.get("data", {}).get("animated", False)),
                    "scope": "channel",
                    "channel_id": str(channel_id)
                })
    except Exception:
        pass

    print(f"Fetched {len(emotes)} channel-specific emotes for channel ID {channel_id}.")
    return emotes


def load_cached_emotes(force_refresh: bool = False) -> Dict[str, Dict]:
    """
    Loads unified emote dictionary from local cache or fetches if expired/missing.
    Returns map of emote_name -> EmoteObject.
    """
    os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)

    if os.path.exists(CACHE_FILE_PATH) and not force_refresh:
        try:
            with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            cached_time = cache_data.get("updated_at", 0)
            if time.time() - cached_time < GLOBAL_CACHE_TTL_SECONDS:
                return cache_data.get("emotes", {})
        except Exception:
            pass

    # Fetch and rebuild cache
    print("Refreshing Sieve global emote cache from 7TV and BTTV APIs...")
    bttv_emotes = fetch_bttv_global_emotes()
    seventv_emotes = fetch_7tv_global_emotes()

    emote_map: Dict[str, Dict] = {}
    for item in bttv_emotes + seventv_emotes:
        name = item.get("name", "").strip()
        if name and name not in emote_map:
            emote_map[name] = item

    # Add core hardcoded defaults if network was unavailable
    fallback_defaults = [
        ("KEKW", "7tv", True), ("OMEGALUL", "bttv", False), ("Pog", "bttv", False),
        ("PogChamp", "twitch", False), ("POGGERS", "bttv", False), ("GIGACHAD", "7tv", False),
        ("catJAM", "7tv", True), ("monkaS", "bttv", False), ("Copium", "7tv", True),
        ("PepeHands", "bttv", False), ("Sadge", "7tv", False), ("Kappa", "twitch", False)
    ]
    for name, src, anim in fallback_defaults:
        if name not in emote_map:
            emote_map[name] = {
                "name": name, "source": src, "id": "fallback",
                "animated": anim, "scope": "global", "channel_id": None
            }

    cache_payload = {
        "updated_at": int(time.time()),
        "total_emotes": len(emote_map),
        "emotes": emote_map
    }

    with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache_payload, f, indent=2)

def get_emote_cdn_url(item: Dict) -> str:
    """Generates the high-resolution direct CDN image URL for any normalized emote."""
    source = item.get("source", "").lower()
    emote_id = str(item.get("id", ""))
    name = item.get("name", "")

    if source == "7tv" and emote_id and emote_id != "fallback":
        return f"https://cdn.7tv.app/emote/{emote_id}/2x.webp"
    elif source == "bttv" and emote_id and emote_id != "fallback":
        return f"https://cdn.betterttv.net/emote/{emote_id}/2x"
    elif source == "ffz" and emote_id and emote_id != "fallback":
        return f"https://cdn.frankerfacez.com/emote/{emote_id}/2"
    elif source == "twitch" and emote_id and emote_id != "fallback":
        return f"https://static-cdn.jtvnw.net/emoticons/v2/{emote_id}/default/dark/2.0"
    
    # Fallback to FrankerFaceZ public archive by name
    return f"https://cdn.frankerfacez.com/emote/381875/2"


def get_all_emote_cdn_map() -> Dict[str, str]:
    """Returns a map of emote_name -> image_cdn_url for all cached emotes."""
    emotes = load_cached_emotes()
    cdn_map = {}
    for name, item in emotes.items():
        url = get_emote_cdn_url(item)
        if url:
            cdn_map[name] = url
    return cdn_map


if __name__ == "__main__":
    emotes = load_cached_emotes(force_refresh=True)
    print(f"Successfully refreshed emote cache with {len(emotes):,} emotes.")
    cdn_map = get_all_emote_cdn_map()
    print(f"Generated {len(cdn_map):,} CDN mapping entries.")
